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
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import Workbook
from graph.water import WaterGraph
from source import usbr_rise
from source.water_year_info import WaterYearInfo
import numpy as np
from report.doc import Report
import pandas as pd
from source.usgs_gage import USGSGage, daily_to_water_year
from typing import List, Tuple, Any
from sheet import sheet
from datetime import datetime

MEXICO = 'Mexico'
CA = 'CA'
AZ = 'AZ'
NV = 'NV'
LOWER_BASIN_CU = 'Lower Basin CU'
HOOVER_USGS = 'Hoover USGS'
HOOVER_RELEASE = 'Hoover Release'
H_M = 'Hv-Mx'
DIFF_7_5 = 'Diff 7.5'
MEAD_EVAPORATION = 'Mead Evaporation'
DIAMOND_CREEK = 'Diamond Creek'
MEAD = 'Mead'
POWELL = 'Powell'
POWELL_EVAPORATION = 'Powell Evaporation'
GLEN_CANYON = 'Glen Canyon'
LEES_FERRY_USGS = 'Lees Ferry USGS'
INFLOW = 'Inflow'
INFLOW_UNREGULATED = 'Inflow Unregulated'
UPPER_BASIN_CU = 'Upper Basin CU'
UPPER_BASIN_CO = 'CO'
UPPER_BASIN_UT = 'UT'
UPPER_BASIN_WY = 'WY'
UPPER_BASIN_NM = 'NM'
UPPER_BASIN_AZ = 'AZ_'

BORDER_NATURAL = 'Natural Border'
LEES_FERRY_NATURAL = 'Natural Lees Ferry'
GC_INFLOW = "GC Inflow"
GILA_NATURAL = "Natural Gila"
GILA_CU = "Gila Consumptive Use"
MEAD_ELEVATION = 'Mead Elevation'
POWELL_ELEVATION = 'Powell Elevation'
SALTON_ELEVATION = 'Salton Elevation'
SALTON_INFLOW = 'Salton Inflow'
ALAMO_RIVER = 'Alamo River'
NEW_RIVER = "New River"
WHITEWATER = "Whitewater"

IIIC = "iii(c)"
EQUALS = " = "
MINUS = " - ("
PLUS = " + "
CLOSE = ")"
UPPER_CU = 'UPPER CU'
LOWER_CU = 'LOWER CU'
MX_TREATY = 'MX TREATY'

LIGHT_RED_BG = 'fff0f0'
LIGHT_GREEN_BG = 'e8ffe0'
LIGHT_BLUE_BG = 'e0f0ff'
LIGHT_PURPLE_BG = 'ffe0ff'
LIGHT_YELLOW_BG = 'ffffd0'
LIGHT_ORANGE_BG = 'ffb66c'
LOWER_BASIN_AR_FLOW = 'b3cac7'

class Colorado:
    def __init__(self):
        self.start_year = 1964
        self.end_year = 2026
        self.headers = [LEES_FERRY_NATURAL, BORDER_NATURAL,
                        NV, AZ, CA, LOWER_BASIN_CU, MEXICO, MEAD_EVAPORATION, HOOVER_RELEASE,
                        H_M, DIFF_7_5, HOOVER_USGS, DIAMOND_CREEK, MEAD,
                        POWELL,POWELL_EVAPORATION, GLEN_CANYON, LEES_FERRY_USGS,
                        INFLOW, INFLOW_UNREGULATED,
                        UPPER_BASIN_CU, UPPER_BASIN_CO, UPPER_BASIN_UT, UPPER_BASIN_WY, UPPER_BASIN_NM, UPPER_BASIN_AZ,
                        GC_INFLOW, MEAD_ELEVATION, POWELL_ELEVATION,
                        SALTON_ELEVATION, SALTON_INFLOW, ALAMO_RIVER, NEW_RIVER, WHITEWATER]
        self.df = Colorado.create_df(self.start_year, self.end_year, self.headers)

        self.headers_iii_c = [IIIC, EQUALS, BORDER_NATURAL, MINUS, LOWER_CU, PLUS, UPPER_CU, CLOSE, MX_TREATY, HOOVER_RELEASE]
        self.df_iii_c = Colorado.create_df(self.start_year, self.end_year, self.headers_iii_c)

        file_path = Path('Colorado_River_Math.xlsx')
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            self.export_all(writer, 'Colorado River')
            self.export_iii_c(writer, 'iii(c)', self.df_iii_c)

            wb: Workbook = writer.book
            wb.calcMode = "auto"  # ensure automatic calculation

        notes_path = Path('Colorado_River_Notes.xlsx')
        sheet.copy_worksheet_to_new_workbook(
            source_wb_path=notes_path,
            sheet_name="Notes",
            target_wb_path=file_path
        )
        Report.open_docx_in_app(file_path)

    @staticmethod
    def lower_basin_annual_reports(df: pd.DataFrame):
        df_ca = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_total_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_ca, CA)

        df_az = sheet.read_csv('data/USBR_Reports/az/usbr_az_total_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_az, AZ)

        df_nv = sheet.read_csv('data/USBR_Reports/nv/usbr_nv_total_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(df, df_nv, NV)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(df, df_mx, MEXICO)

    def export_iii_c(self, writer: pd.ExcelWriter, sheet_name:str, df:pd.DataFrame) -> openpyxl.worksheet.worksheet.Worksheet:
        df[IIIC] = [f"=D{row}-( F{row} + H{row})" for row in range(2, len(df) + 2)]
        df[EQUALS] = [f"=" for _ in range(2, len(df) + 2)]
        self.natural_flow_from_excel(df)
        df.loc[57:, BORDER_NATURAL] = self.df[LEES_FERRY_NATURAL].values[57:]
        df[MINUS] = [f"- (" for _ in range(2, len(df) + 2)]
        df[LOWER_CU] = [f"='Colorado River'!G{row} + 'Colorado River'!I{row}" for row in range(2, len(df) + 2)]
        df[LOWER_CU] = df[LOWER_CU].astype(str)
        df[PLUS] = [f"+" for _ in range(2, len(df) + 2)]
        df[UPPER_CU] = [f"='Colorado River'!V{row}" for row in range(2, len(df) + 2)]
        df[UPPER_CU] = df[UPPER_CU].astype(str)

        df[MX_TREATY] = [f"='Colorado River'!H{row}" for row in range(2, len(df) + 2)]
        df[HOOVER_RELEASE] = [f"='Colorado River'!J{row}" for row in range(2, len(df) + 2)]

        df[CLOSE] = [f")" for _ in range(2, len(df) + 2)]

        ws, df_data = Colorado.export_to_excel(df, writer, sheet_name)

        for col in range(10, 12):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LOWER_BASIN_AR_FLOW)

        sheet.set_column_alignment(ws, 3, 2, len(df) + 2, horizontal='center')
        sheet.set_column_alignment(ws, 5, 2, len(df) + 2, horizontal='center')
        sheet.set_column_alignment(ws, 7, 2, len(df) + 2, horizontal='center')
        sheet.set_column_alignment(ws, 9, 2, len(df) + 2, horizontal='center')

        sheet.color_column(ws, 4, 2, ws.max_row, bg_color=LIGHT_GREEN_BG)
        sheet.color_column(ws, 6, 2, ws.max_row, bg_color=LIGHT_RED_BG)
        sheet.color_column(ws, 8, 2, ws.max_row, bg_color=LIGHT_ORANGE_BG)

        ws.column_dimensions['C'].width = 3
        ws.column_dimensions['E'].width = 3
        ws.column_dimensions['G'].width = 3

        sheet.set_column_negative_red(ws, 2, 2, len(df) + 2)
        sheet.format_header(ws, df_data)

        return ws

    def export_all(self, writer: pd.ExcelWriter, sheet_name:str) -> openpyxl.worksheet.worksheet.Worksheet:
        Colorado.upper_basin_cu_from_excel(self.df)
        Colorado.natural_flow_from_excel(self.df)
        Colorado.lf_natural_flow_from_excel(self.df)

        Colorado.lower_basin_annual_reports(self.df)

        self.df[LOWER_BASIN_CU] = [f'=SUM(D{row}:F{row})' for row in range(2, len(self.df) + 2)]
        self.df[LOWER_BASIN_CU] = self.df[LOWER_BASIN_CU].astype(str)

        df_mead_evap = sheet.read_csv('data/Colorado_River/mead_evap.csv', sep=',')
        sheet.merge_annual_column(self.df, df_mead_evap, MEAD_EVAPORATION, inp_column_name='Evaporation_AcreFeet')

        df_hoover = sheet.read_csv('data/USBR_Reports/releases/usbr_releases_hoover_dam.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_hoover, HOOVER_RELEASE)

        self.usgs_annuals('09421500', title=HOOVER_USGS)

        # FIXME - Have to change these to handle column changes automatically

        usbr_lake_mead_storage_af = 6124
        self.usbr_last_value(usbr_lake_mead_storage_af, title=MEAD, month=10)

        usbr_lake_powell_storage_af = 509
        self.usbr_last_value(usbr_lake_powell_storage_af, title=POWELL)

        usbr_lake_mead_elevation_ft = 6123
        self.usbr_last_value(usbr_lake_mead_elevation_ft, title=MEAD_ELEVATION, divisor=1)

        usbr_lake_powell_elevation_af = 508
        self.usbr_last_value(usbr_lake_powell_elevation_af, title=POWELL_ELEVATION, divisor=1)

        self.usgs_annuals('09404200', title=DIAMOND_CREEK, start_year=2007, offset=1)
        self.usgs_annuals('09380000', title=LEES_FERRY_USGS)

        usbr_lake_powell_evap_af = 510
        self.usbr_annuals(usbr_lake_powell_evap_af, title=POWELL_EVAPORATION)

        usbr_lake_powell_release_total_af = 4354
        self.usbr_annuals(usbr_lake_powell_release_total_af, title=GLEN_CANYON)

        usbr_lake_powell_regulated_inflow_af = 4288
        self.usbr_annuals(usbr_lake_powell_regulated_inflow_af, title=INFLOW)

        usbr_lake_powell_unregulated_inflow_af = 4301
        self.usbr_annuals(usbr_lake_powell_unregulated_inflow_af, title=INFLOW_UNREGULATED)

        self.df[GC_INFLOW][43:len(self.df)] = [f'=N{row}-S{row}' for row in range(45, len(self.df)+2)]

        self.salton_sea()

        ws, df_data = Colorado.export_to_excel(self.df, writer, sheet_name)

        dest_col_h_m = sheet.get_column_number(ws, H_M)
        dest_col_diff = sheet.get_column_number(ws, DIFF_7_5)

        for row in range(2, len(self.df) + 2):   # adjust range
            formula = f"=J{row} - H{row}"
            ws.cell(row=row, column=dest_col_h_m).value = formula
            formula = f"=K{row}-7.5"
            ws.cell(row=row, column=dest_col_diff).value = formula

        sheet.color_column(ws, 8, 2, ws.max_row, bg_color=LOWER_BASIN_AR_FLOW)
        sheet.color_column(ws, 10, 2, ws.max_row, bg_color=LOWER_BASIN_AR_FLOW)
        sheet.set_column_negative_red(ws, 12, 2, ws.max_row)

        sheet.add_borders_to_column(ws, 1, 1, ws.max_row, which='vertical')
        sheet.add_borders_to_column(ws, 3, 1, ws.max_row, which='right')
        sheet.add_borders_to_column(ws, 7, 1, ws.max_row, which='vertical')

        for col in range(2, 4):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_GREEN_BG)
        for col in range(4, 8):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_RED_BG)

        # USGS
        sheet.color_column(ws, 13, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)
        sheet.color_column(ws, 14, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)

        LOWER_BASIN_END_COL = 15
        # Reservoirs
        for col in range(LOWER_BASIN_END_COL, LOWER_BASIN_END_COL+2):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_BLUE_BG)

        sheet.color_column(ws, 17, 2, ws.max_row, bg_color=LIGHT_ORANGE_BG)

        sheet.add_borders_to_column(ws, LOWER_BASIN_END_COL, 1, ws.max_row, which='right', border_style='medium')
        sheet.add_borders_to_column(ws, 22, 1, ws.max_row, which='vertical')

        # USGS
        sheet.color_column(ws, 28, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)
        for col in range(18, 22):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)
        for col in range(32, 36):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)

        # Upper Basin CUL
        for col in range(22, 28):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_ORANGE_BG)

        # Elevations
        for col in range(29, 32):
            sheet.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_PURPLE_BG)

        sheet.format_header(ws, df_data)

        current_str = datetime.now().strftime("%m/%d/%Y %I:%M%p")
        ws.cell(row=1, column=len(self.headers)+2).value = current_str

        ws.sheet_properties.fullCalcOnLoad = True
        return ws

    def salton_sea(self):
        self.usgs_annuals('10254730', title=ALAMO_RIVER)          # 10254580 Alamo at border
        self.usgs_annuals('10255550', title=NEW_RIVER)    # 10254970 New at border
        self.usgs_annuals('10259540', title=WHITEWATER)

        self.df[SALTON_INFLOW] = [f'=SUM(AG{row}:AI{row})' for row in range(2, len(self.df) + 2)]

        self.usgs_value('10254005', start_year=1988, title=SALTON_ELEVATION, parameterCd='62614', statCd='00003')

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

    @staticmethod
    def export_to_excel(df:pd.DataFrame, writer: pd.ExcelWriter, sheet_name:str):
        df_data = pd.DataFrame(df)

        # df_data = MainFrame.insert_units_row(df_data, units)

        df_data.to_excel(writer, sheet_name=sheet_name, index=False)
        ws = writer.sheets[sheet_name]
        ws.freeze_panes = ws['B2']
        # Date column format
        #
        # for row in range(1, len(df_data) + 2):
        #    cell = ws.cell(row=row, column=1)
        #   cell.number_format = 'yyyy'

        sheet.format_sheet(ws, df_data)

        return ws, df_data

    @staticmethod
    def create_df(min_year, max_year, headers):
        years = list(range(min_year, max_year + 1))

        df = pd.DataFrame(index=range(len(years)), columns=['Year'] + headers)
        df['Year'] = years
        df.iloc[:, 1:] = pd.NA

        print(df.head())
        return df

    @staticmethod
    def max_used_column(ws):
        """
        Return the 1-based column index of the *right-most* cell that contains
        a value (int, float, str, datetime, bool, …).
        Formatted-but-empty cells are ignored.
        """
        max_col = 0
        # iter_rows() yields every cell that openpyxl knows about.
        # Empty cells are still present if they have a style, but .value is None.
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    max_col = max(max_col, cell.column)
        return max_col

    @staticmethod
    def lf_natural_flow_from_excel(df: pd.DataFrame):
        wb = openpyxl.load_workbook('data/Colorado_River/LFnatFlow1906-2024.2024.9.12.xlsx', data_only=True)
        ws = wb['Calendar Year']
        # ws = wb['AnnualCYTotalNaturalFlow']
        # ws = wb['TotalNaturalFlow']   # Monthly
        data_start_row = 62 # 1964
        data_end_row = 122  # 2020
        year_column_index = 1
        max_used_column = Colorado.max_used_column(ws)
        for column_index in range(ws.min_column, max_used_column + 1):
            # gage = ws.cell(row=gage_row, column=column_index).value
            # header = ws.cell(row=header_row, column=column_index).value
            # units = ws.cell(row=unit_row, column=column_index).value

            if column_index == 2: # Lees Ferry
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[0: 0 + len(values) - 1, LEES_FERRY_NATURAL] = values

    @staticmethod
    def natural_flow_from_excel(df:pd.DataFrame):
        wb = openpyxl.load_workbook('data/Colorado_River/NaturalFlows1906-2020_20221215.xlsx', data_only=True)
        ws = wb['AnnualCYTotalNaturalFlow']
        # ws = wb['AnnualCYTotalNaturalFlow']
        # ws = wb['TotalNaturalFlow']   # Monthly
        gage_row = 3
        unit_row = 6
        data_start_row = 65 # 1964
        data_end_row = 121  # 2020
        year_column_index = 3
        max_used_column = Colorado.max_used_column(ws)
        for column_index in range(ws.min_column, max_used_column + 1):
            gage = ws.cell(row=gage_row, column=column_index).value
            # header = ws.cell(row=header_row, column=column_index).value
            units = ws.cell(row=unit_row, column=column_index).value

            if units == 'Water Year':
                year_column_index = column_index

            if gage == '09429490': # Imperial
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[0: 0 + len(values) - 1, BORDER_NATURAL] = values

    @staticmethod
    def upper_basin_cu_from_excel(df:pd.DataFrame):
        wb = openpyxl.load_workbook('data/Colorado_River/V24.5_CUL_ResultsCU_CY.xlsx', data_only=True)
        ws = wb['CY Pivot']
        header_row = 2
        unit_row = 3
        data_start_row = 4 # 1971
        data_end_row = 57  # 2024, 2025 is partial not usable
        year_column_index = 1
        max_used_column = Colorado.max_used_column(ws)
        for column_index in range(ws.min_column, max_used_column + 1):
            header = ws.cell(row=header_row, column=column_index).value
            units = ws.cell(row=unit_row, column=column_index).value

            if units == 'Calendar Year':
                year_column_index = column_index

            if header == 'Grand Total':
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[7: 7 + len(values) - 1, UPPER_BASIN_CU] = values
            if header == 'Colorado':
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[7: 7 + len(values) - 1, UPPER_BASIN_CO] = values
            elif header == 'Utah':
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[7: 7 + len(values) - 1, UPPER_BASIN_UT] = values
            elif header == 'Wyoming':
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[7: 7 + len(values) - 1, UPPER_BASIN_WY] = values
            elif header == 'NewMexico':
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[7: 7 + len(values) - 1, UPPER_BASIN_NM] = values
            elif header == 'Arizona':
                pairs, values = Colorado.read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[7: 7 + len(values) - 1, UPPER_BASIN_AZ] = values

    @staticmethod
    def read_year_value_pairs(
            ws,
            year_col: int,
            value_col: int,
            start_row: int,
            end_row: int
    ) -> Tuple[List[Any], List[Any]]:
        """
        Reads year and value pairs from an openpyxl worksheet.

        Parameters:
        -----------
        ws : openpyxl.worksheet.worksheet.Worksheet
            The worksheet object to read from
        year_col : int
            Column index for the year (1 = A, 2 = B, etc.)
        value_col : int
            Column index for the value (1 = A, 2 = B, etc.)
        start_row : int
            First row to read (inclusive, 1-based)
        end_row : int
            Last row to read (inclusive, 1-based)

        Returns:
        --------
        List[Tuple[year, value]]
            List of (year, value) tuples
            - year will be int if possible, else str
            - value will be a float/int if numeric, else str

        Example:
        --------
        wb = load_workbook("data.xlsx")
        ws = wb["Sheet1"]
        pairs = read_year_value_pairs(ws, year_col=1, value_col=3, start_row=2, end_row=50)
        """
        pairs = []
        values = []

        for row in range(start_row, end_row + 1):
            # Get cells (1-based indexing in openpyxl)
            year_cell = ws.cell(row=row, column=year_col)
            value_cell = ws.cell(row=row, column=value_col)

            year = year_cell.value
            value = value_cell.value

            # Try to convert year to int (common for year columns)
            if year is not None:
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    pass  # keep as is (str or None)

            # Try to convert value to float/int
            if value is not None:
                try:
                    if isinstance(value, (int, float)):
                        pass  # already numeric
                    elif str(value).replace(".", "").replace("-", "").isdigit():
                        value = float(value) if "." in str(value) else int(value)
                    else:
                        value = str(value).strip()
                except (ValueError, TypeError):
                    value = str(value).strip() if value is not None else None

            # Only append if we have a year (skip completely empty rows)
            if year is not None:
                pairs.append((year, value / 1000000))
                values.append(value / 1000000)

        return pairs, values

    def usgs_annuals(self, gage_id, title='', start_year=None, parameterCd='00060', statCd='00003', month=10, offset=0):
        annuals = []
        values = []
        if not start_year:
            start_year = self.start_year
        if month != 1:
            start_year -= 1
        for year in range(start_year, self.end_year):
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            gage = USGSGage(gage_id)
            daily_af = gage.daily_discharge(water_year_info=water_year_info, alias=title, parameterCd=parameterCd,
                                            statCd=statCd)
            annual_af = daily_to_water_year(daily_af)
            result = (annual_af[0]['dt'], annual_af[0]['val'])
            annuals.append(result)
            if len(annual_af) == 1:
                values.append(annual_af[0][1] / 1000000)
                annuals.append(annual_af[0])
            else:
                print('Multiple years returned')

        if title:
            print(title)
            for annual in annuals:
                print(f'{annual[0]} {annual[1] / 1000000:10.2f} ')

        if title:
            if len(values) != len(self.df[title]):
                sheet.insert_values_from_year(self.df, title, start_year, values, offset=offset)
            else:
                self.df[title] = values

        return values

    def usgs_value(self, gage_id, title='', start_year=None, parameterCd='00060', statCd='00003', month=10):
        years = []
        annuals = []
        values = []
        if not start_year:
            start_year = self.start_year
        if month != 1:
            start_year -= 1
        for year in range(start_year, self.end_year):
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            gage = USGSGage(gage_id)
            daily_feet = gage.daily_discharge(water_year_info=water_year_info, alias=title, parameterCd=parameterCd,
                                            statCd=statCd)
            # total = daily_release_ft['val'].sum()
            feet = daily_feet[-1]
            years.append(year + 1)
            values.append(feet[1])
            annuals.append(feet)

        if title:
            print(title)
            for annual in annuals:
                # print(f'{annual[0]} {annual[1] / 1000000:10.2f} ')
                print(f'{annual[0]} {annual[1]:10.2f} ')

        if title:
            sheet.insert_values_from_year(self.df, title, start_year, values)

        return values

    def usbr_annuals(self, gage_id, title='', cfs_to_af=False, month=10):
        annuals = []
        values = []
        start_year = self.start_year
        if month != 1:
            start_year -= 1
        for year in range(start_year, self.end_year):
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            if cfs_to_af:
                info, daily_cfs = usbr_rise.load(gage_id, water_year_info=water_year_info)
                daily_af = WaterGraph.convert_cfs_to_af_per_day(daily_cfs)
            else:
                info, daily_af = usbr_rise.load(gage_id, water_year_info=water_year_info)

            # total = daily_release_ft['val'].sum()
            annual_af = WaterGraph.daily_to_water_year(daily_af, water_year_month=month)
            if len(annual_af) == 1:
                values.append(annual_af[0][1] / 1000000)
                annuals.append(annual_af[0])
            else:
                print('Multiple years returned')


        if title:
            print(title)
            for annual in annuals:
                print(f'{annual[0]} {annual[1] / 1000000:10.2f} ')

        if title:
            self.df[title] = values

        return values

    def usbr_last_value(self, gage_id, title='', cfs_to_af=False, month=10, divisor=1000000):
        years = []
        annuals = []
        values = []
        start_year = self.start_year
        if month != 1:
            start_year -= 1
        for year in range(start_year, self.end_year):
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            if cfs_to_af:
                info, daily_cfs = usbr_rise.load(gage_id, water_year_info=water_year_info)
                daily_af = WaterGraph.convert_cfs_to_af_per_day(daily_cfs)
            else:
                info, daily_af = usbr_rise.load(gage_id, water_year_info=water_year_info)

            # total = daily_release_ft['val'].sum()
            af = daily_af[-1]
            years.append(year + 1)
            values.append(af[1] / divisor)
            annuals.append(af)

        if title:
            print(title)
            for annual in annuals:
                print(f'{annual[0]} {annual[1] / divisor:10.2f} ')

        if title:
            year = self.df['Year'][0]
            if np.isnan(year):
                self.df['Year'] = years
            self.df[title] = values

        return values