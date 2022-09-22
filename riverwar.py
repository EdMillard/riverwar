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

current_last_year = 2021

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
    # usbr_lake_powell_elevation_ft = 508
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

    year_interval = 3
    graph = WaterGraph(nrows=4)

    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_powell_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Powell Elevation', ymin=3350, ymax=3725, yinterval=25,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_powell_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Powell Storage',
               ymax=26000000, yinterval=2000000,
               ylabel='maf', format_func=WaterGraph.format_10maf)

    annual_inflow_af = usbr_rise.annual_af(usbr_lake_powell_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=1, title='Lake Powell Inflow',
               ymin=3000000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
               ylabel='maf',  format_func=WaterGraph.format_maf)

    annual_inflow_unregulated_af = usbr_rise.annual_af(usbr_lake_powell_inflow_volume_unregulated_af)
    graph.bars(annual_inflow_unregulated_af, sub_plot=2, title='Lake Powell Unregulated Inflow',
               ymin=2500000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    annual_evaporation_af = usbr_rise.annual_af(usbr_lake_powell_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=3, title='Lake Powell Evaporation',
               ymin=0, ymax=700000, yinterval=50000,
               xlabel='Water Year', xinterval=year_interval,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()

    graph = WaterGraph(nrows=1)

    annual_release_total_af = usbr_rise.annual_af(usbr_lake_powell_release_total_af)
    graph.bars(annual_release_total_af, sub_plot=0, title='Lake Powell Release',
               ymin=7000000, ymax=12600000, yinterval=100000,
               xlabel='Water Year', xinterval=1, xmin=2000, xmax=2021,
               ylabel='maf', format_func=WaterGraph.format_maf)
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
    # usbr_navajo_elevation_ft = 612
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

    graph = WaterGraph(nrows=4)
    year_interval = 3

    # info, daily_elevation_ft = usbr_rise.load(usbr_navajo_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Navajo Elevation', ymin=5700, ymax=6100, yinterval=50,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_navajo_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Navajo Storage',
               ymax=1800000, yinterval=200000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_navajo_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=1, title='Navajo Unregulated Inflow',
               ymin=0, ymax=2000000, yinterval=200000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_cfs = usbr_rise.load(usbr_navajo_release_total_cfs)
    daily_release_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=2, title='Navajo Release',
               ymin=0, ymax=2100000, yinterval=200000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_evaporation_af = usbr_rise.load(usbr_navajo_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=3, title='Navajo Evaporation',
               ymin=0, ymax=32000, yinterval=2000, xlabel='Water Year', xinterval=year_interval,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usbr_blue_mesa():
    usbr_blue_mesa_storage_af = 76
    # usbr_blue_mesa_elevation_ft = 78
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

    graph = WaterGraph(nrows=4)
    year_interval = 3

    # info, daily_elevation_ft = usbr_rise.load(usbr_blue_mesa_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Blue Mesa Elevation', ymin=7425, ymax=7520, yinterval=5,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_blue_mesa_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Blue Mesa Storage',
               ymin=200000, ymax=850000, yinterval=50000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_blue_mesa_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=1, title='Blue Mesa Inflow',
               ymin=0, ymax=1800000, yinterval=200000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_cfs = usbr_rise.load(usbr_blue_mesa_release_total_cfs)
    daily_release_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=2, title='Blue Mesa Release',
               ymin=0, ymax=1800000, yinterval=200000, xinterval=3,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_evaporation_af = usbr_rise.load(usbr_blue_mesa_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=3, title='Blue Mesa Evaporation',
               ymin=0, ymax=10000, yinterval=1000,
               xlabel='Water Year',  xinterval=year_interval,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usbr_flaming_gorge():
    usbr_flaming_gorge_storage_af = 337
    # usbr_flaming_gorge_inflow_unregulated_cfs = 338
    usbr_flaming_gorge_inflow_cfs = 339
    # usbr_flaming_gorge_elevation_ft = 341
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

    graph = WaterGraph(nrows=4)
    year_interval = 3

    # info, daily_elevation_ft = usbr_rise.load(usbr_flaming_gorge_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Flaming Gorge Elevation', ymin=5965, ymax=6045, yinterval=10,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_flaming_gorge_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Flaming Gorge Storage',
               ymax=4000000, yinterval=400000,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_flaming_gorge_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_infow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_infow_af, sub_plot=1, title='Flaming Gorge Inflow',
               ymin=0, ymax=3300000, yinterval=200000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_cfs = usbr_rise.load(usbr_flaming_gorge_release_total_cfs)
    daily_release_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=2, title='Flaming Gorge Total Release',
               ylabel='maf', ymin=0, ymax=3100000, yinterval=200000, xinterval=year_interval,
               format_func=WaterGraph.format_maf)

    info, daily_evaporation_af = usbr_rise.load(usbr_flaming_gorge_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=3, title='Flaming Gorge Evaporation',
               ymin=0, ymax=90000, yinterval=10000, xinterval=year_interval,
               xlabel='Water Year',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usbr_fontenelle():
    usbr_fontenelle_storage_af = 347
    # usbr_fontenelle_elevation_ft = 349
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

    graph = WaterGraph(nrows=4)
    year_interval = 3

    # info, daily_elevation_ft = usbr_rise.load(usbr_fontenelle_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Fontenelle Elevation', ymin=6415, ymax=6510, yinterval=5,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_fontenelle_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Fontenelle Storage', ymax=380000, yinterval=50000,
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    info, daily_inflow_cfs = usbr_rise.load(usbr_fontenelle_inflow_cfs)
    daily_inflow_af = WaterGraph.convert_cfs_to_af_per_day(daily_inflow_cfs)
    annual_inflow_af = WaterGraph.daily_to_water_year(daily_inflow_af)
    graph.bars(annual_inflow_af, sub_plot=1, title='Fontenelle Inflow',
               ymin=0, ymax=2400000, yinterval=200000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_cfs = usbr_rise.load(usbr_fontenelle_release_total_cfs)
    daily_release_total_af = WaterGraph.convert_cfs_to_af_per_day(daily_release_cfs)
    annual_release_total_af = WaterGraph.daily_to_water_year(daily_release_total_af)
    graph.bars(annual_release_total_af, sub_plot=2, title='Fontenelle Release',
               ymin=0, ymax=2400000, yinterval=200000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_evaporation_af = usbr_rise.load(usbr_fontenelle_evaporation_af)
    annual_evaporation_af = WaterGraph.daily_to_water_year(daily_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=3, title='Fontenelle Evaporation',
               ymin=0, ymax=18000, yinterval=2000,  xinterval=year_interval,
               xlabel='Water Year',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usbr_lake_mead():
    usbr_lake_mead_release_total_af = 6122
    # usbr_lake_mead_elevation_ft = 6123
    usbr_lake_mead_storage_af = 6124
    # usbr_lake_mead_release_total_cfs = 6125
    graph = WaterGraph(nrows=2)
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_mead_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mead Elevation', color='firebrick',
    #            ylabel='ft', ymin=900, ymax=1230, yinterval=20,
    #            format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_mead_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Mead Storage (Hoover Dam)', color='firebrick',
               ymax=32000000, yinterval=2000000,
               ylabel='maf', format_func=WaterGraph.format_10maf)
    # usbr_lake_mead_ics_by_state(graph)

    info, daily_release_af = usbr_rise.load(usbr_lake_mead_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=1, title='Lake Mead Release (Hoover Dam)', color='firebrick',
               ymin=3000000, ymax=22500000, yinterval=1000000,
               xlabel='Water Year', xinterval=5,
               ylabel='maf', format_func=WaterGraph.format_maf)
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
    # usbr_lake_mohave_elevation_ft = 6133
    usbr_lake_mohave_storage_af = 6134
    # usbr_lake_mohave_release_total_cfs = 6135

    graph = WaterGraph(nrows=2)
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mohave Elevation', color='firebrick',
    #            ymin=620, ymax=647, yinterval=2,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)
    info, daily_storage_af = usbr_rise.load(usbr_lake_mohave_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Mohave Storage (Davis Dam)', color='firebrick',
               ymin=1000000, ymax=1900000, yinterval=100000,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_af = usbr_rise.load(usbr_lake_mohave_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=1, title='Lake Mohave Release (Davis Dam)', color='firebrick',
               ymin=6500000, ymax=23000000, yinterval=1000000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def usbr_lake_havasu():
    usbr_lake_havasu_release_total_af = 6126
    # usbr_lake_havasu_water_temperature_degf = 6127
    # usbr_lake_havasu_elevation_ft = 6128
    usbr_lake_havasu_storage_af = 6129
    # usbr_lake_havasu_release_total_cfs = 6130

    graph = WaterGraph(nrows=2)
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_havasu_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Havasu Elevation', color='firebrick',
    #            ymin=440, ymax=451, yinterval=1,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_havasu_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Havasu Storage (Parker Dam)', color='firebrick',
               ymax=700000, yinterval=50000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_release_af = usbr_rise.load(usbr_lake_havasu_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=1, title='Lake Havasu Release (Parker Dam)', color='firebrick',
               ymin=4000000, ymax=19200000, yinterval=1000000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf',  format_func=WaterGraph.format_maf)
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
    usgs_lees_ferry_annual_af = lees_ferry_gage.annual_af(water_year_month=10)
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
                   ylabel='af', ymin=7000000, ymax=13000000, yinterval=250000,
                   xlabel='Water Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.running_average(usbr_glen_canyon_annual_release_af, 10, sub_plot=0)
    graph.running_average(usgs_lees_ferry_annual_af, 10, sub_plot=0)

    usbr_lake_powell_release_af_1999_2021 = WaterGraph.array_in_time_range(usbr_glen_canyon_annual_release_af,
                                                                           datetime.datetime(1999, 1, 1),
                                                                           datetime.datetime(2021, 12, 31))

    # USGS Paria At Lees Ferry Gage Daily Discharge Mean
    #
    usgs_paria_annual_af = usgs_paria_lees_ferry().annual_af()
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
                   ylabel='maf', ymin=7000000, ymax=13000000, yinterval=250000,
                   xlabel='Water Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.running_average(glen_canyon_plus_paria, 10, sub_plot=0)
    graph.running_average(usgs_lees_ferry_af_1999_2021, 10, sub_plot=0)
    graph.fig.waitforbuttonpress()

    graph = WaterGraph()
    graph.bars(discrepancy,
               title='Lake Powell Release Difference USBR Glen Canyon + paria vs USGS Lees Ferry',
               ylabel='kaf', ymin=0, ymax=300000, yinterval=50000,
               xlabel='Water Year', xinterval=2, format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usgs_paria_lees_ferry(graph=True):
    gage = USGSGage('09382000', start_date='1932-10-01',
                    cfs_max=6500, cfs_interval=500,
                    annual_min=0, annual_max=50000, annual_interval=2500, annual_unit='kaf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_little_colorado_cameron(graph=True):
    gage = USGSGage('09402000', start_date='1947-06-1', color='firebrick',
                    cfs_max=19000, cfs_interval=1000,
                    annual_min=0, annual_max=850000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_virgin_at_littlefield(graph=True):
    gage = USGSGage('09415000', start_date='1929-10-01', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_min=0, annual_max=600000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_muddy_near_glendale(graph=True):
    gage = USGSGage('09419000', start_date='1950-02-01', color='firebrick',
                    cfs_max=5500, cfs_interval=500,
                    annual_min=0, annual_max=54000, annual_interval=2000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_gila_duncan(graph=True):
    gage = USGSGage('09439000', start_date='2003-09-30', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_min=0, annual_max=350000, annual_interval=25000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_gila_goodyear(graph=True):
    gage = USGSGage('09514100', start_date='1992-10-01', color='firebrick',
                    cfs_max=140000, cfs_interval=10000,
                    annual_min=0, annual_max=1000000, annual_interval=50000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_gila_dome(graph=True):
    gage_full = USGSGage('09520500', start_date='1905-01-01', color='firebrick',
                         cfs_max=96000, cfs_interval=20000,
                         annual_min=0, annual_max=4500000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage_full)

    gage = USGSGage('09520500', start_date='1996-01-01', color='firebrick',
                    cfs_max=1000, cfs_interval=100,
                    annual_min=0, annual_max=200000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage_full


def usgs_bill_williams_parker(graph=True):
    gage = USGSGage('09426620', start_date='1988-10-01', color='firebrick',
                    cfs_max=8000, cfs_interval=500,
                    annual_min=0, annual_max=450000, annual_interval=50000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_salt_above_roosevelt(graph=True):
    gage = USGSGage('09498500', start_date='1913-10-01', color='firebrick',
                    cfs_max=95000, cfs_interval=5000,
                    annual_min=0, annual_max=2400000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_below_parker(graph=True):
    gage = USGSGage('09427520', start_date='1934-11-16', color='firebrick',
                    cfs_max=41000, cfs_interval=1000,
                    annual_min=4000000, annual_max=22000000, annual_interval=1000000, annual_unit='maf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_nv_las_vegas_wash_below_lake_las_vegas(graph=True):
    gage = USGSGage('09419800', start_date='1969-08-01', color='firebrick',
                    cfs_max=2000, cfs_interval=100,
                    annual_min=0, annual_max=300000, annual_interval=10000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_below_palo_verde(graph=True):
    gage = USGSGage('09429100', start_date='1956-03-24', color='firebrick',
                    cfs_max=17000, cfs_interval=1000,
                    annual_min=0, annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_nothern_international_border(graph=True):
    gage = USGSGage('09522000', start_date='1950-01-01', color='firebrick',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=4000000, annual_interval=200000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_below_imperial(graph=True):
    # Bogus gage
    gage = USGSGage('09429500', start_date='2018-11-29', color='firebrick',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=500000, annual_interval=20000, annual_unit='kaf', year_interval=1)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_below_davis(graph=True):
    gage = USGSGage('09423000', start_date='1905-05-11', color='firebrick',
                    cfs_max=120000, cfs_interval=5000,
                    annual_min=6000000, annual_max=23000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_below_laguna(graph=True):
    gage = USGSGage('09429600', start_date='1971-12-16', color='firebrick',
                    cfs_max=32000, cfs_interval=2000,
                    annual_min=0, annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def reshape_annual_range(a, year_min, year_max):
    years = year_max - year_min + 1
    b = np.zeros(years, [('dt', 'i'), ('val', 'f')])

    for year in range(year_min, year_max + 1):
        b[year - year_min][0] = year
        b[year - year_min][1] = 0

    for year_val in a:
        year = year_val[0]
        if year_min <= year <= year_max:
            b[year - year_min][1] = year_val[1]

    return b


def subtract_annual(minuend, subtrahend, start_year=0, end_year=0):
    difference = np.zeros(len(minuend), [('dt', 'i'), ('val', 'f')])
    difference['dt'] = minuend['dt']
    difference['val'] = minuend['val'] - subtrahend['val']
    if start_year and end_year:
        difference = reshape_annual_range(difference, start_year, end_year)
    return difference


def add_annual(augend, addend, start_year=0, end_year=0):
    summation = np.zeros(len(augend), [('dt', 'i'), ('val', 'f')])
    summation['dt'] = augend['dt']
    summation['val'] = augend['val'] + addend['val']
    if start_year and end_year:
        summation = reshape_annual_range(summation, start_year, end_year)
    return summation


def add3_annual(augend, addend, addend2, start_year=0, end_year=0):
    summation = np.zeros(len(augend), [('dt', 'i'), ('val', 'f')])
    summation['dt'] = augend['dt']
    summation['val'] = augend['val'] + addend['val']
    summation['val'] = summation['val'] + addend2['val']

    if start_year and end_year:
        summation = reshape_annual_range(summation, start_year, end_year)
    return summation


def usgs_imperial_all_american():
    year_interval = 4

    # FIXME Hoover, Parker, Davis

    # Colorado River Indian Tribe (CRIT) and Rock Dam Release
    graph = WaterGraph(nrows=4)

    crit_diversion_annual_af = usbr_report.annual_af('az/usbr_az_crit_diversion.csv')
    crit_cu_annual_af = usbr_report.annual_af('az/usbr_az_crit_consumptive_use.csv')

    bar_data = [{'data': crit_diversion_annual_af, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': crit_cu_annual_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='USBR AR CRIT Diversion & Consumptive Use (Annual)',
                       xinterval=year_interval, ymin=150000, ymax=750000, yinterval=100000,
                       ylabel='kaf',  format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(crit_diversion_annual_af, 10, sub_plot=0)
    graph.running_average(crit_cu_annual_af, 10, sub_plot=0)

    rock_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_rock_dam.csv')
    graph.bars(rock_dam_release_annual_af, sub_plot=1, title='USBR AR Rock Dam Release (Annual)',
               xinterval=year_interval, ymin=4500000, ymax=8000000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    crit_return_flows_annual = subtract_annual(crit_diversion_annual_af, crit_cu_annual_af, 1965, current_last_year)
    graph.bars(crit_return_flows_annual, sub_plot=2, title='USBR AR CRIT Return Flows(Annual)',
               xinterval=year_interval, ymin=150000, ymax=400000, yinterval=50000, color='darkmagenta',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    bar_data = [{'data': rock_dam_release_annual_af, 'label': 'Rock Dam Release', 'color': 'firebrick'},
                {'data': crit_return_flows_annual, 'label': 'CRIT Return Flows', 'color': 'darkmagenta'},
                ]
    graph.bars_stacked(bar_data, sub_plot=3, title='USBR AR Flow below Rock Dam with CRIT Return Flows (Annual)',
                       xinterval=year_interval, ymin=4500000, ymax=8000000, yinterval=500000, xlabel='Calendar Year',
                       ylabel='maf',  format_func=WaterGraph.format_maf)
    flows_below_rock_annual = add_annual(rock_dam_release_annual_af, crit_return_flows_annual, 1965, current_last_year)
    graph.running_average(flows_below_rock_annual, 10, sub_plot=3)

    graph.fig.waitforbuttonpress()

    # Palo Verde Diversion Dam Release and Return Flows
    graph = WaterGraph(nrows=4)

    palo_verde_diversion_annual_af = usbr_report.annual_af('ca/usbr_ca_palo_verde_diversion.csv')
    palo_verde_cu_annual_af = usbr_report.annual_af('ca/usbr_ca_palo_verde_consumptive_use.csv')
    bar_data = [{'data': palo_verde_diversion_annual_af, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': palo_verde_cu_annual_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='USBR AR Palo Verde Diversion & Consumptive Use (Annual)',
                       xinterval=year_interval, ymin=200000, ymax=1100000, yinterval=100000,
                       ylabel='kaf',  format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(palo_verde_diversion_annual_af, 10, sub_plot=0)
    graph.running_average(palo_verde_cu_annual_af, 10, sub_plot=0)

    palo_verde_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_palo_verde_dam.csv')
    graph.bars(palo_verde_dam_release_annual_af, sub_plot=1, title='USBR AR Palo Verde Dam Release (Annual)',
               xinterval=year_interval, ymin=3500000, ymax=7000000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    palo_verde_return_flows_annual = subtract_annual(palo_verde_diversion_annual_af, palo_verde_cu_annual_af,
                                                     1965, current_last_year)
    graph.bars(palo_verde_return_flows_annual, sub_plot=2, title='Palo Verde Return Flows(Annual)',
               xinterval=year_interval, ymin=200000, ymax=600000, yinterval=50000, color='darkmagenta',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    bar_data = [{'data': palo_verde_dam_release_annual_af, 'label': 'Palo Verde Dam Release', 'color': 'firebrick'},
                {'data': palo_verde_return_flows_annual, 'label': 'Palo Verde Return Flows', 'color': 'darkmagenta'},
                ]
    graph.bars_stacked(bar_data, sub_plot=3, title='Flow below Palo Verde Dam with PV Return Flows (Annual)',
                       xinterval=year_interval, ymin=3500000, ymax=7000000, yinterval=500000, xlabel='Calendar Year',
                       ylabel='maf', format_func=WaterGraph.format_maf)
    flows_below_rock_annual = add_annual(palo_verde_dam_release_annual_af, palo_verde_return_flows_annual,
                                         1965, current_last_year)
    graph.running_average(flows_below_rock_annual, 10, sub_plot=3)

    graph.fig.waitforbuttonpress()

    # All American Canal Above Imperial Dam
    graph = WaterGraph(nrows=4)

    gage = USGSGage('09523000', start_date='1939-10-01')
    all_american_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(all_american_annual_af, sub_plot=1, title='USGS All American Canal Diversion (Annual)',
               xinterval=year_interval, ymin=3000000, ymax=6500000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    # Imperial Dam Release
    imperial_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv')
    graph.bars(imperial_dam_release_annual_af, sub_plot=3, title='USBR AR Imperial Dam Release (Annual)',
               xinterval=year_interval, ymax=1000000, yinterval=100000,
               color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # Colorado River Below Imperial Dam, new gage, not worth much
    # gage = USGSGage('09429500', start_date='2018-11-29')
    graph.fig.waitforbuttonpress()

    graph = WaterGraph(nrows=4)

    gage = USGSGage('09523200', start_date='1974-10-01')
    reservation_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(reservation_main_annual_af, sub_plot=0, title='USBR AR Reservation Main Canal (Annual)',
               xinterval=year_interval, ymin=0, ymax=70000, yinterval=10000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    gage = USGSGage('09524000', start_date='1938-10-01')
    yuma_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(yuma_main_annual_af, sub_plot=1, title='USGS Yuma Main Canal at Siphon Drop PP (Annual)',
               xinterval=year_interval, ymin=0, ymax=800000, yinterval=100000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # 09530500 10-14 CFS DRAIN 8-B NEAR WINTERHAVEN, CA
    # 0254970 160 CFS NEW R AT INTERNATIONAL BOUNDARY AT CALEXICO CA  1979-10-01
    # 09527594 150-45 CFS COACHELLA CANAL NEAR NILAND, CA  2009-10-17
    # 09527597 COACHELLA CANAL NEAR DESERT BEACH, CA  2009-10-24
    # 10254730 ALAMO R NR NILAND CA   1960-10-01
    # 10255550 NEW R NR WESTMORLAND CA  1943-01-01
    # 10259540 WHITEWATER R NR MECCA  1960-10-01

    # Coachella
    gage = USGSGage('09527590', start_date='2003-10-01')
    coachella_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(coachella_annual_af, sub_plot=2, title='USGS Coachella (Annual)',
               xinterval=year_interval, ymin=0, ymax=400000, yinterval=50000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # All American Drop 2, probably IID
    gage = USGSGage('09527700', start_date='2011-10-26')
    drop_2_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(drop_2_annual_af, sub_plot=3, title='USGS Drop 2 - Imperial(Annual)',
               xlabel='Calendar Year', xinterval=year_interval,
               ymin=0, ymax=3000000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    graph.fig.waitforbuttonpress()

    graph = WaterGraph(nrows=4)
    # Brock Inlet
    gage = USGSGage('09527630', start_date='2013-11-06')
    brock_inlet_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)

    # Brock Outlet
    gage = USGSGage('09527660', start_date='2013-10-23')
    brock_outlet_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)

    graph.bars_two(brock_inlet_annual_af, brock_outlet_annual_af,
                   title='USGS Brock Inlet and Outlet (Annual)', sub_plot=0,
                   label_a='Brock Inlet', color_a='royalblue',
                   label_b='Brock Outlet', color_b='firebrick',
                   xinterval=year_interval, ymax=175000, yinterval=25000,
                   ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(brock_outlet_annual_af, 10, sub_plot=0, label="10Y Avg Brock Outlet")

    gage = USGSGage('09523600', start_date='1966-10-01')
    yaqui_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(yaqui_main_annual_af, sub_plot=1, title='Yaqui (Annual)',
               xinterval=year_interval, ymin=0, ymax=12000, yinterval=2000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    gage = USGSGage('09523800', start_date='1966-10-01')
    pontiac_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(pontiac_main_annual_af, sub_plot=2, title='Pontiac (Annual)',
               xinterval=year_interval, ymin=0, ymax=12000, yinterval=2000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    gage = USGSGage('09526200', start_date='1995-01-01')
    ypsilanti_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(ypsilanti_main_annual_af, sub_plot=3, title='Ypsilanti (Annual)',
               xinterval=year_interval, ymin=0, ymax=15000, yinterval=3000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()


def usgs_imperial_all_american_drop_2(graph=True):
    gage = USGSGage('09527700', start_date='2011-10-26', color='firebrick',
                    cfs_max=6500, cfs_interval=500,
                    annual_min=0, annual_max=2600000, annual_interval=100000, annual_unit='maf', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_coachella_all_american(graph=True):
    gage = USGSGage('09527590', start_date='2003-10-01', color='firebrick',
                    cfs_max=850, cfs_interval=50,
                    annual_min=0, annual_max=400000, annual_interval=20000, annual_unit='kaf', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_gila_gravity_main_canal(graph=True):
    gage = USGSGage('09522500', start_date='1943-08-16', color='firebrick',
                    cfs_max=2300, cfs_interval=100,
                    annual_min=0, annual_max=1000000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_gila_gravity_main_canal_at_yuma_mesa_pumping(graph=True):
    gage = USGSGage('09522600', start_date='2005-09-30', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_north_gila_main_canal(graph=True):
    gage = USGSGage('09522600', start_date='1966-10-01', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_south_gila_main_canal(graph=True):
    gage = USGSGage('09522800', start_date='1973-10-01', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_city_of_yuma_at_avenue_9e_pumping(graph=True):
    gage = USGSGage('09522860', start_date='2015-09-30', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_reservation_main_canal(graph=True):
    gage = USGSGage('09523200', start_date='1974-10-01', color='firebrick',
                    cfs_max=270, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_yuma_main_canal(graph=True):
    gage = USGSGage('09524000', start_date='1938-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_reservation_main_drain_no_4(graph=True):
    gage = USGSGage('09530000', start_date='1966-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_yuma_main_canal_wasteway(graph=True):
    gage = USGSGage('09525000', start_date='1930-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_river_below_yuma_wasteway(graph=True):
    gage = USGSGage('09521100', start_date='1963-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_yuma_municipal(graph=True):
    gage = USGSGage('09526000', start_date='1983-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_unit_b_canal_near_yuma(graph=True):
    gage = USGSGage('09522900', start_date='2005-09-30', color='firebrick',
                    cfs_max=120, cfs_interval=10,
                    annual_min=0, annual_max=30000, annual_interval=1000, annual_unit='kaf', year_interval=1)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_mcas_diversion_of_b_canal_near_yuma(graph=True):
    gage = USGSGage('09522880', start_date='2005-09-30', color='firebrick',
                    cfs_max=120, cfs_interval=10,
                    annual_min=0, annual_max=30000, annual_interval=1000, annual_unit='kaf', year_interval=1)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_wellton_mohawk_main_canal(graph=True):
    gage = USGSGage('09522700', start_date='1974-10-01', color='firebrick',
                    cfs_max=1900, cfs_interval=200,
                    annual_min=0, annual_max=500000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_wellton_mohawk_main_outlet_drain(graph=True):
    gage = USGSGage('09529300', start_date='1966-10-01', color='firebrick',
                    cfs_max=350, cfs_interval=50,
                    annual_min=0, annual_max=230000, annual_interval=20000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_palo_verde_canal(graph=True):
    gage = USGSGage('09429000', start_date='1950-10-01', color='firebrick',
                    cfs_max=2400, cfs_interval=100,
                    annual_min=650000, annual_max=1050000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_crir_canal_near_parker(graph=True):
    gage = USGSGage('09428500', start_date='1954-10-01', color='firebrick',
                    cfs_max=2000, cfs_interval=100,
                    annual_min=250000, annual_max=750000, annual_interval=50000, annual_unit='kaf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_yampa_river_near_maybell(graph=True):
    gage = USGSGage('09251000', start_date='1916-05-01',
                    cfs_max=25000, cfs_interval=5000,
                    annual_min=0, annual_max=2300000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_gunnison_grand_junction(graph=True):
    gage = USGSGage('09152500', start_date='1896-10-01',
                    cfs_max=36000, cfs_interval=2000,
                    annual_max=3800000, annual_interval=200000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_san_juan_bluff(graph=True):
    gage = USGSGage('09379500', start_date='1941-10-01',
                    cfs_max=36000, cfs_interval=2000,
                    annual_min=400000, annual_max=3300000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_green_river_at_green_river(graph=True):
    gage = USGSGage('09315000', start_date='1894-10-01',
                    cfs_max=70000, cfs_interval=5000,
                    annual_min=1000000, annual_max=9000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_cisco(graph=True):
    gage = USGSGage('09180500', start_date='1913-10-01',
                    cfs_max=75000, cfs_interval=2500,
                    annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_colorado_potash(graph=True):
    gage = USGSGage('09185600', start_date='2014-10-29',
                    cfs_max=75000, cfs_interval=2500,
                    annual_max=11000000, annual_interval=250000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_dirty_devil(graph=True):
    gage = USGSGage('09333500', start_date='1948-06-07',
                    cfs_max=28000, cfs_interval=1000,
                    annual_max=190000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_escalante(graph=True):
    gage = USGSGage('09337500', start_date='1911-01-01',
                    cfs_max=1000, cfs_interval=100,
                    annual_max=30000, annual_interval=2000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_dolores_below_rico(graph=True):
    gage = USGSGage('09165000', start_date='1951-10-01',
                    cfs_max=1900, cfs_interval=100,
                    annual_max=170000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_dolores_at_dolores(graph=True):
    gage = USGSGage('09166500', start_date='1895-10-01',
                    cfs_max=7000, cfs_interval=500,
                    annual_max=575000, annual_interval=25000, annual_unit='kaf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_dolores_at_cisco(graph=True):
    gage = USGSGage('09180000', start_date='1950-12-01',
                    cfs_max=17000, cfs_interval=1000,
                    annual_max=1500000, annual_interval=50000, annual_unit='kaf')
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_mud_creek_cortez(graph=True):
    gage = USGSGage('09371492', start_date='1981-10-01',
                    cfs_max=240, cfs_interval=10,
                    annual_max=7500, annual_interval=500, annual_unit='af', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_mcelmo_stateline(graph=True):
    gage = USGSGage('09372000', start_date='1951-03-01',
                    cfs_max=1300, cfs_interval=50,
                    annual_max=70000, annual_interval=5000, annual_unit='af', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def usgs_mcelmo_trail_canyon(graph=True):
    gage = USGSGage('09371520', start_date='1993-08-01',
                    cfs_max=1250, cfs_interval=50,
                    annual_max=60000, annual_interval=5000, annual_unit='af', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def lake_powell_inflow():
    start_year = 1963
    end_year = 2022

    show_graph = False
    show_annotated = False

    usgs_colorado_cisco_gage = usgs_colorado_cisco(graph=show_graph)
    if show_annotated:
        colorado_cisco_af = usgs_colorado_cisco_gage.annual_af()
        graph = WaterGraph(nrows=1)
        graph.bars(colorado_cisco_af, sub_plot=0, title=usgs_colorado_cisco_gage.site_name, color='royalblue',
                   ymin=0, ymax=11500000, yinterval=500000, xinterval=4,
                   xlabel='Water Year', bar_width=1,  # xmin=start_year, xmax=end_year,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.annotate_vertical_arrow(1916, "Grand Valley", offset_percent=2.5)
        graph.annotate_vertical_arrow(1942, "Green Mountain", offset_percent=2.5)
        graph.annotate_vertical_arrow(1947, "Adams Tunnel", offset_percent=5)
        graph.annotate_vertical_arrow(1963, "Dillon", offset_percent=2.5)
        graph.annotate_vertical_arrow(1966, "Blue Mesa", offset_percent=5)
        graph.fig.waitforbuttonpress()
    colorado_cisco_af = usgs_colorado_cisco_gage.annual_af(start_year=start_year, end_year=end_year)

    usgs_green_river_gage = usgs_green_river_at_green_river(graph=show_graph)
    if show_annotated:
        green_river_af = usgs_green_river_gage.annual_af()
        graph = WaterGraph(nrows=1)
        graph.bars(green_river_af, sub_plot=0, title=usgs_green_river_gage.site_name, color='royalblue',
                   ymin=0, ymax=9000000, yinterval=500000, xinterval=4,
                   xlabel='Water Year', bar_width=1,  # xmin=start_year, xmax=end_year,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.annotate_vertical_arrow(1962, "Flaming Gorge", offset_percent=2.5)
        graph.annotate_vertical_arrow(1963, "Fontenelle", offset_percent=5)
        graph.fig.waitforbuttonpress()
    green_river_af = usgs_green_river_gage.annual_af(start_year=start_year, end_year=end_year)

    usgs_san_juan_bluff_gage = usgs_san_juan_bluff(graph=show_graph)
    if show_annotated:
        san_juan_af = usgs_san_juan_bluff_gage.annual_af()
        graph = WaterGraph(nrows=1)
        graph.bars(san_juan_af, sub_plot=0, title=usgs_san_juan_bluff_gage.site_name, color='royalblue',
                   ymin=0, ymax=3250000, yinterval=250000, xinterval=4,
                   xlabel='Water Year', # xmin=start_year, xmax=end_year,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.annotate_vertical_arrow(1962, "Navajo", offset_percent=2.5)
        graph.fig.waitforbuttonpress()
    san_juan_af = usgs_san_juan_bluff_gage.annual_af(start_year=start_year, end_year=end_year)

    usgs_dirty_devil_gage = usgs_dirty_devil(graph=True)
    dirty_devil_af = usgs_dirty_devil_gage.annual_af(start_year=start_year, end_year=end_year)
    # Only around 8 kaf annually
    # usgs_escalante_gage = usgs_escalante(graph=True)
    # escalante_af = usgs_escalante_gage.annual_af(start_year=start_year, end_year=end_year)

    year_interval = 3
    graph = WaterGraph(nrows=1)
    usbr_lake_powell_inflow_af = 4288
    usbr_lake_powell_inflow_volume_unregulated_af = 4301
    annual_inflow_af = usbr_rise.annual_af(usbr_lake_powell_inflow_af)
    # graph.bars(annual_inflow_af, sub_plot=0, title='Lake Powell Inflow',
    #            ymin=3000000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
    #           ylabel='maf',  format_func=WaterGraph.format_maf)

    annual_inflow_unregulated_af = usbr_rise.annual_af(usbr_lake_powell_inflow_volume_unregulated_af)
    # graph.bars(annual_inflow_unregulated_af, sub_plot=1, title='Lake Powell Unregulated Inflow',
    #            ymin=300000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
    #            ylabel='maf', format_func=WaterGraph.format_maf)
    # bar_data = [{'data': annual_inflow_unregulated_af, 'label': 'Lake Powell Unregulated Inflow', 'color': 'blue'},
    #             {'data': annual_inflow_af, 'label': 'Lake Powell Inflow', 'color': 'royalblue'},
    #             ]
    # graph.bars_stacked(bar_data, sub_plot=0, title='Lake Powell Inflow & Unregulated Inflow',
    #                    ymin=300000, ymax=21000000, yinterval=2000000,
    #                    xlabel='Water Year', xinterval=3,
    #                    ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)

    graph.bars_two(annual_inflow_af, annual_inflow_unregulated_af,
                   title='Lake Powell Inflow & Unregulated Inflow',
                   label_a='Inflow', color_a='royalblue',
                   label_b='Unregulated Inflow', color_b='darkblue',
                   ylabel='af', ymin=0, ymax=21000000, yinterval=2000000,
                   xlabel='Water Year', xinterval=year_interval, format_func=WaterGraph.format_maf)
    graph.running_average(annual_inflow_af, 10, sub_plot=0)
    graph.running_average(annual_inflow_unregulated_af, 10, sub_plot=0)

    graph.fig.waitforbuttonpress()

    graph = WaterGraph(nrows=2)
    bar_data = [{'data': colorado_cisco_af, 'label': 'Colorado at Cisco', 'color': 'darkblue'},
                {'data': green_river_af, 'label': 'Green at Green River', 'color': 'royalblue'},
                {'data': san_juan_af, 'label': 'San Juan at Bluff', 'color': 'cornflowerblue'},
                {'data': dirty_devil_af, 'label': 'Dirty Devil', 'color': 'lightblue'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='USGS Lake Powell River Inflows',
                       ymin=0, ymax=22000000, yinterval=1000000,
                       xlabel='Water Year', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=True)
    total = add3_annual(colorado_cisco_af, green_river_af, san_juan_af)
    graph.running_average(total, 10, sub_plot=0)

    graph.bars(annual_inflow_af, sub_plot=1, title='USBR RISE Lake Powell Inflow',
               ymin=0, ymax=22000000, yinterval=1000000, xinterval=year_interval,
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def usbr_southwest_colorado():
    usgs_mud_creek_cortez()
    usgs_mcelmo_trail_canyon()
    usgs_mcelmo_stateline()
    usgs_dolores_below_rico()
    usgs_dolores_at_dolores()


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

    usgs_colorado_river_below_yuma_wasteway()
    usgs_colorado_nothern_international_border()


def usgs_lower_colorado():
    usgs_lees_ferry()
    # usgs_paria_lees_ferry()
    usgs_nv_las_vegas_wash_below_lake_las_vegas()
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
    usgs_lower_colorado()

    usgs_lower_colorado_tributaries()


def usbr_az_cap():
    year_interval = 3

    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_central_arizona_project_diversion.csv')
    graph = WaterGraph(nrows=3)
    graph.plot(monthly_af, sub_plot=0, title='Lake Havasu CAP Wilmer Pumping Plant (Monthly)',
               xinterval=year_interval, ymax=200000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Lake Havasu CAP Wilmer Pumping Plant (Annual)',
               xinterval=year_interval, ymin=0, ymax=1800000, yinterval=100000,
               xlabel='Calendar Year',   color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    ics = usbr_lake_mead_ics()
    ics_az_delta = ics['AZ Delta']
    ics_az_delta = graph.reshape_annual_range(ics_az_delta, 1985, current_last_year)

    bar_data = [{'data': annual_af, 'label': 'CAP Wilmer Pumps', 'color': 'firebrick'},
                {'data': ics_az_delta, 'label': 'AZ ICS Deposits', 'color': 'mediumseagreen'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Lake Havasu CAP Wilmer Pumping Plant + AZ ICS Deposits',
                       ylabel='maf', ymin=0, ymax=1800000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def usbr_ca_palo_verde():
    year_interval = 3
    graph = WaterGraph(nrows=2)

    # Diversion
    monthly_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_palo_verde_diversion.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Palo Verde Diversion & Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=125000, yinterval=50000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    monthly_cu_af = usbr_report.load_monthly_csv('ca/usbr_ca_palo_verde_consumptive_use.csv')
    graph.plot(monthly_cu_af, sub_plot=0,
               xinterval=year_interval, ymax=125000, yinterval=50000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)
    # graph.bars(annual_diversion_af, sub_plot=1, title='Imperial Irrigation District Diversion (Annual)',
    #            ymin=2200000, ymax=3300000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #            ylabel='maf', format_func=WaterGraph.format_maf)

    # Consumptive Use
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)
    # graph.bars(annual_cu_af, sub_plot=3, title='Imperial Irrigtion Consumptive Use',
    #            ymin=2200000, ymax=3400000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #           ylabel='maf', format_func=WaterGraph.format_maf)

    bar_data = [{'data': annual_diversion_af, 'label': 'Palo Verde Diversion', 'color': 'darkmagenta'},
                {'data': annual_cu_af, 'label': 'Palo Verde Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Palo Verde Diversion & Consumptive Use (Annual)',
                       ymin=0, ymax=1100000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def usbr_az_crit():
    year_interval = 3

    # Diversion
    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_crit_diversion.csv')
    graph = WaterGraph(nrows=4)
    graph.plot(monthly_af, sub_plot=0, title='Colorado River Indian Tribe Diversion (Monthly)',
               xinterval=year_interval, ymax=130000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Colorado River Indian Tribe Diversion (Annual)',
               ymin=0, ymax=1200000, yinterval=100000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)

    # Consumptive Use
    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_crit_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=2, title='Colorado River Indian Tribe Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=-15000, ymax=90000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Colorado River Indian Tribe Consumptive Use (Annual)',
               ymin=0, ymax=550000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.fig.waitforbuttonpress()


def usbr_ca_total():
    year_interval = 4

    graph = WaterGraph(nrows=4)

    # Diversion
    monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_diversion.csv')
    graph.plot(monthly_af, sub_plot=0, title='California Total Diversion (Monthly)',
               xinterval=year_interval, ymin=100000, ymax=700000, yinterval=100000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='California Total Diversion (Annual)',
               ymin=3600000, ymax=6000000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='darkmagenta',
               ylabel='maf', format_func=WaterGraph.format_maf)

    # Consumptive Use
    monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=0, title='California Total Diversion & Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=100000, ymax=700000, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=2, title='California Total Consumptive Use (Annual)',
               ymin=3600000, ymax=6000000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)

    monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_measured_returns.csv')
    graph.plot(monthly_af, sub_plot=3, title='California Measured Returns (Monthly)',
               xinterval=year_interval, ymax=100000, yinterval=50000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_unmeasured_returns.csv')
    graph.plot(monthly_af, sub_plot=3, title='California Unmeasured Returns (Monthly)',
               xinterval=year_interval, ymax=100000, yinterval=50000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.fig.waitforbuttonpress()


def usbr_diversion_vs_consumptive(state_code, name, state_name,
                                  ymin1=0, ymax1=1000000, yinterval1=100000, yformat1='maf',
                                  ymin2=0, ymax2=1000000, yinterval2=100000, yformat2='kaf'):
    year_interval = 4

    graph = WaterGraph(nrows=2)

    # Diversion
    diversion_file_name = state_code + '/usbr_' + state_code + '_' + name + '_diversion.csv'
    annual_diversion_af = usbr_report.annual_af(diversion_file_name)

    cu_file_name = state_code + '/usbr_' + state_code + '_' + name + '_consumptive_use.csv'
    annual_cu_af = usbr_report.annual_af(cu_file_name)

    measured_file_name = state_code + '/usbr_' + state_code + '_' + name + '_measured_returns.csv'
    annual_measured_af = usbr_report.annual_af(measured_file_name, 1964, current_last_year)

    unmeasured_file_name = state_code + '/usbr_' + state_code + '_' + name + '_unmeasured_returns.csv'
    annual_unmeasured_af = usbr_report.annual_af(unmeasured_file_name, 1964, current_last_year)

    annual_diversion_minus_cu = subtract_annual(annual_diversion_af, annual_cu_af)

    if yformat1 == 'maf':
        format_func = WaterGraph.format_maf
    elif yformat1 == 'kaf':
        format_func = WaterGraph.format_kaf
    else:
        format_func = WaterGraph.format_af
    graph.bars(annual_diversion_af, sub_plot=0, title=state_name+' Diversion & Consumptive Use (Annual)',
               ymin=ymin1, ymax=ymax1, yinterval=yinterval1, label='Diversion',
               xlabel='', xinterval=year_interval, color='darkmagenta',
               ylabel=yformat1, format_func=format_func)

    bar_data = [
                {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                {'data': annual_measured_af, 'label': 'Measured Returns', 'color': 'darkorchid'},
                {'data': annual_unmeasured_af, 'label': 'Unmeasured Returns', 'color': 'mediumorchid'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title=state_name+' Totals (Annual)',
                       ymin=ymin1, ymax=ymax1, yinterval=yinterval1,
                       xlabel='', xinterval=year_interval,
                       ylabel=yformat1, format_func=format_func)

    if yformat2 == 'maf':
        format_func = WaterGraph.format_maf
    elif yformat2 == 'kaf':
        format_func = WaterGraph.format_kaf
    else:
        format_func = WaterGraph.format_af
    graph.bars(annual_diversion_minus_cu, sub_plot=1, title='Diversion minus Consumptive Use (Annual)',
               ymin=ymin2, ymax=ymax2, yinterval=yinterval2,
               xlabel='', xinterval=year_interval, color='darkmagenta',
               ylabel=yformat1, format_func=format_func)

    graph.fig.waitforbuttonpress()


def usbr_lower_basin_states_total_use():
    year_interval = 3
    graph = WaterGraph(nrows=3)

    # CA Total Diversion & Consumptive Use
    ca_diversion_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_diversion.csv')
    ca_diversion_annual_af = usbr_report.monthly_to_water_year(ca_diversion_monthly_af, water_year_month=1)

    ca_use_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_consumptive_use.csv')
    ca_use_annual_af = usbr_report.monthly_to_water_year(ca_use_monthly_af, water_year_month=1)

    bar_data = [{'data': ca_diversion_annual_af, 'label': 'California Diversion', 'color': 'darkmagenta'},
                {'data': ca_use_annual_af, 'label': 'California Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='California Totals (Annual)',
                       ymin=0, ymax=6000000, yinterval=1000000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(ca_use_annual_af, 10, sub_plot=0)

    # AZ Total Diversion & Consumptive Use
    az_diversion_monthly_af = usbr_report.load_monthly_csv('az/usbr_az_total_diversion.csv')
    az_diversion_annual_af = usbr_report.monthly_to_water_year(az_diversion_monthly_af, water_year_month=1)

    az_use_monthly_af = usbr_report.load_monthly_csv('az/usbr_az_total_consumptive_use.csv')
    az_use_annual_af = usbr_report.monthly_to_water_year(az_use_monthly_af, water_year_month=1)

    bar_data = [{'data': az_diversion_annual_af, 'label': 'Arizona Diversion', 'color': 'darkmagenta'},
                {'data': az_use_annual_af, 'label': 'Arizona Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Arizona Totals (Annual)',
                       ymin=0, ymax=4000000, yinterval=500000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(az_use_annual_af, 10, sub_plot=1)

    # NV Total Diversion & Consumptive Use
    nv_diversion_monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_total_diversion.csv')
    nv_diversion_annual_af = usbr_report.monthly_to_water_year(nv_diversion_monthly_af, water_year_month=1)

    nv_use_monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_total_consumptive_use.csv')
    nv_use_annual_af = usbr_report.monthly_to_water_year(nv_use_monthly_af, water_year_month=1)

    bar_data = [{'data': nv_diversion_annual_af, 'label': 'Nevada Diversion', 'color': 'darkmagenta'},
                {'data': nv_use_annual_af, 'label': 'Nevada Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Nevada Totals (Annual)',
                       ymin=0, ymax=550000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(nv_use_annual_af, 10, sub_plot=2)

    graph.fig.waitforbuttonpress()

    # Total use as stacked bars
    total_use_annual_af = np.zeros(len(ca_use_annual_af), [('dt', 'i'), ('val', 'f')])
    total_use_annual_af['dt'] = ca_use_annual_af['dt']
    total_use_annual_af['val'] = ca_use_annual_af['val']
    total_use_annual_af['val'] += az_use_annual_af['val']
    total_use_annual_af['val'] += nv_use_annual_af['val']

    # total_diversion_annual_af = np.zeros(len(ca_diversion_annual_af), [('dt', 'i'), ('val', 'f')])
    # total_diversion_annual_af['dt'] = ca_diversion_annual_af['dt']
    # total_diversion_annual_af['val'] = ca_diversion_annual_af['val']
    # total_diversion_annual_af['val'] += az_diversion_annual_af['val']
    # total_diversion_annual_af['val'] += nv_diversion_annual_af['val']

    # diversion_above_use_annual_af = np.zeros(len(ca_diversion_annual_af), [('dt', 'i'), ('val', 'f')])
    # diversion_above_use_annual_af['dt'] = ca_diversion_annual_af['dt']
    # diversion_above_use_annual_af['val'] = total_diversion_annual_af['val']
    # diversion_above_use_annual_af['val'] -= total_use_annual_af['val']
    graph = WaterGraph(nrows=1)

    bar_data = [{'data': ca_use_annual_af, 'label': 'California Consumptive Use', 'color': 'maroon'},
                {'data': az_use_annual_af, 'label': 'Arizona Consumptive Use', 'color': 'firebrick'},
                {'data': nv_use_annual_af, 'label': 'Nevada Consumptive Use', 'color': 'lightcoral'},
                # {'data': diversion_above_use_annual_af, 'label': 'Total Diversions', 'color': 'darkmagenta'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Total Lower Basin Consumptive Use (Annual)',
                       ymin=0, ymax=9000000, yinterval=500000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf,)
    graph.running_average(total_use_annual_af, 10, sub_plot=0)
    graph.fig.waitforbuttonpress()


'''
    graph.plot(diversion_monthly_af, sub_plot=0, title='Arizona Total Diversion (Monthly)',
               xinterval=year_interval, ymin=0, ymax=450000, yinterval=100000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.plot(use_monthly_af, sub_plot=0, title='Arizona Total Diversion & Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=0, ymax=450000, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.bars(diversion_annual_af, sub_plot=1, title='Arizona Total Diversion (Annual)',
               ymin=0, ymax=3800000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='darkmagenta',
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.bars(use_annual_af, sub_plot=2, title='Arizona Total Consumptive Use (Annual)',
               ymin=0, ymax=3800000, yinterval=200000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)
'''


def usbr_mx():
    year_interval = 3

    graph = WaterGraph(nrows=3)

    treaty_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_satisfaction_of_treaty.csv')
    treaty_annual_af = usbr_report.monthly_to_water_year(treaty_monthly_af, water_year_month=1)

    excess_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_in_excess.csv')
    excess_annual_af = usbr_report.monthly_to_water_year(excess_monthly_af, water_year_month=1)

    graph.plot(excess_monthly_af, sub_plot=0, title='Mexico in Excess of Treaty (Monthly)',
               xinterval=year_interval, yinterval=100000, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)

    bar_data = [
                {'data': treaty_annual_af, 'label': 'Treaty', 'color': 'firebrick'},
                {'data': excess_annual_af, 'label': 'Excess of Treaty', 'color': 'lightcoral'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Mexico (Annual)',
                       ymin=0, ymax=16000000, yinterval=2000000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(excess_annual_af, 10, sub_plot=1)

    graph.bars_stacked(bar_data, sub_plot=2, title='Mexico (Annual)',
                       ymin=1300000, ymax=2000000, yinterval=100000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(excess_annual_af, 10, sub_plot=2)

    graph.fig.waitforbuttonpress()

    # Bypass pursuant to minute 242
    bypass_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_minute_242_bypass.csv')
    graph = WaterGraph(nrows=2)
    graph.plot(bypass_monthly_af, sub_plot=0, title='Mexico Pursuant to Minute 242 (Monthly)',
               xinterval=year_interval, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bypass_annual_af = usbr_report.monthly_to_water_year(bypass_monthly_af, water_year_month=1)
    graph.bars(bypass_annual_af, sub_plot=1, title='Mexico Pursuant to Minute 242 (Annual)',
               ymin=0, ymax=160000, yinterval=10000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.fig.waitforbuttonpress()

    graph = WaterGraph(nrows=5)
    graph.plot(treaty_monthly_af, sub_plot=0, title='Satisfaction of Treaty (Monthly)',
               xinterval=year_interval, ymin=0, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    nib_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_northern_international_boundary.csv')
    graph.plot(nib_monthly_af, sub_plot=1, title='Northern International Border (Monthly)',
               xinterval=year_interval, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    sib_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_southern_international_boundary.csv')
    graph.plot(sib_monthly_af, sub_plot=2, title='Southern International Border (Monthly)',
               xinterval=year_interval, yinterval=2000, color='firebrick',
               ylabel='af', format_func=WaterGraph.format_af)

    limitrophe_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_limitrophe.csv')
    graph.plot(limitrophe_monthly_af, sub_plot=3, title='Limitrophe (Monthly)',
               xinterval=year_interval, yinterval=200, color='firebrick',
               ylabel='af', format_func=WaterGraph.format_af)

    tijuana_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_tijuana.csv')
    graph.plot(tijuana_monthly_af, sub_plot=4, title='Tijuana (Monthly)',
               xinterval=year_interval, yinterval=100, color='firebrick',
               ylabel='af', format_func=WaterGraph.format_af)

    graph.fig.waitforbuttonpress()


def usbr_ca_imperial_irrigation_district():
    year_interval = 3
    graph = WaterGraph(nrows=3)

    # Diversion
    monthly_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)

    monthly_cu_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    monthly_brock_diversion_af = usbr_report.load_monthly_csv(
        'ca/usbr_ca_imperial_irrigation_brock_diversion.csv')
    annual_brock_diversion_af = usbr_report.monthly_to_water_year(monthly_brock_diversion_af, water_year_month=1)

    graph.plot(monthly_diversion_af, sub_plot=0, title='Imperial Diversions & Consumptive Use (Monthly)',
               xinterval=year_interval, yinterval=50000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0,
               xinterval=year_interval, yinterval=50000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_brock_diversion_af, sub_plot=1, title='Imperial Diversions from Brock (Monthly)',
               xinterval=1, yinterval=5000, color='lightcoral',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    # graph.bars(annual_diversion_af, sub_plot=1, title='Imperial Irrigation District Diversion (Annual)',
    #            ymin=2200000, ymax=3300000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #            ylabel='maf', format_func=WaterGraph.format_maf)

    # Consumptive Use
    # graph.bars(annual_cu_af, sub_plot=3, title='Imperial Irrigtion Consumptive Use',
    #            ymin=2200000, ymax=3400000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #           ylabel='maf', format_func=WaterGraph.format_maf)

    annual_brock_diversion_af = graph.reshape_annual_range(annual_brock_diversion_af, 1964, current_last_year)
    annual_brock_diversion_negative = np.zeros(len(annual_brock_diversion_af), [('dt', 'i'), ('val', 'f')])
    annual_brock_diversion_negative['dt'] = annual_cu_af['dt']
    annual_brock_diversion_negative['val'] = np.negative(annual_brock_diversion_af['val'])

    graph = WaterGraph()
    graph.bars(annual_diversion_af, sub_plot=0, title='USBR AR Imperial Diversions and Consumptive Use (Annual)',
               ymin=2300000, ymax=3300000, yinterval=50000, color='darkmagenta',
               xlabel='', xinterval=year_interval,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    bar_data = [
                {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                {'data': annual_brock_diversion_negative, 'label': 'Brock Diversions', 'color': 'lightcoral'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0, title='USBR AR Imperial Diversions and Consumptive Use (Annual)',
                       ymin=2300000, ymax=3300000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(annual_cu_af, 10, sub_plot=0, label='10Y CU Running Average')

    graph.fig.waitforbuttonpress()


def usbr_ca_coachella():
    year_interval = 3
    graph = WaterGraph(nrows=2)

    # Diversion
    monthly_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_coachella_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)
    monthly_cu_af = usbr_report.load_monthly_csv('ca/usbr_ca_coachella_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    graph.plot(monthly_diversion_af, sub_plot=0, title='USBR AR Coachella Diversion (Monthly)',
               xinterval=year_interval, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
                {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
                {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='USBR AR Coachella Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def usbr_az_yuma():
    year_interval = 3
    graph = WaterGraph(nrows=3)

    # Yuma Mesa Irrigaton - This is complicated, early years had a drain with return flows
    # migrated to returns, then measured and unmeasured returns later
    yuma_mesa_monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_mesa_irrigation_diversion.csv')
    yuma_mesa_annual_diversion_af = usbr_report.monthly_to_water_year(yuma_mesa_monthly_diversion_af,
                                                                      water_year_month=1)
    yuma_mesa_monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    yuma_mesa_annual_cu_af = usbr_report.monthly_to_water_year(yuma_mesa_monthly_cu_af, water_year_month=1)

    yuma_mesa_monthly_drain_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_mesa_outlet_drain_returns.csv')
    yuma_mesa_annual_drain_af = usbr_report.monthly_to_water_year(yuma_mesa_monthly_drain_af, water_year_month=1)

    yuma_mesa_monthly_returns_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_mesa_irrigation_returns.csv')
    yuma_mesa_annual_returns_af = usbr_report.monthly_to_water_year(yuma_mesa_monthly_returns_af, water_year_month=1)

    yuma_mesa_monthly_measured_returns_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_mesa_irrigation_measured_returns.csv')
    yuma_mesa_annual_measured_returns_af = usbr_report.monthly_to_water_year(yuma_mesa_monthly_measured_returns_af, water_year_month=1)

    yuma_mesa_monthly_unmeasured_returns_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_mesa_irrigation_unmeasured_returns.csv')
    yuma_mesa_annual_unmeasured_returns_af = usbr_report.monthly_to_water_year(yuma_mesa_monthly_unmeasured_returns_af, water_year_month=1)

    graph.plot(yuma_mesa_monthly_diversion_af, sub_plot=0, title='USBR AR Yuma Mesa Irrigation Diversion (Monthly)',
               xinterval=year_interval, ymax=35000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(yuma_mesa_monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=35000,  yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(yuma_mesa_monthly_drain_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=35000,  yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(yuma_mesa_monthly_unmeasured_returns_af, sub_plot=2, title='',
               xinterval=year_interval, ymax=50000,  yinterval=5000, color='blue',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(yuma_mesa_monthly_measured_returns_af, sub_plot=2, title='',
               xinterval=year_interval, ymax=50000,  yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(yuma_mesa_monthly_returns_af, sub_plot=2, title='',
               xinterval=year_interval, ymax=50000,  yinterval=5000, color='maroon',
               ylabel='kaf', format_func=WaterGraph.format_kaf)




    bar_data = [
        {'data': yuma_mesa_annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': yuma_mesa_annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='USBR AR Yuma County WUA Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=300000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_mesa_annual_diversion_af, 10, sub_plot=1)
    graph.running_average(yuma_mesa_annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()

    # Yuma County WUA
    yuma_county_monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_county_wua_diversion.csv')
    yuma_county_annual_diversion_af = usbr_report.monthly_to_water_year(yuma_county_monthly_diversion_af,
                                                                        water_year_month=1)
    yuma_county_monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_county_wua_consumptive_use.csv')
    yuma_county_annual_cu_af = usbr_report.monthly_to_water_year(yuma_county_monthly_cu_af, water_year_month=1)

    graph.plot(yuma_county_monthly_diversion_af, sub_plot=0, title='USBR AR Yuma County WUA Diversion (Monthly)',
               xinterval=year_interval, ymax=55000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(yuma_county_monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=55000,  yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': yuma_county_annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': yuma_county_annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='USBR AR Yuma County WUA Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=400000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_county_annual_diversion_af, 10, sub_plot=1)
    graph.running_average(yuma_county_annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()

    # Wellton Mohawk
    graph = WaterGraph(nrows=2)

    wellton_mohawk_monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_wellton_mohawk_diversion.csv')
    wellton_mohawk_annual_diversion_af = usbr_report.monthly_to_water_year(wellton_mohawk_monthly_diversion_af,
                                                                           water_year_month=1)
    wellton_mohawk_monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_wellton_mohawk_consumptive_use.csv')
    wellton_mohawk_annual_cu_af = usbr_report.monthly_to_water_year(wellton_mohawk_monthly_cu_af, water_year_month=1)

    graph.plot(wellton_mohawk_monthly_diversion_af, sub_plot=0, title='USBR AR Wellton-Mohawk Diversion (Monthly)',
               xinterval=year_interval, ymax=75000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(wellton_mohawk_monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=75000,  yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': wellton_mohawk_annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': wellton_mohawk_annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='USBR AR Wellton-Mohawk Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(wellton_mohawk_annual_diversion_af, 10, sub_plot=1)
    graph.running_average(wellton_mohawk_annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def usbr_nv_snwa():
    year_interval = 2
    monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_snwa_griffith_diversion.csv')
    graph = WaterGraph(nrows=4)
    graph.plot(monthly_af, sub_plot=0, title='Lake Mead SNWA Griffith Pumping Plant Diversion (Monthly)',
               xinterval=year_interval, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Lake Mead SNWA Griffith Pumping Plant Diversion (Annual)',
               ymin=0, ymax=500000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_las_vegas_wash_diversion.csv')
    graph.plot(monthly_af, sub_plot=2, title='Lake Mead Las Vegas Wash Return Flows (Monthly)',
               xinterval=year_interval, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Lake Mead Las Vegas Wash Return Flows (Annual)',
               ymin=0, ymax=250000, yinterval=50000,
               xlabel='Calendar Year',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.fig.waitforbuttonpress()


def usbr_ca_metropolitan():
    whitsett_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_metropolitan_diversion.csv')
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

    whitsett_san_diego_monthly_af = usbr_report.load_monthly_csv(
        'usbr_lake_havasu_met_for_san_diego_whitsett_pumps.csv')
    graph.plot(whitsett_san_diego_monthly_af, sub_plot=1,
               title='Lake Havasu Metropolitan San Diego Exchange Whitsett Pumping Plant Diversion (Monthly)',
               yinterval=1000, color='firebrick',
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
    ics_ca_withdrawals = graph.reshape_annual_range(ics_ca_withdrawals, 1964, current_last_year)

    ics_ca_deposits = usbr_report.positive_values(ics_ca_delta)
    ics_ca_deposits = graph.reshape_annual_range(ics_ca_deposits, 1964, current_last_year)

    bar_data = [{'data': whitsett_annual_af, 'label': 'Metropolitan Diversion', 'color': 'firebrick'},
                {'data': ics_ca_withdrawals, 'label': 'CA ICS Withdrawals', 'color': 'maroon'},
                {'data': ics_ca_deposits, 'label': 'CA ICS Deposits', 'color': 'mediumseagreen'},
                {'data': whitsett_san_diego_annual_af, 'label': 'San Diego Exchange', 'color': 'goldenrod'}
                ]
    graph.fig.waitforbuttonpress()

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


def usbr_ca():
    usbr_ca_metropolitan()
    usbr_ca_imperial_irrigation_district()
    usbr_ca_coachella()
    usbr_ca_palo_verde()
    usbr_ca_total()


def usbr_az():
    usbr_az_crit()
    usbr_az_cap()


def usbr_nv():
    usbr_nv_snwa()
    usgs_nv_las_vegas_wash_below_lake_las_vegas()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, keyboardInterruptHandler)

    # usbr_catalog()
    lake_powell_inflow()
    usbr_az_yuma()
    usbr_upper_colorado_reservoirs()
    usbr_lake_havasu()
    usgs_lees_ferry()
    usgs_lower_colorado_tributaries()
    usbr_az_yuma()

    # usbr_az_cap()
    usbr_lower_colorado_reservoirs()

    usbr_nv_snwa()
    usbr_ca_metropolitan()

    # usbr_lake_powell()

    usgs_north_gila_main_canal()
    usgs_south_gila_main_canal()

    usgs_wellton_mohawk_main_canal()
    usgs_wellton_mohawk_main_outlet_drain()

    usbr_ca_imperial_irrigation_district()

    usbr_ca_coachella()
    usgs_imperial_all_american()
    usbr_diversion_vs_consumptive('ca', 'total', 'California',
                                  ymin1=3500000, ymax1=6000000,
                                  ymin2=350000, ymax2=750000, yinterval2=50000)
    usbr_diversion_vs_consumptive('nv', 'total', 'Nevada',
                                  ymin1=0, ymax1=550000, yinterval1=50000, yformat1='kaf',
                                  ymin2=0, ymax2=300000, yinterval2=25000)
    usbr_diversion_vs_consumptive('az', 'total', 'Arizona',
                                  ymin1=900000, ymax1=3800000,
                                  ymin2=550000, ymax2=900000, yinterval2=25000)
    usbr_diversion_vs_consumptive('az', 'crit', 'Colorado River Indian',
                                  ymin1=0, ymax1=750000,
                                  ymin2=170000, ymax2=400000, yinterval2=25000)
    usbr_diversion_vs_consumptive('az', 'wellton_mohawk', 'Wellton-Mohawk',
                                  ymin1=0, ymax1=600000, yformat1='kaf',
                                  ymin2=-20000, ymax2=275000, yinterval2=25000)
    usbr_diversion_vs_consumptive('ca', 'metropolitan', 'Metropolitan',
                                  ymin1=900000, ymax1=3800000,
                                  ymin2=550000, ymax2=900000, yinterval2=25000)
    usbr_mx()

    usbr_az()

    usbr_mx()
    usbr_ca_total()
    usbr_ca()
    usbr_nv()
    usbr_az()

    usbr_lower_basin_states_total_use()
    usbr_lake_powell()

    usbr_lake_mead()
    usbr_lake_mead_ics_by_state()

    usbr_upper_colorado_reservoirs()
    usbr_lower_colorado_reservoirs()

    usgs_lower_colorado()
    usbr_upper_colorado_reservoirs()
    usbr_lower_colorado_reservoirs()
    usgs_colorado_river_gages()
