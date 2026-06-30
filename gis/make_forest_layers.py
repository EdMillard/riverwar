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

# Treemap download
# https://data.fs.usda.gov/geodata/rastergateway/treemap/index.php
#
from osgeo import gdal
import numpy as np
from pathlib import Path
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer
from qgis.PyQt.QtGui import QColor
from gis.forest_type import forest_types
from gis.layer import clip_raster_to_mask, create_group, add_layer_to_group, set_layer_state
import processing # type: ignore

huc_name = "HUC8"

def list_vegtypes_in_clipped(clipped_veg_path: str, huc8_name: str):
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

    print(f"\nTotal unique types found: {len(present)}\n")
    return present


def style_conus_layer_with_colors(conus_layer: QgsRasterLayer, present_codes: list):
    """Apply colors from forest_types dictionary to the original CONUS layer"""
    if not conus_layer.isValid():
        print("⚠️ CONUS layer is not valid for styling")
        return

    classes = []
    for code, _ in present_codes:
        info = forest_types.get(code, {"name": f"Unknown {code}", "color": (150, 150, 150)})
        color = QColor(*info["color"])
        classes.append(QgsPalettedRasterRenderer.Class(code, color, info["name"]))

    renderer = QgsPalettedRasterRenderer(conus_layer.dataProvider(), 1, classes)
    conus_layer.setRenderer(renderer)
    print(f"✅ Styled original CONUS vegtype layer with {len(classes)} vegetation types")


def extract_tree_type_from_clipped(forestry_dir: Path, clipped_veg_path: str, veg_value: int,
                                   tree_name: str, color_rgb: tuple, group):
    safe_name = tree_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("(", "").replace(")", "")
    output_path = forestry_dir / f"{safe_name}.tif"

    nodata_value = -9999

    ds_in = gdal.Open(clipped_veg_path)
    if ds_in is None:
        return None

    driver = gdal.GetDriverByName('GTiff')
    ds_out = driver.Create(str(output_path), ds_in.RasterXSize, ds_in.RasterYSize, 1, gdal.GDT_Int16,
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

    layer_name = f"{tree_name} ({veg_value})"
    output_layer = QgsRasterLayer(str(output_path), layer_name)

    if output_layer.isValid():
        renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1,
                                             [QgsPalettedRasterRenderer.Class(veg_value, QColor(*color_rgb),
                                                                              tree_name)])
        output_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(output_layer, False)
        group.addLayer(output_layer)

        print(f"   ✅ {tree_name} added to group")
        return output_layer
    return None

def style_clipped_layer(clipped_veg_layer: QgsRasterLayer, present_types: list):
    """Apply colors from forest_types to the clipped VegType layer"""
    if not clipped_veg_layer or not clipped_veg_layer.isValid():
        print("❌ Clipped layer is not valid for styling")
        return

    print(f"🎨 Applying palette to layer: {clipped_veg_layer.name()}")

    classes = []
    for code, _ in present_types:
        info = forest_types.get(code, {"name": f"Unknown {code}", "color": (150, 150, 150)})
        color = QColor(*info["color"])
        classes.append(QgsPalettedRasterRenderer.Class(code, color, info["name"]))
        print(f"   {code} → {info['name']} {info['color']}")

    renderer = QgsPalettedRasterRenderer(clipped_veg_layer.dataProvider(), 1, classes)
    clipped_veg_layer.setRenderer(renderer)

    # Force refresh
    clipped_veg_layer.triggerRepaint()

    from qgis.utils import iface
    if iface:
        iface.mapCanvas().refresh()             # type: ignore[attr-defined]
        iface.mapCanvas().refreshAllLayers()    # type: ignore[attr-defined]
        iface.layerTreeView().refreshLayerSymbology(clipped_veg_layer.id())     # type: ignore[attr-defined]

    print(f"✅ Applied {len(classes)} color classes to clipped layer")

def reclassify_raster(
    input_layer: QgsRasterLayer,
    output_dir: Path,
    output_name: str = None,
    classes: list = None,           # List of (min, max, value, color, label)
    no_data: int = 0,
    opacity: float = 0.95
) -> QgsRasterLayer:
    """
    General raster reclassifier with variable number of classes.
    """
    if not input_layer or not input_layer.isValid():
        raise Exception("Input raster layer is invalid")

    if output_name is None:
        output_name = input_layer.name() + "_Reclass"

    output_path = output_dir / f"{output_name}.tif"

    if classes is None:
        classes = [
            (0, 50, 1, QColor(200, 200, 200, 80), "Low"),
            (50, 100, 2, QColor(255, 180, 80, 255), "Medium"),
            (100, 9999, 3, QColor(220, 50, 50, 255), "High")
        ]

    # Build reclassification table
    reclass_table = []
    for min_val, max_val, new_val, _, _ in classes:
        reclass_table.extend([min_val, max_val, new_val])

    params = {
        'INPUT_RASTER': input_layer,
        'RASTER_BAND': 1,
        'TABLE': reclass_table,
        'NO_DATA': no_data,
        'RANGE_BOUNDARIES': 0,
        'OUTPUT': str(output_path)
    }

    result = processing.run("native:reclassifybytable", params)
    reclass_layer = QgsRasterLayer(result['OUTPUT'], output_name)

    if reclass_layer.isValid():
        # Build classes for renderer (newer QGIS style)
        renderer_classes = []
        for value, color, label in [(c[2], c[3], c[4]) for c in classes]:
            renderer_classes.append(
                QgsPalettedRasterRenderer.Class(value, color, label)
            )

        renderer = QgsPalettedRasterRenderer(
            reclass_layer.dataProvider(), 1, renderer_classes
        )
        reclass_layer.setRenderer(renderer)

        reclass_layer.setOpacity(opacity)
        reclass_layer.triggerRepaint()

        QgsProject.instance().addMapLayer(reclass_layer)
        print(f"✅ Reclassified: {reclass_layer.name()} ({len(classes)} classes)")
        return reclass_layer
    else:
        raise Exception(f"Failed to reclassify {input_layer.name()}")


def print_raster_value_counts(raster_layer: QgsRasterLayer, band: int = 1):
    """
    Print ALL unique values (rounded to nearest integer) and their pixel counts.
    """
    if not raster_layer or not raster_layer.isValid():
        print("❌ Invalid raster layer")
        return

    provider = raster_layer.dataProvider()
    extent = raster_layer.extent()

    block = provider.block(band, extent, raster_layer.width(), raster_layer.height())
    array = np.frombuffer(block.data(), dtype=np.float32).reshape(
        raster_layer.height(), raster_layer.width()
    )

    # Round to nearest integer
    rounded = np.round(array).astype(int)

    unique, counts = np.unique(rounded, return_counts=True)
    count_dict = dict(zip(unique, counts))
    sorted_counts = dict(sorted(count_dict.items()))

    total_pixels = array.size

    print(f"✅ Full value counts for: {raster_layer.name()} (rounded to integer)")
    print(f"   Total pixels: {total_pixels:,}")
    print(f"   Unique values: {len(unique)}\n")
    print(f"{'Value':>8} | {'Pixel Count':>12} | {'Percentage':>8}")
    print("-" * 38)

    for value, count in sorted_counts.items():
        percent = (count / total_pixels) * 100
        print(f"{value:8d} | {count:12,} | {percent:7.3f}%")

def raster_value_counts(raster_layer: QgsRasterLayer, band: int = 1, max_unique: int = 500):
    """
    Count pixels for each value in a raster.
    Returns a sorted dictionary {value: pixel_count}
    """
    if not raster_layer or not raster_layer.isValid():
        print("❌ Invalid raster layer")
        return {}

    provider = raster_layer.dataProvider()
    extent = raster_layer.extent()

    # Read the entire band as numpy array
    block = provider.block(band, extent, raster_layer.width(), raster_layer.height())
    array = np.frombuffer(block.data(), dtype=np.float32).reshape(
        raster_layer.height(), raster_layer.width()
    )

    # Count occurrences
    unique, counts = np.unique(array, return_counts=True)

    # Convert to dict and sort by value
    count_dict = dict(zip(unique, counts))
    sorted_counts = dict(sorted(count_dict.items()))

    print(f"✅ Raster statistics for {raster_layer.name()}")
    print(f"   Total pixels: {array.size:,}")
    print(f"   Unique values: {len(unique)}")
    print(f"   Min: {array.min():.1f}   Max: {array.max():.1f}")

    # Print top values
    print("\nTop values by pixel count:")
    for value, count in sorted(sorted_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"   {value:8.1f} : {count:12,} pixels ({count / array.size * 100:5.2f}%)")

    return sorted_counts

def build_forest_layers(forestry_dir: Path, huc_layer, huc8_name: str):
    conus_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"
    clipped_veg_layer, clipped_veg_path = clip_raster_to_mask(conus_raster_path, huc_layer, forestry_dir)
    present_types = list_vegtypes_in_clipped(clipped_veg_path, huc8_name)

    # === Style the clipped layer (this is what you see as VegType_HUC8) ===
    style_clipped_layer(clipped_veg_layer, present_types)

    forest_group = create_group("Forest Types")

    for code, info in forest_types.items():
        if code not in [p[0] for p in present_types]:
            continue
        name = info["name"]
        color = info["color"]
        extract_tree_type_from_clipped(forestry_dir, clipped_veg_path, code, name, color, forest_group)

def build_tree_map_layers(forestry_dir: Path, huc_layer, huc12_layer):

    tree_map_group = create_group("TreeMap 2022", position=None, existing_layer=huc12_layer)

    tree_map_balive_raster_path =  "/opt/dev/gis/TreeMap/TreeMap2022_CONUS_BALIVE/TreeMap2022_CONUS_BALIVE.tif"
    clipped_tree_map_balive, path = clip_raster_to_mask(tree_map_balive_raster_path, huc_layer, forestry_dir)
    #add_layer_to_group(clipped_tree_map_balive, tree_map_group)
    set_layer_state(clipped_tree_map_balive, False, False)

    # counts = raster_value_counts(clipped_tree_map_balive)
    # print_raster_value_counts(clipped_tree_map_balive)
    classes_balive = [
        (0, 60, 1, QColor(0, 0, 200, 255), "Sparse <60"),
        (60, 120, 1, QColor(0, 200, 0, 255), "Healthy 60-120"),
        (120, 180, 2, QColor(255, 180, 80, 255), "Dense 120-180"),
        (180, 9999, 3, QColor(220, 50, 50, 255), "Extreme >180")
    ]
    balive_layer = reclassify_raster(clipped_tree_map_balive, forestry_dir, classes=classes_balive)
    balive_layer.setOpacity(1.0)
    # add_layer_to_group(tpa_dead_layer, tree_map_group)
    set_layer_state(balive_layer, True, False)

    tree_map_canopypct_raster_path =  "/opt/dev/gis/TreeMap/TreeMap2022_CONUS_CANOPYPCT/TreeMap2022_CONUS_CANOPYPCT.tif"
    clipped_tree_map_canopypct, path = clip_raster_to_mask(tree_map_canopypct_raster_path, huc_layer, forestry_dir)
    #add_layer_to_group(clipped_tree_map_canopypct, tree_map_group)
    set_layer_state(clipped_tree_map_canopypct, False, False)

    tree_map_tpa_dead_raster_path =  "/opt/dev/gis/TreeMap/TreeMap2022_CONUS_TPA_DEAD/TreeMap2022_CONUS_TPA_DEAD.tif"
    clipped_tree_map_tpa_dead, path = clip_raster_to_mask(tree_map_tpa_dead_raster_path, huc_layer, forestry_dir)
    #add_layer_to_group(clipped_tree_map_tpa_dead, tree_map_group)
    set_layer_state(clipped_tree_map_tpa_dead, False, False)

    open_et_path = "/opt/dev/gis/OpenET/8ac409f632cecc4ec3f62d12807823a7-ec15122101886c12354db14775427dde_getPixels.tiff"
    open_et, path = clip_raster_to_mask(open_et_path, huc_layer, forestry_dir)
    # add_layer_to_group(open_et, tree_map_group)
    set_layer_state(open_et, False, False)

    classes_tpa = [
        (0, 50, 1, QColor(200, 200, 200, 80), "Low <50"),
        (50, 100, 2, QColor(255, 180, 80, 255), "Medium 50-100"),
        (100, 9999, 3, QColor(220, 50, 50, 255), "High >100")
    ]
    tpa_dead_layer = reclassify_raster(clipped_tree_map_tpa_dead, forestry_dir, classes=classes_tpa)
    tpa_dead_layer.setOpacity(1.0)
    # add_layer_to_group(tpa_dead_layer, tree_map_group)
    set_layer_state(tpa_dead_layer, False, False)

    tree_map_tpa_live_raster_path =  "/opt/dev/gis/TreeMap/TreeMap2022_CONUS_TPA_LIVE/TreeMap2022_CONUS_TPA_LIVE.tif"
    clipped_tree_map_tpa_live, path = clip_raster_to_mask(tree_map_tpa_live_raster_path, huc_layer, forestry_dir)
    # add_layer_to_group(clipped_tree_map_tpa_live, tree_map_group)
    set_layer_state(clipped_tree_map_tpa_live, False, False)

