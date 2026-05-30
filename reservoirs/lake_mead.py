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
import copy
from datetime import date
import pandas as pd
from reservoirs.reservoir import Reservoir
import colorado.lb as lb
import colorado.allb as all_b
from api import df_utils
from typing import List, Optional
from sheet import sheet


# HDB SDI's
# Reservoir water surface elevation (end of period, primary)
# 1930 feet
# Total storage / content
# 1721 acre-feet
# Volume of evaporation
# 1776 acre-feet (per day)
# Total release volume (Hoover Dam from Mead)
# 2114 or related acre-feet
# Average total release
# 1874 cfs

class LakeMead(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None, month=1):
        headers:List[str] = [lb.DIAMOND_CREEK_WY, lb.MEAD_INFLOW, lb.MEAD, lb.MEAD_ABOVE_1000, lb.MEAD_MOST,
                             lb.LAKE_MEAD_CUL, lb.MEAD_ELEVATION,
                             lb.MEAD_RELEASE, lb.MEAD_RELEASE_CFS]
        super().__init__('Lake Mead', headers, catalog_id= 4370, upstream=upstream, month=month)
        self.start_year = 1937

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 895
        self.dead_pool_af = 0

        self.full_feet = 1229
        self.full_af = 27620294

        # Critical
        self.power_head_target_feet = 1035
        self.power_head_target_af = 6637508

        # self.power_head_min_feet = 1000
        # self.power_head_min_af = 4_475_301

        self.special_levels = [
            (1050, 7_682_878, "Level 2"),
            (1025, 5_981_122, "Level 3"),
            # (1000, 4_475_301, "'24 ROD")]
            (950, 2005585, "No power")]

        self.power_head_min_feet = 1000
        self.power_head_min_af = 4_475_301

        # self.power_head_min_feet = 950
        # self.power_head_min_af = 2005585

        self.turbine_intake_feet = 950
        self.turbine_intake_af = 2005585
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]


    def load_data(self, report_path:Path, start_date:date, current_date:date, end_date:date):
        self.load_date(report_path, start_date, current_date, end_date)

        # Current
        #
        self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, lb.MEAD_ELEVATION)
        self.active_capacity_af, daily_storage_af = self.get_storage(self.usbr_rise_storage_af_id, lb.MEAD)  # 1937
        one_month_ago_dt = Reservoir.months_earlier(daily_storage_af['dt'][-1] )
        self.storage_one_month_ago = Reservoir.get_value_at_time(daily_storage_af, one_month_ago_dt)
        two_months_ago_dt = Reservoir.months_earlier(daily_storage_af['dt'][-1], months=2)
        self.storage_two_months_ago = Reservoir.get_value_at_time(daily_storage_af, two_months_ago_dt)
        self.print_storage(daily_storage_af)

        self.release_cfs = self.get_daily_and_last(self.usbr_rise_release_cfs_id, lb.MEAD_RELEASE_CFS)
        self.release_af = self.get_daily_and_last(self.usbr_rise_release_af_id, lb.MEAD_RELEASE)
        self.usgs_load_daily('09404200', lb.DIAMOND_CREEK)

        # usbr_lake_mead_storage_af = 6124  # 1937
        # sheet.usbr_last_value(self.df, usbr_lake_mead_storage_af, self.water_year, self.water_year, title=lb.MEAD, month=1, divisor=1)
        # self.active_capacity_af = self.get_value_by_year(self.water_year, lb.MEAD)

        # 24 Month
        #
        self.inflow_parts = self.get_24_month_inflow(self.df_24_month, "Glen Release")
        self.side_inflow_parts = self.get_24_month_side_inflow(self.df_24_month, "Side Inflow Glen to Hoover")
        self.outflow_parts = self.get_24_month_outflow(self.df_24_month)
        self.evap_parts = self.get_24_month_evap(self.df_24_month)

        self.snwa_actual_af = self.get_24_month_actual(self.df_24_month, "SNWP Use")
        self.snwa_projected_af = self.get_24_month_projected(self.df_24_month, "SNWP Use")

        self.draw_pump_name = False
        self.pump_parts = [("SNWA Actual", self.snwa_actual_af, Reservoir.snwa_pump_actual_color),
                           ("SNWA Projected", self.snwa_projected_af, Reservoir.snwa_pump_projected_color)]

        df_utils.subtract_constant(self.df_daily, lb.MEAD, lb.MEAD_ABOVE_1000, self.power_head_min_af)
        if self.df_24_month is not None:
            Reservoir.interpolate_monthly_storage_to_daily(self.df_24_month, self.df_daily,
                                                           monthly_value_col='End Of Month Storage', daily_target_col=lb.MEAD_MOST)
            df_utils.subtract_constant(self.df_daily, lb.MEAD_MOST, lb.MEAD_MOST, self.power_head_min_af)

        # t1 = '2026-01-01T00:00'
        # t2 = '2026-03-27T23:59'
        # FIXME compare to CUL in 2024
        # evap = usbr_rise.request_hdb(1776, t1, t2)  # Mead evao
        # release = usbr_rise.request_hdb(2114, t1, t2)  # Mead release

        # usbr_rise.request_accum()

        # Current
        #
        # self.elevation_feet = self.get_elevationX(self.water_year)

        # usbr_lake_mead_release_total_af = 6122
        # sheet.usbr_annuals(self.df, usbr_lake_mead_release_total_af, self.water_year, self.water_year, title=lb.HOOVER_RELEASE, month=1, divisor=1)
        # self.outflow_actual_af = self.get_value_by_year(self.water_year, lb.HOOVER_RELEASE)

        # Evap
        # reservoir_path = Path('data/USBR_Lower_Colorado_CUL/Reservoir')
        # df_mead_evap = sheet.read_csv(reservoir_path / 'lake_mead.csv', sep='\s+')
        # sheet.merge_annual_column(self.df, df_mead_evap, lb.LAKE_MEAD_CUL, divisor=1)

        # Inflow
        # FIXME, need Virgin and Muddy
        # sheet.usgs_annuals(self.df, '09404200', self.water_year, self.water_year, title=lb.DIAMOND_CREEK_WY, month=all_b.WY, divisor=1)
        # self.inflow_actual_af = self.get_value_by_year(self.water_year, lb.DIAMOND_CREEK_WY)

        # Outflow
        # 1936
        # Broken since Feb 2026, gage only since
        # sheet.usgs_annuals(self.df, '09421500', self.water_year, self.water_year, title=lb.HOOVER_USGS, divisor=1)

        # ICS
        self.reserved_parts = [("CA", 1661832, lb.CA_COLOR),
                               ("NV", 954013, lb.NV_COLOR),
                               ("AZ", 710589, lb.AZ_COLOR)]

    def load_data_annual(self, start_year:Optional[int]=None, end_year:Optional[int]=None)->pd.DataFrame:
        df = super().load_data_annual(start_year=start_year, end_year=end_year)

        # Lees Ferry is fallback before Diuamond Creek,  Need to add side inflow constant as a hack
        sheet.usgs_annuals(df, '09380000', self.start_year, 2006, title=all_b.INFLOW, divisor=1)
        # Diamond Creek
        sheet.usgs_annuals(df, '09404200', 2007, self.end_year,  title=all_b.INFLOW, divisor=1)
        return df

    def copy(self):
        return copy.copy(self)

    def __str__(self) -> str:
        string = f" '\'{self.name}\'"

        return string