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
import usbr
from source import usbr_report
from graph.water import WaterGraph
from usbr import util
from util import add_annual, subtract_annual, reshape_annual_range

current_last_year = 2021


def test():
    total()
    central_arizona_project()
    colorado_river_indian_tribes()

    yuma_mesa()
    yuma_county_water_users_association()
    north_gila_valley()
    unit_b()
    yuma_irrigation()
    wellton_mohawk()


def total():
    util.diversion_vs_consumptive('az', 'total', 'Arizona',
                                  ymin1=900000, ymax1=3800000,
                                  ymin2=550000, ymax2=900000, yinterval2=25000)


def yuma_area_returns():
    # unit_b()
    # yuma_irrigation()

    data = []
    yuma_mesa_diversion_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_diversion.csv')
    yuma_mesa_cu_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    yuma_mesa_returns_annual_af = subtract_annual(yuma_mesa_diversion_annual_af, yuma_mesa_cu_annual_af)
    data.append({'data': yuma_mesa_returns_annual_af, 'label': 'Yuma Mesa Returns', 'color': 'maroon'})

    yuma_county_diversion_annual_af = usbr_report.annual_af('az/usbr_az_yuma_county_wua_diversion.csv')
    yuma_county_cu_annual_af = usbr_report.annual_af('az/usbr_az_yuma_county_wua_consumptive_use.csv')
    yuma_county_returns_annual_af = subtract_annual(yuma_county_diversion_annual_af, yuma_county_cu_annual_af)
    data.append({'data': yuma_county_returns_annual_af, 'label': 'Yuma County WUA Returns', 'color': 'firebrick'})

    north_gila_diversion_annual_af = usbr_report.annual_af('az/usbr_az_north_gila_irrigation_diversion.csv')
    north_gila_cu_annual_af = usbr_report.annual_af('az/usbr_az_north_gila_irrigation_consumptive_use.csv')
    north_gila_returns_annual_af = subtract_annual(north_gila_diversion_annual_af, north_gila_cu_annual_af)
    data.append({'data': north_gila_returns_annual_af, 'label': 'North Gila Returns', 'color': 'lightcoral'})

    yuma_irrigation_diversion_annual_af = usbr_report.annual_af('az/usbr_az_yuma_irrigation_diversion.csv')
    yuma_irrigation_cu_annual_af = usbr_report.annual_af('az/usbr_az_yuma_irrigation_consumptive_use.csv')
    yuma_irrigation_returns_annual_af = subtract_annual(yuma_irrigation_diversion_annual_af,
                                                        yuma_irrigation_cu_annual_af)
    data.append({'data': yuma_irrigation_returns_annual_af, 'label': 'Yuma IrrigationReturns', 'color': 'royalblue'})
    return data


def yuma_area_diversion():
    data = []
    yuma_mesa_diversion_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_diversion.csv')
    data.append({'data': yuma_mesa_diversion_annual_af, 'label': 'Yuma Mesa Diversion', 'color': 'darkmagenta'})
    return data


def yuma_area_cu():
    data = []
    yuma_mesa_cu_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    data.append({'data': yuma_mesa_cu_annual_af, 'label': 'Yuma Mesa Diversion', 'color': 'firebrick'})
    return data


def central_arizona_project():
    year_interval = 3

    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_central_arizona_project_diversion.csv')
    graph = WaterGraph(nrows=3)
    graph.plot(monthly_af, sub_plot=0, title='Lake Havasu CAP Wilmer Pumping Plant (Monthly)',
               xinterval=year_interval, ymax=200000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Lake Havasu CAP Wilmer Pumping Plant (Annual)',
               xinterval=year_interval, ymin=0, ymax=1800000, yinterval=100000,
               xlabel='Calendar Year',   color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    ics = usbr.lc.lake_mead_load_ics()
    ics_az_delta = ics['AZ Delta']
    ics_az_delta = graph.reshape_annual_range(ics_az_delta, 1985, current_last_year)

    bar_data = [{'data': annual_af, 'label': 'CAP Wilmer Pumps', 'color': 'firebrick'},
                {'data': ics_az_delta, 'label': 'AZ ICS Deposits', 'color': 'mediumseagreen'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Lake Havasu CAP Wilmer Pumping Plant + AZ ICS Deposits',
                       ylabel='maf', ymin=0, ymax=1800000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=3, format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def colorado_river_indian_tribes():
    year_interval = 3

    # Diversion
    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_crit_diversion.csv')
    graph = WaterGraph(nrows=4)
    graph.plot(monthly_af, sub_plot=0, title='Colorado River Indian Tribe Diversion (Monthly)',
               xinterval=year_interval, ymax=100000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=1, title='Colorado River Indian Tribe Diversion (Annual)',
               ymin=0, ymax=1200000, yinterval=80000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    # Consumptive Use
    monthly_af = usbr_report.load_monthly_csv('az/usbr_az_crit_consumptive_use.csv')
    graph.plot(monthly_af, sub_plot=2, title='Colorado River Indian Tribe Consumptive Use (Monthly)',
               xinterval=year_interval, ymin=-15000, ymax=90000, yinterval=10000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_af = usbr_report.monthly_to_water_year(monthly_af, water_year_month=1)
    graph.bars(annual_af, sub_plot=3, title='Colorado River Indian Tribe Consumptive Use (Annual)',
               ymin=0, ymax=550000, yinterval=50000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.fig.waitforbuttonpress()


def yuma_mesa():
    start_year = 1964
    year_interval = 3
    # Yuma Mesa Irrigation
    # This is complicated, early years had a drain with return flows
    # migrated to returns, then measured and unmeasured returns later
    yuma_mesa_diversion_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_diversion.csv')
    yuma_mesa_cu_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_consumptive_use.csv')
    yuma_mesa_drain_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_outlet_drain_returns.csv')

    drain_start_year = yuma_mesa_drain_annual_af['dt'][0]
    drain_end_year = yuma_mesa_drain_annual_af['dt'][-1]
    yuma_mesa_diversion_tmp = reshape_annual_range(yuma_mesa_diversion_annual_af, drain_start_year, drain_end_year)

    yuma_mesa_drain_cu_annual_af = subtract_annual(yuma_mesa_diversion_tmp, yuma_mesa_drain_annual_af)
    yuma_mesa_drain_cu_annual_af = reshape_annual_range(yuma_mesa_drain_cu_annual_af, start_year, current_last_year)

    yuma_mesa_cu_annual_af = reshape_annual_range(yuma_mesa_cu_annual_af, start_year, current_last_year)
    yuma_mesa_cu_annual_af = add_annual(yuma_mesa_cu_annual_af, yuma_mesa_drain_cu_annual_af)

    # yuma_mesa_returns_annual_af = usbr_report.annual_af('az/usbr_az_yuma_mesa_irrigation_returns.csv')
    # yuma_mesa_measured_returns_annual_af = usbr_report.annual_af(
    #     'az/usbr_az_yuma_mesa_irrigation_measured_returns.csv')
    # yuma_mesa_annual_unmeasured_returns_af = usbr_report.annual_af(
    #     'az/usbr_az_yuma_mesa_irrigation_unmeasured_returns.csv')

    graph = WaterGraph(nrows=2)
    bar_data = [
        {'data': yuma_mesa_drain_annual_af, 'label': 'Diversion minus Drain Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Yuma Mesa Drain Returns (Annual)',
                       ymin=0, ymax=300000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_mesa_diversion_annual_af, 10, sub_plot=1)
    bar_data = [
        {'data': yuma_mesa_diversion_annual_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': yuma_mesa_cu_annual_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Yuma Mesa Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=300000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_mesa_diversion_annual_af, 10, sub_plot=1)
    graph.running_average(yuma_mesa_cu_annual_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def yuma_county_water_users_association():
    year_interval = 2

    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_county_wua_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_county_wua_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    graph = WaterGraph(nrows=2)
    graph.plot(monthly_diversion_af, sub_plot=0, title='Yuma County WUA Diversion (Monthly)',
               xinterval=year_interval, ymax=55000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=55000, yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Yuma County WUA Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=400000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def north_gila_valley():
    year_interval = 2

    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_north_gila_irrigation_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af)
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_north_gila_irrigation_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    graph = WaterGraph(nrows=2)
    graph.plot(monthly_diversion_af, sub_plot=0, title='North Gila (Monthly)',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='North Gila Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=75000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def yuma_irrigation():
    year_interval = 2

    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_irrigation_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af)
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_yuma_irrigation_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    graph = WaterGraph(nrows=2)
    graph.plot(monthly_diversion_af, sub_plot=0, title='Yuma Irrigation (Monthly)',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Yuma Irrigation Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=75000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def unit_b():
    year_interval = 2

    monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_unit_b_irrigation_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af)
    monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_unit_b_irrigation_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    graph = WaterGraph(nrows=2)
    graph.plot(monthly_diversion_af, sub_plot=0, title='Unit B (Monthly)',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=10000, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1,
                       title='Unit B Diversions and Consumptive Use (Annual)',
                       ymin=0, ymax=75000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()


def wellton_mohawk():
    year_interval = 3

    graph = WaterGraph(nrows=2)

    wellton_mohawk_monthly_diversion_af = usbr_report.load_monthly_csv('az/usbr_az_wellton_mohawk_diversion.csv')
    wellton_mohawk_annual_diversion_af = usbr_report.monthly_to_water_year(wellton_mohawk_monthly_diversion_af,
                                                                           water_year_month=1)
    wellton_mohawk_monthly_cu_af = usbr_report.load_monthly_csv('az/usbr_az_wellton_mohawk_consumptive_use.csv')
    wellton_mohawk_annual_cu_af = usbr_report.monthly_to_water_year(wellton_mohawk_monthly_cu_af,
                                                                    water_year_month=1)

    graph.plot(wellton_mohawk_monthly_diversion_af, sub_plot=0, title='Wellton-Mohawk Diversion (Monthly)',
               xinterval=year_interval, ymax=75000, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(wellton_mohawk_monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, ymax=75000, yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
        {'data': wellton_mohawk_annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
        {'data': wellton_mohawk_annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Wellton-Mohawk Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(wellton_mohawk_annual_diversion_af, 10, sub_plot=1)
    graph.running_average(wellton_mohawk_annual_cu_af, 10, sub_plot=1)

    graph.fig.waitforbuttonpress()
