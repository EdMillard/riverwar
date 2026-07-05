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
import csv
from pathlib import Path
from qgis.utils import iface
from qgis.core import (
    QgsFeature,  QgsRectangle, QgsFillSymbol, QgsProject, QgsGeometry, QgsVectorLayer,  QgsCoordinateReferenceSystem, QgsCoordinateTransform,
)

openet_path:str='/opt/dev/gis/OpenET/'

def create_openet_boundary_csv(output_path: Path, layer_name:str=""):
    """
    Takes currently selected polygons, dissolves them, gets outer boundary,
    and writes the exact OpenET CSV format.
    """
    project = QgsProject.instance()

    if layer_name:
        layers = project.mapLayersByName(layer_name)
        layer = layers[0] if layers else None
    else:
        layer = iface.activeLayer()

    if not layer:
        print("❌ No layer found")
        return

    selected = layer.selectedFeatures()
    if not selected:
        print("❌ No features selected")
        return

    # Dissolve all selected geometries into one
    dissolved = QgsGeometry.unaryUnion([f.geometry() for f in selected])

    # Get outer boundary (exterior ring)
    if dissolved.isMultipart():
        dissolved = dissolved.asMultiPolygon()[0]  # take first part
    else:
        dissolved = dissolved.asPolygon()

    exterior_ring = dissolved[0]  # exterior ring

    # Build points list
    points = []
    for vertex in exterior_ring:
        points.append((vertex.x(), vertex.y()))

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id","vertex_index","vertex_part","vertex_part_ring","vertex_part_index","distance","angle","lon","lat"])

        for i, (x, y) in enumerate(points[:-1]):   # exclude duplicate closing point
            writer.writerow([
                "1", str(i), "0", "0", str(i), "0.00000000000000", "0.00000000000000",
                round(x, 8), round(y, 8)
            ])

    print(f"✅ OpenET boundary CSV created: {output_path}")
    print(f"   From {len(selected)} selected features")
    print(f"   Vertices: {len(points)-1}")
    return output_path


def create_openet_rectangle_csv(output_path: Path, layer_name: str = None):
    layer = iface.activeLayer()
    if not layer:
        print("No active layer")
        return

    selected = layer.selectedFeatures()
    if not selected:
        print("No features selected")
        return

    # Compute combined extent
    extent = QgsRectangle()
    for f in selected:
        extent.combineExtentWith(f.geometry().boundingBox())

    # Calculate area in acres (using equal-area projection)
    # Albers Equal Area (good for CONUS)
    equal_area_crs = QgsCoordinateReferenceSystem("EPSG:5070")
    transform = QgsCoordinateTransform(layer.crs(), equal_area_crs, QgsProject.instance())

    geom = QgsGeometry.fromRect(extent)
    geom.transform(transform)
    acres = geom.area() / 4046.86  # square meters to acres

    # Counter-clockwise rectangle (closed)
    rect = [
        (extent.xMinimum(), extent.yMinimum()),
        (extent.xMinimum(), extent.yMaximum()),
        (extent.xMaximum(), extent.yMaximum()),
        (extent.xMaximum(), extent.yMinimum()),
        (extent.xMinimum(), extent.yMinimum()),  # close ring
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "vertex_index", "vertex_part", "vertex_part_ring", "vertex_part_index", "distance", "angle", "lon",
             "lat"])

        for i, (x, y) in enumerate(rect):
            writer.writerow([
                "1", str(i), "0", "0", str(i), "0.00000000000000", "0.00000000000000",
                round(x, 8), round(y, 8)
            ])

    print(f"✅ Rectangle CSV created: {output_path}")
    print(f"   Bounds: {extent.toString()}")
    print(f"   Area: {acres:,.2f} acres")
    return output_path

def create_openet_study_area_csv(output_path: Path, layer_name: str = None):
    project = QgsProject.instance()

    if layer_name:
        layers = project.mapLayersByName(layer_name)
        if not layers:
            print(f"❌ Layer '{layer_name}' not found")
            return
        layer = layers[0]
    else:
        layer = iface.activeLayer()

    if not layer or layer.type() != 0:
        print("❌ No valid vector layer")
        return

    # Force refresh selection
    iface.mapCanvas().refresh()

    selected = layer.selectedFeatures()
    print(f"Debug: Found {len(selected)} selected features on layer '{layer.name()}'")

    if len(selected) == 0:
        print("❌ Still no selected features. Try clicking the polygons again or using the Select Tool.")
        return

    # Proceed with extent
    extent = QgsRectangle()
    for f in selected[:2]:
        extent.combineExtentWith(f.geometry().boundingBox())

    rect = [
        (extent.xMinimum(), extent.yMinimum()),
        (extent.xMinimum(), extent.yMaximum()),
        (extent.xMaximum(), extent.yMaximum()),
        (extent.xMaximum(), extent.yMinimum()),
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id","vertex_index","vertex_part","vertex_part_ring","vertex_part_index","distance","angle","lon","lat"])

        for i, (x, y) in enumerate(rect):
            writer.writerow([
                "1", str(i), "0", "0", str(i), "0.00000000000000", "0.00000000000000",
                round(x, 8), round(y, 8)
            ])

    print(f"✅ CSV created: {output_path}")
    return output_path

def create_polygon_from_csv(csv_path: Path, layer_name: str = "Study_Area_Boundary"):
    points = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lon = float(row['lon'])
            lat = float(row['lat'])
            points.append((lon, lat))

    if points[0] != points[-1]:
        points.append(points[0])

    wkt = "POLYGON((" + ", ".join([f"{x} {y}" for x, y in points]) + "))"
    geom = QgsGeometry.fromWkt(wkt)

    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", layer_name, "memory")
    provider = layer.dataProvider()

    feature = QgsFeature()
    feature.setGeometry(geom)
    provider.addFeature(feature)

    # Simple black thin outline, no fill
    symbol = QgsFillSymbol.createSimple({
        'color': 'transparent',      # No fill
        'outline_color': 'black',
        'outline_width': '0.4'       # thin line
    })

    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()

    QgsProject.instance().addMapLayer(layer)
    print(f"✅ Black thin outline polygon created: {layer_name}")
    return layer

layer_name = 'lizard_head'
print("Create boundary CSV")
# create_openet_study_area_csv(Path(f"/opt/dev/gis/{layer_name}_study_area.csv"))
create_openet_rectangle_csv(Path(f"{openet_path}{layer_name}_study_area.csv"))
create_polygon_from_csv(Path(f"{openet_path}{layer_name}_study_area.csv"), layer_name)