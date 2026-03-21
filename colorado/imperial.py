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
import colorado.allb as all_b
import pandas as pd
from sheet import sheet
from sheet.sheet import Sheet, sheets
from sheet.sheet import cl, cn

class Imperial(Sheet):
    def __init__(self, name:str):
        headers = [lb.SALTON_ELEVATION, lb.SALTON_INFLOW,
                   lb.MX_ALAMO_RIVER, lb.ALAMO_RIVER,
                   lb.MX_NEW_RIVER, lb.NEW_RIVER,
                   lb.WHITEWATER,
                   lb.IMPERIAL_TOTAL_CU, lb.IMPERIAL_CU, lb.COACHELLA_CU]
        super().__init__(name, headers)
        sheets.append(self)

    def load_df(self, df_compact : pd.DataFrame) -> None:
        sheet.usgs_annuals(self.df, '10254730', self.start_year, self.end_year, title=lb.ALAMO_RIVER)
        sheet.usgs_annuals(self.df, '10255550', self.start_year, self.end_year, title=lb.NEW_RIVER)
        sheet.usgs_annuals(self.df, '10259540', self.start_year, self.end_year, title=lb.WHITEWATER)
        # Water quality/salinity
        # sheet.usgs_annuals(self.df, '10254580', self.start_year, self.end_year, title=lb.MX_ALAMO_RIVER)
        # sheet.usgs_annuals(self.df, '10254970', self.start_year, self.end_year, title=lb.MX_NEW_RIVER)

        self.df[lb.SALTON_INFLOW] = [f'=SUM(D{row}:F{row})' for row in range(2, len(self.df) + 2)]

        sheet.usgs_value(self.df, '10254005', 1989, self.end_year, title=lb.SALTON_ELEVATION, parameterCd='62614', statCd='00003')

        self.lower_basin_annual_reports(self.df)

    def build_sheet(self) -> None:
        ws = self.ws
        for row in range(2, len(self.df) + 2):
            formula = f"={cl(ws, lb.IMPERIAL_CU)}{row} + {cl(ws, lb.COACHELLA_CU)}{row}"
            ws.cell(row=row, column=cn(ws, lb.IMPERIAL_TOTAL_CU)).value = formula

        self.set_bg(lb.SALTON_ELEVATION, color=all_b.LIGHT_PURPLE_BG)
        self.set_bg(lb.SALTON_INFLOW, to=lb.WHITEWATER, color=all_b.LIGHT_YELLOW_BG)
        self.set_bg(lb.IMPERIAL_TOTAL_CU, to=lb.COACHELLA_CU, color=all_b.LIGHT_RED_BG)

        self.format_header()

    @staticmethod
    def lower_basin_annual_reports(df: pd.DataFrame):
        # df_div = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_imperial_irrigation_diversion.csv', sep='\s+')
        # sheet.merge_annual_column(df, df_div, lb.IMPERIAL_DIVERSION)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_imperial_irrigation_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_cu, lb.IMPERIAL_CU)

        # df_div = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_coachella_diversion.csv', sep='\s+')
        # sheet.merge_annual_column(df, df_div, lb.COACHELLA_DIVERSION)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_coachella_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_cu, lb.COACHELLA_CU)

