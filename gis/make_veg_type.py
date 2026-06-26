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
from gis.forest_type import forest_type_dict
import processing

# ====================== SETTINGS ======================
conus_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"
huc_vector_path = "/opt/dev/gis/upper_dolores_HU8.shp"
huc_name = "Upper Dolores HUC8"

forestry_dir = "/opt/dev/gis/forestry"
os.makedirs(forestry_dir, exist_ok=True)


def reset_qgis():
    print("🧹 Resetting QGIS — removing all layers...")
    QgsProject.instance().removeAllMapLayers()
    iface.mapCanvas().refresh()
    print("✅ QGIS has been reset to a clean state")


def load_vector_layer(path: str, name: str, color: QColor):
    vector_layer = QgsVectorLayer(path, name, "ogr")
    if not vector_layer.isValid():
        raise Exception("❌ Failed to load HUC vector")

    symbol = vector_layer.renderer().symbol()
    symbol.setColor(color)
    vector_layer.setOpacity(0.65)
    QgsProject.instance().addMapLayer(vector_layer)
    print(f"✅ HUC layer added as '{name}'")
    return vector_layer


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


def list_vegtypes_in_clipped(clipped_veg_path: str):
    print("\n=== Vegetation Types Present in Upper Dolores ===")
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
        name = forest_type_dict.get(val, f"Unknown Code {val}")
        print(f"   {val:4d}  →  {name}")
        present.append((val, name))

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
    group_name = "Upper Dolores Forest Types"

    existing = root.findGroup(group_name)
    if existing:
        root.removeChildNode(existing)

    group = root.insertGroup(0, group_name)  # Top of stack
    group.setExpanded(True)
    print(f"✅ Created group at TOP: '{group_name}'")
    return group


# ====================== MAIN ======================

print("\n=== Starting Full Workflow ===")

reset_qgis()

huc_layer = load_vector_layer(huc_vector_path, huc_name, QColor(40, 40, 40))

clipped_veg_layer, clipped_veg_path = clip_conus_to_huc(huc_layer)
present_types = list_vegtypes_in_clipped(clipped_veg_path)

forest_group = create_forest_group()

for code, name in present_types:
    color = (150, 150, 150)
    if code == 221:
        color = (255, 0, 0)
    elif code == 201:
        color = (0, 180, 0)
    elif code == 901:
        color = (255, 215, 0)
    elif code == 265 or code == 266:
        color = (0, 100, 255)
    elif code == 269:
        color = (0, 255, 255)
    elif code == 185:
        color = (139, 69, 19)
    elif code == 925:
        color = (200, 100, 50)
    elif code == 999:
        color = (200, 200, 100)
    elif code == 365:
        color = (180, 100, 220)
    elif code == 366:
        color = (100, 180, 100)
    elif code == 703:
        color = (0, 200, 120)
    elif code == 709:
        color = (0, 160, 100)

    extract_tree_type_from_clipped(clipped_veg_path, code, name, color, forest_group)

print("\n🎉 Done! HUC8 + VegType layer should stay visible, forest types are in the group at the top.")