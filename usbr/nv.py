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
from source import usbr_report
from graph.water import WaterGraph
from usbr import util


def test():
    total()
    southern_nevada_water_authority()


def total():
    util.diversion_vs_consumptive('nv', 'total', 'Nevada',
                                  ymin1=0, ymax1=550000,
                                  ymin2=0, ymax2=250000, yinterval2=10000)


def southern_nevada_water_authority():
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
