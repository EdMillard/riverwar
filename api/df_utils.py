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
from datetime import date
import numpy as np
from typing import List, Union, Dict
import pandas as pd


def create_df(min_year: int, max_year: int, headers: List[str], zero=False):
    years = list(range(min_year, max_year + 1))

    df = pd.DataFrame(index=range(len(years)), columns=['Year'] + headers)
    df['Year'] = years
    if zero:
        df.iloc[:, 1:] = 0
    else:
        df.iloc[:, 1:] = pd.NA

    return df

def create_monthly_df(
    start_date: date | str | tuple[int, int, int],
    end_date: date | str | tuple[int, int, int],
    headers: list[str],
    include_end_month: bool = True
) -> pd.DataFrame:
    """
    Creates a DataFrame with one row per month between start and end date.
    The 'Date' column shows only 'Mon Year' format (e.g. 'Apr 2026', 'May 2026').
    """
    # Normalize inputs
    if isinstance(start_date, (tuple, list)):
        start_date = date(*start_date)
    if isinstance(end_date, (tuple, list)):
        end_date = date(*end_date)

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Generate monthly range
    dates = pd.date_range(
        start=start.replace(day=1),
        end=end,
        freq='MS',                    # Month Start
        inclusive='both' if include_end_month else 'left'
    )

    # Create friendly month-year labels
    month_labels = dates.strftime('%b %Y')

    # Build DataFrame
    df = pd.DataFrame(index=range(len(dates)))   # Simple integer index
    for col in headers:
        df[col] = pd.NA

    df['Date'] = month_labels

    return df


def create_daily_df(
        start_date: date | str | tuple[int, int, int],
        end_date: date | str | tuple[int, int, int],
        headers: list[str],
        include_end_date: bool = True
) -> pd.DataFrame:
    """
    Creates a DataFrame with one row per day between start_date and end_date,
    with a 'Date' column (datetime64[ns]) and the requested columns filled with pd.NA.

    Parameters:
        start_date: date, 'YYYY-MM-DD' string, or (year, month, day) tuple
        end_date:   date, 'YYYY-MM-DD' string, or (year, month, day) tuple
        headers: list of column names (excluding the Date column)
        include_end_date: whether to include the end_date row (default True)

    Returns:
        DataFrame with 'Date' column as first column
    """
    # Normalize inputs to datetime
    if isinstance(start_date, (tuple, list)):
        start_date = date(*start_date)
    if isinstance(end_date, (tuple, list)):
        end_date = date(*end_date)

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Generate daily date range
    dates = pd.date_range(
        start=start,
        end=end,
        freq='D',
        inclusive='both' if include_end_date else 'left'
    )

    # Create DataFrame with Date as a column (not index)
    df = pd.DataFrame({
        'Date': dates
    })

    # Add the requested columns filled with NA
    for col in headers:
        df[col] = pd.NA

    # Optional: Set clean dtypes
    df['Date'] = pd.to_datetime(df['Date']).dt.date  # or keep as datetime64[ns]
    # df['Date'] = pd.to_datetime(df['Date'])          # Uncomment if you prefer full datetime

    return df

def subtract_dataframes(
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        date_col: str = 'Date'
) -> pd.DataFrame:
    """
    Returns a new DataFrame containing ONLY the dates/rows that exist in BOTH df1 and df2.
    Subtracts (df1 - df2) only for those common dates.
    Columns that don't exist in both are dropped.
    """
    if date_col not in df1.columns or date_col not in df2.columns:
        raise ValueError(f"Date column '{date_col}' not found in one or both DataFrames.")

    # Find common dates
    common_dates = pd.merge(
        df1[[date_col]],
        df2[[date_col]],
        on=date_col,
        how='inner'
    )

    if common_dates.empty:
        print("Warning: No common dates between the two DataFrames.")
        return pd.DataFrame(columns=[date_col])

    # Merge only on common dates
    merged = pd.merge(
        df1,
        df2,
        on=date_col,
        how='inner',
        suffixes=('_1', '_2')
    )

    result = merged[[date_col]].copy()

    # Subtract columns that exist in both
    for col in df1.columns:
        if col == date_col:
            continue

        col1 = f"{col}_1"
        col2 = f"{col}_2"

        if col1 in merged.columns and col2 in merged.columns:
            result[col] = merged[col1] - merged[col2]

    return result

def fill_df_from_structured_array(
    df: pd.DataFrame,
    arr: np.ndarray,
    value_column_name: str = None,
    date_column_name: str = "Date",      # Default to 'Date' column
    method: str = 'setitem'              # 'setitem' (fast), 'loc', or 'at'
) -> pd.DataFrame:
    """
    Fills values from a structured array [('dt', '<M8[s]'), ('val', '<f4')]
    into the DataFrame by matching on the 'Date' column.

    Parameters:
        df: DataFrame with a 'Date' column (or specified date_column_name)
        arr: structured ndarray with fields 'dt' and 'val'
        value_column_name: column in df to fill (required if >1 data column)
        date_column_name: name of the date column in df (default: 'Date')
        method: 'setitem' (recommended/fastest), 'loc', or 'at'

    Returns:
        Modified DataFrame (filled in-place)
    """
    if len(arr) == 0:
        return df

    if date_column_name not in df.columns:
        raise ValueError(f"Date column '{date_column_name}' not found in DataFrame. "
                        f"Available columns: {list(df.columns)}")

    # Extract dates and values from structured array
    dates = arr['dt'].astype('datetime64[D]')   # truncate to day only
    values = arr['val']

    # Ensure df['Date'] is datetime for reliable comparison
    df_dates = pd.to_datetime(df[date_column_name]).dt.floor('D')

    # Determine which column to fill
    if value_column_name is None:
        data_cols = [c for c in df.columns if c != date_column_name]
        if len(data_cols) != 1:
            raise ValueError("value_column_name must be specified when there are multiple data columns")
        value_column_name = data_cols[0]

    if value_column_name not in df.columns:
        raise ValueError(f"Column '{value_column_name}' not found in DataFrame")

    # === Fastest and cleanest method ===
    if method == 'setitem':
        for dt, val in zip(dates, values):
            mask = (df_dates == dt)
            if mask.any():
                df.loc[mask, value_column_name] = val

    elif method == 'loc':
        for dt, val in zip(dates, values):
            mask = (df_dates == dt)
            if mask.any():
                df.loc[mask, value_column_name] = val

    elif method == 'at':
        # 'at' is fast but requires integer position or unique index
        df = df.set_index(date_column_name, drop=False)  # temporary index for 'at'
        for dt, val in zip(dates, values):
            if dt in df.index:
                df.at[dt, value_column_name] = val
        df = df.reset_index(drop=True)   # restore original structure
    else:
        raise ValueError("method must be 'setitem', 'loc', or 'at'")

    return df

def subtract_constant(
        df: pd.DataFrame,
        source_col: str,
        target_col: str,
        constant: float,
        inplace: bool = True
) -> None:
    """
    Subtract a constant from source_col and store result in target_col.

    Example:
        subtract_constant(df_daily, "Inflow_cfs", "Inflow_cfs_minus_5000", 5000)
    """
    if source_col not in df.columns:
        raise ValueError(f"Column '{source_col}' not found in DataFrame")

    if not inplace:
        df = df.copy()

    df[target_col] = df[source_col] - constant

    # Optional: convert to numeric and handle NaNs gracefully
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')

def add_column_sum(df: pd.DataFrame,
                   cols_to_sum: list,
                   sum_column_name: str = 'total_sum') -> pd.DataFrame:
    """
    Add (or update) a column with the row-wise sum of specified columns.
    Creates the target column if it doesn't exist.

    Parameters:
        df (pd.DataFrame): The DataFrame to modify.
        cols_to_sum (list): List of column names to sum.
        sum_column_name (str): Name of the column where the sum will be stored.

    Returns:
        pd.DataFrame: The original DataFrame with the sum column added/updated.
    """
    # Input validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    # Check all columns exist
    missing = [col for col in cols_to_sum if col not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in DataFrame: {missing}")

    # Add / overwrite the sum column
    df[sum_column_name] = df[cols_to_sum].sum(axis=1)

    return df

def rename_column(
        df: pd.DataFrame,
        old_name: Union[str, Dict[str, str]],
        new_name: str = None,
        inplace: bool = False
) -> pd.DataFrame:
    """
    Rename one or multiple columns in a DataFrame.

    Parameters:
        df (pd.DataFrame): Input DataFrame
        old_name (str or dict): Old column name (str) or dict of {old: new}
        new_name (str, optional): New column name (only used if old_name is str)
        inplace (bool): If True, modifies the original DataFrame. Default False.

    Returns:
        pd.DataFrame: DataFrame with renamed column(s)
    """
    if inplace:
        df_copy = df
    else:
        df_copy = df.copy()

    if isinstance(old_name, dict):
        # Rename multiple columns at once
        df_copy.rename(columns=old_name, inplace=True)
    elif isinstance(old_name, str):
        if new_name is None:
            raise ValueError("new_name must be provided when old_name is a string")
        df_copy.rename(columns={old_name: new_name}, inplace=True)
    else:
        raise TypeError("old_name must be a string or a dictionary")

    return df_copy