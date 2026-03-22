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
        headers = [all_b.III_D, ub.LEES_FERRY_USGS, ub.NATURAL_LEES_FERRY,
                   all_b.III_C, all_b.III_C_AZ, lb.MEXICO]
        super().__init__(name, headers,  end_year=2026)
        self.years: List[int] = list(range(self.start_year, self.end_year+1))
        sheets.append(self)

    def load_df(self, df_compact : pd.DataFrame) -> None:
        df_len = len(self.df) + 2

        sheet.lf_natural_flow_from_excel(self.df)

        sheet.usgs_annuals(self.df, '09380000', self.start_year, self.end_year, title=ub.LEES_FERRY_USGS)

    def build_sheet(self)-> None:
        # self.set_column_negative_red(all_b.III_C)
        self.set_bg(lb.NATURAL_IMPERIAL, color=all_b.USBR_NATURAL_BG)
        self.set_bg(ub.NATURAL_LEES_FERRY, color=all_b.USBR_NATURAL_BG)

        values = sheet.usgs_annuals(self.df, '09380000', 1955, self.end_year) # ub.LEES_FERRY_USGS
        ten_year = sheet.moving_average_10yr(values)
        sheet.write_column(self.ws, all_b.III_D, ten_year)

        sheet.clear_range(self.ws, self.ws.max_row, self.ws.max_row, 1, self.ws.max_column)
        self.format_header()


