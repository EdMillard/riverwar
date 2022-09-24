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


def yampa_river_near_maybell(graph=True):
    gage = USGSGage('09251000', start_date='1916-05-01',
                    cfs_max=25000, cfs_interval=5000,
                    annual_min=0, annual_max=2300000, annual_interval=100000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def gunnison_grand_junction(graph=True):
    gage = USGSGage('09152500', start_date='1896-10-01',
                    cfs_max=36000, cfs_interval=2000,
                    annual_max=3800000, annual_interval=200000, annual_unit='maf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def dolores_below_rico(graph=True):
    gage = USGSGage('09165000', start_date='1951-10-01',
                    cfs_max=1900, cfs_interval=100,
                    annual_max=170000, annual_interval=10000, annual_unit='kaf', year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def dolores_at_dolores(graph=True):
    gage = USGSGage('09166500', start_date='1895-10-01',
                    cfs_max=7000, cfs_interval=500,
                    annual_max=575000, annual_interval=25000, annual_unit='kaf', year_interval=6)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def dolores_at_cisco(graph=True):
    gage = USGSGage('09180000', start_date='1950-12-01',
                    cfs_max=17000, cfs_interval=1000,
                    annual_max=1500000, annual_interval=50000, annual_unit='kaf')
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def mud_creek_cortez(graph=True):
    gage = USGSGage('09371492', start_date='1981-10-01',
                    cfs_max=240, cfs_interval=10,
                    annual_max=7500, annual_interval=500, annual_unit='af', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def mcelmo_stateline(graph=True):
    gage = USGSGage('09372000', start_date='1951-03-01',
                    cfs_max=1300, cfs_interval=50,
                    annual_max=70000, annual_interval=5000, annual_unit='af', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def mcelmo_trail_canyon(graph=True):
    gage = USGSGage('09371520', start_date='1993-08-01',
                    cfs_max=1250, cfs_interval=50,
                    annual_max=60000, annual_interval=5000, annual_unit='af', year_interval=3)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage
