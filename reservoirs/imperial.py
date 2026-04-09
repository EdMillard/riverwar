"""
Copyright (c) 2026 Ed Millard

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
from reservoirs.reservoir import Reservoir
from source import usbr_rise
import colorado.lb as lb
import colorado.allb as all_b
from sheet import sheet
from typing import List

class Imperial(Reservoir):
    def __init__(self):
        headers:List[str] = [lb.HAVASU, lb.HAVASU_ELEVATION]
        super().__init__('Imperial', headers)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

        self.full_feet =  0
        self.full_af = 0

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 0
        self.power_head_min_af = 0

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

        # Current
        #
        self.elevation_feet = 0
        self.active_capacity_af = 0

        # 24 Month
        #
        # HACK name to get Lake Havasu 24 month with Mexico in it
        self.df_24_month, self.df_24_wy =  self.load_24_month('Lake Havasu', 2026, 'MAR')
        self.flow_to_mexico_actual_af = self.get_24_month_actual(self.df_24_month, "Flow To Mexico")
        self.flow_to_mexico_projected_af = self.get_24_month_projected(self.df_24_month, "Flow To Mexico")

        self.outflow_parts = [
            ("Outflow Actual", self.flow_to_mexico_actual_af, Reservoir.outflow_actual_color),
            ("Outflow Projected", self.flow_to_mexico_projected_af, Reservoir.outflow_projected_color),         ]
