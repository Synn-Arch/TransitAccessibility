import geopandas as gpd
import pandas as pd
import numpy as np

def scoring(points, iso, streets):
    joined_gdf = gpd.sjoin(points, iso, how="left", predicate="intersects")

    # 1. 인덱스를 컬럼으로 변환 (편하게 매칭하기위해) -> index는 일종의 interpolated points의 고유 id로 작용
    joined_gdf = joined_gdf.reset_index()
    #print(f"Debug Check: \n{joined_gdf}")

    # 2. 점마다 significance 합산 (u,v,key, geometry(점) 유지)
    collapsed_gdf = joined_gdf.groupby("index", as_index=False).agg({
    "name": "first",
    "link_id": "first",
    "geometry": "first",
    "significance": "sum"
    })
    collapsed_gdf = collapsed_gdf.rename(columns={"significance": "sig_sum_per_point"})

    # 3. significance를 몇 개 더했는지 count 추가 (점에서 집계된 버스정류장의 개수)
    collapsed_gdf["stops_count"] = joined_gdf.groupby("index")["significance"].count().values

    # 4. 점별로 significance의 평균값 계산 (분모 0일떄는 0)
    if collapsed_gdf["stops_count"].eq(0).all():
        print("⚠️ 모든 stops_count가 0입니다 — Isochrone과 겹치는 포인트가 없습니다.")

    collapsed_gdf['sig_mean_per_point'] = (
        collapsed_gdf['sig_sum_per_point'] / collapsed_gdf['stops_count']
    ).where(collapsed_gdf['stops_count'] != 0, 0)

    # 5. 같은 u,v,key를 가진 점들끼리 그룹화하여 통계 계산
    scoredStreet = collapsed_gdf.groupby(["link_id"], as_index=False).agg(
        #sig_sum_arithmean=("sig_sum_per_point", "mean"),  # 점별 sig의 합의 평균
        #sig_sum_sum=("sig_sum_per_point", "sum"),  # 각 점별 sig의 합의 총합
        points_count=("sig_sum_per_point", "count"),  # 길 위의 보간된 점들 총개수
        stops_computecount=("stops_count", "sum"),  # 계산에 사용된 모든 Isochrone의 개수 (중복 포함))
        sig_mean_mean=("sig_mean_per_point", "mean"),  # 보간된 점 각각의 sig 평균의 길상의 점들에 대한 평균
    )

    # 5-1. None일 경우 0채움
    scoredStreet['sig_mean_mean'] = scoredStreet['sig_mean_mean'].fillna(0)

    # 6. 🌟최종 인덱스 계산🌟
    scoredStreet['Score'] = scoredStreet['sig_mean_mean']*(np.log((scoredStreet['stops_computecount']/scoredStreet['points_count'])+1))

    # 7. Geometry 복구
    scoredStreet = scoredStreet.merge(
        streets[['name', 'link_id', 'geometry']],
        on=['link_id'],
        how='left'  # scoredStreet 기준 유지
    )
    scoredStreet = gpd.GeoDataFrame(
        scoredStreet,
        geometry='geometry',
        crs=streets.crs
    )
    return scoredStreet