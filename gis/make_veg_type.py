"""
Copyright (c) 2025 Ed Millard
"""

import sys

script_paths = ["/opt/dev/riverwar"]
for p in script_paths:
    if p not in sys.path:
        sys.path.append(p)
        print(f"Added to Python path: {p}")

from osgeo import gdal
import numpy as np
import os
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer, QgsCoordinateReferenceSystem, \
    QgsVectorLayer
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
from gis.forest_type import forest_types
from gis.contours import extract_contours, select_contours_on_layer
import processing
import zipfile
import tempfile
from pathlib import Path
import time

# ====================== SETTINGS ======================
conus_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"
huc_vector_path = "/opt/dev/gis/upper_dolores_HU8.shp"
contour_vector_path = "/opt/dev/gis/forestry/contours_reprojected.shp"
huc_name = "HUC8"

# ====================== GLOBAL PROJECT SETTINGS ======================
TARGET_CRS = "EPSG:5070"          # Defualt CRS
forestry_dir = "/opt/dev/gis/forestry"
os.makedirs(forestry_dir, exist_ok=True)

def remove_layer(layer):
    """Remove a layer by passing the layer object"""
    if layer is None:
        print("❌ No layer provided")
        return False
    print(f"✅ Removed layer: {layer.name()}")
    QgsProject.instance().removeMapLayer(layer.id())
    return True

def reset_qgis():
    """Very thorough QGIS reset"""
    print("🧹 Thoroughly resetting QGIS...")

    project = QgsProject.instance()

    # Remove all layers one by one
    layer_ids = list(project.mapLayers().keys())
    for layer_id in layer_ids:
        project.removeMapLayer(layer_id)

    # Extra safety
    project.clear()
    iface.mapCanvas().refresh()
    time.sleep(0.8)  # longer wait

    print("✅ Thorough reset complete — project should be empty")

def load_huc8_from_wbd(gpkg_path: str, huc8_name: str = None, huc8_code: str = None):
    """
    Load HUC8 from the USGS WBD_14_HU2_GPKG file.

    Examples:
        load_huc8_from_wbd("/path/to/WBD_14_HU2_GPKG.gpkg", huc8_name="Upper Dolores")
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
    if huc8_name or huc8_code:
        expression = None
        if huc8_name:
            expression = f'"Name" = \'{huc8_name}\''
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
                huc_layer.setName(huc8_name or huc8_code)
            else:
                print(f"⚠️ No HUC8 found matching {huc8_name or huc8_code}")

    # Basic styling
    symbol = huc_layer.renderer().symbol()
    symbol.setColor(QColor(40, 40, 40))
    huc_layer.setOpacity(0.65)

    QgsProject.instance().addMapLayer(huc_layer)
    print(f"✅ Loaded HUC8 layer: {huc_layer.name()} ({huc_layer.featureCount()} features)")
    return huc_layer

def reproject_layer(layer, new_name=None):
    if layer is None:
        print("❌ No layer provided")
        return None

    print(f"Original CRS: {layer.crs().authid()}")
    print(f"Original features: {layer.featureCount()}")

    if new_name is None:
        new_name = layer.name() + " (Reprojected)"

    output_path = os.path.join(forestry_dir, "contours_fixed.gpkg")

    params = {
        'INPUT': layer,
        'TARGET_CRS': QgsCoordinateReferenceSystem("EPSG:5069"),
        'OUTPUT': output_path
    }

    result = processing.run("native:reprojectlayer", params)
    reproj_layer = QgsVectorLayer(output_path, new_name, "ogr")

    print(f"Reprojected features: {reproj_layer.featureCount()}")

    # Style
    symbol = reproj_layer.renderer().symbol()
    symbol.setColor(QColor(255, 0, 100))
    symbol.setWidth(0.7)

    QgsProject.instance().addMapLayer(reproj_layer)

    # Correct zoom
    if reproj_layer.featureCount() > 0:
        iface.mapCanvas().setExtent(reproj_layer.extent())
        iface.mapCanvas().refresh()

    print(f"✅ Added: {new_name}")
    return reproj_layer

def load_vector_layer(path: str, name: str = None, color: QColor = QColor(40, 40, 40)):
    """
    Load vector layer - automatically handles .zip files by extracting them.
    """
    if not os.path.exists(path):
        raise Exception(f"❌ File not found: {path}")

    layer_name = name or Path(path).stem.replace("_", " ")

    # Handle zipped shapefile
    if path.lower().endswith('.zip'):
        print(f"📦 Zip file detected: {path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Extract the zip
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                print(f"   Extracted to temporary folder")

            # Find the .shp file inside
            shp_files = list(tmpdir.glob("**/*.shp"))
            if not shp_files:
                raise Exception("❌ No .shp file found inside the zip!")

            actual_path = str(shp_files[0])
            print(f"   Using shapefile: {actual_path}")

            layer = QgsVectorLayer(actual_path, layer_name, "ogr")
    else:
        layer = QgsVectorLayer(path, layer_name, "ogr")

    if not layer.isValid():
        raise Exception(f"❌ Failed to load layer from {path}")

    # Style
    symbol = layer.renderer().symbol()
    symbol.setColor(color)
    layer.setOpacity(0.65)

    QgsProject.instance().addMapLayer(layer)
    print(f"✅ Successfully loaded: {layer_name}")
    return layer


def clip_conus_to_huc(huc_layer):
    print(f"Clipping full CONUS vegtype to {huc_name}...")
    output_clipped_veg = os.path.join(forestry_dir, f"vegtype_{huc_name.replace(' ', '_')}.tif")

    target_crs = QgsCoordinateReferenceSystem("EPSG:5069")
    if huc_layer.crs() != target_crs:
        print("Reprojecting HUC...")
        params = {'INPUT': huc_layer, 'TARGET_CRS': target_crs, 'OUTPUT': 'memory:Temp_HUC'}
        huc_layer = processing.run("native:reprojectlayer", params)['OUTPUT']

    params = {
        'INPUT': conus_raster_path,
        'MASK': huc_layer,
        'NODATA': -9999,
        'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': True,
        'OUTPUT': output_clipped_veg
    }

    result = processing.run("gdal:cliprasterbymasklayer", params)
    clipped_veg_layer = QgsRasterLayer(result['OUTPUT'], f"VegType_{huc_name}")

    if clipped_veg_layer.isValid():
        QgsProject.instance().addMapLayer(clipped_veg_layer)
        print(f"✅ Clipped vegtype added (kept outside group)")
        return clipped_veg_layer, result['OUTPUT']
    else:
        raise Exception("❌ Failed to create clipped vegtype")


def list_vegtypes_in_clipped(clipped_veg_path: str, huc8_name:str):
    print(f"\n=== Vegetation Types Present in {huc8_name} ===")
    ds = gdal.Open(clipped_veg_path)
    if ds is None:
        print("❌ Could not open clipped vegtype")
        return []

    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    unique_values = np.unique(data)
    nodata = band.GetNoDataValue()

    present = []
    for val in sorted(unique_values):
        if nodata is not None and val == nodata:
            continue
        info = forest_types.get(val, {"name": f"Unknown Code {val}", "color": (150, 150, 150)})
        print(f"   {val:4d}  →  {info['name']}")
        present.append((val, info["name"]))

    ds = None
    print(f"\nTotal unique types found: {len(present)}\n")
    return present


def extract_tree_type_from_clipped(clipped_veg_path: str, veg_value: int, tree_name: str, color_rgb: tuple, group):
    safe_name = tree_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("(", "").replace(")",
                                                                                                                 "")
    output_path = os.path.join(forestry_dir, f"{safe_name}.tif")

    nodata_value = -9999

    ds_in = gdal.Open(clipped_veg_path)
    if ds_in is None:
        return None

    driver = gdal.GetDriverByName('GTiff')
    ds_out = driver.Create(output_path, ds_in.RasterXSize, ds_in.RasterYSize, 1, gdal.GDT_Int16,
                           options=['COMPRESS=LZW', 'TILED=YES'])
    ds_out.SetGeoTransform(ds_in.GetGeoTransform())
    ds_out.SetProjection(ds_in.GetProjection())

    out_band = ds_out.GetRasterBand(1)
    out_band.SetNoDataValue(nodata_value)

    band = ds_in.GetRasterBand(1)
    block_size = 2048
    for y in range(0, ds_in.RasterYSize, block_size):
        for x in range(0, ds_in.RasterXSize, block_size):
            xsize = min(block_size, ds_in.RasterXSize - x)
            ysize = min(block_size, ds_in.RasterYSize - y)
            data = band.ReadAsArray(x, y, xsize, ysize)
            result = np.where(data == veg_value, veg_value, nodata_value)
            out_band.WriteArray(result, x, y)

    ds_out.FlushCache()
    ds_out = None
    ds_in = None

    layer_name = f"{tree_name} ({veg_value})"
    output_layer = QgsRasterLayer(output_path, layer_name)

    if output_layer.isValid():
        renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1,
                                             [QgsPalettedRasterRenderer.Class(veg_value, QColor(*color_rgb),
                                                                              tree_name)])
        output_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(output_layer, False)  # Don't add to root
        group.addLayer(output_layer)  # Add directly to group

        print(f"   ✅ {tree_name} added to group")
        return output_layer
    return None

def create_forest_group():
    root = QgsProject.instance().layerTreeRoot()
    group_name = "Forest Types"

    # Remove existing group if it exists
    existing = root.findGroup(group_name)
    if existing:
        root.removeChildNode(existing)

    # Create group at top and collapse it
    group = root.insertGroup(0, group_name)
    group.setExpanded(False)      # ← This collapses it
    group.setItemVisibilityChecked(True)

    print(f"✅ Created collapsed group at top: '{group_name}'")
    return group


def ensure_crs_target(layer, layer_name: str = None):
    """Reproject to the global TARGET_CRS if needed"""
    target = QgsCoordinateReferenceSystem(TARGET_CRS)

    if layer.crs() == target:
        print(f"✅ {layer_name or layer.name()} already in {TARGET_CRS}")
        return layer

    print(f"🔄 Reprojecting {layer_name or layer.name()} → {TARGET_CRS}")

    output_path = os.path.join(forestry_dir,
                               f"{(layer_name or layer.name()).replace(' ', '_')}_{TARGET_CRS.split(':')[1]}.gpkg")

    params = {
        'INPUT': layer,
        'TARGET_CRS': target,
        'OUTPUT': output_path
    }

    result = processing.run("native:reprojectlayer", params)
    new_layer = QgsVectorLayer(output_path, layer_name or layer.name(), "ogr")

    return new_layer


def extract_and_reproject_huc8(wbd_layer, huc8_name: str):
    """
    Takes the big WBD HUC8 layer, keeps only the named HUC8,
    reprojects it to TARGET_CRS, and returns a clean single-feature layer named "HUC8".
    """
    if wbd_layer is None:
        print("❌ No WBD layer provided")
        return None

    print(f"Extracting HUC8: '{huc8_name}' from {wbd_layer.featureCount()} features...")

    # Select the desired HUC8
    expression = f'"Name" = \'{huc8_name}\''
    wbd_layer.selectByExpression(expression)

    selected_count = wbd_layer.selectedFeatureCount()
    if selected_count == 0:
        print(f"❌ No HUC8 found with name '{huc8_name}'")
        return None
    if selected_count > 1:
        print(f"⚠️ Found {selected_count} features matching '{huc8_name}' — using first one")

    # Save only the selected feature
    params = {
        'INPUT': wbd_layer,
        'OUTPUT': 'memory:Single_HUC8'
    }
    result = processing.run("native:saveselectedfeatures", params)
    single_huc = result['OUTPUT']

    # === ENSURE TARGET CRS + clean name ===
    final_layer = ensure_crs_target(single_huc, "HUC8")

    # Style
    symbol = final_layer.renderer().symbol()
    symbol.setColor(QColor(40, 40, 40))
    final_layer.setOpacity(0.65)

    QgsProject.instance().addMapLayer(final_layer)

    print(f"✅ Successfully created: HUC8 ({TARGET_CRS}, {final_layer.featureCount()} features)")

    return final_layer


def extract_huc12_in_huc8(wbd_gpkg_path: str, huc8_name: str):
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
    huc8_layer.selectByExpression(f'"Name" = \'{huc8_name}\'')
    if huc8_layer.selectedFeatureCount() == 0:
        print(f"❌ HUC8 '{huc8_name}' not found")
        return None

    feature = next(huc8_layer.getSelectedFeatures())
    huc8_code = feature["HUC8"]
    print(f"Found HUC8 '{huc8_name}' → Code: {huc8_code}")

    # Select matching HUC12s
    expression = f'"huc12" LIKE \'{huc8_code}%\''
    huc12_layer.selectByExpression(expression)

    count = huc12_layer.selectedFeatureCount()
    print(f"Found {count} HUC12 features for {huc8_name}")

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
    final_layer = ensure_crs_target(huc12_subset, "HUC12s")

    # Style
    symbol = final_layer.renderer().symbol()
    symbol.setColor(QColor(0, 100, 200))
    final_layer.setOpacity(0.45)

    QgsProject.instance().addMapLayer(final_layer)
    print(f"✅ Final HUC12 layer ready: HUC12s ({final_layer.featureCount()} features)")

    return final_layer


def build(huc_layer, huc8_name:str):
    # huc_layer = load_vector_layer(huc_vector_path, huc_name, QColor(40, 40, 40))

    clipped_veg_layer, clipped_veg_path = clip_conus_to_huc(huc_layer)
    present_types = list_vegtypes_in_clipped(clipped_veg_path, huc8_name)

    forest_group = create_forest_group()

    for code, info in forest_types.items():
        name = info["name"]
        color = info["color"]

        layer = extract_tree_type_from_clipped(clipped_veg_path, code, name, color, forest_group)

    contour_layer = load_vector_layer(contour_vector_path, "ELEV_Cortez_E_CO_1X1_Shape — Shape/Elev_Contour.shp", QColor(80, 80, 80))
    major_contour_layer = extract_contours("ELEV_Cortez_E_CO_1X1_Shape — Shape/Elev_Contour.shp",
                     [8000, 9000, 10000, 11000, 12000],
                     "Major Contours 8k-12k ft")
    select_contours_on_layer(major_contour_layer, [10000, 11000], highlight_color=QColor(200, 000, 0))
    remove_layer(contour_layer)

    print("\n🎉 Done! HUC8 + VegType layer should stay visible, forest types are in the group at the top.")

reset_qgis()

print("\n=== Starting HUC8 Build ===")
huc8_name =  "Upper Dolores"
wbd_huc8 = load_huc8_from_wbd("/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg")  # Load Upper Colorado HU2, HUC8
huc8_layer = extract_and_reproject_huc8(wbd_huc8, huc8_name)
remove_layer(wbd_huc8)
huc12_layer = extract_huc12_in_huc8('/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg', huc8_name)
build(huc8_layer, huc8_name)