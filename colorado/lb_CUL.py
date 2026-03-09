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
from sheet.sheet import cl, cn
import csv

class LB_CUL(Sheet):
    def __init__(self):
        self.path:Path = Path('data/USBR_Lower_Colorado_CUL/Tributary')

        headers = [
            lb.AZ_TRIBUTARY_CU, lb.NV_TRIBUTARY_CU,
            lb.USGS_GILA_DOME,

            lb.AZ_GILA_CU,
            lb.AZ_GILA_IRRIGATION_CU, lb.AZ_GILA_M_AND_I_CU, lb.AZ_GILA_MINERALS_CU,
            lb.AZ_GILA_LIVESTOCK_CU, lb.AZ_GILA_STOCK_POND_CU,
            lb.AZ_GILA_RESERVOIR_MEASURED_CU, lb.AZ_GILA_RESERVOIR_UNMEASURED_CU,

            lb.AZ_LITTLE_COLORADO_CU,
            lb.AZ_LITTLE_COLORADO_IRRIGATION_CU, lb.AZ_LITTLE_COLORADO_M_AND_I_CU,
            lb.AZ_LITTLE_COLORADO_MINERALS_CU,
            lb.AZ_LITTLE_COLORADO_LIVESTOCK_CU, lb.AZ_LITTLE_COLORADO_STOCK_POND_CU,
            lb.AZ_LITTLE_COLORADO_RESERVOIR_MEASURED_CU, lb.AZ_LITTLE_COLORADO_RESERVOIR_UNMEASURED_CU,

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
        # lower_basin_cu_from_excel(self.path, start_year=self.start_year, end_year=self.end_year)


    def load_df(self, df_compact : pd.DataFrame) -> None:

        divisor = 1

        sheet.usgs_annuals(self.df, '09520500', self.start_year, self.end_year, title=lb.USGS_GILA_DOME,
                           divisor=1)

        path = self.path
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
        # AZ TEP
        # AZ within system

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

        df = sheet.read_csv(path / 'az_gila_measured_reservoirs.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_RESERVOIR_MEASURED_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_gila_unmeasured_reservoirs.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_LITTLE_COLORADO_RESERVOIR_UNMEASURED_CU, divisor=divisor)


        df = sheet.read_csv(path / 'az_virgin_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_VIRGIN_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'az_virgin_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_VIRGIN_M_AND_I_CU, divisor=divisor)


        df = sheet.read_csv(path / 'az_trib_below_lake_mead_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.AZ_TRIB_BELOW_LAKE_MEAD_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nv_virgin_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_VIRGIN_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nv_virgin_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_VIRGIN_M_AND_I_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nv_muddy_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_MUDDY_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nv_muddy_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_MUDDY_M_AND_I_CU, divisor=divisor)


        df = sheet.read_csv(path / 'nv_trib_above_lake_mead_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NV_TRIB_ABOVE_LAKE_MEAD_M_AND_I_CU, divisor=divisor)


        df = sheet.read_csv(path / 'nm_gila_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NM_GILA_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'nm_gila_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.NM_GILA_M_AND_I_CU, divisor=divisor)


        df = sheet.read_csv(path / 'ut_virgin_irrigation.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.UT_VIRGIN_IRRIGATION_CU, divisor=divisor)

        df = sheet.read_csv(path / 'ut_virgin_m_i_other.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df, lb.UT_VIRGIN_M_AND_I_CU, divisor=divisor)



    @staticmethod
    def set_formula(ws:Worksheet, df:pd.DataFrame, formula:str, column_name:str, start_row=1) -> None:
        col_idx = df.columns.get_loc(column_name) + 1  # 1-based
        for i in range(start_row, len(df)+1):
            excel_row = i + 1
            f = formula.replace("[row]", str(excel_row))
            ws.cell(row=excel_row, column=col_idx, value=f)

    def build_sheet(self) -> None:
        self.set_bg(lb.USGS_GILA_DOME, color=all_b.USGS_BG)

        col1 = cl(self.ws, lb.AZ_GILA_CU)
        col2 = cl(self.ws, lb.AZ_LITTLE_COLORADO_CU)
        col3 = cl(self.ws, lb.AZ_VIRGIN_CU)
        formula = f'={col1}[row]+{col2}[row]+{col3}[row]'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.AZ_TRIBUTARY_CU)

        col1 = cl(self.ws, lb.NV_VIRGIN_CU)
        col2 = cl(self.ws, lb.NV_MUDDY_CU)
        col3 = cl(self.ws, lb.NV_TRIB_ABOVE_LAKE_MEAD_M_AND_I_CU)
        formula = f'={col1}[row]+{col2}[row]+{col3}[row]'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.NV_TRIBUTARY_CU)

        col1 = cl(self.ws, lb.AZ_GILA_IRRIGATION_CU)
        col2 = cl(self.ws, lb.AZ_GILA_RESERVOIR_UNMEASURED_CU)
        formula = f'=SUM({col1}[row]:{col2}[row])'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.AZ_GILA_CU)
        self.set_bg(lb.AZ_GILA_IRRIGATION_CU, lb.AZ_GILA_RESERVOIR_UNMEASURED_CU, color=all_b.USBR_LB_CUL_BG)

        col1 = cl(self.ws, lb.AZ_LITTLE_COLORADO_IRRIGATION_CU)
        col2 = cl(self.ws, lb.AZ_LITTLE_COLORADO_RESERVOIR_UNMEASURED_CU)
        formula = f'=SUM({col1}[row]:{col2}[row])'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.AZ_LITTLE_COLORADO_CU)
        self.set_bg(lb.AZ_LITTLE_COLORADO_IRRIGATION_CU, lb.AZ_LITTLE_COLORADO_RESERVOIR_UNMEASURED_CU, color=all_b.USBR_LB_CUL_BG)

        col1 = cl(self.ws, lb.AZ_VIRGIN_IRRIGATION_CU)
        col2 = cl(self.ws, lb.AZ_VIRGIN_M_AND_I_CU)
        formula = f'=SUM({col1}[row]:{col2}[row])'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.AZ_VIRGIN_CU)
        self.set_bg(lb.AZ_VIRGIN_IRRIGATION_CU, lb.AZ_VIRGIN_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG)

        col1 = cl(self.ws, lb.NV_VIRGIN_IRRIGATION_CU)
        col2 = cl(self.ws, lb.NV_VIRGIN_M_AND_I_CU)
        formula = f'=SUM({col1}[row]:{col2}[row])'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.NV_VIRGIN_CU)
        self.set_bg(lb.NV_VIRGIN_IRRIGATION_CU, lb.NV_VIRGIN_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG)

        col1 = cl(self.ws, lb.NV_MUDDY_IRRIGATION_CU)
        col2 = cl(self.ws, lb.NV_MUDDY_M_AND_I_CU)
        formula = f'=SUM({col1}[row]:{col2}[row])'
        LB_CUL.set_formula(self.ws, self.df, formula, lb.NV_MUDDY_CU)
        self.set_bg(lb.NV_MUDDY_IRRIGATION_CU, lb.NV_MUDDY_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG)

        self.set_bg(lb.NM_GILA_IRRIGATION_CU, lb.NM_GILA_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG)
        self.set_bg(lb.UT_VIRGIN_IRRIGATION_CU, lb.UT_VIRGIN_M_AND_I_CU, color=all_b.USBR_LB_CUL_BG)

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

def lower_basin_cu_from_excel(out_path: Path, start_year:int=1971, end_year:int=2024):
    wb: Workbook = openpyxl.load_workbook('data/Colorado_River/1971-2024 Lower Colorado River System CUL Data.xlsx', data_only=True)
    area_reference = sheet.worksheet_to_dict_of_dicts(wb['Area_Reference'], 1, 2, 'HU8_CODE')
    ws: Worksheet = wb['Tributary']

    header_row: int = 1
    years: List[int] = list(range(start_year, end_year+1))

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
