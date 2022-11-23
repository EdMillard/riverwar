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
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES1 OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from sys import modules
from os import chdir
from source import usbr_report
from graph.water import WaterGraph
from basins import lc
from rw.state import State, state_by_abbreviation
from rw.util import add_annual, add_annuals, subtract_annual, replace_annual, reshape_annual_range, reach_for_name
from rw import util


current_last_year = 2021


class California(State):
    def __init__(self, module, reaches, options):
        State.__init__(self, 'California', 'ca',  module, reaches, options)

        module = modules[__name__]
        r3 = reach_for_name(reaches, 'Reach3')
        r3a = reach_for_name(reaches, 'Reach4')
        r3b = reach_for_name(reaches, 'Reach4')
        r4 = reach_for_name(reaches, 'Reach4')
        if options.yuma_users_moved_to_reach_4:
            r4a = reach_for_name(reaches, 'Reach4')
        else:
            r4a = reach_for_name(reaches, 'Reach5')

        r3.add_user(self.user(module, 'fort_mojave'))                 # 1999
        r3.add_user(self.user(None, 'city_of_needles'))               # 1964
        r3.add_user(self.user(None, 'southern_california_gas'))       # 2016
        r3.add_user(self.user(None, 'pacific_gas'))                   # 2016
        r3.add_user(self.user(None, 'havasu_water'))                  # 2016
        r3.add_user(self.user(None, 'vista_del_lago'))                # 2016
        r3.add_user(self.user(None, 'non_federal_subcontractors'))    # 2016
        r3.add_user(self.user(None, 'wetmore_mark'))                  # 2016-2019
        r3.add_user(self.user(None, 'williams_jerry'))                # 2016-2019
        r3.add_user(self.user(None, 'wetmore_kenneth'))               # 2016-2019
        r3.add_user(self.user(None, 'ppr_30_stephenson'))             # 2020
        r3.add_user(self.user(None, 'ppr_38_andrade'))                # 2020
        r3.add_user(self.user(None, 'ppr_40_cooper'))                 # 2021
        r3.add_user(self.user(module, 'chemehuevi'))                  # 1996
        r3.add_user(self.user(module, 'metropolitan', example=True))  # 1964
        r3.add_user(self.user(None, 'bureau_of_reclamation_parker'))  # 2017

        r3a.add_user(self.user(module, 'crit'))                       # 1973
        r3b.add_user(self.user(module, 'city_of_blythe'))             # 1964-1978
        r3b.add_user(self.user(module, 'east_blythe'))                # 1965-1977
        r3b.add_user(self.user(module, 'palo_verde', example=True))   # 1964
        r4.add_user(self.user(None, 'lake_enterprises'))              # 2016
        r4.add_user(self.user(None, 'bureau_of_land_management'))     # 2016
        r4a.add_user(self.user(module, 'yuma_project'))                # 1964
        r4a.add_user(self.user(None, 'fort_yuma'))                     # 2016
        r4a.add_user(self.user(None, 'yuma_island'))                   # 2016
        r4a.add_user(self.user(module, 'winterhaven'))                 # FIXME
        r4.add_user(self.user(module, 'imperial', example=True))      # 1964
        r4.add_user(self.user(None, 'coachella', example=True))       # 1964

        # FIXME, getting reaches out of this before 2016 will be complicated
        self.user(None, 'other_users_pumping')

    def test(self):
        self.orders_not_delivered(self, 'ca')
        data = [
            {'data': state_total_diversion(), 'y_min': 4000000, 'y_max': 6000000, 'y_interval': 500000},
            {'data': user_total_diversion()},
            {'y_min': -100, 'y_max': 1000, 'y_interval': 100},
            {'data': state_total_cu(), 'y_min': 3500000, 'y_max': 5500000, 'y_interval': 500000},
            {'data': user_total_cu()},
            {'y_min': -1000, 'y_max': 60000, 'y_interval': 5000},
        ]
        util.state_total_vs_user_total_graph('CA', data)

        total()
        metropolitan()
        coachella()
        imperial_irrigation_district()
        palo_verde()
        yuma_project()

    @staticmethod
    def orders_not_delivered(self, state_code, show_graph=True, show_error=False):
        year_interval = 3

        orders_not_delivered_af = usbr_report.annual_af('orders/'+state_code+'/total_ordered_but_not_diverted.csv',
                                                        water_year_month=1)
        diverted_by_others_af = usbr_report.annual_af('orders/'+state_code+'/total_diverted_by_others.csv',
                                                      water_year_month=1)
        diverted_to_storage_af = usbr_report.annual_af('orders/'+state_code+'/total_diverted_to_storage.csv',
                                                       water_year_month=1)
        satisfaction_of_treaty_af = usbr_report.annual_af('orders/'+state_code+'/total_satisfaction_of_treaty.csv',
                                                          water_year_month=1)
        excess_of_treaty_af = usbr_report.annual_af('orders/'+state_code+'/total_excess_of_treaty.csv',
                                                    water_year_month=1)

        diverted_total_af = add_annuals([diverted_by_others_af,
                                         diverted_to_storage_af,
                                         satisfaction_of_treaty_af,
                                         excess_of_treaty_af])
        diff = subtract_annual(orders_not_delivered_af, diverted_total_af)

        if show_graph:
            if show_error:
                graph = WaterGraph(nrows=6)
                show_tick_labels = False
            else:
                graph = WaterGraph(nrows=5)
                show_tick_labels = True

            graph.bars(orders_not_delivered_af, sub_plot=0, title='California Total Orders Not Delivered',
                       ymin=0, ymax=500000, yinterval=50000,
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_by_others_af, sub_plot=1,
                       ymin=0, ymax=125000, yinterval=25000, title='Diverted by Others',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_to_storage_af, sub_plot=2,
                       ymin=0, ymax=250000, yinterval=50000, title='Diverted to Storage',
                       xlabel='', x_labels=False,  xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(satisfaction_of_treaty_af, sub_plot=3,
                       ymin=0, ymax=300000, yinterval=50000, title='Delivered in Satisfaction of Treaty',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(excess_of_treaty_af, sub_plot=4,
                       ymin=0, ymax=100000, yinterval=20000, title='Delivered in Excess of Treaty',
                       xlabel='',  x_labels=show_tick_labels, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            if show_error:
                graph.bars(diff, sub_plot=5,
                           ymin=-100000, ymax=100000, yinterval=50000,
                           title='Diff Orders Not Diverted, Diverted/Delivered',
                           xlabel='',  xinterval=year_interval, color='firebrick',
                           ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.date_and_wait()

        orders_not_delivered_af = usbr_report.annual_af('orders/'+state_code+'/imperial_ordered_but_not_diverted.csv',
                                                        water_year_month=1)
        diverted_by_others_af = usbr_report.annual_af('orders/'+state_code+'/imperial_diverted_by_others.csv',
                                                      water_year_month=1)
        diverted_to_storage_af = usbr_report.annual_af('orders/'+state_code+'/imperial_diverted_to_storage.csv',
                                                       water_year_month=1)
        satisfaction_of_treaty_af = usbr_report.annual_af('orders/'+state_code+'/imperial_satisfaction_of_treaty.csv',
                                                          water_year_month=1)
        excess_of_treaty_af = usbr_report.annual_af('orders/'+state_code+'/imperial_excess_of_treaty.csv',
                                                    water_year_month=1)
        diverted_total_af = add_annuals([diverted_by_others_af,
                                         diverted_to_storage_af,
                                         satisfaction_of_treaty_af,
                                         excess_of_treaty_af])
        diff = subtract_annual(orders_not_delivered_af, diverted_total_af)
        if show_graph:
            if show_error:
                graph = WaterGraph(nrows=6)
                show_tick_labels = False
            else:
                graph = WaterGraph(nrows=5)
                show_tick_labels = True
            graph.bars(orders_not_delivered_af, sub_plot=0, title='Imperial Irrigation Orders Not Delivered',
                       ymin=0, ymax=350000, yinterval=50000,
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_by_others_af, sub_plot=1,
                       ymin=0, ymax=100000, yinterval=25000, title='Diverted by Others',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_to_storage_af, sub_plot=2,
                       ymin=0, ymax=125000, yinterval=25000, title='Diverted to Storage',
                       xlabel='', x_labels=False,  xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(satisfaction_of_treaty_af, sub_plot=3,
                       ymin=0, ymax=250000, yinterval=50000, title='Delivered in Satisfaction of Treaty',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(excess_of_treaty_af, sub_plot=4,
                       ymin=0, ymax=100000, yinterval=20000, title='Delivered in Excess of Treaty',
                       xlabel='', x_labels=show_tick_labels, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            if show_error:
                graph.bars(diff, sub_plot=5,
                           ymin=-100000, ymax=100000, yinterval=50000,
                           title='Diff Orders Not Diverted, Diverted/Delivered',
                           xlabel='',  xinterval=year_interval, color='firebrick',
                           ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.date_and_wait()

        orders_not_delivered_af = usbr_report.annual_af(
            'orders/' + state_code + '/palo_verde_ordered_but_not_diverted.csv',
            water_year_month=1)
        diverted_by_others_af = usbr_report.annual_af('orders/' + state_code + '/palo_verde_diverted_by_others.csv',
                                                      water_year_month=1)
        diverted_to_storage_af = usbr_report.annual_af('orders/' + state_code + '/palo_verde_diverted_to_storage.csv',
                                                       water_year_month=1)
        satisfaction_of_treaty_af = usbr_report.annual_af(
            'orders/' + state_code + '/palo_verde_satisfaction_of_treaty.csv',
            water_year_month=1)
        excess_of_treaty_af = usbr_report.annual_af('orders/' + state_code + '/palo_verde_excess_of_treaty.csv',
                                                    water_year_month=1)
        diverted_total_af = add_annuals([diverted_by_others_af,
                                         diverted_to_storage_af,
                                         satisfaction_of_treaty_af,
                                         excess_of_treaty_af])
        diff = subtract_annual(orders_not_delivered_af, diverted_total_af)
        if show_graph:
            if show_error:
                graph = WaterGraph(nrows=6)
                show_tick_labels = False
            else:
                graph = WaterGraph(nrows=5)
                show_tick_labels = True
            graph.bars(orders_not_delivered_af, sub_plot=0, title='Palo Verde Orders Not Delivered',
                       ymin=0, ymax=60000, yinterval=5000,
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_by_others_af, sub_plot=1,
                       ymin=0, ymax=35000, yinterval=5000, title='Diverted by Others',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_to_storage_af, sub_plot=2,
                       ymin=0, ymax=50000, yinterval=5000, title='Diverted to Storage',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(satisfaction_of_treaty_af, sub_plot=3,
                       ymin=0, ymax=10000, yinterval=1000, title='Delivered in Satisfaction of Treaty',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(excess_of_treaty_af, sub_plot=4,
                       ymin=0, ymax=10000, yinterval=1000, title='Delivered in Excess of Treaty',
                       xlabel='', x_labels=show_tick_labels, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            if show_error:
                graph.bars(diff, sub_plot=5,
                           ymin=-100000, ymax=100000, yinterval=50000,
                           title='Diff Orders Not Diverted, Diverted/Delivered',
                           xlabel='', xinterval=year_interval, color='firebrick',
                           ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.date_and_wait()

        orders_not_delivered_af = usbr_report.annual_af(
            'orders/' + state_code + '/metropolitan_ordered_but_not_diverted.csv', water_year_month=1)
        diverted_by_others_af = usbr_report.annual_af('orders/' + state_code + '/metropolitan_diverted_by_others.csv',
                                                      water_year_month=1)
        diverted_to_storage_af = usbr_report.annual_af('orders/' + state_code + '/metropolitan_diverted_to_storage.csv',
                                                       water_year_month=1)
        satisfaction_of_treaty_af = usbr_report.annual_af(
            'orders/' + state_code + '/metropolitan_satisfaction_of_treaty.csv', water_year_month=1)
        excess_of_treaty_af = usbr_report.annual_af('orders/' + state_code + '/metropolitan_excess_of_treaty.csv',
                                                    water_year_month=1)

        diverted_total_af = add_annuals([diverted_by_others_af,
                                         diverted_to_storage_af,
                                         satisfaction_of_treaty_af,
                                         excess_of_treaty_af])
        diff = subtract_annual(orders_not_delivered_af, diverted_total_af)

        if show_graph:
            if show_error:
                graph = WaterGraph(nrows=3)
                show_tick_labels = False
            else:
                graph = WaterGraph(nrows=2)
                show_tick_labels = True
            graph.bars(orders_not_delivered_af, sub_plot=0, title='Metropolitan Total Orders Not Delivered',
                       ymin=0, ymax=70000, yinterval=10000,
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_to_storage_af, sub_plot=1,
                       ymin=0, ymax=70000, yinterval=10000, title='Diverted to Storage',
                       xlabel='', x_labels=show_tick_labels, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            if show_error:
                graph.bars(diff, sub_plot=2,
                           ymin=-100000, ymax=100000, yinterval=50000,
                           title='Diff Orders Not Diverted, Diverted/Delivered',
                           xlabel='', xinterval=year_interval, color='firebrick',
                           ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.date_and_wait()


def total():
    # This graph will be wrong because Brock is mishandled by Bureau AR's in Diversion Total
    # Use the special cased revised graph in usbr_ca_total() instead
    # usbr.util.diversion_vs_consumptive('ca', 'total', 'California',
    #                               ymin1=3500000, ymax1=6000000,
    #                               ymin2=350000, ymax2=750000, yinterval2=50000)
    start_year = 1964
    end_year = current_last_year
    year_interval = 4

    graph = WaterGraph(nrows=2)

    # Diversion
    diversion_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_diversion.csv')
    diversion_annual_af = usbr_report.monthly_to_water_year(diversion_monthly_af, water_year_month=1)
    # Brock
    brock_diversion_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_brock_diversion.csv')
    brock_diversion_annual_af = usbr_report.monthly_to_water_year(brock_diversion_monthly_af, water_year_month=1)
    # Need to remove 2010 brock diversion, its correctly incorporated to CA Total Diversion in 2010 AR
    brock_diversion_annual_af = reshape_annual_range(brock_diversion_annual_af, 2011, end_year)
    brock_diversion_annual_af = reshape_annual_range(brock_diversion_annual_af, start_year, end_year)
    # Diversion Revised with Block
    diversion_revised_annual_af = add_annual(diversion_annual_af, brock_diversion_annual_af)
    cu_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_total_consumptive_use.csv')
    cu_annual_af = usbr_report.monthly_to_water_year(cu_monthly_af, water_year_month=1)
    returns_annual_af = subtract_annual(diversion_revised_annual_af, cu_annual_af)

    measured_returns_annual_af = usbr_report.annual_af('ca/usbr_ca_total_measured_returns.csv')
    measured_returns_annual_af = reshape_annual_range(measured_returns_annual_af, start_year, end_year)
    unmeasured_returns_annual_af = usbr_report.annual_af('ca/usbr_ca_total_unmeasured_returns.csv')
    unmeasured_returns_annual_af = reshape_annual_range(unmeasured_returns_annual_af, start_year, end_year)
    graph.bars(returns_annual_af, sub_plot=1, title='California Return Flows Computed w Brock Revision (Annual)',
               ymin=350000, ymax=750000, yinterval=50000, label='Computed Returns (Revised Diversion minus CU)',
               xlabel='',  xinterval=year_interval, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    bar_data = [{'data': measured_returns_annual_af, 'label': 'Measured Returns from AR', 'color': 'indigo'},
                {'data': unmeasured_returns_annual_af, 'label': 'Unmeasured Returns from AR', 'color': 'violet'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='California Return Flows Computed w Brock Revision (Annual)',
                       ymin=350000, ymax=750000, yinterval=50000,
                       xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=True)
    # graph.plot(diversion_monthly_af, sub_plot=0, title='California Total Diversion (Monthly)',
    #            xinterval=year_interval, ymin=100000, ymax=700000, yinterval=100000, color='darkmagenta',
    #            ylabel='kaf', format_func=WaterGraph.format_kaf)
    # graph.plot(cu_monthly_af, sub_plot=0, title='California Total Diversion & Consumptive Use (Monthly)',
    #            xinterval=year_interval, ymin=100000, ymax=700000, yinterval=100000, color='firebrick',
    #            ylabel='kaf', format_func=WaterGraph.format_kaf)
    # graph.bars(diversion_annual_af, sub_plot=1, title='California Total Diversion (Annual)',
    #            ymin=3600000, ymax=8000000, yinterval=1000000,
    #            xlabel='',  xinterval=year_interval, color='darkmagenta',
    #            ylabel='maf', format_func=WaterGraph.format_maf)
    bar_data = [{'data': diversion_revised_annual_af, 'label': 'Diversion w Brock Revision', 'color': 'violet'},
                {'data': diversion_annual_af, 'label': 'Diversion from Annual Reports', 'color': 'darkmagenta'},
                {'data': cu_annual_af, 'label': 'Consumptive Use from AR', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title=' CA Revised Diversion & Consumptive Use Totals (Annual)',
                       ymin=3600000, ymax=6000000, yinterval=200000,
                       xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf, vertical=False)
    graph.running_average(diversion_revised_annual_af, 10, sub_plot=0)
    graph.running_average(cu_annual_af, 10, sub_plot=0)

    # Consumptive Use
    # graph.bars(cu_annual_af, sub_plot=2, title='California Total Consumptive Use (Annual)',
    #           ymin=3600000, ymax=6000000, yinterval=200000,
    #          xlabel='',  xinterval=year_interval, color='firebrick',
    #           ylabel='maf', format_func=WaterGraph.format_maf)
    # graph.plot(measured_returns_monthly_af, sub_plot=2, title='California Measured & Unmeasured Returns (Monthly)',
    #            xinterval=year_interval, ymax=100000, yinterval=50000, color='firebrick',
    #            ylabel='kaf', format_func=WaterGraph.format_kaf)
    # graph.plot(unmeasured_returns_monthly_af, sub_plot=2,
    #            xinterval=year_interval, ymax=100000, yinterval=50000, color='darkmagenta',
    #           ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


def state_total_diversion():
    annuals = [usbr_report.annual_af('ca/usbr_ca_total_diversion.csv'),
               usbr_report.annual_af('ca/usbr_ca_imperial_irrigation_brock_diversion.csv')
               ]
    return add_annuals(annuals)


def state_total_cu():
    return usbr_report.annual_af('ca/usbr_ca_total_consumptive_use.csv')


def state_total_returns():
    return usbr_report.annual_af('ca/usbr_ca_total_returns.csv')


def user_total_diversion():
    california = state_by_abbreviation('ca')
    return california.total_user_diversion()


def user_total_cu():
    california = state_by_abbreviation('ca')
    return california.total_user_cu()


def user_total_returns():
    california = state_by_abbreviation('ca')
    return california.total_user_returns()


def yuma_area_returns():
    data = [{'data': imperial_returns(), 'label': 'Imperial', 'color': 'maroon'},
            {'data': yuma_project_returns(), 'label': 'Yuma Project', 'color': 'firebrick'},
            {'data': coachella_returns(), 'label': 'Coachella', 'color': 'lightcoral'}
            ]
    return data


def not_yuma_area_returns():
    data = [{'data': palo_verde_returns(), 'label': 'Palo Verde', 'color': 'maroon'},
            {'data': metropolitan_returns(), 'label': 'Metropolitan', 'color': 'firebrick'}]

    # diversions = [metropolitan_diversion, metropolitan_san_diego_exchange, metropolitan_supplemental]
    # metropolitan_total_diversion = add_annuals(diversions)

    # metropolitan_cu = usbr_report.annual_af('ca/usbr_ca_metropolitan_consumptive_use.csv')
    # metropolitan_returns = subtract_annual(metropolitan_total_diversion, metropolitan_cu)

    return data


def fort_mojave_diversion(water_year_month=1):
    data = [
        usbr_report.annual_af('ca/usbr_ca_fort_mojave_pumped_diversion.csv', water_year_month=water_year_month),
        usbr_report.annual_af('ca/usbr_ca_fort_mojave_well_diversion.csv', water_year_month=water_year_month)
    ]
    return add_annuals(data)


def fort_mojave_cu(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_fort_mojave_consumptive_use.csv', water_year_month=water_year_month)


def fort_mojave_returns(water_year_month=1):
    return subtract_annual(fort_mojave_diversion(water_year_month=water_year_month),
                           fort_mojave_cu(water_year_month=water_year_month))


def metropolitan_annotate(graph, sub_plot=0):
    graph.annotate_horizontal_line(550000, 'p4 550 maf 1930-1946', sub_plot=sub_plot)
    graph.annotate_horizontal_line(1100000, 'p5a 550 maf 1930-1931', sub_plot=sub_plot)
    graph.annotate_horizontal_line(1220000, 'p5b 112 maf 1933\nSan Diego', sub_plot=sub_plot)


def metropolitan():
    start_year = 1964
    year_interval = 3
    whitsett_monthly_af = usbr_report.load_monthly_csv('ca/usbr_ca_metropolitan_diversion.csv')
    # graph = WaterGraph.plot(whitsett_monthly_af,
    #                               'Lake Havasu Metropolitan Whitsett Pumping Plant (Monthly)',
    #                               ylabel='kaf', ymin=0, ymax=120000, yinterval=10000, color='firebrick',
    #                               format_func=WaterGraph.format_kaf)
    # graph.date_and_wait()

    whitsett_annual_af = usbr_report.monthly_to_water_year(whitsett_monthly_af, water_year_month=1)
    graph = WaterGraph(nrows=3)
    graph.bars(whitsett_annual_af, sub_plot=0,
               title='Lake Havasu Metropolitan Whitsett Pumping Plant Diversion (Annual)',
               ymin=0, ymax=1350000, yinterval=100000,
               xlabel='Calendar Year',  xinterval=year_interval, color='firebrick',
               ylabel='maf',  format_func=WaterGraph.format_maf)
    metropolitan_annotate(graph, sub_plot=0)

    whitsett_san_diego_monthly_af = usbr_report.load_monthly_csv(
        'usbr_lake_havasu_met_for_san_diego_whitsett_pumps.csv')
    graph.plot(whitsett_san_diego_monthly_af, sub_plot=1,
               title='Lake Havasu Metropolitan San Diego Exchange Whitsett Pumping Plant Diversion (Monthly)',
               yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    whitsett_san_diego_annual_af = usbr_report.monthly_to_calendar_year(whitsett_san_diego_monthly_af)
    bar_data = [{'data': whitsett_annual_af, 'label': 'Metropolitan', 'color': 'firebrick'},
                {'data': whitsett_san_diego_annual_af, 'label': 'San Diego Exchange', 'color': 'goldenrod'},
                ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Lake Havasu Metropolitan + San Diego Exchange (Annual)',
                       ymin=400000, ymax=1400000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
    metropolitan_annotate(graph, sub_plot=2)
    graph.date_and_wait()

    ics = lc.lake_mead_load_ics()
    ics_ca_delta = ics['CA Delta']

    ics_ca_withdrawals = usbr_report.negative_values(ics_ca_delta)
    ics_ca_withdrawals = graph.reshape_annual_range(ics_ca_withdrawals, start_year, current_last_year)

    ics_ca_deposits = usbr_report.positive_values(ics_ca_delta)
    ics_ca_deposits = graph.reshape_annual_range(ics_ca_deposits, start_year, current_last_year)

    bar_data = [{'data': whitsett_annual_af, 'label': 'Metropolitan Diversion', 'color': 'firebrick'},
                {'data': ics_ca_withdrawals, 'label': 'CA ICS Withdrawals', 'color': 'maroon'},
                {'data': ics_ca_deposits, 'label': 'CA ICS Deposits', 'color': 'mediumseagreen'},
                {'data': whitsett_san_diego_annual_af, 'label': 'San Diego Exchange', 'color': 'goldenrod'}
                ]

    graph = WaterGraph()
    graph.bars_stacked(bar_data, sub_plot=0,
                       title='Lake Havasu Metropolitan Diversion + San Diego Exchange, CA ICS (Annual)',
                       ylabel='kaf', ymin=400000, ymax=1400000, yinterval=50000,
                       xlabel='Calendar Year', xinterval=3, format_func=WaterGraph.format_kaf)
    metropolitan_annotate(graph, sub_plot=0)
    graph.date_and_wait()


def metropolitan_diversion(water_year_month=1):
    data = [usbr_report.annual_af('ca/usbr_ca_metropolitan_diversion.csv', water_year_month=water_year_month),
            usbr_report.annual_af('ca/usbr_ca_metropolitan_san_diego_exchange.csv', water_year_month=water_year_month),
            usbr_report.annual_af('ca/usbr_ca_metropolitan_supplemental.csv', water_year_month=water_year_month),
            usbr_report.annual_af('ca/usbr_ca_metropolitan_for_snwa.csv', water_year_month=water_year_month),
            ]
    return add_annuals(data)


def metropolitan_cu(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_metropolitan_consumptive_use.csv', water_year_month=water_year_month)


def metropolitan_returns(water_year_month=1):
    return subtract_annual(metropolitan_diversion(water_year_month=water_year_month),
                           metropolitan_cu(water_year_month=water_year_month))


def chemehuevi_diversion(water_year_month=1):
    diversion = usbr_report.annual_af('ca/usbr_ca_chemehuevi_diversion.csv', water_year_month=water_year_month)
    domestic = usbr_report.annual_af('ca/usbr_ca_chemehuevi_domestic_diversion.csv', water_year_month=water_year_month)
    return add_annual(diversion, domestic)


def chemehuevi_cu(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_chemehuevi_consumptive_use.csv', water_year_month=water_year_month)


def chemehuevi_returns():
    return subtract_annual(chemehuevi_diversion(), chemehuevi_diversion())


def city_of_blythe_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_city_of_blythe_diversion.csv', water_year_month=water_year_month)


def city_of_blythe_cu(water_year_month=1):
    return city_of_blythe_diversion(water_year_month)


def city_of_blythe_returns():
    # City of Blythe has no return flows so cu is the same as diversion
    return subtract_annual(city_of_blythe_diversion(), city_of_blythe_cu())


def east_blythe_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_east_blythe_diversion.csv', water_year_month=water_year_month)


def east_blythe_cu(water_year_month=1):
    return east_blythe_diversion(water_year_month)


def east_blythe_returns():
    #  East_Blythe has no return flows so cu is the same as diversion
    return subtract_annual(east_blythe_diversion(), east_blythe_cu())


def palo_verde_annotate(graph, sub_plot=0):
    graph.annotate_horizontal_line(219780, 'PPR 1, 219.78 kaf, 1877\n3(b) 16,000 acres, 1933', sub_plot=sub_plot)


def palo_verde():
    year_interval = 3
    graph = WaterGraph(nrows=2)

    # Diversion
    monthly_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_palo_verde_diversion.csv')
    graph.plot(monthly_diversion_af, sub_plot=0, title='Palo Verde Diversion & Consumptive Use (Monthly)',
               xinterval=year_interval, ymax=125000, yinterval=50000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    monthly_cu_af = usbr_report.load_monthly_csv('ca/usbr_ca_palo_verde_consumptive_use.csv')
    graph.plot(monthly_cu_af, sub_plot=0,
               xinterval=year_interval, ymax=125000, yinterval=50000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)
    # graph.bars(annual_diversion_af, sub_plot=1, title='Imperial Irrigation District Diversion (Annual)',
    #            ymin=2200000, ymax=3300000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #            ylabel='maf', format_func=WaterGraph.format_maf)

    # Consumptive Use
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)
    # graph.bars(annual_cu_af, sub_plot=3, title='Imperial Irrigtion Consumptive Use',
    #            ymin=2200000, ymax=3400000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #           ylabel='maf', format_func=WaterGraph.format_maf)

    bar_data = [{'data': annual_diversion_af, 'label': 'Palo Verde Diversion', 'color': 'darkmagenta'},
                {'data': annual_cu_af, 'label': 'Palo Verde Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Palo Verde Diversion & Consumptive Use (Annual)',
                       ymin=0, ymax=1100000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    palo_verde_annotate(graph, 1)
    graph.date_and_wait()


def palo_verde_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_palo_verde_diversion.csv', water_year_month=water_year_month)


def palo_verde_cu(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_palo_verde_consumptive_use.csv', water_year_month=water_year_month)


def palo_verde_returns(water_year_month=1):
    return subtract_annual(palo_verde_diversion(water_year_month=water_year_month),
                           palo_verde_cu(water_year_month=water_year_month))


def crit_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_crit_pumped_diversion.csv', water_year_month=water_year_month)


def crit_cu(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_crit_consumptive_use.csv', water_year_month=water_year_month)


def crit_returns():
    # CRIT has no return flows so cu is the same as diversion
    return subtract_annual(crit_diversion(), crit_cu())


def imperial_irrigation_district():
    start_year = 1964
    year_interval = 3
    graph = WaterGraph(nrows=3)

    # Diversion
    monthly_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)

    monthly_cu_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    monthly_brock_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_imperial_irrigation_brock_diversion.csv')
    annual_brock_diversion_af = usbr_report.monthly_to_water_year(monthly_brock_diversion_af, water_year_month=1)

    graph.plot(monthly_diversion_af, sub_plot=0, title='Imperial Diversion (Monthly)',
               xinterval=year_interval, yinterval=50000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=1,
               xinterval=year_interval, yinterval=50000, color='firebrick',
               title='Imperial Consumptive Use (Monthly)',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_brock_diversion_af, sub_plot=2, title='Imperial Diversion from Brock (Monthly)',
               xinterval=1, yinterval=5000, color='lightcoral',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()

    # graph.bars(annual_diversion_af, sub_plot=1, title='Imperial Irrigation District Diversion (Annual)',
    #            ymin=2200000, ymax=3300000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #            ylabel='maf', format_func=WaterGraph.format_maf)

    # Consumptive Use
    # graph.bars(annual_cu_af, sub_plot=3, title='Imperial Irrigtion Consumptive Use',
    #            ymin=2200000, ymax=3400000, yinterval=100000,
    #            xlabel='',  xinterval=year_interval, color='firebrick',
    #           ylabel='maf', format_func=WaterGraph.format_maf)

    annual_brock_diversion_af = graph.reshape_annual_range(annual_brock_diversion_af, start_year, current_last_year)
    # annual_brock_diversion_negative = np.zeros(len(annual_brock_diversion_af), [('dt', 'i'), ('val', 'f')])
    # annual_brock_diversion_negative['dt'] = annual_cu_af['dt']
    # annual_brock_diversion_negative['val'] = np.negative(annual_brock_diversion_af['val'])
    annual_total_diversion_af = add_annual(annual_diversion_af, annual_brock_diversion_af)
    graph = WaterGraph()
    bar_data = [
                {'data': annual_diversion_af, 'label': 'Diversion without Brock', 'color': 'darkmagenta'},
                {'data': annual_brock_diversion_af, 'label': 'Diversion with Brock ', 'color': 'm'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0, title='USBR AR Imperial Diversion + Brock Diversion (Annual)',
                       ymin=2300000, ymax=3300000, yinterval=100000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_total_diversion_af, 10, sub_plot=0)

    # graph.bars(annual_diversion_af, sub_plot=0, title='USBR AR Imperial Diversions and Consumptive Use (Annual)',
    #            ymin=2300000, ymax=3300000, yinterval=100000, color='darkmagenta', label='Diversion',
    #            xlabel='', xinterval=year_interval,
    #           ylabel='maf', format_func=WaterGraph.format_maf)
    bar_data = [
                {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                # {'data': annual_brock_diversion_negative, 'label': 'Brock Diversions', 'color': 'lightcoral'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Imperial Diversion with Brock & Consumptive Use (Annual)',
                       ymin=2300000, ymax=3300000, yinterval=100000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(annual_cu_af, 10, sub_plot=0)
    graph.annotate_horizontal_line(2600000, 'PPR 3(a), 2.6 maf, 1901 ')
    graph.date_and_wait()


def brock_diversion(water_year_month=1):
    brock_annual_af = usbr_report.annual_af('ca/usbr_ca_imperial_irrigation_brock_diversion.csv',
                                            water_year_month=water_year_month)
    return brock_annual_af


def imperial_diversion(water_year_month=1):
    annuals = [
        usbr_report.annual_af('ca/usbr_ca_imperial_irrigation_diversion.csv', water_year_month=water_year_month),
        brock_diversion(water_year_month),
        usbr_report.annual_af('ca/usbr_ca_imperial_irrigation_sdcwa_mitigation_diversion.csv',
                              water_year_month=water_year_month)
    ]
    return add_annuals(annuals)


def imperial_cu(water_year_month=1):
    cu = usbr_report.annual_af('ca/usbr_ca_imperial_irrigation_consumptive_use.csv', water_year_month=water_year_month)
    cu_sdcwa = usbr_report.annual_af('ca/usbr_ca_imperial_irrigation_sdcwa_consumptive_use.csv',
                                     water_year_month=water_year_month)
    return add_annuals([cu, cu_sdcwa])


def imperial_returns(water_year_month=1):
    return subtract_annual(imperial_diversion(water_year_month=water_year_month),
                           imperial_cu(water_year_month=water_year_month))


def coachella():
    year_interval = 3
    graph = WaterGraph(nrows=2)

    # Diversion
    monthly_diversion_af = usbr_report.load_monthly_csv('ca/usbr_ca_coachella_diversion.csv')
    annual_diversion_af = usbr_report.monthly_to_water_year(monthly_diversion_af, water_year_month=1)
    monthly_cu_af = usbr_report.load_monthly_csv('ca/usbr_ca_coachella_consumptive_use.csv')
    annual_cu_af = usbr_report.monthly_to_water_year(monthly_cu_af, water_year_month=1)

    graph.plot(monthly_diversion_af, sub_plot=0, title='Coachella Diversion (Monthly)',
               xinterval=year_interval, yinterval=5000, color='darkmagenta',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    graph.plot(monthly_cu_af, sub_plot=0, title='',
               xinterval=year_interval, yinterval=5000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bar_data = [
                {'data': annual_diversion_af, 'label': 'Diversions', 'color': 'darkmagenta'},
                {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Coachella Diversion and Consumptive Use (Annual)',
                       ymin=0, ymax=600000, yinterval=50000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.annotate_horizontal_line(100000, '100 kaf\n1987', sub_plot=1)
    graph.running_average(annual_cu_af, 10, sub_plot=1)
    graph.running_average(annual_diversion_af, 10, sub_plot=1)

    graph.date_and_wait()


def coachella_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_coachella_diversion.csv', water_year_month=water_year_month)


def coachella_cu(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_coachella_consumptive_use.csv', water_year_month=water_year_month)


def coachella_returns(water_year_month=1):
    return subtract_annual(coachella_diversion(water_year_month=water_year_month),
                           coachella_cu(water_year_month=water_year_month))


# def usbr_ca_yuma_project(graph, sub_plot=0):
#    graph.annotate_horizontal_line(550000, 'p4 550 maf 1930-1946', offset_percent=0, sub_plot=sub_plot)
#    Reservation Division PPR #2 1905 not to exceed 25,000 acres, no acre-feet listed
def yuma_project():
    year_interval = 3
    graph = WaterGraph(nrows=4)

    # CA Yuma Project, Indian, Bard and Unassigned returns
    yuma_project_indian_diversion_annual_af = usbr_report.annual_af('ca/usbr_ca_yuma_project_indian_unit_diversion.csv')
    yuma_project_bard_diversion_annual_af = usbr_report.annual_af('ca/usbr_ca_yuma_project_bard_unit_diversion.csv')
    yuma_project_returns_annual_af = usbr_report.annual_af('ca/usbr_ca_yuma_project_returns.csv')

    bar_data = [
        {'data': yuma_project_indian_diversion_annual_af, 'label': 'Yuma Project Bard Diversion', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0, title='Yuma Project Indian Diversion (Annual)',
                       ymin=0, ymax=65000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_project_indian_diversion_annual_af, 10, sub_plot=0)

    bar_data = [
        {'data': yuma_project_bard_diversion_annual_af, 'label': 'Yuma Project Bard Diversion', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='USBR Yuma Project Bard Diversion (Annual)',
                       ymin=0, ymax=65000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_project_bard_diversion_annual_af, 10, sub_plot=1)

    yuma_project_total_diversion_annual_af = add_annual(yuma_project_indian_diversion_annual_af,
                                                        yuma_project_bard_diversion_annual_af)
    yuma_project_total_cu_annual_af = subtract_annual(yuma_project_total_diversion_annual_af,
                                                      yuma_project_returns_annual_af)

    bar_data = [
        {'data': yuma_project_total_diversion_annual_af, 'label': 'Total Diversion', 'color': 'darkmagenta'},
        {'data': yuma_project_total_cu_annual_af, 'label': 'Total Consumptive Use', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=2, title='Yuma Project Total Diversion & Consumptive Use (Annual)',
                       ymin=0, ymax=110000, yinterval=10000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_project_total_diversion_annual_af, 10, sub_plot=2)
    graph.running_average(yuma_project_total_cu_annual_af, 10, sub_plot=2)

    bar_data = [
        {'data': yuma_project_returns_annual_af, 'label': 'Returns', 'color': 'darkmagenta'},
    ]
    graph.bars_stacked(bar_data, sub_plot=3, title='Yuma Project Unassigned Returns (Annual)',
                       ymin=0, ymax=50000, yinterval=5000,
                       xlabel='', xinterval=year_interval,
                       ylabel='kaf', format_func=WaterGraph.format_kaf, vertical=False)
    graph.running_average(yuma_project_returns_annual_af, 10, sub_plot=3)
    graph.date_and_wait()


def yuma_project_diversion(water_year_month=1):
    indian_diversion_annual_af = usbr_report.annual_af(
        'ca/usbr_ca_yuma_project_indian_unit_diversion.csv',  water_year_month=water_year_month)
    indian_domestic_diversion_annual_af = usbr_report.annual_af(
        'ca/usbr_ca_yuma_project_indian_unit_domestic_diversion.csv', water_year_month=water_year_month)
    bard_diversion_annual_af = usbr_report.annual_af(
        'ca/usbr_ca_yuma_project_bard_unit_diversion.csv', water_year_month=water_year_month)
    return add_annuals([indian_diversion_annual_af, indian_domestic_diversion_annual_af, bard_diversion_annual_af])


def yuma_project_indian_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_yuma_project_indian_unit_diversion.csv', water_year_month=water_year_month)


def yuma_project_bard_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_yuma_project_bard_unit_diversion.csv', water_year_month=water_year_month)


def yuma_project_cu(water_year_month=1):
    cu1 = subtract_annual(yuma_project_diversion(water_year_month=water_year_month),
                          yuma_project_returns(water_year_month=water_year_month))
    cu2 = usbr_report.annual_af('ca/usbr_ca_yuma_project_sum_consumptive_use.csv', water_year_month=water_year_month)
    replace_annual(cu1, cu2)
    return cu1


def yuma_project_returns(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_yuma_project_returns.csv', water_year_month=water_year_month)


def winterhaven_diversion(water_year_month=1):
    return usbr_report.annual_af('ca/usbr_ca_winterhaven_diversion.csv', water_year_month=water_year_month)


def winterhaven_cu(water_year_month=1):
    return winterhaven_diversion(water_year_month)


def winterhaven_returns():
    return subtract_annual(winterhaven_diversion(), winterhaven_diversion())


if __name__ == '__main__':
    chdir('../')
    test_model = lc.Model('test')
    test_model.initialize()
    state = test_model.state_by_name('California')
    state.test()
