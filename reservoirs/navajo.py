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

class Navajo(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = [ub.NAVAJO_WY,  ub.NAVAJO_ELEVATION_WY,
                             ub.NAVAJO_INFLOW, ub.NAVAJO_INFLOW_CFS,
                             ub.NAVAJO_RELEASE, ub.NAVAJO_RELEASE_CFS, ub.NAVAJO_EVAPORATION_WY]
        super().__init__('Navajo', headers, upstream=upstream)

        self.usbr_rise_elevation_ft_id = 612
        self.usbr_rise_storage_af_id = 613
        self.end_of_month_storage_str = 'Live Storage'
        self.usbr_rise_inflow_af_id = 4289
        self.usbr_rise_inflow_cfs_id = 615
        self.usbr_rise_evap_af_id = 617
        self.usbr_rise_release_af_id = 4290
        self.usbr_rise_release_cfs_id = 616
        self.usbr_rise_power_release_af_id = 4290
        self.usbr_rise_power_release_cfs_id = 4316

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

        self.full_feet = 6085
        self.full_af = 1701300

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 5990 # Elevation where pumps to NAIP/Domestic stop working
        self.power_head_min_af = 661800

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.NAVAJO_ELEVATION_WY)
        self.active_capacity_af = self.get_storage(self.usbr_rise_storage_af_id, ub.NAVAJO_WY)

        self.evao_af = self.get_daily_and_last(self.usbr_rise_evap_af_id, ub.NAVAJO_EVAPORATION_WY)
        self.inflow_cfs = self.get_daily_and_last(self.usbr_rise_inflow_cfs_id, ub.NAVAJO_INFLOW_CFS)
        # self.inflow_af = self.get_daily_and_last(self.usbr_rise_inflow_af_id, ub.NAVAJO_INFLOW)
        self.release_cfs = self.get_daily_and_last(self.usbr_rise_release_cfs_id, ub.NAVAJO_RELEASE_CFS)
        # self.release_af = self.get_daily_and_last(self.usbr_rise_release_af_id, ub.NAVAJO_RELEASE)

        # self.power_release_cfs = self.get_daily_and_last(self.usbr_rise_power_release_cfs_id, ub.NAVAJO_POWER_RELEASE_CFS)
        # self.power_release_af = self.get_daily_and_last(self.usbr_rise_power_release_af_id, ub.NAVAJO_POWER_RELEASE)

        # usbr_navajo_storage_af = 613
        # sheet.usbr_last_value(self.df, usbr_navajo_storage_af, self.water_year, self.water_year, title=ub.NAVAJO_WY, month=all_b.WY, divisor=1)
        # self.active_capacity_af = self.get_value_by_year(self.water_year, ub.NAVAJO_WY)

        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Modified Unregulated Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        # usbr_navajo_release_total_cfs = 4316
        # sheet.usbr_annuals(self.df, usbr_navajo_release_total_cfs, self.water_year, self.water_year, title=ub.NAVAJO_RELEASE_WY, month=all_b.WY, divisor=1)
        # self.outflow_actual_af = self.get_value_by_year(self.water_year, ub.NAVAJO_RELEASE_WY)

        # usbr_navajo_evaporation_af = 617
        # sheet.usbr_annuals(self.df, usbr_navajo_evaporation_af, self.water_year, self.water_year,  title=ub.NAVAJO_EVAPORATION_WY, month=all_b.WY, divisor=1)

        # usbr_navajo_inflow_unregulated_cfs = 615

        # usbr_navajo_inflow_af = 4289
        # usbr_navajo_release_total_af = 4355
        # usbr_navajo_inflow_volume_unregulated_af = 4358
        # usbr_navajo_modified_unregulated_inflow_cfs = 4369
        # usbr_navajo_modified_unregulated_inflow_volume_af = 4370
        # usbr_navajo_change_in_storage_af = 4405
        # usbr_navajo_area_acres = 4785

        # Inflow
        # usbr_navajo_inflow_cfs = 616
        # sheet.usbr_annuals(self.df, usbr_navajo_inflow_cfs, self.water_year, self.water_year,  title=ub.NAVAJO_INFLOW_WY, month=all_b.WY, divisor=1)
        # self.inflow_actual_af = self.get_value_by_year(self.water_year, ub.NAVAJO_INFLOW_WY)
