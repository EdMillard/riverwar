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

# Some history on Lower Colorado flows and gages
# https://www.researchgate.net/publication/308133114_Geomorphic_change_and_sediment_transport_during_a_small_artificial_flood_in_a_transformed_post-dam_delta_The_Colorado_River_delta_United_States_and_Mexico


def test():
    # above_little_colorado()
    # above_national_canyon_near_supai()
    near_grand_canyon()
    above_diamond_creek_near_peach_springs()
    below_hoover()
    below_davis()
    below_parker()
    below_palo_verde()
    below_imperial()
    below_laguna()
    below_yuma_wasteway()
    northern_international_border()


def above_little_colorado(graph=True):
    # Ends 2002
    gage = USGSGage('09383100', start_date='1985-09-28', color='firebrick',
                    cfs_max=55000, cfs_interval=5000,
                    annual_min=6000000, annual_max=15000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def above_national_canyon_near_supai(graph=True):
    # Ends 1993
    gage = USGSGage('09404120', start_date='1983-07-31', color='firebrick',
                    cfs_max=55000, cfs_interval=5000,
                    annual_min=6000000, annual_max=15000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_hoover(graph=True):
    gage = USGSGage('09421500', start_date='1934-04-01', color='firebrick',
                    cfs_max=120000, cfs_interval=5000,
                    annual_min=6000000, annual_max=23000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_davis(graph=True):
    # Three years, 1905-1907 pre dam; then 1949-present when dam was built
    gage = USGSGage('09423000', start_date='1905-05-11', color='firebrick',
                    cfs_max=120000, cfs_interval=5000,
                    annual_min=6000000, annual_max=23000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_parker(graph=True):
    gage = USGSGage('09427520', start_date='1934-11-16', color='firebrick',
                    cfs_max=41000, cfs_interval=5000,
                    annual_min=4000000, annual_max=22000000, annual_interval=1000000, annual_unit='maf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_palo_verde(graph=True):
    gage = USGSGage('09429100', start_date='1956-03-24', color='firebrick',
                    cfs_max=17000, cfs_interval=1000,
                    annual_min=0, annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def northern_international_border(graph=True):
    gage = USGSGage('09522000', start_date='1950-01-01', color='firebrick',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=4000000, annual_interval=200000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_imperial(graph=True):
    gage = USGSGage('09429500', start_date='2018-11-29', color='firebrick',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=500000, annual_interval=20000, annual_unit='kaf', year_interval=1)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def southern_international_border(graph=True):
    gage = USGSGage('09522200', start_date='1960-10-01', color='firebrick',  # end_date='1986-09-29'
                    cfs_max=40000, cfs_interval=50000,
                    annual_min=0, annual_max=14000000, annual_interval=1000000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def yuma(graph=True):
    # Bogus gage
    gage = USGSGage('09521000', start_date='1904-01-01', color='firebrick',  # end_date='1983-11-01'
                    cfs_max=250000, cfs_interval=10000,
                    annual_min=0, annual_max=27000000, annual_interval=1000000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_laguna(graph=True):
    gage = USGSGage('09429600', start_date='1971-12-16', color='firebrick',
                    cfs_max=32000, cfs_interval=2000,
                    annual_min=0, annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def below_yuma_wasteway(graph=True):
    gage = USGSGage('09521100', start_date='1963-10-01', color='firebrick',
                    cfs_max=2100, cfs_interval=100,
                    annual_min=0, annual_max=1500000, annual_interval=100000, annual_unit='maf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage
