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
from sheet.sheet import Sheet
from typing import List

EQUALS = "="
MINUS = " - ("
PLUS = "+"
CLOSE = ")"
UPPER_CU = 'UPPER CU'
LOWER_CU = 'LOWER CU'

class III_C(Sheet):
    def __init__(self):
        headers = [all_b.III_C, EQUALS, lb.NATURAL_IMPERIAL, MINUS, LOWER_CU, PLUS, UPPER_CU, CLOSE, lb.MX_TREATY,
                              lb.HOOVER_RELEASE, ub.GLEN_CANYON_RELEASE]
        super().__init__(headers,  end_year=2024)
        self.years: List[int] = list(range(self.start_year, self.end_year+1))

    def load_df(self, df_compact : pd.DataFrame) -> None:
        df_len = len(self.df) + 2
        self.df[all_b.III_C] = [f"=D{row}-( F{row} + H{row})" for row in range(2, df_len)]
        self.df[EQUALS] = [f"=" for _ in range(2, df_len)]

        sheet.natural_flow_from_excel(self.df)

        self.df.loc[57:, lb.NATURAL_IMPERIAL] = df_compact[ub.NATURAL_LEES_FERRY].values[57:]
        self.df[MINUS] = [f"- (" for _ in range(2, df_len)]
        self.df[LOWER_CU] = [f"='{all_b.COMPACT}'!G{row} + '{all_b.COMPACT}'!I{row}" for row in range(2, df_len)]
        self.df[LOWER_CU] = self.df[LOWER_CU].astype(str)
        self.df[PLUS] = [f"+" for _ in range(2, df_len)]
        self.df[UPPER_CU] = [f"='{all_b.COMPACT}'!V{row}" for row in range(2, df_len)]
        self.df[UPPER_CU] = self.df[UPPER_CU].astype(str)

        self.df[lb.MX_TREATY] = [f"='{all_b.COMPACT}'!H{row}" for row in range(2, df_len)]

        df_hoover = sheet.read_csv('data/USBR_Reports/releases/usbr_releases_hoover_dam.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_hoover, lb.HOOVER_RELEASE)

        df_glen_canyon = sheet.read_csv('data/USBR_Reports/releases/usbr_releases_glen_canyon_dam.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_glen_canyon, ub.GLEN_CANYON_RELEASE)

        self.df[CLOSE] = [f")" for _ in range(2, df_len)]

    def build_sheet(self)-> None:
        self.set_column_negative_red(all_b.III_C)

        self.set_column_alignment(EQUALS, horizontal='center')
        self.set_column_alignment(MINUS, horizontal='center')
        self.set_column_alignment(PLUS, horizontal='center')
        self.set_column_alignment(CLOSE, horizontal='center')

        self.set_bg(lb.MX_TREATY, ub.GLEN_CANYON_RELEASE, color=all_b.USBR_AR_FLOW)
        self.set_bg(lb.NATURAL_IMPERIAL, color=all_b.USBR_NATURAL_BG)
        self.set_bg(LOWER_CU, color=all_b.USBR_AR_CU_BG)
        self.set_bg(UPPER_CU, color=all_b.USBR_UB_CUL_BG)

        self.format_header()

        self.set_column_width(EQUALS, 2)
        self.set_column_width(MINUS, 2)
        self.set_column_width(PLUS, 2)
        self.set_column_width(CLOSE, 2)


