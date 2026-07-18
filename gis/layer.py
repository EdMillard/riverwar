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
from qgis.core import (QgsRasterLayer, QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem, QgsFeatureRequest, QgsFeature, QgsProcessingFeedback,
                       QgsSingleSymbolRenderer, QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsWkbTypes)
from PyQt5.QtCore import QDate, QDateTime
import datetime
from collections import defaultdict
from osgeo import ogr
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
import zipfile
import tempfile
from typing import Optional, List
from qgis.core import QgsApplication

def zoom_to_layer(layer):
    if layer and layer.isValid():
        extent = layer.extent()
        # extent.scale(1.12)  # Slightly larger view
        canvas = iface.mapCanvas()  # type: ignore[attr-defined]
        canvas.setExtent(extent)
        canvas.refresh()
    else:
        print(f"⚠️ Could not zoom to {layer.name()}")

def refresh_display(pause: float = 0.03):
    """Force QGIS GUI and map to update"""
    QgsApplication.processEvents()

    canvas = iface.mapCanvas()
    canvas.refresh()
    canvas.repaint()

    # Safely repaint all layers
    root = QgsProject.instance().layerTreeRoot()
    for tree_layer in root.findLayers():           # this is the correct way
        layer = tree_layer.layer()
        if layer:
            layer.triggerRepaint()

    time.sleep(pause)

def reset_layer_parent_to_root():
    """Reset new layers to be added to the project root"""
    root = QgsProject.instance().layerTreeRoot()

    # Main fix
    iface.layerTreeView().setCurrentLayer(None)  # deselect any group

    # Force root as default
    root.setCustomProperty("addLayersToGroup", False)

    # print("✅ Default parent reset to Root (new layers will go to top level)")

def clip_to_mask_fast(source_layer, mask_layer, project_dir, output_name):
    """
    Fast clipping using spatial index.\
    This is fussier on geometry errors and not sure it's faster
    """
    if source_layer is None or mask_layer is None:
        print("❌ Invalid input layer")
        return None, None

    output_path = os.path.join(project_dir, f"{output_name}_clipped.gpkg")

    # Use 'native:clip' with better parameters or fallback to intersection
    params = {
        'INPUT': source_layer,
        'OVERLAY': mask_layer,
        'OUTPUT': output_path
    }

    print(f"Clipping {source_layer.featureCount():,} features... (this may take a while)")

    try:
        result = processing.run("native:clip", params, feedback=QgsProcessingFeedback())
        clipped_layer = QgsVectorLayer(output_path, output_name, "ogr")

        if clipped_layer.isValid():
            print(f"✅ Successfully Clipped : {clipped_layer.featureCount():,} features")
            QgsProject.instance().addMapLayer(clipped_layer)
            return clipped_layer, output_path
        else:
            print("❌ Clipped layer is invalid")
            return None, None
    except Exception as e:
        print(f"❌ Clipping error: {e}")
        return None, None

def fix_geometries(layer):
    """Fix invalid geometries in a layer."""
    if layer is None or not layer.isValid():
        print("❌ Invalid layer")
        return None

    params = {
        'INPUT': layer,
        'OUTPUT': 'memory:Fixed_' + layer.name()
    }

    result = processing.run("native:fixgeometries", params)
    fixed_layer = result['OUTPUT']

    print(f"✅ Fixed geometries. Original features: {layer.featureCount()}, Fixed: {fixed_layer.featureCount()}")
    return fixed_layer

def _parse_date(val):
    """Handles QDate, QDateTime, strings, etc."""
    if isinstance(val, QDate):
        return val.toPyDate()

    if isinstance(val, QDateTime):
        date_part = val.date()
        return date_part.toPyDate() if not date_part.isNull() else None

    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val

    if isinstance(val, str):
        clean = val.split('(')[0].strip()
        formats = [
            '%m/%d/%y %H:%M:%S', '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d',
            '%m/%d/%y', '%m/%d/%Y'
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(clean, fmt).date()
            except ValueError:
                continue
    return None

def split_layer_by_date(layer: QgsVectorLayer,
                        date_field: str = 'DATE_COMPLETED',
                        fallback_field: str = 'DATE_AWARDED',
                        divider_dates: Optional[list] = None,
                        base_name=None,
                        base_color: QColor = QColor(255, 0, 255)) -> Optional[List[QgsVectorLayer]]:
    """
    Split layer by date. Newest decade = full base_color brightness.
    Older decades get progressively darker (down to 20% brightness).
    """
    if layer is None or not layer.isValid():
        print("❌ Invalid input layer")
        return []

    if base_name is None:
        base_name = layer.name()

    # Collect valid dates
    dates = []
    for feat in layer.getFeatures():
        val = feat[date_field] or feat[fallback_field]
        d = _parse_date(val)
        if d:
            dates.append(d)

    if not dates:
        print(f"❌ No valid dates found in '{date_field}' or '{fallback_field}'")
        return []

    min_date = min(dates)
    max_date = max(dates)

    # === Define bins ===
    if divider_dates is None:
        # Decade bins
        start_year = (min_date.year // 10) * 10
        end_year = ((max_date.year // 10) * 10) + 10

        bin_starts = [datetime.date(y, 1, 1) for y in range(start_year, end_year + 11, 10)]
        bin_labels = [f"{y}s" for y in range(start_year, end_year + 11, 10)]
    else:
        # Custom dividers
        bin_starts = []
        for d in divider_dates:
            parsed = _parse_date(d)
            if parsed:
                bin_starts.append(parsed)
        bin_starts = sorted(set(bin_starts))
        bin_labels = [d.strftime('%Y') for d in bin_starts]

    # Build bin ranges
    bins = []
    for i in range(len(bin_starts)):
        start = bin_starts[i]
        end = bin_starts[i + 1] if i + 1 < len(bin_starts) else datetime.date(9999, 12, 31)
        label = bin_labels[i] if i < len(bin_labels) else f"{start.year}s"
        bins.append((start, end, label))

    # Group features
    grouped = defaultdict(list)
    for feat in layer.getFeatures():
        val = feat[date_field] or feat[fallback_field]
        d = _parse_date(val)
        if not d:
            continue
        for start, end, label in bins:
            if start <= d < end:
                grouped[label].append(feat)
                break

    # Create layers - newest to oldest with color ramp
    created_layers = []
    sorted_bins = sorted(bins, key=lambda x: x[0], reverse=True)  # Newest first
    n = len(sorted_bins)

    for i, (start, end, label) in enumerate(sorted_bins):
        features = grouped.get(label, [])
        if not features:
            continue

        # Brightness from 100% (newest) to 20% (oldest)
        factor = 1.0 - (i / max(n - 1, 1) * 0.8)   # 1.0 → 0.2

        # Scale color
        r = int(base_color.red() * factor)
        g = int(base_color.green() * factor)
        b = int(base_color.blue() * factor)
        color = QColor(r, g, b)

        new_layer = QgsVectorLayer("Polygon", f"{label}", "memory")
        new_layer.setCrs(layer.crs())
        provider = new_layer.dataProvider()
        provider.addAttributes(layer.fields())
        new_layer.updateFields()

        for feat in features:
            new_feat = QgsFeature(new_layer.fields())
            new_feat.setGeometry(feat.geometry())
            new_feat.setAttributes(feat.attributes())
            provider.addFeature(new_feat)

        new_layer.updateExtents()

        # Apply solid color (no opacity ramp)
        renderer = QgsSingleSymbolRenderer.defaultRenderer(new_layer.geometryType())
        symbol = renderer.symbol()
        symbol.setColor(color)
        new_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(new_layer)
        created_layers.append(new_layer)

        print(f"✅ Created: {base_name} {label} | Features: {len(features):,} | Color: {color.name()} ({factor:.0%} brightness)")

    print(f"\n✅ Split complete. {len(created_layers)} layers created.")
    return created_layers

def load_vector_layer_masked(name: str, path: str, mask_layer: QgsVectorLayer, project_dir: Path,
                             color: QColor = QColor(100, 255, 100),
                             layer_name: str = None) -> Optional[QgsVectorLayer]:
    """
    General purpose loader + clip + color.
    Works with .gpkg, .gdb (unzipped), and zipped GDBs.
    """
    if not path or not os.path.exists(path):
        print(f"❌ Path does not exist: {path}")
        return None

    os.makedirs(project_dir, exist_ok=True)

    clipped_name = f"{name}.gpkg"
    clipped_path = os.path.join(project_dir, clipped_name)

    # Try cached version first
    if os.path.exists(clipped_path):
        print(f"🔄 Found cached: {clipped_name}")
        vector_layer = QgsVectorLayer(clipped_path, name, "ogr")
        if vector_layer.isValid() and vector_layer.featureCount() > 0:
            apply_solid_color(vector_layer, color)
            QgsProject.instance().addMapLayer(vector_layer)
            return vector_layer

    # === Load original layer ===
    p = Path(path)
    lower = str(p).lower()

    print(f"Loading original: {path}")

    if lower.endswith('.gpkg'):
        # Auto-detect first layer if none provided
        internal = layer_name
        if not internal:
            ds = ogr.Open(path)
            if ds and ds.GetLayerCount() > 0:
                internal = ds.GetLayer(0).GetName()
            ds = None
        temp_layer = load_gpkg_with_ogr(path, internal, f"Temp_{name}")

    elif lower.endswith('.zip') and '.gdb' in lower:   # zipped GDB
        internal = layer_name or "Perimeters"
        uri = f"/vsizip/{path}|layername={internal}"
        temp_layer = QgsVectorLayer(uri, f"Temp_{name}", "ogr")

    elif p.suffix.lower() == '.gdb' or '.gdb' in str(p):   # unzipped GDB folder
        internal = layer_name
        if not internal:
            print("⚠️ For .gdb you should pass layer_name= (internal name)")
            # Auto-pick first layer
            ds = ogr.Open(str(p))
            if ds and ds.GetLayerCount() > 0:
                internal = ds.GetLayer(0).GetName()
                print(f"   Auto-selected: {internal}")
            ds = None
        temp_layer = load_gdb_layer(path, internal, f"Temp_{name}")

    else:
        temp_layer = QgsVectorLayer(path, f"Temp_{name}", "ogr")

    if not temp_layer or not temp_layer.isValid():
        print(f"❌ Failed to load original: {name}")
        return None

    print(f"   Original: {temp_layer.featureCount():,} features")

    # === Fix geometries + Clip ===
    try:
        fixed = processing.run("native:fixgeometries", {'INPUT': temp_layer, 'OUTPUT': 'memory:Fixed'})['OUTPUT']
    except:
        fixed = temp_layer

    try:
        result = processing.run("native:clip", {
            'INPUT': fixed,
            'OVERLAY': mask_layer,
            'OUTPUT': clipped_path
        })
        vector_layer = QgsVectorLayer(clipped_path, name, "ogr")
    except Exception as e:
        print(f"❌ Clipping failed: {e}")
        return None

    if vector_layer.isValid() and vector_layer.featureCount() > 0:
        apply_solid_color(vector_layer, color)
        QgsProject.instance().addMapLayer(vector_layer)
        print(f"✅ Loaded + clipped: {name} ({vector_layer.featureCount():,} features)")
        return vector_layer

    print("❌ Final layer invalid or empty")
    return None

def apply_solid_color(layer: QgsVectorLayer, color: QColor):
    """Apply a solid color to the layer based on geometry type."""
    geom_type = layer.geometryType()

    if geom_type == QgsWkbTypes.PointGeometry:
        symbol = QgsMarkerSymbol.createSimple({
            'color': color.name(),
            'size': '2.5',
            'outline_color': 'black',
            'outline_width': '0.2'
        })
    elif geom_type == QgsWkbTypes.LineGeometry:
        symbol = QgsLineSymbol.createSimple({
            'color': color.name(),
            'width': '1.8'
        })
    else:  # Polygon
        symbol = QgsFillSymbol.createSimple({
            'color': color.name(),
            'outline_color': 'black',
            'outline_width': '0.4'
        })

    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    layer.triggerRepaint()

def inspect_gpkg_layers(gpkg_path: str):
    print(f"\n🔍 Inspecting: {os.path.basename(gpkg_path)}")
    ds = ogr.Open(gpkg_path)
    if ds is None:
        print("   ❌ Could not open with OGR")
        return

    for i in range(ds.GetLayerCount()):
        layer = ds.GetLayer(i)
        print(f"   Layer {i}: '{layer.GetName()}'  ({layer.GetFeatureCount()} features)")


def remove_features_by_attribute_fast(layer: QgsVectorLayer, field_name: str = "gnis_name"):
    """Simple & reliable filter for NHD flowlines"""
    if not layer or not layer.isValid():
        print("❌ Invalid layer")
        return layer

    # Create a new memory layer with only features that HAVE a gnis_name
    expression = f'"{field_name}" IS NOT NULL AND "{field_name}" != \'\''

    result = processing.run("native:extractbyexpression", {
        'INPUT': layer,
        'EXPRESSION': expression,
        'OUTPUT': 'memory:Flowlines_With_Name'
    })['OUTPUT']

    print(f"✅ Kept {result.featureCount():,} features with {field_name}")

    # Optional: replace the original layer in the project
    # QgsProject.instance().removeMapLayer(layer.id())
    # QgsProject.instance().addMapLayer(result)

    return result

def remove_features_by_attribute(layer: QgsVectorLayer, field_name: str, value=None):
    """
    Remove features where field equals value (default: NULL/None)
    """
    if not layer or not layer.isValid():
        print("❌ Invalid layer")
        return 0

    if value is None:
        # Remove where field IS NULL
        expression = f'"{field_name}" IS NULL'
    else:
        expression = f'"{field_name}" = {value}' if isinstance(value, (int, float)) else f'"{field_name}" = \'{value}\''

    layer.selectByExpression(expression)
    count = layer.selectedFeatureCount()

    if count > 0:
        layer.startEditing()
        layer.deleteSelectedFeatures()
        layer.commitChanges()
        print(f"✅ Removed {count} features where {field_name} = {value}")
    else:
        print(f"No features found where {field_name} = {value}")

    return count

def create_group(group_name, position:Optional[int]=None, visible=False, existing_layer=None, layers=None, layer_dict=None, ):
    root = QgsProject.instance().layerTreeRoot()
    existing = root.findGroup(group_name)
    if existing:
        root.removeChildNode(existing)

    if existing_layer is not None:
        existing_layer_node = root.findLayer(existing_layer.id())
        if existing_layer_node:
            group = root.insertGroup(root.children().index(existing_layer_node), group_name)
        else:
            print(f"Existing group invalid {group_name}")
            return None
    elif position is None:
        group = root.addGroup(group_name)
    else:
        group = root.insertGroup(0, group_name)

    if layer_dict is not None:
        # print(f"Add Layers to Group {group_name}")
        for key, layer in layer_dict.items():
            add_layer_to_group(layer, group)
            set_layer_state(layer, visible, False)
            layer.triggerRepaint()
            # layer.setOpacity(1.0)'
    elif layers is not None:
        # print(f"Add Layers to Group {group_name}")
        for layer in layers:
            add_layer_to_group(layer, group)
            set_layer_state(layer, visible, False)
            layer.triggerRepaint()
            # layer.setOpacity(1.0)'
    group.setExpanded(False)
    group.setItemVisibilityChecked(visible)
    return group

def add_layer_to_group(layer, group):
    group.addLayer(layer)
    # Remove from EVERYWHERE else
    root = QgsProject.instance().layerTreeRoot()
    root.removeLayer(layer)

    # group.setExpanded(False)
    # group.setItemVisibilityChecked(False)

def get_symbol(layer):
    renderer = layer.renderer()
    if renderer:
        if hasattr(renderer, 'symbol') and renderer.symbol() is not None:
            return renderer.symbol()   # type: ignore[attr-defined]
    return None

def force_collapse(layer):
    if layer is not None:
        root = QgsProject.instance().layerTreeRoot()
        node = root.findLayer(layer.id())
        if node:
            node.setExpanded(False)
            for child in node.children():
                child.setExpanded(False)
            iface.layerTreeView().refreshLayerSymbology(layer.id())
            # iface.layerTreeView().collapseAll()

def force_group_visibility(group, visible:bool = True):
    # Set visibility
    group.setItemVisibilityChecked(visible)

    # Force UI refresh for groups
    view = iface.layerTreeView()
    view.update()  # important for groups
    iface.mapCanvas().refresh()

    # Alternative strong refresh
    view.refreshLayerSymbology("")  # dummy to trigger full refresh

def set_layer_state(layer, visible:bool, expanded:bool):
    root = QgsProject.instance().layerTreeRoot()
    layer_node = root.findLayer(layer.id())
    if layer_node:
        layer_node.setItemVisibilityChecked(visible)  # Hidden
        layer_node.setExpanded(expanded)


def load_gpkg_with_ogr(gpkg_path: str, layer_name: str, display_name: str = None, group=None):
    """
    Load a (possibly zipped) GeoPackage layer into QGIS.
    """
    print(f'Loading {gpkg_path} | layer: {layer_name}')

    # Handle zipped GeoPackages
    if gpkg_path.lower().endswith('.zip'):
        # Use GDAL Virtual File System for zip
        zip_path = f"/vsizip/{os.path.abspath(gpkg_path)}"
        # Usually the .gpkg is inside with same basename or we need to find it
        gpkg_inside = None
        ds = ogr.Open(zip_path)
        if ds:
            # Try to find the .gpkg file inside the zip
            for i in range(ds.GetLayerCount()):
                lyr = ds.GetLayer(i)
                if lyr:
                    gpkg_inside = lyr.GetName()  # often works
                    break
        if not gpkg_inside:
            # Common fallback: same name as zip but .gpkg
            base = os.path.splitext(os.path.basename(gpkg_path))[0]
            gpkg_inside = f"{base}.gpkg"

        open_path = f"{zip_path}/{gpkg_inside}"
    else:
        open_path = gpkg_path

    # Open with OGR first (for validation)
    ds = ogr.Open(open_path)
    if ds is None:
        print("❌ Failed to open with OGR")
        return None

    # Create QGIS layer
    uri = f"{open_path}|layername={layer_name}"
    qgis_layer = QgsVectorLayer(uri, display_name or layer_name, "ogr")

    if not qgis_layer.isValid():
        print("❌ QGIS layer is invalid")
        print("   Error:", qgis_layer.error().message())
        return None

    # Add to project (with the group hack you mentioned)
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    if group:
        # Remove from root first (important for some rendering issues)
        root.removeLayer(qgis_layer)
        project.addMapLayer(qgis_layer, False)  # add without legend
        group.addLayer(qgis_layer)
    else:
        project.addMapLayer(qgis_layer)

    print(f"✅ Successfully loaded: {display_name or layer_name}")
    return qgis_layer

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


def list_gdb_layers(gdb_path: str):
    if not os.path.exists(gdb_path):
        print("❌ Path not found")
        return []

    # Correct path for this specific zip
    inner_gdb = "Data/FPA_FOD_20221014.gdb"
    uri = f"/vsizip/{gdb_path}/{inner_gdb}"

    print(f"Opening with URI: {uri}")

    vlayer = QgsVectorLayer(uri, "temp", "ogr")

    if vlayer.isValid():
        sublayers = vlayer.dataProvider().subLayers()
        print(f"\n✅ SUCCESS! Layers found: {len(sublayers)}")

        layer_list = []
        for sub in sublayers:
            parts = sub.split('|')
            name = parts[0]
            layer_list.append(name)
            print(f"   • {name}")

        return layer_list
    else:
        print("❌ Still failed")
        print("Error:", vlayer.error().message())
        return []


def load_gdb_layer(gdb_path: str, layer_name: str, display_name: str = None):
    gdb_path = str(Path(gdb_path).resolve())

    if not Path(gdb_path).exists():
        print(f"❌ GDB folder not found: {gdb_path}")
        return None

    if display_name is None:
        display_name = layer_name

    # Clean URI - no vsizip, no inner Data/ folder
    uri = f"{gdb_path}|layername={layer_name}"
    print(f"Opening with URI: {uri}")

    layer = QgsVectorLayer(uri, display_name, "ogr")

    if layer.isValid():
        QgsProject.instance().addMapLayer(layer)
        print(f"✅ SUCCESS: {display_name} ({layer.featureCount():,} features)")
        return layer
    else:
        print(f"❌ Failed to load '{layer_name}'")
        print("   Error:", layer.error().message())
        # Show what layers actually exist
        list_gdb_layers(gdb_path)
        return None

def load_vector_layer(path: str, name: str = None, color: QColor = QColor(40, 40, 40)):
    if not os.path.exists(path):
        raise Exception(f"❌ File not found: {path}")

    layer_name = name or Path(path).stem.replace("_", " ")

    actual_path = path

    if path.lower().endswith('.zip'):
        # print(f"📦 Zip file detected: {path}")

        # Use a persistent temp folder instead of TemporaryDirectory
        tmpdir = Path("/tmp/qgis_extract") / Path(path).stem
        tmpdir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        shp_files = list(tmpdir.glob("**/*.shp"))
        if not shp_files:
            raise Exception("❌ No .shp file found inside the zip!")

        actual_path = str(shp_files[0])
        # print(f"   Extracted to: {actual_path}")

    # Load with QGIS directly (skip OGR for now)
    qgis_layer = QgsVectorLayer(actual_path, layer_name, "ogr")
    symbol = get_symbol(qgis_layer)
    if symbol is not None:
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
    input_layer,
    mask_layer,
    output_dir: Path,
    output_name: str = None,
    target_crs: str = "EPSG:4269",
    nodata: int = -9999,
    crop_to_cutline: bool = True,
    keep_resolution: bool = True
):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle input...
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

    # print(f"Clipping {'raster' if is_raster else 'vector'} to mask...")

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
        # === VECTOR CLIP WITH GEOMETRY FIX ===
        # First fix invalid geometries
        fix_params = {
            'INPUT': input_path,
            'OUTPUT': 'memory:Fixed_Geometries'
        }
        fixed_layer = processing.run("native:fixgeometries", fix_params)['OUTPUT']

        # Then clip
        clip_params = {
            'INPUT': fixed_layer,
            'OVERLAY': mask_layer,
            'OUTPUT': str(output_path)
        }
        result = processing.run("native:clip", clip_params)
        clipped_layer = QgsVectorLayer(str(output_path), output_name, "ogr")

    if clipped_layer.isValid():
        QgsProject.instance().addMapLayer(clipped_layer)
        # print(f"✅ Clipped successfully: {output_name} ({clipped_layer.featureCount()} features)")
        return clipped_layer, str(output_path)
    else:
        raise Exception(f"❌ Failed to clip layer: {output_name}")

def tight_clip_raster(
    input_layer: QgsRasterLayer,
    mask_layer,                    # polygon layer or feature
    output_path: Path = None,
    name: str = None
) -> QgsRasterLayer:
    """
    Clip raster tightly to mask with minimal NoData.
    """
    if output_path is None:
        output_path = Path("/tmp") / f"{input_layer.name()}_clipped.tif"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if name is None:
        name = input_layer.name() + "_clipped"

    clipped_layer = tight_clip_raster(
        input_layer=input_layer,
        mask_layer=mask_layer,
        output_path=output_path
    )

    if 0:
        params = {
            'INPUT': input_layer,
            'MASK': mask_layer,
            'SOURCE_CRS': input_layer.crs(),
            'TARGET_CRS': input_layer.crs(),
            'CROP_TO_CUTLINE': True,      # Important for tight clip
            'KEEP_NODATA': False,         # Helps reduce NoData padding
            'OUTPUT': str(output_path)
        }

        result = processing.run("gdal:cliprasterbymasklayer", params)
        clipped_layer = QgsRasterLayer(result['OUTPUT'], name)

    if clipped_layer.isValid():
        QgsProject.instance().addMapLayer(clipped_layer)
        print(f"✅ Tight clip created: {clipped_layer.name()}")
        return clipped_layer
    else:
        raise Exception("Failed to create clipped raster")


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

    # print(f"Clipping raster: {Path(input_raster_path).name}")

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
        # print(f"✅ Clipped raster added: {output_name}")
        return clipped_layer, result['OUTPUT']
    else:
        raise Exception(f"❌ Failed to clip raster: {input_raster_path}")

def remove_layer(layer):
    """Remove a layer by passing the layer object"""
    if layer is None:
        print("❌ No layer provided")
        return False
    # print(f"✅ Removed layer: {layer.name()}")
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

    # print("✅ Thorough reset complete — project should be empty")

