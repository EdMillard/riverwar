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
import json
import math
import time
import gzip
from pathlib import Path
import pandas as pd
import geopandas as gpd
from typing import Optional, Tuple, Dict, List
import ee
from shapely.geometry import Polygon
from json import JSONDecodeError
from bs4 import BeautifulSoup
from colorado.river_war import RiverWar
import re
from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# ====================== OAUTH SETUP ======================
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('/opt/dev/riverwar/client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)



# OpemET API testing:
#   https://openet-api.org/
#   https://etdata.org
#
openet_file_dir:str = "/opt/dev/gis/OpenET/"

'''
"model"
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

"variable": "ET" This is the main output you want.
"ET" = Actual Evapotranspiration (the total water lost to the atmosphere from soil evaporation + plant transpiration).

    Core Variables:
    ET — Actual Evapotranspiration (the main one — total water lost from soil + plants)
    ETo — Reference Evapotranspiration (standardized "potential" ET for grass)
    ETR — Alfalfa Reference ET (another reference standard)
    NDVI — Normalized Difference Vegetation Index (vegetation greenness)
    PET — Potential Evapotranspiration
    
    Other Available Variables:
    EToF — Fraction of Reference ET (how much of potential ET is actually happening)
    ETR F — Fraction of Alfalfa Reference ET
    Precip — Precipitation (from gridMET or other sources)
    SoilMoisture — Surface soil moisture estimates (in some endpoints)
    LST — Land Surface Temperature (raw input)

"reference_et": "gridMET"This tells the models what reference evapotranspiration dataset to use for scaling or comparison.
gridMET is the default and most commonly used (gridded weather data covering the western U.S.).
Other options: "CIMIS" (California only), "FRET" (forecast), etc.

"reducer": "mean"How to aggregate pixel values when your geometry covers multiple pixels.
"mean" = Average value across all pixels in your rectangle/polygon (most common and recommended).
Other options: "sum", "max", "min", etc.

"crs": "EPSG:4326",  Geometry should always be EPSG:4326, tiffs returned are always 5070, this is only used in special cases
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

def raster_timeseries_point(api_key: str, lat:float, lon:float,
                            date_range:List[str], model:str='ensemble', units:str="in", interval:str="daily")->Dict:
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
        "geometry": [
            lon,
            lat
        ],
        "model": model,
        "units": units,
        "interval": interval,
        "variable": "ET",
        "reference_et": "gridMET",
        "file_format": "JSON"
    }
    if interval == "monthly":
        args["include_count"] = True    # type: ignore

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

def gdf_to_geometry(gdf:gpd.GeoDataFrame)->List[str]:
    geom = gdf.geometry.iloc[0]

    # Force single polygon and remove duplicate closing point
    if geom.geom_type == 'MultiPolygon':
        geom = max(geom.geoms, key=lambda g: g.area)

    # Build coordinates WITHOUT the closing duplicate
    geometry = []
    for x, y in list(geom.exterior.coords)[:-1]:  # ← This slice removes the last point
        geometry.extend([round(x, 8), round(y, 8)])

    print(f"Sending {len(geometry) // 2} points")  # Should be 4 for a rectangle

    return geometry

def geotiff_composite_monthly(api_key:str, gdf:gpd.GeoDataFrame,
                              date_range:List[str], model:str='ensemble', units:str="in") -> str:
    header = {"Authorization": api_key}
    geometry = gdf_to_geometry(gdf)
    args = {
        "date_range": date_range,
        "geometry": geometry,
        "model": model,
        "units": units,
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean",
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
            print(f"✅ Raster saved: {output_path}")
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
        except (JSONDecodeError, TypeError, KeyError, AttributeError):
            # Direct binary download (common for some task URLs)
            with open(output_path, 'wb') as f:
                f.write(r.content)
            print(f"✅ Saved binary: {output_path}")
            return output_path

        except Exception as e:
            # Only catch unexpected errors
            print(f"Unexpected error: {e}")
            raise

        time.sleep(poll_interval)

def polygons(api_key:str,
             date_range:List[str], model:str='ensemble', units:str="in"):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
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
        "model": model,
        "units": units,
        "variable": "ETo",
        "reference_et": "gridMET",
        "reducer": "mean",
        "file_format": "JSON"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/timeseries/polygon"
    )
    print(resp.json())

def multi_polygon(api_key: str,
                  date_range: List[str], model: str = 'ensemble', units: str = "in"):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
        "interval": "monthly",
        "asset_id": "projects/openet/api_demo_features",
        "attributes": [
        "id"
        ],
        "model": model,
        "units": units,
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean"
    }

    # query the api
    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/timeseries/multipolygon"
    )
    print(resp.json())

def download_openet_point_or_rect(api_key: str,
        lat: float,
        lon: float,
        date_range:List[str],
        acres: float = None,  # if None → single point, else square
        model: str = 'ensemble',
        units: str = "in",
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
        "date_range": date_range,
        "interval": "monthly",
        "geometry": geometry,
        "model": model.capitalize(),  # Ensemble or EEMetric
        "variable": "ET",
        "reference_et": "gridMET",
        "units": units,
        "file_format": output
    }

    print(f"Requesting {date_range} - {acres if acres else 'Point'} acres - {model}")
    resp = requests.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        print("Error:", resp.status_code)
        print(resp.text)
        return None

    data = resp.json()

    if "download_url" in data:
        filename = f"data/et/OpenET_{model}_{date_range[0].replace('-', '')}_{int(acres) if acres else 'point'}.tif"
        print(f"Downloading → {filename}")

        r = requests.get(data["download_url"])
        with open(filename, 'wb') as f:
            f.write(r.content)
        print("✅ Success!")
        return filename
    else:
        print("Response:", data)
        return data

def geotiff_stack(api_key:str,
                  date_range:List[str], model:str='ensemble', units:str="in"):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
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
        "model": model,
        "units": units,
        "interval": "monthly",
        "variable": "ET",
        "reference_et": "gridMET",
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/geotiff/stack"
    )
    print(resp.json())

def export_composite(api_key:str,
                     date_range:List[str], model:str='ensemble', units:str="in"):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
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
        "model": model,
        "units": units,
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean",
        "encrypt": False
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/export/composite"
    )
    print(resp.json())

def extract_folder_id(drive_url: str) -> str:
    """Extract folder ID from various Google Drive folder URL formats."""
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',  # Standard /folders/ID
        r'/drive/folders/([a-zA-Z0-9_-]+)',  # Full drive URL
        r'id=([a-zA-Z0-9_-]+)',  # ?id=ID
    ]

    for pattern in patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1)
    raise ValueError("Could not extract folder ID from the provided URL.")


def debug_list_google_drive_files(tid: str, drive_api_key: str):
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": f"name contains '{tid}' and trashed=false",
        "key": drive_api_key,
        "fields": "files(id, name, mimeType)",
        "pageSize": 100
    }
    response = requests.get(url, params=params)

    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(response.text[:500])
        return

    files = response.json().get('files', [])
    print(f"Found {len(files)} files containing '{tid}':")
    for f in files:
        print(f"   • {f.get('name')} ({f.get('mimeType')})")

def list_google_drive_files_by_name(name_fragment: str, drive_service):
    results = drive_service.files().list(
        q=f"name contains '{name_fragment}' and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])

def list_files_in_drive_folder(drive_url: str, credentials=None, api_key: str = None):
    """
    List files in a Google Drive folder.

    Args:
        drive_url (str): Google Drive folder URL
        credentials: OAuth2 Credentials object (recommended for private/shared folders)
        api_key (str, optional): API key for public folders (limited access)

    Returns:
        list: List of dicts with file info (id, name, mimeType, webViewLink, etc.)
    """
    folder_id = extract_folder_id(drive_url)
    print(f"📁 Extracted Folder ID: {folder_id}")

    if credentials:
        service = build('drive', 'v3', credentials=credentials)
    elif api_key:
        service = build('drive', 'v3', developerKey=api_key)
    else:
        raise ValueError("Provide either OAuth credentials or an API key.")

    files = []
    page_token = None

    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, webViewLink, size, modifiedTime)",
            pageSize=1000,
            pageToken=page_token,
            # For shared drives:
            # supportsAllDrives=True,
            # includeItemsFromAllDrives=True,
            # corpora='drive',
            # driveId=...  # if using shared drive
        ).execute()

        files.extend(results.get('files', []))
        page_token = results.get('nextPageToken')

        if not page_token:
            break

    return files


def list_folder(url, exclude_pattern="image")->List:
    """Lists files from public Google Drive folder, excluding names with pattern"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    files = []
    for item in soup.find_all(attrs={"data-id": re.compile(r"^[0-9A-Za-z_-]{28,}$")}):
        name_tag = item.find(string=re.compile(r'\S'))
        if name_tag:
            name = name_tag.strip()
            if re.search(exclude_pattern, name, re.IGNORECASE):
                continue  # Skip files with "Image" in name

            file_id = item['data-id']
            files.append({
                "name": name,
                "id": file_id,
                "url": f"https://drive.google.com/file/d/{file_id}/view"
            })

    if not files:
        print("No files found after filtering (or folder requires sign-in).")

    return files

def poll_and_download_stack(
    tracking: dict,
    openet_api_key: str,
    drive_service,               # ← OAuth service
    name: str,
    output_dir: Path = Path(".")
) -> bool:
    header = {"Authorization": openet_api_key}
    output_dir.mkdir(parents=True, exist_ok=True)

    for date, info in list(tracking.items()):
        tid = info.get("tracking_id")
        if not tid:
            continue

        print(f"Polling {date}...")

        for _ in range(60):
            resp = requests.get(
                f"https://openet-api.org/raster/export/track?tracking_id={tid}",
                headers=header
            )

            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                if status == "SUCCEEDED":
                    # Search using service
                    tracking_name = info.get("name")
                    files = list_google_drive_files_by_name(tracking_name, drive_service)
                    for file in files:
                        file_name = file.get("name", "")
                        if file_name and tracking_name in file_name:
                            file_id = file.get('id', "")
                            r = drive_service.files().get_media(fileId=file_id).execute()
                            if len(r) > 10000:   # basic size check
                                output_path = output_dir / file_name.replace("OpenET Exports/", f"{name}_")
                                with open(output_path, 'wb') as f:
                                    f.write(r)
                                print(f"✅ Raster saved: {output_path}")
                                tracking.pop(date, None)
                                break
                    break
            time.sleep(10)
        else:
            print(f"Timeout for {date}")

    return len(tracking) == 0


def find_file_by_name(name_fragment: str, drive_service):
    """Search by name fragment"""
    results = drive_service.files().list(
        q=f"name contains '{name_fragment}' and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])

def export_stack(
    api_key: str,
    gdf: gpd.GeoDataFrame,
    date_range: List[str],
    model: str = "ensemble",
    units: str = "in",
    poll_interval: int = 15,
    timeout: int = 600
) -> Dict[str, str]:
    """
    Export OpenET Stack (multi-month) and return dict of month -> download URL or file path.
    """
    header = {"Authorization": api_key}

    geometry = gdf_to_geometry(gdf)  # your existing function

    args = {
        "date_range": date_range,
        "geometry": geometry,
        "model": model,
        "variable": "ET",
        "reference_et": "gridMET",
        "interval": "monthly",
        "units": units,
        "encrypt": False
    }

    resp = requests.post(
        url="https://openet-api.org/raster/export/stack",
        json=args,
        headers=header
    )

    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print("Error:", resp.text)
        resp.raise_for_status()

    data = resp.json()
    tracking = data.get("tracking", {}) or data  # sometimes it's flat

    print("Tracking IDs received:", tracking)

    return tracking

def export_multipolygon(api_key: str, gdf: gpd.GeoDataFrame,
                        date_range: List[str], model: str = 'ensemble', units: str = "in") -> str:
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
        "geometry": [polygon],           # List of polygons (even for one)
        "model": model,
        "units": units,
        "interval": "monthly",  # Required for this endpoint
        "variable": "ET",
        "reference_et": "gridMET",
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

def export_multipolygons(api_key: str,
                         date_range: List[str], model: str = 'ensemble', units: str = "in"):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
        "asset_id": "projects/openet/api_demo_features",
        "attributes": [
            "id"
        ],
        "model": model,
        "units": units,
        "interval": "monthly",
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "mean",
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

def raster_metadata(api_key: str, model: str = 'ensemble'):
    header = {"Authorization": api_key}

    # endpoint arguments
    args = {
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
        "model": model,
        "interval": "monthly",
        "variable": "ET",
        "reference_et": "gridMET"
    }

    resp = requests.post(
        headers=header,
        json=args,
        url="https://openet-api.org/raster/metadata"
    )
    print(resp.json())

def tile_cache(api_key: str,
               date_range: List[str], model: str = 'ensemble', units: str = "in"):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
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
        "model": model,
        "units": units,
        "variable": "ET",
        "reference_et": "gridMET",
        "reducer": "sum",
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

def animate(api_key: str):
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

def field_ids(api_key: str):
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

def field_properties(api_key: str):
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

def timeseries_by_field_id(api_key: str,
                           date_range: List[str], model: str = 'ensemble'):
    header = {"Authorization": api_key}

    args = {
        "date_range": date_range,
        "interval": "monthly",
        "field_ids": [
            "06183913",
            "06208981"
        ],
        "models": [
            model
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

def field_boundaries(api_key: str):
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

def load_study_area(name:str) -> gpd.GeoDataFrame:
    path:str = f'{openet_file_dir}{name}_study_area.csv'
    # df:pd.DataFrame = pd.read_csv(path)
    gdf, area_acres = load_rectangle_csv_to_gdf(path)
    return gdf

def build_date_range(start_year, start_month:int, end_year:int, end_month:int)->List[str]:
    last_day = days_in_month(end_year, end_month)
    date_range = [
        f"{start_year}-{start_month:02d}-01",
        f"{end_year}-{end_month:02d}-{last_day:02d}"
    ]
    return date_range

def get_composite_monthly(api_key:str, name:str, gdf:gpd.GeoDataFrame):
    year = 2026
    month = 2
    last_day = days_in_month(year, month)
    date_range = [
        f"{year}-{month:02d}-01",
        f"{year}-{month:02d}-{last_day:02d}"
    ]
    # On forest Ensemble has double lobe histogram from low models and high models, needs 0.75-0.8 correction
    # model = "ensemble"
    # On forest DisALEXI is low and eeMetric is high, the average may be OK
    model = 'eeMETRIC'
    # model = 'DisALEXI'
    # Ob forest this tends to be the low one
    # model = "PTJPL"

    units = "in"
    url = geotiff_composite_monthly(api_key, gdf, date_range, model=model, units=units)
    if url:
        print(f"download geotiff_composite_monthly: {name} {date_range} {model} {units}")
        download_openet_tiff(url, Path(f"{openet_file_dir}{name}/{name}_{month:02d}_{year}_{model}_{units}.tiff"))


def get_export_stack(api_key: str, google_drive_service, name: str, gdf: gpd.GeoDataFrame):
    date_range = build_date_range(2026, 1, 2026, 6)
    # On forest Ensemble has double lobe histogram from low models and high models, needs 0.75-0.8 correction
    # model = "ensemble"
    # On forest DisALEXI is low and eeMetric is high, the average may be OK
    # model = 'eeMETRIC'
    model = 'DisALEXI'
    # Ob forest this tends to be the low one
    # model = "PTJPL"

    units = "in"
    tracking = export_stack(api_key, gdf, date_range, model=model, units=units)
    if tracking:
        path = Path(f"{openet_file_dir}{name}/")
        print(f"get stack: {path}")
        poll_and_download_stack(tracking, api_key, google_drive_service,  name, output_dir=path)

def get_timeseries_point(api:str, name:str, model:str):
    # Ob forest this tends to be the low one
    # model = "PTJPL"
    date_range = build_date_range(2016, 8, 2026, 6)
    interval = 'daily'
    units = 'in'

    output_path = Path(f"{openet_file_dir}{name}")
    output_path = output_path / f"{name}_{date_range[0]}_{date_range[1]}_{model}_{units}_{interval}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = raster_timeseries_point(api, 37.6080455554, -108.2942018753, date_range, model, units, interval)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path


def get_gee_timeseries_point(
        lon: float,
        lat: float,
        start_date: str = "2000-01-01",
        end_date: str = "2025-12-31",
        model: str = "ensemble",  # "ensemble", "eemetric", "ptjpl", "ssebop", etc.
        variable: str = "et",  # "et", "et_reference", etc.
        scale: int = 30
) -> pd.DataFrame:
    """
    Get OpenET time series for a point using Google Earth Engine.
    Works for monthly data back to ~2000 (or earlier depending on model).
    """

    point = ee.Geometry.Point([lon, lat])

    # Choose the collection
    if model.lower() == "ensemble":
        collection_id = "projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1"
    elif model.lower() == "eemetric":
        collection_id = "projects/openet/assets/eemetric/conus/gridmet/monthly/v2_1"
    else:
        # Add more models as needed
        collection_id = f"projects/openet/assets/{model}/conus/gridmet/monthly/v2_1"

    collection = (ee.ImageCollection(collection_id)
                  .filterDate(start_date, end_date)
                  .select(variable))

    # Reduce to point
    def image_to_feature(img):
        value = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=scale,
            maxPixels=1e9
        ).get(variable)

        return ee.Feature(None, {
            'date': img.date().format('YYYY-MM-dd'),
            variable: value
        })

    features = collection.map(image_to_feature)

    # Get the data
    data = features.getInfo()['features']

    # Convert to DataFrame
    df = pd.DataFrame([f['properties'] for f in data])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # Rename to match your earlier format
    df = df.rename(columns={'date': 'Date', variable: 'et'})

    return df


# =========================
# Example Usage
# =========================
'''
df = get_gee_timeseries_point(
    lon=-121.36322,
    lat=38.87626,
    start_date="2010-01-01",
    end_date="2016-12-31",
    model="ensemble",
    variable="et"
)
print(df.head(10))
print(f"\nTotal records: {len(df)}")
df.to_csv("openet_historical.csv", index=False)
'''


def openet_json_file_to_dataframe(
        file_path: str | Path,
        existing_df: pd.DataFrame | None = None,
        model_col_prefix: str = None
) -> pd.DataFrame:
    """
    Load OpenET point data from a JSON file and convert/merge into a pandas DataFrame.

    Parameters:
        file_path: Path to the JSON file
        existing_df: Optional existing DataFrame with 'Date' column to merge into
        model_col_prefix: Optional override for column name. If None, extracted from filename.

    Returns:
        DataFrame with 'Date' and model-specific ET column (e.g. 'DisALEXI', 'eeMETRIC')
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Read the JSON file
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of dictionaries at the root level.")

    if not data:
        return existing_df if existing_df is not None else pd.DataFrame(columns=['Date'])

    # Convert to DataFrame
    df_new = pd.DataFrame(data)

    # Rename 'time' → 'Date'
    if 'time' in df_new.columns:
        df_new = df_new.rename(columns={'time': 'Date'})
    else:
        raise KeyError("Column 'time' not found in the JSON data.")

    # Convert to datetime
    df_new['Date'] = pd.to_datetime(df_new['Date'])

    # Extract model name from filename if not provided
    if model_col_prefix is None:
        # Extract from filename like: ..._DisALEXI_in_daily.json
        stem = path.stem
        match = re.search(r'_([A-Za-z0-9]+?)(?:_in|_daily|_monthly|$)', stem)
        model_col_prefix = match.group(1) if match else "ET"

    # Rename 'et' to the model name
    if 'et' in df_new.columns:
        df_new = df_new.rename(columns={'et': model_col_prefix})
    else:
        # If no 'et' column, assume the model column already exists or use first numeric column
        numeric_cols = df_new.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            df_new = df_new.rename(columns={numeric_cols[0]: model_col_prefix})

    # Sort new data
    df_new = df_new.sort_values('Date').reset_index(drop=True)

    # Merge with existing DataFrame if provided
    if existing_df is not None:
        if 'Date' not in existing_df.columns:
            raise ValueError("existing_df must have a 'Date' column")

        existing_df = existing_df.copy()
        existing_df['Date'] = pd.to_datetime(existing_df['Date'])

        merged = pd.merge(
            existing_df,
            df_new[['Date', model_col_prefix]],
            on='Date',
            how='left'
        )
        return merged
    else:
        return df_new

if __name__ == "__main__":
    river_war = RiverWar()
    # ee.Authenticate()                                 # One time only, usually
    ee.Initialize(project='winter-heat-497923')
    # print(ee.Image('USGS/SRTMGL1_003').getInfo())     # Test image to verify Earth Engine authentication

    # Lizard head SNOTEL
    # '37.799991'
    # '-107.933968'
    #
    # El Diente SNOTEL
    # "37.79"
    # '-108.02'
    #

    api = os.getenv("OPENET_API_KEY")
    # google_drive_api_key = os.getenv("GOOGLE_DRIVE_API_KEY")
    # google_drive_service = get_drive_service()

    account_status(api)

    # study_area_name = 'stoner_mesa'
    study_area_name = 'lizard_head'
    study_area_gdf = load_study_area(study_area_name)

    # get_omposite_monthly(api, study_area_name, study_area_gdf)
    '''
    tracking = {'2026-01-01': {'tracking_id': 'ULEGBBUGAIHDKDT7MTAGWDWE', 'encrypted': False, 'name': 'a040b', 'destination': 'drive'},
                '2026-02-01': {'tracking_id': '4FYQAXBVYAKRLWUTEYODRJBR', 'encrypted': False, 'name': 'a965f', 'destination': 'drive'},
                '2026-03-01': {'tracking_id': 'JWQQZXZETFQWTY5KC7OA64X7', 'encrypted': False, 'name': 'e2a10', 'destination': 'drive'},
                '2026-04-01': {'tracking_id': 'RCIBOB54H6L2LIHUALFGOEYB', 'encrypted': False, 'name': '73763', 'destination': 'drive'},
                '2026-05-01': {'tracking_id': 'DAGCX4P6WMQW6BWTGAQMQYIS', 'encrypted': False, 'name': '22a56', 'destination': 'drive'},
                '2026-06-01': {'tracking_id': 'JWA3X743IRQQNEH6MVMUOQMB', 'encrypted': False, 'name': '36b75', 'destination': 'drive'}}

    output_path = Path(f"{openet_file_dir}{study_area_name}/")
    poll_and_download_stack(tracking, api, google_drive_service, study_area_name, output_path)
    '''
    # get_export_stack(api, google_drive_service, study_area_name, study_area_gdf)

    # On forest Ensemble has double lobe histogram from low models and high models, needs 0.75-0.8 correction
    model = "ensemble"
    # On forest DisALEXI is low and eeMetric is high, the average may be OK
    # model = 'eeMETRIC'
    # model = 'DisALEXI'
    path = get_timeseries_point(api, "lizard_head", model)

