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


def lees_ferry(graph=True):
    gage = USGSGage('09380000', start_date='1921-10-01',
                    cfs_max=130000, cfs_interval=5000,
                    annual_min=6000000, annual_max=21000000, annual_interval=500000, annual_unit='maf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def paria_lees_ferry(graph=True):
    gage = USGSGage('09382000', start_date='1932-10-01',
                    cfs_max=6500, cfs_interval=500,
                    annual_min=0, annual_max=50000, annual_interval=2500, annual_unit='kaf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def little_colorado_cameron(graph=True):
    gage = USGSGage('09402000', start_date='1947-06-1', color='firebrick',
                    cfs_max=19000, cfs_interval=1000,
                    annual_min=0, annual_max=850000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def virgin_at_littlefield(graph=True):
    gage = USGSGage('09415000', start_date='1929-10-01', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_min=0, annual_max=600000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def bill_williams_parker(graph=True):
    gage = USGSGage('09426620', start_date='1988-10-01', color='firebrick',
                    cfs_max=8000, cfs_interval=500,
                    annual_min=0, annual_max=450000, annual_interval=50000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def palo_verde_canal(graph=True):
    gage = USGSGage('09429000', start_date='1950-10-01', color='firebrick',
                    cfs_max=2400, cfs_interval=100,
                    annual_min=650000, annual_max=1050000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def colorado_river_indian_canal_near_parker(graph=True):
    gage = USGSGage('09428500', start_date='1954-10-01', color='firebrick',
                    cfs_max=2000, cfs_interval=100,
                    annual_min=250000, annual_max=750000, annual_interval=50000, annual_unit='kaf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def salt_above_roosevelt(graph=True):
    gage = USGSGage('09498500', start_date='1913-10-01', color='firebrick',
                    cfs_max=95000, cfs_interval=5000,
                    annual_max=2400000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def verde_above_horshoe(graph=True):
    gage = USGSGage('09508500', start_date='1945-08-22', color='firebrick',
                    cfs_max=70000, cfs_interval=5000,
                    annual_max=1300000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def verde_below_bartlett_dam(graph=True):
    gage = USGSGage('09510000', start_date='1904-01-01', color='firebrick',
                    cfs_max=85000, cfs_interval=5000,
                    annual_max=1900000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def verde_near_scottsdale(graph=True):
    gage = USGSGage('09511300', start_date='1961-02-13', color='firebrick',
                    cfs_max=85000, cfs_interval=5000,
                    annual_max=1900000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_river_near_redrock(graph=True):
    gage = USGSGage('09431500', start_date='1930-10-01', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_max=500000, annual_interval=50000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_duncan(graph=True):
    gage = USGSGage('09439000', start_date='2003-09-30', color='firebrick',
                    cfs_max=26000, cfs_interval=1000,
                    annual_min=0, annual_max=350000, annual_interval=25000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_at_head_of_safford_valley(graph=True):
    gage = USGSGage('09448500', start_date='1920-10-01', color='firebrick',
                    cfs_max=50000, cfs_interval=5000,
                    annual_max=1500000, annual_interval=100000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_at_calva(graph=True):
    gage = USGSGage('09466500', start_date='1929-10-01', color='firebrick',
                    cfs_max=50000, cfs_interval=5000,
                    annual_max=1500000, annual_interval=100000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_below_coolidge_dam(graph=True):
    gage = USGSGage('09469500', start_date='1899-07-11', color='firebrick',
                    cfs_max=50000, cfs_interval=5000,
                    annual_max=1500000, annual_interval=100000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_goodyear(graph=True):
    gage = USGSGage('09514100', start_date='1992-10-01', color='firebrick',
                    cfs_max=140000, cfs_interval=10000,
                    annual_min=0, annual_max=1000000, annual_interval=50000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_dome(graph=True):
    gage_full = USGSGage('09520500', start_date='1905-01-01', color='firebrick',
                         cfs_max=96000, cfs_interval=20000,
                         annual_min=0, annual_max=4500000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage_full)

    # gage = USGSGage('09520500', start_date='1996-01-01', color='firebrick',
    #                 cfs_max=1000, cfs_interval=100,
    #                 annual_min=0, annual_max=200000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    # if graph:
    #     WaterGraph(nrows=2).plot_gage(gage)
    return gage_full


def yuma_municipal(graph=True):
    gage = USGSGage('09526000', start_date='1983-10-01', color='firebrick',
                    cfs_max=50, cfs_interval=5,
                    annual_min=0, annual_max=25000, annual_interval=1000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def city_of_yuma_at_avenue_9e_pumping(graph=True):
    gage = USGSGage('09522860', start_date='2015-09-30', color='firebrick',
                    cfs_max=25, cfs_interval=5,
                    annual_min=0, annual_max=10000, annual_interval=1000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yuma_main_canal(graph=True):
    gage = USGSGage('09524000', start_date='1938-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=1000,
                    annual_min=0, annual_max=1500000, annual_interval=500000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def unit_b_canal_near_yuma(graph=True):
    gage = USGSGage('09522900', start_date='2005-09-30', color='firebrick',
                    cfs_max=120, cfs_interval=10,
                    annual_min=0, annual_max=30000, annual_interval=1000, annual_unit='kaf', year_interval=1)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def mcas_diversion_of_b_canal_near_yuma(graph=True):
    gage = USGSGage('09522880', start_date='2005-09-30', color='firebrick',
                    cfs_max=20, cfs_interval=5,
                    annual_min=0, annual_max=3000, annual_interval=500, annual_unit='kaf', year_interval=1)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def wellton_mohawk_main_canal(graph=True):
    gage = USGSGage('09522700', start_date='1974-10-01', color='firebrick',
                    cfs_max=1900, cfs_interval=200,
                    annual_min=0, annual_max=500000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_gravity_main_canal(graph=True):
    gage = USGSGage('09522500', start_date='1943-08-16', color='firebrick',
                    cfs_max=2300, cfs_interval=100,
                    annual_min=0, annual_max=1000000, annual_interval=100000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_gravity_main_canal_at_yuma_mesa_pumping(graph=True):
    gage = USGSGage('09522600', start_date='2005-09-30', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def north_gila_main_canal(graph=True):
    gage = USGSGage('09522600', start_date='1966-10-01', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=45000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def north_gila_main_canal_number_2(graph=True):
    gage = USGSGage('09522650', start_date='1969-07-01', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=65000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def cocopah_from_west_main_canal_near_somerton(graph=True):
    gage = USGSGage('09528200', start_date='2007-01-23', color='firebrick',
                    cfs_max=30, cfs_interval=5,
                    annual_min=0, annual_max=8000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_monster_farms_no_1(graph=True):
    gage = USGSGage('09522660', start_date='2004-10-01', color='firebrick',
                    cfs_max=35, cfs_interval=5,
                    annual_min=0, annual_max=4500, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_monster_farms_no_2(graph=True):
    gage = USGSGage('09522660', start_date='2007-10-01', color='firebrick',
                    cfs_max=35, cfs_interval=5,
                    annual_min=0, annual_max=45000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def south_gila_main_canal(graph=True):
    gage = USGSGage('09522800', start_date='1973-10-01', color='firebrick',
                    cfs_max=170, cfs_interval=10,
                    annual_min=0, annual_max=50000, annual_interval=5000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


# Wasteways and drains
def yuma_main_canal_wasteway(graph=True):
    gage = USGSGage('09525000', start_date='1930-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1100000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def wellton_mohawk_main_outlet_drain(graph=True):
    gage = USGSGage('09529300', start_date='1966-10-01', color='firebrick',
                    cfs_max=350, cfs_interval=50,
                    annual_min=0, annual_max=230000, annual_interval=20000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def levee_canal_wasteway(graph=True):
    gage = USGSGage('09528800', start_date='1966-10-01', color='firebrick',
                    cfs_max=50, cfs_interval=5,
                    annual_min=0, annual_max=6000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gila_drain_no_1(graph=True):
    gage = USGSGage('09529000', start_date='1974-10-01', color='firebrick',
                    cfs_max=25, cfs_interval=5,
                    annual_min=0, annual_max=9000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def north_gila_main_canal_wasteway(graph=True):
    gage = USGSGage('09529150', start_date='1966-10-01', color='firebrick',
                    cfs_max=50, cfs_interval=5,
                    annual_min=0, annual_max=6000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def bruce_church_wasteway(graph=True):
    gage = USGSGage('09529250', start_date='1966-10-01', color='firebrick',
                    cfs_max=30, cfs_interval=5,
                    annual_min=0, annual_max=5000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def south_gila_terminal_canal_wasteway(graph=True):
    gage = USGSGage('09529420', start_date='1966-10-01', color='firebrick',
                    cfs_max=25, cfs_interval=5,
                    annual_min=0, annual_max=6000, annual_interval=500, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def test():
    test_gila()
    test_middle_colorado()
    test_lower_colorado()
    test_returns()


def test_middle_colorado():
    lees_ferry()
    paria_lees_ferry()
    little_colorado_cameron()
    virgin_at_littlefield()

    bill_williams_parker()
    palo_verde_canal()
    colorado_river_indian_canal_near_parker()


def test_gila():
    salt_above_roosevelt()
    verde_above_horshoe()
    verde_below_bartlett_dam()
    verde_near_scottsdale()
    gila_river_near_redrock()
    gila_duncan()
    gila_at_head_of_safford_valley()
    gila_at_calva()
    gila_below_coolidge_dam()
    gila_goodyear()
    gila_dome()


def test_lower_colorado():
    cocopah_from_west_main_canal_near_somerton()
    gila_monster_farms_no_1()
    gila_monster_farms_no_2()

    yuma_municipal()
    city_of_yuma_at_avenue_9e_pumping()
    yuma_main_canal()
    unit_b_canal_near_yuma()
    mcas_diversion_of_b_canal_near_yuma()
    wellton_mohawk_main_canal()

    gila_gravity_main_canal()
    north_gila_main_canal_number_2()
    gila_gravity_main_canal_at_yuma_mesa_pumping()
    north_gila_main_canal()
    south_gila_main_canal()


def test_returns():
    # Wasteways and drains
    yuma_main_canal_wasteway()
    wellton_mohawk_main_outlet_drain()
    levee_canal_wasteway()
    gila_drain_no_1()
    north_gila_main_canal_wasteway()
    bruce_church_wasteway()
    south_gila_terminal_canal_wasteway()
