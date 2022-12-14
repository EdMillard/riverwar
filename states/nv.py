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
from rw.state import State, state_by_abbreviation
from rw.util import subtract_annual, add_annuals, reshape_annual_range_to, reach_for_name
from rw.util import state_total_vs_user_total_graph
from source.usbr_report import diversion_vs_consumptive


current_last_year = 2021


class Nevada(State):
    def __init__(self, module, reaches, options):
        State.__init__(self, 'Nevada', 'nv', module, reaches, options)
        module = modules[__name__]
        r1 = reach_for_name(reaches, 'Reach1')
        r2 = reach_for_name(reaches, 'Reach2')
        r3 = reach_for_name(reaches, 'Reach3')

        r1.add_user(self.user(None, 'bureau_of_reclamation'))             # 1985- aka Boulder Canyon Project and Hoover
        r1.add_user(self.user(module, 'boulder_city'))                    # 1964-1983
        r1.add_user(self.user(None, 'lake_mead_national'))                # 1964-
        r1.add_user(self.user(module, 'snwa_griffith', example=True))     # 1984-
        r1.add_user(self.user(module, 'basic'))                           # 1964-
        r1.add_user(self.user(module, 'city_of_henderson'))               # 1972-
        r1.add_user(self.user(None, 'nevada_dept_of_wildlife'))           # 1973-
        r1.add_user(self.user(module, 'las_vegas_valley'))                # 1964-1983
        r1.add_user(self.user(module, 'north_las_vegas'))                 # 1971-1983
        r1.add_user(self.user(module, 'nellis'))                          # 1971-2002
        r1.add_user(self.user(module, 'pacific_coast'))                   # 1964-
        r1.add_user(self.user(module, 'socal_edison'))                    # 1967-2011

        r2.add_user(self.user(None, 'lake_mead_national_lake_mohave'))    # 1993-

        r3.add_user(self.user(None, 'big_bend'))                          # 1984-
        r3.add_user(self.user(module, 'fort_mojave_indian'))              # 1996-

    def test(self):
        data = [
            {'data': state_total_diversion(), 'y_min': 0, 'y_max': 550000, 'y_interval': 50000},
            {'data': user_total_diversion()},
            {'y_min': -50, 'y_max': 200, 'y_interval': 50},
            {'data': state_total_cu(), 'y_min': 0, 'y_max': 350000, 'y_interval': 50000},
            {'data': user_total_cu()},
            {'y_min': -50, 'y_max': 200, 'y_interval': 100},
        ]
        state_total_vs_user_total_graph('NV', data, y_formatter='kaf')
        total()
        southern_nevada_water_authority()


def state_total_diversion():
    return usbr_report.annual_af('nv/usbr_nv_total_diversion.csv')


def state_total_cu():
    return usbr_report.annual_af('nv/usbr_nv_total_consumptive_use.csv')


def user_total_diversion():
    nevada = state_by_abbreviation('nv')
    return nevada.total_user_diversion()


def user_total_cu():
    nevada = state_by_abbreviation('nv')
    return nevada.total_user_cu()


def user_total_returns():
    nevada = state_by_abbreviation('nv')
    return nevada.total_user_returns()


def total():
    diversion_vs_consumptive('nv', 'total', 'Nevada',
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


def lake_mead_national_lake_mohave_diversion():
    return usbr_report.annual_af('nv/usbr_nv_lake_mead_national_lake_mohave_diversion.csv')


def lake_mead_national_lake_mohave_cu():
    return lake_mead_national_lake_mohave_diversion()


def lake_mead_national_lake_mohave_returns():
    return subtract_annual(lake_mead_national_lake_mohave_diversion(), lake_mead_national_lake_mohave_cu())


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


def pacific_coast_diversion():
    return usbr_report.annual_af('nv/usbr_nv_pacific_coast_diversion.csv')


def pacific_coast_cu():
    return pacific_coast_diversion()


def pacific_coast_returns():
    return subtract_annual(pacific_coast_diversion(), pacific_coast_cu())


def basic_diversion():
    return usbr_report.annual_af('nv/usbr_nv_basic_diversion.csv')


def basic_cu():
    return basic_diversion()


def basic_returns():
    return subtract_annual(basic_diversion(), basic_cu())


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


def nellis_diversion():
    return usbr_report.annual_af('nv/usbr_nv_nellis_diversion.csv')


def nellis_cu():
    # FIXME, are returns in Las Vegas Wash or is this all consumptive use
    return nellis_diversion()


def nellis_returns():
    return subtract_annual(nellis_diversion(), nellis_cu())


def fort_mojave_indian_diversion():
    ag = usbr_report.annual_af('nv/usbr_nv_fort_mojave_indian_diversion.csv')
    domestic = usbr_report.annual_af('nv/usbr_nv_fort_mojave_indian_domestic_diversion.csv')
    return add_annuals([ag, domestic])


def fort_mojave_indian_cu():
    return usbr_report.annual_af('nv/usbr_nv_fort_mojave_indian_consumptive_use.csv')


def fort_mojave_indian_returns():
    return subtract_annual(fort_mojave_indian_diversion(), fort_mojave_indian_cu())


if __name__ == '__main__':
    chdir('../')
    test_model = lc.Model('test')
    test_model.initialize(1964, 2021)
    state = test_model.state_by_name('Nevada')
    state.test()
