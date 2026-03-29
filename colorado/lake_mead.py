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
import copy
from api.reservoir import Reservoir
from source import usbr_rise
import colorado.lb as lb
from sheet import sheet
from typing import List
from pathlib import Path

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
    def __init__(self, month=1):
        headers:List[str] = [lb.DIAMOND_CREEK, lb.MEAD_INFLOW, lb.MEAD, lb.LAKE_MEAD_CUL, lb.MEAD_ELEVATION, lb.HOOVER_RELEASE]
        super().__init__('Lake Mead', headers, month=month)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 895
        self.dead_pool_af = 2546532

        self.full_feet = 1229
        self.full_af = 27620294

        # Critical
        self.power_head_target_feet = 1035
        self.power_head_target_af = 6637508

        self.power_head_min_feet = 950
        self.power_head_min_af = 2005585

        self.turbine_intake_feet = 950
        self.turbine_intake_af = 2005585
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

        t1 = '2026-01-01T00:00'
        t2 = '2026-03-27T23:59'
        # FIXME compare to CUL in 2024
        evap = usbr_rise.request_hdb(1776, t1, t2)  # Mead evao
        release = usbr_rise.request_hdb(2114, t1, t2)  # Mead release

        # usbr_rise.request_accum()

        # Current
        #
        self.elevation_feet = self.get_elevation(self.water_year)

        usbr_lake_mead_release_total_af = 6122
        sheet.usbr_annuals(self.df, usbr_lake_mead_release_total_af, self.water_year, self.water_year, title=lb.HOOVER_RELEASE, month=1, divisor=1)

        usbr_lake_mead_storage_af = 6124  # 1937
        sheet.usbr_last_value(self.df, usbr_lake_mead_storage_af, self.water_year, self.water_year, title=lb.MEAD, month=1, divisor=1)
        self.active_capacity_af = self.get_value_by_year(self.water_year, lb.MEAD)

        # Evap
        reservoir_path = Path('data/USBR_Lower_Colorado_CUL/Reservoir')
        df_mead_evap = sheet.read_csv(reservoir_path / 'lake_mead.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_mead_evap, lb.LAKE_MEAD_CUL, divisor=1)

        # Inflow 2007
        # FIXME, need Virgin and Muddy
        sheet.usgs_annuals(self.df, '09404200', self.water_year, self.water_year, title=lb.DIAMOND_CREEK, divisor=1)
        self.inflow_actual_af = self.get_value_by_year(self.water_year, lb.DIAMOND_CREEK)
        self.inflow_parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                             ("Projected", 0, Reservoir.inflow_projected_color)]

        # Outflow
        # 1936
        # Broken since Feb 2026, gage only since
        # sheet.usgs_annuals(self.df, '09421500', self.water_year, self.water_year, title=lb.HOOVER_USGS, divisor=1)

        self.outflow_actual_af = self.get_value_by_year(self.water_year, lb.HOOVER_RELEASE)
        self.release_af = 8300000
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        self.reserved_parts = [("CA", 1661832, '#1f77b4'),
                               ("NV", 954013, '#ff7f0e'),
                               ("AZ", 710589, '#2ca02c')]

    def get_elevation(self, year, end_year:int|None =None)->float:
        usbr_lake_mead_elevation_ft = 6123 # 1936
        sheet.usbr_last_value(self.df, usbr_lake_mead_elevation_ft, self.water_year, self.water_year, title=lb.MEAD_ELEVATION, divisor=1)
        return self.get_value_by_year(self.water_year, lb.MEAD_ELEVATION)

    def copy(self):
        return copy.copy(self)

    def __str__(self) -> str:
        string = f" '\'{self.name}\'"

        return string