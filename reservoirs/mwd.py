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
import datetime
from reservoirs.reservoir import Reservoir
from typing import List, Optional, Dict
import pandas as pd
import colorado.lb as lb

selenium_driver = None

class MWD(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Metropolitan', headers, upstream=upstream)
        self.custom_color = lb.CA_COLOR

        # self.df_daily:pd.DataFrame = LakePleasant.from_adwr_csv(self.name)

        self.catalog_id = 0
        # self.get_lake_pleasant_data()

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0
        # Bottom 5586.00

        # Maximum conservation storage: ~812,100 acre-feet at elevation 1,702 feet (surface area ~9,970 acres).
        # This is the primary "full" operational target for conservation/storage purposes
        # Conservation pool
        self.full_feet =  1_702
        self.full_af = 812_000

        # Flood pool
        # self.full_feet =  1_725
        # self.full_af = 1_108_600

        diamond_valley_lake_capacity_af = 810_000
        diamond_valley_lake_mathews_storage_af = 787_815

        lake_mathews_capacity_af = 182_000
        lake_mathews_storage_af = 182_000

        lake_skinner_capacity_af = 44_000
        lake_skinner_storage_af = 36_041

        self.mwd_capacity_af = diamond_valley_lake_capacity_af + lake_mathews_capacity_af + lake_skinner_capacity_af
        self.mwd_storage_af = diamond_valley_lake_mathews_storage_af + lake_mathews_storage_af + lake_skinner_storage_af
        self.full_af = self.mwd_capacity_af

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        # Top of inactive conservation pool
        self.power_head_min_feet =  0
        self.power_head_min_af = 0

        # Actual dead pool is 1506 ft,

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

        # self.inflow_actual_af = self.get_value_by_year(self.water_year, lb.MOHAVE_INFLOW)
        self.inflow_actual_af = 0
        self.inflow_parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                             ("Projected", 0, Reservoir.inflow_projected_color)]

        # Outflow
        self.outflow_actual_af = 0
        self.release_af = 0
        self.outflow_actual_af = 0
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        # self.reserved_parts = reserved_parts or []

    def get_elevation(self, year, end_year:int|None =None)->float:
        return 0

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        self.elevation_feet = 0
        self.active_capacity_af = self.mwd_storage_af
