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

class LakeMohave(Reservoir):
    def __init__(self):
        headers:List[str] = [lb.MOHAVE,  lb.MOHAVE_ELEVATION, lb.MOHAVE_INFLOW,
                             lb.MOHAVE_RELEASE,lb.MOHAVE_ELEVATION, lb.MOHAVE_EVAPORATION]
        super().__init__('Lake Mohave', headers)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 7358.0
        self.dead_pool_af = 0
        # Bottom 5586.00

        self.full_feet =  7519.4
        self.full_af = 748430

        # Critical
        self.power_head_target_feet = 7460
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

        usbr_lake_mohave_storage_af = 6134
        sheet.usbr_last_value(self.df, usbr_lake_mohave_storage_af, self.water_year, self.water_year, title=lb.MOHAVE, month=all_b.CY, divisor=1)
        self.active_capacity_af = self.get_value_by_year(self.water_year, lb.MOHAVE)

        # 24 Month
        #
        self.df_24_month, self.df_24_wy =  self.load_24_month(self.name, 2026, 'MAR')
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Hoover Release", side="Side Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        # usbr_lake_mohave_release_total_af = 6131
        # sheet.usbr_annuals(self.df, usbr_lake_mohave_release_total_af, self.water_year, self.water_year, title=lb.MOHAVE_RELEASE, month=all_b.WY, divisor=1)

        # usbr_blue_mesa_evaporation_af = 79
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_evaporation_af, self.water_year, self.water_year,  title=lb.MOHAVE_EVAPORATION, month=all_b.CY, divisor=1)

        # usbr_lake_mohave_water_temperature_degf = 6132
        # usbr_lake_mohave_release_total_cfs = 6135

        # Inflow
        # self.inflow_actual_af = self.get_value_by_year(self.water_year, lb.MOHAVE_INFLOW)

        # Outflow
        # self.outflow_actual_af = self.get_value_by_year(self.water_year, lb.MOHAVE_RELEASE)

    def get_elevation(self, year, end_year:int|None =None)->float:
        usbr_lake_mohave_elevation_ft = 6133
        info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft, water_year_info=self.water_year_info,
                                                  alias=lb.MOHAVE_ELEVATION)
        sheet.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date', value_column_name=lb.MOHAVE_ELEVATION)
        return daily_elevation_ft[-1]