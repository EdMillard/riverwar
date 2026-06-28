"""
Copyright (c) 2025 Ed Millard
"""
from osgeo import gdal
import numpy as np
from pathlib import Path
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer, QgsCoordinateReferenceSystem
from qgis.PyQt.QtGui import QColor
from gis.forest_type import forest_types
import processing # type: ignore

conus_raster_path = "/opt/dev/gis/USFS/conus_foresttype.img"
huc_name = "HUC8"

def clip_conus_to_huc(forestry_dir: Path, huc_layer):
    print(f"Clipping full CONUS vegtype to {huc_name}...")
    output_clipped_veg = forestry_dir / f"vegtype_{huc_name.replace(' ', '_')}.tif"

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
        'OUTPUT': str(output_clipped_veg)
    }

    result = processing.run("gdal:cliprasterbymasklayer", params)
    clipped_veg_layer = QgsRasterLayer(result['OUTPUT'], f"VegType_{huc_name}")

    if clipped_veg_layer.isValid():
        QgsProject.instance().addMapLayer(clipped_veg_layer)
        print(f"✅ Clipped vegtype added (kept outside group)")
        return clipped_veg_layer, result['OUTPUT']
    else:
        raise Exception("❌ Failed to create clipped vegtype")


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


def create_forest_group():
    root = QgsProject.instance().layerTreeRoot()
    group_name = "Forest Types"

    existing = root.findGroup(group_name)
    if existing:
        root.removeChildNode(existing)

    group = root.insertGroup(0, group_name)
    group.setExpanded(False)
    group.setItemVisibilityChecked(False)

    print(f"✅ Created collapsed group at top: '{group_name}'")
    return group


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

def build_forest_layers(forestry_dir: Path, huc_layer, huc8_name: str):
    clipped_veg_layer, clipped_veg_path = clip_conus_to_huc(forestry_dir, huc_layer)
    present_types = list_vegtypes_in_clipped(clipped_veg_path, huc8_name)

    # === Style the clipped layer (this is what you see as VegType_HUC8) ===
    style_clipped_layer(clipped_veg_layer, present_types)

    forest_group = create_forest_group()

    for code, info in forest_types.items():
        if code not in [p[0] for p in present_types]:
            continue
        name = info["name"]
        color = info["color"]
        extract_tree_type_from_clipped(forestry_dir, clipped_veg_path, code, name, color, forest_group)

    return