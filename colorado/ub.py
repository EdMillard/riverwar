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
NATURAL_LEES_FERRY = 'Natural Lees Ferry'
SUPPLY = 'Supply'

UB_RESERVOIR_EVAP = 'UB Reservoir Evap'
GLEN_CANYON_RELEASE = 'Glen Canyon Release'
POWELL = 'Powell'
POWELL_DELTA = 'Powell Δ'
POWELL_EVAPORATION = 'Powell Evaporation'
POWELL_ELEVATION = 'Powell Elevation'
POWELL_ELEVATION_DELTA = 'Powell Δ Elevation'

GLEN_CANYON_RELEASE_WY = 'Glen Canyon WY Release'
POWELL_WY = 'Powell WY Active'
POWELL_MOST = 'Powell Most'
POWELL_MIN = 'Powell Min'
POWELL_ABOVE_3500 = 'Powell Above 3500'
POWELL_DELTA_WY = 'Powell WY Δ'
POWELL_EVAPORATION_WY = 'Powell WY Evaporation'
POWELL_ELEVATION_WY = 'Powell WY Elevation'
POWELL_ELEVATION_DELTA_WY = 'Powell WY Δ Elevation'
POWELL_INFLOW_WY = 'Powell Inflow WY'
POWELL_INFLOW = 'Powell Inflow'
POWELL_INFLOW_CFS = 'Powell Inflow CFS'
POWELL_INFLOW_UNREGULATED = 'Powell Inflow Unregulated'
POWELL_INFLOW_UNREGULATED_CFS = 'Powell Inflow Unregulated CFS'
POWELL_RELEASE = 'Powell Release'
POWELL_RELEASE_CFS = 'Powell Release CFS'

GLEN_CANYON = 'Glen Canyon '
LEES_FERRY_USGS = 'Lees Ferry USGS'
INFLOW_UNREGULATED = 'Inflow Unregulated'

GLEN_CANYON_WY = 'Glen Canyon WY'
LEES_FERRY_USGS_WY = 'Lees Ferry USGS WY'
INFLOW_WY = 'Inflow WY'
INFLOW_UNREGULATED_WY = 'Inflow Unregulated WY'

FLAMING_GORGE = 'Flaming Gorge'
FLAMING_GORGE_DELTA = 'Flaming Gorge Δ'
BLUE_MESA = 'Blue Mesa'

FLAMING_GORGE_WY = 'Flaming Gorge WY'
FLAMING_GORGE_MOST = 'Flaming Gorge Most'
FLAMING_GORGE_MIN = 'Flaming Gorge Min'
FLAMING_GORGE_ABOVE_5868 = 'Flaming Gorge Above 5868'
FLAMING_GORGE_DELTA_WY = 'Flaming Gorge WY Δ'
FLAMING_GORGE_RELEASE_WY = 'Flaming Gorge Release WY'
FLAMING_GORGE_RELEASE = 'Flaming Gorge Release'
FLAMING_GORGE_RELEASE_CFS = 'Flaming Gorge Release CFS'
FLAMING_GORGE_INFLOW_WY = 'Flaming Gorge Inflow WY'
FLAMING_GORGE_INFLOW = 'Flaming Gorge Inflow'
FLAMING_GORGE_INFLOW_CFS = 'Flaming Gorge Inflow CFS'
FLAMING_GORGE_INFLOW_UNREGULATED = 'Flaming Gorge Inflow Unregulated'
FLAMING_GORGE_INFLOW_UNREGULATED_CFS = 'Flaming Gorge Inflow Unregulated CFS'
FLAMING_GORGE_ELEVATION_WY = 'Flaming Gorge Elevation WY'
FLAMING_GORGE_EVAPORATION_WY = 'Flaming Gorge Evap WY'

BLUE_MESA_WY = 'Blue Mesa WY'
BLUE_MESA_DELTA_WY = 'Blue Mesa WY Δ'
BLUE_MESA_RELEASE_WY = 'Blue Mesa Release WY'
BLUE_MESA_RELEASE = 'Blue Mesa Release'
BLUE_MESA_RELEASE_CFS = 'Blue Mesa Release CFS'
BLUE_MESA_INFLOW_WY = 'Blue Mesa Inflow WY'
BLUE_MESA_INFLOW = 'Blue Mesa Inflow'
BLUE_MESA_INFLOW_CFS = 'Blue Mesa Inflow CFS'
BLUE_MESA_ELEVATION_WY = 'Blue Mesa Elevation WY'
BLUE_MESA_EVAPORATION_WY = 'Blue Mesa Evap WY'

NAVAJO_WY = 'Navajo WY'
NAVAJO_DELTA_WY = 'Navajo WY Δ'
NAVAJO_RELEASE_WY = 'Navajo Release WY'
NAVAJO_RELEASE = 'Navajo Release'
NAVAJO_RELEASE_CFS = 'Navajo Release CFS'
NAVAJO_POWER_RELEASE = 'Navajo Power Release'
NAVAJO_POWER_RELEASE_CFS = 'Navajo Power Release CFS'
NAVAJO_INFLOW_WY = 'Navajo Inflow WY'
NAVAJO_INFLOW = 'Navajo Inflow'
NAVAJO_INFLOW_CFS = 'Navajo Inflow CFS'
NAVAJO_ELEVATION_WY = 'Navajo Elevation WY'
NAVAJO_EVAPORATION_WY = 'Navajo Evap WY'

MORROW_EVAPORATION_WY = 'Morrow Evap WY'

UB_TOTAL = 'UB Total'
III_A_UB = 'III(a) Upper'
CU_CO = 'CO'
CU_UT = 'UT'
CU_WY = 'WY'
CU_NM = 'NM'
AZ_CU = 'AZ_'

# CO TMD's
CO_TRANS_MOUNTAIN_DIVERSIONS = 'CO TMD'

CO_WEST_SLOPE = 'CO'
# CO_WEST_SLOPE = 'West Slope'

CO_NORTHERN_WATER = 'Northern Water'
CDSS_CO_ADAMS_TUNNEL_DIVERSION = 'Adams Tunnel Diversion'   # CO, Northern Water
CDSS_CO_ADAMS_TUNNEL_RELEASE = 'Adams Tunnel Release'       # CO, Northern Water
CDSS_CO_ADAMS_TUNNEL = 'Adams Tunnel'                       # CO, Northern Water
USGS_CO_ADAMS_TUNNEL_GAGE = '09013000'                      # CO, Northern Water

# Denver Water
CO_DENVER_WATER = 'Denver Water'
CDSS_CO_MOFFAT_TUNNEL = 'Moffat Tunnel'    # CO, Denver Water
USGS_CO_MOFFAT_TUNNEL = 'Moffat Tunnel'    # CO, Denver Water
USGS_CO_MOFFAT_TUNNEL_GAGE = '09024000'    # CO, Denver Water

CDSS_CO_ROBERTS_TUNNEL = 'Roberts Tunnel'   # CO, Denver Water
USGS_CO_ROBERTS_TUNNEL = 'Roberts Tunnel'   # CO, Denver Water
USGS_CO_ROBERTS_TUNNEL_GAGE = '09063000'   # CO, Denver Water

# Fryark
CO_FRYARK = 'Fryark'
CDSS_CO_BOUSTEAD_TUNNEL = 'Boustead Tunnel'  # CO Fryark
CDSS_CO_BOUSTEAD_TUNNEL_DIVERSION = 'Boustead Tunnel Diversion'  # CO Fryark
CDSS_CO_BOUSTEAD_TUNNEL_RELEASE = 'Boustead Tunnel Release'  # CO Fryark

# Aurora
CO_AURORA = 'Aurora'
CDSS_CO_HOMESTAKE_TUNNEL = 'Homestake Tunnel CDSS' # CO, Aurora
USGS_CO_HOMESTAKE_TUNNEL = 'Homestake Tunnel' # CO, Aurora
USGS_CO_HOMESTAKE_TUNNEL_GAGE = '09064000' # CO, Aurora

# UT
USGS_UT_Duchesne_TUNNEL = 'Duchesne Tunnel'

USGS_UT_JORDAN_RIVER = 'Jordan River'
USGS_UT_JORDAN_RIVER_GAGE = '10171000'

# NM
USGS_NM_SAN_JUAN_CHAMA_TUNNEL = 'San Juan Chama Azotea Tunnel'
USGS_NM_SAN_JUAN_CHAMA_TUNNEL_GAGE = '08284160'
