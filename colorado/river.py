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
import openpyxl
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from source import usbr_rise
from source.water_year_info import WaterYearInfo
from datetime import datetime
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as allb
import pandas as pd
from report.doc import Report
from sheet import sheet
from colorado.iii_c import III_C

class Colorado:
    def __init__(self):
        self.start_year = 1964
        self.end_year = 2026
        self.headers = [ub.LEES_FERRY_NATURAL, lb.BORDER_NATURAL,
                        lb.CU_NV, lb.CU_AZ, lb.CU_CA, lb.CU, lb.MEXICO, lb.MEAD_EVAPORATION, lb.HOOVER_RELEASE,
                        lb.H_M, lb.DIFF_7_5, lb.HOOVER_USGS, lb.DIAMOND_CREEK, lb.MEAD,
                        ub.POWELL,ub.POWELL_EVAPORATION, ub.GLEN_CANYON, ub.LEES_FERRY_USGS,
                        ub.INFLOW, ub.INFLOW_UNREGULATED,
                        ub.CU, ub.CU_CO, ub.CU_UT, ub.CU_WY,
                        ub.CU_NM, ub.CU_AZ,
                        lb.GC_INFLOW, lb.MEAD_ELEVATION, ub.POWELL_ELEVATION,
                        lb.SALTON_ELEVATION, lb.SALTON_INFLOW, lb.ALAMO_RIVER, lb.NEW_RIVER, lb.WHITEWATER]
        self.df = sheet.create_df(self.start_year, self.end_year, self.headers)



    @staticmethod
    def lower_basin_annual_reports(df: pd.DataFrame):
        df_ca = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_total_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_ca, lb.CU_CA)

        df_az = sheet.read_csv('data/USBR_Reports/az/usbr_az_total_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_az, lb.CU_AZ)

        df_nv = sheet.read_csv('data/USBR_Reports/nv/usbr_nv_total_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_nv,lb.CU_NV)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(df, df_mx, lb.MEXICO)

    def export(self, writer: pd.ExcelWriter, sheet_name:str) -> openpyxl.worksheet.worksheet.Worksheet:
        sheet.upper_basin_cu_from_excel(self.df)
        sheet.natural_flow_from_excel(self.df)
        sheet.lf_natural_flow_from_excel(self.df)

        Colorado.lower_basin_annual_reports(self.df)

        self.df[lb.CU] = [f'=SUM(D{row}:F{row})' for row in range(2, len(self.df) + 2)]
        self.df[lb.CU] = self.df[lb.CU].astype(str)

        df_mead_evap = sheet.read_csv('data/Colorado_River/mead_evap.csv', sep=',')
        sheet.merge_annual_column(self.df, df_mead_evap, lb.MEAD_EVAPORATION, inp_column_name='Evaporation_AcreFeet')

        df_hoover = sheet.read_csv('data/USBR_Reports/releases/usbr_releases_hoover_dam.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_hoover, lb.HOOVER_RELEASE)

        sheet.usgs_annuals(self.df, '09421500', self.start_year, self.end_year, title=lb.HOOVER_USGS)

        # FIXME - Have to change these to handle column changes automatically

        usbr_lake_mead_storage_af = 6124
        sheet.usbr_last_value(self.df, usbr_lake_mead_storage_af, self.start_year, self.end_year, title=lb.MEAD, month=10)

        usbr_lake_powell_storage_af = 509
        sheet.usbr_last_value(self.df, usbr_lake_powell_storage_af, self.start_year, self.end_year,  title=ub.POWELL)

        usbr_lake_mead_elevation_ft = 6123
        sheet.usbr_last_value(self.df, usbr_lake_mead_elevation_ft, self.start_year, self.end_year, title=lb.MEAD_ELEVATION, divisor=1)

        usbr_lake_powell_elevation_af = 508
        sheet.usbr_last_value(self.df, usbr_lake_powell_elevation_af, self.start_year, self.end_year, title=ub.POWELL_ELEVATION, divisor=1)

        sheet.usgs_annuals(self.df, '09404200', 2007, self.end_year,  title=lb.DIAMOND_CREEK, offset=1)
        sheet.usgs_annuals(self.df, '09380000', self.start_year, self.end_year, title=ub.LEES_FERRY_USGS)

        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(self.df, usbr_lake_powell_evap_af, self.start_year, self.end_year,  title=ub.POWELL_EVAPORATION)

        usbr_lake_powell_release_total_af = 4354
        sheet.usbr_annuals(self.df, usbr_lake_powell_release_total_af, self.start_year, self.end_year, title=ub.GLEN_CANYON)

        usbr_lake_powell_regulated_inflow_af = 4288
        sheet.usbr_annuals(self.df, usbr_lake_powell_regulated_inflow_af, self.start_year, self.end_year, title=ub.INFLOW)

        usbr_lake_powell_unregulated_inflow_af = 4301
        sheet.usbr_annuals(self.df, usbr_lake_powell_unregulated_inflow_af, self.start_year, self.end_year, title=ub.INFLOW_UNREGULATED)

        self.df[lb.GC_INFLOW][43:len(self.df)] = [f'=N{row}-S{row}' for row in range(45, len(self.df)+2)]

        self.salton_sea()

        ws, df_data = sheet.export_to_excel(self.df, writer, sheet_name)

        dest_col_h_m = sheet.get_column_number(ws, lb.H_M)
        dest_col_diff = sheet.get_column_number(ws, lb.DIFF_7_5)

        for row in range(2, len(self.df) + 2):   # adjust range
            formula = f"=J{row} - H{row}"
            ws.cell(row=row, column=dest_col_h_m).value = formula
            formula = f"=K{row}-7.5"
            ws.cell(row=row, column=dest_col_diff).value = formula

        sheet.color_column(ws, 8, 2, ws.max_row, bg_color=lb.LOWER_BASIN_AR_FLOW)
        sheet.color_column(ws, 10, 2, ws.max_row, bg_color=lb.LOWER_BASIN_AR_FLOW)
        sheet.set_column_negative_red(ws, 12, 2, ws.max_row)

        sheet.add_borders_to_column(ws, 1, 1, ws.max_row, which='vertical')
        sheet.add_borders_to_column(ws, 3, 1, ws.max_row, which='right')
        sheet.add_borders_to_column(ws, 7, 1, ws.max_row, which='vertical')

        for col in range(2, 4):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_GREEN_BG)
        for col in range(4, 8):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_RED_BG)

        # USGS
        sheet.color_column(ws, 13, 2, ws.max_row, bg_color=allb.LIGHT_YELLOW_BG)
        sheet.color_column(ws, 14, 2, ws.max_row, bg_color=allb.LIGHT_YELLOW_BG)

        lower_basin_end_col = 15
        # Reservoirs
        for col in range(lower_basin_end_col, lower_basin_end_col+2):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_BLUE_BG)

        sheet.color_column(ws, 17, 2, ws.max_row, bg_color=allb.LIGHT_ORANGE_BG)

        sheet.add_borders_to_column(ws, lower_basin_end_col, 1, ws.max_row, which='right', border_style='medium')
        sheet.add_borders_to_column(ws, 22, 1, ws.max_row, which='vertical')

        # USGS
        sheet.color_column(ws, 28, 2, ws.max_row, bg_color=allb.LIGHT_YELLOW_BG)
        for col in range(18, 22):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_YELLOW_BG)
        for col in range(32, 36):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_YELLOW_BG)

        # Upper Basin CUL
        for col in range(22, 28):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_ORANGE_BG)

        # Elevations
        for col in range(29, 32):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=allb.LIGHT_PURPLE_BG)

        sheet.format_header(ws, df_data)

        current_str = datetime.now().strftime("%m/%d/%Y %I:%M%p")
        ws.cell(row=1, column=len(self.headers)+2).value = current_str

        ws.sheet_properties.fullCalcOnLoad = True
        return ws

    def salton_sea(self):
        sheet.usgs_annuals(self.df, '10254730', self.start_year, self.end_year, title=lb.ALAMO_RIVER)          # 10254580 Alamo at border
        sheet.usgs_annuals(self.df, '10255550', self.start_year, self.end_year, title=lb.NEW_RIVER)    # 10254970 New at border
        sheet.usgs_annuals(self.df, '10259540', self.start_year, self.end_year, title=lb.WHITEWATER)

        self.df[lb.SALTON_INFLOW] = [f'=SUM(AG{row}:AI{row})' for row in range(2, len(self.df) + 2)]

        sheet.usgs_value(self.df, '10254005', 1988, self.end_year, title=lb.SALTON_ELEVATION, parameterCd='62614', statCd='00003')

    @staticmethod
    def lake_powell(clicked_str):
        annuals_total = None
        # https://pubs.usgs.gov/sir/2022/5017/sir20225017.pdf
        # https://www.sciencebase.gov/catalog/item/614ccd07d34e0df5fb9868e2

        # 510: Daily Lake/Reservoir Evaporation - af (acre-feet per day; this is the primary evaporation loss series for Lake Powell)
        # 4301: Daily Lake/Reservoir Inflow - Unregulated - af (daily total unregulated inflow volume in acre-feet; key for natural supply calculations, forecasts, and storage change)
        # 512: Daily Lake/Reservoir Inflow - Unregulated - cfs (same as above but in cubic feet per second; often used interchangeably or converted to af)
        # 4288: Daily Lake/Reservoir Inflow - af (total regulated/observed inflow; contrasts with unregulated)
        # 511: Daily Lake/Reservoir Inflow - cfs (total inflow in cfs)
        # 4354: Daily Lake/Reservoir Release - Total - af (total dam releases, as we discussed earlier)
        # 507: Daily Lake/Reservoir Release - Power plant - cfs
        # 508: Daily Lake/Reservoir Elevation - ft (pool elevation)

        if clicked_str == 'Lake Powell Elevation':
            ts = pd.Timestamp('2025-11-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=10)
            usbr_lake_powell_elevation_af = 508
            usbr_rise.load(usbr_lake_powell_elevation_af, water_year_info=water_year_info)
        return annuals_total

def run():
    iii_c = III_C()
    colorado = Colorado()

    file_path = Path('Colorado_River_Math.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        colorado.export(writer, 'Colorado River')
        iii_c.export(writer, 'iii(c)', colorado.df)

        wb: Workbook = writer.book
        wb.calcMode = "auto"  # ensure automatic calculation

    notes_path = Path('Colorado_River_Notes.xlsx')
    sheet.copy_worksheet_to_new_workbook(
        source_wb_path=notes_path,
        sheet_name="Notes",
        target_wb_path=file_path
    )
    Report.open_docx_in_app(file_path)