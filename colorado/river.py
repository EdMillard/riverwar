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
from openpyxl.styles import Alignment, Font, PatternFill, Side, Border
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from graph.water import WaterGraph
from source import usbr_rise
from source.water_year_info import WaterYearInfo
import numpy as np
from report.doc import Report
import pandas as pd
from io import StringIO
from source.usgs_gage import USGSGage, daily_to_water_year
from typing import List, Tuple, Union

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

class Colorado():
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
        writer =  pd.ExcelWriter(file_path, engine='openpyxl')

        ws = self.export_all(writer, 'Colorado River')
        ws = self.export_iii_c(writer, 'iii(c)', self.df_iii_c)

        writer.close()
        Report.open_docx_in_app(file_path)

    def merge_annual_column(self, df:pd.DataFrame, annual_df:pd.DataFrame,
                            column_name:str, inp_column_name='Total'):
        annual_df[inp_column_name] = annual_df[inp_column_name] / 1_000_000
        df1 = df.merge(
            annual_df[['Year', inp_column_name]],
            on='Year',
            how='left'  # keeps all rows from df1, fills NaN where no match
        )
        df[column_name] = df1[inp_column_name].combine_first(df1[column_name])

    def lower_basin_annual_reports(self, df: pd.DataFrame):
        df_ca = Colorado.read_csv('data/USBR_Reports/ca/usbr_ca_total_consumptive_use.csv', sep='\s+')
        self.merge_annual_column(df, df_ca, CA)

        df_az = Colorado.read_csv('data/USBR_Reports/az/usbr_az_total_consumptive_use.csv', sep='\s+')
        self.merge_annual_column(df, df_az, AZ)

        df_nv = Colorado.read_csv('data/USBR_Reports/nv/usbr_nv_total_consumptive_use.csv', sep='\s+')
        self.merge_annual_column(df, df_nv, NV)

        df_mx = Colorado.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        self.merge_annual_column(df, df_mx, MEXICO)

    def export_iii_c(self, writer: pd.ExcelWriter, sheet_name:str, df:pd.DataFrame) -> openpyxl.worksheet.worksheet.Worksheet:
        df[IIIC] = [f"=D{row}-( F{row} + H{row})" for row in range(2, len(df) + 2)]
        df[EQUALS] = [f"=" for row in range(2, len(df) + 2)]
        self.natural_flow_from_excel(df)
        df.loc[57:, BORDER_NATURAL] = self.df[LEES_FERRY_NATURAL].values[57:]
        df[MINUS] = [f"- (" for row in range(2, len(df) + 2)]
        df[LOWER_CU] = [f"='Colorado River'!G{row} + 'Colorado River'!I{row}" for row in range(2, len(df) + 2)]
        df[PLUS] = [f"+" for row in range(2, len(df) + 2)]
        df[UPPER_CU] = [f"='Colorado River'!V{row}" for row in range(2, len(df) + 2)]

        df[MX_TREATY] = [f"='Colorado River'!H{row}" for row in range(2, len(df) + 2)]
        df[HOOVER_RELEASE] = [f"='Colorado River'!J{row}" for row in range(2, len(df) + 2)]

        df[CLOSE] = [f")" for row in range(2, len(df) + 2)]

        ws, df_data = self.export_to_excel(df, writer, sheet_name)

        Colorado.set_column_alignment(ws, 3, 2, len(df) + 2, horizontal='center')
        Colorado.set_column_alignment(ws, 5, 2, len(df) + 2, horizontal='center')
        Colorado.set_column_alignment(ws, 7, 2, len(df) + 2, horizontal='center')
        Colorado.set_column_alignment(ws, 9, 2, len(df) + 2, horizontal='center')

        Colorado.color_column(ws, 4, 2, ws.max_row, bg_color=LIGHT_GREEN_BG)
        Colorado.color_column(ws, 6, 2, ws.max_row, bg_color=LIGHT_RED_BG)
        Colorado.color_column(ws, 8, 2, ws.max_row, bg_color=LIGHT_RED_BG)

        ws.column_dimensions['C'].width = 3
        ws.column_dimensions['E'].width = 3
        ws.column_dimensions['G'].width = 3

        Colorado.set_column_negative_red(ws, 2, 2, len(df) + 2)
        Colorado.format_header(ws, df_data)

        return ws

    def export_all(self, writer: pd.ExcelWriter, sheet_name:str) -> openpyxl.worksheet.worksheet.Worksheet:
        Colorado.upper_basin_cu_from_excel(self.df)
        Colorado.natural_flow_from_excel(self.df)
        Colorado.lf_natural_flow_from_excel(self.df)

        self.lower_basin_annual_reports(self.df)

        self.df[LOWER_BASIN_CU] = [f'=SUM(D{row}:F{row})' for row in range(2, len(self.df) + 2)]

        df_mead_evap = Colorado.read_csv('data/Colorado_River/mead_evap.csv', sep=',')
        self.merge_annual_column(self.df, df_mead_evap, MEAD_EVAPORATION, inp_column_name='Evaporation_AcreFeet')

        df_hoover = Colorado.read_csv('data/USBR_Reports/releases/usbr_releases_hoover_dam.csv', sep='\s+')
        self.merge_annual_column(self.df, df_hoover, HOOVER_RELEASE)

        self.usgs_annuals('09421500', title=HOOVER_USGS)

        # FIXME - Have to change these to handle column chamges automatically
        self.df[H_M] = [f'=J{row}-H{row}' for row in range(2, len(self.df) + 2)]
        self.df[DIFF_7_5] = [f'=K{row}-7.5' for row in range(2, len(self.df) + 2)]

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

        ws, df_data = self.export_to_excel(self.df, writer, sheet_name)

        Colorado.add_borders_to_column(ws, 1, 1, ws.max_row, which='vertical')
        Colorado.add_borders_to_column(ws, 3, 1, ws.max_row, which='right')
        Colorado.add_borders_to_column(ws, 7, 1, ws.max_row, which='vertical')

        for col in range(2, 4):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_GREEN_BG)
        for col in range(4, 10):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_RED_BG)

        # USGS
        Colorado.color_column(ws, 13, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)
        Colorado.color_column(ws, 14, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)

        LOWER_BASIN_END_COL = 15
        # Reservoirs
        for col in range(LOWER_BASIN_END_COL, LOWER_BASIN_END_COL+2):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_BLUE_BG)

        Colorado.color_column(ws, 17, 2, ws.max_row, bg_color=LIGHT_RED_BG)

        Colorado.add_borders_to_column(ws, LOWER_BASIN_END_COL, 1, ws.max_row, which='right', border_style='medium')
        Colorado.add_borders_to_column(ws, 22, 1, ws.max_row, which='vertical')

        # USGS
        Colorado.color_column(ws, 28, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)
        for col in range(18, 22):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)
        for col in range(32, 36):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_YELLOW_BG)

        # Upper Basin CUL
        for col in range(22, 28):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_RED_BG)

        # Elevations
        for col in range(29, 32):
            Colorado.color_column(ws, col, 2, ws.max_row, bg_color=LIGHT_PURPLE_BG)

        Colorado.format_header(ws, df_data)

        return ws

    def salton_sea(self):
        self.usgs_annuals('10254730', title=ALAMO_RIVER)          # 10254580 Alamo at border
        self.usgs_annuals('10255550', title=NEW_RIVER)    # 10254970 New at border
        self.usgs_annuals('10259540', title=WHITEWATER)

        self.df[SALTON_INFLOW] = [f'=SUM(AG{row}:AI{row})' for row in range(2, len(self.df) + 2)]

        self.usgs_value('10254005', start_year=1988, title=SALTON_ELEVATION, parameterCd='62614', statCd='00003')

    def lake_powell(self, clicked_str):
        annuals_total = None
        # https://pubs.usgs.gov/sir/2022/5017/sir20225017.pdf
        # https://www.sciencebase.gov/catalog/item/614ccd07d34e0df5fb9868e2

        # 510: Daily Lake/Reservoir Evaporation - af (acre-feet per day; this is the primary evaporation loss series for Lake Powell)
        # 4301: Daily Lake/Reservoir Inflow - Unregulated - af (daily total unregulated inflow volume in acre-feet; key for natural supply calculations, forecasts, and storage change)
        # 512: Daily Lake/Reservoir Inflow - Unregulated - cfs (same as above but in cubic feet per second; often used interchangeably or converted to af)
        # 4288: Daily Lake/Reservoir Inflow - af (total regulated/observed inflow; contrasts with unregulated)
        # 511: Daily Lake/Reservoir Inflow - cfs (total inflow in cfs)
        # 4354: Daily Lake/Reservoir Release - Total - af (total dam releases, as we discussed earlier)
        # 507: Daily Lake/Reservoir Release - Powerplant - cfs
        # 508: Daily Lake/Reservoir Elevation - ft (pool elevation)

        if clicked_str == 'Lake Powell Elevation':
            ts = pd.Timestamp('2025-11-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=10)
            usbr_lake_powell_elevation_af = 508
            info, usbr_lake_powell_evaporation_af = usbr_rise.load(usbr_lake_powell_elevation_af,
                                                                   water_year_info=water_year_info)
        return annuals_total

    @staticmethod
    def read_csv(filename, sep='\s+', comment_char='#'):
        cleaned_lines = []
        with open(filename, 'r') as f:
            for line in f:
                # Remove everything from comment_char to end of line
                line = line.split(comment_char, 1)[0].rstrip()
                # Skip completely empty lines after cleaning
                if line.strip():
                    cleaned_lines.append(line)

        # Now feed the cleaned text to pandas
        clean_text = '\n'.join(cleaned_lines)
        df = pd.read_csv(StringIO(clean_text), sep=sep, comment=comment_char)
        return df

    @staticmethod
    def format_sheet(ws, df):
        # Set font for everything
        red_font = Font(name='Arial Narrow', size=10, color="700000")
        green_font = Font(name='Arial Narrow', size=10, color="007000")
        blue_font = Font(name='Arial Narrow', size=10, color="000070")
        black_font = Font(name='Arial Narrow', size=10, color="000000") # RRGGBB hex
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.font = black_font
                # cell.fill = red_fill

        # Set default float format for all columns except date
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=ws.max_column):
            for cell in row:
                cell.number_format = '0.00'

    # Variable name ahd units Row centered
    #
    @staticmethod
    def format_header(ws, df):

        start_row = 1
        end_row = 2
        start_col = 1
        end_col = len(df.columns) + 1
        ws.row_dimensions[1].height = 25
        for col in range(1, end_col):
            ws.column_dimensions[get_column_letter(col)].width = 5
            for row in range(start_row, end_row):
                cell = ws.cell(row=row, column=col)
                cell.alignment = Alignment(wrap_text=True, vertical='top', horizontal='center')

        Colorado.add_borders_to_column(ws, start_col, start_row, end_row-1, end_col=end_col-1, which='none')
        Colorado.add_borders_to_column(ws, start_col, start_row, end_row-1, end_col=end_col-1, which='outer')

    @staticmethod
    def insert_units_row(df, variable_name_to_units):
        variable_names = df.columns.tolist()
        units = []
        for variable_name in variable_names:
            unit = variable_name_to_units.get(variable_name)
            if unit:
                units.append(unit)
            else:
                units.append('')
        df.loc[-1] = units  # Add units row at index -1
        df.index = df.index + 1  # Shift index
        df = df.sort_index()  # Sort to move units row to position 0
        return df.reset_index(drop=True)

    def export_to_excel(self, df:pd.DataFrame, writer: pd.ExcelWriter, sheet_name:str):
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

        Colorado.format_sheet(ws, df_data)

        return ws, df_data

    @staticmethod
    def color_column(
            ws,
            column: str | int,  # e.g. "C" or 3
            start_row: int,
            end_row: int,
            fg_color: str = "FFFFFF",  # foreground / fill color (hex without #)
            bg_color: str = None,  # optional separate background (usually same as fg)
            text_color: str = "000000",  # font color (usually black)
    ) -> None:
        """
        Apply fill (background) and font color to a specific column over a row range.

        Args:
            ws: openpyxl worksheet object
            column: column letter ("A", "C") or column number (1-based)
            start_row: first row to color (inclusive)
            end_row: last row to color (inclusive)
            fg_color: fill color hex (e.g. "FFFF00" = yellow) - without #
            bg_color: if you want different background vs foreground (rare)
            text_color: font color hex (e.g. "FF0000" = red)

        Example:
            color_column(ws, "D", 5, 25, fg_color="FFD966", text_color="000000")
        """
        # Normalize column to letter
        if isinstance(column, int):
            col_letter = get_column_letter(column)
        else:
            col_letter = column.upper()

        # Decide fill color (most people mean background when they say "background color")
        fill_color = bg_color if bg_color else fg_color

        # Create fill style
        fill = PatternFill(
            start_color=fill_color,
            end_color=fill_color,
            fill_type="solid"
        )

        # Create font style
        font = Font(name='Arial Narrow', size=10, color=text_color)

        # Apply to each cell in the range
        for row in range(start_row, end_row + 1):
            cell = ws[f"{col_letter}{row}"]
            cell.fill = fill
            cell.font = font


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
        gage_row = 3
        header_row = 5
        unit_row = 6
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
        header_row = 5
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
    ) -> List[Tuple[Union[int, str], Union[float, int, str]]]:
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
            - value will be float/int if numeric, else str

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

    def usgs_annuals(self, id, title='', start_year=None, parameterCd='00060', statCd='00003', month=10, offset=0):
        annuals = []
        values = []
        if not start_year:
            start_year = self.start_year
        if month != 1:
            start_year -= 1
        for year in range(start_year, self.end_year):
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            gage = USGSGage(id)
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
                self.insert_values_from_year(self.df, title, start_year, values, offset=offset)
            else:
                self.df[title] = values

        return values

    def usgs_value(self, id, title='', start_year=None, parameterCd='00060', statCd='00003', month=10):
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
            gage = USGSGage(id)
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
            self.insert_values_from_year(self.df, title, start_year, values)

        return values

    def usbr_annuals(self, id, title='', cfs_to_af=False, month=10):
        annuals = []
        values = []
        start_year = self.start_year
        if month != 1:
            start_year -= 1
        for year in range(start_year, self.end_year):
            ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            if cfs_to_af:
                info, daily_cfs = usbr_rise.load(id, water_year_info=water_year_info)
                daily_af = WaterGraph.convert_cfs_to_af_per_day(daily_cfs)
            else:
                info, daily_af = usbr_rise.load(id, water_year_info=water_year_info)

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

    def usbr_last_value(self, id, title='', cfs_to_af=False, month=10, divisor=1000000):
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
                info, daily_cfs = usbr_rise.load(id, water_year_info=water_year_info)
                daily_af = WaterGraph.convert_cfs_to_af_per_day(daily_cfs)
            else:
                info, daily_af = usbr_rise.load(id, water_year_info=water_year_info)

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

    @staticmethod
    def insert_values_from_year(
            df: pd.DataFrame,
            target_column: str,
            start_year: int,
            values: list,
            offset = 0
    ) -> pd.DataFrame:
        """
        Inserts a list of values into an existing column of a DataFrame,
        starting from the row where 'Year' matches start_year and continuing
        downward for each subsequent value.

        Parameters:
        - df: pandas DataFrame with a 'Year' column
        - target_column: name of the existing column to update
        - start_year: integer year where insertion begins
        - values: list of values to insert (len(values) determines how many rows are updated)

        Returns:
        - The modified DataFrame (in-place changes are also applied)

        Raises:
        - ValueError if target_column doesn't exist or 'Year' column missing
        - LookupError if start_year not found
        """
        if 'Year' not in df.columns:
            raise ValueError("DataFrame must have a 'Year' column")
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' does not exist in DataFrame")

        # Ensure Year is integer for reliable matching
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')

        # Find the starting row index
        matching_rows = df[df['Year'] == start_year]
        if matching_rows.empty:
            raise LookupError(f"Year {start_year} not found in DataFrame")

        start_idx = matching_rows.index[0] + offset

        # Check if there are enough rows after start_idx
        required_rows = len(values)
        available_rows = len(df) - start_idx
        if required_rows > available_rows:
            print(f"Warning: Only {available_rows} rows available after year {start_year}. "
                  f"Inserting {available_rows} values and truncating the rest.")
            values = values[:available_rows]

        # Insert the values
        df.loc[start_idx: start_idx + len(values) - 1, target_column] = values

        return df

    @staticmethod
    def add_borders_to_column(
            ws,
            start_col: int,
            start_row: int,
            end_row: int,
            end_col: int = None,
            border_style: str = "thin",  # thin, medium, thick, dashed, dotted, double, etc.
            which: str = "all",  # "all", "outer", "horizontal", "vertical", "top", "bottom", "left", "right"
            color: str = "000000"  # hex color without #
    ) -> None:
        """
        Apply borders to every cell in a specified column over a range of rows.

        Args:
            ws: openpyxl worksheet object
            start_col: 1-based column number
            start_row: first row (inclusive)
            end_row: last row (inclusive)
            end_col: last col (inclusive)
            border_style: 'thin', 'medium', 'thick', 'dashed', 'dotted', 'double', ...
            which: which borders to apply
                   - "all": full box around each cell
                   - "outer": only top of first + bottom of last + left + right
                   - "horizontal": top + bottom only
                   - "vertical": left + right only
                   - or single side: "top", "bottom", "left", "right"
            color: border color (hex without #)

        Examples:
            add_borders_to_column(ws, "D", 5, 25, border_style="medium", which="all")
            add_borders_to_column(ws, 2, 2, 100, "thin", "horizontal", "808080")  # gray horizontal lines
        """
        if end_col is None:
            end_col = start_col
        # Define side style
        side = Side(border_style=border_style, color=color)

        # Prepare border objects based on 'which'
        if which == "all":
            full_border = Border(left=side, right=side, top=side, bottom=side)
            cell_border = full_border
        elif which == "none":
            cell_border = Border(left=None, right=None, top=None, bottom=None)
        elif which == "outer":
            # Only outer perimeter of the whole range
            for col in range(start_col, end_col + 1):
                for row in range(start_row, end_row + 1):
                    col_letter = get_column_letter(col)
                    cell = ws[f"{col_letter}{row}"]
                    border = Border()
                    if row == start_row:
                        border.top = side
                    if row == end_row:
                        border.bottom = side
                    if col == start_col:
                        border.left = side
                    if col == end_col:
                        border.right = side
                    cell.border = border
            return  # special case — skip the loop below
        elif which == "horizontal":
            cell_border = Border(top=side, bottom=side)
        elif which == "vertical":
            cell_border = Border(left=side, right=side)
        elif which == "top":
            cell_border = Border(top=side)
        elif which == "bottom":
            cell_border = Border(bottom=side)
        elif which == "left":
            cell_border = Border(left=side)
        elif which == "right":
            cell_border = Border(right=side)
        else:
            raise ValueError(
                f"Invalid 'which' value: {which}. Use 'all', 'outer', 'horizontal', 'vertical', 'top', 'bottom', 'left', 'right'")

        # Apply to each cell in range
        for col in range(start_col, end_col + 1):
            for row in range(start_row, end_row + 1):
                col_letter = get_column_letter(col)
                cell = ws[f"{col_letter}{row}"]
                cell.border = cell_border

    @staticmethod
    def set_column_alignment(
        ws: Worksheet,
        column: str | int,
        start_row: int,
        end_row: int,
        horizontal: str = 'center',
        vertical: str = 'center',
        wrap_text: bool = False,
        shrink_to_fit: bool = False,
        indent: int = 0
    ) -> None:
        """
        Set alignment for all cells in a given column between start_row and end_row (inclusive).

        Parameters:
        -----------
        ws : Worksheet
            The openpyxl worksheet to modify
        column : str or int
            Column letter ('A', 'B', ...) or column number (1, 2, ...)
        start_row : int
            First row to apply alignment to (1-based)
        end_row : int
            Last row to apply alignment to (1-based, inclusive)
        horizontal : str, optional
            'left', 'center', 'right', 'general', 'justify', 'distributed'
            Default: 'center'
        vertical : str, optional
            'top', 'center', 'bottom', 'justify', 'distributed'
            Default: 'center'
        wrap_text : bool, optional
            Whether to wrap text in the cells
            Default: False
        shrink_to_fit : bool, optional
            Whether text should shrink to fit the cell
            Default: False
        indent : int, optional
            Indent level (0 or more)
            Default: 0

        Example:
        --------
        set_column_alignment(ws, 'B', 5, 100, horizontal='right', vertical='center', wrap_text=True)
        set_column_alignment(ws, 3, 2, 50, horizontal='center', vertical='top')  # column C
        """
        # Normalize column to letter
        if isinstance(column, int):
            col_letter = get_column_letter(column)
        else:
            col_letter = str(column).upper()

        # Create the alignment object once
        align = Alignment(
            horizontal=horizontal,
            vertical=vertical,
            wrap_text=wrap_text,
            shrink_to_fit=shrink_to_fit,
            indent=indent
        )

        # Fastest way: iterate only over the specific column slice
        for row in range(start_row, end_row + 1):
            cell = ws[f"{col_letter}{row}"]
            cell.alignment = align

    @staticmethod
    def set_column_negative_red(
            ws: Worksheet,
            column: str | int,
            start_row: int,
            end_row: int,
            base_format: str = '#,##0.00',
            use_parentheses: bool = False,
            negative_color: str = 'Red'
    ) -> None:
        """
        Apply number format so negative values show in red **with a minus sign**.

        Options:
        - base_format:       Format for positive numbers (e.g. '#,##0.00', '0', '$#,##0.00')
        - use_parentheses:   If True → negatives appear as (123.45) in red (accounting style)
                             If False → negatives appear as -123.45 in red (default)
        """
        if isinstance(column, int):
            col_letter = get_column_letter(column)
        else:
            col_letter = str(column).upper().strip()

        if use_parentheses:
            # Accounting style: positives normal, negatives red + parentheses
            fmt = f"{base_format};[Red]({base_format})"
        else:
            # Standard: explicit minus sign in red
            fmt = f"{base_format};[Red]-{base_format}"

        for row in range(start_row, end_row + 1):
            cell = ws[f"{col_letter}{row}"]
            cell.number_format = fmt