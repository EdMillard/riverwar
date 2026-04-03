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
from pathlib import Path
import re
from collections import Counter
import pandas as pd
from source.water_year_info import WaterYearInfo
from datetime import date
from typing import List
from sheet import sheet

class Reservoir:
    high_power_pool_color = "lightblue"
    low_power_pool_color = "cornflowerblue"
    non_power_pool_color = '#ffbbff'
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

    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f" '\'{self.name}\'"
        string += f" '\'{self.elevation_feet} ft\'"
        string += f" '\'{self.active_capacity_af} af\'"

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
    def read_usbr_24month_table(file_path, first_header_row: int = 4, parent_name: str = None):
        file_path = Path(file_path)

        # 1. Read headers
        raw = pd.read_csv(file_path, header=None, dtype=str, quoting=3, escapechar='\\', engine='python')

        h1_idx = first_header_row - 1
        h2_idx = h1_idx + 1
        units_idx = h1_idx + 2
        data_start_idx = h1_idx + 3

        # Merge headers
        header1 = raw.iloc[h1_idx].fillna('').astype(str).str.strip()
        header2 = raw.iloc[h2_idx].fillna('').astype(str).str.strip()

        merged_headers = [(h1 or h2).strip() if not (h2 and h2 not in h1) else f"{h1} ({h2})".strip()
                          for h1, h2 in zip(header1, header2)]

        # 2. Read data rows line by line
        data_rows = []
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, quoting=csv.QUOTE_NONE, escapechar='\\')
            for _ in range(data_start_idx):
                next(reader, None)
            for row in reader:
                if row and not all(x.strip() == '' for x in row):
                    data_rows.append(row)

        if not data_rows:
            raise ValueError(f"No data rows found in {file_path}")

        # Determine correct column count from data
        max_cols = Counter(len(row) for row in data_rows).most_common(1)[0][0]
        merged_headers = merged_headers[:max_cols]

        # Align all rows
        cleaned_data = []
        for row in data_rows:
            row = row[:max_cols] + [''] * (max_cols - len(row))
            cleaned_data.append(row)

        df = pd.DataFrame(cleaned_data, columns=merged_headers)

        # Clean column names
        df.columns = [str(col).strip().replace('\n', ' ').replace('  ', ' ') for col in df.columns]

        date_col = df.columns[0]

        # Split WY vs Monthly
        def is_wy_row(val):
            return bool(re.search(r'WY\s*\d{4}', str(val), re.IGNORECASE))

        wy_mask = df[date_col].apply(is_wy_row)

        df_wy = df[wy_mask].copy().reset_index(drop=True)
        df_monthly = df[~wy_mask].copy().reset_index(drop=True)

        # === SAFE CONVERSION ===
        if not df_monthly.empty:
            df_monthly[date_col] = pd.to_datetime(df_monthly[date_col], errors='coerce')

            numeric_cols = [col for col in df_monthly.columns if col != date_col]
            for col in numeric_cols:
                try:
                    df_monthly[col] = pd.to_numeric(df_monthly[col], errors='coerce')
                except Exception as e:
                    print(f"Warning: Could not convert column '{col}' to numeric: {e}")

        if not df_wy.empty:
            numeric_cols = [col for col in df_wy.columns if col != date_col]
            for col in numeric_cols:
                try:
                    df_wy[col] = pd.to_numeric(df_wy[col], errors='coerce')
                except Exception as e:
                    print(f"Warning: Could not convert column '{col}' to numeric: {e}")

        if parent_name:
            if not df_monthly.empty:
                df_monthly.insert(0, 'Source', parent_name)
            if not df_wy.empty:
                df_wy.insert(0, 'Source', parent_name)

        units_dict = dict(zip(merged_headers, raw.iloc[units_idx].fillna('').astype(str).str.strip()[:max_cols]))

        return df_monthly, df_wy, units_dict