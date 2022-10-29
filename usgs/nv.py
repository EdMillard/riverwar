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


def test():
    muddy_near_glendale()
    las_vegas_wash_below_lake_las_vegas()


def muddy_near_glendale(graph=True):
    gage = USGSGage('09419000', start_date='1921-10-01',
                    cfs_max=5500, cfs_interval=1000,
                    annual_min=0, annual_max=55000, annual_interval=5000, annual_unit='kaf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def virgin_abv_lake_mead_nr_overton(graph=True):
    gage = USGSGage('09415250', start_date='2006-04-21',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=250000, annual_interval=10000, annual_unit='kaf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def las_vegas_wash_below_lake_las_vegas(graph=True):
    gage = USGSGage('09419800', start_date='1969-08-01',
                    cfs_max=3000, cfs_interval=500,
                    annual_min=0, annual_max=250000, annual_interval=10000, annual_unit='kaf',
                    year_interval=5)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage

