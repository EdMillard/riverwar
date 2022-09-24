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
from source.usgs_gage import USGSGage
from graph.water import WaterGraph


def all_american_canal(graph=True):
    gage = USGSGage('09523000', start_date='1939-10-01', color='firebrick',
                    cfs_max=15000, cfs_interval=2000,
                    annual_min=3000000, annual_max=9000000, annual_interval=500000, year_interval=3,
                    annual_unit='maf')
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def brock_inlet(graph=True):
    gage = USGSGage('09527630', start_date='2013-11-06', color='firebrick',
                    cfs_max=2000, cfs_interval=200,
                    annual_min=0, annual_max=150000, annual_interval=10000, year_interval=1,
                    annual_unit='kaf')
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def brock_outlet(graph=True):
    gage = USGSGage('09527660', start_date='2013-11-06', color='firebrick',
                    cfs_max=1600, cfs_interval=200,
                    annual_min=0, annual_max=150000, annual_interval=10000, year_interval=1,
                    annual_unit='kaf')
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def imperial_all_american_drop_2(graph=True):
    gage = USGSGage('09527700', start_date='2011-10-26', color='firebrick',
                    cfs_max=6500, cfs_interval=500,
                    annual_min=0, annual_max=2900000, annual_interval=100000, annual_unit='maf', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def coachella_all_american(graph=True):
    gage = USGSGage('09527590', start_date='2003-10-01', color='firebrick',
                    cfs_max=850, cfs_interval=50,
                    annual_min=0, annual_max=400000, annual_interval=20000, annual_unit='kaf', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def reservation_main_canal(graph=True):
    gage = USGSGage('09523200', start_date='1974-10-01', color='firebrick',
                    cfs_max=240, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yaqui_canal(graph=True):
    gage = USGSGage('09523600', start_date='1966-10-01', color='firebrick',
                    cfs_max=240, cfs_interval=10,
                    annual_min=0, annual_max=12000, annual_interval=2000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def pontiac_canal(graph=True):
    gage = USGSGage('09523800', start_date='1966-10-01', color='firebrick',
                    cfs_max=240, cfs_interval=10,
                    annual_min=0, annual_max=12000, annual_interval=2000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def ypsilanti_canal(graph=True):
    gage = USGSGage('09526200', start_date='1995-01-01', color='firebrick',
                    cfs_max=240, cfs_interval=10,
                    annual_min=0, annual_max=15000, annual_interval=3000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def reservation_main_drain_no_4(graph=True):
    gage = USGSGage('09530000', start_date='1966-10-01', color='firebrick',
                    cfs_max=220, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yuma_main_canal_at_siphon_drop_PP(graph=True):
    gage = USGSGage('09524000', start_date='1938-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=1000000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yuma_main_canal_below_colorado_river_siphon_at_yuma(graph=True):
    gage = USGSGage('09525500', start_date='1938-10-01', color='firebrick',
                    cfs_max=1000, cfs_interval=200,
                    annual_min=0, annual_max=450000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yuma_main_canal_above_wasteway_near_winterhaven(graph=True):
    gage = USGSGage('09524700', start_date='2015-04-09', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=800000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yuma_main_canal_wasteway_at_yuma(graph=True):
    gage = USGSGage('09525000', start_date='1930-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=800000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def alamo_river_near_niland(graph=True):
    gage = USGSGage('10254730', start_date='1960-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=800000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def new_river_at_international_boundary_near_calexico(graph=True):
    gage = USGSGage('0254970', start_date='1979-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=800000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def new_river_near_westmorland(graph=True):
    gage = USGSGage('10255550', start_date='1943-01-01', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=600000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def drain_8_b_near_winterhaven(graph=True):
    gage = USGSGage('1979-10-01', start_date='1943-01-01', color='firebrick',
                    cfs_max=2100, cfs_interval=200,
                    annual_min=0, annual_max=600000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def test():
    # Diversions
    all_american_canal()
    brock_inlet()
    brock_outlet()
    coachella_all_american()
    reservation_main_canal()
    yaqui_canal()
    pontiac_canal()
    ypsilanti_canal()
    yuma_main_canal_below_colorado_river_siphon_at_yuma()
    yuma_main_canal_at_siphon_drop_PP()
    yuma_main_canal_above_wasteway_near_winterhaven()
    imperial_all_american_drop_2()

    # Salton sea
    new_river_at_international_boundary_near_calexico()  #  not responding to request
    new_river_near_westmorland()
    alamo_river_near_niland()

    # Wasteways and drains
    drain_8_b_near_winterhaven()
    reservation_main_drain_no_4()
    yuma_main_canal_wasteway_at_yuma()


    # 09527594 150-45 CFS COACHELLA CANAL NEAR NILAND, CA  2009-10-17
    # 09527597 COACHELLA CANAL NEAR DESERT BEACH, CA  2009-10-24
    # 10259540 WHITEWATER R NR MECCA  1960-10-01

