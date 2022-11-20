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
from sys import modules
from os import chdir
from source import usbr_report
from graph.water import WaterGraph
from basins import lc
from rw.lake import Lake
import usgs
from rw.util import subtract_annual, reach_for_name
from rw.state import State


class Mexico(State):
    def __init__(self, module, reaches, options):
        State.__init__(self, 'Mexico', 'mx', module, reaches, options)

        module = modules[__name__]
        r5 = reach_for_name(reaches, 'Reach5')
        r5.add_user(self.user(module, 'mexico', example=True))

    def test(self):
        mexico()


class Morelos(Lake):
    def __init__(self, water_month):
        Lake.__init__(self, 'morelos', water_month)

    def inflow(self, year_begin, year_end):
        nib_morelos_gage = usgs.lc.northern_international_border(graph=False)
        nib = nib_morelos_gage.annual_af(water_year_month=self.water_year_month,
                                         start_year=year_begin, end_year=year_end)
        return nib

    def release(self, year_begin, year_end):
        return None

    def storage(self):
        return None

    def evaporation(self, year_begin, year_end):
        return None


def yuma_area_returns():
    data = []
    minute_242_returns = usbr_report.annual_af('mx/usbr_mx_minute_242_bypass.csv')
    data.append({'data': minute_242_returns, 'label': 'Minute 242', 'color': 'maroon'})
    return data


def mexico():
    year_interval = 3

    graph = WaterGraph(nrows=3)

    treaty_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_satisfaction_of_treaty.csv')
    treaty_annual_af = usbr_report.monthly_to_water_year(treaty_monthly_af, water_year_month=1)

    excess_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_in_excess.csv')
    excess_annual_af = usbr_report.monthly_to_water_year(excess_monthly_af, water_year_month=1)

    graph.plot(excess_monthly_af, sub_plot=0, title='Mexico in Excess of Treaty (Monthly)',
               xinterval=year_interval, yinterval=100000, color='firebrick',
               ylabel='maf', format_func=WaterGraph.format_maf)

    bar_data = [
                {'data': treaty_annual_af, 'label': 'Treaty', 'color': 'firebrick'},
                {'data': excess_annual_af, 'label': 'Excess of Treaty', 'color': 'lightcoral'},
    ]
    graph.bars_stacked(bar_data, sub_plot=1, title='Mexico (Annual)',
                       ymin=0, ymax=16000000, yinterval=2000000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(excess_annual_af, 10, sub_plot=1)

    graph.bars_stacked(bar_data, sub_plot=2, title='Mexico (Annual)',
                       ymin=1300000, ymax=2000000, yinterval=100000,
                       xlabel='', xinterval=year_interval,
                       ylabel='maf', format_func=WaterGraph.format_maf)
    graph.running_average(excess_annual_af, 10, sub_plot=2)

    graph.date_and_wait()

    # Bypass pursuant to minute 242
    bypass_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_minute_242_bypass.csv')
    graph = WaterGraph(nrows=2)
    graph.plot(bypass_monthly_af, sub_plot=0, title='Mexico Pursuant to Minute 242 (Monthly)',
               xinterval=year_interval, yinterval=1000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    bypass_annual_af = usbr_report.monthly_to_water_year(bypass_monthly_af, water_year_month=1)
    graph.bars(bypass_annual_af, sub_plot=1, title='Mexico Pursuant to Minute 242 (Annual)',
               ymin=0, ymax=160000, yinterval=10000,
               xlabel='',  xinterval=year_interval, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()

    graph = WaterGraph(nrows=5)
    graph.plot(treaty_monthly_af, sub_plot=0, title='Satisfaction of Treaty (Monthly)',
               xinterval=year_interval, ymin=0, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    nib_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_northern_international_boundary.csv')
    graph.plot(nib_monthly_af, sub_plot=1, title='Northern International Border (Monthly)',
               xinterval=year_interval, yinterval=100000, color='firebrick',
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    sib_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_southern_international_boundary.csv')
    graph.plot(sib_monthly_af, sub_plot=2, title='Southern International Border (Monthly)',
               xinterval=year_interval, yinterval=2000, color='firebrick',
               ylabel='af', format_func=WaterGraph.format_af)

    limitrophe_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_limitrophe.csv')
    graph.plot(limitrophe_monthly_af, sub_plot=3, title='Limitrophe (Monthly)',
               xinterval=year_interval, yinterval=200, color='firebrick',
               ylabel='af', format_func=WaterGraph.format_af)

    tijuana_monthly_af = usbr_report.load_monthly_csv('mx/usbr_mx_tijuana.csv')
    graph.plot(tijuana_monthly_af, sub_plot=4, title='Tijuana (Monthly)',
               xinterval=year_interval, yinterval=100, color='firebrick',
               ylabel='af', format_func=WaterGraph.format_af)

    graph.date_and_wait()


def mexico_diversion(water_year_month=1):
    nib_morelos_gage = usgs.lc.northern_international_border(graph=False)
    nib = nib_morelos_gage.annual_af(water_year_month=water_year_month)
    return nib
    # satisfaction = usbr_report.annual_af('mx/usbr_mx_satisfaction_of_treaty.csv', water_year_month=water_year_month)
    # excess = usbr_report.annual_af('mx/usbr_mx_in_excess.csv', water_year_month=water_year_month)
    # return add_annual(satisfaction, excess)


def mexico_cu(water_year_month=1):
    return mexico_diversion(water_year_month=water_year_month)


def mexico_returns(water_year_month=1):
    return subtract_annual(mexico_diversion(water_year_month=water_year_month),
                           mexico_diversion(water_year_month=water_year_month))


if __name__ == '__main__':
    chdir('../')
    test_model = lc.Model('test')
    test_model.initialize()
    state = test_model.state_by_name('Mexico')
    state.test()
