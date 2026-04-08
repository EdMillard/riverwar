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
import csv
from datetime import datetime
from pathlib import Path
import re
from collections import Counter
import pandas as pd
from ruamel.yaml.timestamp import TimeStamp
from source.water_year_info import WaterYearInfo
from datetime import date
from typing import List, Tuple
from sheet import sheet
from source import usbr_rise
import colorado.allb as all_b


class Reservoir:
    high_power_pool_color = "lightblue"
    low_power_pool_color = "cornflowerblue"
    non_power_pool_color = '#ffbbff'
    outflow_actual_color = 'red'
    outflow_projected_color = '#FF746C'
    inflow_actual_color = '#2ca02c'
    inflow_projected_color = '#98fb98'
    side_inflow_actual_color = '#3cb03c'
    side_inflow_projected_color = '#a8ffa8'
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
        self.date_time:TimeStamp = 0

        self.elevation_feet:float = 0
        self.active_capacity_af:float = 0

        self.full_feet:float = 0
        self.power_head_target_feet:float = 0
        self.power_head_lowest_feet:float = 0
        self.turbine_intake_feet:float = 0
        self.dead_pool_feet:float = 0

        self.critical_elevations:List[float] = []
        self.reserved_parts:List[tuple] = []
        self.inflow_parts:List[tuple] =  []
        self.outflow_parts:List[tuple] =  []

        self.start_month_year_actual = "Oct 2025"
        self.end_month_year_actual = "Mar 2026"
        self.start_month_year_projected = "Apr 2026"
        self.emd_month_year_projected = "Sep 2026"

    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f" '\'{self.name}\'"
        string += f" '\'{self.elevation_feet} ft\'"
        string += f" '\'{self.active_capacity_af} af\'"

        return string

    def get_elevation(self, usbr_rise_id:int, column_name:str)->Tuple[datetime, float]:
        info, daily_elevation_ft = usbr_rise.load(usbr_rise_id,
                                                  water_year_info=self.water_year_info,
                                                  alias=column_name)
        sheet.fill_df_from_structured_array(self.df_daily, daily_elevation_ft, date_column_name='Date',
                                            value_column_name=column_name)

        date_time = daily_elevation_ft['dt'][-1]
        elevation_feet = daily_elevation_ft['val'][-1]
        return date_time, elevation_feet

    def get_storage(self, usbr_rise_id: int, column_name:str, month=all_b.WY, divisor:int=1)->float:
        if usbr_rise_id:
            sheet.usbr_last_value(self.df, usbr_rise_id, self.water_year, self.water_year,
                                  title=column_name, month=month, divisor=divisor)
            active_capacity_af = self.get_value_by_year(self.water_year, column_name)
        else:
            active_capacity_af = 0
        return active_capacity_af

    def get_evaporation(self, usbr_rise_id: int, column_name: str, month=all_b.WY, divisor: int = 1)->float:
        if usbr_rise_id:
            evaporation_af = sheet.usbr_annuals(self.df, usbr_rise_id, self.water_year, self.water_year,
                                                     title=column_name, month=month, divisor=divisor)
        else:
            evaporation_af = 0
        return evaporation_af[0]

    def get_sum_end_of_month(self, usbr_rise_id: int)->float:
        monthly = sheet.usbr_monthly(usbr_rise_id, self.water_year, month=all_b.WY)
        monthly.pop()
        total:float = 0
        for month in monthly:
            total += month['val']
        return total

    def get_24_month_projected(self, df, column_name:str)->float:
        total = Reservoir.sum_column_between_dates(
            df,
            column_name=column_name,
            start_month_year=self.start_month_year_projected,
            end_month_year=self.emd_month_year_projected
        ) * 1000
        return total

    def get_24_month_actual(self, df, column_name:str)->float:
        total = Reservoir.sum_column_between_dates(
            df,
            column_name=column_name,
            start_month_year=self.start_month_year_actual,
            end_month_year=self.end_month_year_actual
        ) * 1000
        return total

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
    def get_float_value(df: pd.DataFrame,
                        row_key: str,
                        column_name: str) -> float:
        """
        Safely gets a float value even when column names have spaces.
        """
        df = df.copy()

        # Convert first column to string for matching
        first_col = df.columns[0]
        df[first_col] = df[first_col].astype(str).str.strip()

        # Handle column name safely (in case of spaces or special chars)
        if column_name not in df.columns:
            # Try to find column with partial match (helpful with weird names)1
            matches = [col for col in df.columns if column_name.strip().lower() in col.strip().lower()]
            if matches:
                column_name = matches[0]
                print(f"Found matching column: '{column_name}'")
            else:
                raise KeyError(f"Column '{column_name}' not found. Available columns: {list(df.columns)}")

        # Get the value
        try:
            value = df.loc[df[first_col] == row_key, column_name].iloc[0]
            return float(pd.to_numeric(value, errors='coerce'))
        except (IndexError, KeyError, ValueError) as e:
            raise ValueError(f"Could not find value for row '{row_key}' in column '{column_name}'") from e
    @staticmethod
    def get_water_year_info(year:int, month:int=10):
        if month == 1:
            start_date = date(year, month, 1)
        else:
            start_date = date(year-1, month, 1)
        water_year_info = WaterYearInfo.get_water_year(start_date, month=month)
        return water_year_info

    def sum_column_between_dates(
            df_monthly: pd.DataFrame,
            column_name: str,
            start_month_year: str,  # e.g. "Mar 2025" or "2025-03"
            end_month_year: str,  # e.g. "Sep 2026" or "2026-09"
            date_col: str = None
    ) -> float:
        """
        Sum a column in the monthly dataframe between two dates (inclusive).

        Parameters:
            df_monthly: The monthly DataFrame returned from read_usbr_24month_table
            column_name: Name of the column you want to sum (e.g. "Glen Release (1000 Ac-Ft)")
            start_month_year: Start date (e.g. "Mar 2025", "2025-03", "March 2025")
            end_month_year: End date
            date_col: Name of the date column (usually auto-detected)

        Returns:
            Sum of the column between the dates (float)
        """
        if df_monthly.empty:
            return 0.0

        # Auto-detect date column if not provided
        if date_col is None:
            for col in df_monthly.columns:
                if 'date' in col.lower() or pd.api.types.is_datetime64_any_dtype(df_monthly[col]):
                    date_col = col
                    break
            else:
                date_col = df_monthly.columns[0]  # fallback to first column

        # Make a copy to avoid modifying original
        df = df_monthly.copy()

        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        # Convert start/end strings to datetime
        start_date = pd.to_datetime(start_month_year, errors='coerce')
        end_date = pd.to_datetime(end_month_year, errors='coerce')

        # Filter the dataframe
        mask = (df[date_col] >= start_date) & (df[date_col] <= end_date)
        filtered = df[mask]

        if filtered.empty:
            print(f"Warning: No data found between {start_month_year} and {end_month_year}")
            return 0.0

        # Sum the requested column
        if column_name not in filtered.columns:
            raise KeyError(f"Column '{column_name}' not found. Available columns: {list(filtered.columns)}")

        total = pd.to_numeric(filtered[column_name], errors='coerce').sum()

        return float(total)

    @staticmethod
    def load_24_month(name:str, year:int, month:str)->Tuple[pd.DataFrame, pd.DataFrame|None]:
        res_peth = name.replace(' ', '_') + '.csv'
        path = f'data/USBR_24Month_Reports/{year}/{month.upper()}{year%100:02d}/'
        df_24_month, df_24_wy, units = Reservoir.read_usbr_24month_table(path + res_peth)
        return df_24_month, df_24_wy

    @staticmethod
    def load_24_month_min(name:str, year:int, month:str)->Tuple[pd.DataFrame, pd.DataFrame|None]:
        res_peth = name.replace(' ', '_') + '.csv'
        path = f'data/USBR_24Month_Reports/{year}/{month.upper()}{year%100:02d}_MIN/'
        df_24_month, df_24_wy, units = Reservoir.read_usbr_24month_table(path + res_peth)
        return df_24_month, df_24_wy

    @staticmethod
    def clean_column_name(col):
        col = str(col).strip()

        # Find unit in parentheses
        if '(' in col and ')' in col:
            base = col.split('(')[0].strip()
            unit = col.split('(')[1].split(')')[0].strip().lower()

            # Rule 1: If unit is 1000 acre feet (default), discard it
            if unit in ['1000 ac-ft']:
                return base
            # Rule 2: If unit is Ft or CFS or whatever, append without parens
            elif unit in ['feet', 'ft']:
                return f"{base} {unit}"
            elif unit in ['1000 CFS', '1000 cfs']:
                return f"{base} cfs"
            else:
                return f"{base} {unit}"
        return col

    @staticmethod
    def read_usbr_24month_table(file_path, parent_name: str = None):
        file_path = Path(file_path)

        # Skip the units row (row 1, 0-based)
        df = pd.read_csv(
            file_path,
            header=0,  # Use the first row as headers
            skiprows=[1],  # Skip the second row (units row)
            quoting=csv.QUOTE_NONE,
            escapechar='\\',
            dtype=str,
            keep_default_na=False
        )

        # Clean column names
        df.columns = [Reservoir.clean_column_name(col) for col in df.columns]

        # Fix first column name if needed
        if str(df.columns[0]).strip() in ['nan', '', 'Unnamed: 0']:
            df.columns = ['Date'] + list(df.columns[1:])

        date_col = df.columns[0]

        print("Loaded columns:", list(df.columns))  # ← debug

        # Split WY vs Monthly
        wy_mask = df[date_col].astype(str).str.contains(r'WY', case=False, na=False, regex=True)

        df_wy = df[wy_mask].copy().reset_index(drop=True)
        df_monthly = df[~wy_mask].copy().reset_index(drop=True)

        # Extra safety: remove any remaining WY rows from monthly
        df_monthly = df_monthly[~df_monthly[date_col].astype(str).str.contains(r'WY', case=False, na=False, regex=True)]

        # Convert to numeric
        for dframe in [df_monthly, df_wy]:
            if dframe.empty:
                continue
            for col in dframe.columns[1:]:
                dframe[col] = pd.to_numeric(dframe[col], errors='coerce')

        if parent_name:
            if not df_monthly.empty:
                df_monthly.insert(0, 'Source', parent_name)
            if not df_wy.empty:
                df_wy.insert(0, 'Source', parent_name)

        return df_monthly, df_wy, {}