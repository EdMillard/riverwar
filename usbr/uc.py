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
from source import usbr_rise
from graph.water import WaterGraph
current_last_year = 2021


def test():
    lake_powell()
    fontenelle()
    flaming_gorge()
    blue_mesa()
    navajo_reservoir()
    lake_granby()
    green_mountain()
    ruedi()
    mcphee()


def lake_powell():
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
               ylabel='maf', format_func=WaterGraph.format_maf)

    annual_inflow_unregulated_af = usbr_rise.annual_af(usbr_lake_powell_inflow_volume_unregulated_af)
    graph.bars(annual_inflow_unregulated_af, sub_plot=2, title='Lake Powell Unregulated Inflow',
               ymin=2500000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
               ylabel='maf', format_func=WaterGraph.format_maf)

    annual_evaporation_af = usbr_rise.annual_af(usbr_lake_powell_evaporation_af)
    graph.bars(annual_evaporation_af, sub_plot=3, title='Lake Powell Evaporation',
               ymin=0, ymax=700000, yinterval=50000,
               xlabel='Water Year', xinterval=year_interval,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()

    graph = WaterGraph(nrows=1)

    annual_release_total_af = usbr_rise.annual_af(usbr_lake_powell_release_total_af)
    graph.bars(annual_release_total_af, sub_plot=0, title='Lake Powell Release',
               ymin=7000000, ymax=12600000, yinterval=100000,
               xlabel='Water Year', xinterval=1, xmin=2000, xmax=current_last_year,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.date_and_wait()


def navajo_reservoir():
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
    graph.date_and_wait()


def blue_mesa():
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
               xlabel='Water Year', xinterval=year_interval,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


def flaming_gorge():
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
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


def fontenelle():
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
               ylabel='kaf', format_func=WaterGraph.format_kaf)

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
               ymin=0, ymax=18000, yinterval=2000, xinterval=year_interval,
               xlabel='Water Year',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


# noinspection PyUnusedLocal
def green_mountain():
    usbr_green_mountain_storage_af = 21
    usbr_green_mountain_elevation_ft = 22
    usbr_green_mountain_release_total_cfs = 23


# noinspection PyUnusedLocal
def ruedi():
    usbr_ruedi_storage_af = 711
    usbr_ruedi_elevation_ft = 712
    usbr_ruedi_release_total_cfs = 716


# noinspection PyUnusedLocal
def mcphee():
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
def lake_granby():
    usbr_lake_granby_storage_af = 383
    usbr_lake_granby_elevation_ft = 384
    usbr_lake_granby_release_total_cfs = 386


# noinspection PyUnusedLocal
def grand_lake():
    usbr_lake_grand_lake_storage_af = 371
    usbr_lake_grand_lake_elevation_ft = 372


# noinspection PyUnusedLocal
def shadow_mountain():
    usbr_lake_shadow_mountain_storage_af = 737
    usbr_lake_shadow_mountain_elevation_ft = 738
    usbr_lake_shadow_mountain_release_total_cfs = 740
