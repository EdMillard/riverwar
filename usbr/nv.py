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
from util import add_annuals, subtract_annual, reshape_annual_range, reshape_annual_range_to
from usbr import util

current_last_year = 2021


def test():
    data = [
        {'data': state_total_diversion(), 'y_min': 0, 'y_max': 550000, 'y_interval': 50000},
        {'data': user_total_diversion()},
        {'y_min': -5000, 'y_max': 40000, 'y_interval': 5000},
        {'data': state_total_cu(), 'y_min': 0, 'y_max': 350000, 'y_interval': 50000},
        {'data': user_total_cu()},
        {'y_min': -5000, 'y_max': 35000, 'y_interval': 5000},
    ]
    util.state_total_vs_user_total_graph('NV', data, y_formatter='kaf')
    total()
    southern_nevada_water_authority()


def state_total_diversion():
    return usbr_report.annual_af('nv/usbr_nv_total_diversion.csv')


def state_total_cu():
    return usbr_report.annual_af('nv/usbr_nv_total_consumptive_use.csv')


def user_total_diversion():
    data = [
        basic_diversion(),
        city_of_henderson_diversion(),
        las_vegas_valley_diversion(),
        snwa_griffith_diversion()
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


def user_total_cu():
    data = [
        basic_cu(),
        city_of_henderson_cu(),
        las_vegas_valley_cu(),
        snwa_griffith_cu()
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


def user_total_returns():
    data = [
        basic_returns(),
        city_of_henderson_returns(),
        las_vegas_valley_returns(),
        snwa_griffith_returns()
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


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

    monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_las_vegas_wash_returns.csv')
    graph.plot(monthly_af, sub_plot=2, title='Lake Mead Las Vegas Wash Return Flows (Monthly)',
               xinterval=year_interval, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Lake Mead Las Vegas Wash Return Flows (Annual)',
               ymin=0, ymax=250000, yinterval=50000,
               xlabel='Calendar Year',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.date_and_wait()


def snwa_griffith_diversion():
    return usbr_report.annual_af('nv/usbr_nv_snwa_griffith_diversion.csv')


def snwa_griffith_cu():
    return subtract_annual(snwa_griffith_diversion(), snwa_griffith_returns())


def snwa_griffith_returns():
    las_vegas_wash_returns = usbr_report.annual_af('nv/usbr_nv_las_vegas_wash_returns.csv')
    return reshape_annual_range_to(las_vegas_wash_returns, snwa_griffith_diversion())


def las_vegas_valley_diversion():
    return usbr_report.annual_af('nv/usbr_nv_las_vegas_valley_diversion.csv')


def las_vegas_valley_cu():
    return subtract_annual(las_vegas_valley_diversion(), las_vegas_valley_returns())


def las_vegas_valley_returns():
    las_vegas_wash_returns = usbr_report.annual_af('nv/usbr_nv_las_vegas_wash_returns.csv')
    return reshape_annual_range_to(las_vegas_wash_returns, las_vegas_valley_diversion())


def city_of_henderson_diversion():
    return usbr_report.annual_af('nv/usbr_nv_city_of_henderson_diversion.csv')


def city_of_henderson_cu():
    return city_of_henderson_diversion()


def city_of_henderson_returns():
    return subtract_annual(city_of_henderson_diversion(), city_of_henderson_cu())


def basic_diversion():
    return usbr_report.annual_af('nv/usbr_nv_basic_diversion.csv')


def basic_cu():
    return basic_diversion()


def basic_returns():
    return subtract_annual(basic_diversion(), basic_cu())
