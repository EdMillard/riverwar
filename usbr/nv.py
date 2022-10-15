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
        {'y_min': -500, 'y_max': 4500, 'y_interval': 500},
        {'data': state_total_cu(), 'y_min': 0, 'y_max': 350000, 'y_interval': 50000},
        {'data': user_total_cu()},
        {'y_min': -1000, 'y_max': 9000, 'y_interval': 1000},
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
        boulder_city_diversion(),
        snwa_griffith_diversion(),
        basic_diversion(),
        city_of_henderson_diversion(),
        nevada_dept_of_wildlife_diversion(),
        las_vegas_valley_diversion(),
        north_las_vegas_diversion(),
        socal_edison_diversion(),
        big_bend_diversion(),
        fort_mojave_indian_diversion()
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


def user_total_cu():
    data = [
        boulder_city_cu(),
        snwa_griffith_cu(),
        basic_cu(),
        city_of_henderson_cu(),
        nevada_dept_of_wildlife_cu(),
        las_vegas_valley_cu(),
        north_las_vegas_cu(),
        socal_edison_cu(),
        big_bend_cu(),
        fort_mojave_indian_cu()
    ]
    data[0] = reshape_annual_range(data[0], 1964, current_last_year)
    return add_annuals(data)


def user_total_returns():
    data = [
        boulder_city_returns(),
        snwa_griffith_returns(),
        basic_returns(),
        city_of_henderson_returns(),
        nevada_dept_of_wildlife_returns(),
        las_vegas_valley_returns(),
        north_las_vegas_returns(),
        socal_edison_returns(),
        big_bend_returns(),
        fort_mojave_indian_returns()
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


def boulder_city_diversion():
    return usbr_report.annual_af('nv/usbr_nv_boulder_city_diversion.csv')


def boulder_city_cu():
    # No returns for now, probably mixed into Las Vegas Wash
    return subtract_annual(boulder_city_diversion(), boulder_city_returns())


def boulder_city_returns():
    # No returns for now, probably mixed into Las Vegas Wash
    return subtract_annual(boulder_city_diversion(), boulder_city_diversion())


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


def big_bend_diversion():
    return usbr_report.annual_af('nv/usbr_nv_big_bend_diversion.csv')


def big_bend_cu():
    return usbr_report.annual_af('nv/usbr_nv_big_bend_consumptive_use.csv')


def big_bend_returns():
    return subtract_annual(big_bend_diversion(), big_bend_cu())


def socal_edison_diversion():
    return usbr_report.annual_af('nv/usbr_nv_socal_edison_diversion.csv')


def socal_edison_cu():
    return socal_edison_diversion()


def socal_edison_returns():
    return subtract_annual(socal_edison_diversion(), socal_edison_cu())


def north_las_vegas_diversion():
    return usbr_report.annual_af('nv/usbr_nv_north_las_vegas_diversion.csv')


def north_las_vegas_cu():
    # FIXME, are returns in Las Vegas Wash or is this all consumptive use
    return north_las_vegas_diversion()


def north_las_vegas_returns():
    return subtract_annual(north_las_vegas_diversion(), north_las_vegas_cu())


def fort_mojave_indian_diversion():
    return usbr_report.annual_af('nv/usbr_nv_fort_mojave_indian_diversion.csv')


def fort_mojave_indian_cu():
    return usbr_report.annual_af('nv/usbr_nv_fort_mojave_indian_consumptive_use.csv')


def fort_mojave_indian_returns():
    return subtract_annual(fort_mojave_indian_diversion(), fort_mojave_indian_cu())


def nevada_dept_of_wildlife_diversion():
    return usbr_report.annual_af('nv/usbr_nv_nevada_dept_of_wildlife_diversion.csv')


def nevada_dept_of_wildlife_cu():
    return usbr_report.annual_af('nv/usbr_nv_nevada_dept_of_wildlife_consumptive_use.csv')


def nevada_dept_of_wildlife_returns():
    return subtract_annual(nevada_dept_of_wildlife_diversion(), nevada_dept_of_wildlife_cu())
