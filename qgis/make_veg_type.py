from osgeo import gdal
import numpy as np
import os
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer, QgsCoordinateReferenceSystem
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
import processing

# ====================== SETTINGS ======================
conus_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"
huc_vector_path = "/opt/dev/gis/upper_dolores_HU8.shp"
huc_name = "Upper_Dolores"

forestry_dir = "/opt/dev/gis/forestry"
os.makedirs(forestry_dir, exist_ok=True)


# ====================== RESET QGIS ======================
def reset_qgis():
    """Remove all layers and reset QGIS to a clean state"""
    print("🧹 Resetting QGIS — removing all layers...")
    QgsProject.instance().removeAllMapLayers()
    iface.mapCanvas().refresh()
    print("✅ QGIS has been reset to a clean state")


# ====================== CLIP CONUS VEGTYPE TO HUC ======================
def clip_conus_to_huc():
    print(f"Clipping full CONUS vegtype to {huc_name}...")
    output_clipped_veg = os.path.join(forestry_dir, f"vegtype_{huc_name}.tif")

    huc_layer = QgsVectorLayer(huc_vector_path, huc_name, "ogr")
    if not huc_layer.isValid():
        raise Exception("❌ Failed to load HUC vector")

    target_crs = QgsCoordinateReferenceSystem("EPSG:5069")
    if huc_layer.crs() != target_crs:
        print("Reprojecting HUC to EPSG:5069...")
        params = {'INPUT': huc_layer, 'TARGET_CRS': target_crs, 'OUTPUT': 'memory:Reprojected_HUC'}
        huc_layer = processing.run("native:reprojectlayer", params)['OUTPUT']

    QgsProject.instance().addMapLayer(huc_layer)

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
        print(f"✅ Clipped vegtype added to QGIS")
        return clipped_veg_layer, result['OUTPUT']
    else:
        raise Exception("❌ Failed to create clipped vegtype")


# ====================== EXTRACT TREE TYPE ======================
def extract_tree_type_from_clipped(clipped_veg_path: str, veg_value: int, tree_name: str, color_rgb: tuple):
    safe_name = tree_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    output_path = os.path.join(forestry_dir, f"{huc_name}_{safe_name}.tif")

    nodata_value = -9999
    print(f"Extracting {tree_name} (value {veg_value})...")

    ds_in = gdal.Open(clipped_veg_path)
    if ds_in is None:
        print("❌ Could not open clipped vegtype")
        return

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

    layer_name = f"{tree_name} ({veg_value}) - {huc_name}"
    output_layer = QgsRasterLayer(output_path, layer_name)

    if output_layer.isValid():
        classes = [QgsPalettedRasterRenderer.Class(veg_value, QColor(*color_rgb), tree_name)]
        renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1, classes)
        output_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(output_layer)
        print(f"   ✅ {tree_name} extracted and styled")
    else:
        print(f"   ❌ Failed to load {tree_name}")


# ====================== MAIN PROGRAM (runs automatically) ======================

print("\n=== Running Full Workflow ===")

# Optional: Start with a clean map
# reset_qgis()

# Step 1: Clip the big raster once
clipped_veg_layer, clipped_veg_path = clip_conus_to_huc()

# Step 2: Extract all tree types
extract_tree_type_from_clipped(clipped_veg_path, 221, "Ponderosa Pine", (255, 0, 0))  # Bright Red
extract_tree_type_from_clipped(clipped_veg_path, 201, "Douglas Fir", (0, 180, 0))  # Green
extract_tree_type_from_clipped(clipped_veg_path, 901, "Aspen", (255, 215, 0))  # Gold
extract_tree_type_from_clipped(clipped_veg_path, 265, "Engelmann Spruce", (0, 100, 255))  # Blue
extract_tree_type_from_clipped(clipped_veg_path, 266, "Engelmann Spruce / Subalpine Fir", (0, 160, 140))  # Teal
extract_tree_type_from_clipped(clipped_veg_path, 269, "Blue Spruce", (0, 255, 255))  # Cyan
extract_tree_type_from_clipped(clipped_veg_path, 185, "Pinyon Juniper", (139, 69, 19))  # Brown

print("\n🎉 All done! Upper Dolores tree layers are ready.")