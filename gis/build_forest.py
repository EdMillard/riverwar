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
from typing import Optional, List
from qgis.core import QgsVectorLayer, QgsProject, QgsRasterLayer, QgsProcessingException, QgsFeature, QgsProcessingFeedback
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
from PyQt5.QtCore import QDate, QDateTime
import datetime
from collections import defaultdict
import processing   # type: ignore

# https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/GovtUnit/
# https://data-usfs.hub.arcgis.com/datasets/usfs::national-interagency-fire-occurrence-sixth-edition-1992-2020-feature-layer/about
# https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.6
#

script_paths = ["/opt/dev/riverwar"]
for p in script_paths:
    if p not in sys.path:
        sys.path.append(p)
        print(f"Added to Python path: {p}")

def reload_modules():
    print("Reload Modules")
    modules_to_reload = [
        'gis.layer',
        'gis.make_forest_layers',
        'gis.forest_type',
        'gis.contours',
        'gis.wildfires',
        'et.openet',
    ]
    for mod in modules_to_reload:
        if mod in sys.modules:
            importlib.reload(sys.modules[mod])
            print(f"✅ Reloaded {mod}")
        else:
            print(f"⚠️  {mod} not loaded yet")
    print("Modules Loaded")
reload_modules()

from gis.layer import remove_layer, reset_qgis, get_symbol, ensure_crs, load_vector_layer, clip_to_mask, create_group, \
    add_layer_to_group, remove_features_by_attribute_fast, load_gpkg_with_ogr, force_collapse, force_group_visibility, \
    load_gdb_layer
from gis.contours import build_elevation_layers
from gis.make_forest_layers import build_forest_layers, build_tree_map_layers, build_open_et_layers
from gis.wildfire import build_wildfires

# ====================== GLOBAL PROJECT SETTINGS ======================
# TARGET_CRS = "EPSG:5070"
TARGET_CRS = "EPSG:4269"
wbd_gpkg_path = '/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg'

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

def extract_huc12_in_huc8(gpkg_path: str, huc_name: str):
    """
    Extract HUC12s belonging to a HUC8 and ensure they are in TARGET_CRS.
    """
    huc8_path = f"{gpkg_path}|layername=WBDHU8"
    huc8_layer = QgsVectorLayer(huc8_path, "WBDHU8", "ogr")
    huc12_path = f"{gpkg_path}|layername=WBDHU12"
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

def build_hydrology()->list:
    layers = []
    nhd_gpkg_path = "/opt/dev/gis/NHD/NHD_H_14030002_HU8_GPKG.gpkg"

    group = create_group("Hydrology", position=0)

    water_body_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDWaterbody", group=group)
    symbol = get_symbol(water_body_layer)
    symbol.setColor(QColor(165, 191, 221))
    layers.append(water_body_layer)

    river_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDArea", group=group)
    symbol = get_symbol(river_layer)
    symbol.symbolLayer(0).setStrokeColor(QColor(60, 60, 221))
    symbol.symbolLayer(0).setStrokeWidth(0.4)
    layers.append(river_layer)

    flow_line_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDFlowline", group=group)
    remove_features_by_attribute_fast(flow_line_layer, "gnis_name")
    symbol = get_symbol(flow_line_layer)
    symbol.setColor(QColor(60, 60, 221))
    layers.append(flow_line_layer)

    return layers

def build_weather_stations(huc8_layer):
    temp_weather_station_layer = load_vector_layer("/opt/dev/gis/CO_DWR/ClimateStationPOR.zip", "Teno Weather Stations", QColor(255, 0, 0))
    weather_station_layer, weather_station_path = clip_to_mask(temp_weather_station_layer, huc8_layer, forestry_dir, "Weather Stations")
    remove_layer(temp_weather_station_layer)
    weather_station_layer.setOpacity(1.0)
    symbol = get_symbol(weather_station_layer)
    if symbol:
        symbol.setColor(QColor(255, 0, 0))
        symbol.setSize(2)
        symbol.setOpacity(0.9)

def clip_to_mask_fast(source_layer, mask_layer, project_dir, output_name):
    """
    Fast clipping using spatial index.\
    This is fussier on geometry errors and not sure it's faster
    """
    if source_layer is None or mask_layer is None:
        print("❌ Invalid input layer")
        return None, None

    output_path = os.path.join(project_dir, f"{output_name}_clipped.gpkg")

    # Use 'native:clip' with better parameters or fallback to intersection
    params = {
        'INPUT': source_layer,
        'OVERLAY': mask_layer,
        'OUTPUT': output_path
    }

    print(f"Clipping {source_layer.featureCount():,} features... (this may take a while)")

    try:
        result = processing.run("native:clip", params, feedback=QgsProcessingFeedback())
        clipped_layer = QgsVectorLayer(output_path, output_name, "ogr")

        if clipped_layer.isValid():
            print(f"✅ Clipped successfully: {clipped_layer.featureCount():,} features")
            QgsProject.instance().addMapLayer(clipped_layer)
            return clipped_layer, output_path
        else:
            print("❌ Clipped layer is invalid")
            return None, None
    except Exception as e:
        print(f"❌ Clipping error: {e}")
        return None, None

def fix_geometries(layer):
    """Fix invalid geometries in a layer."""
    if layer is None or not layer.isValid():
        print("❌ Invalid layer")
        return None

    params = {
        'INPUT': layer,
        'OUTPUT': 'memory:Fixed_' + layer.name()
    }

    result = processing.run("native:fixgeometries", params)
    fixed_layer = result['OUTPUT']

    print(f"✅ Fixed geometries. Original features: {layer.featureCount()}, Fixed: {fixed_layer.featureCount()}")
    return fixed_layer

def _parse_date(val):
    """Handles QDate, QDateTime, strings, etc."""
    if isinstance(val, QDate):
        return val.toPyDate()

    if isinstance(val, QDateTime):
        date_part = val.date()
        return date_part.toPyDate() if not date_part.isNull() else None

    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val

    if isinstance(val, str):
        clean = val.split('(')[0].strip()
        formats = [
            '%m/%d/%y %H:%M:%S', '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d',
            '%m/%d/%y', '%m/%d/%Y'
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(clean, fmt).date()
            except ValueError:
                continue
    return None

def split_layer_by_date(layer:QgsVectorLayer,
                        date_field:str='DATE_COMPLETED',
                        fallback_field:str='DATE_AWARDED',
                        divider_dates:Optional[list]=None,
                        base_name=None)->Optional[List[QgsVectorLayer]]:
    """
    Split layer by date with proper bin/label alignment. Handles QDateTime safely.
    """
    if layer is None or not layer.isValid():
        print("❌ Invalid input layer")
        return []

    if base_name is None:
        base_name = layer.name()

    # Collect valid dates
    dates = []
    for feat in layer.getFeatures():
        val = feat[date_field] or feat[fallback_field]
        d = _parse_date(val)
        if d:
            dates.append(d)

    if not dates:
        print(f"❌ No valid dates found in '{date_field}' or '{fallback_field}'")
        return []

    min_date = min(dates)
    max_date = max(dates)

    # === Define bins ===
    if divider_dates is None:
        # Decade bins
        start_year = (min_date.year // 10) * 10
        end_year = ((max_date.year // 10) * 10) + 10

        bin_starts = [datetime.date(y, 1, 1) for y in range(start_year, end_year + 11, 10)]
        bin_labels = [f"{y}s" for y in range(start_year, end_year + 11, 10)]  # Fixed: same length as starts
    else:
        # Custom dividers
        bin_starts = []
        for d in divider_dates:
            parsed = _parse_date(d)
            if parsed:
                bin_starts.append(parsed)
        bin_starts = sorted(set(bin_starts))
        bin_labels = [d.strftime('%Y') for d in bin_starts]

    # Build bin ranges (last bin goes to far future)
    bins = []
    for i in range(len(bin_starts)):
        start = bin_starts[i]
        end = bin_starts[i + 1] if i + 1 < len(bin_starts) else datetime.date(9999, 12, 31)
        label = bin_labels[i] if i < len(bin_labels) else f"{start.year}s"
        bins.append((start, end, label))

    # Group features
    grouped = defaultdict(list)
    for feat in layer.getFeatures():
        val = feat[date_field] or feat[fallback_field]
        d = _parse_date(val)
        if not d:
            continue
        for start, end, label in bins:
            if start <= d < end:
                grouped[label].append(feat)
                break

    # Create layers (newest → oldest with fading opacity)
    created_layers = []
    sorted_bins = sorted(bins, key=lambda x: x[0], reverse=True)
    n = len(sorted_bins)

    for i, (start, end, label) in enumerate(sorted_bins):
        features = grouped.get(label, [])
        if not features:
            continue

        opacity = 1.0 - (i / max(n - 1, 1) * 0.9) if n > 1 else 1.0

        new_layer = QgsVectorLayer("Polygon", f"{base_name} {label}", "memory")
        new_layer.setCrs(layer.crs())
        provider = new_layer.dataProvider()
        provider.addAttributes(layer.fields())
        new_layer.updateFields()

        for feat in features:
            new_feat = QgsFeature(new_layer.fields())
            new_feat.setGeometry(feat.geometry())
            new_feat.setAttributes(feat.attributes())
            provider.addFeature(new_feat)

        new_layer.updateExtents()
        new_layer.setOpacity(opacity)

        QgsProject.instance().addMapLayer(new_layer)
        created_layers.append(new_layer)

        print(f"✅ Created: {base_name} {label} | Features: {len(features):,} | Opacity: {opacity:.2f}")

    print(f"\n✅ Split complete. {len(created_layers)} layers created.")
    return created_layers


def load_vector_layer_masked(name: str, path: str, mask_layer:QgsVectorLayer, project_dir: Path,
                             color: QColor = QColor(100, 255, 100))->Optional[QgsVectorLayer]:
    """
    Load vector layer (shapefile, GDB, GeoPackage, etc.) and clip to mask.
    Uses a cached .gpkg version if available.
    """
    if not path or not os.path.exists(path):
        print(f"❌ Path does not exist: {path}")
        return None

    os.makedirs(project_dir, exist_ok=True)

    clipped_name = f"{name}.gpkg"
    clipped_path = os.path.join(project_dir, clipped_name)

    # === Try cached clipped version ===
    if os.path.exists(clipped_path):
        print(f"🔄 Found cached: {clipped_name}")
        vector_layer = QgsVectorLayer(clipped_path, name, "ogr")
        if vector_layer.isValid() and vector_layer.featureCount() > 0:
            print(f"✅ Loaded cached layer: {name} ({vector_layer.featureCount():,} features)")
            QgsProject.instance().addMapLayer(vector_layer)
            return vector_layer
        else:
            print("⚠️ Cached file invalid or empty → will re-clip")

    # === Load original ===

    if ".gdb" in path.lower() or "gdb.":
        print(f"🔄 Loading gdb: {name} {path} {path.lower()}")
        temp_layer = load_gdb_layer(path, name)  # assume this exists elsewhere
    else:
        print(f"🔄 Loading shape file: {name} {path} {path.lower()}")
        temp_layer = QgsVectorLayer(path, f"Temp_{name}", "ogr")

    if not temp_layer or not temp_layer.isValid():
        print(f"❌ Failed to load original layer: {name}")
        return None

    print(f"   Original: {temp_layer.featureCount():,} features")

    # Fix geometries
    try:
        fixed = processing.run("native:fixgeometries", {
            'INPUT': temp_layer,
            'OUTPUT': 'memory:Fixed'
        })['OUTPUT']
        print(f"   Fixed geometries: {fixed.featureCount():,} features")
    except Exception:
        fixed = temp_layer
        print("   Geometry fixing skipped")

    # Clip to mask
    try:
        print("   Clipping to mask...")
        result = processing.run("native:clip", {
            'INPUT': fixed,
            'OVERLAY': mask_layer,
            'OUTPUT': clipped_path
        })
        vector_layer = QgsVectorLayer(clipped_path, name, "ogr")

        if vector_layer.isValid() and vector_layer.featureCount() > 0:
            print(f"✅ Clipped & saved: {vector_layer.featureCount():,} features")
            QgsProject.instance().addMapLayer(vector_layer)
            return vector_layer
        else:
            print("❌ Clipped layer invalid or empty")
    except QgsProcessingException as e:
        print(f"❌ Clipping failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during clip: {e}")

    # Cleanup temporary layer
    if 'temp_layer' in locals() and temp_layer and temp_layer != fixed:
        try:
            remove_layer(temp_layer)  # assume you have this helper
        except Exception:
            pass

    return None

def build_disturbance(project_dir:Path, huc_layer:QgsVectorLayer):
    timber_harvest_layer = load_vector_layer_masked("Actv_TimberHarvest", "/opt/dev/gis/USFS/Actv_TimberHarvest.gdb",
                                                   huc_layer, project_dir, QColor(180, 0, 180))
    layers = split_layer_by_date(timber_harvest_layer)

    # hazard_fuel_treatment_layer = load_vector_layer_masked("Actv_HazFuelTrt_PL", "/opt/dev/gis/USFS/Actv_HazFuelTrt_PL.gdb",
    #                                                huc_layer, project_dir, QColor(180, 0, 180))

    # silva_reforest_treatment_layer = load_vector_layer_masked("Actv_SilvReforest", "/opt/dev/gis/USFS/Actv_SilvReforest/S_USA.Actv_SilvReforest.shp",
    #                                                huc_layer, project_dir, QColor(0, 180, 0))

    # protected_area_layer = load_vector_layer_masked("Protected Areas", "/opt/dev/gis/PAD/PADUS4_1Designation_StateCO.kmz",
    #                                                huc_layer, project_dir, QColor(100, 255, 100))

    # small_fire_layer = load_vector_layer_masked("Fires", "/opt/dev/gis/USFS/RDS-2013-0009.6_Data_Format2_GDB.zip",
    #                                                 huc_layer, project_dir, QColor(0, 180, 0))

    # build_wildfires()


def build(huc_name:str):
    # co_counties = load_vector_layer('/opt/dev/gis/Gov/GOVTUNIT_Colorado_State_Shape.zip', 'GU_CountyOrEquivalent.shp', QColor(140, 0, 140))

    huc2_path = f"{wbd_gpkg_path}|layername=WBDHU2"
    huc2_layer = QgsVectorLayer(huc2_path, "Upper Colorado", "ogr")
    QgsProject.instance().addMapLayer(huc2_layer)

    huc4_path = f"{wbd_gpkg_path}|layername=WBDHU4"
    huc4_layer = QgsVectorLayer(huc4_path, "WBDHU4", "ogr")
    QgsProject.instance().addMapLayer(huc4_layer)
    symbol = get_symbol(huc4_layer)
    symbol.setColor(QColor(60, 60, 60))

    wbd_huc8 = load_huc8_from_wbd("/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg")  # Load Upper Colorado HU2, HUC8
    huc8_layer = extract_and_reproject_huc8(wbd_huc8, huc_name)
    remove_layer(wbd_huc8)
    huc12_layer = extract_huc12_in_huc8(wbd_gpkg_path, huc_name)
    symbol = get_symbol(huc12_layer)
    symbol.setColor(QColor(200, 200, 150))

    # build_forest_layers(forestry_dir, huc8_layer, huc_name)

    # build_open_et_layers(forestry_dir, huc8_layer, huc12_layer)

    tree_map_layers = build_tree_map_layers(forestry_dir, huc8_layer, huc4_layer)

    build_disturbance(forestry_dir, huc8_layer)

    # build_elevation_layers(forestry_dir, huc8_layer)

    hydrology_layers = build_hydrology()

    build_weather_stations(huc8_layer)

    tree_map_group = create_group("TreeMap 2022", position=0, existing_layer=huc12_layer, layer_dict=tree_map_layers)
    hydrology_group = create_group("NHD Hydrology", visible=True, position=0, existing_layer=huc12_layer, layers=hydrology_layers)
    force_group_visibility(hydrology_group)



    layer:Optional[QgsRasterLayer, None] = tree_map_layers.get('FLDTYPCD', None)
    if layer is not None:
        force_collapse(layer)

    return huc8_layer

reset_qgis()

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