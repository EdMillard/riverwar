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
from rw.util import af_as_str, number_as_str, percent_as_str, right_justified, left_justified, generate_year_header
from rw.util import add_annual, subtract_annual, subtract_vector_from_annual, annual_as_str, vector_as_str
from rw.util import annual_is_zero, annual_zeroed_for_years, vector_is_zero, vector_zeroed_for_years
from rw.state import state_by_abbreviation

debug = True


class Reach(object):
    reaches = {}

    def __init__(self, name, upper_lake, lower_lake, water_year_month):
        Reach.reaches[name] = self
        self.name = name
        self.upper_lake = upper_lake
        self.lower_lake = lower_lake
        # Model Parameters
        self.water_month = water_year_month
        # Users
        self.users = []
        self.active_users_in_reach = []
        self.active_users_through_reach = {}
        self.state_assessment = {}
        # Reach
        self.loss = None
        self.loss_note = ''

        self.reach_cu = None
        self.reach_cu_note = ''

        self.in_reach_cu_avg = None
        self.through_reach_cu_avg = None

        self.reach_inflow = None
        self.reach_inflow_note = ''

        self.upper_lake_bypass = None
        self.upper_lake_bypass_note = ''

        self.reach_side_inflows = None
        self.reach_side_inflows_note = ''

        self.reach_total_inflow = None
        self.reach_total_inflow_note = ''

        self._24_month_side_inflows = None
        self._24_month_side_inflows_note = ''

        # Lower Lake
        self.loss_corridor = None
        self.loss_corridor_note = ''

        self.lower_lake_inflow = None
        self.lower_lake_inflow_note = ''

        self.loss_evaporation = None
        self.loss_evaporation_note = ''

        self.lower_lake_release = None
        self.lower_lake_release_note = ''

        self.lower_lake_bypass = None
        self.lower_lake_bypass_note = ''

        self.inflow_outflow_delta = None
        self.inflow_outflow_delta_note = ''

        self.storage_delta = None
        self.storage_delta_note = ''

        self.states = ['az', 'ca', 'nv', 'mx']

    @staticmethod
    def reach_by_name(name):
        return Reach.reaches[name]

    def add_user(self, user):
        self.users.append(user)

    def model(self, year_begin, year_end):
        if not self.upper_lake:
            return None, None

        self.reach_inflow = self.upper_lake.release
        self.reach_inflow_note = self.upper_lake.release_note
        self.upper_lake_bypass = self.upper_lake.bypass
        if self.upper_lake_bypass is not None:
            self.upper_lake_bypass_note = self.upper_lake.bypass_note
            self.reach_total_inflow = add_annual(self.reach_inflow, self.upper_lake_bypass)
        else:
            self.reach_total_inflow = self.reach_inflow

        if self.lower_lake:
            self.loss_evaporation = self.lower_lake.evaporation
            self.lower_lake_release = self.lower_lake.release
            self.lower_lake_bypass = self.lower_lake.bypass
            self.storage_delta = self.lower_lake.storage_delta()
            self._24_month_side_inflows = self.lower_lake.side_inflow
        else:
            self.loss_evaporation = annual_zeroed_for_years(year_begin, year_end)
            self.lower_lake_release = annual_zeroed_for_years(year_begin, year_end)
            self.lower_lake_bypass = annual_zeroed_for_years(year_begin, year_end)
            self.storage_delta = vector_zeroed_for_years(year_begin, year_end)
            self._24_month_side_inflows = None

        if self._24_month_side_inflows is not None:
            self.reach_side_inflows = self._24_month_side_inflows
            self.reach_side_inflows_note = self.lower_lake.side_inflow_note
            self.reach_total_inflow = add_annual(self.reach_total_inflow, self.reach_side_inflows)
        elif self.lower_lake and self.lower_lake.inflow is not None:
            self.lower_lake_inflow = self.lower_lake.inflow
            self.reach_side_inflows = subtract_annual(self.reach_total_inflow, self.lower_lake_inflow)
            self.reach_side_inflows_note = 'Estimated from reach inflow and lower lake inflow'
            self.reach_total_inflow = add_annual(self.reach_total_inflow, self.reach_side_inflows)
        else:
            pass

        # Total user consumptive use
        #
        self.active_users_in_reach = self.cu(year_begin, year_end)
        self.reach_cu = [0] * (year_end - year_begin + 1)
        self.in_reach_cu_avg = 0
        if len(self.active_users_in_reach):
            for user in self.active_users_in_reach:
                self.reach_cu = [self.reach_cu[x] + user.cu_for_years[x][1] for x in range(len(self.reach_cu))]
            self.in_reach_cu_avg = int(sum(self.reach_cu) / len(self.reach_cu))
            self.reach_cu_note = self.name + ' Total User CU, USBR Annual Report'

        self.inflow_outflow_delta = subtract_vector_from_annual(self.reach_total_inflow, self.reach_cu)
        if self.lower_lake_release is not None:
            self.inflow_outflow_delta = subtract_annual(self.inflow_outflow_delta, self.lower_lake_release)
        if self.loss_evaporation is not None:
            self.inflow_outflow_delta = subtract_annual(self.inflow_outflow_delta, self.loss_evaporation)
        if self.lower_lake_bypass is not None:
            self.inflow_outflow_delta = subtract_annual(self.inflow_outflow_delta, self.lower_lake_bypass)

        if debug:
            print('\n==', self.name + ',', self.upper_lake.name, 'to', self.lower_lake.name)
            print('                           ', generate_year_header(year_begin, year_end))
            print(' reach_inflow:         ', annual_as_str(self.reach_inflow), self.reach_inflow_note)
            if not annual_is_zero(self.upper_lake_bypass):
                print('+upper_lake_bypass:    ', annual_as_str(self.upper_lake_bypass), self.upper_lake.bypass_note)
            if not annual_is_zero(self.reach_side_inflows):
                print('+reach_side_inflows:   ', annual_as_str(self.reach_side_inflows), self.reach_side_inflows_note)
            print('=reach_total_inflow:   ', annual_as_str(self.reach_total_inflow), self.reach_total_inflow_note)

            if not annual_is_zero(self.lower_lake_inflow):
                print(' lower_lake_inflow:    ', annual_as_str(self.lower_lake_inflow), self.lower_lake_inflow_note)
            print('-reach cu:             ', vector_as_str(self.reach_cu), self.reach_cu_note)
            if not annual_is_zero(self.loss_evaporation):
                print('-loss_evaporation:     ', annual_as_str(self.loss_evaporation), self.lower_lake.evaporation_note)
            if not annual_is_zero(self.lower_lake_release):
                print('-lower_lake_release:   ', annual_as_str(self.lower_lake_release), self.lower_lake.release_note)
            if not annual_is_zero(self.lower_lake_bypass):
                print('-lower_lake_bypass:    ', annual_as_str(self.lower_lake_bypass), self.lower_lake.bypass_note)

            print('=inflow_outflow_delta: ', annual_as_str(self.inflow_outflow_delta))
            if not vector_is_zero(self.storage_delta):
                print('-storage_delta:        ', vector_as_str(self.storage_delta), self.lower_lake.storage_note)
                diff = subtract_vector_from_annual(self.inflow_outflow_delta, self.storage_delta)
            else:
                diff = self.inflow_outflow_delta
            print('=water balance_delta   ', annual_as_str(diff))

    def cu(self, year_begin, year_end):
        active_users = []
        for user in self.users:
            user_cu_for_years = user.get_cu_for_years(year_begin, year_end)
            if user_cu_for_years is not None:
                active_users.append(user)

        return active_users

    def compute_through_reach_cu_avg(self):
        self.through_reach_cu_avg = 0
        for state in self.states:
            try:
                users = self.active_users_through_reach[state]
            except KeyError:
                users = []
            for user in users:
                avg_cu = user.avg_cu()
                self.through_reach_cu_avg += avg_cu

    def compute_state_assessment(self):
        for state_code in self.states:
            state = state_by_abbreviation(state_code)
            try:
                users = self.active_users_through_reach[state_code]
            except KeyError:
                users = []

            state_through_reach_cu_avg = 0
            for user in users:
                avg_cu = user.avg_cu()
                state_through_reach_cu_avg += avg_cu

            if self.through_reach_cu_avg != 0:
                percent = state_through_reach_cu_avg / self.through_reach_cu_avg
            else:
                percent = 0
            state_assessment = self.loss * percent
            state.loss_assessment += state_assessment

            for user in users:
                user.factor = user.avg_cu() / state_through_reach_cu_avg
                user.assessment += state_assessment * user.factor

            self.state_assessment[state_code] = {'cu_avg': state_through_reach_cu_avg,
                                                 'assessment': state_assessment,
                                                 'percent': percent,
                                                 'users': users}

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
        print(self.name + '{0: >95}'.format('2019        2020        2021'))  # FIXME need to build this from year range
        print('{0: <28}'.format('  inflow: '), annual_as_str(self.reach_inflow))
        if self._24_month_side_inflows is not None:
            print('{0: <28}'.format(' +24 month side inflows: '), annual_as_str(self._24_month_side_inflows))
        else:
            print('{0: <28}'.format(' +side inflows: '), annual_as_str(self.reach_side_inflows))
        print('{0: <28}'.format(' =total inflow: '), annual_as_str(self.reach_total_inflow))
        print('  ' + self.lower_lake.name)
        print('{0: <28}'.format('    inflow '), annual_as_str(self.lower_lake_inflow))
        print('{0: <28}'.format('   -cu: '), vector_as_str(self.reach_cu), '  avg: ',
              vector_as_str([self.in_reach_cu_avg]))
        if self.loss_evaporation is not None:
            print('{0: <28}'.format('   -evap '), annual_as_str(self.loss_evaporation))
        print('{0: <28}'.format('   -release '), annual_as_str(self.lower_lake_release))
        if self.lower_lake_bypass is not None:
            print('{0: <28}'.format('   -bypass '), annual_as_str(self.lower_lake_bypass))
        print('{0: <28}'.format('   =inflow/outflow delta '), annual_as_str(self.inflow_outflow_delta))
        print('{0: <28}'.format('    storage delta '), vector_as_str(self.storage_delta))
        print()

    def state_assessment_as_str(self, state, print_num_users=True, print_percent=True, print_reach_cu=False):
        s = '\t'
        number_of_active_users_through_reach = 0
        try:
            state_dictionary = self.state_assessment[state]
            users = state_dictionary['users']
            s += state + '    '  # Pad to match 'Total'
            if print_num_users:
                s += number_as_str(len(users))
            s += af_as_str(state_dictionary['cu_avg'])
            if print_reach_cu:
                s += af_as_str(self.through_reach_cu_avg)
            if print_percent:
                s += ' '
                s += percent_as_str(state_dictionary['percent'])
                s += ' '
            state_assessment = state_dictionary['assessment']
            s += af_as_str(state_assessment)
            number_of_active_users_through_reach = len(users)
        except KeyError:
            print('\t' + state + '   ')
        return s, number_of_active_users_through_reach

    def print_state_assessments(self):
        print('\n--- ' + self.name + ' ---')
        number_of_active_users_through_reach = 0
        for state in self.states:
            try:
                s, number_of_state_users = self.state_assessment_as_str(state)
                number_of_active_users_through_reach += number_of_state_users
                print(s)
            except KeyError:
                print('\t' + state + '   ')

        print('\tTotal', number_as_str(number_of_active_users_through_reach) + af_as_str(self.through_reach_cu_avg),
              percent_as_str(1.0), af_as_str(self.loss))

    @staticmethod
    def user_as_str(user, print_cu=False, print_state=False):
        s = '\t'
        if print_state:
            s += user.state
        s += right_justified(user.name, 40)
        if print_cu:
            s += annual_as_str(user.cu_for_years)
        s += af_as_str(user.avg_cu())
        return s
