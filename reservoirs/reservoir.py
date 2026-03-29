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
import copy
import colorado.allb as all_b
import numpy as np
import pandas as pd
from source.water_year_info import WaterYearInfo
from datetime import date
from typing import List
from sheet import sheet

class Reservoir:
    high_power_pool_color = "lightblue"
    low_power_pool_color = "cornflowerblue"
    non_power_pool_color = '#FFEE8C'
    outflow_actual_color = 'red'
    outflow_projected_color = '#FF746C'
    inflow_actual_color = '#2ca02c'
    inflow_projected_color = '#98fb98'
    # facecolor="skyblue"
    # facecolor="dodgerblue"
    # facecolor="steelblue"
    # facecolor="deepskyblue"

    def __init__(self, name:str, headers:List[str], month=10):
        self.name:str = name
        start_year = self.water_year = 2026
        self.water_year_info = self.get_water_year_info(start_year, month=month)
        self.headers = headers
        self.df = sheet.create_df(self.water_year, self.water_year, self.headers)
        self.df_daily: pd.DataFrame = sheet.create_daily_df(self.water_year_info.start_date, self.water_year_info.end_date, self.headers)

        self.elevation:float = 0

        self.full_feet:float = 0
        self.power_head_target_feet:float = 0
        self.power_head_lowest_feet:float = 0
        self.turbine_intake_feet:float = 0
        self.dead_pool_feet:float = 0

        self.active_capacity:float = 0

        self.critical_elevations:List[float] = []
        self.reserved_parts:List[tuple] = []
        self.inflow_parts:List[tuple] =  []
        self.outflow_parts:List[tuple] =  []



    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f" '\'{self.name}\'"

        return string

    def get_value_by_year(self, year: int, column_name: str):
        """
        Returns the value from a DataFrame for a given year and column.

        Parameters:
            df (pd.DataFrame): DataFrame where the first column contains years
            year (int): The year to look up
            column_name (str): Name of the column to retrieve the value from

        Returns:
            The value at the specified year and column, or None if not found
        """
        if self.df.empty:
            return None

        # Assuming first column is the year column (index 0)
        year_col = self.df.columns[0]

        # Find the row where the year matches
        mask = self.df[year_col] == year

        if not mask.any():
            print(f"Warning: Year {year} not found in data.")
            return None

        # Return the value from the requested column
        try:
            value = self.df.loc[mask, column_name].iloc[0]
            return value
        except KeyError:
            print(f"Error: Column '{column_name}' not found in DataFrame.")
            return None
        except Exception as e:
            print(f"Error retrieving value: {e}")
            return None

    @staticmethod
    def get_water_year_info(year:int, month:int=10):
        if month == 1:
            start_date = date(year, month, 1)
        else:
            start_date = date(year-1, month, 1)
        water_year_info = WaterYearInfo.get_water_year(start_date, month=month)
        return water_year_info

    @staticmethod
    def clip_array_by_dates(arr, start_date, end_date):
        # Ensure start_date and end_date are datetime64
        start_date = np.datetime64(start_date)
        end_date = np.datetime64(end_date)

        dates = arr['dt'].astype('datetime64[D]')
        # Create mask for dates within the range (inclusive)
        mask = (dates >= start_date) & (dates <= end_date)

        # Return clipped array
        return arr[mask]

