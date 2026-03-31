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
from reservoirs.reservoir import Reservoir
import colorado.lb as lb
import openpyxl
from sheet import sheet
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import Workbook
from typing import List, Dict, Union
import pandas as pd

class Aquifers(Reservoir):
    def __init__(self):
        headers:List[str] = [lb.AQUIFER, lb.AQUIFER_INFLOW, lb.AQUIFER_RELEASE]
        super().__init__('Aquifers', headers)
        self.start_year = 1989
        self.end_year = 2022
        self.years: List[int] = list(range(self.start_year, self.end_year+1))
        self.recharge_summary_data_from_excel(self.years)
        # Elevations
        #
        # Must be called first
        self.dead_pool_feet = 0
        self.dead_pool_af = 0

        self.full_feet = 0
        self.full_af = 0

        # Critical
        self.power_head_target_feet = 0
        self.power_head_target_af = 0

        self.power_head_min_feet = 0
        self.power_head_min_af = 0

        self.turbine_intake_feet = 0
        self.turbine_intake_af = 0
        self.critical_elevations_feet = [("Safe Power Head", self.power_head_min_feet, self.power_head_min_af, Reservoir.non_power_pool_color),
                                         ("Min Power Head", self.power_head_target_feet, self.power_head_target_af, Reservoir.low_power_pool_color)]

        # Current
        #
        self.elevation_feet = 0
        self.active_capacity_af = 9000000

        # Inflow

        self.inflow_actual_af = 0
        self.inflow_parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                             ("Projected", 0, Reservoir.inflow_projected_color)]

        # Outflow
        self.outflow_actual_af = 0
        self.release_af = 0
        self.outflow_projected_af = self.release_af -  self.outflow_actual_af
        self.outflow_parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                              ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]

        # self.reserved_parts = reserved_parts or []

    def recharge_summary_data_from_excel(self, years: List[int]):
        wb: Workbook = openpyxl.load_workbook('excel/ADWR_Data_Warehouse_Recharge_Summary_Data.xlsx', data_only=True)
        ws: Worksheet = wb['Sheet1']

        header_row: int = 2

        headers: List[str] = []
        for column_index in range(ws.min_column, 20):
            header: str = ws.cell(row=header_row, column=column_index).value
            headers.append(header)

        out_headers = ['Water Delivered', 'Annual Recovery', 'Evaporation Transpiration Losses', 'Cut to Aquifer']
        self.df: pd.DataFrame = sheet.create_df(self.start_year, self.end_year, out_headers)
        nodes: dict[str, pd.DataFrame] = {}
        df: Union[pd.DataFrame, None] = None
        year: int = 0
        ama_name: str | None = None
        category: str | None = None
        parent_water_type: str | None = None
        specific_water_type: str | None = None
        recharge_method: str | None = None
        recharge_element: str | None = None
        water_delivered_total:float = 0
        annual_recovery_total:float = 0
        et_total:float = 0
        cut_total:float = 0
        finished:bool = False
        max_row = ws.max_row
        for row in ws.iter_rows(min_row=header_row+2):
            column_index = 0
            for cell in row:
                if column_index < len(headers):
                    header = headers[column_index]
                    if header is None:
                        pass
                    elif header == 'Year':
                        if cell.value is not None:
                            year = int(cell.value)
                        else:
                            finished = True
                            break
                    elif header == 'AMA':
                        ama_name = cell.value
                    elif header == 'Category':
                        category = cell.value
                    elif header == 'Parent Water Type or Element':
                        parent_water_type = cell.value
                    elif header == 'Specific Water Type':
                        specific_water_type = cell.value
                    elif header == 'Recharge Method':
                        recharge_method = cell.value
                    elif header == 'Recharge Element':
                        recharge_element = cell.value
                    elif header == 'Quantity':
                        quantity:float = float(cell.value)
                        if parent_water_type == 'CAP':
                            if recharge_element == 'Water Delivered':
                                self.df.loc[self.df['Year'] == year, recharge_element] = quantity
                                water_delivered_total += quantity
                            elif recharge_element == 'Annual Recovery':
                                self.df.loc[self.df['Year'] == year, recharge_element] = quantity
                                annual_recovery_total += quantity
                            elif recharge_element == 'Evaporation Transpiration Losses':
                                self.df.loc[self.df['Year'] == year, recharge_element] = quantity
                                et_total += quantity
                            elif recharge_element == 'Cut to Aquifer':
                                self.df.loc[self.df['Year'] == year, recharge_element] = quantity
                                cut_total += quantity
                column_index += 1
            if finished:
                break
        stored = water_delivered_total - annual_recovery_total
        pass
