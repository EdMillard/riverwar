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
from pathlib import Path
import processing # type: ignore
import time
import os
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
import zipfile
import tempfile

def get_symbol(layer):
    """Safe way to get symbol (avoids PyCharm unresolved attribute warning)"""
    renderer = layer.renderer()
    if renderer is not None:
        return renderer.symbol()   # type: ignore[attr-defined]
    return None

# Not used
def reproject_layer(forestry_dir:Path, layer, new_name=None):
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

def ensure_crs(forestry_dir:Path, target_crs:str, layer, layer_name: str = None):
    if layer is None or not layer.isValid():
        print("❌ Input layer is invalid")
        return None

    target = QgsCoordinateReferenceSystem(target_crs)

    if layer.crs() == target:
        print(f"✅ Already in {target_crs}")
        return layer

    print(f"🔄 Reprojecting {layer_name or layer.name()} → {target_crs}")

    output_path = forestry_dir / f"{(layer_name or layer.name()).replace(' ', '_')}_{target_crs.split(':')[1]}.gpkg"

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

def clip_raster_to_mask(
    input_raster_path: str,
    mask_layer,
    output_dir: Path,
    output_name: str = None,
    target_crs: str = "EPSG:5070",
    nodata: int = -9999
):
    """
    General purpose raster clipper.
    Works with TreeMap, CONUS Forest Type, or any other raster.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_name is None:
        output_name = Path(input_raster_path).stem + "_clipped"

    output_path = output_dir / f"{output_name}.tif"

    print(f"Clipping raster: {Path(input_raster_path).name}")

    # Reproject mask if needed
    if mask_layer.crs().authid() != target_crs:
        print(f"Reprojecting mask to {target_crs}...")
        params = {
            'INPUT': mask_layer,
            'TARGET_CRS': QgsCoordinateReferenceSystem(target_crs),
            'OUTPUT': 'memory:Reprojected_Mask'
        }
        mask_layer = processing.run("native:reprojectlayer", params)['OUTPUT']

    # Clip the raster
    params = {
        'INPUT': input_raster_path,
        'MASK': mask_layer,
        'NODATA': nodata,
        'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': True,
        'OUTPUT': str(output_path)
    }

    result = processing.run("gdal:cliprasterbymasklayer", params)

    clipped_layer = QgsRasterLayer(result['OUTPUT'], output_name)

    if clipped_layer.isValid():
        QgsProject.instance().addMapLayer(clipped_layer)
        print(f"✅ Clipped raster added: {output_name}")
        return clipped_layer, result['OUTPUT']
    else:
        raise Exception(f"❌ Failed to clip raster: {input_raster_path}")

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
    iface.mapCanvas().refresh()  # type: ignore[attr-defined]
    time.sleep(0.8)  # longer wait

    print("✅ Thorough reset complete — project should be empty")

