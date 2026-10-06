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
import requests
from typing import Optional, List
from qgis.core import (QgsVectorLayer, QgsProject, QgsRasterLayer)
from qgis.PyQt.QtGui import QColor
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
        'et.openet',
        'gis.dem'
    ]
    for mod in modules_to_reload:
        if mod in sys.modules:
            importlib.reload(sys.modules[mod])
            print(f"✅ Reloaded {mod}")
        else:
            print(f"⚠️  {mod} not loaded yet")
    print("Modules Loaded")
reload_modules()

import gis.layer as gis_layer
from gis.layer import remove_layer, reset_qgis, get_symbol, ensure_crs, load_vector_layer, clip_to_mask, create_group, \
    remove_features_by_attribute_fast, load_gpkg_with_ogr, force_collapse, \
    load_vector_layer_masked, split_layer_by_date, reset_layer_parent_to_root
from gis.contours import build_elevation_layers
from gis.make_forest_layers import build_forest_layers, build_tree_map_layers, build_open_et_layers, build_zenodo_layers
from gis.dem import build_dem_from_huc

# ====================== GLOBAL PROJECT SETTINGS ======================
# TARGET_CRS = "EPSG:5070"
TARGET_CRS = "EPSG:4269"
wbd_gpkg_path = '/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg'

base_path:Path = Path("/opt/dev/gis/")
huc8_name =  "Upper Dolores"
# huc8_name =  "Upper Gunnison"
# huc8_name =  "Uncompahgre"
# huc8_name =  "San Miguel"
# huc8_name =  "Animas"

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

def extract_and_reproject_huc8(wbd_layer, huc_name: str)->tuple[Optional[QgsVectorLayer], str]:
    """
    Takes the big WBD HUC8 layer, keeps only the named HUC8,
    reprojects it to TARGET_CRS, and returns a clean single-feature layer named "HUC8".
    """
    if wbd_layer is None:
        print("❌ No WBD layer provided")
        return None, ""

    print(f"Extracting HUC: '{huc_name}' from {wbd_layer.featureCount()} features...")

    # Select the desired HUC
    expression = f'"Name" = \'{huc_name}\''
    wbd_layer.selectByExpression(expression)

    selected_count = wbd_layer.selectedFeatureCount()
    if selected_count == 0:
        print(f"❌ No HUC8 found with name '{huc_name}'")
        return None, ""
    if selected_count > 1:
        print(f"⚠️ Found {selected_count} features matching '{huc_name}' — using first one")
    feature = wbd_layer.selectedFeatures()[0]
    huc8 = feature['huc8']
    print(f"Found {huc_name} {huc8}")

    # Save only the selected feature
    params = {
        'INPUT': wbd_layer,
        'OUTPUT': f'memory:{huc_name}'
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

    return final_layer, huc8

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

def build_hydrology(huc8: str) -> list:
    layers = []

    nhd_base: Path = Path("/opt/dev/gis/NHD/")
    nhd_base.mkdir(parents=True, exist_ok=True)

    zip_filename = f"NHD_H_{huc8}_HU8_GPKG.zip"
    local_zip_path = nhd_base / zip_filename  # corrected path

    url = f"https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU8/GPKG/{zip_filename}"

    # === Download if file doesn't exist ===
    if not local_zip_path.exists():
        print(f"📥 Downloading {zip_filename} ...")
        try:
            r = requests.get(url, stream=True, timeout=120)
            r.raise_for_status()

            with open(local_zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192 * 4):
                    f.write(chunk)
            print(f"✅ Downloaded: {local_zip_path}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return layers
    else:
        print(f"✅ Using cached file: {local_zip_path}")

    # === Load and style layers ===

    # 1. Waterbodies
    water_body_layer = load_gpkg_with_ogr(str(local_zip_path), "NHDWaterbody", f"{huc8} - Waterbodies")
    if water_body_layer:
        symbol = get_symbol(water_body_layer)
        symbol.setColor(QColor(165, 191, 221))
        layers.append(water_body_layer)

    # 2. NHDArea (rivers/lakes polygons)
    river_layer = load_gpkg_with_ogr(str(local_zip_path), "NHDArea", f"{huc8} - Rivers/Areas")
    if river_layer:
        symbol = get_symbol(river_layer)
        symbol.symbolLayer(0).setStrokeColor(QColor(60, 60, 221))
        symbol.symbolLayer(0).setStrokeWidth(0.4)
        layers.append(river_layer)

    # 3. Flowlines
    flow_line_layer = load_gpkg_with_ogr(str(local_zip_path), "NHDFlowline", f"{huc8} - Flowlines")
    if flow_line_layer:
        # After loading the flow_line_layer
        print("Original flowlines:", flow_line_layer.featureCount())

        # Create filtered layer (keep only named ones)
        filtered_layer = processing.run("native:extractbyexpression", {
            'INPUT': flow_line_layer,
            'EXPRESSION': '"gnis_name" IS NOT NULL AND "gnis_name" != \'\'',
            'OUTPUT': 'memory:NHDFlowline_Major'
        })['OUTPUT']

        print("Filtered to named flowlines:", filtered_layer.featureCount())

        # Add the filtered layer to the project
        QgsProject.instance().addMapLayer(filtered_layer)
        remove_layer(flow_line_layer)

        # Style it
        symbol = get_symbol(filtered_layer)
        symbol.setColor(QColor(60, 60, 221))

        layers.append(filtered_layer)

    print(f"✅ build_hydrology completed for HUC8 {huc8} — {len(layers)} layers loaded")
    return layers

def build_weather_stations(huc8_layer):
    temp_weather_station_layer = load_vector_layer("/opt/dev/gis/CO_DWR/ClimateStationPOR.zip", "Temp Weather Stations", QColor(255, 0, 0))
    weather_station_layer, weather_station_path = clip_to_mask(temp_weather_station_layer, huc8_layer, forestry_dir, "Weather Stations")
    remove_layer(temp_weather_station_layer)
    weather_station_layer.setOpacity(1.0)
    symbol = get_symbol(weather_station_layer)
    if symbol:
        symbol.setColor(QColor(0, 255, 255))
        symbol.setSize(1.5)
        symbol.setOpacity(0.9)


def build_wildfires(huc_layer=None, project_dir: Path = None)->List[QgsVectorLayer]:
    # https://data-nifc.opendata.arcgis.com/search?tags=historic_wildlandfire_opendata%2CCategory
    # WFIGS
    # https://data-nifc.opendata.arcgis.com/datasets/5e72b1699bf74eefb3f3aff6f4ba5511_0/explore?location=39.663857%2C-107.050782%2C8
    # https://data.usgs.gov/datacatalog/data/USGS:61aa537dd34eb622f699df81

    # Current fires
    # https://data-nifc.opendata.arcgis.com/datasets/nifc::wfigs-current-interagency-fire-perimeters/about

    layers = []

    # Very latest perimeters
    layer = load_vector_layer_masked(
        name="Wildfires Current",
        path='/opt/dev/gis/wildfire/WFIGS_Interagency_Perimeters_Current_-6952035509289917377.gdb.zip',
        mask_layer=huc_layer,
        project_dir=project_dir,
        color=QColor(255, 128, 0),
        layer_name="Perimeters"  # ← pass it here when needed
    )
    if layer:
        layers.append(layer)
    else:
        print("build WFIGS_Interagency_Perimeters_Current failed")

    # Recent perimeters
    layer = load_vector_layer_masked(
        name="Wildfires Recent",
        path='/opt/dev/gis/wildfire/WFIGS_Interagency_Perimeters_-6137106134146866405.gpkg',
        mask_layer=huc_layer,
        project_dir=project_dir,
        color=QColor(255, 0, 0),
        layer_name="Perimeters",
    )
    if layer:
        layers.append(layer)
    else:
        print("build WFIGS_Interagency_Perimeters failed")

    # Historical
    layer = load_vector_layer_masked(
        name="InteragencyFirePerimeterHistory",
        path='/opt/dev/gis/wildfire/InterAgencyFirePerimeterHistory_All_Years_View_5907997263350188958.gpkg',
        mask_layer=huc_layer,
        project_dir=project_dir,
        color=QColor(200, 0, 0)
    )
    if layer:
        layers.append(layer)
    else:
        print("build InterAgencyFirePerimeterHistory_All_Years failed")

    create_group("Fire", visible=True, position=0, existing_layer=huc_layer, layers=layers)

    return layers

def build_disturbance(project_dir:Path, huc_layer:QgsVectorLayer)->List[QgsVectorLayer]:

    layers = []
    layer = load_vector_layer_masked("Actv_HazFuelTrt_PL", "/opt/dev/gis/USFS/Actv_HazFuelTrt_PL.gdb",
                                                   huc_layer, project_dir, QColor(180, 0, 180))
    if layer:
        layers.append(layer)
    else:
        print("build Actv_HazFuelTrt_PL failed")

    layer = load_vector_layer_masked("Actv_SilvReforest", "/opt/dev/gis/USFS/Actv_SilvReforest/S_USA.Actv_SilvReforest.shp",
                                                   huc_layer, project_dir, QColor(0, 180, 0))
    if layer:
        layers.append(layer)
    else:
        print("build Actv_SilvReforest failed")

    # layer = load_vector_layer_masked("Fires", "/opt/dev/gis/USFS/RDS-2013-0009.6_Data_Format2_GDB.zip",
    #                                                  huc_layer, project_dir, QColor(0, 180, 0))
    # layers.append(layer)
    create_group("Disturbance", visible=True, position=0, existing_layer=huc_layer, layers=layers)

    timber_harvest_layer = load_vector_layer_masked("Actv_TimberHarvest", "/opt/dev/gis/USFS/Actv_TimberHarvest.gdb",
                                                   huc_layer, project_dir, QColor(180, 0, 180))
    if timber_harvest_layer:
        layers = split_layer_by_date(timber_harvest_layer)
        for layer in layers:
            symbol = get_symbol(layer)
            symbol.symbolLayer(0).setStrokeWidth(0.4)
        layers.append(timber_harvest_layer)
        create_group("Timber Harvest", visible=True, position=0, existing_layer=huc_layer, layers=layers)
    else:
        print("build Actv_TimberHarvest failed")


    build_wildfires(huc_layer, project_dir)

    return layers

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

    # huc6_path = f"{wbd_gpkg_path}|layername=WBDHU6"
    # huc6_layer = QgsVectorLayer(huc6_path, "WBDHU6", "ogr")
    # QgsProject.instance().addMapLayer(huc6_layer)
    # symbol = get_symbol(huc6_layer)
    # symbol.setColor(QColor(90, 90, 90))

    wbd_huc8 = load_huc8_from_wbd("/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg")  # Load Upper Colorado HU2, HUC8
    huc8_layer, huc8 = extract_and_reproject_huc8(wbd_huc8, huc_name)
    remove_layer(wbd_huc8)
    huc12_layer = extract_huc12_in_huc8(wbd_gpkg_path, huc_name)
    symbol = get_symbol(huc12_layer)
    symbol.setColor(QColor(200, 200, 150))

    gis_layer.zoom_to_layer(huc8_layer)
    gis_layer.refresh_display()

    # build_dem_from_huc(huc8_layer, "/opt/dev/gis/USGS_DEM",  str(forestry_dir))

    # build_forest_layers(forestry_dir, huc8_layer, huc_name)

    # build_open_et_layers(forestry_dir, huc8_layer, huc12_layer)

    # zenodo_layers = build_zenodo_layers(forestry_dir, huc8_layer, huc4_layer)
    tree_map_layers = build_tree_map_layers(forestry_dir, huc8_layer, huc4_layer)
    gis_layer.zoom_to_layer(huc8_layer)

    # build_disturbance(forestry_dir, huc12_layer)
    gis_layer.zoom_to_layer(huc8_layer)

    # load_vector_layer_masked("Protected Areas", "/opt/dev/gis/PAD/PADUS4_1Designation_StateCO.kmz",
    #                                                huc12_layer, forestry_dir, QColor(100, 255, 100))

    # build_elevation_layers(forestry_dir, huc8_layer)

    # create_group("Zenodo SDI 2022", position=0, existing_layer=huc12_layer, layer_dict=zenodo_layers)

    create_group("TreeMap 2022", position=0, existing_layer=huc12_layer, layer_dict=tree_map_layers)
    layer:Optional[QgsRasterLayer, None] = tree_map_layers.get('FLDTYPCD', None)
    if layer is not None:
        force_collapse(layer)

    hydrology_layers = build_hydrology(huc8)
    create_group("NHD Hydrology", visible=True, position=0, layers=hydrology_layers)
    reset_layer_parent_to_root()

    build_weather_stations(huc8_layer)

    return huc8_layer

reset_qgis()

print(f"\n=== Starting {huc8_name} Build ===")
huc8_layer = build(huc8_name)
gis_layer.zoom_to_layer(huc8_layer)