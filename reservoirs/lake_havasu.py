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
import colorado.lb as lb
from typing import List, Optional

class LakeHavasu(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = [lb.HAVASU, lb.HAVASU_ELEVATION, lb.HAVASU_INFLOW,
                             lb.HAVASU_RELEASE, lb.HAVASU_EVAPORATION]
        super().__init__('Lake Havasu', headers, upstream=upstream)

        self.usbr_rise_elevation_ft_id = 6128
        self.usbr_rise_storage_af_id = 6129
        # self.usbr_rise_inflow_af_id = 0
        # self.usbr_rise_evap_af_id = 0
        self.usbr_rise_release_af_id = 6126

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

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, lb.HAVASU_ELEVATION)
        self.active_capacity_af = self.get_storage(self.usbr_rise_storage_af_id, lb.HAVASU)

        # usbr_lake_havasu_storage_af = 6129
        # sheet.usbr_last_value(self.df, usbr_lake_havasu_storage_af, self.water_year, self.water_year, title=lb.HAVASU, month=all_b.CY, divisor=1)
        # self.active_capacity_af = self.get_value_by_year(self.water_year, lb.HAVASU)

        # 24 Month
        #
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Davis Release")
        self.side_inflow_parts = self.get_24_month_inflow(self.df_24_month, "Side Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        self.cap_diversion_actual_af = self.get_24_month_actual(self.df_24_month, "CAP Diversion")
        self.cap_diversion_projected_af = self.get_24_month_projected(self.df_24_month, "CAP Diversion")

        self.mwd_diversion_actual_af = self.get_24_month_actual(self.df_24_month, "MWD Diversion")
        self.mwd_diversion_projected_af = self.get_24_month_projected(self.df_24_month, "MWD Diversion")

        self.flow_to_mexico_actual_af = self.get_24_month_actual(self.df_24_month, "Flow To Mexico")
        self.flow_to_mexico_projected_af = self.get_24_month_projected(self.df_24_month, "Flow To Mexico")

        self.outflow_actual_af -= self.flow_to_mexico_actual_af
        self.outflow_projected_af -= self.flow_to_mexico_projected_af

        self.salton_actual_af = 400000
        self.salton_projected_af = 400000

        self.outflow_actual_af -= self.salton_actual_af
        self.outflow_projected_af -= self.salton_projected_af

        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]


        self.pump_parts = [
            ("MX Actual", self.flow_to_mexico_actual_af, Reservoir.flow_to_mexico_actual_color),
            ("MX Projected", self.flow_to_mexico_projected_af, Reservoir.flow_to_mexico_projected_color),
            ("Salton Actual", self.salton_actual_af, Reservoir.salton_actual_color),
            ("Salton Projected", self.salton_projected_af, Reservoir.salton_projected_color),
            ("CAP Actual", self.cap_diversion_actual_af, Reservoir.cap_pump_actual_color),
            ("CAP Projected", self.cap_diversion_projected_af, Reservoir.cap_pump_projected_color),
            ("MPW Actual", self.mwd_diversion_actual_af, Reservoir.mwd_pump_actual_color),
            ("MPW Projected", self.mwd_diversion_projected_af, Reservoir.mwd_pump_projected_color),
             ]

        # usbr_lake_havasu_release_total_af = 6126
        # sheet.usbr_annuals(self.df, usbr_lake_havasu_release_total_af, self.water_year, self.water_year, title=lb.HAVASU_RELEASE, month=all_b.CY, divisor=1)

        # usbr_blue_mesa_evaporation_af = 79
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_evaporation_af, self.water_year, self.water_year,  title=lb.HAVASU_EVAPORATION, month=all_b.CY, divisor=1)

        # usbr_lake_havasu_water_temperature_degf = 6127
        # usbr_lake_havasu_release_total_cfs = 6130

        # Inflow
        # usbr_blue_mesa_inflow_cfs = 4279
        # sheet.usbr_annuals(self.df, usbr_blue_mesa_inflow_cfs, self.water_year, self.water_year,  title=lb.HAVASU_INFLOW, month=all_b.CY, divisor=1)1
        # self.inflow_actual_af = self.get_value_by_year(self.water_year, lb.HAVASU_INFLOW)

        # Outflow
        # self.outflow_actual_af = self.get_value_by_year(self.water_year, lb.HAVASU_RELEASE)
