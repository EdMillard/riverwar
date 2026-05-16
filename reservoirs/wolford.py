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
from typing import List, Optional
from source import cdss
import pandas as pd
from api import df_utils
from pathlib import Path
from datetime import date
import colorado.allb as all_b
from sheet import sheet

class Wolford(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Wolford',headers,  catalog_id=0, upstream=upstream)
        self.start_year = 1996

        # Elevations
        #
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet = 6_871.13
        self.full_af = 84_410

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet =  6_720
        self.power_head_min_af = 25_014


        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

    def load_data(self, report_path: Path, start_date: date, current_date: date, end_date: date):
        super().load_data(report_path, start_date, current_date, end_date)
        self.start_date = date(2026 - 1, 10, 1)
        self.end_date = date(2026, 9, 30)
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date,
                                                               [all_b.STORAGE, all_b.STORAGE_DELTA, all_b.ELEVATION,
                                                                all_b.RELEASE, all_b.EVAPORATION, all_b.INFLOW])
        # USGS=09041395
        sheet.usgs_value(self.df_daily, '09041395', self.start_year, 2026, title=all_b.STORAGE, parameterCd='62614', statCd='00003')

        # wdid=5003657
        # time_series = cdss.telemetry_station_time_series(None, 'WOLFORD', 'STORAGE',
        #                                                  water_year_info=self.water_year_info,
        #                                                  alias='WOLFORD CAPACITY')
        # self.active_capacity_af = time_series[-1][1]

        # time_series = cdss.telemetry_station_time_series(None, 'WOLF', 'GAGE_HT',
        #                                                 water_year_info=self.water_year_info, alias='WOLFORD ELEVATION')
        # if time_series is not None:
        #     self.elevation_feet = time_series[-1][1]
        # time_series = cdss.telemetry_station_time_series(logger, 'WOLF', 'DISCHRG',
        #                                                 water_year_info=water_year_info, alias='WOLFORD DISCHARGE')
        pass