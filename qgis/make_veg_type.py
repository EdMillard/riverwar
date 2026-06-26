from osgeo import gdal
import numpy as np
import os
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer, QgsCoordinateReferenceSystem
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
import processing

# ====================== LOAD CONUS VEGTYPE ONCE ======================
input_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"

ds_in = gdal.Open(input_raster_path)
if ds_in is None:
    raise Exception("❌ Could not open the CONUS vegtype raster!")
else:
    print(f"✅ CONUS vegtype raster loaded successfully")


# ====================== EXTRACT TREE TYPE ======================
def extract_tree_type(veg_value: int, tree_name: str, color_rgb: tuple):
    safe_name = tree_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    output_raster_path = f"/opt/dev/gis/forestry/{safe_name}.tif"

    nodata_value = -9999
    print(f"Creating {tree_name} ...")

    driver = gdal.GetDriverByName('GTiff')
    ds_out = driver.Create(output_raster_path, ds_in.RasterXSize, ds_in.RasterYSize, 1, gdal.GDT_Int16,
                           options=['COMPRESS=LZW', 'TILED=YES'])

    ds_out.SetGeoTransform(ds_in.GetGeoTransform())
    ds_out.SetProjection(ds_in.GetProjection())

    out_band = ds_out.GetRasterBand(1)
    out_band.SetNoDataValue(nodata_value)

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

    layer_name = f"{tree_name} ({veg_value})"
    output_layer = QgsRasterLayer(output_raster_path, layer_name)

    if output_layer.isValid():
        classes = [QgsPalettedRasterRenderer.Class(veg_value, QColor(*color_rgb), tree_name)]
        renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1, classes)
        output_layer.setRenderer(renderer)
        QgsProject.instance().addMapLayer(output_layer)
        print(f"   ✅ {tree_name} created")
    else:
        print(f"   ❌ Failed to create {tree_name}")


# ====================== CLIP TO HUC + AUTO REMOVE ORIGINALS ======================
def clip_to_huc(huc_vector_path: str, huc_name: str = "Upper_Dolores"):
    if not os.path.exists(huc_vector_path):
        print("❌ HUC vector file not found!")
        return

    output_dir = f"/opt/dev/gis/forestry/{huc_name.replace(' ', '_').replace('-', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Output folder: {output_dir}")

    # Load & reproject HUC
    huc_layer = QgsVectorLayer(huc_vector_path, huc_name, "ogr")
    if not huc_layer.isValid():
        print("❌ Failed to load HUC")
        return

    target_crs = QgsCoordinateReferenceSystem("EPSG:5069")
    if huc_layer.crs() != target_crs:
        print("Reprojecting HUC to EPSG:5069...")
        params = {'INPUT': huc_layer, 'TARGET_CRS': target_crs, 'OUTPUT': 'memory:Reprojected_HUC'}
        huc_layer = processing.run("native:reprojectlayer", params)['OUTPUT']

    QgsProject.instance().addMapLayer(huc_layer)

    # Get tree rasters
    forestry_dir = "/opt/dev/gis/forestry"
    tree_rasters = [f for f in os.listdir(forestry_dir)
                    if f.endswith('.tif') and not f.lower().startswith('conus')]

    print(f"Clipping {len(tree_rasters)} rasters and removing originals...")

    for raster_file in tree_rasters:
        input_raster = os.path.join(forestry_dir, raster_file)
        output_clipped = os.path.join(output_dir, raster_file)

        print(f"   Clipping: {raster_file}")

        # Clip
        params = {
            'INPUT': input_raster,
            'MASK': huc_layer,
            'NODATA': -9999,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'OUTPUT': output_clipped
        }

        try:
            result = processing.run("gdal:cliprasterbymasklayer", params)
            clipped_layer = QgsRasterLayer(result['OUTPUT'], f"{raster_file[:-4]} ({huc_name})")

            if clipped_layer.isValid():
                # Copy color
                base = raster_file[:-4].lower().replace("_", " ")
                original = None
                for lyr in list(QgsProject.instance().mapLayers().values()):
                    lyr_lower = lyr.name().lower()
                    if (base in lyr_lower or lyr_lower.startswith(
                            base.split()[0])) and huc_name.lower() not in lyr_lower:
                        original = lyr
                        break

                if original and original.renderer():
                    clipped_layer.setRenderer(original.renderer().clone())
                    print(f"   ✅ Color copied from original")
                else:
                    print(f"   ⚠️ No original found for color")

                # Add the clipped layer
                QgsProject.instance().addMapLayer(clipped_layer)

                # === REMOVE ORIGINAL LAYER (improved matching) ===
                removed_count = 0
                for lyr in list(QgsProject.instance().mapLayers().values()):
                    lyr_lower = lyr.name().lower()
                    if (base in lyr_lower or lyr_lower.startswith(
                            base.split()[0])) and huc_name.lower() not in lyr_lower:
                        QgsProject.instance().removeMapLayer(lyr.id())
                        print(f"   🗑️ Removed original: {lyr.name()}")
                        removed_count += 1

                if removed_count == 0:
                    print(f"   ⚠️ No original layer found to remove for {raster_file}")

            else:
                print(f"   ❌ Failed to load clipped layer")

        except Exception as e:
            print(f"   ❌ Error with {raster_file}: {e}")

    iface.mapCanvas().refresh()
    print(f"🎉 Finished clipping to {huc_name} — originals should now be removed.")


# ====================== MAIN PROGRAM ======================

print("\n=== Starting Main Program ===")

# Create tree layers
extract_tree_type(221, "Ponderosa Pine", (255, 0, 0))
extract_tree_type(201, "Douglas Fir", (0, 180, 0))
extract_tree_type(901, "Aspen", (255, 215, 0))
extract_tree_type(265, "Engelmann Spruce", (0, 100, 255))
extract_tree_type(185, "Pinyon Juniper", (139, 69, 19))

# Clip and clean up
clip_to_huc("/opt/dev/gis/upper_dolores_HU8.shp", "Upper_Dolores")

print("\n🎉 All done!")