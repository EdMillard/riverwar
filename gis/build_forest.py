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
from pathlib import Path
import importlib
import sys
import os
from qgis.core import QgsVectorLayer, QgsProject
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
from osgeo import ogr
import processing   # type: ignore

script_paths = ["/opt/dev/riverwar"]
for p in script_paths:
    if p not in sys.path:
        sys.path.append(p)
        print(f"Added to Python path: {p}")

def reload_modules():
    modules_to_reload = [
        'gis.make_forest_layers',
        'gis.forest_type',
        'gis.contours',
        'gis.layers',
    ]
    for mod in modules_to_reload:
        if mod in sys.modules:
            importlib.reload(sys.modules[mod])
            print(f"✅ Reloaded {mod}")
        else:
            print(f"⚠️  {mod} not loaded yet")
reload_modules()

from gis.layer import remove_layer, reset_qgis, get_symbol, ensure_crs, load_vector_layer, clip_to_mask
from gis.contours import build_elevation_layers
from gis.make_forest_layers import build_forest_layers
reset_qgis()

# ====================== GLOBAL PROJECT SETTINGS ======================
# TARGET_CRS = "EPSG:5070"
TARGET_CRS = "EPSG:4269"

base_path:Path = Path("/opt/dev/gis/")
huc8_name =  "Upper Dolores"
huc8_dir_name = "HUC8" + '_' + huc8_name.replace(" ", "_")
forestry_dir = base_path / huc8_dir_name
forestry_dir.mkdir(parents=True, exist_ok=True)

def load_huc8_from_wbd(gpkg_path: str, huc_name: str = None, huc8_code: str = None):
    """
    Load HUC8 from the USGS WBD_14_HU2_GPKG file.

    Examples:
        load_huc8_from_wbd("/path/to/WBD_14_HU2_GPKG.gpkg", huc_name="Upper Dolores")
        load_huc8_from_wbd(..., huc8_code="14080101")
    """
    if not os.path.exists(gpkg_path):
        raise FileNotFoundError(f"GPKG not found: {gpkg_path}")

    # The standard HUC8 layer name in USGS WBD GeoPackages
    layer_name = "WBDHU8"

    full_layer_path = f"{gpkg_path}|layername={layer_name}"
    huc_layer = QgsVectorLayer(full_layer_path, "HUC8", "ogr")

    if not huc_layer.isValid():
        print("❌ Failed to load WBDHU8 layer. Available layers:")
        # List all layers in the geopackage for debugging
        layers = QgsVectorLayer(gpkg_path, "temp", "ogr").dataProvider().subLayers()
        for l in layers:
            print("   ", l)
        return None

    # Optional: Filter to a specific HUC8
    if huc_name or huc8_code:
        expression = None
        if huc_name:
            expression = f'"Name" = \'{huc_name}\''
        elif huc8_code:
            expression = f'"HUC8" = \'{huc8_code}\''

        if expression:
            huc_layer.selectByExpression(expression)
            if huc_layer.selectedFeatureCount() > 0:
                # Create a new layer from selection
                params = {
                    'INPUT': huc_layer,
                    'OUTPUT': 'memory:Filtered_HUC8'
                }
                result = processing.run("native:saveselectedfeatures", params)
                huc_layer = result['OUTPUT']
                huc_layer.setName(huc_name or huc8_code)
            else:
                print(f"⚠️ No HUC8 found matching {huc_name or huc8_code}")

    # Basic styling
    symbol = get_symbol(huc_layer)
    symbol.setColor(QColor(40, 40, 40))
    huc_layer.setOpacity(0.65)

    QgsProject.instance().addMapLayer(huc_layer)
    print(f"✅ Loaded HUC8 layer: {huc_layer.name()} ({huc_layer.featureCount()} features)")
    return huc_layer

def extract_and_reproject_huc8(wbd_layer, huc_name: str):
    """
    Takes the big WBD HUC8 layer, keeps only the named HUC8,
    reprojects it to TARGET_CRS, and returns a clean single-feature layer named "HUC8".
    """
    if wbd_layer is None:
        print("❌ No WBD layer provided")
        return None

    print(f"Extracting HUC: '{huc_name}' from {wbd_layer.featureCount()} features...")

    # Select the desired HUC
    expression = f'"Name" = \'{huc_name}\''
    wbd_layer.selectByExpression(expression)

    selected_count = wbd_layer.selectedFeatureCount()
    if selected_count == 0:
        print(f"❌ No HUC8 found with name '{huc_name}'")
        return None
    if selected_count > 1:
        print(f"⚠️ Found {selected_count} features matching '{huc_name}' — using first one")

    # Save only the selected feature
    params = {
        'INPUT': wbd_layer,
        'OUTPUT': 'memory:Single_HUC8'
    }
    result = processing.run("native:saveselectedfeatures", params)
    single_huc = result['OUTPUT']

    # === ENSURE TARGET CRS + clean name ===
    final_layer = ensure_crs(forestry_dir, TARGET_CRS, single_huc, "HUC8")

    # Style
    symbol = get_symbol(final_layer)
    symbol.setColor(QColor(40, 40, 40))
    final_layer.setOpacity(0.65)

    QgsProject.instance().addMapLayer(final_layer)

    print(f"✅ Successfully created: HUC8 ({TARGET_CRS}, {final_layer.featureCount()} features)")

    return final_layer

def extract_huc12_in_huc8(wbd_gpkg_path: str, huc_name: str):
    """
    Extract HUC12s belonging to a HUC8 and ensure they are in TARGET_CRS.
    """
    huc8_path = f"{wbd_gpkg_path}|layername=WBDHU8"
    huc12_path = f"{wbd_gpkg_path}|layername=WBDHU12"

    huc8_layer = QgsVectorLayer(huc8_path, "WBDHU8", "ogr")
    huc12_layer = QgsVectorLayer(huc12_path, "WBDHU12", "ogr")

    if not huc8_layer.isValid() or not huc12_layer.isValid():
        print("❌ Failed to load HUC8 or HUC12 layer")
        return None

    # Get HUC8 code
    huc8_layer.selectByExpression(f'"Name" = \'{huc_name}\'')
    if huc8_layer.selectedFeatureCount() == 0:
        print(f"❌'{huc_name}' not found")
        return None

    feature = next(huc8_layer.getSelectedFeatures())
    huc8_code = feature["HUC8"]
    print(f"Found'{huc_name}' → Code: {huc8_code}")

    # Select matching HUC12s
    expression = f'"huc12" LIKE \'{huc8_code}%\''
    huc12_layer.selectByExpression(expression)

    count = huc12_layer.selectedFeatureCount()
    print(f"Found {count} HUC12 features for {huc_name}")

    if count == 0:
        print("⚠️ No matching HUC12s found.")
        return None

    # Save selected features
    params = {
        'INPUT': huc12_layer,
        'OUTPUT': 'memory:HUC12_subset'
    }
    result = processing.run("native:saveselectedfeatures", params)
    huc12_subset = result['OUTPUT']

    # Clean naming (no redundant HUC name)
    huc12_subset.setName("HUC12s")

    # === ENSURE TARGET CRS ===
    final_layer = ensure_crs(forestry_dir, TARGET_CRS, huc12_subset, "HUC12s")

    # Style
    symbol = get_symbol(final_layer)
    symbol.setColor(QColor(0, 100, 200))
    final_layer.setOpacity(0.45)

    QgsProject.instance().addMapLayer(final_layer)
    print(f"✅ Final HUC12 layer ready: HUC12s ({final_layer.featureCount()} features)")

    return final_layer

def load_gpkg_with_ogr(gpkg_path: str, layer_name: str, display_name: str = None):
    gpkg_path = Path(gpkg_path)

    ds = ogr.Open(str(gpkg_path))
    if ds is None:
        print(f"❌ Failed to open {gpkg_path}")
        return None

    ogr_layer = ds.GetLayerByName(layer_name)
    if ogr_layer is None:
        print(f"❌ Layer '{layer_name}' not found")
        return None

    print(f"✅ OGR loaded {ogr_layer.GetFeatureCount()} features from '{layer_name}'")

    # Create QGIS layer
    qgis_layer = QgsVectorLayer(
        f"{gpkg_path}|layername={layer_name}",
        display_name or layer_name,
        "ogr"
    )

    if qgis_layer.isValid():
        QgsProject.instance().addMapLayer(qgis_layer)
        print(f"✅ Added to QGIS: {qgis_layer.name()}")
        return qgis_layer
    else:
        print("❌ QGIS layer is invalid")
        return None

def build_hydrology():
    nhd_gpkg_path = "/opt/dev/gis/NHD/NHD_H_14030002_HU8_GPKG.gpkg"

    water_body_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDWaterbody")
    symbol = get_symbol(water_body_layer)
    symbol.setColor(QColor(64, 64, 255))

    river_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDArea")
    symbol = get_symbol(river_layer)
    symbol.symbolLayer(0).setStrokeColor(QColor(64, 64, 255))
    symbol.symbolLayer(0).setStrokeWidth(0.4)

def build_weather_stations(huc8_layer):
    temp_weather_station_layer = load_vector_layer("/opt/dev/gis/CO_DWR/ClimateStationPOR.zip", "Teno Weather Stations", QColor(0, 0, 0))
    weather_station_layer, weather_station_path = clip_to_mask(temp_weather_station_layer, huc8_layer, forestry_dir, "Weather Stations")
    remove_layer(temp_weather_station_layer)
    weather_station_layer.setOpacity(1.0)
    symbol = get_symbol(weather_station_layer)
    if symbol:
        symbol.setColor(QColor(255, 0, 0))
        symbol.setSize(2)
        symbol.setOpacity(0.9)

def build(huc_name:str):
    wbd_huc8 = load_huc8_from_wbd("/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg")  # Load Upper Colorado HU2, HUC8
    huc8_layer = extract_and_reproject_huc8(wbd_huc8, huc_name)
    remove_layer(wbd_huc8)
    huc12_layer = extract_huc12_in_huc8('/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg', huc_name)

    build_forest_layers(forestry_dir, huc8_layer, huc_name)

    build_elevation_layers(forestry_dir, huc8_layer)

    build_hydrology()

    build_weather_stations(huc8_layer)

    return huc8_layer

print(f"\n=== Starting {huc8_name} Build ===")
huc8_layer = build(huc8_name)
if huc8_layer and huc8_layer.isValid():
    extent = huc8_layer.extent()
    # extent.scale(1.12)  # Slightly larger view
    canvas = iface.mapCanvas()  # type: ignore[attr-defined]
    canvas.setExtent(extent)
    canvas.refresh()
else:
    print("⚠️ Could not zoom to HUC8")