import os
import pandas as pd
import geopandas as gpd
from typing import Optional, Tuple
from gtfs_pipeline.plot import plot
from gtfs_pipeline.interpolation import interpolate_roads
from gtfs_pipeline.scoring import scoring


def combine_scores(
    bus_result_iso: Optional[gpd.GeoDataFrame],
    rail_result_iso: Optional[gpd.GeoDataFrame],
    streets: gpd.GeoDataFrame,
    place_geometry,
) -> Tuple[Optional[gpd.GeoDataFrame], Optional[gpd.GeoDataFrame], gpd.GeoDataFrame, gpd.GeoDataFrame]:
    
    # Interpolate points along streets using the provided geometry
    points = interpolate_roads(streets, target_crs=streets.crs)
    streets_gdf = streets.to_crs(bus_result_iso.crs)

    has_bus = bus_result_iso is not None
    has_rail = rail_result_iso is not None

    bus_score  = scoring(points, bus_result_iso, streets_gdf) \
        if (bus_result_iso is not None and not bus_result_iso.empty) else None
    rail_score = scoring(points, rail_result_iso, streets_gdf) \
        if (rail_result_iso is not None and not rail_result_iso.empty) else None

    if has_bus and has_rail:
        all_result_iso = pd.concat([bus_result_iso, rail_result_iso], ignore_index=True)
    elif has_bus:
        all_result_iso = bus_result_iso
    elif has_rail:
        all_result_iso = rail_result_iso
    else:
        raise ValueError("Scoring cannot be combined: both bus_result_iso and rail_result_iso are None or empty.")

    concat_score = scoring(points, all_result_iso, streets)

    # Aggregate bus and rail scores
    bus_rail_score = (bus_score.copy() if bus_score is not None else concat_score.copy())
    bus_rail_score['Score_Bus'] = bus_score['Score'] if bus_score is not None else 0
    bus_rail_score['Score_Rail'] = rail_score['Score'] if rail_score is not None else 0
    bus_rail_score['Score'] = bus_rail_score['Score_Bus'] + bus_rail_score['Score_Rail']

    return bus_rail_score


def persist_and_plot(
    place_geometry,
    bus_rail_score: gpd.GeoDataFrame,
):
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)

    html_path = os.path.join(output_dir, "bus_rail_score.html")
    plot(bus_rail_score, place_geometry, score_column="Score", filename=html_path)

    csv_path = os.path.join(output_dir, "bus_rail_score.csv")
    bus_rail_score.to_csv(csv_path, index=False)