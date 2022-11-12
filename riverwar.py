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
import datetime
import numpy as np
import signal
import sys
from rw.util import add_annual, add_annuals, subtract_annual, multiply_annual, reshape_annual_range, flow_for_year
from graph.water import WaterGraph
import usgs
from usgs import lc
from usgs import az, ca, ut, nv   # nm, wy
import usbr
from usbr import az, ca, uc, nv, mx
from source.usgs_gage import USGSGage
from source import usbr_report
from source import usbr_rise

interrupted = False

current_last_year = 2021

# FIXME Revision 1967_0, 1967_1, 1968_0, 1968_1, 1970_0, 1971_0, 1973_1
# Fixed 1969_0, 1969_1, 1970_1, 1971_1, 1972_1,1980_1, 1984_1

# matplotlib colors
# https://i.stack.imgur.com/lFZum.png
#
# USBR  24 month reports
#   https://www.usbr.gov/lc/region/g4000/24mo/index.html
# Yuma area info
#   https://www.usbr.gov/lc/yuma/
#   https://www.usbr.gov/lc/yuma/programs/YAWMS/GROUNDWATER_maps.cfm
#   https://www.usbr.gov/lc/yuma/environmental_docs/environ_docs.html
#   estinates of evaporation on lower colorado
#   https://eros.usgs.gov/doi-remote-sensing-activities/2020/bor/estimates-evapotranspiration-and-evaporation-along-lower-colorado-river
#   https://usbr.gov/lc/region/g4000/4200Rpts/LCRASRpt/2009/report09.pdf
#   https://www.usbr.gov/lc/region/g4000/contracts/entitlements.html


def usbr_glen_canyon_annual_release_af(graph=False, start_year=None, end_year=None):
    usbr_lake_powell_release_total_af = 4354
    info, daily_usbr_glen_canyon_daily_release_af = usbr_rise.load(usbr_lake_powell_release_total_af)
    annual_af = WaterGraph.daily_to_water_year(daily_usbr_glen_canyon_daily_release_af)
    if start_year and end_year:
        annual_af = reshape_annual_range(annual_af, start_year, end_year)
    if graph:
        graph = WaterGraph(nrows=1)
        graph.bars(annual_af, sub_plot=0, title='Glen Canyon Release (Annual)', color='firebrick',
                   ymin=4000000, ymax=21000000, yinterval=1000000,
                   xlabel='Water Year', xinterval=4,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.date_and_wait()
    return annual_af


def model_glen_canyon(show_graph=False):
    lees_ferry_gage = usgs.az.lees_ferry(graph=True)

    # USGS Lees Ferry Gage Daily Discharge Mean
    #
    usgs_lees_ferry_annual_af = lees_ferry_gage.annual_af(water_year_month=10)
    # usgs_lees_ferry_running_average = rw_running_average(usgs_lees_ferry_annual_af, 10)
    # x = usgs_lees_ferry_running_average['dt']
    # y = usgs_lees_ferry_running_average['val']
    # plot_bars.plot(x, y, linestyle='-', linewidth=3, marker='None', color='goldenrod', label='10Y Running Average')
    # plot_bars.legend()
    # plot_bars.show()
    # plot_bars.waitforbuttonpress()

    usgs_lees_ferry_af_1999_2021 = WaterGraph.array_in_time_range(usgs_lees_ferry_annual_af,
                                                                  datetime.datetime(1999, 1, 1),
                                                                  datetime.datetime(current_last_year, 12, 31))
    # rw_bars(annual_discharge_af, title=name, color='royalblue',
    #        ylabel='maf', ymin=2000000, ymax=21000000, yinterval=500000, format_func=format_maf,
    #        xlabel='Water Year', xinterval=5)
    glen_canyon_annual_release_af = usbr_glen_canyon_annual_release_af()

    # rw_bars(a, title='Lake Powell Release',
    #        ylabel='maf', ymin=7000000, ymax=20750000, yinterval=500000,
    #        xlabel='Water Year', xinterval=3, format_func=format_maf)
    if show_graph:
        graph = WaterGraph()
        graph.plot_gage(lees_ferry_gage)

        graph = WaterGraph()
        graph.bars_two(glen_canyon_annual_release_af, usgs_lees_ferry_annual_af,
                       title='Lake Powell Release Comparison, USBR Glen Canyon vs USGS Lees Ferry',
                       label_a='Glen Canyon', color_a='royalblue',
                       label_b='Lees Ferry', color_b='limegreen',
                       ylabel='af', ymin=7000000, ymax=13000000, yinterval=250000,
                       xlabel='Water Year', xinterval=3, format_func=WaterGraph.format_maf)
        graph.running_average(glen_canyon_annual_release_af, 10, sub_plot=0)
        graph.running_average(usgs_lees_ferry_annual_af, 10, sub_plot=0)

    usbr_lake_powell_release_af_1999_2021 = WaterGraph.array_in_time_range(glen_canyon_annual_release_af,
                                                                           datetime.datetime(1999, 1, 1),
                                                                           datetime.datetime(current_last_year, 12, 31))

    # USGS Paria At Lees Ferry Gage Daily Discharge Mean
    #
    usgs_paria_annual_af = usgs.az.paria_lees_ferry().annual_af()
    usgs_paria_annual_af_1999_2021 = WaterGraph.array_in_time_range(usgs_paria_annual_af,
                                                                    datetime.datetime(1999, 1, 1),
                                                                    datetime.datetime(current_last_year, 12, 31))

    usbr_glen_canyon_vector = usbr_lake_powell_release_af_1999_2021['val']
    usgs_paria_vector = usgs_paria_annual_af_1999_2021['val']
    usgs_glen_canyon_plus_paria = usbr_glen_canyon_vector + usgs_paria_vector

    glen_canyon_plus_paria = np.empty(2021-1999+1, [('dt', 'i'), ('val', 'f')])
    glen_canyon_plus_paria['dt'] = usbr_lake_powell_release_af_1999_2021['dt']
    glen_canyon_plus_paria['val'] = usgs_glen_canyon_plus_paria

    usgs_lees_ferry_vector = usgs_lees_ferry_af_1999_2021['val']

    print('USBR Glen Canyon:\n', usbr_glen_canyon_vector)
    print('USGS Lees Ferry:\n', usgs_lees_ferry_vector)
    difference = usgs_lees_ferry_vector - usgs_glen_canyon_plus_paria
    difference_sum = difference.sum()
    difference_average = difference_sum / len(difference)
    print('Total discrepancy 1999-2021   = ', int(difference_sum))
    print('Average discrepancy 1999-2021 = ', int(difference_average))
    print('Difference vector:\n', difference)

    discrepancy = np.empty(len(usgs_lees_ferry_af_1999_2021['dt']), [('dt', 'i'), ('val', 'f')])
    discrepancy['dt'] = usgs_lees_ferry_af_1999_2021['dt']
    discrepancy['val'] = difference

    if show_graph:
        graph = WaterGraph()
        graph.bars_two(glen_canyon_plus_paria, usgs_lees_ferry_af_1999_2021,
                       title='Lake Powell Release Comparison, USBR Glen Canyon + Paria vs USGS Lees Ferry',
                       label_a='Glen Canyon + Paria', color_a='royalblue',
                       label_b='Lees Ferry', color_b='limegreen',
                       ylabel='maf', ymin=7000000, ymax=13000000, yinterval=250000,
                       xlabel='Water Year', xinterval=3, format_func=WaterGraph.format_maf)
        graph.running_average(glen_canyon_plus_paria, 10, sub_plot=0)
        graph.running_average(usgs_lees_ferry_af_1999_2021, 10, sub_plot=0)
        graph.date_and_wait()

        graph = WaterGraph()
        graph.bars(discrepancy,
                   title='Lake Powell Release Difference USBR Glen Canyon + paria vs USGS Lees Ferry',
                   ylabel='kaf', ymin=0, ymax=300000, yinterval=50000,
                   xlabel='Water Year', xinterval=2, format_func=WaterGraph.format_kaf)
        graph.date_and_wait()


def model_imperial_to_mexico():
    year_interval = 4
    # All American Canal Above Imperial Dam
    graph = WaterGraph(nrows=3)

    all_american_annual_gage = usgs.ca.all_american_canal(graph=False)
    all_american = all_american_annual_gage.annual_af(start_year=1964, end_year=current_last_year, water_year_month=1)
    graph.bars(all_american, sub_plot=0, title='USGS All American Canal Diversion',
               xinterval=year_interval, ymin=3000000, ymax=6500000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    # Gila Gravity Main Canal
    gila_gravity_gage = usgs.az.gila_gravity_main_canal(graph=False)
    gila_gravity = gila_gravity_gage.annual_af(start_year=1964, end_year=current_last_year, water_year_month=1)
    graph.bars(gila_gravity, sub_plot=1, title='USGS Gila Gravity Main Canal Diversion',
               xinterval=year_interval, ymin=0, ymax=1000000, yinterval=100000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    # Imperial Dam Release
    imperial_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv')
    imperial_dam_release_annual_af = reshape_annual_range(imperial_dam_release_annual_af, 1964, current_last_year)
    graph.bars(imperial_dam_release_annual_af, sub_plot=2, title='Imperial Dam Release',
               xinterval=year_interval, ymax=500000, yinterval=50000,
               color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    graph.date_and_wait()

    graph = WaterGraph(nrows=4)
    below_yuma_wasteway_annual = usgs.lc.below_yuma_wasteway(graph=False).annual_af()
    graph.bars(below_yuma_wasteway_annual, sub_plot=0, title='Colorado River Below Yuma Wasteway',
               xinterval=year_interval, ymax=1000000, yinterval=100000,
               color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    nib_morelos_gage = usgs.lc.northern_international_border(graph=False)
    nib = nib_morelos_gage.annual_af(water_year_month=1, start_year=1964, end_year=current_last_year)
    graph.bars(nib, sub_plot=1, xinterval=year_interval, ymax=2400000, yinterval=200000,
               color='goldenrod', label='USGS NIB at Morelos',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    pilot_knob_gage = usgs.ca.pilot_knob_powerplant_and_wasteway(graph=False)
    pilot_knob = pilot_knob_gage.annual_af(water_year_month=1, start_year=1964, end_year=current_last_year)

    colorado_below_yuma_wasteway_gage = usgs.lc.below_yuma_wasteway(graph=False)
    colorado_below_yuma_wasteway = colorado_below_yuma_wasteway_gage.annual_af(water_year_month=1,
                                                                               start_year=1964,
                                                                               end_year=current_last_year)
    yuma_wasteway_gage = usgs.ca.yuma_main_canal_wasteway_at_yuma(graph=False)
    yuma_wasteway = yuma_wasteway_gage.annual_af(water_year_month=1, start_year=1964, end_year=current_last_year)

    reservation_main_drain_gage = usgs.ca.reservation_main_drain_no_4(graph=False)
    reservation_main_drain = reservation_main_drain_gage.annual_af(water_year_month=1,
                                                                   start_year=1964, end_year=current_last_year)
    yuma_wasteway_estimated = subtract_annual(colorado_below_yuma_wasteway, imperial_dam_release_annual_af)

    data = [{'data': imperial_dam_release_annual_af, 'label': 'USBR Imperial Dam Release', 'color': 'maroon'},
            {'data': yuma_wasteway_estimated, 'label': 'USGS Yuma Wasteway', 'color': 'firebrick'},
            {'data': pilot_knob, 'label': 'USGS All American Pilot Knob Return Flow', 'color': 'indianred'}]
    graph.bars_stacked(data, sub_plot=1, title='Lower Colorado Between Yuma Wasteway and Morelos',
                       ymin=0, ymax=2400000, yinterval=200000, xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=True)
    graph.running_average(imperial_dam_release_annual_af, 10, sub_plot=1)
    graph.running_average(colorado_below_yuma_wasteway, 10, sub_plot=1)

    flows = add_annual(colorado_below_yuma_wasteway, pilot_knob)
    morelos_minus_breakdown = subtract_annual(nib, flows)
    graph.bars(morelos_minus_breakdown, sub_plot=2, title='Morelos minus Flow Breakdown',
               xinterval=year_interval, ymin=-50000, ymax=200000, yinterval=50000,
               color='firebrick', ylabel='kaf',  format_func=WaterGraph.format_kaf)

    graph.bars(yuma_wasteway_estimated, sub_plot=3, title='Colorado Below Yuma Wasteway minus Imperial Release',
               xinterval=year_interval, ymin=0, ymax=700000, yinterval=50000,
               color='firebrick', ylabel='kaf',  format_func=WaterGraph.format_kaf)

    graph.date_and_wait()

    graph = WaterGraph(nrows=3)
    # yuma_wasteway_diff = subtract_annual(yuma_wasteway_estimated, yuma_wasteway)
    graph.bars(yuma_wasteway, sub_plot=0, title='Yuma Wasteway',
               xinterval=year_interval, ymin=0, ymax=400000, yinterval=50000,
               color='firebrick', ylabel='kaf',  format_func=WaterGraph.format_kaf)

    graph.bars(reservation_main_drain, sub_plot=1, title='Reservation Main Drain',
               xinterval=year_interval, ymin=0, ymax=75000, yinterval=10000,
               color='firebrick', ylabel='kaf',  format_func=WaterGraph.format_kaf)

    drain_8b_gage = usgs.ca.drain_8_b_near_winterhaven(graph=False)
    drain_8b = drain_8b_gage.annual_af(water_year_month=1, start_year=1964, end_year=current_last_year)
    graph.bars(drain_8b, sub_plot=2, title='Drain 8B',
               xinterval=year_interval, ymin=0, ymax=75000, yinterval=10000,
               color='firebrick', ylabel='kaf',  format_func=WaterGraph.format_kaf)

    graph.date_and_wait()


def model_all_american():
    year_interval = 3

    usbr_imperial_diversion = usbr.ca.imperial_diversion()
    usbr_imperial_cu = usbr.ca.imperial_cu()
    usbr_imperial_returns = usbr.ca.imperial_returns()

    usbr_coachella_diversion = usbr.ca.coachella_diversion()
    usbr_coachella_cu = usbr.ca.coachella_cu()
    usbr_coachella_returns = usbr.ca.coachella_returns()

    # usbr_yuma_project_diversion = usbr.ca.yuma_project_diversion()
    # usbr_yuma_project_cu = usbr.ca.yuma_project_cu()
    usbr_yuma_project_returns = usbr.ca.yuma_project_returns()

    reservation_main_canal_gage = usgs.ca.reservation_main_canal(graph=False)
    reservation_main_annual_af = reservation_main_canal_gage.annual_af(water_year_month=1,
                                                                       start_year=1964, end_year=current_last_year)
    yuma_project_indian_diversion = usbr.ca.yuma_project_indian_diversion()

    yuma_main_canal_gage = usgs.ca.yuma_main_canal_at_siphon_drop_PP(graph=False)
    yuma_main_annual_af = yuma_main_canal_gage.annual_af(water_year_month=1,
                                                         start_year=1964, end_year=current_last_year)

    pilot_knob_gage = usgs.ca.pilot_knob_powerplant_and_wasteway(graph=False)
    pilot_knob_annual_af = pilot_knob_gage.annual_af(water_year_month=1, start_year=1964, end_year=current_last_year)
    returns = [usbr_imperial_returns, usbr_coachella_returns, usbr_yuma_project_returns]
    return_flows = add_annuals(returns)

    usgs_all_american_gage = usgs.ca.all_american_canal(graph=False)
    usgs_all_american_annual_af = usgs_all_american_gage.annual_af(water_year_month=1,
                                                                   start_year=1964, end_year=current_last_year)
    graph = WaterGraph(nrows=1)
    graph.bars(usgs_all_american_annual_af, sub_plot=0, title='USGS All American Canal Gage',
               xinterval=year_interval, ymin=0, ymax=8000000, yinterval=500000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.date_and_wait()

    graph = WaterGraph(nrows=1)
    bar_data = [{'data': usbr_imperial_cu, 'label': 'Imperial CU (USBR AR)', 'color': 'maroon'},
                {'data': usbr_coachella_cu, 'label': 'Coachella CU (USBR AR)', 'color': 'firebrick'},
                {'data': yuma_main_annual_af, 'label': 'Yuma Main Canal (USGS)', 'color': 'indianred'},
                {'data': yuma_project_indian_diversion, 'label': 'Yuma Project Indian (USBR)', 'color': 'lightcoral'},
                {'data': return_flows, 'label': 'IID/Coachela Returns (USBR AR)', 'color': 'pink'},
                {'data': pilot_knob_annual_af, 'label': 'Pilot Knob Returns (USGS)', 'color': 'mistyrose'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='All American Canal Flow Breakdown',
                       ymin=0, ymax=8000000, yinterval=500000, xinterval=year_interval, xlabel='Calendar Year',
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=True)
    flows = [usbr_imperial_cu,
             usbr_coachella_cu,
             yuma_project_indian_diversion,
             yuma_main_annual_af,
             return_flows,
             pilot_knob_annual_af]
    total_flow = add_annuals(flows)
    graph.running_average(total_flow, 10, sub_plot=0)

    graph.date_and_wait()

    graph = WaterGraph(nrows=4)

    difference = subtract_annual(usgs_all_american_annual_af, total_flow)
    graph.bars(difference, sub_plot=0, title='Error in All American Flow Breakdown vs USGS Gage',
               xinterval=year_interval, ymin=0, ymax=250000, yinterval=25000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    bar_data = [{'data': usbr_imperial_diversion, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': usbr_imperial_cu, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Imperial Diversion & Consumptive Use',
                       ymin=2400000, ymax=3300000, yinterval=100000, xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(usbr_imperial_diversion, 10, sub_plot=1)
    graph.running_average(usbr_imperial_cu, 10, sub_plot=1)

    bar_data = [{'data': usbr_coachella_diversion, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': usbr_coachella_cu, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Coachella Diversion & Consumptive Use',
                       ymin=270000, ymax=580000, yinterval=20000, xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(usbr_coachella_diversion, 10, sub_plot=2)
    graph.running_average(usbr_coachella_cu, 10, sub_plot=2)

    bar_data = [{'data': usbr_imperial_returns, 'label': 'Imperial', 'color': 'darkmagenta'},
                {'data': usbr_coachella_returns, 'label': 'Coachella', 'color': 'm'},
                ]
    graph.bars_stacked(bar_data, sub_plot=3, title='Imperial & Coachella Return Flows (All American Canal Seep?)',
                       ymin=0, ymax=225000, yinterval=25000, xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=True)
    graph.running_average(usbr_imperial_returns, 10, sub_plot=3)
    graph.running_average(add_annual(usbr_imperial_returns, usbr_coachella_returns), 10, sub_plot=3)
    graph.date_and_wait()

    graph = WaterGraph(nrows=3)
    graph.bars(reservation_main_annual_af, sub_plot=0, title='Reservation Main Canal to Yuma Project Indian Diversion',
               xinterval=year_interval, ymin=0, ymax=60000, yinterval=10000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    # graph.bars(yuma_project_indian_diversion, sub_plot=0, title='Yuma Project Indian Diversion',
    #           xinterval=year_interval, ymin=0, ymax=60000, yinterval=10000, color='firebrick',
    #           ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # reservation_diff = subtract_annual(reservation_main_annual_af, usbr.ca.yuma_project_indian_diversion())
    # graph.bars(reservation_diff, sub_plot=0, title='USGS Reservation Main Canal (Annual)',
    #            xinterval=year_interval, ymin=-70000, ymax=70000, yinterval=10000, color='firebrick',
    #            ylabel='kaf',  format_func=WaterGraph.format_kaf)

    graph.bars(yuma_main_annual_af, sub_plot=1, title='USGS Yuma Main Canal at Siphon Drop PP',
               xinterval=year_interval, ymin=0, ymax=800000, yinterval=100000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # Pilot Knob return flow to Colorado River above Morelos
    graph.bars(pilot_knob_annual_af, sub_plot=2, title='USGS All American Pilot Knob Drop 1 Return to Colorado River',
               xinterval=year_interval, ymin=0, ymax=1000000, yinterval=100000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.date_and_wait()
    # Desilting Water
    # imperial_release = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv', water_year_month=1)
    # laguna_release = usbr_report.annual_af('releases/usbr_releases_laguna_dam.csv', water_year_month=1)
    # desilting_water = subtract_annual(laguna_release, imperial_release)
    # graph.bars(desilting_water, sub_plot=2, title='Imperial Dam Desilting water...maybe',
    #            xinterval=year_interval, ymin=-50000, ymax=175000, yinterval=50000, color='firebrick',
    #            ylabel='kaf',  format_func=WaterGraph.format_kaf)


def all_american_extras():
    year_interval = 4
    # All American Canal Above Imperial Dam
    graph = WaterGraph(nrows=3)

    gage = USGSGage('09523000', start_date='1939-10-01')
    all_american_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(all_american_annual_af, sub_plot=0, title='USGS All American Canal Diversion (Annual)',
               xinterval=year_interval, ymin=3000000, ymax=6500000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    # Gila Gravity Main Canal
    gage = USGSGage('09522500', start_date='1943-08-16')
    gila_gravity_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(gila_gravity_annual_af, sub_plot=1, title='USGS Gila Gravity Main Canal Diversion (Annual)',
               xinterval=year_interval, ymin=0, ymax=1000000, yinterval=100000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    # Imperial Dam Release
    imperial_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv')
    graph.bars(imperial_dam_release_annual_af, sub_plot=2, title='USBR AR Imperial Dam Release (Annual)',
               xinterval=year_interval, ymax=500000, yinterval=50000,
               color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # Colorado River Below Imperial Dam, new gage, not worth much
    # gage = USGSGage('09429500', start_date='2018-11-29')
    graph.date_and_wait()

    graph = WaterGraph(nrows=4)

    reservation_main_annual_af = usgs.ca.reservation_main_canal(graph=False).annual_af(water_year_month=1)
    graph.bars(reservation_main_annual_af, sub_plot=0, title='USGS Reservation Main Canal (Annual)',
               xinterval=year_interval, ymin=0, ymax=70000, yinterval=10000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    yuma_main_annual_af = usgs.ca.yuma_main_canal_at_siphon_drop_PP(graph=False).annual_af(water_year_month=1,
                                                                                           start_year=1964)
    graph.bars(yuma_main_annual_af, sub_plot=1, title='USGS Yuma Main Canal at Siphon Drop PP (Annual)',
               xinterval=year_interval, ymin=0, ymax=800000, yinterval=100000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # 09530500 10-14 CFS DRAIN 8-B NEAR WINTERHAVEN, CA
    # 0254970 160 CFS NEW R AT INTERNATIONAL BOUNDARY AT CALEXICO CA  1979-10-01
    # 09527594 150-45 CFS COACHELLA CANAL NEAR NILAND, CA  2009-10-17
    # 09527597 COACHELLA CANAL NEAR DESERT BEACH, CA  2009-10-24
    # 10254730 ALAMO R NR NILAND CA   1960-10-01
    # 10255550 NEW R NR WESTMORLAND CA  1943-01-01
    # 10259540 WHITEWATER R NR MECCA  1960-10-01

    # Coachella
    gage = USGSGage('09527590', start_date='2003-10-01')
    coachella_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(coachella_annual_af, sub_plot=2, title='USGS Coachella (Annual)',
               xinterval=year_interval, ymin=0, ymax=400000, yinterval=50000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    # All American Drop 2, probably IID
    gage = USGSGage('09527700', start_date='2011-10-26')
    drop_2_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(drop_2_annual_af, sub_plot=3, title='USGS Drop 2 - Imperial(Annual)',
               xlabel='Calendar Year', xinterval=year_interval,
               ymin=0, ymax=3000000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    graph.date_and_wait()

    graph = WaterGraph(nrows=4)
    # Brock Inlet
    gage = USGSGage('09527630', start_date='2013-11-06')
    brock_inlet_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)

    # Brock Outlet
    gage = USGSGage('09527660', start_date='2013-10-23')
    brock_outlet_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)

    graph.bars_two(brock_inlet_annual_af, brock_outlet_annual_af,
                   title='USGS Brock Inlet and Outlet (Annual)', sub_plot=0,
                   label_a='Brock Inlet', color_a='royalblue',
                   label_b='Brock Outlet', color_b='firebrick',
                   xinterval=year_interval, ymax=175000, yinterval=25000,
                   ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.running_average(brock_outlet_annual_af, 10, sub_plot=0, label="10Y Avg Brock Outlet")

    gage = USGSGage('09523600', start_date='1966-10-01')
    yaqui_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(yaqui_main_annual_af, sub_plot=1, title='Yaqui (Annual)',
               xinterval=year_interval, ymin=0, ymax=12000, yinterval=2000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    gage = USGSGage('09523800', start_date='1966-10-01')
    pontiac_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(pontiac_main_annual_af, sub_plot=2, title='Pontiac (Annual)',
               xinterval=year_interval, ymin=0, ymax=12000, yinterval=2000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    gage = USGSGage('09526200', start_date='1995-01-01')
    ypsilanti_main_annual_af = gage.annual_af(start_year=1965, end_year=current_last_year)
    graph.bars(ypsilanti_main_annual_af, sub_plot=3, title='Ypsilanti (Annual)',
               xinterval=year_interval, ymin=0, ymax=15000, yinterval=3000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


def lake_powell_inflow():
    start_year = 1963
    end_year = 2022
    water_year_month = 10

    show_graph = False
    show_annotated = show_graph

    usgs_colorado_cisco_gage = usgs.ut.colorado_cisco(graph=show_graph)
    colorado_cisco_af = usgs_colorado_cisco_gage.annual_af(start_year=start_year, end_year=end_year,
                                                           water_year_month=water_year_month)
    if show_annotated:
        graph = WaterGraph(nrows=1)
        graph.bars(colorado_cisco_af, sub_plot=0, title=usgs_colorado_cisco_gage.site_name, color='royalblue',
                   ymin=0, ymax=11500000, yinterval=500000, xinterval=4,
                   xlabel='Water Year', bar_width=1,  # xmin=start_year, xmax=end_year,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.annotate_vertical_arrow(1916, "Grand Valley", offset_percent=2.5)
        graph.annotate_vertical_arrow(1942, "Green Mountain", offset_percent=2.5)
        graph.annotate_vertical_arrow(1947, "Adams Tunnel", offset_percent=5)
        graph.annotate_vertical_arrow(1963, "Dillon", offset_percent=2.5)
        graph.annotate_vertical_arrow(1966, "Blue Mesa", offset_percent=5)
        graph.date_and_wait()

    usgs_green_river_gage = usgs.ut.green_river_at_green_river(graph=show_graph)
    green_river_af = usgs_green_river_gage.annual_af(start_year=start_year, end_year=end_year,
                                                     water_year_month=water_year_month)
    if show_annotated:
        graph = WaterGraph(nrows=1)
        graph.bars(green_river_af, sub_plot=0, title=usgs_green_river_gage.site_name, color='royalblue',
                   ymin=0, ymax=9000000, yinterval=500000, xinterval=4,
                   xlabel='Water Year', bar_width=1,  # xmin=start_year, xmax=end_year,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.annotate_vertical_arrow(1962, "Flaming Gorge", offset_percent=2.5)
        graph.annotate_vertical_arrow(1963, "Fontenelle", offset_percent=5)
        graph.date_and_wait()

    usgs_san_juan_bluff_gage = usgs.ut.san_juan_bluff(graph=show_graph)
    san_juan_af = usgs_san_juan_bluff_gage.annual_af(start_year=start_year, end_year=end_year,
                                                     water_year_month=water_year_month)
    if show_annotated:
        graph = WaterGraph(nrows=1)
        graph.bars(san_juan_af, sub_plot=0, title=usgs_san_juan_bluff_gage.site_name, color='royalblue',
                   ymin=0, ymax=3250000, yinterval=250000, xinterval=4,
                   xlabel='Water Year',  # xmin=start_year, xmax=end_year,
                   ylabel='maf', format_func=WaterGraph.format_maf)
        graph.annotate_vertical_arrow(1962, "Navajo", offset_percent=2.5)
        graph.date_and_wait()

    usgs_dirty_devil_gage = usgs.ut.dirty_devil(graph=True)
    dirty_devil_af = usgs_dirty_devil_gage.annual_af(start_year=start_year, end_year=end_year,
                                                     water_year_month=water_year_month)
    # Only around 8 kaf annually
    # usgs_escalante_gage = usgs_escalante(graph=True)
    # escalante_af = usgs_escalante_gage.annual_af(start_year=start_year, end_year=end_year)

    year_interval = 3
    graph = WaterGraph(nrows=1)
    usbr_lake_powell_inflow_af = 4288
    usbr_lake_powell_inflow_volume_unregulated_af = 4301
    annual_inflow_af = usbr_rise.annual_af(usbr_lake_powell_inflow_af)
    annual_inflow_af = reshape_annual_range(annual_inflow_af, 1963, 2022)
    # graph.bars(annual_inflow_af, sub_plot=0, title='Lake Powell Inflow',
    #            ymin=3000000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
    #           ylabel='maf',  format_func=WaterGraph.format_maf)

    annual_inflow_unregulated_af = usbr_rise.annual_af(usbr_lake_powell_inflow_volume_unregulated_af)
    # graph.bars(annual_inflow_unregulated_af, sub_plot=1, title='Lake Powell Unregulated Inflow',
    #            ymin=300000, ymax=21000000, yinterval=2000000, xinterval=year_interval,
    #            ylabel='maf', format_func=WaterGraph.format_maf)
    # bar_data = [{'data': annual_inflow_unregulated_af, 'label': 'Lake Powell Unregulated Inflow', 'color': 'blue'},
    #             {'data': annual_inflow_af, 'label': 'Lake Powell Inflow', 'color': 'royalblue'},
    #             ]
    # graph.bars_stacked(bar_data, sub_plot=0, title='Lake Powell Inflow & Unregulated Inflow',
    #                    ymin=300000, ymax=21000000, yinterval=2000000,
    #                    xlabel='Water Year', xinterval=3,
    #                    ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    total = add_annuals([colorado_cisco_af, green_river_af, san_juan_af])
    if show_graph:
        graph.bars_two(annual_inflow_af, annual_inflow_unregulated_af,
                       title='Lake Powell Inflow & Unregulated Inflow, 10 yr moving avg',
                       label_a='Inflow', color_a='royalblue',
                       label_b='Unregulated Inflow', color_b='darkblue',
                       ylabel='af', ymin=0, ymax=21000000, yinterval=2000000,
                       xlabel='Water Year', xinterval=year_interval, format_func=WaterGraph.format_maf)
        graph.running_average(annual_inflow_af, 10, sub_plot=0)
        graph.running_average(annual_inflow_unregulated_af, 10, sub_plot=0)
        graph.date_and_wait()

        graph = WaterGraph(nrows=2)
        bar_data = [{'data': colorado_cisco_af, 'label': 'Colorado at Cisco', 'color': 'darkblue'},
                    {'data': green_river_af, 'label': 'Green at Green River', 'color': 'royalblue'},
                    {'data': san_juan_af, 'label': 'San Juan at Bluff', 'color': 'cornflowerblue'},
                    {'data': dirty_devil_af, 'label': 'Dirty Devil', 'color': 'lightblue'},
                    ]
        graph.bars_stacked(bar_data, sub_plot=0, title='USGS Lake Powell River Inflows',
                           ymin=0, ymax=22000000, yinterval=1000000,
                           xlabel='Water Year', xinterval=year_interval,
                           ylabel='maf', format_func=WaterGraph.format_maf, vertical=True)
        graph.running_average(total, 5, sub_plot=0, label='5 yr moving avg', color='goldenrod')
        graph.running_average(total, 7, sub_plot=0, label='7 yr moving avg', color='gold')

        graph.bars(annual_inflow_af, sub_plot=1, title='USBR RISE Lake Powell Inflow, 10 yr moving avg',
                   ymin=0, ymax=22000000, yinterval=1000000, xinterval=year_interval, xlabel='Water Year',
                   ylabel='maf',  format_func=WaterGraph.format_maf)
        graph.date_and_wait()
    return total


def lake_powell_outflow():
    return usgs.az.lees_ferry(graph=False).annual_af(water_year_month=1)


def lake_mead_side_inflows(show_graph=False):
    start_year = 1995
    water_year_month = 10
    end_year = current_last_year
    year_interval = 3

    colorado_near_grand_canyon_af = usgs.az.colorado_near_grand_canyon(graph=False).annual_af(
        water_year_month=water_year_month, start_year=1995, end_year=end_year)
    # colorado_above_diamond_creek = usgs.az.colorado_above_diamond_creek_near_peach_springs(graph=False).annual_af(
    #   water_year_month=water_year_month, start_year=1995, end_year=end_year)
    colorado_lees_ferry_af = usgs.az.lees_ferry(graph=False).annual_af(
        water_year_month=water_year_month, start_year=1995, end_year=end_year)
    little_colorado_af = usgs.az.little_colorado_cameron(graph=False).annual_af(
        water_year_month=water_year_month, start_year=1995, end_year=end_year)
    paria_annual_af = usgs.az.paria_lees_ferry(graph=False).annual_af(
        water_year_month=water_year_month, start_year=1995, end_year=end_year)
    upper_grand_canyon_af = add_annuals([colorado_lees_ferry_af, little_colorado_af, paria_annual_af])
    usgs_havasu_creek_gage = usgs.az.havasu_creek_above_the_mouth_near_supai(graph=show_graph)
    havasu_creek_af = usgs_havasu_creek_gage.annual_af(
        water_year_month=water_year_month, start_year=start_year, end_year=end_year)
    difference = subtract_annual(colorado_near_grand_canyon_af, upper_grand_canyon_af)

    # USBR 24 month study numbers, some of these are generated (i.e. Davis evap) or may be from models
    lake_mead_side_inflow_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_mead_side_inflow.csv', multiplier=1000)

    # lake_mead_side_inflow_af = reshape_annual_range(lake_mead_side_inflow_af, start_year, end_year)
    if show_graph:
        graph = WaterGraph(nrows=3)
        bar_data = [
            {'data': colorado_near_grand_canyon_af, 'label': 'Colorado nr Grand Canyon Resort', 'color': 'darkred'},
            {'data': upper_grand_canyon_af, 'label': 'Lees Ferry + Paria + Little Colorado', 'color': 'firebrick'}]
        graph.bars_stacked(bar_data, sub_plot=0, title='Colorado River Gages Above Lake Mead',
                           ymin=7000000, ymax=14500000, yinterval=500000,
                           xinterval=year_interval,
                           ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
        graph.running_average(colorado_near_grand_canyon_af, 10, sub_plot=1)
        graph.running_average(upper_grand_canyon_af, 10, sub_plot=1)

        graph.bars(difference, sub_plot=1,
                   title='Difference between Grand Canyon Resort Gage & Lees Ferry+Paria+Little Colorado',
                   ymin=0, ymax=400000, yinterval=25000, xinterval=year_interval,
                   ylabel='kaf',  format_func=WaterGraph.format_kaf)
        graph.bars(lake_mead_side_inflow_af, sub_plot=2, title='Lake Mead Side Inflow (USBR 24 month studies)',
                   ymin=0, ymax=1200000, yinterval=100000, xinterval=year_interval,
                   xlabel='Water Year', ylabel='kaf',  format_func=WaterGraph.format_kaf)
        graph.date_and_wait()

    usgs_virgin_gage = usgs.az.virgin_at_littlefield(graph=show_graph)
    virgin_af = usgs_virgin_gage.annual_af(water_year_month=water_year_month, start_year=start_year, end_year=end_year)

    usgs_muddy_gage = usgs.nv.muddy_near_glendale(graph=show_graph)
    muddy_af = usgs_muddy_gage.annual_af(water_year_month=water_year_month, start_year=start_year, end_year=end_year)

    lees_ferry_gage = usgs.az.lees_ferry(graph=show_graph)
    lees_ferry_af = lees_ferry_gage.annual_af(water_year_month=water_year_month,
                                              start_year=start_year, end_year=end_year)

    glen_canyon_annual_release_af = usbr_glen_canyon_annual_release_af(graph=show_graph,
                                                                       start_year=start_year, end_year=end_year)
    paria_annual_af = usgs.az.paria_lees_ferry(graph=show_graph).annual_af(water_year_month=water_year_month,
                                                                           start_year=start_year, end_year=end_year)

    glen_canyon_plus_paria_af = add_annual(glen_canyon_annual_release_af, paria_annual_af)
    glen_canyon_seep_af = subtract_annual(lees_ferry_af, glen_canyon_plus_paria_af)

    # Stacked graph of the inflows
    # Compare to USBR side flows from 24 month
    total = add_annuals([little_colorado_af, virgin_af, muddy_af])
    total = add_annual(total, glen_canyon_seep_af)
    if show_graph:
        graph = WaterGraph(nrows=2)
        graph.bars(glen_canyon_seep_af, sub_plot=0, title='Glen Canyon + Paria - Lees Ferry Gage',
                   ymin=0, ymax=300000, yinterval=50000, xinterval=year_interval,
                   ylabel='kaf',  format_func=WaterGraph.format_kaf)
        bar_data = [{'data': glen_canyon_seep_af, 'label': 'Theoretical Glen Canyon Seep', 'color': 'royalblue'},
                    {'data': little_colorado_af, 'label': 'Little Colorado at Cameron', 'color': 'darkred'},
                    {'data': virgin_af, 'label': 'Virgin at Littlefield', 'color': 'firebrick'},
                    {'data': muddy_af, 'label': 'Muddy at Glendale', 'color': 'indianred'},
                    {'data': havasu_creek_af, 'label': 'Havasu Creek at Supai', 'color': 'lightcoral'},
                    ]
        graph.bars_stacked(bar_data, sub_plot=1, title='Lake Mead Inflows Excluding Glen Canyon Release',
                           ymin=0, ymax=1150000, yinterval=100000,
                           xlabel='Water Year', xinterval=year_interval,
                           ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=True)
        graph.annotate_vertical_arrow(2005, "Big Monsoon", sub_plot=1, offset_percent=5.0)
        graph.annotate_vertical_arrow(2017, "May Rain", sub_plot=1, offset_percent=40.0)
        graph.annotate_vertical_arrow(2019, "Spring Bomb Cyclone", sub_plot=1, offset_percent=30.0)
        graph.running_average(total, 10, sub_plot=1)
        graph.date_and_wait()
    return total


def lake_mead_inflow():
    colorado_above_diamond_creek = usgs.az.colorado_above_diamond_creek_near_peach_springs(graph=False).annual_af()
    return colorado_above_diamond_creek


def usgs_lower_colorado_to_border_gages():
    usgs.ca.all_american_canal()
    usgs.az.gila_gravity_main_canal()
    usgs.ca.pilot_knob_powerplant_and_wasteway()
    usgs.ca.reservation_main_canal()
    usgs.az.yuma_main_canal()
    usgs.lc.below_imperial()

    usgs.az.north_gila_main_canal()
    usgs.az.unit_b_canal_near_yuma()
    usgs.lc.below_laguna()

    usgs.az.wellton_mohawk_main_canal()
    usgs.az.wellton_mohawk_main_outlet_drain()

    usgs.az.yuma_main_canal_wasteway()

    usgs.lc.below_yuma_wasteway()
    usgs.lc.northern_international_border()


def usbr_lower_basin_states_total_use():
    year_interval = 3
    graph = WaterGraph(nrows=3)

    # CA Total Diversion & Consumptive Use
    ca_diversion_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_diversion.csv')
    ca_diversion_annual_af = usbr_report.monthly_to_water_year(ca_diversion_monthly_af, water_year_month=1)

    ca_use_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_consumptive_use.csv')
    ca_use_annual_af = usbr_report.monthly_to_water_year(ca_use_monthly_af, water_year_month=1)

    bar_data = [{'data': ca_diversion_annual_af, 'label': 'California Diversion', 'color': 'darkmagenta'},
                {'data': ca_use_annual_af, 'label': 'California Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='California Totals (Annual)',
                       ymin=0, ymax=6000000, yinterval=1000000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(ca_use_annual_af, 10, sub_plot=0)

    # AZ Total Diversion & Consumptive Use
    az_diversion_monthly_af = usbr_report.load_monthly_csv('az/usbr_az_total_diversion.csv')
    az_diversion_annual_af = usbr_report.monthly_to_water_year(az_diversion_monthly_af, water_year_month=1)

    az_use_monthly_af = usbr_report.load_monthly_csv('az/usbr_az_total_consumptive_use.csv')
    az_use_annual_af = usbr_report.monthly_to_water_year(az_use_monthly_af, water_year_month=1)

    bar_data = [{'data': az_diversion_annual_af, 'label': 'Arizona Diversion', 'color': 'darkmagenta'},
                {'data': az_use_annual_af, 'label': 'Arizona Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Arizona Totals (Annual)',
                       ymin=0, ymax=4000000, yinterval=500000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(az_use_annual_af, 10, sub_plot=1)

    # NV Total Diversion & Consumptive Use
    nv_diversion_monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_total_diversion.csv')
    nv_diversion_annual_af = usbr_report.monthly_to_water_year(nv_diversion_monthly_af, water_year_month=1)

    nv_use_monthly_af = usbr_report.load_monthly_csv('nv/usbr_nv_total_consumptive_use.csv')
    nv_use_annual_af = usbr_report.monthly_to_water_year(nv_use_monthly_af, water_year_month=1)

    bar_data = [{'data': nv_diversion_annual_af, 'label': 'Nevada Diversion', 'color': 'darkmagenta'},
                {'data': nv_use_annual_af, 'label': 'Nevada Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Nevada Totals (Annual)',
                       ymin=0, ymax=550000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(nv_use_annual_af, 10, sub_plot=2)
    graph.date_and_wait()

    # Total use as stacked bars
    total_use_annual_af = np.zeros(len(ca_use_annual_af), [('dt', 'i'), ('val', 'f')])
    total_use_annual_af['dt'] = ca_use_annual_af['dt']
    total_use_annual_af['val'] = ca_use_annual_af['val']
    total_use_annual_af['val'] += az_use_annual_af['val']
    total_use_annual_af['val'] += nv_use_annual_af['val']

    # total_diversion_annual_af = np.zeros(len(ca_diversion_annual_af), [('dt', 'i'), ('val', 'f')])
    # total_diversion_annual_af['dt'] = ca_diversion_annual_af['dt']
    # total_diversion_annual_af['val'] = ca_diversion_annual_af['val']
    # total_diversion_annual_af['val'] += az_diversion_annual_af['val']
    # total_diversion_annual_af['val'] += nv_diversion_annual_af['val']

    # diversion_above_use_annual_af = np.zeros(len(ca_diversion_annual_af), [('dt', 'i'), ('val', 'f')])
    # diversion_above_use_annual_af['dt'] = ca_diversion_annual_af['dt']
    # diversion_above_use_annual_af['val'] = total_diversion_annual_af['val']
    # diversion_above_use_annual_af['val'] -= total_use_annual_af['val']
    graph = WaterGraph(nrows=1)

    bar_data = [{'data': ca_use_annual_af, 'label': 'California Consumptive Use', 'color': 'maroon'},
                {'data': az_use_annual_af, 'label': 'Arizona Consumptive Use', 'color': 'firebrick'},
                {'data': nv_use_annual_af, 'label': 'Nevada Consumptive Use', 'color': 'lightcoral'},
                # {'data': diversion_above_use_annual_af, 'label': 'Total Diversions', 'color': 'darkmagenta'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Total Lower Basin Consumptive Use (Annual)',
                       ymin=0, ymax=9000000, yinterval=500000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(total_use_annual_af, 10, sub_plot=0)
    graph.date_and_wait()


# noinspection PyUnusedLocal
def keyboardInterruptHandler(sig, frame):
    global interrupted
    interrupted = True

    try:
        print("exit")
        sys.exit(0)
    except OSError as e:
        print("riverwar exit exception:", e)


def model_yuma_area():
    year_interval = 4

    # CA Yuma Area Returns
    graph = WaterGraph(nrows=2)
    data = usbr.ca.yuma_area_returns()
    graph.bars_stacked(data, sub_plot=0, title='CA Yuma Area Returns',
                       ymin=0, ymax=250000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    ca_total = add_annuals(arrays)
    graph.running_average(ca_total, 10, sub_plot=0)

    # AZ Yuma Area Returns
    data = usbr.az.yuma_area_returns()
    graph.bars_stacked(data, sub_plot=1, title='AZ Yuma Area Returns',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    az_return_total = add_annuals(arrays)
    graph.running_average(az_return_total, 10, sub_plot=1)
    graph.date_and_wait()

    # Yuma Area Diversion
    graph = WaterGraph(nrows=2)
    data = usbr.az.yuma_area_diversion()
    graph.bars_stacked(data, sub_plot=0, title='AZ Yuma Area Diversion',
                       ymin=0, ymax=1300000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    az_diversion_total = add_annuals(arrays)
    graph.running_average(az_diversion_total, 10, sub_plot=0)

    # Yuma Area Consumptive Use
    data = usbr.az.yuma_area_cu()
    graph.bars_stacked(data, sub_plot=1, title='AZ Yuma Area Consumptive Use',
                       ymin=0, ymax=1300000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    az_cu_total = add_annuals(arrays)
    graph.running_average(az_cu_total, 10, sub_plot=1)
    graph.date_and_wait()

    # MX Yuma Area Returns
    graph = WaterGraph(nrows=1)
    data = usbr.mx.yuma_area_returns()
    graph.bars_stacked(data, sub_plot=0, title='Mexico Yuma Area Returns',
                       ymin=0, ymax=200000, yinterval=10000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    az_total = add_annuals(arrays)
    graph.running_average(az_total, 10, sub_plot=0)
    graph.date_and_wait()

    graph = WaterGraph(nrows=2)
    data = []
    below_yuma_wasteway_annual = usgs.lc.below_yuma_wasteway(graph=False).annual_af()
    nib_annual = usgs.lc.northern_international_border(graph=False).annual_af()
    data.append({'data': nib_annual, 'label': 'USGS Morelos Northern International Border (NIB)', 'color': 'maroon'})
    data.append({'data': below_yuma_wasteway_annual, 'label': 'USGS Colorado River Below Yuma Wasteway',
                 'color': 'firebrick'})

    graph.bars_stacked(data, sub_plot=0, title='Lower Colorado Between Yuma and Morelos',
                       ymin=0, ymax=2000000, yinterval=200000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(nib_annual, 10, sub_plot=0)
    graph.running_average(below_yuma_wasteway_annual, 10, sub_plot=0)

    difference = subtract_annual(nib_annual, below_yuma_wasteway_annual)
    graph.bars(difference, sub_plot=1, title='Inflows between Yuma Wasteway and NIB', color='firebrick',
               ymin=0, ymax=1000000, yinterval=100000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.date_and_wait()


def yuma_area_wasteways():
    year_interval = 4
    graph = WaterGraph(nrows=1)
    data = usgs.az.yuma_area_wasteways()
    graph.bars_stacked(data, sub_plot=0, title='Yuma Area Wasteways and Drains',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    total = add_annuals(arrays)
    graph.running_average(total, 10, sub_plot=0)
    graph.date_and_wait()


def model_not_yuma_area():
    year_interval = 4
    graph = WaterGraph(nrows=1)
    data = usbr.ca.not_yuma_area_returns()
    graph.bars_stacked(data, sub_plot=0, title='CA Returns Not in Yuma Area',
                       ymin=300000, ymax=600000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    ca_total = add_annuals(arrays)
    graph.running_average(ca_total, 10, sub_plot=0)

    graph.date_and_wait()

    graph = WaterGraph(nrows=1)
    data = usbr.az.not_yuma_area_returns()
    graph.bars_stacked(data, sub_plot=0, title='AZ Returns Not in Yuma Area',
                       ymin=0, ymax=500000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    arrays = []
    for water_user in data:
        arrays.append(water_user['data'])
    az_total = add_annuals(arrays)
    graph.running_average(az_total, 10, sub_plot=0)
    graph.date_and_wait()


def model_lower_colorado_1905_1964():
    year_interval = 2
    water_year_month = 10

    show_graph = False
    lees_ferry_gage = usgs.az.lees_ferry(graph=show_graph)
    lees_ferry_annual_af = lees_ferry_gage.annual_af(water_year_month=water_year_month, start_year=1922, end_year=1964)

    # usgs_little_colorado_gage = usgs.az.little_colorado_cameron(graph=show_graph)
    # little_colorado_af = usgs_little_colorado_gage.annual_af(water_year_month=water_year_month)

    # usgs_virgin_gage = usgs.az.virgin_at_littlefield(graph=show_graph)
    # virgin_af = usgs_virgin_gage.annual_af(water_year_month=water_year_month)

    # usgs_muddy_gage = usgs.nv.muddy_near_glendale(graph=show_graph)
    # muddy_af = usgs_muddy_gage.annual_af(water_year_month=water_year_month)

    gila_dome_gage = usgs.az.gila_dome(graph=show_graph)
    gila_dome_af = gila_dome_gage.annual_af(water_year_month=water_year_month, start_year=1922, end_year=1964)

    graph = WaterGraph(nrows=2)
    yuma_gage = usgs.lc.yuma(graph=show_graph)
    daily_discharge_cfs = yuma_gage.daily_discharge()
    graph.plot(daily_discharge_cfs, title=yuma_gage.site_name, sub_plot=0, ylabel='CFS',
               xinterval=year_interval,
               ymin=yuma_gage.cfs_min, ymax=yuma_gage.cfs_max, yinterval=yuma_gage.cfs_interval,
               format_func=WaterGraph.format_discharge, color=yuma_gage.color)

    yuma_annual_af = yuma_gage.annual_af(water_year_month=water_year_month)
    graph.bars(yuma_annual_af, sub_plot=1,
               xinterval=year_interval, ymin=0, ymax=27000000, yinterval=2000000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.date_and_wait()

    # usgs_all_american_gage = usgs.ca.all_american_canal(graph=show_graph)
    # all_american_af = usgs_all_american_gage.annual_af(water_year_month=water_year_month)

    # nib_gage = usgs.lc.northern_international_border(graph=False)
    # nib_annual_af = nib_gage.annual_af()

    # below_davis_gage = usgs.lc.below_davis(graph=False)
    # below_davis_annual_af = below_davis_gage.annual_af()

    hoover_release = usbr.lc.lake_mead(graph=show_graph)
    hoover_release = reshape_annual_range(hoover_release, 1922, 1964)
    # davis_release = usbr.lc.lake_mohave(graph=False)
    # parker_release = usbr.lc.lake_havasu(graph=False)

    graph = WaterGraph(nrows=4)
    graph.bars(lees_ferry_annual_af, sub_plot=0, title='USGS Lees Ferry',
               xinterval=year_interval, ymin=0, ymax=20000000, yinterval=2000000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.bars(hoover_release, sub_plot=1, title='USBR RISE Hoover Release',
               xinterval=year_interval, ymin=0, ymax=20000000, yinterval=2000000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.bars(gila_dome_af, sub_plot=2, title='USGS Gila Dome',
               xinterval=year_interval, ymin=0, ymax=1000000, yinterval=200000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.bars(yuma_annual_af, sub_plot=3, title='USGS Yuma',
               xinterval=year_interval, ymin=0, ymax=20000000, yinterval=2000000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    # graph.bars(nib_annual_af, sub_plot=3, title='USGS NIB',
    #           xinterval=year_interval, ymin=0, ymax=18000000, yinterval=2000000, color='firebrick',
    #            ylabel='maf',  format_func=WaterGraph.format_maf)

    graph.date_and_wait()

    # graph = WaterGraph(nrows=4)

    # graph.bars(below_davis_annual_af, sub_plot=1, title='USGS Below Davis',
    #            xinterval=year_interval, ymin=0, ymax=24000000, yinterval=5000000, color='firebrick',
    #            ylabel='maf',  format_func=WaterGraph.format_maf)
    # graph.bars(davis_release, sub_plot=2, title='USBR RISE Davis Release',
    #            xinterval=year_interval, ymin=0, ymax=24000000, yinterval=5000000, color='firebrick',
    #            ylabel='maf',  format_func=WaterGraph.format_maf)
    # graph.bars(parker_release, sub_plot=3, title='USBR RISE Parker Release',
    #            xinterval=year_interval, ymin=0, ymax=24000000, yinterval=5000000, color='firebrick',
    #            ylabel='maf',  format_func=WaterGraph.format_maf)
    # graph.date_and_wait()


def hoover_to_imperial_graph():
    hoover_release = usbr.lc.lake_mead(graph=False)
    davis_release = usbr.lc.lake_mohave(graph=False)
    parker_release = usbr.lc.lake_havasu(graph=False)
    rock_release = usbr_report.annual_af('releases/usbr_releases_rock_dam.csv')
    palo_verde_release = usbr_report.annual_af('releases/usbr_releases_palo_verde_dam.csv')
    imperial_release = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv')
    laguna_release = usbr_report.annual_af('releases/usbr_releases_laguna_dam.csv')

    year_interval = 3
    graph = WaterGraph(nrows=1)
    bar_data = [{'data': hoover_release, 'label': 'Hoover', 'color': 'mistyrose'},
                {'data': davis_release, 'label': 'Davis', 'color': 'pink'},
                {'data': parker_release, 'label': 'Parker', 'color': 'lightcoral'},
                {'data': rock_release, 'label': 'Rock', 'color': 'indianred'},
                {'data': palo_verde_release, 'label': 'Palo Verde', 'color': 'firebrick'},
                {'data': laguna_release, 'label': 'Laguna', 'color': 'black'},
                {'data': imperial_release, 'label': 'Imperial', 'color': 'maroon'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Lower Colorado Dam Releases (Annual)',
                       xinterval=year_interval, ymin=0, ymax=23000000, yinterval=1000000, width=0.9,
                       ylabel='maf',  format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(hoover_release, 10, sub_plot=0, color='goldenrod', label='10Y Hoover')
    graph.running_average(parker_release, 10, sub_plot=0, color='darkgoldenrod', label='10Y Parker')
    graph.date_and_wait()

    graph = WaterGraph(nrows=4)

    hoover_minus_davis = subtract_annual(hoover_release, davis_release)
    graph.bars(hoover_minus_davis, sub_plot=0, title='Hoover minus Davis Releases',
               xinterval=year_interval, ymin=-500000, ymax=750000, yinterval=250000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.running_average(hoover_minus_davis, 10, sub_plot=0)

    davis_minus_parker = subtract_annual(davis_release, parker_release)
    graph.bars(davis_minus_parker, sub_plot=1, title='Davis minus Parker Release',
               xinterval=year_interval, ymin=0, ymax=3100000, yinterval=250000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(davis_minus_parker, 10, sub_plot=1)

    parker_minus_rock = subtract_annual(parker_release, rock_release)
    graph.bars(parker_minus_rock, sub_plot=2, title='Parker minus Rock Release',
               xinterval=year_interval, ymin=-1000000, ymax=2500000, yinterval=250000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(parker_minus_rock, 10, sub_plot=2)

    # crit_release_returns = add_annual(rock_release, usbr.az.crit_returns())
    rock_minus_palo_verde = subtract_annual(rock_release, palo_verde_release)
    graph.bars(rock_minus_palo_verde, sub_plot=3, title='Rock minus Palo Verde Release ',
               xinterval=year_interval, ymin=0, ymax=1600000, yinterval=250000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(rock_minus_palo_verde, 10, sub_plot=3)

    graph.date_and_wait()

    graph = WaterGraph(nrows=2)
    palo_verde_release_returns = add_annual(palo_verde_release, usbr.ca.palo_verde_returns())
    palo_verde_minus_imperial = subtract_annual(palo_verde_release_returns, imperial_release)
    graph.bars(palo_verde_minus_imperial, sub_plot=0, title='(Palo Verde Release & Returns) minus Imperial Release',
               xinterval=year_interval, ymin=3000000, ymax=8000000, yinterval=1000000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.running_average(palo_verde_minus_imperial, 10, sub_plot=0)

    laguna_minus_imperial = subtract_annual(laguna_release, imperial_release)
    graph.bars(laguna_minus_imperial, sub_plot=1, title='Laguna minus Imperial Release',
               xinterval=year_interval, ymin=-50000, ymax=200000, yinterval=50000, color='firebrick',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)
    graph.running_average(laguna_minus_imperial, 10, sub_plot=1)
    graph.date_and_wait()

    # Colorado River Indian Tribe (CRIT) and Rock Dam Release
    graph = WaterGraph(nrows=4)

    crit_diversion_annual_af = usbr.az.crit_diversion()
    crit_cu_annual_af = usbr.az.crit_cu()

    bar_data = [{'data': crit_diversion_annual_af, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': crit_cu_annual_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='USBR AR CRIT Diversion & Consumptive Use (Annual)',
                       xinterval=year_interval, ymin=150000, ymax=750000, yinterval=100000, width=0.9,
                       ylabel='kaf',  format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(crit_diversion_annual_af, 10, sub_plot=0)
    graph.running_average(crit_cu_annual_af, 10, sub_plot=0)

    rock_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_rock_dam.csv')
    graph.bars(rock_dam_release_annual_af, sub_plot=1, title='USBR AR Rock Dam Release (Annual)',
               xinterval=year_interval, ymin=4500000, ymax=8000000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    crit_return_flows_annual = subtract_annual(crit_diversion_annual_af, crit_cu_annual_af, 1965, current_last_year)
    graph.bars(crit_return_flows_annual, sub_plot=2, title='USBR AR CRIT Return Flows(Annual)',
               xinterval=year_interval, ymin=150000, ymax=400000, yinterval=50000, color='darkmagenta',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    bar_data = [{'data': rock_dam_release_annual_af, 'label': 'Rock Dam Release', 'color': 'firebrick'},
                {'data': crit_return_flows_annual, 'label': 'CRIT Return Flows', 'color': 'darkmagenta'},
                ]
    graph.bars_stacked(bar_data, sub_plot=3, title='USBR AR Flow below Rock Dam with CRIT Return Flows (Annual)',
                       xinterval=year_interval, ymin=4500000, ymax=8000000, yinterval=500000, xlabel='Calendar Year',
                       ylabel='maf',  format_func=WaterGraph.format_maf)
    flows_below_rock_annual = add_annual(rock_dam_release_annual_af, crit_return_flows_annual,
                                         1965, current_last_year)
    graph.running_average(flows_below_rock_annual, 10, sub_plot=3)

    graph.date_and_wait()

    # Palo Verde Diversion Dam Release and Return Flows
    graph = WaterGraph(nrows=4)

    palo_verde_diversion_annual_af = usbr_report.annual_af('ca/usbr_ca_palo_verde_diversion.csv')
    palo_verde_cu_annual_af = usbr_report.annual_af('ca/usbr_ca_palo_verde_consumptive_use.csv')
    bar_data = [{'data': palo_verde_diversion_annual_af, 'label': 'Diversion', 'color': 'darkmagenta'},
                {'data': palo_verde_cu_annual_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Palo Verde Diversion & Consumptive Use (Annual)',
                       xinterval=year_interval, ymin=200000, ymax=1100000, yinterval=100000,
                       ylabel='kaf',  format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(palo_verde_diversion_annual_af, 10, sub_plot=0)
    graph.running_average(palo_verde_cu_annual_af, 10, sub_plot=0)

    palo_verde_dam_release_annual_af = usbr_report.annual_af('releases/usbr_releases_palo_verde_dam.csv')
    graph.bars(palo_verde_dam_release_annual_af, sub_plot=1, title='Palo Verde Dam Release (Annual)',
               xinterval=year_interval, ymin=3500000, ymax=7000000, yinterval=500000, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)

    palo_verde_return_flows_annual = subtract_annual(palo_verde_diversion_annual_af, palo_verde_cu_annual_af,
                                                     1965, current_last_year)
    graph.bars(palo_verde_return_flows_annual, sub_plot=2, title='Palo Verde Return Flows(Annual)',
               xinterval=year_interval, ymin=200000, ymax=600000, yinterval=50000, color='darkmagenta',
               ylabel='kaf',  format_func=WaterGraph.format_kaf)

    bar_data = [{'data': palo_verde_dam_release_annual_af, 'label': 'Palo Verde Dam Release', 'color': 'firebrick'},
                {'data': palo_verde_return_flows_annual, 'label': 'Palo Verde Return Flows', 'color': 'darkmagenta'},
                ]
    graph.bars_stacked(bar_data, sub_plot=3, title='Flow below Palo Verde Dam with PV Return Flows (Annual)',
                       xinterval=year_interval, ymin=3500000, ymax=7000000, yinterval=500000, xlabel='Calendar Year',
                       ylabel='maf', format_func=WaterGraph.format_maf)
    flows_below_rock_annual = add_annual(palo_verde_dam_release_annual_af, palo_verde_return_flows_annual,
                                         1965, current_last_year)
    graph.running_average(flows_below_rock_annual, 10, sub_plot=3)

    graph.date_and_wait()


def release_delta(a, b, study_year):
    reach_a_release = flow_for_year(a, study_year)
    reach_b_release = flow_for_year(b, study_year)
    return reach_a_release - reach_b_release


def reach_inflow_minus_outflow(reach, study_year):
    try:
        # func_inflow = getattr(reach.inflow.module, reach.inflow.name)
        inflow = reach.inflow()
        inflow_yr = flow_for_year(inflow, study_year)

        outflow = reach.outflow()
        outflow_yr = flow_for_year(outflow, study_year)

        print(reach.name, " Inflow: ", inflow_yr, " Outflow:", outflow_yr, " CU & Loss: ", inflow_yr - outflow_yr)

        return inflow_yr - outflow_yr
    except AttributeError as e:
        print('reach_delta flow attribute missing: ', e)
    except TypeError as e:
        print('reach_delta flow attribute missing: ', e)

    return None


def model_hoover_to_imperial_extras():
    study_year = 2021

    parker_release = usbr_report.annual_af('releases/usbr_releases_parker_dam.csv')

    rock_release = usbr_report.annual_af('releases/usbr_releases_rock_dam.csv')
    reach_3a_cu_loss = release_delta(parker_release, rock_release, study_year)

    palo_verde_release = usbr_report.annual_af('releases/usbr_releases_palo_verde_dam.csv')
    reach_3b_cu_loss = release_delta(rock_release, palo_verde_release, study_year)

    # Yuma return flows cause gains here
    imperial_release = usbr_report.annual_af('releases/usbr_releases_imperial_dam.csv')
    laguna_release = usbr_report.annual_af('releases/usbr_releases_laguna_dam.csv')
    reach_4a_loss = release_delta(imperial_release, laguna_release, study_year)

    yuma_main_canal_gage = usgs.ca.yuma_main_canal_at_siphon_drop_PP(graph=False)
    yuma_main_annual_af = yuma_main_canal_gage.annual_af(water_year_month=1,
                                                         start_year=1964, end_year=current_last_year)
    # FIXME Pilot Knob and Yuma waste water cause gains in here
    nib_morelos_gage = usgs.lc.northern_international_border(graph=False)
    nib = nib_morelos_gage.annual_af(water_year_month=1)
    reach_5_loss = release_delta(imperial_release, nib, study_year)

    # USBR 24 month study numbers, some of these are generated (i.e. Davis evap) or may be from models
    lake_mead_side_inflow_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_mead_side_inflow.csv', multiplier=1000)

    lake_mead_evap_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_mead_evap_losses.csv', multiplier=1000)

    lake_mohave_side_inflow_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_mohave_side_inflow.csv', multiplier=1000)

    lake_mohave_evap_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_mohave_evap_losses.csv', multiplier=1000)

    lake_havasu_side_inflow_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_havasu_side_inflow.csv', multiplier=1000)

    lake_havasu_evap_af = usbr_report.annual_af(
        '/opt/dev/riverwar/data/USBR_24_Month/usbr_lake_havasu_evap_losses.csv', multiplier=1000)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, keyboardInterruptHandler)

    reaches = usbr.lc.initialize()
    usbr.lc.model(reaches, 2019, 2021, water_year_month=1)

    lake_mead_side_inflows()

    usbr.lc.lake_mead()
    usgs.lc.test()
    usbr.ca.palo_verde()
    usbr.az.colorado_river_indian_tribes()

    model_lower_colorado_1905_1964()

    # gage = usgs.nv.las_vegas_wash_below_lake_las_vegas()
    # monthly_af = gage.monthly_af(start_year=1975, end_year=1975)

    # usbr_rise.catalog()
    # usgs.az.test_returns()
    lake_powell_inflow()
    model_all_american()
    model_imperial_to_mexico()
    model_yuma_area()
    model_not_yuma_area()

    usgs.ca.test()
    usbr.az.colorado_river_indian_tribes()
    usbr.ca.test()
    usbr_lower_basin_states_total_use()
    usbr_glen_canyon_annual_release_af()
    model_glen_canyon()

    usgs.az.test()
    usgs.lc.test()
    usgs.ca.test()
    usgs.nv.test()
    usgs.co.test()

    usbr.nv.test()
    usbr.lc.test()
    usbr.uc.test()
    usbr.az.test()
    usbr.ca.test()
    usbr.uc.test()

    all_american_extras()
