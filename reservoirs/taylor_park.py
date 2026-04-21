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

class TaylorPark(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Taylor Park', headers, catalog_id=2459, upstream=upstream)
        self.start_year = 1959

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet = 0
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

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.BLUE_MESA_ELEVATION_WY)
        self.active_capacity_af = self.get_storage(self.usbr_rise_storage_af_id, ub.BLUE_MESA_WY)

        self.evap_af = self.get_daily_and_last(self.usbr_rise_evap_af_id, ub.BLUE_MESA_EVAPORATION_WY)
        self.inflow_cfs = self.get_daily_and_last(self.usbr_rise_inflow_cfs_id, ub.BLUE_MESA_INFLOW_CFS)
        # self.inflow_af = self.get_daily_and_last(self.usbr_rise_inflow_af_id, ub.BLUE_MESA_INFLOW)
        self.release_cfs = self.get_daily_and_last(self.usbr_rise_release_cfs_id, ub.BLUE_MESA_RELEASE_CFS)
        # self.release_af = self.get_daily_and_last(self.usbr_rise_release_af_id, ub.BLUE_MESA_RELEASE)

        # usbr_blue_mesa_storage_af = 76
        # sheet.usbr_last_value(self.df, usbr_blue_mesa_storage_af, self.water_year, self.water_year,
        #                        title=ub.BLUE_MESA_WY, month=all_b.WY, divisor=1)
        # self.active_capacity_af = self.get_value_by_year(self.water_year, ub.BLUE_MESA_WY)

        # 24 Month
        #
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Unregulated Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)