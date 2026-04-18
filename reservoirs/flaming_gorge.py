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
import pandas as pd
from api import df_utils
import colorado.allb as all_b
from reservoirs.reservoir import Reservoir
import colorado.ub as ub
from typing import List, Optional

class FlamingGorge(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = [ub.FLAMING_GORGE_WY,  ub.FLAMING_GORGE_ELEVATION_WY,
                             ub.FLAMING_GORGE_INFLOW, ub.FLAMING_GORGE_INFLOW_CFS,
                             ub.FLAMING_GORGE_INFLOW_UNREGULATED, ub.FLAMING_GORGE_INFLOW_UNREGULATED_CFS,
                             ub.FLAMING_GORGE_RELEASE, ub.FLAMING_GORGE_RELEASE_CFS, ub.FLAMING_GORGE_EVAPORATION_WY]
        super().__init__('Flaming Gorge', headers, upstream=upstream)

        self.usbr_rise_elevation_ft_id = 341
        self.usbr_rise_storage_af_id = 337
        self.end_of_month_storage_str = 'Live Storage'
        self.usbr_rise_inflow_af_id = 4287
        self.usbr_rise_inflow_cfs_id = 339
        self.usbr_rise_inflow_unregulated_af_id = 4300
        self.usbr_rise_inflow_unregulated_cfs_id = 338
        self.usbr_rise_evap_af_id = 342
        self.usbr_rise_release_af_id = 4353
        self.usbr_rise_release_cfs_id = 4314

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

        self.full_feet = 6047       # Practical max with free board is 6,040 – 6,046
        self.full_af = 4_019_148.1

        # Critical
        self.power_head_target_feet = 5908
        self.power_head_target_af = 573219.6880

        self.power_head_min_feet = 5868
        self.power_head_min_af = 260726.9980

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):

        self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.FLAMING_GORGE_ELEVATION_WY)
        self.active_capacity_af = self.get_storage(self.usbr_rise_storage_af_id, ub.FLAMING_GORGE_WY)
        self.inflow_cfs = self.get_daily_and_last(self.usbr_rise_inflow_cfs_id, ub.FLAMING_GORGE_INFLOW_CFS)
        # self.inflow_af = self.get_daily_and_last(self.usbr_rise_inflow_af_id, ub.FLAMING_GORGE_INFLOW)
        self.inflow_unregulated_cfs = self.get_daily_and_last(self.usbr_rise_inflow_unregulated_cfs_id, ub.FLAMING_GORGE_INFLOW_UNREGULATED_CFS)
        # self.inflow_unregulated_af = self.get_daily_and_last(self.usbr_rise_inflow_unregulated_af_id, ub.FLAMING_GORGE_INFLOW_UNREGULATED)
        self.release_cfs = self.get_daily_and_last(self.usbr_rise_release_cfs_id, ub.FLAMING_GORGE_RELEASE_CFS)
        # self.release_af = self.get_daily_and_last(self.usbr_rise_release_af_id, ub.FLAMING_GORGE_RELEASE)

        # Actual from USBR/USGS
        headers_24_month = list(self.df_24_month.columns.astype(str))
        df: pd.DataFrame = df_utils.create_monthly_df(self.water_year_info.start_date, self.water_year_info.end_date,
                                                   headers_24_month)
        Reservoir.usbr_monthly(df, self.usbr_rise_inflow_af_id, self.water_year, "Unregulated Inflow", month=all_b.WY)
        Reservoir.usbr_monthly(df, self.usbr_rise_release_af_id, self.water_year, "Total Release", month=all_b.WY)
        Reservoir.usbr_monthly(df, self.usbr_rise_evap_af_id, self.water_year, "Evaporation Losses", month=all_b.WY)

        Reservoir.usbr_end_of_month(df, self.usbr_rise_elevation_ft_id, self.water_year,
                                    "Reservoir Elevation End of Month ft", month=all_b.WY)
        Reservoir.usbr_end_of_month(df, self.usbr_rise_storage_af_id, self.water_year, "Live Storage",
                                    month=all_b.WY)

        df_utils.subtract_constant(self.df_daily, ub.FLAMING_GORGE_WY, ub.FLAMING_GORGE_ABOVE_5868, self.power_head_min_af)
        Reservoir.interpolate_monthly_storage_to_daily(self.df_24_month, self.df_daily,
                                                       monthly_value_col='Live Storage',
                                                       daily_target_col=ub.FLAMING_GORGE_MOST)
        df_utils.subtract_constant(self.df_daily, ub.FLAMING_GORGE_MOST, ub.FLAMING_GORGE_MOST, self.power_head_min_af)

        # usbr_flaming_gorge_storage_af = 337
        # sheet.usbr_last_value(self.df, usbr_flaming_gorge_storage_af, self.water_year, self.water_year,
        #                       title=ub.FLAMING_GORGE_WY, month=all_b.WY, divisor=1)
        # self.active_capacity_af = self.get_value_by_year(self.water_year, ub.FLAMING_GORGE_WY)

        # 24 Month
        #
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Unregulated Inflow")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        # usbr_flaming_gorge_release_total_cfs = 4314
        # sheet.usbr_annuals(self.df, usbr_flaming_gorge_release_total_cfs, self.water_year, self.water_year, title=ub.FLAMING_GORGE_RELEASE_WY, month=all_b.WY, divisor=1)
        # self.outflow_actual_af = self.get_value_by_year(self.water_year, ub.FLAMING_GORGE_RELEASE_WY)

        # usbr_flaming_gorge_evaporation_af = 342
        # sheet.usbr_annuals(self.df, usbr_flaming_gorge_evaporation_af, self.water_year, self.water_year,  title=ub.FLAMING_GORGE_EVAPORATION_WY, month=all_b.WY, divisor=1)

        # usbr_flaming_gorge_inflow_unregulated_cfs = 338

        # usbr_flaming_gorge_elevation_ft = 341
        # usbr_flaming_gorge_bank_storage_af = 4275
        # usbr_flaming_gorge_inflow_af = 4287
        # usbr_flaming_gorge_inflow_volume_unregulated_af = 4300
        # usbr_flaming_gorge_release_power_plant_cfs = 4306

        # Inflow
        # usbr_flaming_gorge_inflow_cfs = 339
        # sheet.usbr_annuals(self.df, usbr_flaming_gorge_inflow_cfs, self.water_year, self.water_year,  title=ub.FLAMING_GORGE_INFLOW_WY, month=all_b.WY, divisor=1)
        # self.inflow_actual_af = self.get_value_by_year(self.water_year, ub.FLAMING_GORGE_INFLOW_WY)
