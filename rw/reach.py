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
from rw.util import subtract_annual


class Reach(object):
    def __init__(self, name, upper_lake, lower_lake, water_year_month):
        self.name = name
        self.upper_lake = upper_lake
        self.lower_lake = lower_lake
        self.water_month = water_year_month
        self.users = []
        self.active_users_in_reach = []

    def add_user(self, user):
        self.users.append(user)

    def model(self, year_begin, year_end):
        if not self.upper_lake or not self.lower_lake:
            return None, None
        reach_inflow = self.upper_lake.release(year_begin, year_end)
        lower_lake_inflow = self.lower_lake.inflow(year_begin, year_end)

        reach_side_inflows = subtract_annual(lower_lake_inflow, reach_inflow)

        lower_lake_release = self.lower_lake.release(year_begin, year_end)

        if lower_lake_release is not None:
            inflow_outflow_delta = subtract_annual(lower_lake_inflow, lower_lake_release)
        else:
            print(self.lower_lake.name + " release not implemented")
            inflow_outflow_delta = lower_lake_inflow

        storage_delta = self.lower_lake.storage_delta(year_begin, year_end)

        self.active_users_in_reach = self.cu(year_begin, year_end)
        reach_cu = [0] * (year_end - year_begin + 1)
        cu_avg = 0
        print('\n--- ' + self.name + ' ---')
        if len(self.active_users_in_reach):
            print('Active users: ', len(self.active_users_in_reach))
            for user in self.active_users_in_reach:
                print('\t', user.state, ' ', '{0: <30}'.format(user.name), user.cu_for_years)
                reach_cu = [reach_cu[x] + user.cu_for_years[x][1] for x in range(len(reach_cu))]
            cu_avg = sum(reach_cu) / len(reach_cu)
        else:
            print("No consumptive use in reach")

        users_in_reach_by_state = self.users_in_reach_by_state()
        for state in users_in_reach_by_state:
            users_in_state = users_in_reach_by_state.get(state)
            print('\t' + state, ':', len(users_in_state))
        print(self.name + '{0: <40}'.format(' inflow: '), reach_inflow)
        print(self.name + '{0: <40}'.format(' side inflows: '), reach_side_inflows)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' inflow '), lower_lake_inflow)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' release '), lower_lake_release)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' cu      '), reach_cu, ' avg: ', int(cu_avg))
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' inflow/outflow delta '),
              inflow_outflow_delta)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' storage delta '), storage_delta)
        print()

    def cu(self, year_begin, year_end):
        active_users = []
        for user in self.users:
            user_cu_for_years = user.get_cu_for_years(year_begin, year_end)
            if user_cu_for_years is not None:
                active_users.append(user)

        return active_users

    def users_in_reach_by_state(self, state=None):
        users_by_state = {}
        for user in self.active_users_in_reach:
            try:
                users_for_state = users_by_state[user.state]
            except KeyError:
                users_for_state = []
                users_by_state[user.state] = users_for_state

            users_for_state.append(user)
        return users_by_state




