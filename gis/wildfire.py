
# https://data-nifc.opendata.arcgis.com/search?tags=historic_wildlandfire_opendata%2CCategory
# WFIGS
# https://data-nifc.opendata.arcgis.com/datasets/5e72b1699bf74eefb3f3aff6f4ba5511_0/explore?location=39.663857%2C-107.050782%2C8
# https://data.usgs.gov/datacatalog/data/USGS:61aa537dd34eb622f699df81
from gis.layer import load_gpkg_with_ogr

def build_wildfires():
    wildfire_recent_gpkg_path = '/opt/dev/gis/wildfire/WFIGS_Interagency_Perimeters_-6137106134146866405.gpkg'
    wildfire_recent = load_gpkg_with_ogr(wildfire_recent_gpkg_path, "Perimeters", "Wildfires Recent")

    wildfire_history_gpkg_path = '/opt/dev/gis/wildfire/InterAgencyFirePerimeterHistory_All_Years_View_5907997263350188958.gpkg'
    wildfire_recent = load_gpkg_with_ogr(wildfire_history_gpkg_path,'InteragencyFirePerimeterHistory', "Wildfires 2000-2018")
