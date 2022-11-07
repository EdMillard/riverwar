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
from rw.util import flow_for_year, subtract_annual


class Reach(object):
    def __init__(self, name, upper_lake, lower_lake, water_year_month):
        self.name = name
        self.upper_lake = upper_lake
        self.lower_lake = lower_lake
        self.water_month = water_year_month
        self.users = []

    def add_user(self, user):
        self.users.append(user)

    def model(self, year_begin, year_end):
        if not self.upper_lake or not self.lower_lake:
            return None, None
        reach_inflow = self.upper_lake.release(year_begin, year_end)
        lower_lake_inflow = self.lower_lake.inflow(year_begin, year_end)

        reach_side_inflows = subtract_annual(lower_lake_inflow, reach_inflow)

        lower_lake_release = self.lower_lake.release(year_begin, year_end)

        inflow_outflow_delta = subtract_annual(lower_lake_inflow, lower_lake_release)

        cu, active_users = self.cu(year_begin, year_end)
        cu_avg = sum(cu) / len(cu)

        storage_delta = self.lower_lake.storage_delta(year_begin, year_end)

        print(self.name + '{0: <40}'.format(' inflow: '), reach_inflow)
        print(self.name + '{0: <40}'.format(' side inflows: '), reach_side_inflows)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' inflow '), lower_lake_inflow)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' release '), lower_lake_release)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' cu      '), cu,
              ' avg: ', int(cu_avg), ' users ', active_users)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' inflow/outflow delta '),
              inflow_outflow_delta)
        print(self.name + ' ' + self.lower_lake.name + '{0: <30}'.format(' storage delta '), storage_delta)
        print()

    def cu(self, year_begin, year_end):
        cu = []
        for year in range(year_begin, year_end+1):
            year_cu = 0
            for user in self.users:
                user_cu = user.cu()
                user_cu_for_year = flow_for_year(user_cu, year)
                print('\t', user.name, ' ', user_cu_for_year)
                if user_cu_for_year and user_cu_for_year > 0:
                    year_cu += user_cu_for_year
                    user.active = True
            cu.append(year_cu)
        active_users = 0
        for user in self.users:
            if user.active:
                print('\t', user.state, ' ', user.name)
                active_users += 1
        return cu, active_users

