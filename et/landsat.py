import ee
ee.Initialize()

# Define your area (Lizard Head SNOTEL area)
area = ee.Geometry.Point([-108.0, 37.7]).buffer(5000)  # adjust buffer

# Load Landsat collection
landsat = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')  # or LT05, LE07, etc.
           .filterBounds(area)
           .filterDate('1985-01-01', '2025-12-31'))

# Example: Annual median NDVI (proxy for forest density)
def add_ndvi(image):
    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    return image.addBands(ndvi)

ndvi_collection = landsat.map(add_ndvi)

annual_ndvi = ndvi_collection.select('NDVI').reduce(ee.Reducer.median()).clip(area)

# Export or chart changes
print(annual_ndvi.getInfo())  # or export to Drive