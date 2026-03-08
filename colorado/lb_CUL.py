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
from sheet.sheet import Sheet
from sheet.sheet import cl, cn
from sheet import sheet


class LB_CUL(Sheet):
    def __init__(self):
        headers = [lb.MEAD]
        super().__init__(headers)

    def load_df(self, df_compact : pd.DataFrame) -> None:
        sheet.lower_basin_cu_from_excel(self.df)

    def build_sheet(self) -> None:
        ws = self.ws

        # self.set_bg(lb.SALTON_INFLOW, to=lb.WHITEWATER, color=all_b.LIGHT_YELLOW_BG)
        # self.set_bg(lb.IMPERIAL_TOTAL_CU, to=lb.COACHELLA_CU, color=all_b.LIGHT_RED_BG)

        self.format_header()
