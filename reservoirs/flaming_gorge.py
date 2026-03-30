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
import colorado.ub as ub
import colorado.allb as all_b
from sheet import sheet
from typing import List

class FlamingGorge(Reservoir):
    def __init__(self):
        headers:List[str] = [ub.FLAMING_GORGE_WY,  ub.FLAMING_GORGE_ELEVATION_WY, ub.FLAMING_GORGE_INFLOW_WY,
                             ub.FLAMING_GORGE_RELEASE_WY, ub.FLAMING_GORGE_EVAPORATION_WY]
        super().__init__('Flaming Gorge', headers)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

        self.full_feet = 6046
        self.full_af = 0

        # Critical
        self.power_head_target_feet = 5908
        self.power_head_target_af = 573219.6880

        self.power_head_min_feet = 5868
        self.power_head_min_af = 260726.9980

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

        # Current
        #
        self.elevation_feet = self.get_elevation(self.water_year)[1]
        self.active_capacity_af = 0

        usbr_flaming_gorge_release_total_cfs = 4314
        sheet.usbr_annuals(self.df, usbr_flaming_gorge_release_total_cfs, self.water_year, self.water_year, title=ub.FLAMING_GORGE_RELEASE_WY, month=all_b.WY, divisor=1)

        usbr_flaming_gorge_storage_af = 337
        sheet.usbr_last_value(self.df, usbr_flaming_gorge_storage_af, self.water_year, self.water_year, title=ub.FLAMING_GORGE_WY, month=all_b.WY, divisor=1)
        self.active_capacity_af = self.get_value_by_year(self.water_year, ub.FLAMING_GORGE_WY)

        usbr_flaming_gorge_evaporation_af = 342
        sheet.usbr_annuals(self.df, usbr_flaming_gorge_evaporation_af, self.water_year, self.water_year,  title=ub.FLAMING_GORGE_EVAPORATION_WY, month=all_b.WY, divisor=1)

        # usbr_flaming_gorge_inflow_unregulated_cfs = 338

        # usbr_flaming_gorge_elevation_ft = 341
        # usbr_flaming_gorge_bank_storage_af = 4275
        # usbr_flaming_gorge_inflow_af = 4287
        # usbr_flaming_gorge_inflow_volume_unregulated_af = 4300
        # usbr_flaming_gorge_release_powerplant_cfs = 4306

        # Inflow
        usbr_flaming_gorge_inflow_cfs = 339
        sheet.usbr_annuals(self.df, usbr_flaming_gorge_inflow_cfs, self.water_year, self.water_year,  title=ub.FLAMING_GORGE_INFLOW_WY, month=all_b.WY, divisor=1)

        self.inflow_actual_af = self.get_value_by_year(self.water_year, ub.FLAMING_GORGE_INFLOW_WY)
        self.inflow_parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                             ("Projected", 0, Reservoir.inflow_projected_color)]

        # Outflow
        self.outflow_actual_af = self.get_value_by_year(self.water_year, ub.FLAMING_GORGE_RELEASE_WY)
        self.release_af = 500000
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        # self.reserved_parts = reserved_parts or []

    def get_elevation(self, year, end_year:int|None =None)->float:
        usbr_lake_powell_elevation_ft = 341
        info, daily_elevation_ft = usbr_rise.load(usbr_lake_powell_elevation_ft, water_year_info=self.water_year_info,
                                                  alias=ub.FLAMING_GORGE_ELEVATION_WY)
        sheet.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date', value_column_name=ub.FLAMING_GORGE_ELEVATION_WY)
        return daily_elevation_ft[-1]