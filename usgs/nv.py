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


def las_vegas_wash_below_lake_las_vegas(graph=True):
    gage = USGSGage('09419800', start_date='1969-08-01', color='firebrick',
                    cfs_max=2000, cfs_interval=100,
                    annual_min=0, annual_max=300000, annual_interval=10000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage


def muddy_near_glendale(graph=True):
    gage = USGSGage('09419000', start_date='1950-02-01', color='firebrick',
                    cfs_max=5500, cfs_interval=500,
                    annual_min=0, annual_max=54000, annual_interval=2000, annual_unit='kaf', year_interval=4)
    if graph:
        WaterGraph(nrows=2).plot_gage(gage)
    return gage
