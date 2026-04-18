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
from __future__ import annotations
import copy
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
import pandas as pd
from ruamel.yaml.timestamp import TimeStamp
from source.water_year_info import WaterYearInfo
from datetime import date
from typing import List, Tuple, Literal, Optional
from sheet import sheet
from source import usbr_rise
import colorado.allb as all_b
from graph.water import WaterGraph
import calendar
from pandas.tseries.offsets import MonthEnd
from api import df_utils

class Reservoir:
    high_power_pool_color = "lightblue"
    low_power_pool_color = "cornflowerblue"
    non_power_pool_color = '#ffbbff'

    outflow_actual_color = 'red'
    outflow_projected_color = '#FF746C'

    inflow_actual_color = 'dodgerblue'          # Blue
    inflow_projected_color = 'skyblue'

    side_inflow_actual_color = '#5acf5a'    # Green
    side_inflow_projected_color = '#88ff88'

    evap_actual_color = '#FFEA00'           # Yellow
    evap_projected_color = '#FFDD33'

    cap_pump_actual_color = '#8B4513'       # Brown
    cap_pump_projected_color = '#D2A679'

    mwd_pump_actual_color = '#707070'     # Gray
    mwd_pump_projected_color = '#C0C0C0'

    snwa_pump_actual_color = '#9B59B6'      # Purple
    snwa_pump_projected_color = '#C39BD3'

    flow_to_mexico_actual_color = '#ff9966'      # Orange
    flow_to_mexico_projected_color = '#ffbb77'

    salton_actual_color = '#FFEA00'  # Yellow, same as evap
    salton_projected_color = '#FFDD33'

    def __init__(self, name:str, headers:List[str], upstream:Optional[List[Reservoir]]=None, month=10):
        self.name:str = name
        self.upstream = upstream
        self.water_year_month = month
        start_year = self.water_year = 2026
        self.water_year_info = self.get_water_year_info(start_year, month=month)

        # DataFrames
        self.headers = headers
        self.df: Optional[pd.DataFrame] = df_utils.create_df(self.water_year, self.water_year, self.headers)
        self.df_daily: Optional[pd.DataFrame] = None
        self.df_24_month: Optional[pd.DataFrame] = None
        self.df_24_wy: Optional[pd.DataFrame] = None
        self.date_time:TimeStamp = TimeStamp(1970, 1, 1)

        # Month Year Range
        #
        self.start_date = None
        self.current_date = None
        self.end_date = None
        self.today = date.today()

        self.report_start_date = None
        self.report_end_date = None

        self.start_month_year_actual = "Oct 2025"
        self.end_month_year_actual = "Mar 2026"
        self.start_month_year_projected = "Apr 2026"
        self.emd_month_year_projected = "Sep 2026"

        # USBR RISE ID's
        #
        self.usbr_rise_elevation_ft_id = 0
        self.usbr_rise_storage_af_id = 0
        self.end_of_month_storage_str = 'End Of Month Storage'
        self.usbr_rise_inflow_af_id = 0
        self.usbr_rise_evap_af_id = 0
        self.usbr_rise_release_af_id = 0
        self.usbr_rise_release_cfs_id = 0

        # Elevations
        #
        self.elevation_feet:float = 0
        self.active_capacity_af:float = 0
        self.evap_af:float = 0
        self.inflow_af:float = 0
        self.inflow_cfs:float = 0
        self.release_af:float = 0
        self.release_cfs:float = 0

        self.inflow_unregulated_af = 0
        self.inflow_unregulated_cfs = 0

        self.full_feet:float = 0
        self.power_head_target_feet:float = 0
        self.power_head_lowest_feet:float = 0
        self.turbine_intake_feet:float = 0
        self.dead_pool_feet:float = 0

        self.critical_elevations:List[float] = []

        self.inflow_actual_af = 0
        self.inflow_projected_af= 0
        self.inflow_parts:List[tuple] =  []

        self.side_inflow_actual_af = 0
        self.side_inflow_projected_af= 0
        self.side_inflow_parts:List[tuple] =  []

        self.outflow_actual_af = 0
        self.outflow_projected_af= 0
        self.outflow_parts:List[tuple] =  []

        self.evap_af = 0
        self.evap_actual_af = 0
        self.evap_projected_af= 0
        self.evap_parts:List[tuple] =  []

        # Reserve (i.e. ICS)
        self.reserved_parts:List[tuple] = []

    @staticmethod
    def get_end_of_month(d: date) -> date:
        """Return a date set to the last day of the input date's month."""
        if not isinstance(d, date):
            d = pd.to_datetime(d).date()  # in case it's a string or Timestamp

        last_day = calendar.monthrange(d.year, d.month)[1]
        return date(d.year, d.month, last_day)

    def load_date(self, report_path:Optional[Path], start_date:date, current_date:date, end_date:date):
        self.start_date = start_date
        self.current_date = current_date
        self.end_date = end_date
        previous_month = self.today - relativedelta(months=1)
        self.start_month_year_actual = start_date.strftime("%b %Y")
        self.end_month_year_actual = previous_month.strftime("%b %Y")
        self.start_month_year_projected = self.today.strftime("%b %Y")
        self.emd_month_year_projected = end_date.strftime("%b %Y")

        if report_path is not None:
            self.df_24_month, self.df_24_wy =  self.load_24_month(report_path, self.name)
            start_str = self.df_24_month['Date'].iloc[0]
            end_str = self.df_24_month['Date'].iloc[-1]
            self.report_start_date = pd.to_datetime(start_str, format="%b %Y").date()
            end_date = pd.to_datetime(end_str, format="%b %Y").date()
            self.report_end_date = Reservoir.get_end_of_month(end_date)
            self.df_daily = df_utils.create_daily_df(self.report_start_date, self.report_end_date, self.headers)
        else:
            self.df_daily = df_utils.create_daily_df(self.start_date, self.end_date, self.headers)
            self.report_start_date = self.start_date
            self.report_end_date = self.end_date
        
    def load_data(self, report_path:Path, start_date:date, current_date:date, end_date:date):
        pass

    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f" '\'{self.name}\'"
        string += f" '\'{self.elevation_feet} ft\'"
        string += f" '\'{self.active_capacity_af} af\'"

        return string

    def usbr_rise_load_daily(self, usbr_rise_id:int, column_name:str):

        daily = 0
        start_year = self.report_start_date.year
        end_year = self.report_end_date.year
        if end_year > date.today().year:
            end_year = date.today().year
        for year in range(start_year, end_year+1):
            self.water_year_info = self.get_water_year_info(year, month=self.water_year_month)

            info, daily = usbr_rise.load(usbr_rise_id,
                                                      water_year_info=self.water_year_info,
                                                      alias=column_name)
            df_utils.fill_df_from_structured_array(self.df_daily, daily, date_column_name='Date',
                                                value_column_name=column_name)
        return daily

    def get_elevation(self, usbr_rise_id:int, column_name:str)->Tuple[datetime, float]:
        when = Reservoir.compare_to_today(self.current_date)
        # print(f'relative time: {when}')
        if when == 'match':
            daily_elevation_ft = self.usbr_rise_load_daily(usbr_rise_id, column_name)
            date_time = daily_elevation_ft['dt'][-1]
            elevation_feet = daily_elevation_ft['val'][-1]
        elif when =='less':
            # actual for month
            date_time = self.date_time
            elevation_feet = Reservoir.get_value_for_month_year(self.df_24_month, self.current_date, 'Reservoir Elevation End of Month ft')
        else:
            # predicted for month
            date_time = self.date_time
            elevation_feet = Reservoir.get_value_for_month_year(self.df_24_month, self.current_date, 'Reservoir Elevation End of Month ft')

        return date_time, elevation_feet

    def get_storage(self, usbr_rise_id: int, column_name:str, month=all_b.WY, divisor:int=1)->float:
        active_capacity_af = 0
        when = Reservoir.compare_to_today(self.current_date)
        if when == 'match':
            if usbr_rise_id:
                daily_storage_af = self.usbr_rise_load_daily(usbr_rise_id, column_name)
                date_time = daily_storage_af['dt'][-1]
                active_capacity_af = daily_storage_af['val'][-1]
                # sheet.usbr_last_value(self.df, usbr_rise_id, self.water_year, self.water_year,
                #                       title=column_name, month=month, divisor=divisor)
                # active_capacity_af = self.get_value_by_year(self.water_year, column_name)
        elif when =='less':
            # actual for month
            active_capacity_af = Reservoir.get_value_for_month_year(self.df_24_month, self.current_date, self.end_of_month_storage_str)
        else:
            # predicted for month
            active_capacity_af = Reservoir.get_value_for_month_year(self.df_24_month, self.current_date, self.end_of_month_storage_str)

        return active_capacity_af

    def get_daily_and_last(self, usbr_rise_id: int, column_name:str, month=all_b.WY, divisor:int=1)->float:
        release = 0

        if usbr_rise_id:
            daily_release = self.usbr_rise_load_daily(usbr_rise_id, column_name)
            date_time = daily_release['dt'][-1]
            release = daily_release['val'][-1]

        return release

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

    @staticmethod
    def interpolate_monthly_storage_to_daily(
            df_monthly: pd.DataFrame,
            df_daily: pd.DataFrame,
            monthly_date_col: str = "Date",
            monthly_value_col: str = "Storage_af",
            daily_date_col: str = "Date",
            daily_target_col: str = "Storage_af",
            smoothing: str = "cubic"
    ) -> None:
        """
        Full smooth interpolation using ALL monthly points,
        then forces the first calendar month in df_daily to NaN.
        """
        if df_monthly.empty or df_daily.empty:
            return

        # 1. Prepare monthly data (end of each month)
        monthly = df_monthly[[monthly_date_col, monthly_value_col]].copy()
        monthly[monthly_date_col] = pd.to_datetime(
            monthly[monthly_date_col], format="%b %Y"
        ) + MonthEnd(0)

        monthly_series = monthly.set_index(monthly_date_col)[monthly_value_col].sort_index()

        # 2. Daily dates
        daily_dates = pd.to_datetime(df_daily[daily_date_col])

        # 3. Full interpolation using ALL monthly points
        if smoothing in ['quadratic', 'cubic'] and len(monthly_series) >= 3:
            from scipy.interpolate import interp1d
            x = monthly_series.index.astype('int64')
            y = monthly_series.values
            f = interp1d(x, y, kind=smoothing, fill_value="extrapolate")
            interpolated = f(daily_dates.astype('int64'))
        else:
            interpolated = monthly_series.reindex(daily_dates).interpolate(method='linear')

        # 4. Copy ALL interpolated values first
        df_daily[daily_target_col] = interpolated

        # 5. Then force the entire FIRST MONTH to NaN
        first_day = daily_dates.iloc[0]
        first_month_start = first_day.replace(day=1)
        first_month_end = first_month_start + MonthEnd(0)

        mask = (daily_dates >= first_month_start) & (daily_dates <= first_month_end)
        df_daily.loc[mask, daily_target_col] = pd.NA


    @staticmethod
    def usbr_end_of_month(
            df: pd.DataFrame,
            gage_id: int,
            year: int,
            column_name: str,
            cfs_to_af: bool = False,
            month: int = 1
    ) -> None:
        """
        Gets last value for each FULL month, then explicitly adds the very last record
        if it belongs to a partial month.
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame.")

        # Load data
        if month != 1:
            ts = pd.Timestamp(f'{year - 1}-{month:02d}-01')
        else:
            ts = pd.Timestamp(f'{year}-{month:02d}-01')

        water_year_info = WaterYearInfo.get_water_year(ts, month=month)

        if cfs_to_af:
            info, raw_data = usbr_rise.load(gage_id, water_year_info=water_year_info)
            daily_data = WaterGraph.convert_cfs_to_af_per_day(raw_data)
        else:
            info, daily_data = usbr_rise.load(gage_id, water_year_info=water_year_info)

        # Convert to DataFrame
        daily_list = list(daily_data)
        dates = [item[0] for item in daily_list]
        values = [item[1] for item in daily_list]

        daily_df = pd.DataFrame({'date': dates, 'value': values})
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        daily_df['month_label'] = daily_df['date'].dt.strftime('%b %Y')

        # 1. Get last value for each FULL month
        monthly = daily_df.groupby('month_label').last().reset_index()

        # 2. Check the very last record in the entire dataset
        if len(daily_list) > 0:
            last_item = daily_list[-1]
            last_date = pd.to_datetime(last_item[0])
            last_month_label = last_date.strftime('%b %Y')
            last_value = float(last_item[1])

            # If this last record is in a month that isn't fully covered or is the current month
            if last_month_label not in monthly['month_label'].values:
                # Add it as a new row
                new_row = pd.DataFrame({
                    'month_label': [last_month_label],
                    'date': [last_date],
                    'value': [last_value]
                })
                monthly = pd.concat([monthly, new_row], ignore_index=True)
            else:
                # Override with the absolute last value for that month
                monthly.loc[monthly['month_label'] == last_month_label, 'value'] = last_value

        # Fill into target DataFrame
        mask = df['Date'].isin(monthly['month_label'])
        filled = mask.sum()

        # print(f"✓ Filled {filled} months into '{column_name}' (last value per month + forced partial month)")

    @staticmethod
    def usbr_monthly(
            df: pd.DataFrame,
            gage_id: int,
            year: int,
            column_name: str,
            cfs_to_af: bool = False,
            month: int = 1
    ) -> None:
        """
        Fills monthly USBR data into your existing monthly DataFrame.
        Matches by 'Date' column ('Apr 2026', 'May 2026', etc.).
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame.")

        # Get the data using your original logic
        if month != 1:
            ts = pd.Timestamp(f'{year - 1}-{month:02d}-01')
        else:
            ts = pd.Timestamp(f'{year}-{month:02d}-01')

        water_year_info = WaterYearInfo.get_water_year(ts, month=month)

        if cfs_to_af:
            info, daily_cfs = usbr_rise.load(gage_id, water_year_info=water_year_info)
            daily_af = WaterGraph.convert_cfs_to_af_per_day(daily_cfs)
        else:
            info, daily_af = usbr_rise.load(gage_id, water_year_info=water_year_info)

        monthly_af = usbr_rise.daily_to_monthly_sum(daily_af)

        # Fill values by matching month-year string
        for entry in monthly_af:
            if 'dt' not in entry:
                continue

            # Convert to 'Mon Year' format to match your df
            entry_date = pd.to_datetime(entry['dt'])
            mon_year_str = entry_date.strftime('%b %Y')

            # Find the row and put the value
            mask = df['Date'] == mon_year_str

            if mask.any():  # type: ignore[attr-defined]
                value = entry.get('val')
                if value is not None:
                    df.loc[mask, column_name] = float(value)
                else:
                    print(f'fill_usbt_monthly_into_df failed: month-year not found -> {mon_year_str}')

        filled = df[column_name].notna().sum()
        # print(f"✓ Filled {filled} months into '{column_name}' for gage {gage_id}")

    @staticmethod
    def get_value_for_month_year(
            df: pd.DataFrame,
            target_month_year: date,
            column_name: str,
            date_column: str = 'Date'  # if None, uses first column
    ) -> Optional[float]:
        """
        Returns the value for a given 'Mon Year' string (e.g. 'Mar 2026')
        """
        if date_column is None:
            date_column = df.columns[0]  # First column by default

        # Find the matching row
        month_name = target_month_year.strftime("%b")
        date_str = f"{month_name} {target_month_year.year}"
        mask = df[date_column] == date_str

        if not mask.any():
            print(f"Warning: '{target_month_year}' not found in column '{date_column}'")
            return None

        # Return the value (first match)
        value = df.loc[mask, column_name].iloc[0]
        return float(value) if pd.notna(value) else None

    def get_24_month_projected(self, df, column_name:str)->float:
        total = Reservoir.sum_column_between_dates(
            df,
            column_name=column_name,
            start_month_year=self.start_month_year_projected,
            end_month_year=self.emd_month_year_projected
        )
        return total

    def get_24_month_actual(self, df, column_name:str)->float:
        total = Reservoir.sum_column_between_dates(
            df,
            column_name=column_name,
            start_month_year=self.start_month_year_actual,
            end_month_year=self.end_month_year_actual
        )
        return total

    def get_value_by_year(self, year: int, column_name: str):
        """
        Returns the value from a DataFrame for a given year and column.

        Parameters:
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

        if not mask.any():  # type: ignore[attr-defined]
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
    def compare_to_today(
            target_date: date,
            mode: Literal["month_year", "full"] = "month_year"
    ) -> Literal["less", "match", "greater"]:
        """
        Compare a date against today's date.

        Parameters:
            target_date: One of self.start_date, self.current_date, or self.end_date
            mode: "month_year" = ignore day, "full" = compare exact date

        Returns: "less", "match", or "greater"
        """
        today = date.today()

        if mode == "month_year":
            # Compare only year and month
            target_ym = (target_date.year, target_date.month)
            today_ym = (today.year, today.month)

            if target_ym < today_ym:
                return "less"
            elif target_ym > today_ym:
                return "greater"
            else:
                return "match"

        else:  # full date comparison
            if target_date < today:
                return "less"
            elif target_date > today:
                return "greater"
            else:
                return "match"
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

    @staticmethod
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
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', format='%b %Y')

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
    def load_24_month(report_path:Path, name:str)->Tuple[pd.DataFrame, pd.DataFrame] | Tuple[None, None]:
        if report_path is not None:
            res_peth = name.replace(' ', '_') + '.csv'
            path = report_path / res_peth
            df_24_month, df_24_wy, units = Reservoir.read_usbr_24month_table(path)
            return df_24_month, df_24_wy
        else:
            return None, None

    def get_24_month_inflow(self, df:pd.DataFrame, inflow_name:str, side:str|None=None)\
            -> List[Tuple[str, float, str]]:
        inflow_actual_af = self.get_24_month_actual(df, inflow_name)
        if side is not None:
            side_inflow_actual_af = self.get_24_month_actual(df, side)
        else:
            side_inflow_actual_af = 0
        self.inflow_actual_af = inflow_actual_af + side_inflow_actual_af


        inflow_project_af = self.get_24_month_projected(df, inflow_name)
        if side is not None:
            side_inflow_projected_af = self.get_24_month_projected(df, side)
        else:
            side_inflow_projected_af = 0
        self.inflow_projected_af = inflow_project_af + side_inflow_projected_af

        parts = [("Actual", self.inflow_actual_af, Reservoir.inflow_actual_color),
                 ("Projected", self.inflow_projected_af, Reservoir.inflow_projected_color)]
        return parts

    def get_24_month_side_inflow(self, df:pd.DataFrame, name:str)\
            -> List[Tuple[str, float, str]]:

        self.side_inflow_actual_af = self.get_24_month_actual(df, name)
        self.side_inflow_projected_af = self.get_24_month_projected(df, name)
        parts = [("Actual", self.side_inflow_actual_af, Reservoir.side_inflow_actual_color),
                 ("Projected", self.side_inflow_projected_af, Reservoir.side_inflow_projected_color)]
        return parts

    def get_24_month_outflow(self, df:pd.DataFrame, name:str="Total Release")\
            -> List[Tuple[str, float, str]]:
        self.outflow_actual_af = self.get_24_month_actual(df, name)
        self.outflow_projected_af = self.get_24_month_projected(df, name)
        parts = [("Actual", self.outflow_actual_af, Reservoir.outflow_actual_color),
                 ("Projected", self.outflow_projected_af, Reservoir.outflow_projected_color)]
        return parts

    def get_24_month_evap(self, df:pd.DataFrame, name:str='Evaporation Losses')\
            -> List[Tuple[str, float, str]]:
        self.evap_actual_af = self.get_24_month_actual(df, name)
        self.evap_projected_af = self.get_24_month_projected(df, name)
        parts = [("Actual", self.evap_actual_af, Reservoir.evap_actual_color),
                 ("Projected", self.evap_projected_af, Reservoir.evap_projected_color)]
        return parts

    @staticmethod
    def load_24_month_min(name:str, year:int, month:str)->Tuple[pd.DataFrame, pd.DataFrame|None]:
        res_peth = name.replace(' ', '_') + '.csv'
        path = f'data/USBR_24Month_Reports/{year}/{month.upper()}{year%100:02d}_MIN/'
        df_24_month, df_24_wy, units = Reservoir.read_usbr_24month_table(path + res_peth)
        return df_24_month, df_24_wy

    @staticmethod
    def clean_column_name(col)->Tuple[str, str]:
        col = str(col).strip()
        unit = ''
        # Find unit in parentheses
        if '(' in col and ')' in col:
            base = col.split('(')[0].strip()
            unit = col.split('(')[1].split(')')[0].strip().lower()

            # Rule 1: If unit is 1000 acre feet (default), discard it
            if unit in ['1000 ac-ft']:
                return base, unit
            # Rule 2: If unit is Ft or CFS or whatever, append without parens
            elif unit in ['feet', 'ft']:
                return f"{base} {unit}", unit
            elif unit in ['1000 CFS', '1000 cfs']:
                return f"{base} cfs", unit
            else:
                return f"{base} {unit}", unit
        return col, unit

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
        new_columns = []
        multiplier_columns = {}
        for col in df.columns:
            clean_name, unit = Reservoir.clean_column_name(col)
            new_columns.append(clean_name)

            if unit.lower().startswith('1000') or '1000' in unit:
                multiplier_columns[clean_name] = 1000.0

        # Apply new column names
        df.columns = new_columns

        # Apply scaling where needed
        for col, factor in multiplier_columns.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col] * factor
                df[col] = df[col].round(0).astype('Int64')
                # print(f"Scaled column '{col}' by {factor:,}")

        # Fix first column name if needed
        if str(df.columns[0]).strip() in ['nan', '', 'Unnamed: 0']:
            df.columns = ['Date'] + list(df.columns[1:])

        date_col = df.columns[0]

        # print("Loaded columns:", list(df.columns))  # ← debug

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