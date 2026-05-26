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
import colorado.ub as ub
import colorado.allb as all_b
from typing import List, Optional
from sheet import sheet
import pandas as pd
from api import df_utils


class Heron(Reservoir):
    def __init__(self, upstream: Optional[List[Reservoir]] = None):
        headers:List[str] = []
        super().__init__('Heron',headers,  catalog_id=2334, upstream=upstream) # 4503
        self.start_year = 1971
        self.end_year = 2026

        self.usbr_rise_san_juan_chama_average_inflow_af_id = self.usbr_item_ids.get('average_san_juan_chama_inflow_volume_af', None)

        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet = 0
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

    def load_data_annual(self, start_year:Optional[int]=None, end_year:Optional[int]=None)->pd.DataFrame:
        if self.usbr_rise_san_juan_chama_average_inflow_af_id:
            self.df_annual: pd.DataFrame = df_utils.create_df(self.start_year, self.end_year,
                                                         [ub.USGS_NM_SAN_JUAN_CHAMA_TUNNEL, all_b.STORAGE, all_b.ELEVATION, all_b.RELEASE, all_b.EVAPORATION,
                                                          all_b.INFLOW])
            sheet.usgs_annuals(self.df_annual, ub.USGS_NM_SAN_JUAN_CHAMA_TUNNEL_GAGE, self.start_year, 2008,
                               divisor=1, month=all_b.WY, title=ub.USGS_NM_SAN_JUAN_CHAMA_TUNNEL)

            sheet.usbr_annuals(self.df_annual, self.usbr_rise_san_juan_chama_average_inflow_af_id, 2009, self.end_year,
                               month=all_b.WY, title=ub.USGS_NM_SAN_JUAN_CHAMA_TUNNEL, divisor=1)


        return self.df_annual

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        super().load_data(report_path, start_date, current_date, end_date)

        if self.usbr_rise_san_juan_chama_average_inflow_af_id:
            self.usbr_rise_load_daily(self.usbr_rise_san_juan_chama_average_inflow_af_id, ub.USBR_NM_SAN_JUAN_CHAMA_TUNNEL_AF)
            df_utils.multiply_constant(self.df_daily, ub.USBR_NM_SAN_JUAN_CHAMA_TUNNEL_AF, ub.USBR_NM_SAN_JUAN_CHAMA_TUNNEL_CFS, 1/1.983459)

        if self.df_annual is not None:
            sheet.usbr_annuals(self.df_annual, self.usbr_rise_san_juan_chama_average_inflow_af_id, 2009, self.end_year,
                               month=all_b.WY,
                               title=ub.USBR_NM_SAN_JUAN_CHAMA_TUNNEL_AF, divisor=1)
            print('san juan chama')
