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
from datetime import date
from reservoirs.reservoir import Reservoir
from source import usbr_rise
import colorado.ub as ub
import colorado.allb as all_b
from sheet import sheet
from typing import List, Optional

class BlueMesa(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = [ub.BLUE_MESA_WY,  ub.BLUE_MESA_ELEVATION_WY, ub.BLUE_MESA_INFLOW_WY,
                             ub.BLUE_MESA_RELEASE_WY, ub.BLUE_MESA_EVAPORATION_WY]
        super().__init__('Blue Mesa', headers, upstream=upstream)

        self.usbr_rise_elevation_ft_id = 78
        self.usbr_rise_storage_af_id = 76
        self.end_of_month_storage_str = 'Live Storage'
        self.usbr_rise_inflow_af_id = 4283
        self.usbr_rise_evap_af_id = 79
        # self.usbr_rise_release_af_id = 0

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 7358.0
        self.dead_pool_af = 0

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

    def load_data(self, start_date: date, current_date: date, end_date: date):
        self.load_date(start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.BLUE_MESA_ELEVATION_WY)
        self.active_capacity_af = self.get_storage(self.usbr_rise_storage_af_id, ub.BLUE_MESA_WY)

        # usbr_blue_mesa_storage_af = 76
        # sheet.usbr_last_value(self.df, usbr_blue_mesa_storage_af, self.water_year, self.water_year,
        #                        title=ub.BLUE_MESA_WY, month=all_b.WY, divisor=1)
        # self.active_capacity_af = self.get_value_by_year(self.water_year, ub.BLUE_MESA_WY)

        # 24 Month
        #
        self.df_24_month, self.df_24_wy =  self.load_24_month(self.name, 2026, 'MAR')
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Unregulated Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        # usbr_blue_mesa_release_total_cfs = 4310
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_release_total_cfs, self.water_year, self.water_year, title=ub.BLUE_MESA_RELEASE_WY, month=all_b.WY, divisor=1)
        # self.outflow_actual_af = self.get_value_by_year(self.water_year, ub.BLUE_MESA_RELEASE_WY)

        # usbr_blue_mesa_evaporation_af = 79
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_evaporation_af, self.water_year, self.water_year,  title=ub.BLUE_MESA_EVAPORATION_WY, month=all_b.WY, divisor=1)

        # usbr_blue_mesa_inflow_af = 4283
        # usbr_blue_mesa_inflow_unregulated_cfs = 4295
        # usbr_blue_mesa_inflow_volume_unregulated_af = 4297
        # usbr_blue_mesa_release_powerplant_cfs = 4302

        # usbr_blue_mesa_release_total_af = 4349
        # usbr_blue_mesa_release_powerplant_af = 4361
        # usbr_blue_mesa_release_spillway_cfs = 4380
        # usbr_blue_mesa_release_bypass_cfs = 4381
        # usbr_blue_mesa_release_bypass_af = 4382
        # usbr_blue_mesa_change_in_storage_af = 4398
        # usbr_blue_mesa_area_acres = 4773
        # Inflow
        # usbr_blue_mesa_inflow_cfs = 4279
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_inflow_cfs, self.water_year, self.water_year,  title=ub.BLUE_MESA_INFLOW_WY, month=all_b.WY, divisor=1)
        # self.inflow_actual_af = self.get_value_by_year(self.water_year, ub.BLUE_MESA_INFLOW_WY)