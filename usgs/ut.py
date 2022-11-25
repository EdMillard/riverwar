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
from os import chdir
from source.usgs_gage import USGSGage
from graph.water import WaterGraph


def test():
    san_juan_bluff()
    green_river_at_green_river()
    colorado_cisco()
    colorado_potash()
    dirty_devil()
    escalante()
    virgin_river_at_virgin()
    virgin_river_near_st_george()


def san_juan_bluff(graph=True):
    gage = USGSGage('09379500', start_date='1941-10-01',
                    cfs_max=36000, cfs_interval=2000,
                    annual_min=400000, annual_max=3300000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def green_river_at_green_river(graph=True):
    gage = USGSGage('09315000', start_date='1894-10-01',
                    cfs_max=70000, cfs_interval=5000,
                    annual_min=1000000, annual_max=9000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def colorado_cisco(graph=True):
    gage = USGSGage('09180500', start_date='1913-10-01',
                    cfs_max=75000, cfs_interval=2500,
                    annual_max=11000000, annual_interval=500000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def colorado_potash(graph=True):
    gage = USGSGage('09185600', start_date='2014-10-29',
                    cfs_max=37500, cfs_interval=2500,
                    annual_max=6000000, annual_interval=250000, annual_unit='maf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def dirty_devil(graph=True):
    gage = USGSGage('09333500', start_date='1948-06-07',
                    cfs_max=28000, cfs_interval=1000,
                    annual_max=190000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def escalante(graph=True):
    gage = USGSGage('09337500', start_date='1911-01-01',
                    cfs_max=1000, cfs_interval=100,
                    annual_max=30000, annual_interval=2000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def virgin_river_at_virgin(graph=True):
    gage = USGSGage('09406000', start_date='1950-10-01',
                    cfs_max=10000, cfs_interval=1000,
                    annual_max=400000, annual_interval=20000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def virgin_river_near_st_george(graph=True):
    gage = USGSGage('09413500', start_date='1909-05-01',
                    cfs_max=19000, cfs_interval=1000,
                    annual_max=550000, annual_interval=50000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


if __name__ == '__main__':
    chdir('../')
    test()
