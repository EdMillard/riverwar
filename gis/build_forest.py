"""
Copyright (c) 2025 Ed Millard
"""
import sys
import os
import time
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
from osgeo import ogr
import processing   # type: ignore
import importlib
import zipfile
import tempfile
from pathlib import Path

script_paths = ["/opt/dev/riverwar"]
for p in script_paths:
    if p not in sys.path:
        sys.path.append(p)
        print(f"Added to Python path: {p}")

from gis.contours import extract_contours, select_contours_on_layer
from gis.make_forest_layers import build_forest_layers

# ====================== GLOBAL PROJECT SETTINGS ======================
# TARGET_CRS = "EPSG:5070"
TARGET_CRS = "EPSG:4269"
huc_name = "HUC8"
huc8_name =  "Upper Dolores"

base_path:Path = Path("/opt/dev/gis/")
huc8_dir_name = huc_name + '_' + huc8_name.replace(" ", "_")
forestry_dir = base_path / huc8_dir_name
forestry_dir.mkdir(parents=True, exist_ok=True)

contour_vector_path = "contours_reprojected.shp"

def reload_modules():
    modules_to_reload = [
        'gis.make_forest_layers',
        'gis.forest_type',
        'gis.contours',
        # add any other modules you edit often
    ]
    for mod in modules_to_reload:
        if mod in sys.modules:
            importlib.reload(sys.modules[mod])
            print(f"✅ Reloaded {mod}")
        else:
            print(f"⚠️  {mod} not loaded yet")

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
    iface.mapCanvas().refresh() # type: ignore[attr-defined]
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
    symbol = get_symbol(huc_layer)
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
    if result is None:
        print("❌ Processing algorithm failed (returned None)")
    elif 'OUTPUT' not in result:
        print("❌ No OUTPUT in result")
        print("Result keys:", list(result.keys()))

    reproj_layer = QgsVectorLayer(output_path, new_name, "ogr")

    print(f"Reprojected features: {reproj_layer.featureCount()}")

    # Style
    symbol = get_symbol(reproj_layer)
    symbol.setColor(QColor(255, 0, 100))
    symbol.setWidth(0.7)

    QgsProject.instance().addMapLayer(reproj_layer)
    print(f"✅ Added: {new_name}")
    return reproj_layer

def load_vector_layer(path: str, name: str = None, color: QColor = QColor(40, 40, 40)):
    if not os.path.exists(path):
        raise Exception(f"❌ File not found: {path}")

    layer_name = name or Path(path).stem.replace("_", " ")

    actual_path = path

    if path.lower().endswith('.zip'):
        print(f"📦 Zip file detected: {path}")

        # Use a persistent temp folder instead of TemporaryDirectory
        tmpdir = Path("/tmp/qgis_extract") / Path(path).stem
        tmpdir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        shp_files = list(tmpdir.glob("**/*.shp"))
        if not shp_files:
            raise Exception("❌ No .shp file found inside the zip!")

        actual_path = str(shp_files[0])
        print(f"   Extracted to: {actual_path}")

    # Load with QGIS directly (skip OGR for now)
    qgis_layer = QgsVectorLayer(actual_path, layer_name, "ogr")
    symbol = get_symbol(qgis_layer)
    symbol.setColor(color)

    if not qgis_layer.isValid():
        raise Exception(f"❌ Failed to load layer from {actual_path}")

    QgsProject.instance().addMapLayer(qgis_layer)
    # qgis_layer.triggerRepaint()

    print(f"✅ Successfully loaded: {layer_name} ({qgis_layer.featureCount()} features)")
    return qgis_layer

def load_gpkg_from_zip(zip_path: str, layer_name: str, display_name: str = None):
    """
    Extract .gpkg from zip and load a specific layer.
    Works with files like NHD_H_14030002_HU8_GPKG.zip
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    print(f"📦 Extracting GPKG from zip: {zip_path.name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Extract everything
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(tmpdir)

        # Find the .gpkg file
        gpkg_files = list(tmpdir.glob("**/*.gpkg"))
        if not gpkg_files:
            raise Exception("No .gpkg file found inside the zip!")

        gpkg_path = gpkg_files[0]
        print(f"   Extracted: {gpkg_path.name}")

        # Now load the layer
        full_path = f"{gpkg_path}|layername={layer_name}"
        layer = QgsVectorLayer(full_path, display_name or layer_name, "ogr")

        if not layer.isValid():
            print(f"❌ Failed to load layer '{layer_name}'")
            return None

        QgsProject.instance().addMapLayer(layer)
        print(f"✅ Loaded {layer.name()} ({layer.featureCount()} features) from zipped GPKG")
        return layer

def ensure_crs_target(layer, layer_name: str = None):
    if layer is None or not layer.isValid():
        print("❌ Input layer is invalid")
        return None

    target = QgsCoordinateReferenceSystem(TARGET_CRS)

    if layer.crs() == target:
        print(f"✅ Already in {TARGET_CRS}")
        return layer

    print(f"🔄 Reprojecting {layer_name or layer.name()} → {TARGET_CRS}")

    output_path = forestry_dir / f"{(layer_name or layer.name()).replace(' ', '_')}_{TARGET_CRS.split(':')[1]}.gpkg"

    params = {
        'INPUT': layer,
        'TARGET_CRS': target,
        'OUTPUT': str(output_path),
        'OPERATION': '',           # Let QGIS choose best transformation
        'ERROR': 0.0               # Tolerance
    }

    result = processing.run("native:reprojectlayer", params)
    if result is None:
        print("❌ Processing algorithm failed (returned None)")
        # Optionally raise or return early
    elif 'OUTPUT' not in result:
        print("❌ No OUTPUT in result")
        print("Result keys:", list(result.keys()))

    new_layer = QgsVectorLayer(str(output_path), layer_name or layer.name(), "ogr")

    print(f"   New layer feature count: {new_layer.featureCount()}")

    if new_layer.featureCount() == 0:
        print("❌ Reprojection produced empty layer! Possible causes:")
        print("   - Invalid geometries in source")
        print("   - CRS transformation failed")
        print("   - Features outside valid area")
        # Optional: save without reprojection as fallback
        QgsProject.instance().addMapLayer(layer)
        return layer

    QgsProject.instance().addMapLayer(new_layer)

    print(f"✅ Successfully reprojected: {new_layer.featureCount()} features")
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
    symbol = get_symbol(final_layer)
    symbol.setColor(QColor(40, 40, 40))
    final_layer.setOpacity(0.65)

    QgsProject.instance().addMapLayer(final_layer)

    print(f"✅ Successfully created: HUC8 ({TARGET_CRS}, {final_layer.featureCount()} features)")

    return final_layer

def get_symbol(layer):
    """Safe way to get symbol (avoids PyCharm unresolved attribute warning)"""
    renderer = layer.renderer()
    if renderer is not None:
        return renderer.symbol()   # type: ignore[attr-defined]
    return None

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
    symbol = get_symbol(final_layer)
    symbol.setColor(QColor(0, 100, 200))
    final_layer.setOpacity(0.45)

    QgsProject.instance().addMapLayer(final_layer)
    print(f"✅ Final HUC12 layer ready: HUC12s ({final_layer.featureCount()} features)")

    return final_layer

def clip_to_mask(
    input_layer,           # Can be path (str/Path) or QgsLayer object
    mask_layer,            # Vector mask (usually HUC8)
    output_dir: Path,
    output_name: str = None,
    target_crs: str = "EPSG:4269",
    nodata: int = -9999,
    crop_to_cutline: bool = True,
    keep_resolution: bool = True
):
    """
    General purpose clip: works on both raster and vector.
    Returns (clipped_layer, output_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle input as path or layer
    if isinstance(input_layer, (str, Path)):
        input_path = str(input_layer)
        layer_name = Path(input_layer).stem
        is_raster = input_path.lower().endswith(('.tif', '.img', '.asc', '.dem'))
    else:
        input_path = input_layer
        layer_name = input_layer.name() if hasattr(input_layer, 'name') else "clipped"
        is_raster = isinstance(input_layer, QgsRasterLayer)

    if output_name is None:
        output_name = f"{layer_name}_clipped"

    output_path = output_dir / f"{output_name}.{'tif' if is_raster else 'gpkg'}"

    print(f"Clipping {'raster' if is_raster else 'vector'} to mask...")

    # Reproject mask if needed
    if mask_layer.crs().authid() != target_crs:
        print("Reprojecting mask layer...")
        params = {
            'INPUT': mask_layer,
            'TARGET_CRS': QgsCoordinateReferenceSystem(target_crs),
            'OUTPUT': 'memory:Reprojected_Mask'
        }
        mask_layer = processing.run("native:reprojectlayer", params)['OUTPUT']

    if is_raster:
        # Raster clipping
        params = {
            'INPUT': input_path,
            'MASK': mask_layer,
            'NODATA': nodata,
            'CROP_TO_CUTLINE': crop_to_cutline,
            'KEEP_RESOLUTION': keep_resolution,
            'OUTPUT': str(output_path)
        }
        result = processing.run("gdal:cliprasterbymasklayer", params)
        clipped_layer = QgsRasterLayer(result['OUTPUT'], output_name)

    else:
        # Vector clipping
        params = {
            'INPUT': input_path,
            'OVERLAY': mask_layer,
            'OUTPUT': str(output_path)
        }
        result = processing.run("native:clip", params)
        if result is None:
            print("❌ Processing algorithm failed (returned None)")
            # Optionally raise or return early
        elif 'OUTPUT' not in result:
            print("❌ No OUTPUT in result")
            print("Result keys:", list(result.keys()))

        clipped_layer = QgsVectorLayer(str(output_path), output_name, "ogr")

    if clipped_layer.isValid():
        QgsProject.instance().addMapLayer(clipped_layer)
        print(f"✅ Clipped successfully: {output_name}")
        return clipped_layer, str(output_path)
    else:
        raise Exception(f"❌ Failed to clip layer: {output_name}")

def load_gpkg_with_ogr(gpkg_path: str, layer_name: str, display_name: str = None):
    gpkg_path = Path(gpkg_path)

    ds = ogr.Open(str(gpkg_path))
    if ds is None:
        print(f"❌ Failed to open {gpkg_path}")
        return None

    ogr_layer = ds.GetLayerByName(layer_name)
    if ogr_layer is None:
        print(f"❌ Layer '{layer_name}' not found")
        return None

    print(f"✅ OGR loaded {ogr_layer.GetFeatureCount()} features from '{layer_name}'")

    # Create QGIS layer
    qgis_layer = QgsVectorLayer(
        f"{gpkg_path}|layername={layer_name}",
        display_name or layer_name,
        "ogr"
    )

    if qgis_layer.isValid():
        QgsProject.instance().addMapLayer(qgis_layer)
        print(f"✅ Added to QGIS: {qgis_layer.name()}")
        return qgis_layer
    else:
        print("❌ QGIS layer is invalid")
        return None

def build(huc_layer, huc8_name:str):
    build_forest_layers(forestry_dir, huc_layer, huc8_name)

    path = forestry_dir / contour_vector_path
    print(f"Contour path {path}")
    contour_layer = load_vector_layer(str(path), "ELEV_Cortez_E_CO_1X1_Shape — Shape/Elev_Contour.shp", QColor(80, 80, 80))
    temp_contour_layer = extract_contours("ELEV_Cortez_E_CO_1X1_Shape — Shape/Elev_Contour.shp",
                     [8440, 9000, 10000, 11000, 12000],
                     "Temp Major Contours")
    elevation_layer, elevation_path = clip_to_mask(temp_contour_layer, huc_layer, forestry_dir, "Elevation Contours")
    layer_node = QgsProject.instance().layerTreeRoot().findLayer(elevation_layer.id())
    if layer_node:
        layer_node.setItemVisibilityChecked(False)
    symbol = get_symbol(elevation_layer)
    symbol.setColor(QColor(0, 0, 0))
    symbol.setWidth(0.5)
    select_contours_on_layer(elevation_layer, [9000], highlight_color=QColor(200, 000, 0))

    nhd_gpkg_path = "/opt/dev/gis/NHD/NHD_H_14030002_HU8_GPKG.gpkg"  # extracted

    water_body_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDWaterbody")
    symbol = get_symbol(water_body_layer)
    symbol.setColor(QColor(64, 64, 255))

    river_layer = load_gpkg_with_ogr(nhd_gpkg_path, "NHDArea")
    symbol = get_symbol(river_layer)
    symbol.symbolLayer(0).setStrokeColor(QColor(64, 64, 255))
    symbol.symbolLayer(0).setStrokeWidth(0.4)

    temp_weather_station_layer = load_vector_layer("/opt/dev/gis/CO_DWR/ClimateStationPOR.zip", "Teno Weather Stations", QColor(0, 0, 0))
    weather_station_layer, weather_station_path = clip_to_mask(temp_weather_station_layer, huc_layer, forestry_dir, "Weather Stations")
    remove_layer(temp_weather_station_layer)
    weather_station_layer.setOpacity(1.0)
    symbol = get_symbol(weather_station_layer)
    if symbol:
        symbol.setColor(QColor(255, 0, 0))
        symbol.setSize(2)
        symbol.setOpacity(0.9)

    remove_layer(temp_contour_layer)
    remove_layer(contour_layer)

    iface.mapCanvas().setExtent(huc_layer.extent()) # type: ignore[attr-defined]
    iface.mapCanvas().refresh()                     # type: ignore[attr-defined]

reset_qgis()
reload_modules()

print("\n=== Starting HUC8 Build ===")

wbd_huc8 = load_huc8_from_wbd("/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg")  # Load Upper Colorado HU2, HUC8
huc8_layer = extract_and_reproject_huc8(wbd_huc8, huc8_name)
remove_layer(wbd_huc8)
huc12_layer = extract_huc12_in_huc8('/opt/dev/gis/WBD/WBD_14_HU2_GPKG.gpkg', huc8_name)
build(huc8_layer, huc8_name)