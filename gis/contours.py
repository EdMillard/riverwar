"""
Copyright (c) 2025 Ed Millard

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
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QColor
from qgis.utils import iface
import processing


def extract_contours(layer_name: str,
                     elevations: list,
                     output_name: str = None,
                     line_color: QColor = QColor(0, 0, 0),
                     line_width: float = 0.35):
    """
    Extract contours with controllable color and line width.
    Default width = 0.35 (nice and thin)
    """
    layers = QgsProject.instance().mapLayersByName(layer_name)
    if not layers:
        print(f"❌ Layer '{layer_name}' not found!")
        return None

    layer = layers[0]

    # Build expression
    if isinstance(elevations, (int, float)):
        elevations = [elevations]

    expr_parts = [f'"ContourEle" = {elev}' for elev in elevations]
    expression = " OR ".join(expr_parts)

    params = {
        'INPUT': layer,
        'EXPRESSION': expression,
        'OUTPUT': 'memory:Temp_Contours'
    }

    result = processing.run("native:extractbyexpression", params)
    new_layer = result['OUTPUT']

    # Set name
    if output_name is None:
        elev_str = ", ".join(map(str, elevations))
        output_name = f"Contours {elev_str} ft"
    new_layer.setName(output_name)

    # Style with thinner lines
    symbol = new_layer.renderer().symbol()
    symbol.setColor(line_color)
    symbol.setWidth(line_width)  # Much thinner now

    QgsProject.instance().addMapLayer(new_layer)
    print(f"✅ Created '{output_name}' — color: {line_color.name()}, width: {line_width}")
    return new_layer

def select_contours_on_layer(layer, elevations, highlight_color: QColor = QColor(255, 0, 0)):
    """
    Select contours and highlight them with a color.
    """
    if layer is None:
        print("❌ No layer provided")
        return 0

    if isinstance(elevations, (int, float)):
        elevations = [elevations]

    expr_parts = [f'"ContourEle" = {elev}' for elev in elevations]
    expression = " OR ".join(expr_parts)

    layer.selectByExpression(expression)
    count = layer.selectedFeatureCount()

    print(f"✅ Selected {count} features matching {elevations}")

    if count > 0:
        # Highlight selected features
        iface.mapCanvas().setSelectionColor(highlight_color)
        iface.mapCanvas().zoomToSelected(layer)

    return count

contour_layer = extract_contours("ELEV_Cortez_E_CO_1X1_Shape — Shape/Elev_Contour.shp",
                 [8000, 9000, 10000, 11000, 12000],
                 "Major Contours 8k-12k ft")


select_contours_on_layer(contour_layer, [10000, 11000], highlight_color=QColor(200, 000, 0))


