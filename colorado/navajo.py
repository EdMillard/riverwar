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
from api.reservoir import Reservoir
from source import usbr_rise
import colorado.ub as ub
import colorado.allb as all_b
from sheet import sheet
from typing import List

class Navajo(Reservoir):
    def __init__(self):
        headers:List[str] = [ub.NAVAJO_WY,  ub.NAVAJO_ELEVATION_WY, ub.NAVAJO_INFLOW_WY,
                             ub.NAVAJO_RELEASE_WY, ub.NAVAJO_ELEVATION_WY, ub.NAVAJO_EVAPORATION_WY]
        super().__init__('Navajo', headers)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

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

        # Current
        #
        self.elevation_feet = self.get_elevation(self.water_year)[1]
        self.active_capacity_af = 0

        usbr_navajo_release_total_cfs = 4316
        sheet.usbr_annuals(self.df, usbr_navajo_release_total_cfs, self.water_year, self.water_year, title=ub.NAVAJO_RELEASE_WY, month=all_b.WY, divisor=1)

        usbr_navajo_storage_af = 613
        sheet.usbr_last_value(self.df, usbr_navajo_storage_af, self.water_year, self.water_year, title=ub.NAVAJO_WY, month=all_b.WY, divisor=1)
        self.active_capacity_af = self.get_value_by_year(self.water_year, ub.NAVAJO_WY)

        usbr_navajo_evaporation_af = 617
        sheet.usbr_annuals(self.df, usbr_navajo_evaporation_af, self.water_year, self.water_year,  title=ub.NAVAJO_EVAPORATION_WY, month=all_b.WY, divisor=1)

        # usbr_navajo_inflow_unregulated_cfs = 615

        # usbr_navajo_inflow_af = 4289
        # usbr_navajo_release_total_af = 4355
        # usbr_navajo_inflow_volume_unregulated_af = 4358
        # usbr_navajo_modified_unregulated_inflow_cfs = 4369
        # usbr_navajo_modified_unregulated_inflow_volume_af = 4370
        # usbr_navajo_change_in_storage_af = 4405
        # usbr_navajo_area_acres = 4785

        # Inflow
        usbr_navajo_inflow_cfs = 616
        sheet.usbr_annuals(self.df, usbr_navajo_inflow_cfs, self.water_year, self.water_year,  title=ub.NAVAJO_INFLOW_WY, month=all_b.WY, divisor=1)

        self.inflow_actual_af = self.get_value_by_year(self.water_year, ub.NAVAJO_INFLOW_WY)
        self.inflow_parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                             ("Projected", 0, Reservoir.inflow_projected_color)]

        # Outflow
        self.outflow_actual_af = self.get_value_by_year(self.water_year, ub.NAVAJO_RELEASE_WY)
        self.release_af = 0
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        # self.reserved_parts = reserved_parts or []

    def get_elevation(self, year, end_year:int|None =None)->float:
        usbr_navajo_elevation_ft = 612
        info, daily_elevation_ft = usbr_rise.load(usbr_navajo_elevation_ft, water_year_info=self.water_year_info,
                                                  alias=ub.NAVAJO_ELEVATION_WY)
        sheet.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date', value_column_name=ub.NAVAJO_ELEVATION_WY)
        return daily_elevation_ft[-1]