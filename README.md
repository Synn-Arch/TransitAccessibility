![Transit Animation](docs/img/animation.gif)

# Transit Accessibility Pipeline (GTFS + OSMnx)

## 📍 Objective
This repository provides tools to compute **transit accessibility scores** along road network segments using **GTFS feeds** and **OSMnx pedestrian networks**.  
It outputs both an **interactive Folium map** and structured **CSV/GeoJSON** files at the **link level**.

## Input

A **GeoJSON file** representing road segment links (EPSG:4326), along with:

- One or more **GTFS`.zip` files**
- A GeoJSON file of road segment points
- (Optional) Amenity score file (`all_scores.json`) to enrich bus stop facility scoring

## Process

1. Load and merge **GTFS feeds** into unified stop, route, and trip tables.  
2. Download pedestrian networks and generate **walkable isochrones** using OSMnx.  
3. Compute **stop significance** using a multi-factor model (E/S/F/Q).  
4. Interpolate analysis points along road links and **aggregate accessibility** via spatial joins.  
5. Export results as **interactive HTML maps**, **CSV summaries**, and **GeoJSON layers**.

## Output

- **Interactive map** (HTML)
- **CSV file** with road segment-level transit accessibility scores  
- **GeoJSON files** with road segment-level transit accessibility scores 

## 📦 Features

- Automated GTFS ingestion and merging  
- OSMnx-based pedestrian network & walkable catchments  
- Multi-factor stop significance model (E, S, F, Q)  
- Road-link interpolation and aggregated scoring  
- Optional integration of bus-stop amenities  

## 🚗 Quick Guide

### 1. Environment Setup

#### Option A — `venv` + pip

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\Activate.ps1    # Windows

pip install -U pip
pip install -r requirements.txt
````

> If installation of geospatial packages fails, use Conda instead.

#### Option B — Conda (Recommended)

```bash
conda create -n gtfs python=3.11 -y
conda activate gtfs

conda install -c conda-forge geopandas pyproj rtree -y
pip install -r requirements.txt
```

### 2. Prepare Input Data

Your project directory should contain:

```
data/
├─ gtfs/                  
│  └─ gtfs.zip            # One or more GTFS .zip files (can be various names)
├─ amenities/
│  └─ all_scores.json     # Optional amenity score dictionary
├─ output/                # Output folder
└─ LINE_EPSG4326.geojson  # Road network (EPSG:4326)
```

1. Add the road network file:
   `data/LINE_EPSG4326.geojson`
2. Place one or more GTFS ZIP files in:
   `data/gtfs/`
3. (Optional) Add amenity data in:
   `data/amenities/all_scores.json`

If no amenity data is provided, the pipeline still executes without evaluating quality score.

#### 2-1. What Is GTFS & How to Get It

GTFS is a standardized data format that provides all essential public transit information, such as stops, routes, schedules, and trips, in a consistent structure so that transit systems can be easily analyzed.  

Sources for GTFS feeds:

* Search online: `"Seoul GTFS"`, `"NYC GTFS"`, `"London GTFS"`
* Mobility Database:
  [https://mobilitydatabase.org/](https://mobilitydatabase.org/)

Download `.zip` files and place them in `data/gtfs/`.

### 3. Run the Pipeline

From the project root:

```bash
python -m scripts.run_pipeline
```

All results will be written into the `data/output/` directory.

## 🧩 Notes
* Links with no intersecting stops receive a score of **0**.
* Full functionality is preserved even without amenity data.
* Multiple GTFS feeds are merged automatically.

---

## ⚙️ Process (High-Level)

1. Load GTFS feeds and unify stops/trips/routes.
2. Define a **study boundary** with a 750 m buffer around road link midpoints.
3. Select bus and rail stops intersecting the study boundary.
4. Build **OSMnx pedestrian networks** and generate walkable catchments:
   * 700 m for all modes
   * 100 m for rail (for bus–rail connectivity)
5. Compute stop significance using:
   * `E`: route diversity
   * `S`: connectivity
   * `F`: service frequency
   * `Q`: amenities
6. Interpolate road links at **10 m spacing**.
7. Join interpolated points with stop isochrones and compute mean significance per point.
8. Aggregate scores to each road link to produce final accessibility scores.

---

# 🧠 Methodology

This section describes the full scoring framework applied in the pipeline.

## 1) Study Area Definition

* Compute midpoints of road centerlines.
* Apply a **750 m buffer** to form the analysis boundary.
* Select all bus/rail stops intersecting the boundary.

## 2) Walkable Catchments (Isochrones)

Generated in `network.py` using OSMnx:

* **700 m isochrones**: all transit modes
* **100 m isochrones**: rail modes (for multimodal connectivity)

These polygons are used to identify which stops influence which locations.

## 3) Stop Significance (E/S/F/Q)

Overall model:

```
significance = E × S × F + Q
```

### E — Route Diversity

```
factor_e = 0.5 + 0.5 * min(E, 3)
```

### S — Connectivity

**Bus stops:**

```
factor_s_bus = 1 + 0.5 * min(k, 2)
```

`k` = number of rail routes within 3 km.

**Rail stops:**

```
factor_s_rail = 1 + 0.5 * min(S_r, 2)
```

`S_r` = number of bus stops inside a 100 m rail catchment.

### F — Service Frequency

Peak hours: **07–09**, **16–19** (6 hours total)

```
< 2 → 1.00
< 3 → 1.25
< 4 → 1.50
≤ 6 → 1.75
> 6 → 2.00
```

### Q — Stop Facilities

**Bus:**

```
shelter_index = 2.0 if shelter else 1.0
amenities_index: ≤1→1.0, 2–3→1.5, ≥4→2.0
factor_q_bus = (shelter_index × amenities_index) / 2
```

If no amenity data → `factor_q_bus = 0`.

**Rail:**

```
2.5 (if amenity data exists)
0.5 (if missing)
```

### Combined

```
significance_bus  = E × S_bus  × F + Q_bus
significance_rail = E × S_rail × F + Q_rail
```

## 4) Road Point Interpolation

Road segments are sampled every **10 m** to form analysis points.

## 5) Point-Level Aggregation

For each interpolated point:

```
sig_sum_per_point  = Σ significance of intersecting stops
stops_count        = number of intersecting stops
sig_mean_per_point = sig_sum_per_point / stops_count  (or 0)
```

## 6) Link-Level Scoring

For each road link:

```
Score = sig_mean_mean × log((stops_computecount / points_count) + 1)
```

Separate scores for bus and rail are maintained.

## 7) Combined & Scaled Score

```
Transit_attribute = Score_Bus + Score_Rail
Transit_score     = clip(Transit_attribute, 0, 22) / 22 × 12.6
```

## 8) Final Outputs

Saved under `data/output/`:
* **Interactive map:**
  `Transit_Attributes_Map.html`
* **GeoJSON:**
  `Transit_Accessibility_SCORE.geojson`

Geometries are processed in **local UTM** and exported as **EPSG:4326** for mapping.