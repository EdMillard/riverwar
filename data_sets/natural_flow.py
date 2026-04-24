"""
Copyright (c) 2025 Ed Millard

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
from data_sets.data_set import DataSet
import openpyxl
from api import df_utils
import colorado.lb as lb
import colorado.ub as ub
import pandas as pd
from sheet.sheet import max_used_column, read_year_value_pairs

class NaturalFlowDataSet(DataSet):
    def __init__(self, name:str, month:int=10):
        super().__init__(name, month=month)
        self.start_year = 1906
        self.start_row = 4
        # self.start_year = 1964
        # self.start_row = 62
        self.end_year = 2024

        self.df: pd.DataFrame = df_utils.create_df(self.start_year, self.end_year, [ub.SUPPLY])
        NaturalFlowDataSet.lf_natural_flow_from_excel(self.df, start_row=self.start_row, column_name=ub.SUPPLY)
        self.df[ub.SUPPLY] = self.df[ub.SUPPLY] * 1_000_000
        df_utils.moving_average(self.df, ub.SUPPLY, 'Supply 10 yr avg')

    @staticmethod
    def lf_natural_flow_from_excel(df: pd.DataFrame, start_row:int=62, column_name:str=ub.NATURAL_LEES_FERRY):
        wb = openpyxl.load_workbook('data/Colorado_River/LFnatFlow1906-2024.2024.9.12.xlsx', data_only=True)
        ws = wb['Calendar Year']
        # ws = wb['AnnualCYTotalNaturalFlow']
        # ws = wb['TotalNaturalFlow']   # Monthly
        data_start_row = start_row
        data_end_row = 122  # 2024
        year_column_index = 1
        for column_index in range(ws.min_column, max_used_column(ws) + 1):
            # gage = ws.cell(row=gage_row, column=column_index).value
            # header = ws.cell(row=header_row, column=column_index).value
            # units = ws.cell(row=unit_row, column=column_index).value

            if column_index == 2: # Lees Ferry
                pairs, values = read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[0: 0 + len(values) - 1, column_name] = values

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
        for column_index in range(ws.min_column,  max_used_column(ws) + 1):
            gage = ws.cell(row=gage_row, column=column_index).value
            # header = ws.cell(row=header_row, column=column_index).value
            units = ws.cell(row=unit_row, column=column_index).value

            if units == 'Water Year':
                year_column_index = column_index

            if gage == '09429490': # Imperial
                pairs, values = read_year_value_pairs(ws, year_column_index, column_index, data_start_row, data_end_row)
                df.loc[0: 0 + len(values) - 1, lb.NATURAL_IMPERIAL] = values
