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
from typing import List, Optional
from source import cdss
from api import df_utils
import colorado.ub as ub
import colorado.allb as all_b


class WilliamsFork(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Williams Fork',headers,  catalog_id=0, upstream=upstream)
        self.start_year = 1965
        self.no_elevation_available = True

        # Elevations
        #
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet = 7_811
        self.full_af = 97_000

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
        super().load_data(report_path, start_date, current_date, end_date)
        time_series = cdss.telemetry_station_time_series(None, ub.CDSS_CO_WILLIAMS_FORK_ABBREV, 'STORAGE',
                                                         water_year_info=self.water_year_info, alias=self.name+'.'+all_b.STORAGE)
        self.active_capacity_af = time_series[-1][1]
        df_utils.fill_df_from_structured_array(self.df_daily, time_series, date_column_name='Date', value_column_name=self.name+'.'+all_b.STORAGE)
        pass
        # time_series = cdss.telemetry_station_time_series(None, ub.CDSS_CO_WILLIAMS_FORK_ABBREV, 'DISCHRG',
        #                                                  water_year_info=self.water_year_info, alias=self.name+'.'+all_b.RELEASE)
        # df_utils.fill_df_from_structured_array(self.df_daily, time_series, date_column_name='Date', value_column_name=self.name+'.'+all_b.RELEASE)


