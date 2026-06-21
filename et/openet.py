import requests
import os
import math
import gzip
import pandas as pd
import geopandas as gpd
from pandas.core.interchange.dataframe_protocol import DataFrame
from shapely.geometry import Polygon
from typing import Optional, Tuple, Dict


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

def geotiff_composite_monthly(api_key: str, gdf:gpd.GeoDataFrame)->str:
    header = {"Authorization": api_key}

    geom = gdf.geometry.iloc[0]  # or gdf.geometry[0] if it's a Series
    geometry = []
    for x, y in list(geom.exterior.coords)[:-1]:  # ← slice off the last (duplicate) point
        geometry.extend([round(x, 8), round(y, 8)])
    '''
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
    '''
    args = {
        "date_range": [
            "2025-05-01",
            "2025-06-30"
        ],
        "geometry": geometry,
        "model": "PTJPL",
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean",
        "units": "mm"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/geotiff/composite"
    )
    print(resp.json())
    url = ""
    if resp.status_code == 200:
        content = resp.json()
        url = content.get("url", "")
    return url

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
