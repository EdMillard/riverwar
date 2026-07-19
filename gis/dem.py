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
import os
import glob
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject
from qgis import processing

def build_dem_from_huc(
    huc_layer: QgsVectorLayer,
    dem_dir: str = "/opt/dev/gis/USGS_DEM",
    project_dir: str = None,
    to_feet: bool = True,
    add_to_project: bool = True,
    force_rebuild: bool = False
) -> QgsRasterLayer:
    if not huc_layer or not huc_layer.isValid():
        print("❌ Invalid HUC layer")
        return None

    if not project_dir:
        print("❌ project_dir is required")
        return None

    os.makedirs(project_dir, exist_ok=True)

    suffix = "_feet_clipped" if to_feet else "_meters_clipped"
    cache_path = os.path.join(project_dir, f"DEM{suffix}.tif")

    if os.path.exists(cache_path) and not force_rebuild:
        print(f"✅ Loading cached: {cache_path}")
        layer = QgsRasterLayer(cache_path, os.path.basename(cache_path))
        if layer.isValid():
            if add_to_project:
                QgsProject.instance().addMapLayer(layer)
            stats = layer.dataProvider().bandStatistics(1)
            print(f"   Range: {stats.minimumValue:.0f} to {stats.maximumValue:.0f}")
            return layer

    print("Building DEM...")

    dem_files = [f for f in glob.glob(os.path.join(dem_dir, "*.tif")) if QgsRasterLayer(f).isValid()]

    intersecting = []
    for tif in dem_files:
        r = QgsRasterLayer(tif)
        if r.isValid() and huc_layer.extent().intersects(r.extent()):
            # Tighter mask check
            try:
                test_clip = processing.run("gdal:cliprasterbymasklayer", {
                    'INPUT': tif,
                    'MASK': huc_layer,
                    'CROP_TO_CUTLINE': True,
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })['OUTPUT']
                test_layer = QgsRasterLayer(test_clip)
                if test_layer.isValid():
                    stats = test_layer.dataProvider().bandStatistics(1)
                    if stats.minimumValue < stats.maximumValue:  # has real variation
                        intersecting.append(tif)
                        print(f"  ✓ Mask intersect: {os.path.basename(tif)}")
                    else:
                        print(f"  ✗ Mask no real data: {os.path.basename(tif)}")
                else:
                    print(f"  ✗ Mask no intersect: {os.path.basename(tif)}")
            except:
                print(f"  ✗ Mask no intersect: {os.path.basename(tif)}")
        r = None

    print(f"Final intersecting tiles for merge: {len(intersecting)}")

    if not intersecting:
        print("❌ No intersecting DEMs after mask check")
        return None

    temp_merged = os.path.join(project_dir, "temp_merged.tif")
    processing.run("gdal:merge", {
        'INPUT': intersecting,
        'OUTPUT': temp_merged,
        'NODATA_INPUT': -9999,
        'NODATA_OUTPUT': -9999,
        'OPTIONS': 'COMPRESS=LZW',
        'DATA_TYPE': 5
    })

    temp_clipped = os.path.join(project_dir, "temp_clipped.tif")
    processing.run("gdal:cliprasterbymasklayer", {
        'INPUT': temp_merged,
        'MASK': huc_layer,
        'CROP_TO_CUTLINE': True,
        'NODATA': -9999,
        'OUTPUT': temp_clipped,
        'OPTIONS': 'COMPRESS=LZW',
        'DATA_TYPE': 5
    })

    if os.path.exists(temp_merged):
        os.remove(temp_merged)

    final_path = cache_path
    if to_feet:
        processing.run("gdal:rastercalculator", {
            'INPUT_A': temp_clipped,
            'BAND_A': 1,
            'FORMULA': '(A != -9999) * A * 3.28084 + (A == -9999) * -9999',
            'NO_DATA': -9999,
            'OUTPUT': final_path,
            'OPTIONS': 'COMPRESS=LZW',
            'DATA_TYPE': 5
        })
        if os.path.exists(temp_clipped):
            os.remove(temp_clipped)
    else:
        final_path = temp_clipped

    layer = QgsRasterLayer(final_path, os.path.basename(final_path).replace('.tif', ''))

    if layer.isValid():
        if add_to_project:
            QgsProject.instance().addMapLayer(layer)
        stats = layer.dataProvider().bandStatistics(1)
        print(f"✅ Seamless DEM ready: {final_path}")
        print(f"   Range: {stats.minimumValue:.0f} to {stats.maximumValue:.0f}")
        return layer
    else:
        print("❌ Failed to load final raster")
        return None