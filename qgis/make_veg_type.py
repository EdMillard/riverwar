from osgeo import gdal
import numpy as np
import os
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer
from qgis.PyQt.QtGui import QColor  # ← This is the correct import
from qgis.utils import iface

# ====================== LOAD INPUT RASTER ONCE ======================
input_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"

ds_in = gdal.Open(input_raster_path)
if ds_in is None:
    raise Exception("❌ Could not open the CONUS vegtype raster!")
else:
    print(f"✅ CONUS vegtype raster loaded successfully (size: {ds_in.RasterXSize} x {ds_in.RasterYSize})")


# ====================== REUSABLE FUNCTION ======================
def extract_tree_type(veg_value: int, tree_name: str, color_rgb: tuple):
    """
    Extracts a single vegetation type and adds it as a styled layer.

    Parameters:
        veg_value (int): Pixel value (e.g. 221)
        tree_name (str): Name for the layer (e.g. "Ponderosa Pine")
        color_rgb (tuple): RGB color (e.g. (255, 0, 0) for bright red)
    """
    safe_name = tree_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    output_raster_path = f"/opt/dev/gis/forestry/{safe_name}.tif"

    nodata_value = -9999

    print(f"Processing {tree_name} (value = {veg_value}) ...")

    # Create output raster
    driver = gdal.GetDriverByName('GTiff')
    ds_out = driver.Create(
        output_raster_path,
        ds_in.RasterXSize,
        ds_in.RasterYSize,
        1,
        gdal.GDT_Int16,
        options=['COMPRESS=LZW', 'TILED=YES']
    )

    ds_out.SetGeoTransform(ds_in.GetGeoTransform())
    ds_out.SetProjection(ds_in.GetProjection())

    out_band = ds_out.GetRasterBand(1)
    out_band.SetNoDataValue(nodata_value)

    # Process block by block
    block_size = 2048
    band = ds_in.GetRasterBand(1)

    for y in range(0, ds_in.RasterYSize, block_size):
        for x in range(0, ds_in.RasterXSize, block_size):
            xsize = min(block_size, ds_in.RasterXSize - x)
            ysize = min(block_size, ds_in.RasterYSize - y)

            data = band.ReadAsArray(x, y, xsize, ysize)
            result = np.where(data == veg_value, veg_value, nodata_value)
            out_band.WriteArray(result, x, y)

    ds_out.FlushCache()
    ds_out = None

    print(f"   → Raster saved: {output_raster_path}")

    # Load and style
    layer_name = f"{tree_name} ({veg_value})"
    output_layer = QgsRasterLayer(output_raster_path, layer_name)

    if output_layer.isValid():
        classes = [
            QgsPalettedRasterRenderer.Class(veg_value, QColor(*color_rgb), tree_name)
        ]

        renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1, classes)
        output_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(output_layer)
        output_layer.triggerRepaint()
        iface.mapCanvas().refresh()

        print(f"   ✅ {tree_name} added in color {color_rgb}!")
    else:
        print(f"   ❌ Failed to load {tree_name} layer")


# ====================== EXAMPLE CALLS ======================

extract_tree_type(221, "Ponderosa Pine", (255, 0, 0))  # Bright Red
extract_tree_type(201, "Douglas Fir", (0, 180, 0))       # Green
extract_tree_type(901, "Aspen", (255, 215, 0))           # Gold/Yellow
extract_tree_type(265, "Engelmann Spruce", (0, 100, 255))# Blue
# extract_tree_type(185, "Pinyon Juniper", (139, 69, 19))  # Brown

print("\n✅ All done! Uncomment and modify the calls above as needed.")