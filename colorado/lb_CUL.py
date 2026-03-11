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
import colorado.lb as lb
import colorado.allb as all_b
import pandas as pd
from sheet.sheet import Sheet
import openpyxl
from sheet import sheet
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import Workbook
from typing import List, Dict, Union
from sheet.sheet import cl
import csv

class LB_CUL(Sheet):
    def __init__(self):
        self.path:Path = Path('data/USBR_Lower_Colorado_CUL/Tributary')

        headers = [
            lb.AZ_TRIBUTARY_CU, lb.NV_TRIBUTARY_CU,
            lb.AZ_GILA_DOME_USGS,

            lb.AZ_GILA_CU,
            lb.AZ_GILA_IRRIGATION_CU, lb.AZ_GILA_M_AND_I_CU, lb.AZ_GILA_MINERALS_CU,
            lb.AZ_GILA_LIVESTOCK_CU, lb.AZ_GILA_STOCK_POND_CU,
            lb.AZ_GILA_RESERVOIR_MEASURED_CU, lb.AZ_GILA_RESERVOIR_UNMEASURED_CU,
            lb.AZ_GILA_TEP_CU, lb.AZ_GILA_WITHIN_SYSTEM_CU,

            lb.AZ_LITTLE_COLORADO_CAMERON_USGS, lb.AZ_LITTLE_COLORADO_CU,
            lb.AZ_LITTLE_COLORADO_IRRIGATION_CU, lb.AZ_LITTLE_COLORADO_M_AND_I_CU,
            lb.AZ_LITTLE_COLORADO_MINERALS_CU,
            lb.AZ_LITTLE_COLORADO_LIVESTOCK_CU, lb.AZ_LITTLE_COLORADO_STOCK_POND_CU,
            lb.AZ_LITTLE_COLORADO_RESERVOIR_MEASURED_CU, lb.AZ_LITTLE_COLORADO_RESERVOIR_UNMEASURED_CU,
            lb.AZ_LITTLE_COLORADO_TEP_CU, lb.AZ_LITTLE_COLORADO_WITHIN_SYSTEM_CU,

            lb.AZ_VIRGIN_CU,
            lb.AZ_VIRGIN_IRRIGATION_CU, lb.AZ_VIRGIN_M_AND_I_CU,

            lb.AZ_TRIB_BELOW_LAKE_MEAD_IRRIGATION_CU,
            lb.NV_TRIB_ABOVE_LAKE_MEAD_M_AND_I_CU,

            lb.NV_MUDDY_CU,
            lb.NV_MUDDY_IRRIGATION_CU, lb.NV_MUDDY_M_AND_I_CU,

            lb.NV_VIRGIN_CU,
            lb.NV_VIRGIN_IRRIGATION_CU, lb.NV_VIRGIN_M_AND_I_CU,

            lb.NM_GILA_CU,
            lb.NM_GILA_IRRIGATION_CU, lb.NM_GILA_M_AND_I_CU,

            lb.UT_VIRGIN_CU,
            lb.UT_VIRGIN_IRRIGATION_CU, lb.UT_VIRGIN_M_AND_I_CU
        ]
        super().__init__(headers, start_year=1971, end_year=2024)
        self.years: List[int] = list(range(self.start_year, self.end_year+1))
        # lower_basin_cu_from_excel(self.path, years)


    def load_df(self, df_compact : pd.DataFrame) -> None:

        divisor = 1

        path = self.path

        # Little Colorado River Abv Mouth NR Desert View, AZ
        # sheet.usgs_annuals(self.df, '09402300', 1990, self.end_year, title=lb.AZ_LITTLE_COLORADO_MOUTH_USGS, divisor=1)

        # Little Colorado River Near Cameron, AZ
        sheet.usgs_annuals(self.df, '09402000', 1981, self.end_year, title=lb.AZ_LITTLE_COLORADO_CAMERON_USGS,
                           offset=1, divisor=1)

        # AZ Gila
        sheet.usgs_annuals(self.df, '09520500', self.start_year, self.end_year, title=lb.AZ_GILA_DOME_USGS, divisor=1)
        df = sheet.read_csv(path / 'az_gila_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_M_AND_I_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_mineral_resources.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_MINERALS_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_livestock.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_LIVESTOCK_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_stockpond.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_STOCK_POND_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_measured_reservoirs.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_RESERVOIR_MEASURED_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_unmeasured_reservoirs.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_RESERVOIR_UNMEASURED_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_tep.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_TEP_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_within_system.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_GILA_WITHIN_SYSTEM_CU, divisor=divisor)

        # AZ Little Colorado

        df = sheet.read_csv(path / 'az_little_colorado_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_M_AND_I_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_mineral_resources.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_MINERALS_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_livestock.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_LIVESTOCK_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_stockpond.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_STOCK_POND_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_measured_reservoirs.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_RESERVOIR_MEASURED_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_unmeasured_reservoirs.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_RESERVOIR_UNMEASURED_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_tep.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_TEP_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_little_colorado_within_system.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_WITHIN_SYSTEM_CU, divisor=divisor)

        # AZ Virgin
        df = sheet.read_csv(path / 'az_virgin_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_VIRGIN_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_virgin_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_VIRGIN_M_AND_I_CU, divisor=divisor)

        # AZ Trib
        df = sheet.read_csv(path / 'az_trib_below_lake_mead_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_TRIB_BELOW_LAKE_MEAD_IRRIGATION_CU, divisor=divisor)

        # NV Virgin
        df = sheet.read_csv(path / 'nv_virgin_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_VIRGIN_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nv_virgin_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_VIRGIN_M_AND_I_CU, divisor=divisor)

        # NV Muddy
        df = sheet.read_csv(path / 'nv_muddy_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_MUDDY_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nv_muddy_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_MUDDY_M_AND_I_CU, divisor=divisor)

        # NV Trib
        df = sheet.read_csv(path / 'nv_trib_above_lake_mead_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_TRIB_ABOVE_LAKE_MEAD_M_AND_I_CU, divisor=divisor)

        # NM Gila
        df = sheet.read_csv(path / 'nm_gila_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NM_GILA_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nm_gila_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NM_GILA_M_AND_I_CU, divisor=divisor)

        # UT Virgin
        df = sheet.read_csv(path / 'ut_virgin_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.UT_VIRGIN_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'ut_virgin_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.UT_VIRGIN_M_AND_I_CU, divisor=divisor)

    @staticmethod
    def set_col_formula(ws:Worksheet, df:pd.DataFrame, formula:str, column_name:str, start_row=1) -> None:
        col_idx = df.columns.get_loc(column_name) + 1  # 1-based
        for i in range(start_row, len(df)+1):
            excel_row = i + 1
            f = formula.replace("[row]", str(excel_row))
            ws.cell(row=excel_row, column=col_idx, value=f)

    @staticmethod
    def set_row_formula(
            ws: Worksheet,
            df: pd.DataFrame,
            formula_template: str,
            target_row: int,
            start_col: str | int | None = None,
            end_col: str | int | None = None,
            start_data_row: int = 2,
            header: str = ''
    ) -> None:
        """
        Puts the same formula pattern across a range of columns in one specific row.

        Parameters:
        - ws: openpyxl Worksheet
        - df: pandas DataFrame (used only to know column order/names)
        - formula_template: str with placeholder e.g. '=AVERAGE({col_letter}{start_data_row}:{col_letter}[row-1])'
        - target_row: the Excel row number where formulas should be written
        - start_col / end_col: optional column limits (can be named, letter or 1-based index)
        - start_data_row: usually 2 (first data row after header)

        Example:
            formula = '=AVERAGE(B{start}:B[row-1])'
            set_row_formula(ws, df, formula, target_row=15, start_data_row=2)
            → puts in row 15: =AVERAGE(B2:B14), =AVERAGE(C2:C14), etc.
        """
        from openpyxl.utils import get_column_letter, column_index_from_string

        # Determine column range
        all_cols = list(df.columns)
        n_cols = len(all_cols)

        # Resolve start_col and end_col to 0-based indices in df
        if start_col is None:
            start_idx = 0
        elif isinstance(start_col, str):
            if start_col in all_cols:
                start_idx = all_cols.index(start_col)
            else:
                start_idx = column_index_from_string(start_col) - 1
        else:
            start_idx = int(start_col) - 1  # assume 1-based → 0-based

        if end_col is None:
            end_idx = n_cols - 1
        elif isinstance(end_col, str):
            if end_col in all_cols:
                end_idx = all_cols.index(end_col)
            else:
                end_idx = column_index_from_string(end_col) - 1
        else:
            end_idx = int(end_col) - 1

        start_idx = max(0, start_idx)
        end_idx = min(n_cols - 1, end_idx)

        for col_idx in range(start_idx, end_idx + 1):  # 0-based in df
            col_letter = get_column_letter(col_idx + 1)  # 1-based for Excel
            excel_col = col_idx + 1

            # Replace placeholders
            f = formula_template
            f = f.replace("[row]", str(target_row))
            f = f.replace("{col_letter}", col_letter)
            f = f.replace("{col}", col_letter)
            f = f.replace("[col]", col_letter)

            # Common patterns for dynamic row ranges
            f = f.replace("{start}", str(start_data_row))
            f = f.replace("[start]", str(start_data_row))
            f = f.replace("{start_row}", str(start_data_row))
            f = f.replace("[start_row]", str(start_data_row))

            # Optional: [row-1], [row+1], etc.
            import re
            def offset_replacer(m):
                try:
                    offset = int(m.group(1))
                    return str(target_row + offset)
                except:
                    return m.group(0)

            f = re.sub(r'\[row([+-]\d+)]', offset_replacer, f)

            # Write formula to cell
            ws.cell(row=target_row, column=excel_col, value=f)
        ws.cell(row=target_row, column=start_col-1, value=header)


    def build_sheet(self) -> None:

        formula = '=AVERAGE({col_letter}2:{col_letter}[row-1])'
        ws: Worksheet = self.ws
        number_format = '#,##0;-#,##0'
        target_row = len(self.years) + 2
        last_row = len(self.years) + 1
        LB_CUL.set_row_formula(ws, self.df, formula, target_row=target_row, start_data_row=2,
                               start_col=2, end_col=ws.max_column, header='Avg')
        sheet.set_number_format(ws, target_row, target_row+1, 2, ws.max_column, number_format=number_format)
        sheet.set_font(ws, start_row=target_row, end_row=target_row+1, start_col=2, end_col=ws.max_column)
        sheet.set_font(ws, start_row=target_row, end_row=target_row+1, start_col=1, end_col=1)

        # Sum AZ Rivers
        columns = [lb.AZ_GILA_CU, lb.AZ_LITTLE_COLORADO_CU, lb.AZ_VIRGIN_CU]
        sheet.formula_add(ws, self.df, lb.AZ_TRIBUTARY_CU, columns)

        # Sum NV Rivers
        columns = [lb.NV_VIRGIN_CU, lb.NV_MUDDY_CU, lb.NV_TRIB_ABOVE_LAKE_MEAD_M_AND_I_CU]
        sheet.formula_add(ws, self.df, lb.NV_TRIBUTARY_CU, columns)

        # AZ Gila
        self.set_bg(lb.AZ_GILA_DOME_USGS, color=all_b.USGS_BG)
        sheet.formula_sum(ws, self.df, lb.AZ_GILA_CU, lb.AZ_GILA_IRRIGATION_CU, lb.AZ_GILA_WITHIN_SYSTEM_CU)
        self.set_bg(lb.AZ_GILA_IRRIGATION_CU, lb.AZ_GILA_WITHIN_SYSTEM_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # AZ Little Colorado
        self.set_bg(lb.AZ_LITTLE_COLORADO_CAMERON_USGS, color=all_b.USGS_BG)
        sheet.formula_sum(ws, self.df, lb.AZ_LITTLE_COLORADO_CU, lb.AZ_LITTLE_COLORADO_IRRIGATION_CU,
                          lb.AZ_LITTLE_COLORADO_WITHIN_SYSTEM_CU)
        self.set_bg(lb.AZ_LITTLE_COLORADO_IRRIGATION_CU, lb.AZ_LITTLE_COLORADO_WITHIN_SYSTEM_CU,
                    color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # AZ Virgin
        sheet.formula_sum(ws, self.df, lb.AZ_VIRGIN_CU, lb.AZ_VIRGIN_IRRIGATION_CU, lb.AZ_VIRGIN_M_AND_I_CU)
        self.set_bg(lb.AZ_VIRGIN_IRRIGATION_CU, lb.AZ_VIRGIN_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # AZ Trib Below
        self.set_bg(lb.AZ_TRIB_BELOW_LAKE_MEAD_IRRIGATION_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # NV Trib Above
        self.set_bg(lb.NV_TRIB_ABOVE_LAKE_MEAD_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # NV Virgin
        sheet.formula_sum(ws, self.df, lb.NV_VIRGIN_CU, lb.NV_VIRGIN_IRRIGATION_CU, lb.NV_VIRGIN_M_AND_I_CU)
        self.set_bg(lb.NV_VIRGIN_IRRIGATION_CU, lb.NV_VIRGIN_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # NV Muddy
        sheet.formula_sum(ws, self.df, lb.NV_MUDDY_CU, lb.NV_MUDDY_IRRIGATION_CU, lb.NV_MUDDY_M_AND_I_CU)
        self.set_bg(lb.NV_MUDDY_IRRIGATION_CU, lb.NV_MUDDY_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # NM Gila
        sheet.formula_sum(ws, self.df, lb.NM_GILA_CU, lb.NM_GILA_IRRIGATION_CU, lb.NM_GILA_M_AND_I_CU)
        self.set_bg(lb.NM_GILA_IRRIGATION_CU, lb.NM_GILA_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        # UT Virgin
        sheet.formula_sum(ws, self.df, lb.UT_VIRGIN_IRRIGATION_CU, lb.UT_VIRGIN_M_AND_I_CU, lb.NM_GILA_M_AND_I_CU)
        self.set_bg(lb.UT_VIRGIN_CU, lb.UT_VIRGIN_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG, end_row=last_row)

        self.format_header()

        self.set_column_width(lb.AZ_TRIBUTARY_CU, 6, to=lb.UT_VIRGIN_M_AND_I_CU,)

states = {
    '04': 'az',
    '06': 'ca',
    '32': 'nv',
    '35': 'nm',
    '49': 'ut',
}

def get_node(node_code: str, area_reference: Dict[str, Dict], calc_type:str, years: List[int], nodes: Dict) -> pd.DataFrame:
    parts = node_code.split('_')
    if len(parts) != 3:
        print(f'Invalid node code: {node_code}')
        return pd.DataFrame()
    state_code = parts[0]
    # down_stream_node = parts[1]
    node: str = parts[2]
    area = area_reference.get(node, None)
    if area:
        area_name:str | None = area.get('REPORTING_AREA', None)
        if area_name:
            state = states.get(state_code, None)
            node_name = f"{state}_{area_name.lower()}_{calc_type}"
            df: Union[pd.DataFrame, None] = nodes.get(node_name, None)
            if df is None:
                df = sheet.create_month_year_df(years)
                nodes[node_name] = df
        else:
            print('Reporting area not found')
            return pd.DataFrame()
    else:
        print(f'node code not found: {area}')
        return pd.DataFrame()

    return df

def lower_basin_cu_from_excel(out_path: Path, years):
    wb: Workbook = openpyxl.load_workbook('data/Colorado_River/1971-2024 Lower Colorado River System CUL Data.xlsx', data_only=True)
    area_reference = sheet.worksheet_to_dict_of_dicts(wb['Area_Reference'], 1, 2, 'HU8_CODE')
    ws: Worksheet = wb['Tributary']

    header_row: int = 1

    sheet.ensure_directory(out_path)

    headers: List[str] = []
    for column_index in range(ws.min_column, 20):
        header: str = ws.cell(row=header_row, column=column_index).value
        headers.append(header)

    nodes: dict[str, pd.DataFrame] = {}
    df:  Union[pd.DataFrame, None] = None
    year: int = 0
    calc_type: str | None = None
    node_code: str | None = None
    for row in ws.iter_rows(min_row=2):
        column_index = 0
        for cell in row:
            if column_index < len(headers):
                header = headers[column_index]
                if header == 'STATE_CODE':
                    pass
                elif header == 'NODE_CODE':
                    node_code = cell.value
                elif header == 'SOURCE':
                    pass
                elif header == 'CALC_TYPE':
                    calc_type = cell.value.lower()
                elif header == 'Year':
                    year = cell.value
                    df = get_node(node_code, area_reference, calc_type, years, nodes)
                elif header == 'Total':
                    df.loc[df['Year'] == year, header] += int(cell.value)
                elif header is None:
                    pass
                else:
                    month = header
                    try:
                        df.loc[df['Year'] == year, month] += int(cell.value)
                    except KeyError:
                        print(header)
            else:
                pass
            column_index += 1

    for key, df in nodes.items():
        exclude_cols = ['Year']
        all_rows_are_zero = df.drop(columns=exclude_cols, errors='ignore').eq(0).all(axis=1).all()
        if not all_rows_are_zero:
            out_csv_path = out_path / f'{key}.csv'
            df.to_csv(out_csv_path, index=False, quoting=csv.QUOTE_NONE,  escapechar='\\', sep=' ')
