"""
Copyright (c) 2025 Ed Millard

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
script_paths = [
    "/opt/dev/riverwar"
]
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


# ====================== RESET QGIS ======================
def reset_qgis():
    print("🧹 Resetting QGIS — removing all layers...")
    QgsProject.instance().removeAllMapLayers()
    iface.mapCanvas().refresh()
    print("✅ QGIS has been reset to a clean state")


# ====================== FOREST TYPE DICTIONARY ======================



# ====================== CLIP CONUS VEGTYPE TO HUC ======================
def clip_conus_to_huc():
    print(f"Clipping full CONUS vegtype to {huc_name}...")
    output_clipped_veg = os.path.join(forestry_dir, f"vegtype_{huc_name.replace(' ', '_')}.tif")

    # Load HUC
    huc_layer = QgsVectorLayer(huc_vector_path, huc_name, "ogr")
    if not huc_layer.isValid():
        raise Exception("❌ Failed to load HUC vector")

    # Style as dark gray
    symbol = huc_layer.renderer().symbol()
    symbol.setColor(QColor(50, 50, 50))
    huc_layer.setOpacity(0.65)
    QgsProject.instance().addMapLayer(huc_layer)
    print(f"✅ HUC layer added as '{huc_name}' (dark gray)")

    # Reproject if needed (without adding extra layer)
    target_crs = QgsCoordinateReferenceSystem("EPSG:5069")
    if huc_layer.crs() != target_crs:
        print("Reprojecting HUC to EPSG:5069...")
        params = {'INPUT': huc_layer, 'TARGET_CRS': target_crs, 'OUTPUT': 'memory:Temp_HUC'}
        reprojected = processing.run("native:reprojectlayer", params)['OUTPUT']
        huc_layer = reprojected  # Use reprojected version

    # Clip the raster using the (possibly reprojected) HUC
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


def extract_tree_type_from_clipped(clipped_veg_path: str, veg_value: int, tree_name: str, color_rgb: tuple):
    safe_name = tree_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("(", "").replace(")",
                                                                                                                 "")
    output_path = os.path.join(forestry_dir, f"{safe_name}.tif")

    nodata_value = -9999
    print(f"Extracting {tree_name} ({veg_value})...")

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

    layer_name = f"{tree_name} ({veg_value})"
    output_layer = QgsRasterLayer(output_path, layer_name)

    if output_layer.isValid():
        classes = [QgsPalettedRasterRenderer.Class(veg_value, QColor(*color_rgb), tree_name)]
        renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1, classes)
        output_layer.setRenderer(renderer)
        QgsProject.instance().addMapLayer(output_layer)
        print(f"   ✅ {tree_name} extracted and styled")
    else:
        print(f"   ❌ Failed to load {tree_name}")


# ====================== MAIN PROGRAM ======================

print("\n=== Starting Full Workflow ===")

reset_qgis()

clipped_veg_layer, clipped_veg_path = clip_conus_to_huc()
present_types = list_vegtypes_in_clipped(clipped_veg_path)

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

    extract_tree_type_from_clipped(clipped_veg_path, code, name, color)

print("\n🎉 Workflow complete!")