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


class Options(object):
    def __init__(self):
        self.reset()
        self.yuma_users_moved_to_reach_4 = False
        self.havasu_evap_charge_to_havasu_users = False
        self.grand_canyon_inflow_cancels_mead_evap = False
        self.crit_in_reach_3a = False
        self.palo_verde_in_reach_3b = False
        self.usgs_lake_mead_inflow = False
        self.reach6_for_mexico = False
        self.use_rise_release_data_if_available = False


    def reset(self):
        self.yuma_users_moved_to_reach_4 = False
        self.havasu_evap_charge_to_havasu_users = False
        self.grand_canyon_inflow_cancels_mead_evap = False
        self.crit_in_reach_3a = False
        self.palo_verde_in_reach_3b = False
        self.usgs_lake_mead_inflow = False
        self.reach6_for_mexico = False
        self.use_rise_release_data_if_available = False

