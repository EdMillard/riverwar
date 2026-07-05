"""
Copyright (c) 2026 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all

copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import calendar
import requests
import os
import math
import time
import gzip
from pathlib import Path
import pandas as pd
import geopandas as gpd
from typing import Optional, Tuple, Dict, List
import ee
from shapely.geometry import Polygon

# OpemET API testing:
#    https://openet-api.org/

'''
ALEXI/DisALEXI (Atmosphere-Land Exchange Inverse / Disaggregation ALEXI): Two-source energy balance model using thermal infrared data. 
    Strong for partitioning evaporation/transpiration and handling varied conditions.
eeMETRIC (Google Earth Engine implementation of METRIC): High-resolution energy balance model with internalized calibration. 
    Good at capturing actual ET under stress.
geeSEBAL (Google Earth Engine implementation of SEBAL): Surface energy balance algorithm. 
    Effective for mapping ET across landscapes using thermal and optical data.
PT-JPL (Priestley-Taylor Jet Propulsion Laboratory): Simplified Priestley-Taylor approach. 
    Computationally efficient; originally designed for broader/global applications with fewer assumptions in some components.
SIMS (Satellite Irrigation Management Support): Reflectance-based crop coefficient approach using NDVI and crop type info. 
    Excellent for well-watered agricultural/irrigation contexts.
SSEBop (Operational Simplified Surface Energy Balance): Simplified energy balance model. 
    Operational focus, relatively robust and less computationally intensive.
    
Ensemble: Arithmetic mean of the models after removing outliers (using Median Absolute Deviation/MAD method, keeping at least 4 models). 
This reduces uncertainty, smooths individual biases, and generally outperforms any single model across many metrics and landscapes.
========
Performance for Forests (Evergreen & Mixed)Accuracy 
is lower in forests than in croplands across all models and the ensemble, with higher relative errors (due to lower absolute ET 
rates in natural systems) and greater inter-model variability. 
etdata.org

Key findings from major assessments (e.g., Volk et al. 2024 and related studies):Positive bias (overestimation) is common in 
evergreen and mixed forests. Ensemble bias factor is roughly 1.20–1.25 for monthly data (models range ~1.05–1.35). 
Most models overestimate, especially in evergreen forests:

eeMETRIC often shows the least bias in evergreen forest flux tower sites (e.g., slope closer to 1.0 and lower MBE).
DisALEXI and eeMETRIC sometimes agree better with ground data in mixed forests than the plain ensemble.
PT-JPL tends to have higher errors in evergreen forests.
Ensemble frequently has the best or near-best MAE and RMSE (error magnitude) even in forests, though bias remains an issue. 
It performs well overall for many natural land covers.

Relative errors in forests are higher (e.g., ~35% or more in some assessments) vs. ~10–17% in croplands during growing season. 
Absolute errors (mm) can still be reasonable.
Non-growing season and complex topography/cloudy conditions increase uncertainty for all models.
'''
def account_status(api_key:str):
    header = {"Authorization": api_key}

    resp = requests.get(
        headers=header,
        url="https://openet-api.org/account/status"
    )
    print(resp.json())

def account_storage(api_key:str):
    header = {"Authorization": api_key}

    resp = requests.get(
        headers=header,
        url="https://openet-api.org/account/storage"
    )
    print(resp.json())

def upload_file(api_key:str):
    header = {"Authorization": api_key}

    args = {
        'file': ('PATH/TO/sample.geojson', open('PATH/TO/sample.geojson', 'rb'), 'application/geo+json')
    }

    resp = requests.post(
        headers=header,
        files=args,
        url="https://openet-api.org/account/upload"
    )
    print(resp.json())

def decrypt_file(api_key:str):
    header = {"Authorization": api_key}

    args = {
        'file': ('PATH/TO/encrypted.geojson', open('PATH/TO/encrypted.geojson', 'rb'), 'application/geo+json')
    }

    resp = requests.get(
        headers=header,
        files=args,
        url="https://openet-api.org/account/decrypt"
    )
    print(resp.json())

def raster_timeseries_point(api_key: str, lat:float, lon:float)->Dict:
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2024-01-01",
            "2024-12-31"
        ],
        "interval": "monthly",
        "geometry": [
            lon,
            lat
        ],
        "model": "Ensemble",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm",
        "file_format": "JSON"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/timeseries/point"
    )
    print(resp.json())
    content = {}
    if resp.status_code == 200:
        content = resp.json()
    return content

def geotiff_composite_monthly(api_key: str, gdf: gpd.GeoDataFrame, date_range: List[str]) -> str:
    header = {"Authorization": api_key}

    geom = gdf.geometry.iloc[0]

    # Force single polygon and remove duplicate closing point
    if geom.geom_type == 'MultiPolygon':
        geom = max(geom.geoms, key=lambda g: g.area)

    # Build coordinates WITHOUT the closing duplicate
    geometry = []
    for x, y in list(geom.exterior.coords)[:-1]:  # ← This slice removes the last point
        geometry.extend([round(x, 8), round(y, 8)])

    print(f"Sending {len(geometry) // 2} points")  # Should be 4 for a rectangle

    args = {
        "date_range": date_range,
        # "geometry": [-108.29420188, 37.60804556, -108.29420188, 37.72136553, -108.15115862, 37.72136553, -108.15115862, 37.60804556],
        "geometry": geometry,
        # "model": "ensemble",
        "model": "PTJPL",
        "variable": "ET",
        # "crs": "EPSG:4326",
        "reference_et": "gridMET",
        "reducer": "mean",
        "units": "mm"
    }

    resp = requests.post(
        url="https://openet-api.org/raster/geotiff/composite",
        json=args,
        headers=header
    )

    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        content = resp.json()
        url = content.get("url") or content.get("task_url", "")
        print(f"Task URL: {url}")
        return url
    else:
        print("Error:", resp.text)
        resp.raise_for_status()
        return ""

def download_openet_tiff(
        task_url: str,
        output_path: Path = None,
        poll_interval: int = 10,
        timeout: int = 600
) -> Path:
    if output_path is None:
        output_path = Path(f"openet_{int(time.time())}.tif")
    elif output_path.is_dir():
        output_path = output_path / f"openet_{int(time.time())}.tif"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("Task timed out")

        r = requests.get(task_url, stream=True)

        # If it's binary TIFF (Content-Type image/tiff or direct download)
        if r.headers.get('content-type', '').startswith('image') or len(r.content) > 10000:
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192 * 4):
                    f.write(chunk)
            print(f"✅ Saved directly: {output_path}")
            return output_path

        # Otherwise assume JSON status
        try:
            data = r.json()
            status = data.get('status')
            if status == 'completed':
                dl_url = data.get('download_url') or data.get('url')
                if dl_url:
                    print(f"Downloading from: {dl_url}")
                    with requests.get(dl_url, stream=True) as resp:
                        resp.raise_for_status()
                        with open(output_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=8192 * 4):
                                f.write(chunk)
                    print(f"✅ Saved: {output_path}")
                    return output_path
            elif status in ['failed', 'error']:
                raise Exception(f"Task failed: {data}")
            print(f"Status: {status}... waiting")
        except:
            # If not JSON, treat as direct binary
            with open(output_path, 'wb') as f:
                f.write(r.content)
            print(f"✅ Saved binary: {output_path}")
            return output_path

        time.sleep(poll_interval)

def polygons(api_key:str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2021-01-01",
            "2021-12-31"
        ],
        "interval": "monthly",
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "SIMS",
        "variable": "ETo",
        "reference_et": "gridMET",
        "reducer": "mean",
        "units": "mm",
        "file_format": "JSON"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/timeseries/polygon"
    )
    print(resp.json())

def multi_polygon(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
      "date_range": [
        "2019-01-01",
        "2019-12-31"
      ],
      "interval": "monthly",
      "asset_id": "projects/openet/api_demo_features",
      "attributes": [
        "id"
      ],
      "reducer": "mean",
      "model": "ptJPL",
      "variable": "ET",
      "reference_et": "gridMET",
      "units": "mm"
    }

    # query the api
    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/timeseries/multipolygon"
    )
    print(resp.json())

def download_openet_point_or_rect(
        lat: float,
        lon: float,
        acres: float = None,  # if None → single point, else square
        year_month: str = '2024-07',
        model: str = 'ensemble',
        api_key: str = None,
        output: str = "GeoTIFF"  # "GeoTIFF" or "JSON"
) -> Optional[str]:
    if not api_key:
        raise ValueError("API key required")

    os.makedirs('data/et', exist_ok=True)

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    if acres is None:
        # Point query
        geometry = [lon, lat]
        url = "https://openet-api.org/raster/timeseries/point"
    else:
        # Rectangle (square)
        side_m = math.sqrt(acres * 4046.8564224)
        half = side_m / 2 / 111320
        geometry = [
            [lon - half, lat - half],
            [lon + half, lat - half],
            [lon + half, lat + half],
            [lon - half, lat + half],
            [lon - half, lat - half]
        ]
        url = "https://openet-api.org/raster/timeseries/multipolygon"

    payload = {
        "date_range": [f"{year_month}-01", f"{year_month}-31"],
        "interval": "monthly",
        "geometry": geometry,
        "model": model.capitalize(),  # Ensemble or EEMetric
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm",
        "file_format": output
    }

    print(f"Requesting {year_month} - {acres if acres else 'Point'} acres - {model}")
    resp = requests.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        print("Error:", resp.status_code)
        print(resp.text)
        return None

    data = resp.json()

    if "download_url" in data:
        filename = f"data/et/OpenET_{model}_{year_month.replace('-', '')}_{int(acres) if acres else 'point'}.tif"
        print(f"Downloading → {filename}")

        r = requests.get(data["download_url"])
        with open(filename, 'wb') as f:
            f.write(r.content)
        print("✅ Success!")
        return filename
    else:
        print("Response:", data)
        return data

def geotiff_stack(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2020-01-01",
            "2020-03-31"
        ],
        "interval": "monthly",
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "EEmetric",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/geotiff/stack"
    )
    print(resp.json())

def export_composite(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2018-01-01",
            "2018-06-30"
        ],
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "DisALEXI",
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean",
        "units": "mm",
        "encrypt": False
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/export/composite"
    )
    print(resp.json())

def export_stack(apu_key: str = None):
    header = {"Authorization": apu_key}

    args = {
        "date_range": [
            "2020-01-01",
            "2020-03-31"
        ],
        "interval": "monthly",
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "EEmetric",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm",
        "encrypt": False
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/export/stack"
    )
    print(resp.json())

def export_multipolygon(api_key: str, gdf: gpd.GeoDataFrame, date_range: List[str]) -> str:
    header = {"Authorization": api_key}

    geom = gdf.geometry.iloc[0]
    if geom.geom_type == 'MultiPolygon':
        geom = max(geom.geoms, key=lambda g: g.area)

    # One polygon as list of [lon, lat] pairs, closed
    polygon = []
    for x, y in list(geom.exterior.coords):
        polygon.append([round(x, 8), round(y, 8)])

    args = {
        "date_range": date_range,
        "interval": "monthly",           # Required for this endpoint
        "geometry": [polygon],           # List of polygons (even for one)
        "model": "PTJPL",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm"
        # "file_format": "GeoTIFF"   # May not be needed here
    }

    resp = requests.post(
        url="https://openet-api.org/raster/export/multipolygon",
        json=args,
        headers=header
    )

    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.json())
        return resp.json().get("url") or "Check response for task_url"
    else:
        print("Error:", resp.text)
        return ""

def export_multipolygons(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2019-01-01",
            "2019-12-31"
        ],
        "interval": "monthly",
        "asset_id": "projects/openet/api_demo_features",
        "attributes": [
            "id"
        ],
        "model": "ptJPL",
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean",
        "units": "mm",
        "encrypt": False
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/export/multipolygon"
    )
    print(resp.json())

def export_track(api_key: str = None, tracking_id: str = None):
    header = {"Authorization": api_key}

    args = {
        "tracking_id": tracking_id
    }

    # query the api
    resp = requests.get(
        headers=header,
        params=args,
        url="https://openet-api.org/raster/export/track"
    )
    print(resp.json())

def raster_metadata(api_key: str = None):
    header = {"Authorization": api_key}

    # endpoint arguments
    args = {
        "interval": "monthly",
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "geeSEBAL",
        "variable": "ET",
        "reference_et": "gridMET"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/metadata"
    )
    print(resp.json())

def tile_cache(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2021-10-01",
            "2021-11-05"
        ],
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "Ensemble",
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "sum",
        "units": "mm",
        "resample": 0,
        "gradient": {
            "min": 0,
            "max": 100,
            "palette": [
                "#9e6212",
                "#dcdd45",
                "#44b36c",
                "#2a3f65"
            ]
        }
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/visual/tile_cache"
    )
    print(resp.json())

def animate(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2021-01-01",
            "2021-12-31"
        ],
        "interval": "monthly",
        "geometry": [
            -121.00747,
            44.2442,
            -121.00747,
            44.24742,
            -121.00295,
            44.24742,
            -121.00295,
            44.24422
        ],
        "model": "Ensemble",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm",
        "resample": 0,
        "gradient": {
            "min": 0,
            "max": 100,
            "palette": [
                "#9e6212",
                "#dcdd45",
                "#44b36c",
                "#2a3f65"
            ]
        }
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/visual/animate"
    )
    print(resp.json())

def field_ids(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "geometry": [
            -121.67364,
            38.61593,
            -121.67364,
            38.65611,
            -121.65401,
            38.65611,
            -121.65401,
            38.61593
        ],
        # For old field ID format:
        # "version": 2.0,
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/geodatabase/metadata/ids"
    )
    data = eval(gzip.decompress(resp.content).decode())
    print(data)

def field_properties(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "field_ids": [
            "06183913",
            "06208981"
        ]
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/geodatabase/metadata/properties"
    )
    data = eval(gzip.decompress(resp.content).decode())
    print(data)

def timeseries_by_field_id(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "date_range": [
            "2020-01-01",
            "2020-12-31"
        ],
        "interval": "monthly",
        "field_ids": [
            "06183913",
            "06208981"
        ],
        "models": [
            "Ensemble"
        ],
        "variables": [
            "ET"
        ],
        "file_format": "JSON"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/geodatabase/timeseries"
    )
    data = eval(gzip.decompress(resp.content).decode())
    print(data)

def field_boundaries(api_key: str = None):
    header = {"Authorization": api_key}

    args = {
        "field_ids": [
            "06183913",
            "06208981"
        ]
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/geodatabase/metadata/boundaries"
    )
    data = eval(gzip.decompress(resp.content).decode())
    print(data)


def load_rectangle_csv_to_gdf(file_path:str) -> Tuple[gpd.GeoDataFrame, float]:
    """
    Load rectangle CSV from file, create polygon, and calculate acreage.

    Parameters:
        file_path (str): Path to your CSV file

    Returns:
        gdf (GeoDataFrame): Polygon GeoDataFrame
        area_acres (float): Area in acres
    """
    # Load CSV
    df = pd.read_csv(file_path)

    print(f"✅ Loaded {len(df)} rows from {file_path}")

    # Extract corners in order (removes duplicate closing point)
    corners = df[['lon', 'lat']].drop_duplicates().values.tolist()

    # Create Polygon
    poly = Polygon(corners)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")

    # Calculate accurate area using UTM projection (Zone 12N for this region)
    gdf_utm = gdf.to_crs(epsg=32612)
    area_m2 = gdf_utm.geometry.area[0]
    area_acres = area_m2 / 4046.8564224

    print(f"📏 Rectangle Area: {area_acres:,.2f} acres")

    return gdf, area_acres


def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month/year."""
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    return calendar.monthrange(year, month)[1]

def open_et():
    api_key = os.getenv("OPENET_API_KEY")
    account_status(api_key)

    # study_area_name = 'stoner_mesa'
    study_area_name = 'lizard_head'

    path:str = f'/opt/dev/gis/OpenET/{study_area_name}_study_area.csv'
    # path:str = '/opt/dev/gis/OpenET/lizard_head_study_area.csv'
    df:pd.DataFrame = pd.read_csv(path)
    gdf, area_acres = load_rectangle_csv_to_gdf(path)

    year = 2024
    month = 7
    last_day = days_in_month(year, month)
    date_range = [
        f"{year}-{month:02d}-01",
        f"{year}-{month:02d}-{last_day:02d}"
    ]
    url = geotiff_composite_monthly(api_key, gdf, date_range)
    if url:
        print(f"geotiff_composite_monthly: {date_range} {url}")
        download_openet_tiff(url, Path(f"/opt/dev/gis/OpenET/{study_area_name}/{study_area_name}_{month:02d}_{year}.tiff"))

    # data = openet.raster_timeseries_point(api_key, 37.6080455554, -108.2942018753)

    pass

if __name__ == "__main__":
    # ee.Authenticate()                                 # One time only, usually
    ee.Initialize(project='winter-heat-497923')
    # print(ee.Image('USGS/SRTMGL1_003').getInfo())     # Test image to verify Earth Engine authentication
    open_et()