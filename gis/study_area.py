import csv
from pathlib import Path
from qgis.core import QgsProject, QgsRectangle, QgsVectorLayer, QgsFeature, QgsGeometry, QgsWkbTypes
from qgis.utils import iface


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

create_openet_study_area_csv(Path("/opt/dev/gis/study_area.csv"))