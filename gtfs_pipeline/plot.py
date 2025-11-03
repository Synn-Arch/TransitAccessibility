import folium
import branca.colormap as cm
import webbrowser
import os
import geopandas as gpd

def plot(score_gdf, place, score_column="Score", filename="score_map.html"):
    score_gdf = score_gdf.copy()

    # 지도 중심 좌표 계산
    geom = place.geometry.unary_union
    center_point = geom.centroid
    center = [center_point.y, center_point.x]
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB dark_matter")

    # 컬러맵 정의 (작은 값: 빨간색, 큰 값: 파란색)
    colormap = cm.linear.RdYlBu_05.scale(score_gdf[score_column].min(), score_gdf[score_column].max())

    # 지도에 도로 추가
    for _, row in score_gdf.iterrows():
        if row['geometry'].geom_type == 'LineString':
            coords = [(lat, lon) for lon, lat in row['geometry'].coords]
            folium.PolyLine(
                locations=coords,
                color=colormap(row[score_column]),
                weight=1.5,
                opacity=0.7,
                tooltip=folium.Tooltip(
                    f"Score: {row[score_column]:.2f}<br>Street Name: {row['name']}"
                    )
            ).add_to(m)

    # 컬러바 추가
    # 캡션 지정
    colormap.caption = score_column
    colormap.add_to(m)

    # CSS 덮어쓰기 (legend 글자색 흰색)
    legend_css = """
    <style>
    .legend {
        color: white !important;
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(legend_css))

    # 저장
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    m.save(filename)