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
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
import pandas as pd
from sheet import sheet
from sheet.sheet import Sheet, sheets
from typing import List

class III_D(Sheet):
    def __init__(self, name:str):
        headers = [ub.NATURAL_LEES_FERRY, all_b.III_D, ub.LEES_FERRY_USGS,
                   ub.GLEN_CANYON, ub.POWELL, ub.POWELL_DELTA, ub.POWELL_EVAPORATION,
                   ub.POWELL_ELEVATION, ub.POWELL_ELEVATION_DELTA,
                   ub.INFLOW, ub.INFLOW_UNREGULATED,]
        super().__init__(name, headers,  start_year=1921, end_year=2026)
        self.years: List[int] = list(range(self.start_year, self.end_year+1))
        sheets.append(self)

    def load_df(self, df_compact : pd.DataFrame) -> None:
        df_len = len(self.df) + 2

        sheet.lf_natural_flow_from_excel(self.df, start_row=19)

        sheet.usgs_annuals(self.df, '09380000', self.start_year, self.end_year, title=ub.LEES_FERRY_USGS)

        usbr_lake_powell_storage_af = 509
        sheet.usbr_last_value(self.df, usbr_lake_powell_storage_af, 1964, self.end_year,  title=ub.POWELL)

        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(self.df, usbr_lake_powell_evap_af, 1965, self.end_year,  title=ub.POWELL_EVAPORATION)

        usbr_lake_powell_release_total_af = 4354
        sheet.usbr_annuals(self.df, usbr_lake_powell_release_total_af, 1964, self.end_year, title=ub.GLEN_CANYON)

        usbr_lake_powell_regulated_inflow_af = 4288
        sheet.usbr_annuals(self.df, usbr_lake_powell_regulated_inflow_af, 1964, self.end_year, title=ub.INFLOW)

        usbr_lake_powell_unregulated_inflow_af = 4301
        sheet.usbr_annuals(self.df, usbr_lake_powell_unregulated_inflow_af, 1964, self.end_year, title=ub.INFLOW_UNREGULATED)

        usbr_lake_powell_elevation_af = 508
        sheet.usbr_last_value(self.df, usbr_lake_powell_elevation_af, 1965, self.end_year, title=ub.POWELL_ELEVATION, divisor=1)


    def build_sheet(self)-> None:
        # self.set_column_negative_red(all_b.III_C)
        self.set_bg(ub.NATURAL_LEES_FERRY, color=all_b.USBR_NATURAL_BG)
        self.set_bg(ub.LEES_FERRY_USGS, color=all_b.USGS_BG)
        self.set_bg(ub.GLEN_CANYON, color=all_b.USGS_BG)

        self.set_bg(ub.POWELL, color=all_b.LIGHT_BLUE_BG)
        sheet.formula_delta(self.ws, self.df, ub.POWELL_DELTA, ub.POWELL, start_row=45)
        self.set_column_negative_red(ub.POWELL_DELTA, negative_color='Red', positive_color='Color22')
        self.set_bg(ub.POWELL, color=all_b.LIGHT_BLUE_BG)
        self.set_bg(ub.POWELL_DELTA, color=all_b.LIGHT_BLUE_BG)
        self.set_bg(ub.POWELL_EVAPORATION, color=all_b.EVAPORATION_BG)
        self.set_bg(ub.POWELL_ELEVATION, color=all_b.USBR_RISE_ELEVATION_BG)
        self.set_bg(ub.POWELL_ELEVATION_DELTA, color=all_b.USBR_RISE_ELEVATION_BG)

        self.set_bg(ub.INFLOW, color=all_b.USGS_BG)
        self.set_bg(ub.INFLOW_UNREGULATED, color=all_b.USGS_BG)

        sheet.formula_delta(self.ws, self.df, ub.POWELL_ELEVATION_DELTA, ub.POWELL_ELEVATION,
                            start_row=45)
        self.set_column_negative_red(ub.POWELL_ELEVATION_DELTA, negative_color='Red',
                                     positive_color='Color22')

        # values = sheet.usgs_annuals(self.df, '09380000', 1955, self.end_year) # ub.LEES_FERRY_USGS
        # ten_year = sheet.moving_average_10yr(values)
        # sheet.write_column(self.ws, all_b.III_D, ten_year)

        sheet.formula(self.ws, self.df, all_b.III_D,
                      f"=AVERAGE('{ub.LEES_FERRY_USGS}'[row-9]:'{ub.LEES_FERRY_USGS}'[row])",
                      start_row=10, insert_row_index=False)

        sheet.clear_range(self.ws, self.ws.max_row, self.ws.max_row, 1, self.ws.max_column)
        self.format_header()
        self.set_column_width(ub.NATURAL_LEES_FERRY, 7, to=ub.INFLOW_UNREGULATED)



