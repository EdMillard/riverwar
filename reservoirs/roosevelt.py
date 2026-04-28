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
from pathlib import Path
from datetime import date
from reservoirs.reservoir import Reservoir
import colorado.ub as ub
from typing import List, Optional

class Roosevelt(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Roosevelt', headers, catalog_id=0, upstream=upstream)
        self.start_year = 1910

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 1910  # range is 1900-1920
        self.dead_pool_af = 18500   # range is 17000-20000

        self.full_feet = 2_151
        self.full_af = 1_653_043

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 0
        self.power_head_min_af = 0

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        # self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        # self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.BLUE_MESA_ELEVATION_WY)
        self.elevation_feet =  2_098.76
        self.active_capacity_af = 734_034