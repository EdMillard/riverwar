"""
Copyright (c) 2022 Ed Millard

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
import datetime
import numpy as np
import signal
import sys
from source.usgs_gage import USGSGage
from source import usbr_report
from source import usbr_rise
from graph.water import WaterGraph
from pathlib import Path

interrupted = False

# matplotlib colors
# https://i.stack.imgur.com/lFZum.png


# noinspection PyUnusedLocal
def usbr_catalog():
    # unified_region_north_atlantic_appalachian = 1
    # unified_region_south_atlantic_gulf = 2
    # unified_region_great_lakes = 3
    # unified_region_mississippi = 4
    # unified_region_missouri = 5
    # unified_region_arkansas_rio_grande_texas_gulf = 6
    unified_region_upper_colorado = 7
    unified_region_lower_colorado = 8
    # unified_region_columbia_pacific_northwest = 9
    # unified_region_california_great_basin = 10
    # unified_region_alaska = 11
    # unified_region_pacific_islands = 12

    theme_water = 1
    # theme_water_quality = 2
    # theme_biological = 3
    # theme_environmental = 4
    # theme_infrastructure_and_assets = 5
    # theme_hydropower = 7
    # theme_safety_health_and_industrial_hygiene = 10

    catalog_path = Path('data/USBR_RISE/')
    catalog_path.mkdir(parents=True, exist_ok=True)

    upper_colorado_catalog_path = catalog_path.joinpath('Upper_Colorado_Catalog.json')
    records = usbr_rise.load_catalog(upper_colorado_catalog_path, unified_region_upper_colorado, theme_id=theme_water)
    for record in records:
        attributes = record['attributes']
        record_title = attributes['recordTitle']
        if record_title.startswith('Navajo Reservoir'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_navajo')
        elif record_title.startswith('Lake Powell') and not record_title.endswith('Evaporation Pan'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_powell')
        elif record_title.startswith('Fontenelle Reservoir'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_fontenelle')
        elif record_title.startswith('Blue Mesa'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_blue_mesa')
        elif record_title.startswith('Flaming Gorge'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_flaming_gorge')
        elif record_title.startswith('Green Mountain'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_green_mountain')
        elif record_title.startswith('Ruedi'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_ruedi')
        elif record_title.startswith('Lake Granby'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_granby')
        elif record_title.startswith('Grand Lake'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_grand_lake')
        elif record_title.startswith('Willow Creek'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_willow_creek')
        elif record_title.startswith('Shadow Mountain'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_shadow_mountain')
        elif record_title.startswith('Mcphee'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_mcphee')
        elif record_title.startswith('Taylor Park'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_taylor_park')
        # else:
        #    print(record_title)

    lower_colorado_catalog_path = catalog_path.joinpath('Lower_Colorado_Catalog.json')
    records = usbr_rise.load_catalog(lower_colorado_catalog_path, unified_region_lower_colorado, theme_id=theme_water)
    for record in records:
        attributes = record['attributes']
        record_title = attributes['recordTitle']
        if record_title.startswith('Lake Mead'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_mead')
        elif record_title.startswith('Lake Mohave'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_mohave')
        elif record_title.startswith('Lake Havasu'):
            catalog_items = usbr_rise.load_catalog_items(record, 'usbr_lake_havasu')
        else:
            print(record_title)


'''
    SW Colorado
    Lemon Reservoir and Dam Water Operations Monitoring Data from Upper Colorado Hydrologic Database
    Jackson Gulch Reservoir and Dam Water Operations Monitoring Data from Upper Colorado Hydrologic Database
    Vallecito Reservoir and Dam Water Operations Monitoring Data from Upper Colorado Hydrologic Database

    Ridgway Reservoir and Dam Water Operations Monitoring Data from Upper Colorado Hydrologic Database
    Paonia Reservoir and Dam Water Operations Monitoring Data from Upper Colorado Hydrologic Database
    Fruitgrowers Reservoir - Orchard, CO
    Silver Jack Reservoir - Gunnison, CO
    Morrow Point Reservoir Dam and Powerplant Water Operations Monitoring Data from Upper Colorado Hydrologic Database
    Crystal Reservoir Dam and Powerplant Water Operations Monitoring Data from Upper Colorado Hydrologic Database
    Taylor Park Reservoir - Uncompaghre
    Utah:
        Strawberry Reservoir - East Slope of Wasatch
        Starvation Reservoir - West of Duschesne
        Moon Lake Reservoir - North of Duschesne
        Stateline Reservoir - Wyoming Border, Smiths Fork
        Scofield Reservoir - Price River
        Rockport Reservoir - Weber River
        Lost Creek Reservoir - Weber
        Red Fleet Reservoir - Vernal
        Steinaker Reservoir - Vernal
        Trial Lake - Wasatch
        Pineview Reservoir - Ogden
        Willard Bay Reservoir - Ogden
        Upper Stillwater Reservoir - Bonneville
    Wyoming:
        Meeks Cabin Reservoir


'''
'''
    Colorado River Below Davis Dam Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River At Water Wheel Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River At Taylor Ferry Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River At River Section 41 Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River At Parker Gage Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River At Cibola Gage Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River Below Oxbow Bridge Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River Below Mcintyre Park Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River Below Interstate Bridge Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
    Colorado River Below Big Bend Water Operations Monitoring Data from the Lower Colorado Hydrologic Database
'''


def usbr_lake_powell():
    # usbr_lake_powell_release_powerplant_cfs = 507
    usbr_lake_powell_elevation_ft = 508
    usbr_lake_powell_storage_af = 509
    usbr_lake_powell_evaporation_af = 510
    # usbr_lake_powell_inflow_cfs = 511
    # usbr_lake_powell_inflow_unregulated_cfs = 512
    # usbr_lake_powell_bank_storage_af = 4276
    usbr_lake_powell_inflow_af = 4288
    usbr_lake_powell_inflow_volume_unregulated_af = 4301
    # usbr_lake_powell_release_total_cfs = 4315
    usbr_lake_powell_release_total_af = 4354
    # usbr_lake_powell_release_powerplant_af = 4356
    # usbr_lake_powell_release_spillway_cfs = 4391
    # usbr_lake_powell_release_bypass_cfs = 4392
    # usbr_lake_powell_release_bypass_af = 4393
    # usbr_lake_powell_change_in_storage_af = 4404
    # usbr_lake_powell_area_acres = 4784

    info, daily_elevation_ft = usbr_rise.load(usbr_lake_powell_elevation_ft)
    graph = WaterGraph(nrows=6)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Powell Elevation', ymin=3350, ymax=3725, yinterval=25,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_powell_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Lake Powell Storage',
               ymin=0, ymax=26000000, yinterval=1000000,
               ylabel='maf', format_func=WaterGraph.format_10maf)

    info, daily_inflow_af = usbr_rise.load(usbr_lake_powell_inflow_af)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=2, title='Lake Powell Inflow',
               ymin=3000000, ymax=21000000, yinterval=500000,
               xlabel='Water Year', xinterval=3,
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(annual_inflow_af, 10, sub_plot=2)

    info, daily_inflow_unregulated_af = usbr_rise.load(usbr_lake_powell_inflow_volume_unregulated_af)
    annual_inflow_unregulated_af = WaterGraph.daily_to_water_year(daily_inflow_unregulated_af)
    graph.bars(annual_inflow_unregulated_af, sub_plot=3, title='Lake Powell Unregulated Inflow',
               ymin=2500000, ymax=21000000, yinterval=500000,
               xlabel='Water Year', xinterval=3,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_inflow_unregulated_af, 10, sub_plot=3)
    graph.fig.waitforbuttonpress()

    info, daily_release_total_af = usbr_rise.load(usbr_lake_powell_release_total_af)
    annual_release_total_af = WaterGraph.daily_to_water_year(daily_release_total_af)
    graph.bars(annual_release_total_af, sub_plot=4, title='Lake Powell Release',
               ymin=7000000, ymax=20750000, yinterval=500000,
               xlabel='Water Year', xinterval=3,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_total_af, 10, sub_plot=4)

    info, daily_evaporation_af = usbr_rise.load(usbr_lake_powell_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=5, title='Lake Powell Evaporation', ymin=0, ymax=700000, yinterval=50000,
               xlabel='Water Year', xinterval=3,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_evaporation_af, 10, sub_plot=5)
    graph.fig.waitforbuttonpress()


# noinspection PyUnusedLocal
def usbr_green_mountain():
    usbr_green_mountain_storage_af = 21
    usbr_green_mountain_elevation_ft = 22
    usbr_green_mountain_release_total_cfs = 23


# noinspection PyUnusedLocal
def usbr_ruedi():
    usbr_ruedi_storage_af = 711
    usbr_ruedi_elevation_ft = 712
    usbr_ruedi_release_total_cfs = 716


# noinspection PyUnusedLocal
def usbr_mcphee():
    usbr_mcphee_storage_af = 569
    usbr_mcphee_inflow_cfs = 570
    usbr_mcphee_elevation_ft = 572
    usbr_mcphee_evaporation_af = 573
    usbr_mcphee_release_total_cfs = 4342
    usbr_mcphee_inflow_af = 4379
    usbr_mcphee_release_total_af = 4420
    usbr_mcphee_change_in_storage_af = 4421
    usbr_mcphee_area_acres = 4791


# noinspection PyUnusedLocal
def usbr_lake_granby():
    usbr_lake_granby_storage_af = 383
    usbr_lake_granby_elevation_ft = 384
    usbr_lake_granby_release_total_cfs = 386


# noinspection PyUnusedLocal
def usbr_grand_lake():
    usbr_lake_grand_lake_storage_af = 371
    usbr_lake_grand_lake_elevation_ft = 372


# noinspection PyUnusedLocal
def usbr_shadow_mountain():
    usbr_lake_shadow_mountain_storage_af = 737
    usbr_lake_shadow_mountain_elevation_ft = 738
    usbr_lake_shadow_mountain_release_total_cfs = 740


def usbr_navajo_reservoir():
    usbr_navajo_elevation_ft = 612
    usbr_navajo_storage_af = 613
    # usbr_navajo_inflow_unregulated_cfs = 615
    usbr_navajo_inflow_cfs = 616
    usbr_navajo_evaporation_af = 617
    # usbr_navajo_inflow_af = 4289
    usbr_navajo_release_total_cfs = 4316
    # usbr_navajo_release_total_af = 4355
    # usbr_navajo_inflow_volume_unregulated_af = 4358
    # usbr_navajo_modified_unregulated_inflow_cfs = 4369
    # usbr_navajo_modified_unregulated_inflow_volume_af = 4370
    # usbr_navajo_change_in_storage_af = 4405
    # usbr_navajo_area_acres = 4785

    info, daily_elevation_ft = usbr_rise.load(usbr_navajo_elevation_ft)
    graph = WaterGraph(nrows=5)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Navajo Elevation', ymin=5700, ymax=6100, yinterval=50,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_navajo_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Navajo Storage', ymin=0, ymax=1800000, yinterval=100000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_navajo_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=2, title='Navajo Unregulated Inflow',
               ylabel='maf', ymin=0, ymax=2000000, yinterval=100000,
               xlabel='Water Year',  xinterval=3,
               format_func=WaterGraph.format_maf)
    graph.running_average(annual_inflow_af, 10, sub_plot=2)

    info, daily_release_cfs = usbr_rise.load(usbr_navajo_release_total_cfs)
    daily_release_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=3, title='Navajo Release', ymin=0, ymax=2100000, yinterval=100000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_af, 10, sub_plot=3)

    info, daily_evaporation_af = usbr_rise.load(usbr_navajo_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=4, title='Navajo Evaporation', ymin=0, ymax=32000, yinterval=1000,
               xlabel='Water Year', xinterval=3,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_evaporation_af, 10, sub_plot=4)
    graph.fig.waitforbuttonpress()


def usbr_blue_mesa():
    usbr_blue_mesa_storage_af = 76
    usbr_blue_mesa_elevation_ft = 78
    usbr_blue_mesa_evaporation_af = 79
    usbr_blue_mesa_inflow_cfs = 4279
    # usbr_blue_mesa_inflow_af = 4283
    # usbr_blue_mesa_inflow_unregulated_cfs = 4295
    # usbr_blue_mesa_inflow_volume_unregulated_af = 4297
    # usbr_blue_mesa_release_powerplant_cfs = 4302
    usbr_blue_mesa_release_total_cfs = 4310
    # usbr_blue_mesa_release_total_af = 4349
    # usbr_blue_mesa_release_powerplant_af = 4361
    # usbr_blue_mesa_release_spillway_cfs = 4380
    # usbr_blue_mesa_release_bypass_cfs = 4381
    # usbr_blue_mesa_release_bypass_af = 4382
    # usbr_blue_mesa_change_in_storage_af = 4398
    # usbr_blue_mesa_area_acres = 4773

    info, daily_elevation_ft = usbr_rise.load(usbr_blue_mesa_elevation_ft)
    graph = WaterGraph(nrows=5)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Blue Mesa Elevation', ymin=7425, ymax=7520, yinterval=5,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_blue_mesa_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Blue Mesa Storage', ymin=200000, ymax=850000, yinterval=20000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_blue_mesa_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=2, title='Blue Mesa Inflow', ymin=0, ymax=1800000, yinterval=100000,
               xlabel='Water Year', xinterval=3,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_inflow_af, 10, sub_plot=2)

    info, daily_release_cfs = usbr_rise.load(usbr_blue_mesa_release_total_cfs)
    daily_release_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=3, title='Blue Mesa Release', ymin=0, ymax=1800000, yinterval=100000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_af, 10, sub_plot=3)

    info, daily_evaporation_af = usbr_rise.load(usbr_blue_mesa_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=4, title='Blue Mesa Evaporation', ymin=0, ymax=10000, yinterval=500,
               xlabel='Water Year',  xinterval=3,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_evaporation_af, 10, sub_plot=4)
    graph.fig.waitforbuttonpress()


def usbr_flaming_gorge():
    usbr_flaming_gorge_storage_af = 337
    # usbr_flaming_gorge_inflow_unregulated_cfs = 338
    usbr_flaming_gorge_inflow_cfs = 339
    usbr_flaming_gorge_elevation_ft = 341
    usbr_flaming_gorge_evaporation_af = 342
    # usbr_flaming_gorge_bank_storage_af = 4275
    # usbr_flaming_gorge_inflow_af = 4287
    # usbr_flaming_gorge_inflow_volume_unregulated_af = 4300
    # usbr_flaming_gorge_release_powerplant_cfs = 4306
    usbr_flaming_gorge_release_total_cfs = 4314
    # usbr_flaming_gorge_release_total_af = 4353
    # usbr_flaming_gorge_release_powerplant_af = 4360
    # usbr_flaming_gorge_release_spillway_cfs = 4371
    # usbr_flaming_gorge_release_bypass_cfs = 4390
    # usbr_flaming_gorge_change_in_storage_af = 4402
    # usbr_flaming_gorge_area_acres = 4782

    info, daily_elevation_ft = usbr_rise.load(usbr_flaming_gorge_elevation_ft)
    graph = WaterGraph(nrows=5)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Flaming Gorge Elevation', ymin=5965, ymax=6045, yinterval=10,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_flaming_gorge_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Flaming Gorge Storage', ymin=0, ymax=4000000, yinterval=100000,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_flaming_gorge_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_infow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_infow_af, sub_plot=2, title='Flaming Gorge Inflow',
               ylabel='maf', ymin=0, ymax=3300000, yinterval=100000,
               xlabel='Water Year',  xinterval=3,
               format_func=WaterGraph.format_maf)
    graph.running_average(annual_infow_af, 10, sub_plot=2)

    info, daily_release_cfs = usbr_rise.load(usbr_flaming_gorge_release_total_cfs)
    daily_release_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=3, title='Flaming Gorge Total Release',
               ylabel='maf', ymin=0, ymax=3100000, yinterval=100000,
               xlabel='Water Year', xinterval=4,
               format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_af, 10, sub_plot=3)

    info, daily_evaporation_af = usbr_rise.load(usbr_flaming_gorge_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=4, title='Flaming Gorge Evaporation',
               ylabel='kaf', ymin=0, ymax=90000, yinterval=5000,
               xlabel='Water Year', xinterval=3,
               format_func=WaterGraph.format_kaf)
    graph.running_average(annual_evaporation_af, 10, sub_plot=4)
    graph.fig.waitforbuttonpress()


def usbr_fontenelle():
    usbr_fontenelle_storage_af = 347
    usbr_fontenelle_elevation_ft = 349
    usbr_fontenelle_evaporation_af = 350
    usbr_fontenelle_inflow_cfs = 4281
    # usbr_fontenelle_inflow_af = 4286
    # usbr_fontenelle_release_powerplant_cfs = 4305
    usbr_fontenelle_release_total_cfs = 4313
    # usbr_fontenelle_release_total_af = 4352
    # usbr_fontenelle_release_powerplant_af = 4359
    # usbr_fontenelle_release_spillway_cfs = 4388
    # usbr_fontenelle_release_bypass_cfs = 4389
    # usbr_fontenelle_change_in_storage_af = 4403
    # usbr_fontenelle_area_acres = 4783

    info, daily_elevation_ft = usbr_rise.load(usbr_fontenelle_elevation_ft)
    graph = WaterGraph(nrows=5)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Fontenelle Elevation', ymin=6415, ymax=6510, yinterval=5,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_fontenelle_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Fontenelle Storage', ymin=0, ymax=380000, yinterval=20000,
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_fontenelle_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=2, title='Fontenelle Inflow', ymin=0, ymax=2400000, yinterval=100000,
               xlabel='Water Year', xinterval=3,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_inflow_af, 10, sub_plot=2)

    info, daily_release_cfs = usbr_rise.load(usbr_fontenelle_release_total_cfs)
    daily_release_total_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_total_af = WaterGraph.daily_to_water_year(daily_release_total_af)
    graph.bars(annual_release_total_af, sub_plot=3, title='Fontenelle Release', ymin=0, ymax=2400000, yinterval=100000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_total_af, 10, sub_plot=3)

    info, daily_evaporation_af = usbr_rise.load(usbr_fontenelle_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=4, title='Fontenelle Evaporation',
               ymin=0, ymax=18000, yinterval=500,
               xlabel='Water Year',  xinterval=3,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_evaporation_af, 10, sub_plot=4)
    graph.fig.waitforbuttonpress()


def usbr_lake_mead():
    usbr_lake_mead_release_total_af = 6122
    usbr_lake_mead_elevation_ft = 6123
    usbr_lake_mead_storage_af = 6124
    # usbr_lake_mead_release_total_cfs = 6125
    graph = WaterGraph(nrows=3)
    info, daily_elevation_ft = usbr_rise.load(usbr_lake_mead_elevation_ft)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mead Elevation', color='firebrick',
               ylabel='ft', ymin=900, ymax=1230, yinterval=10,
               format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_mead_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Lake Mead Storage', color='firebrick',
               ymin=0, ymax=32000000, yinterval=1000000,
               ylabel='maf', format_func=WaterGraph.format_10maf)
    # usbr_lake_mead_ics_by_state(graph)

    info, daily_release_af = usbr_rise.load(usbr_lake_mead_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=2, title='Lake Mead Release', color='firebrick',
               ymin=3000000, ymax=22500000, yinterval=500000,
               xlabel='Water Year', xinterval=5,
               ylabel='maf', format_func=WaterGraph.format_maf)
    # graph.running_average(annual_release_af, 10)
    graph.fig.waitforbuttonpress()

    # info, release = usbrrise.load(usbr_lake_mead_release_avg_cfs)


def usbr_lake_mead_ics_by_state():
    ics = usbr_lake_mead_ics()
    ics_az_total = ics['AZ Total']
    ics_ca_total = ics['CA Total']
    ics_nv_total = ics['NV Total']

    bar_data = [{'data': ics_nv_total, 'label': 'NV ICS', 'color': 'maroon'},
                {'data': ics_az_total, 'label': 'AZ ICS', 'color': 'firebrick'},
                {'data': ics_ca_total, 'label': 'CA ICS', 'color': 'lightcoral'}
                ]
    graph = WaterGraph()
    graph.bars_stacked(bar_data, title='Lower Basin ICS By State',
                       ylabel='maf', ymin=0, ymax=3000000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=1, format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def usbr_lake_mohave():
    usbr_lake_mohave_release_total_af = 6131
    # usbr_lake_mohave_water_temperature_degf = 6132
    usbr_lake_mohave_elevation_ft = 6133
    usbr_lake_mohave_storage_af = 6134
    # usbr_lake_mohave_release_total_cfs = 6135

    info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft)
    graph = WaterGraph(nrows=3)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mohave Elevation', color='firebrick',
               ymin=620, ymax=647, yinterval=2,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_mohave_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Lake Mohave Storage', color='firebrick',
               ymin=1000000, ymax=1900000, yinterval=100000,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_af = usbr_rise.load(usbr_lake_mohave_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=2, title='Lake Mohave Release', color='firebrick',
               ymin=6500000, ymax=23000000, yinterval=500000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_af, 10, sub_plot=2)
    graph.fig.waitforbuttonpress()


def usbr_lake_havasu():
    usbr_lake_havasu_release_total_af = 6126
    # usbr_lake_havasu_water_temperature_degf = 6127
    usbr_lake_havasu_elevation_ft = 6128
    usbr_lake_havasu_storage_af = 6129
    # usbr_lake_havasu_release_total_cfs = 6130

    info, daily_elevation_ft = usbr_rise.load(usbr_lake_havasu_elevation_ft)
    graph = WaterGraph(nrows=3)
    graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Havasu Elevation', color='firebrick',
               ymin=440, ymax=451, yinterval=1,
               ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_havasu_storage_af)
    graph.plot(daily_storage_af, sub_plot=1, title='Lake Havasu Storage', color='firebrick',
               ymin=0, ymax=700000, yinterval=50000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_release_af = usbr_rise.load(usbr_lake_havasu_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=2, title='Lake Havasu Release', color='firebrick',
               ymin=4000000, ymax=19200000, yinterval=500000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(annual_release_af, 10, sub_plot=2)
    graph.fig.waitforbuttonpress()


def usgs_lees_ferry():
    lees_ferry_gage = USGSGage('09380000', start_date='1921-10-01',
                               cfs_max=130000, cfs_interval=5000,
                               annual_min=6000000, annual_max=21000000, annual_interval=500000, annual_unit='maf',
                               year_interval=5)
    graph = WaterGraph()
    graph.plot_gage(lees_ferry_gage)

    # USGS Lees Ferry Gage Daily Discharge Mean
    #
    usgs_lees_ferry_annual_af = lees_ferry_gage.annual_af
    # usgs_lees_ferry_running_average = rw_running_average(usgs_lees_ferry_annual_af, 10)
    # x = usgs_lees_ferry_running_average['dt']
    # y = usgs_lees_ferry_running_average['val']
    # plot_bars.plot(x, y, linestyle='-', linewidth=3, marker='None', color='goldenrod', label='10Y Running Average')
    # plot_bars.legend()
    # plot_bars.show()
    # plot_bars.waitforbuttonpress()

    usgs_lees_ferry_af_1999_2021 = WaterGraph.array_in_time_range(usgs_lees_ferry_annual_af,
                                                                  datetime.datetime(1999, 1, 1),
                                                                  datetime.datetime(2021, 12, 31))
    # rw_bars(annual_discharge_af, title=name, color='royalblue',
    #        ylabel='maf', ymin=2000000, ymax=21000000, yinterval=500000, format_func=format_maf,
    #        xlabel='Water Year', xinterval=5)

    # USBR Lake Powell Annual Water Year Releases from RISE
    #
    usbr_lake_powell_release_total_af = 4354
    info, daily_usbr_glen_canyon_daily_release_af = usbr_rise.load(usbr_lake_powell_release_total_af)
    usbr_glen_canyon_annual_release_af = WaterGraph.daily_to_water_year(daily_usbr_glen_canyon_daily_release_af)
    # rw_bars(a, title='Lake Powell Release',
    #        ylabel='maf', ymin=7000000, ymax=20750000, yinterval=500000,
    #        xlabel='Water Year', xinterval=3, format_func=format_maf)
    graph = WaterGraph()
    graph.bars_two(usbr_glen_canyon_annual_release_af, usgs_lees_ferry_annual_af,
                   title='Lake Powell Release Comparison, USBR Glen Canyon vs USGS Lees Ferry',
                   label_a='Glen Canyon', color_a='royalblue',
                   label_b='Lees Ferry', color_b='limegreen',
                   ylabel='af', ymin=7000000, ymax=14000000, yinterval=250000,
                   xlabel='Water Year', xinterval=3, format_func=WaterGraph.format_maf)

    usbr_lake_powell_release_af_1999_2021 = WaterGraph.array_in_time_range(usbr_glen_canyon_annual_release_af,
                                                                           datetime.datetime(1999, 1, 1),
                                                                           datetime.datetime(2021, 12, 31))

    # USGS Paria At Lees Ferry Gage Daily Discharge Mean
    #
    usgs_paria_annual_af = usgs_paria_lees_ferry()
    usgs_paria_annual_af_1999_2021 = WaterGraph.array_in_time_range(usgs_paria_annual_af,
                                                                    datetime.datetime(1999, 1, 1),
                                                                    datetime.datetime(2021, 12, 31))

    usbr_glen_canyon_vector = usbr_lake_powell_release_af_1999_2021['val']
    usgs_paria_vector = usgs_paria_annual_af_1999_2021['val']
    usgs_glen_canyon_plus_paria = usbr_glen_canyon_vector + usgs_paria_vector

    glen_canyon_plus_paria = np.empty(2021-1999+1, [('dt', 'i'), ('val', 'f')])
    glen_canyon_plus_paria['dt'] = usbr_lake_powell_release_af_1999_2021['dt']
    glen_canyon_plus_paria['val'] = usgs_glen_canyon_plus_paria

    usgs_lees_ferry_vector = usgs_lees_ferry_af_1999_2021['val']

    print('USBR Glen Canyon:\n', usbr_glen_canyon_vector)
    print('USGS Lees Ferry:\n', usgs_lees_ferry_vector)
    difference = usgs_lees_ferry_vector - usgs_glen_canyon_plus_paria
    difference_sum = difference.sum()
    difference_average = difference_sum / len(difference)
    print('Total discrepancy 1999-2021   = ', int(difference_sum))
    print('Average discrepancy 1999-2021 = ', int(difference_average))
    print('Difference vector:\n', difference)

    discrepancy = np.empty(len(usgs_lees_ferry_af_1999_2021['dt']), [('dt', 'i'), ('val', 'f')])
    discrepancy['dt'] = usgs_lees_ferry_af_1999_2021['dt']
    discrepancy['val'] = difference

    graph = WaterGraph()
    graph.bars_two(glen_canyon_plus_paria, usgs_lees_ferry_af_1999_2021,
                   title='Lake Powell Release Comparison, USBR Glen Canyon + Paria vs USGS Lees Ferry',
                   label_a='Glen Canyon + Paria', color_a='royalblue',
                   label_b='Lees Ferry', color_b='limegreen',
                   ylabel='maf', ymin=7000000, ymax=14000000, yinterval=250000,
                   xlabel='Water Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()

    graph = WaterGraph()
    graph.bars(discrepancy,
               title='Lake Powell Release Difference USBR Glen Canyon + paria vs USGS Lees Ferry',
               ylabel='kaf', ymin=0, ymax=300000, yinterval=50000,
               xlabel='Water Year', xinterval=2, format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usgs_paria_lees_ferry():
    paria_lees_ferry_gage = USGSGage('09382000', start_date='1932-10-01',
                                     cfs_max=6500, cfs_interval=500,
                                     annual_min=0, annual_max=50000, annual_interval=2500, annual_unit='kaf',
                                     year_interval=5)
    graph = WaterGraph()
    graph.plot_gage(paria_lees_ferry_gage)
    return paria_lees_ferry_gage.annual_af


def usgs_little_colorado_cameron():
    gage = USGSGage('09402000', start_date='1947-06-1', color='firebrick',
                    cfs_max=19000, cfs_interval=1000,
                    annual_min=0, annual_max=850000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_virgin_at_littlefield():
    gage = USGSGage('09415000', start_date='1929-10-01', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_min=0, annual_max=600000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_muddy_near_glendale():
    gage = USGSGage('09419000', start_date='1950-02-01', color='firebrick',
                    cfs_max=5500, cfs_interval=500,
                    annual_min=0, annual_max=54000, annual_interval=2000, annual_unit='kaf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_gila_duncan():
    gage = USGSGage('09439000', start_date='2003-09-30', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_min=0, annual_max=350000, annual_interval=25000, annual_unit='kaf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_gila_goodyear():
    gage = USGSGage('09514100', start_date='1992-10-01', color='firebrick',
                    cfs_max=140000, cfs_interval=10000,
                    annual_min=0, annual_max=1000000, annual_interval=50000, annual_unit='maf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_gila_dome():
    gage = USGSGage('09520500', start_date='1905-01-01', color='firebrick',
                    cfs_max=96000, cfs_interval=10000,
                    annual_min=0, annual_max=4500000, annual_interval=500000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)

    gage = USGSGage('09520500', start_date='1996-01-01', color='firebrick',
                    cfs_max=1000, cfs_interval=100,
                    annual_min=0, annual_max=200000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_bill_williams_parker():
    gage = USGSGage('09426620', start_date='1988-10-01', color='firebrick',
                    cfs_max=8000, cfs_interval=500,
                    annual_min=0, annual_max=450000, annual_interval=50000, annual_unit='maf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_salt_above_roosevelt():
    gage = USGSGage('09498500', start_date='1913-10-01', color='firebrick',
                    cfs_max=95000, cfs_interval=5000,
                    annual_min=0, annual_max=2400000, annual_interval=100000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_colorado_below_parker():
    gage = USGSGage('09427520', start_date='1934-11-16', color='firebrick',
                    cfs_max=41000, cfs_interval=1000,
                    annual_min=4000000, annual_max=22000000, annual_interval=1000000, annual_unit='maf',
                    year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_las_vegas_wash_below_lake_las_vegas():
    gage = USGSGage('09419800', start_date='1969-08-01', color='firebrick',
                    cfs_max=2000, cfs_interval=100,
                    annual_min=0, annual_max=300000, annual_interval=10000, annual_unit='kaf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_colorado_below_palo_verde():
    gage = USGSGage('09429100', start_date='1956-03-24', color='firebrick',
                    cfs_max=17000, cfs_interval=1000,
                    annual_min=0, annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_colorado_nothern_international_border():
    gage = USGSGage('09522000', start_date='1950-01-01', color='firebrick',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=4000000, annual_interval=200000, annual_unit='maf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_colorado_below_imperial():
    # Bogus gage
    gage = USGSGage('09429500', start_date='2018-11-29', color='firebrick',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=500000, annual_interval=20000, annual_unit='kaf', year_interval=1)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_colorado_below_davis():
    gage = USGSGage('09423000', start_date='1905-05-11', color='firebrick',
                    cfs_max=120000, cfs_interval=5000,
                    annual_min=6000000, annual_max=23000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_colorado_below_laguna():
    gage = USGSGage('09429600', start_date='1971-12-16', color='firebrick',
                    cfs_max=32000, cfs_interval=2000,
                    annual_min=0, annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_imperial_all_american():
    # All American Colorado River
    gage = USGSGage('09523000', start_date='1939-10-01', color='firebrick',
                    cfs_max=15000, cfs_interval=1000,
                    annual_min=3000000, annual_max=8700000, annual_interval=200000, annual_unit='maf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)

    # Coachella
    gage = USGSGage('09527590', start_date='2003-10-01', color='firebrick',
                    cfs_max=850, cfs_interval=50,
                    annual_min=0, annual_max=400000, annual_interval=20000, annual_unit='kaf', year_interval=3)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)

    # All American Drop 2, probably IID
    gage = USGSGage('09527700', start_date='2011-10-26', color='firebrick',
                    cfs_max=6500, cfs_interval=500,
                    annual_min=0, annual_max=2600000, annual_interval=100000, annual_unit='maf', year_interval=3)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_imperial_all_american_drop_2():
    gage = USGSGage('09527700', start_date='2011-10-26', color='firebrick',
                    cfs_max=6500, cfs_interval=500,
                    annual_min=0, annual_max=2600000, annual_interval=100000, annual_unit='maf', year_interval=3)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_coachella_all_american():
    gage = USGSGage('09527590', start_date='2003-10-01', color='firebrick',
                    cfs_max=850, cfs_interval=50,
                    annual_min=0, annual_max=400000, annual_interval=20000, annual_unit='kaf', year_interval=3)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_gila_gravity_main_canal():
    gage = USGSGage('09522500', start_date='1943-08-16', color='firebrick',
                    cfs_max=2300, cfs_interval=100,
                    annual_min=0, annual_max=1000000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_north_gila_main_canal():
    gage = USGSGage('09522600', start_date='1966-10-01', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_reservation_main_canal():
    gage = USGSGage('09523200', start_date='1974-10-01', color='firebrick',
                    cfs_max=270, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_yuma_main_canal():
    gage = USGSGage('09524000', start_date='1938-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_colorado_below_yuma_main_canal():
    gage = USGSGage('09521100', start_date='1963-10-01', color='firebrick',
                    cfs_max=10000, cfs_interval=1000,
                    annual_min=0, annual_max=3000000, annual_interval=100000, annual_unit='maf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_yuma_main_canal_wasteway():
    gage = USGSGage('09525000', start_date='1930-10-01', color='firebrick',
                    cfs_max=2200, cfs_interval=200,
                    annual_min=0, annual_max=1100000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_unit_b_canal_near_yuma():
    gage = USGSGage('09522900', start_date='2005-09-30', color='firebrick',
                    cfs_max=120, cfs_interval=10,
                    annual_min=0, annual_max=30000, annual_interval=1000, annual_unit='kaf', year_interval=1)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_wellton_mohawk_main_canal():
    gage = USGSGage('09522700', start_date='1974-10-01', color='firebrick',
                    cfs_max=1900, cfs_interval=200,
                    annual_min=0, annual_max=500000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_wellton_mohawk_main_outlet_drain():
    gage = USGSGage('09529300', start_date='1966-10-01', color='firebrick',
                    cfs_max=350, cfs_interval=50,
                    annual_min=0, annual_max=230000, annual_interval=20000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)


def usgs_palo_verde_canal():
    gage = USGSGage('09429000', start_date='1950-10-01', color='firebrick',
                    cfs_max=2400, cfs_interval=100,
                    annual_min=650000, annual_max=1050000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_crir_canal_near_parker():
    gage = USGSGage('09428500', start_date='1954-10-01', color='firebrick',
                    cfs_max=2000, cfs_interval=100,
                    annual_min=250000, annual_max=750000, annual_interval=50000, annual_unit='kaf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_san_juan_bluff():
    gage = USGSGage('09379500', start_date='1941-10-01',
                    cfs_max=43000, cfs_interval=2000,
                    annual_min=400000, annual_max=3300000, annual_interval=100000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_green_river():
    gage = USGSGage('09315000', start_date='1894-10-01',
                    cfs_max=70000, cfs_interval=10000,
                    annual_min=1000000, annual_max=9000000, annual_interval=200000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_gunnison_grand_junction():
    gage = USGSGage('09152500', start_date='1896-10-01',
                    cfs_max=36000, cfs_interval=1000,
                    annual_max=3800000, annual_interval=100000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_colorado_cisco():
    gage = USGSGage('09180500', start_date='1913-10-01',
                    cfs_max=75000, cfs_interval=2500,
                    annual_max=11000000, annual_interval=250000, annual_unit='maf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_colorado_potash():
    gage = USGSGage('09185600', start_date='2014-10-29',
                    cfs_max=75000, cfs_interval=2500,
                    annual_max=11000000, annual_interval=250000, annual_unit='maf', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_dirty_devil():
    gage = USGSGage('09333500', start_date='1948-06-07',
                    cfs_max=28000, cfs_interval=1000,
                    annual_max=190000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_dolores_below_rico():
    gage = USGSGage('09165000', start_date='1951-10-01',
                    cfs_max=1900, cfs_interval=100,
                    annual_max=170000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_dolores_at_dolores():
    gage = USGSGage('09166500', start_date='1895-10-01',
                    cfs_max=7000, cfs_interval=500,
                    annual_max=575000, annual_interval=25000, annual_unit='kaf', year_interval=6)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_dolores_at_cisco():
    gage = USGSGage('09180000', start_date='1950-12-01',
                    cfs_max=17000, cfs_interval=1000,
                    annual_max=1500000, annual_interval=50000, annual_unit='kaf')
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_mud_creek_cortez():
    gage = USGSGage('09371492', start_date='1981-10-01',
                    cfs_max=240, cfs_interval=10,
                    annual_max=7500, annual_interval=500, annual_unit='af', year_interval=3)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_mcelmo_stateline():
    gage = USGSGage('09372000', start_date='1951-03-01',
                    cfs_max=1300, cfs_interval=50,
                    annual_max=70000, annual_interval=5000, annual_unit='af', year_interval=4)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_mcelmo_trail_canyon():
    gage = USGSGage('09371520', start_date='1993-08-01',
                    cfs_max=1250, cfs_interval=50,
                    annual_max=60000, annual_interval=5000, annual_unit='af', year_interval=3)
    graph = WaterGraph(nrows=2)
    graph.plot_gage(gage)
    return gage


def usgs_upper_colorado():
    usgs_gunnison_grand_junction()
    usgs_dirty_devil()
    usgs_green_river()
    usgs_colorado_cisco()
    usgs_san_juan_bluff()

    # usgs_mud_creek_cortez()
    # usgs_mcelmo_trail_canyon()
    # usgs_mcelmo_stateline()
    # usgs_dolores_below_rico()
    # usgs_dolores_at_dolores()
    usgs_dolores_at_cisco()


def usbr_upper_colorado_reservoirs():
    usbr_fontenelle()
    usbr_flaming_gorge()
    usbr_blue_mesa()
    usbr_navajo_reservoir()
    usbr_lake_powell()


def usbr_lower_colorado_reservoirs():
    usbr_lake_mead()
    usbr_lake_mohave()
    usbr_lake_havasu()


def usgs_lower_colorado_to_border_gages():
    usgs_unit_b_canal_near_yuma()

    usgs_gila_gravity_main_canal()
    usgs_imperial_all_american()
    usgs_colorado_below_imperial()
    usgs_north_gila_main_canal()
    usgs_reservation_main_canal()
    usgs_colorado_below_laguna()

    usgs_wellton_mohawk_main_canal()
    usgs_wellton_mohawk_main_outlet_drain()

    usgs_yuma_main_canal()
    usgs_yuma_main_canal_wasteway()

    usgs_colorado_below_yuma_main_canal()
    usgs_colorado_nothern_international_border()


def usgs_lower_colorado():
    usgs_lees_ferry()
    # usgs_paria_lees_ferry()
    usgs_las_vegas_wash_below_lake_las_vegas()
    usgs_colorado_below_davis()
    usgs_colorado_below_parker()
    usgs_crir_canal_near_parker()
    usgs_palo_verde_canal()
    usgs_colorado_below_palo_verde()
    usgs_lower_colorado_to_border_gages()


def usgs_lower_colorado_tributaries():
    # usgs_gila_duncan()
    usgs_gila_dome()
    usgs_gila_goodyear()
    usgs_muddy_near_glendale()
    usgs_virgin_at_littlefield()
    usgs_little_colorado_cameron()
    usgs_bill_williams_parker()
    usgs_salt_above_roosevelt()


def usgs_all_american_canal():
    # Imperial, Yuma, Coachella, Infer Alamo/Mexico (all american below imperial dam - coachella - drop_2)
    usgs_imperial_all_american()
    usgs_imperial_all_american_drop_2()
    usgs_coachella_all_american()


def usgs_colorado_river_gages():
    usgs_upper_colorado()
    usgs_lower_colorado()

    usgs_lower_colorado_tributaries()


def usbr_lake_havasu_cap_wilmer_pumping_plant():
    year_interval = 3

    headers, monthly_af = usbr_report.load_monthly_csv('usbr_lake_havasu_cap_wilmer_pumps.csv')
    graph = WaterGraph(nrows=3)
    graph.plot(monthly_af, sub_plot=0, title='Lake Havasu CAP Wilmer Pumping Plant (Monthly)',
               xinterval=year_interval, ymin=0, ymax=200000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Lake Havasu CAP Wilmer Pumping Plant (Annual)',
               xinterval=year_interval, ymin=0, ymax=1800000, yinterval=100000,
               xlabel='Calendar Year',   color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=1)

    ics = usbr_lake_mead_ics()
    ics_az_delta = ics['AZ Delta']
    ics_az_delta = graph.reshape_annual_range(ics_az_delta, 1985, 2021)

    bar_data = [{'data': annual_af, 'label': 'Metropolitan', 'color': 'firebrick'},
                {'data': ics_az_delta, 'label': 'AZ ICS Deposits', 'color': 'mediumseagreen'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Lake Havasu CAP Wilmer Pumping Plant + AZ ICS Deposits',
                       ylabel='maf', ymin=0, ymax=1800000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def usbr_palo_verde():
    year_interval = 3

    # Diversion
    headers, monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_palo_verde_diversion.csv')
    graph = WaterGraph(nrows=4)
    graph.plot(monthly_af, sub_plot=0, title='Palo Verde Diversion (Monthly)',
               xinterval=year_interval, ymin=0, ymax=130000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Palo Verde Diversion (Annual)',
               ymin=0, ymax=1200000, yinterval=100000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=1)

    # Consumptive Use
    headers, monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_palo_verde_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=2, title='Palo Verde Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=-15000, ymax=90000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Palo Verde Consumptive Use (Annual)',
               ymin=0, ymax=550000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_af, 10, sub_plot=3)

    graph.fig.waitforbuttonpress()


def usbr_crit():
    year_interval = 3

    # Diversion
    headers, monthly_af = usbr_report.load_monthly_csv('az/usbr_az_crit_diversion.csv')
    graph = WaterGraph(nrows=4)
    graph.plot(monthly_af, sub_plot=0, title='Colorado River Indian Tribe Diversion (Monthly)',
               xinterval=year_interval, ymin=0, ymax=130000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Colorado River Indian Tribe Diversion (Annual)',
               ymin=0, ymax=1200000, yinterval=100000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=1)

    # Consumptive Use
    headers, monthly_af = usbr_report.load_monthly_csv('az/usbr_az_crit_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=2, title='Colorado River Indian Tribe Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=-15000, ymax=90000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Colorado River Indian Tribe Consumptive Use (Annual)',
               ymin=0, ymax=550000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_af, 10, sub_plot=3)

    graph.fig.waitforbuttonpress()


def usbr_california_total():
    year_interval = 3

    # Diversion
    headers, monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_diversion.csv')
    graph = WaterGraph(nrows=3)
    graph.plot(monthly_af, sub_plot=0, title='California Total Diversion (Monthly)',
               xinterval=year_interval, ymin=100000, ymax=700000, yinterval=100000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='California Total Diversion (Annual)',
               ymin=3600000, ymax=6000000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='darkmagenta',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=1)

    # Consumptive Use
    headers, monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=0, title='California Total Diversion & Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=100000, ymax=700000, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=2, title='California Total Consumptive Use (Annual)',
               ymin=3600000, ymax=6000000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=2)

    graph.fig.waitforbuttonpress()


def usbr_arizona_total():
    year_interval = 3

    # Diversion
    headers, monthly_af = usbr_report.load_monthly_csv('az/usbr_az_total_diversion.csv')
    graph = WaterGraph(nrows=3)
    graph.plot(monthly_af, sub_plot=0, title='Arizona Total Diversion (Monthly)',
               xinterval=year_interval, ymin=0, ymax=450000, yinterval=100000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Arizona Total Diversion (Annual)',
               ymin=0, ymax=3800000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='darkmagenta',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=1)

    # Consumptive Use
    headers, monthly_af = usbr_report.load_monthly_csv('az/usbr_az_total_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=0, title='Arizona Total Diversion & Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=0, ymax=450000, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=2, title='Arizona Total Consumptive Use (Annual)',
               ymin=0, ymax=3800000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=2)

    graph.fig.waitforbuttonpress()


def usbr_imperial_irrigation_district():
    year_interval = 3

    # Diversion
    headers, monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_diversion.csv')
    graph = WaterGraph(nrows=2)
    graph.plot(monthly_af, sub_plot=0, title='Imperial Irrigation District Diversion (Monthly)',
               xinterval=year_interval, ymin=0, ymax=400000, yinterval=20000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Imperial Irrigation District Diversion (Annual)',
               ymin=2200000, ymax=3300000, yinterval=100000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_af, 10, sub_plot=1)

    # Consumptive Use
    # headers, monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_consumptive_use.csv')
    # graph.plot(monthly_af, sub_plot=2, title='Imperial Irrigtion District Consumptive Use',
    #            xinterval=year_interval, ymin=0, ymax=400000, yinterval=20000, color='firebrick',
    #            ylabel='maf', format_func=WaterGraph.format_maf)

    # annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    # graph.bars(annual_af, sub_plot=3, title='Imperial Irrigtion Consumptive Use',
    #            ymin=2200000, ymax=3400000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #            ylabel='maf', format_func=WaterGraph.format_maf)
    # graph.running_average(annual_af, 10, sub_plot=3)

    graph.fig.waitforbuttonpress()


def usbr_lake_mead_snwa_griffith_pumping_plant():
    year_interval = 2
    headers, monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_snwa_griffith_diversion.csv')
    graph = WaterGraph(nrows=4)
    graph.plot(monthly_af, sub_plot=0, title='Lake Mead SNWA Griffith Pumping Plant Diversion (Monthly)',
               xinterval=year_interval, ymin=0, ymax=55000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Lake Mead SNWA Griffith Pumping Plant Diversion (Annual)',
               ymin=0, ymax=500000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_af, 10, sub_plot=1)

    headers, monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_las_vegas_wash_diversion.csv')
    graph.plot(monthly_af, sub_plot=2, title='Lake Mead Las Vegas Wash Return Flows (Monthly)',
               xinterval=year_interval, ymin=0, ymax=25000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Lake Mead Las Vegas Wash Return Flows (Annual)',
               ymin=0, ymax=250000, yinterval=50000,
               xlabel='Calendar Year',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_af, 10, sub_plot=3)

    graph.fig.waitforbuttonpress()


def usbr_lake_havasu_metropolitan_whitsett_pumping_plant():
    headers, whitsett_monthly_af = usbr_report.load_monthly_csv('usbr_lake_havasu_metropolitan_whitsett_pumps.csv')
    # graph = WaterGraph.plot(whitsett_monthly_af,
    #                               'Lake Havasu Metropolitan Whitsett Pumping Plant (Monthly)',
    #                               ylabel='kaf', ymin=0, ymax=120000, yinterval=10000, color='firebrick',
    #                               format_func=WaterGraph.format_kaf)
    # graph.fig.waitforbuttonpress()

    whitsett_annual_af = usbr_report.monthly_to_water_year(whitsett_monthly_af, water_year_month=1)
    graph = WaterGraph(nrows=3)
    graph.bars(whitsett_annual_af, sub_plot=0,
               title='Lake Havasu Metropolitan Whitsett Pumping Plant Diversion (Annual)',
               ymin=0, ymax=1350000, yinterval=100000,
               xlabel='Calendar Year',  xinterval=3, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(whitsett_annual_af, 10, sub_plot=0)

    headers, whitsett_san_diego_monthly_af = usbr_report.load_monthly_csv(
        'usbr_lake_havasu_met_for_san_diego_whitsett_pumps.csv')
    graph.plot(whitsett_san_diego_monthly_af, sub_plot=1,
               title='Lake Havasu Metropolitan San Diego Exchange Whitsett Pumping Plant Diversion (Monthly)',
               ymin=0, ymax=25000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    whitsett_san_diego_annual_af = usbr_report.monthly_to_calendar_year(whitsett_san_diego_monthly_af)
    bar_data = [{'data': whitsett_annual_af, 'label': 'Metropolitan', 'color': 'firebrick'},
                {'data': whitsett_san_diego_annual_af, 'label': 'San Diego Exchange', 'color': 'goldenrod'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Lake Havasu Metropolitan + San Diego Exchange (Annual)',
                       ymin=400000, ymax=1400000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=3,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)

    ics = usbr_lake_mead_ics()
    ics_ca_delta = ics['CA Delta']

    ics_ca_withdrawals = usbr_report.negative_values(ics_ca_delta)
    ics_ca_withdrawals = graph.reshape_annual_range(ics_ca_withdrawals, 1964, 2021)

    ics_ca_deposits = usbr_report.positive_values(ics_ca_delta)
    ics_ca_deposits = graph.reshape_annual_range(ics_ca_deposits, 1964, 2021)

    bar_data = [{'data': whitsett_annual_af, 'label': 'Metropolitan Diversion', 'color': 'firebrick'},
                {'data': whitsett_san_diego_annual_af, 'label': 'San Diego Exchange', 'color': 'goldenrod'},
                {'data': ics_ca_withdrawals, 'label': 'CA ICS Withdrawals', 'color': 'lightcoral'},
                {'data': ics_ca_deposits, 'label': 'CA ICS Deposits', 'color': 'mediumseagreen'}
                ]
    graph = WaterGraph()
    graph.bars_stacked(bar_data, sub_plot=3,
                       title='Lake Havasu Metropolitan Diversion + San Diego Exchange, CA ICS (Annual)',
                       ylabel='kaf', ymin=400000, ymax=1400000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=3, format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usbr_lake_mead_ics():
    results = usbr_report.load_ics_csv('usbr_lake_mead_ics.csv', sep='\t')
    return results


# noinspection PyUnusedLocal
def keyboardInterruptHandler(sig, frame):
    global interrupted
    interrupted = True

    try:
        print("exit")
        sys.exit(0)
    except OSError as e:
        print("riverwar exit exception:", e)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, keyboardInterruptHandler)

    # usbr_catalog()
    usbr_arizona_total()
    usbr_california_total()
    usbr_crit()
    usbr_palo_verde()
    usbr_imperial_irrigation_district()
    usbr_lake_mead_snwa_griffith_pumping_plant()
    usbr_lake_havasu_metropolitan_whitsett_pumping_plant()
    usbr_lake_mead()
    usbr_lake_mead_ics_by_state()
    usbr_lake_havasu_cap_wilmer_pumping_plant()

    usbr_upper_colorado_reservoirs()
    usbr_lower_colorado_reservoirs()

    usgs_las_vegas_wash_below_lake_las_vegas()

    usgs_lower_colorado()
    usbr_upper_colorado_reservoirs()
    usbr_lower_colorado_reservoirs()
    usgs_colorado_river_gages()
