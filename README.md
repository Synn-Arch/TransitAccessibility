# Transit Accessibility Pipeline (GTFS + OSMnx)

This pipeline calculates **bus and rail accessibility scores** using **GTFS**, **OSMnx**, and **GeoPandas**, and exports the results as an interactive **Folium map** and a CSV file.
The main entry point is:

```bash
python -m scripts.run_pipeline
```

---

## 1️⃣ Installation (Virtual Environment + Dependencies)

### Option A: Standard `venv` + pip

```bash
# Clone repository
git clone <YOUR_REPO_URL> TransitAccessibility
cd TransitAccessibility

# Create and activate virtual environment
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

# Update pip and install dependencies
pip install -U pip
pip install -r requirements.txt
```

> ⚠️ If you encounter errors installing `geopandas`, `pyproj`, or `rtree`,
> we recommend using **Option B (Conda)** below.

---

### Option B: Conda (Recommended for stable geospatial setup)

```bash
# Clone repository
git clone <YOUR_REPO_URL> TransitAccessibility
cd TransitAccessibility

# Create a clean Conda environment
conda create -n gtfs python=3.11 -y
conda activate gtfs

# Install geospatial core packages
conda install -c conda-forge geopandas pyproj rtree -y

# Install remaining dependencies via pip
pip install -r requirements.txt
```

---

## 2️⃣ Data Preparation

Before running, prepare the following folder structure inside the project root:

```
data/
├─ gtfs/                  # GTFS .zip files (can contain multiple)
├─ amenities/
│  ├─ all_scores.json     # Stop-level amenity score dictionary
│  └─ Inventory.csv       # Amenity inventory file
├─ output/                # Output folder (auto-created if missing)
└─ LINE_EPSG4326.geojson  # Study area road network (EPSG:4326)
```

### Notes
* **GTFS**: Place one or more `.zip` feeds inside `data/gtfs/`.
  The pipeline automatically merges and cleans them.
* **`LINE_EPSG4326.geojson`**: A GeoJSON of road segments extracted from the `step1_loader` stage.
  Must be in **EPSG:4326** (WGS84).
* **`amenities`**: Contains precomputed amenity scores (`all_scores.json`).
  This will be integrated with a future pipeline step for automated amenity extraction.
  If no amenity information is available, leave this directory empty. The pipeline will still compute without the amenity scores.


---

### What is GTFS?

**GTFS (General Transit Feed Specification)** is a standardized data format that describes public transportation schedules, stops, routes, and related information.
It was originally developed by Google and Portland’s TriMet to enable transit data integration into Google Maps, and is now widely used by transit agencies around the world.

Each GTFS feed provides complete schedule data for one or more transit providers in a city.

#### 📥 How to get GTFS data

* Most cities or transportation agencies publish their GTFS data publicly.
  Try searching on Google for your city name along with “**GTFS**”.
  For example:

  ```
  "Seoul GTFS"
  "New York City GTFS"
  "London GTFS"
  ```

  This usually leads to an official open-data portal or a public transport API.

* You can also browse and download GTFS feeds from the **Mobility Database**:
  🔗 [https://mobilitydatabase.org/](https://mobilitydatabase.org/)


---

## 3️⃣ Running the Pipeline

Run the pipeline directly from the project root:

```bash
python -m scripts.run_pipeline
```

---

### Execution Flow Overview

1. **Load and process GTFS ZIP files**
   → merges `stops.txt`, `trips.txt`, `routes.txt`, and others into unified dataframes.
2. **Load road network GeoJSON** and convert CRS to the appropriate **local UTM**.
3. **Download pedestrian network** from OSMnx and compute **isochrones** (700m radius, 100m for rail).
4. **Compute stop significance** using the E/S/F/Q scoring model.
5. **Interpolate points along streets** and aggregate scores per link (`scoring.py`).
6. **Save results:**
   * `data/output/bus_rail_score.html` — interactive map
   * `data/output/bus_rail_score.csv` — link-level accessibility scores

---

## 4️⃣ Outputs

* **Interactive map:**
  `data/output/bus_rail_score.html`
* **Score table (CSV):**
  `data/output/bus_rail_score.csv`
  Columns typically include:

  * `link_id`, `Score`, `Score_Bus`, `Score_Rail`, `geometry`, etc.