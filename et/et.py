import ee
import geemap
import os
import math
import rasterio
import wx
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def download_openet_old(lat: float, lon: float, acres: float = 1000,
                    target_date: str = '2024-07-01',
                    model: str = 'eemetric') -> str:
    """
    Download OpenET data for a rectangular area and save it as GeoTIFF.

    Returns: full path to the saved file
    """
    # Create output folder
    os.makedirs('data/et', exist_ok=True)

    # Calculate buffer for square area
    buffer_m = math.sqrt(acres * 4046.8564224) / 2
    point = ee.Geometry.Point(lon, lat)
    rectangle = point.buffer(buffer_m).bounds()

    # Choose collection
    if model.lower() == 'eemetric':
        collection_id = 'projects/openet/assets/eemetric/conus/gridmet/monthly/v2_1'
    elif model.lower() == 'ensemble':
        collection_id = 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0'
    else:
        raise ValueError("model must be 'eemetric' or 'ensemble'")

    # Load image for the month
    img = (ee.ImageCollection(collection_id)
           .filterDate(target_date, ee.Date(target_date).advance(1, 'month'))
           .select('et')
           .first())

    if img is None:
        raise ValueError(f"No OpenET data available for {target_date}")

    # Descriptive filename
    date_str = target_date.replace('-', '')
    filename = f"data/et/OpenET_{model}_et_{date_str}_{int(acres)}acres_lat{lat:.4f}_lon{lon:.4f}.tif"

    print(f"Downloading {acres} acres → {filename}")

    # Download
    geemap.ee_export_image(
        img,
        filename=filename,
        scale=30,
        region=rectangle,
        file_per_band=False,
        crs='EPSG:4326'
    )

    print("✅ Download complete!")
    return filename


import requests
import os
import math


def download_monthly_openet_api(
        lat: float,
        lon: float,
        acres: float = 1000,
        year_month: str = '2024-07',
        model: str = 'ensemble',
        api_key: str = None
) -> str:
    if not api_key:
        raise ValueError("Missing API key")

    os.makedirs('data/et', exist_ok=True)

    side_m = math.sqrt(acres * 4046.8564224)
    half = side_m / 2 / 111320

    geometry = [
        [lon - half, lat - half],
        [lon + half, lat - half],
        [lon + half, lat + half],
        [lon - half, lat + half],
        [lon - half, lat - half]
    ]

    payload = {
        "model": model,
        "date_range": [f"{year_month}-01", f"{year_month}-31"],
        "variable": "et",
        "geometry": geometry,
        "units": "mm",
        "file_format": "GeoTIFF",
        "interval": "monthly",
        "reference_et": "gridMET",
        "reducer": "mean",
        "attributes": [],
        "asset_id": None
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    url = "https://openet-api.org/raster/export/multipolygon"

    print(f"Requesting {year_month} {model}...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("Error:", response.status_code)
        print(response.text)
        return None

    data = response.json()
    print("✅ Request successful!")

    if "download_url" in data:
        filename = f"data/et/OpenET_{model}_{year_month.replace('-', '')}_{int(acres)}acres_lat{lat:.4f}_lon{lon:.4f}.tif"
        print(f"Downloading to {filename}...")

        r = requests.get(data["download_url"])
        with open(filename, 'wb') as f:
            f.write(r.content)
        print("✅ Download complete!")
        return filename
    else:
        print("Response:", data)
        return data


import requests
import os
import math
from pathlib import Path

import requests
import os
import math
from pathlib import Path


def download_openet_monthlyX(
        lat: float,
        lon: float,
        acres: float = None,  # Set to None for single point, or acres for square
        year_month: str = '2024-07',
        model: str = 'Ensemble',  # "Ensemble" or "EEMetric"
        api_key: str = None
) -> str:
    if not api_key:
        raise ValueError("You must provide your API key")

    os.makedirs('data/et', exist_ok=True)

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    # Geometry
    if acres is None:
        # Point query (simplest)
        geometry = [lon, lat]
        url = "https://openet-api.org/raster/timeseries/point"
    else:
        # Square around point
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
        "model": model,
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm",
        "file_format": "GeoTIFF"
    }

    print(f"Requesting {year_month} {model}...")
    resp = requests.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        print(f"❌ Error {resp.status_code}")
        print(resp.text)
        return None

    data = resp.json()

    if "download_url" in data:
        filename = f"data/et/OpenET_{model}_{year_month.replace('-', '')}_{int(acres) if acres else 'point'}.tif"
        print(f"Downloading → {filename}")

        r = requests.get(data["download_url"])
        with open(filename, 'wb') as f:
            f.write(r.content)
        print("✅ Download complete!")
        return filename
    else:
        print("Response:", data)
        return data


def download_monthly_openet_api_old(
        lat: float,
        lon: float,
        acres: float = 1000,
        year_month: str = '2024-07',
        model: str = 'ensemble',
        api_key: str = None
) -> str:
    if not api_key:
        raise ValueError("Please pass your OpenET API key")

    os.makedirs('data/et', exist_ok=True)

    # Square geometry around center
    side_m = math.sqrt(acres * 4046.8564224)
    half_deg = (side_m / 2) / 111320

    geometry = [
        [lon - half_deg, lat - half_deg],
        [lon + half_deg, lat - half_deg],
        [lon + half_deg, lat + half_deg],
        [lon - half_deg, lat + half_deg],
        [lon - half_deg, lat - half_deg]
    ]

    payload = {
        "model": model,
        "date_range": [f"{year_month}-01", f"{year_month}-31"],
        "variable": "et",
        "geometry": geometry,
        "units": "mm",
        "file_format": "GeoTIFF",
        "interval": "monthly",  # ← Required
        "reference_et": "gridMET",  # ← Required
        "reducer": "mean",  # ← Required
        "attributes": [],  # ← Required (can be empty)
        "asset_id": None  # ← Required (can be null for simple requests)
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    url = "https://openet-api.org/raster/timeseries/multipolygon"

    print(f"Requesting {year_month} {model} data...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    print("✅ Request accepted!")

    if "download_url" in data:
        download_url = data["download_url"]
        filename = f"data/et/OpenET_{model}_{year_month.replace('-', '')}_{int(acres)}acres_lat{lat:.4f}_lon{lon:.4f}.tif"

        print(f"Downloading file → {filename}")
        r = requests.get(download_url)
        with open(filename, 'wb') as f:
            f.write(r.content)

        print("✅ File successfully downloaded!")
        return filename
    else:
        print("Response:", data)
        return data

def download_monthly_openet(lat: float, lon: float, acres: float = 1000,
                            year_month: str = '2024-07',
                            model: str = 'ensemble'):
    os.makedirs('data/et', exist_ok=True)

    buffer_m = math.sqrt(acres * 4046.8564224) / 2
    point = ee.Geometry.Point(lon, lat)
    rectangle = point.buffer(buffer_m).bounds()

    if model.lower() == 'eemetric':
        collection_id = 'projects/openet/assets/eemetric/conus/gridmet/monthly/v2_1'
        band_name = 'et'
    else:
        collection_id = 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1'
        band_name = 'et_ensemble_mad'

    if len(year_month) == 7:
        target_date = f"{year_month}-01"
    else:
        target_date = year_month

    start = ee.Date(target_date)
    img = (ee.ImageCollection(collection_id)
           .filterDate(start, start.advance(1, 'month'))
           .select(band_name)
           .first())

    if img is None:
        raise ValueError("No image found")

    print(f"Image date: {img.date().format('YYYY-MM-dd').getInfo()}")

    # Try multiple scales to detect any data
    for scale in [30, 100, 500, 1000]:
        stats = img.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=rectangle,
            scale=scale,
            maxPixels=1e12,
            bestEffort=True
        ).getInfo()

        minv = stats.get(f'{band_name}_min')
        maxv = stats.get(f'{band_name}_max')
        print(f"  Scale {scale}m → Min: {minv} | Max: {maxv}")

    # Download anyway (even if masked, so you can visually confirm)
    date_str = year_month.replace('-', '')
    filename = f"data/et/OpenET_{model}_monthly_{date_str}_{int(acres)}acres_lat{lat:.4f}_lon{lon:.4f}.tif"

    print(f"\nDownloading to: {filename}")
    geemap.ee_export_image(img, filename=filename, scale=30, region=rectangle, crs='EPSG:4326')
    print("✅ Downloaded. Open the .tif — is it all black/zero?")

    return filename

def download_openet_diagnostic(lat: float, lon: float, acres: float = 1000,
                               target_date: str = '2024-04-01',
                               model: str = 'ensemble'):
    os.makedirs('data/et', exist_ok=True)

    buffer_m = math.sqrt(acres * 4046.8564224) / 2
    point = ee.Geometry.Point(lon, lat)
    rectangle = point.buffer(buffer_m).bounds()

    if model.lower() == 'eemetric':
        collection_id = 'projects/openet/assets/eemetric/conus/gridmet/monthly/v2_1'
        band_name = 'et'
    else:
        collection_id = 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1'
        band_name = 'et_ensemble_mad'

    start = ee.Date(target_date)
    coll = ee.ImageCollection(collection_id).filterDate(start, start.advance(1, 'month')).select(band_name)

    img = coll.first()

    print(f"Image exists: {img is not None}")
    if img:
        print(f"Image date: {img.date().format('YYYY-MM-dd').getInfo()}")
        print(f"Bands: {img.bandNames().getInfo()}")

    # Try different scales and reducers for diagnostics
    for scale in [30, 100, 500]:
        stats = img.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=rectangle,
            scale=scale,
            maxPixels=1e12
        ).getInfo()

        print(f"Scale {scale}m → Min: {stats.get(f'{band_name}_min')} | Max: {stats.get(f'{band_name}_max')}")

    # If still bad, try the raw image without reduceRegion
    sample = img.sample(region=rectangle, scale=100, numPixels=10).getInfo()
    print(f"Sample pixels found: {len(sample['features']) if sample else 0}")

    # Fallback to eeMETRIC if needed
    if model == 'ensemble':
        print("Trying eeMETRIC fallback...")
        img = (ee.ImageCollection('projects/openet/assets/eemetric/conus/gridmet/monthly/v2_1')
               .filterDate(start, start.advance(1, 'month'))
               .select('et')
               .first())

def load_and_display_in_notebook(filename: str,
                                 notebook: wx.Notebook,
                                 tab_name: str = None,
                                 max_scale_factor: float = 3.0):
    """
    Load OpenET GeoTIFF and display it scaled to nicely fill the notebook tab.
    """
    # === Load raster data ===
    with rasterio.open(filename) as src:
        data = src.read(1).astype(np.float32)
        bounds = src.bounds
        mean_et = float(data.mean())
        orig_height, orig_width = data.shape

        # Normalize
        data_min, data_max = data.min(), data.max()
        norm = np.clip((data - data_min) / (data_max - data_min + 1e-8), 0, 1)

    # Viridis colormap
    cmap = plt.get_cmap('viridis')
    rgb = (cmap(norm)[:, :, :3] * 255).astype(np.uint8)

    # Create tab name
    if tab_name is None:
        tab_name = Path(filename).stem[:55]

    # Create panel
    panel = wx.Panel(notebook)
    main_sizer = wx.BoxSizer(wx.VERTICAL)

    # Create base wx.Image
    wx_image = wx.Image(orig_width, orig_height)
    wx_image.SetData(rgb.tobytes())

    # StaticBitmap (we'll update it later)
    static_bitmap = wx.StaticBitmap(panel, bitmap=wx.NullBitmap)

    # Info text
    info_text = f"Mean ET: {mean_et:.2f} mm\n" \
                f"Original: {orig_width} × {orig_height} pixels\n" \
                f"Range: {data_min:.1f} – {data_max:.1f} mm"

    info = wx.StaticText(panel, label=info_text)
    info.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

    main_sizer.Add(static_bitmap, 0, wx.CENTER | wx.ALL, 8)
    main_sizer.Add(info, 0, wx.CENTER | wx.ALL, 8)

    panel.SetSizer(main_sizer)

    # === Scaling Function ===
    def update_image():
        panel_width, panel_height = panel.GetClientSize()
        if panel_width < 50 or panel_height < 50:
            # Use a reasonable default size if panel not ready
            panel_width, panel_height = 800, 600

        panel_width -= 40
        panel_height -= 140

        scale_x = panel_width / orig_width
        scale_y = panel_height / orig_height
        scale = min(max_scale_factor, max(scale_x, scale_y))

        new_w = max(100, int(orig_width * scale))
        new_h = max(100, int(orig_height * scale))

        scaled = wx_image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
        static_bitmap.SetBitmap(wx.Bitmap(scaled))
        panel.Layout()

    # Initial display
    wx.CallAfter(update_image)        # Important: run after panel is realized

    # Bind resize
    def on_resize(event):
        update_image()
        event.Skip()

    panel.Bind(wx.EVT_SIZE, on_resize)

    # Add to notebook
    notebook.AddPage(panel, tab_name, select=True)
    print(f"✅ Added tab with scaled image: {tab_name}")

    return data

import rasterio
import wx
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


def load_and_display_in_notebook_debug(filename: str,
                                 notebook: wx.Notebook,
                                 tab_name: str = None,
                                 max_scale_factor: float = 3.0):
    """
    Load OpenET GeoTIFF with improved visualization for mountainous regions.
    """
    with rasterio.open(filename) as src:
        data = src.read(1).astype(np.float32)
        bounds = src.bounds
        mean_et = float(data.mean())
        orig_height, orig_width = data.shape

        # === DIAGNOSTICS ===
        print(f"\n=== {Path(filename).name} ===")
        print(f"Min ET : {data.min():.2f} mm")
        print(f"Max ET : {data.max():.2f} mm")
        print(f"Mean ET: {mean_et:.2f} mm")
        print(f"Low ET pixels (<10mm): {(data < 10).sum() / data.size * 100:.1f}%")

        # Normalize with fixed scale (better for mountains)
        vmin = 0
        vmax = 180                    # Good summer range for high elevation
        norm = np.clip((data - vmin) / (vmax - vmin + 1e-8), 0, 1)

    # Better colormap for ET in complex terrain
    cmap = plt.get_cmap('plasma')     # Good contrast on low values
    # Alternatives: 'YlOrRd', 'viridis', 'magma', 'coolwarm'

    rgb = (cmap(norm)[:, :, :3] * 255).astype(np.uint8)

    # Tab name
    if tab_name is None:
        tab_name = Path(filename).stem[:60]

    # Create panel
    panel = wx.Panel(notebook)
    main_sizer = wx.BoxSizer(wx.VERTICAL)

    # Create wx Image
    wx_image = wx.Image(orig_width, orig_height)
    wx_image.SetData(rgb.tobytes())

    static_bitmap = wx.StaticBitmap(panel, bitmap=wx.NullBitmap)

    # Info text
    info_text = f"Mean ET: {mean_et:.2f} mm\n" \
                f"Range: {data.min():.1f} – {data.max():.1f} mm\n" \
                f"Size: {orig_width} × {orig_height} pixels"

    info = wx.StaticText(panel, label=info_text)
    info.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

    main_sizer.Add(static_bitmap, 0, wx.CENTER | wx.ALL, 10)
    main_sizer.Add(info, 0, wx.CENTER | wx.ALL, 8)

    panel.SetSizer(main_sizer)

    # Scaling function
    def update_image():
        pw, ph = panel.GetClientSize()
        if pw < 100 or ph < 100:
            pw, ph = 1000, 700

        pw -= 50
        ph -= 160

        scale_x = pw / orig_width
        scale_y = ph / orig_height
        scale = min(max_scale_factor, max(scale_x, scale_y))

        new_w = max(200, int(orig_width * scale))
        new_h = max(200, int(orig_height * scale))

        scaled = wx_image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
        static_bitmap.SetBitmap(wx.Bitmap(scaled))
        panel.Layout()

    # Show image after panel is ready
    wx.CallAfter(update_image)

    # Resize handler
    def on_resize(event):
        update_image()
        event.Skip()

    panel.Bind(wx.EVT_SIZE, on_resize)

    # Add to notebook
    notebook.AddPage(panel, tab_name, select=True)
    print(f"✅ Added tab: {tab_name}\n")

    return data

def et_init():
    # ee.Authenticate()
    ee.Initialize(project='winter-heat-497923')