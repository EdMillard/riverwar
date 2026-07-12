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
# https://data.fs.usda.gov/geodata/edw/datasets.php
# https://data-usfs.hub.arcgis.com/datasets/f8fb12b1bab44c11b1bee96562cc4773
# https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/
#
from osgeo import gdal
import numpy as np
from pathlib import Path
from qgis.core import (QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer, QgsProcessingException, QgsRasterBandStats,
                       QgsSingleBandGrayRenderer, QgsContrastEnhancement, QgsProject)
from qgis.PyQt.QtGui import QColor
from gis.forest_type import forest_types
from gis.layer import clip_raster_to_mask, create_group, add_layer_to_group, set_layer_state
import processing # type: ignore
from typing import Optional

huc_name = "HUC8"

def list_vegtypes_in_layer(input_item, forest_types: dict):
    """
    List vegetation types present in a raster.
    Works with either a file path (str/Path) or a QgsRasterLayer.
    """
    print(f"\n=== Vegetation Types Present ===")

    # Handle both path and layer
    if isinstance(input_item, (str, Path)):
        ds = gdal.Open(str(input_item))
        layer_name = Path(input_item).stem
    else:
        # It's a QgsRasterLayer
        ds = gdal.Open(input_item.source())
        layer_name = input_item.name()

    if ds is None:
        print("❌ Could not open raster")
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

    print(f"\nTotal unique types found in '{layer_name}': {len(present)}\n")
    ds = None  # close dataset
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


def apply_discrete_colors(
        layer: QgsRasterLayer,
        class_colors: dict,  # {value: (color, label)}
        band: int = 1,
        opacity: float = 0.9
):
    """
    Apply colors to specific discrete values (no reclassification needed).

    Example:
    class_colors = {
        1: (QColor(0, 200, 0, 255), "Seedlings/Saplings"),
        2: (QColor(100, 255, 100, 255), "Small trees"),
        3: (QColor(255, 255, 100, 255), "Medium trees"),
        4: (QColor(255, 140, 0, 255), "Large trees"),
        5: (QColor(220, 50, 50, 255), "Multi-layered"),
        0: (QColor(150, 150, 150, 255), "No Data")
    }
    """
    if not layer or not layer.isValid():
        print("❌ Invalid layer")
        return

    renderer_classes = []
    for value, (color, label) in class_colors.items():
        renderer_classes.append(
            QgsPalettedRasterRenderer.Class(value, color, label)
        )

    renderer = QgsPalettedRasterRenderer(layer.dataProvider(), band, renderer_classes)
    layer.setRenderer(renderer)
    layer.setOpacity(opacity)
    layer.triggerRepaint()

    QgsProject.instance().addMapLayer(layer)
    print(f"✅ Styled discrete classes on: {layer.name()}")

def print_raster_value_counts(raster_layer: QgsRasterLayer, band: int = 1):
    if not raster_layer or not raster_layer.isValid():
        print("❌ Invalid raster layer")
        return

    provider = raster_layer.dataProvider()
    extent = raster_layer.extent()
    width = raster_layer.width()
    height = raster_layer.height()

    block = provider.block(band, extent, width, height)
    data_buffer = block.data()

    # Read as flat array first
    array = np.frombuffer(data_buffer, dtype=np.float32)

    expected = height * width
    actual = len(array)

    print(f"Expected pixels: {expected:,}, Actual buffer: {actual:,}")

    if actual < expected:
        print("⚠️ Buffer smaller than expected (likely NoData or masked raster). Using available data.")
        # Pad with NoData if needed, or just use what we have
        array = np.pad(array, (0, expected - actual), mode='constant', constant_values=np.nan)
    elif actual > expected:
        array = array[:expected]

    array = array.reshape(height, width)

    # Round to integer
    rounded = np.round(array).astype(int)

    unique, counts = np.unique(rounded, return_counts=True)
    sorted_counts = dict(sorted(zip(unique, counts)))

    total = array.size   # or np.count_nonzero(~np.isnan(array)) if you want to exclude NaN

    print(f"\n✅ Value counts for: {raster_layer.name()}")
    print(f"   Total pixels: {total:,}")
    print(f"   Unique values: {len(unique)}\n")
    print(f"{'Value':>8} | {'Count':>12} | {'%':>7}")
    print("-" * 35)

    for value, count in sorted_counts.items():
        percent = (count / total) * 100 if total > 0 else 0
        print(f"{value:8d} | {count:12,} | {percent:6.2f}%")

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
    present_types = list_vegtypes_in_layer(clipped_veg_path, forest_types)

    # === Style the clipped layer (this is what you see as VegType_HUC8) ===
    style_clipped_layer(clipped_veg_layer, present_types)

    forest_group = create_group("Forest Types")

    for code, info in forest_types.items():
        if code not in [p[0] for p in present_types]:
            continue
        name = info["name"]
        color = info["color"]
        extract_tree_type_from_clipped(forestry_dir, clipped_veg_path, code, name, color, forest_group)

def style_rasters_consistently(
        layers: list,
        method: str = "shared_scale",
        num_classes: int = 5,
        opacity: float = 0.85,
        color_ramp: list = None
):
    """
    Style multiple rasters consistently and add them to the map.
    """
    if color_ramp is None:
        color_ramp = [
            QColor(0, 100, 0, 255),
            QColor(100, 200, 0, 255),
            QColor(255, 255, 100, 255),
            QColor(255, 140, 0, 255),
            QColor(200, 0, 0, 255)
        ]

    # Collect statistics
    stats = []
    all_mins = []
    all_maxs = []

    for layer in layers:
        provider = layer.dataProvider()
        stat = provider.bandStatistics(1, QgsRasterBandStats.All)

        stats.append({
            'layer': layer,
            'min': stat.minimumValue,
            'max': stat.maximumValue,
            'mean': stat.mean
        })
        all_mins.append(stat.minimumValue)
        all_maxs.append(stat.maximumValue)

    global_min = min(all_mins)
    global_max = max(all_maxs)

    print(f"Global range: {global_min:.1f} — {global_max:.1f}")

    for s in stats:
        layer = s['layer']

        if method == "shared_scale":
            breaks = np.linspace(global_min, global_max, num_classes + 1)
        else:
            breaks = np.linspace(s['min'], s['max'], num_classes + 1)

        # Build classes
        renderer_classes = []
        for i in range(num_classes):
            low = breaks[i]
            high = breaks[i + 1]
            color = color_ramp[i % len(color_ramp)]
            label = f"{low:.0f}–{high:.0f}"
            renderer_classes.append(
                QgsPalettedRasterRenderer.Class(i + 1, color, label)
            )

        renderer = QgsPalettedRasterRenderer(layer.dataProvider(), 1, renderer_classes)
        layer.setRenderer(renderer)
        layer.setOpacity(opacity)
        layer.triggerRepaint()

        # Add to map
        # QgsProject.instance().addMapLayer(layer)
        print(f"✅ Styled and added: {layer.name()}")

    print("🎉 All layers styled and added to the map!")

def normalize_grayscale_rasters(layers: list, global_min=None, global_max=None):
    """
    Normalize multiple rasters to the same grayscale range so 128 = middle value.
    """
    # Get global min/max if not provided
    if global_min is None or global_max is None:
        all_mins = []
        all_maxs = []
        for layer in layers:
            stat = layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
            all_mins.append(stat.minimumValue)
            all_maxs.append(stat.maximumValue)
        global_min = min(all_mins)
        global_max = max(all_maxs)

    print(f"Normalizing to range: {global_min:.1f} — {global_max:.1f}")

    for layer in layers:
        renderer = QgsSingleBandGrayRenderer(layer.dataProvider(), 1)

        # Set contrast enhancement to stretch to global min/max
        ce = QgsContrastEnhancement()
        ce.setMinimumValue(global_min)
        ce.setMaximumValue(global_max)
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
        renderer.setContrastEnhancement(ce)

        layer.setRenderer(renderer)
        layer.setOpacity(1.0)  # full opacity for grayscale
        layer.triggerRepaint()

        QgsProject.instance().addMapLayer(layer)
        print(f"Normalized grayscale: {layer.name()}")

    print("✅ All layers normalized to same grayscale scale")

def create_overstocked_mortality_layer(
    balive_layer: QgsRasterLayer,
    tpa_dead_layer: QgsRasterLayer,
    output_dir: Path,
    output_name: str = "Overstocked_HighMortality",
    balive_threshold: float = 160,      # adjust as needed
    tpa_dead_threshold: float = 50,
    opacity: float = 0.9
) -> QgsRasterLayer:
    """
    Creates a raster showing areas that are both too dense (high BALIVE) and high mortality.
    """
    output_path = output_dir / f"{output_name}.tif"

    # Step 1: Reclassify BALIVE
    balive_reclass = [
        (0, balive_threshold, 1, QColor(100, 200, 100, 80), "Normal Density"),
        (balive_threshold, 9999, 2, QColor(255, 100, 100, 80), "Too Dense")
    ]

    balive_params = {
        'INPUT_RASTER': balive_layer,
        'RASTER_BAND': 1,
        'TABLE': [item for c in balive_reclass for item in c[:3]],
        'NO_DATA': 0,
        'RANGE_BOUNDARIES': 0,
        'OUTPUT': 'memory:balive_reclass'
    }
    balive_re = processing.run("native:reclassifybytable", balive_params)['OUTPUT']

    # Step 2: Reclassify TPA_DEAD
    tpa_params = {
        'INPUT_RASTER': tpa_dead_layer,
        'RASTER_BAND': 1,
        'TABLE': [0, tpa_dead_threshold, 1, tpa_dead_threshold, 9999, 2],
        'NO_DATA': 0,
        'RANGE_BOUNDARIES': 0,
        'OUTPUT': 'memory:tpa_reclass'
    }
    tpa_re = processing.run("native:reclassifybytable", tpa_params)['OUTPUT']

    # Step 3: Combine (Too Dense AND High Mortality)
    combine_params = {
        'INPUT_A': balive_re,
        'INPUT_B': tpa_re,
        'BAND_A': 1,
        'BAND_B': 1,
        'FORMULA': '(A@1 == 2) * (B@1 == 2) * 1',   # 1 = Overstocked + High Mortality
        'NO_DATA': 0,
        'OUTPUT': str(output_path)
    }
    result = processing.run("gdal:rastercalculator", combine_params)

    combined_layer = QgsRasterLayer(result['OUTPUT'], output_name)

    if combined_layer.isValid():
        # Simple 2-class renderer
        classes = [
            QgsPalettedRasterRenderer.Class(0, QColor(150, 150, 150, 80), "Normal"),
            QgsPalettedRasterRenderer.Class(1, QColor(220, 50, 50, 255), "Too Dense + High Mortality")
        ]
        renderer = QgsPalettedRasterRenderer(combined_layer.dataProvider(), 1, classes)
        combined_layer.setRenderer(renderer)
        combined_layer.setOpacity(opacity)
        combined_layer.triggerRepaint()

        QgsProject.instance().addMapLayer(combined_layer)
        print(f"✅ Created Overstocked + High Mortality layer: {output_name}")
        return combined_layer
    else:
        raise Exception("Failed to create combined layer")

# overstocked = create_overstocked_mortality_layer(
#     balive_layer=balive_layer,
#      tpa_dead_layer=tpa_dead_layer,
#     output_dir=forestry_dir,
#     balive_threshold=160,
#     tpa_dead_threshold=50
# )

def create_high_canopy_low_et_risk(
    canopy_layer: QgsRasterLayer,
    et_layer: QgsRasterLayer,
    output_dir: Path,
    output_name: str = "HighCanopy_LowET_Risk",
    canopy_threshold: float = 60,      # % canopy cover considered "high"
    et_threshold: float = 150,         # adjust based on your ET units (mm)
    opacity: float = 0.9
) -> QgsRasterLayer:
    """
    Creates a raster showing areas with high canopy cover but unexpectedly low ET.
    """
    output_path = output_dir / f"{output_name}.tif"

    # Reclassify Canopy
    canopy_params = {
        'INPUT_RASTER': canopy_layer,
        'RASTER_BAND': 1,
        'TABLE': [0, canopy_threshold, 1, canopy_threshold, 9999, 2],
        'NO_DATA': 0,
        'RANGE_BOUNDARIES': 0,
        'OUTPUT': 'memory:canopy_reclass'
    }
    canopy_re = processing.run("native:reclassifybytable", canopy_params)['OUTPUT']

    # Reclassify ET (low ET = risk)
    et_params = {
        'INPUT_RASTER': et_layer,
        'RASTER_BAND': 1,
        'TABLE': [0, et_threshold, 2, et_threshold, 9999, 1],
        'NO_DATA': 0,
        'RANGE_BOUNDARIES': 0,
        'OUTPUT': 'memory:et_reclass'
    }
    et_re = processing.run("native:reclassifybytable", et_params)['OUTPUT']

    # Combine: High Canopy (2) AND Low ET (2) = Risk (1)
    combine_params = {
        'INPUT_A': canopy_re,
        'INPUT_B': et_re,
        'BAND_A': 1,
        'BAND_B': 1,
        'FORMULA': '(A@1 == 2) * (B@1 == 2) * 1',
        'NO_DATA': 0,
        'OUTPUT': str(output_path)
    }
    result = processing.run("gdal:rastercalculator", combine_params)

    risk_layer = QgsRasterLayer(result['OUTPUT'], output_name)

    if risk_layer.isValid():
        classes = [
            QgsPalettedRasterRenderer.Class(0, QColor(150, 150, 150, 80), "Normal"),
            QgsPalettedRasterRenderer.Class(1, QColor(220, 50, 50, 255), "High Canopy + Low ET (Risk)")
        ]
        renderer = QgsPalettedRasterRenderer(risk_layer.dataProvider(), 1, classes)
        risk_layer.setRenderer(renderer)
        risk_layer.setOpacity(opacity)
        risk_layer.triggerRepaint()

        QgsProject.instance().addMapLayer(risk_layer)
        print(f"✅ Created High Canopy + Low ET Risk layer: {output_name}")
        return risk_layer
    else:
        raise Exception("Failed to create risk layer")

# risk = create_high_canopy_low_et_risk(
#     canopy_layer=canopy_layer,
#     et_layer=et_layer,
#     output_dir=forestry_dir,
#     canopy_threshold=60,
#     et_threshold=150   # adjust based on your ET units
# )



def build_tree_map_layers(forestry_dir: Path, huc_layer, huc12_layer):

    tree_map_layers = {}
    tree_map_files = [
        'TreeMap2022_CONUS_BALIVE',
        'TreeMap2022_CONUS_FLDTYPCD',   # Recommended
    ]
    tree_map_files_all = [
        'TreeMap2022_CONUS_BALIVE',
        "TreeMap2022_CONUS_CANOPYPCT",

        'TreeMap2022_CONUS_FLDTYPCD',   # Recommended
        # 'TreeMap2022_CONUS_FORTYPCD',

        'TreeMap2022_CONUS_STANDHT',

        'TreeMap2022_CONUS_STDSZCD',    # Recommended
        # 'TreeMap2022_CONUS_FLDSZCD',

        'TreeMap2022_CONUS_TPA_DEAD',
        'TreeMap2022_CONUS_TPA_LIVE',

        'TreeMap2022_CONUS_VOLBFNET_L',
        'TreeMap2022_CONUS_VOLCFNET_D',
        'TreeMap2022_CONUS_VOLCFNET_L',
    ]
    for raster_file in tree_map_files:
        raster_path =  f"/opt/dev/gis/TreeMap/{raster_file}/{raster_file}.tif"
        layer_name = raster_file.replace('TreeMap2022_CONUS_', '')
        layer, path = clip_raster_to_mask(raster_path, huc_layer, forestry_dir, output_name=layer_name)
        tree_map_layers[layer_name] = layer

    layer:Optional[QgsRasterLayer, None] = tree_map_layers.get('FLDTYPCD', None)
    if layer is not None:
        present_types = list_vegtypes_in_layer(layer, forest_types)
        style_clipped_layer(layer, present_types)
        set_layer_state(layer, True, False)

    layer:Optional[QgsRasterLayer, None] = tree_map_layers.get('STDSZCD', None)
    if layer is not None:
        # print_raster_value_counts(layer)
        # counts = raster_value_counts(layer)
        stand_colors = {
            1: (QColor(0, 200, 0, 255), "1 - Seedlings/Saplings"),
            2: (QColor(100, 255, 100, 255), "2 - Small trees"),
            3: (QColor(255, 255, 100, 255), "3 - Medium trees"),
            4: (QColor(255, 140, 0, 255), "4 - Large trees"),
            5: (QColor(220, 50, 50, 255), "5 - Multi-layered / Old Growth"),
            0: (QColor(150, 150, 150, 255), "No Data")
        }
        apply_discrete_colors(layer, stand_colors)

    layer:Optional[QgsRasterLayer, None] = tree_map_layers.get('BALIVE', None)
    if layer is not None:
        # print_raster_value_counts(layer)
        # counts = raster_value_counts(layer)
        classes_balive = [
            (0, 60, 1, QColor(0, 80, 0, 255), "Sparse <60"),
            (60, 120, 2, QColor(0, 200, 0, 255), "Healthy 60-120"),
            (120, 180, 3, QColor(255, 180, 80, 255), "Dense 120-180"),
            (180, 9999, 4, QColor(220, 50, 50, 255), "Extreme >180")
        ]
        classified_layer = reclassify_raster(layer, forestry_dir, classes=classes_balive)
        tree_map_layers[classified_layer.name()+'_Classified'] = classified_layer

    layer:Optional[QgsRasterLayer, None] = tree_map_layers.get('TPA_DEAD', None)
    if layer is not None:
        classes_tpa = [
            (0, 50, 1, QColor(200, 200, 200, 80), "Low <50"),
            (50, 100, 2, QColor(255, 180, 80, 255), "Medium 50-100"),
            (100, 9999, 3, QColor(220, 50, 50, 255), "High >100")
        ]
        classified_layer = reclassify_raster(layer, forestry_dir, classes=classes_tpa)
        tree_map_layers[classified_layer.name() + '_Classified'] = classified_layer

    return tree_map_layers


def build_open_et_layers(forestry_dir, huc_layer, huc12_layer):
    month = 5
    open_et_layers = []
    for year in range(2018, 2027):
        open_et_path = f"/opt/dev/gis/OpenET/stoner_mesa_{month:02d}_{year}.tiff"
        try:
            open_et, path = clip_raster_to_mask(open_et_path, huc_layer, forestry_dir)
            open_et_layers.append(open_et)
        except QgsProcessingException:
            print(f"⚠️  Skipping {year} - file not found: {open_et_path}")
            continue  # or pass
    normalize_grayscale_rasters(open_et_layers)

    open_et_group = create_group("OpenET Stoner Mesa", position=0)
    for layer in open_et_layers:
        add_layer_to_group(layer, open_et_group,)
        set_layer_state(layer, False, False)

