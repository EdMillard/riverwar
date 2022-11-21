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
from rw.user import User
from rw.util import add_annuals, subtract_annual, reshape_annual_range
from graph.water import WaterGraph
from source import usbr_report

states = {}
current_last_year = 2021


def state_by_abbreviation(abbreviation):
    return states[abbreviation]


class State(object):
    def __init__(self, name, abbreviation, module, reaches, options):
        self.name = name
        self.abbreviation = abbreviation
        self.module = module
        self.loss_assessment = None
        self.other_user_loss_assessments = None
        self.users = {}
        self.reaches = reaches
        self.options = options

        states[abbreviation] = self

    def test(self):
        pass

    def user(self, module, name, example=False):
        user = User(module, name, self.abbreviation, example=example)
        self.users[name] = user
        return user

    def total_user_diversion(self):
        user_diversions = []
        for key, value in self.users.items():
            user_diversions.append(value.diversion())
        user_diversions[0] = reshape_annual_range(user_diversions[0], 1964, current_last_year)
        return add_annuals(user_diversions)

    def total_user_cu(self):
        user_cus = []
        for key, value in self.users.items():
            user_cus.append(value.cu())
        user_cus[0] = reshape_annual_range(user_cus[0], 1964, current_last_year)
        return add_annuals(user_cus)

    def total_user_returns(self):
        user_returns = []
        for key, user in self.users.items():
            user_returns.append(user.returns())
        user_returns[0] = reshape_annual_range(user_returns[0], 1964, current_last_year)
        return add_annuals(user_returns)

    def user_for_name(self, name):
        state = self.users[name]
        return state

    @staticmethod
    def orders_not_delivered(self, state_code):
        year_interval = 3
        show_graph = True

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
            graph = WaterGraph(nrows=6)
            graph.bars(orders_not_delivered_af, sub_plot=0, title=state_code + ' Total Orders Not Delivered',
                       ymin=0, ymax=500000, yinterval=50000,
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_by_others_af, sub_plot=1,
                       ymin=0, ymax=150000, yinterval=50000, title='Diverted by Others',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diverted_to_storage_af, sub_plot=2,
                       ymin=0, ymax=300000, yinterval=50000, title='Diverted to Storage',
                       xlabel='', x_labels=False,  xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(satisfaction_of_treaty_af, sub_plot=3,
                       ymin=0, ymax=300000, yinterval=50000, title='Delivered in Satisfaction of Treaty',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(excess_of_treaty_af, sub_plot=4,
                       ymin=0, ymax=100000, yinterval=20000, title='Delivered in Excess of Treaty',
                       xlabel='', x_labels=False, xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.bars(diff, sub_plot=5,
                       ymin=-100000, ymax=100000, yinterval=50000, title='Diff Orders Not Diverted, Diverted/Delivered',
                       xlabel='',  xinterval=year_interval, color='firebrick',
                       ylabel='kaf', format_func=WaterGraph.format_kaf)
            graph.date_and_wait()
