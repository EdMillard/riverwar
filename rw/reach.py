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
from rw.util import af_as_str, number_as_str, percent_as_str
from rw.util import subtract_annual, subtract_vector_from_annual, annual_as_str, vector_as_str


class Reach(object):
    def __init__(self, name, upper_lake, lower_lake, water_year_month):
        self.name = name
        self.upper_lake = upper_lake
        self.lower_lake = lower_lake
        # Model Parameters
        self.water_month = water_year_month
        # Users
        self.users = []
        self.active_users_in_reach = []
        self.active_users_through_reach = {}
        # Reach
        self.loss = None
        self.reach_cu = None
        self.reach_cu_avg = None
        self.reach_inflow = None
        self.reach_side_inflows = None
        self.reach_total_inflow = None
        self._24_month_side_inflows = None
        # Lower Lake
        self.loss_corridor = None
        self.lower_lake_inflow = None
        self.loss_evaporation = None
        self.lower_lake_release = None
        self.lower_lake_bypass = None
        self.inflow_outflow_delta = None
        self.storage_delta = None

    def add_user(self, user):
        self.users.append(user)

    def model(self, year_begin, year_end):
        if not self.upper_lake or not self.lower_lake:
            return None, None

        self.reach_inflow = self.upper_lake.release(year_begin, year_end)
        self.lower_lake_inflow = self.lower_lake.inflow(year_begin, year_end)
        self.loss_evaporation = self.lower_lake.evaporation(year_begin, year_end)
        self.lower_lake_release = self.lower_lake.release(year_begin, year_end)
        self.lower_lake_bypass = self.lower_lake.bypass(year_begin, year_end)
        self._24_month_side_inflows = self.lower_lake.side_inflow(year_begin, year_end)
        if self._24_month_side_inflows is not None:
            self.reach_side_inflows = self._24_month_side_inflows
        else:
            self.reach_side_inflows = subtract_annual(self.lower_lake_inflow, self.reach_inflow)
        #self.reach_total_inflow = add_annual(self.reach_inflow, self.reach_side_inflows)
        self.reach_total_inflow = self.reach_inflow

        if self.lower_lake_release is not None:
            self.inflow_outflow_delta = subtract_annual(self.lower_lake_inflow, self.lower_lake_release)
        else:
            # print(self.lower_lake.name + " release not implemented")
            self.inflow_outflow_delta = self.lower_lake_inflow

        if self.loss_evaporation is not None:
            self.inflow_outflow_delta = subtract_annual(self.inflow_outflow_delta, self.loss_evaporation)

        if self.lower_lake_bypass is not None:
            self.inflow_outflow_delta = subtract_annual(self.inflow_outflow_delta, self.lower_lake_bypass)

        self.storage_delta = self.lower_lake.storage_delta(year_begin, year_end)

        self.active_users_in_reach = self.cu(year_begin, year_end)
        self.reach_cu = [0] * (year_end - year_begin + 1)
        self.reach_cu_avg = 0
        if len(self.active_users_in_reach):
            for user in self.active_users_in_reach:
                self.reach_cu = [self.reach_cu[x] + user.cu_for_years[x][1] for x in range(len(self.reach_cu))]
            self.reach_cu_avg = int(sum(self.reach_cu) / len(self.reach_cu))

            self.inflow_outflow_delta = subtract_vector_from_annual(self.inflow_outflow_delta, self.reach_cu)

    def cu(self, year_begin, year_end):
        active_users = []
        for user in self.users:
            user_cu_for_years = user.get_cu_for_years(year_begin, year_end)
            if user_cu_for_years is not None:
                active_users.append(user)

        return active_users

    def users_in_reach_by_state(self):
        users_by_state = {}
        for user in self.active_users_in_reach:
            try:
                users_for_state = users_by_state[user.state]
            except KeyError:
                users_for_state = []
                users_by_state[user.state] = users_for_state

            users_for_state.append(user)
        return users_by_state

    def users_through_reach_by_state(self):
        users_by_state = {}
        for user in self.active_users_through_reach:
            try:
                users_for_state = users_by_state[user.state]
            except KeyError:
                users_for_state = []
                users_by_state[user.state] = users_for_state

            users_for_state.append(user)
        return users_by_state

    def print_model(self):
        print(self.name + '{0: >95}'.format('2016        2017        2018        2019        2020        2021'))  # FIXME need to build this from year range
        print('{0: <28}'.format('  inflow: '), annual_as_str(self.reach_inflow))
        if self._24_month_side_inflows is not None:
            print('{0: <28}'.format(' +24 month side inflows: '), annual_as_str(self._24_month_side_inflows))
        else:
            print('{0: <28}'.format(' +side inflows: '), annual_as_str(self.reach_side_inflows))
        print('{0: <28}'.format(' =total inflow: '), annual_as_str(self.reach_total_inflow))
        print('  ' + self.lower_lake.name)
        print('{0: <28}'.format('    inflow '), annual_as_str(self.lower_lake_inflow))
        print('{0: <28}'.format('   -cu: '), vector_as_str(self.reach_cu), '  avg: ', vector_as_str([self.reach_cu_avg]))
        if self.loss_evaporation is not None:
            print('{0: <28}'.format('   -evap '), annual_as_str(self.loss_evaporation))
        print('{0: <28}'.format('   -release '), annual_as_str(self.lower_lake_release))
        if self.lower_lake_bypass is not None:
            print('{0: <28}'.format('   -bypass '), annual_as_str(self.lower_lake_bypass))
        print('{0: <28}'.format('   =inflow/outflow delta '), annual_as_str(self.inflow_outflow_delta))
        print('{0: <28}'.format('    storage delta '), vector_as_str(self.storage_delta))
        print()

    def print_users(self):
        users_through_reach = self.active_users_through_reach
        states = ['az', 'ca', 'nv', 'mx']
        print('\n--- ' + self.name + ' ---')

        print('  Active users through reach')

        # Total average CU
        total_avg_cu = 0
        for state in states:
            try:
                users = users_through_reach[state]
            except KeyError:
                users = []
            for user in users:
                avg_cu = user.avg_cu()
                total_avg_cu += avg_cu

        # Average CU by state and state assessments per SNWA formula
        active_users_through_reach = 0
        for state in users_through_reach:
            try:
                users = users_through_reach[state]
            except KeyError:
                users = []
            state_total_avg_cu = 0
            for user in users:
                avg_cu = user.avg_cu()
                state_total_avg_cu += avg_cu
            percent = state_total_avg_cu / total_avg_cu
            state_assessment = self.loss * percent
            print('\t'+state+'   ', number_as_str(len(users)), af_as_str(state_total_avg_cu),
                  percent_as_str(percent), af_as_str(state_assessment))
            active_users_through_reach += len(users)
        print('\tTotal', number_as_str(active_users_through_reach), af_as_str(total_avg_cu),
              percent_as_str(1.0), af_as_str(self.loss))

        print('  Active users in reach')
        users_in_reach_by_state = self.users_in_reach_by_state()
        active_users_in_reach = 0
        for state in states:
            users_in_state = users_in_reach_by_state.get(state)
            if users_in_state is None:
                users_in_state = []
            print('\t'+state+'   ', number_as_str(len(users_in_state)))
            active_users_in_reach += len(users_in_state)
        print('\tTotal', number_as_str(active_users_in_reach))

        # FIXME Sort by CU
        # def get_year(element):
        #     return element['year']
        #
        # programming_languages.sort(key=get_year)
        if len(self.active_users_in_reach):
            print('  Active users in reach: ', len(self.active_users_in_reach))
            for user in self.active_users_in_reach:
                print('\t', user.state, ' ', '{0: <30}'.format(user.name), annual_as_str(user.cu_for_years),
                      af_as_str(user.avg_cu()))
        else:
            print("No consumptive use in reach")
