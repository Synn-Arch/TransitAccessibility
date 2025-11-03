import os
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import box

from gtfs_pipeline.processor import concat_dataframes
from gtfs_pipeline.network import download_walknetwork, compute_isochrones1, compute_isochrones
from gtfs_pipeline.interpolation import interpolate_roads
from gtfs_pipeline.analysis import stop_significance
from gtfs_pipeline.results import combine_scores, persist_and_plot


def main():
    # GTFS directory
    dl_dir = "data/gtfs"

    # GTFS Data Cleaning
    sched_merged, stops_bymode, tag = concat_dataframes(dl_dir)
    print("Processing Data Complete")

    # Study Area
    # LINE_EPSG4326.geojson - GeoJSON of road segments extracted from the ./../../step1_loader step.
    network_gdf = gpd.read_file("data/LINE_EPSG4326.geojson")
    network_gdf = network_gdf.iloc[:5]
    print("Study Area Load")

    # Check Existence of Bus or Subway
    has_bus = 3 in stops_bymode['route_type'].unique()
    has_rail = stops_bymode['route_type'].isin({0,1,2,5,12}).any()
    if has_bus and has_rail:
        print("✅ Both bus and rail stops are available.")
    elif not has_bus and has_rail:
        print("⚠️ No bus stops found in this city.")
    elif has_bus and not has_rail:
        print("⚠️ No rail stops found in this city.")
    print(f"{len(stops_bymode)} Stops will be processed")

    streets = network_gdf.copy()
    first_geom = streets.geometry.iloc[0]
    lon, lat = first_geom.coords[0]
    zone = int((lon + 180) // 6) + 1
    epsg = (32600 if lat >= 0 else 32700) + zone
    target_crs = CRS.from_epsg(epsg)
    streets = streets.to_crs(target_crs)

    # Download Walking Network & Compute Isochrones
    points_gdf = interpolate_roads(streets, target_crs)
    streets_buffer = streets.buffer(700).union_all()
    walk_network = download_walknetwork(streets_buffer, crs=streets.crs)
    iso_700_road = compute_isochrones1(points_gdf, walk_network)
    print(f"Data is ready")

    iso_by_link = iso_700_road.dissolve(by="link_id", as_index=False)
    stops_within_iso = gpd.sjoin(stops_bymode, iso_by_link, how="inner", predicate='intersects')
    isos_700_rail, isos_700_bus, isos_100_rail = compute_isochrones(stops_within_iso, walk_network)


    # 8) Bus Stops Significance Calculation
    bus_iso_scored, rail_iso_scored = stop_significance(stops_within_iso, stops_bymode, isos_100_rail, isos_700_bus, isos_700_rail, sched_merged, target_crs, tag) if has_bus else None
    print("Step 8: Significance + Isochrone Complete")
    
    # 9) Scoring, Plot
    minx, miny, maxx, maxy = stops_bymode.total_bounds
    bbox_geom = box(minx, miny, maxx, maxy)
    bbox_gdf = gpd.GeoDataFrame(geometry=[bbox_geom], crs=stops_bymode.crs)
    try:
        bus_rail_score = combine_scores(
            bus_iso_scored,
            rail_iso_scored,
            streets,
            bbox_gdf,
        )
        print("Step 11: Scoring Each Street Complete ('Score' Column) + Geometry is allocated")
    except ValueError as e:
        print(f"❌ Scoring failed: {e}")
        return

    persist_and_plot(
        place_geometry=bbox_gdf,
        bus_rail_score=bus_rail_score,
    )
    print("Step 12: Maps are prepared, and saved")

    exit(0)

final_score = main()

# 사용법: python -m scripts.run_pipeline