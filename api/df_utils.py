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
from typing import List, Union, Dict, Optional
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


import pandas as pd
from typing import List, Tuple, Optional


def add_columns_across_dfs(
        sources: List[Tuple[pd.DataFrame, str]],
        target_df: pd.DataFrame,
        result_column: str = 'total_sum',
        key_column: Optional[str] = None,
        inplace: bool = True,
        fill_value: float = 0.0
) -> pd.DataFrame:
    """
    Sum columns from multiple DataFrames into target_df, aligned by key_column.
    """
    if not isinstance(target_df, pd.DataFrame):
        raise TypeError("target_df must be a pandas DataFrame")

    if not sources:
        raise ValueError("sources list cannot be empty")

    target = target_df if inplace else target_df.copy()

    # Auto-detect key column
    if key_column is None:
        for candidate in ['Year', 'Date', 'year', 'date', 'Month', 'quarter']:
            if candidate in target.columns:
                key_column = candidate
                break
        else:
            raise ValueError("Could not auto-detect key_column. Please specify it.")

    if key_column not in target.columns:
        raise ValueError(f"Key column '{key_column}' not found in target_df")

    # === CRITICAL FIXES ===
    # 1. Ensure key_column is the same dtype everywhere
    target_key = target[key_column].astype(str).str.strip()

    # Initialize result column safely
    if result_column in target.columns:
        target[result_column] = pd.to_numeric(target[result_column], errors='coerce')
    else:
        target[result_column] = fill_value

    # Make sure it's numeric (prevents object dtype issues)
    target[result_column] = pd.to_numeric(target[result_column], errors='coerce').fillna(fill_value)

    for src_df, col_name in sources:
        if col_name not in src_df.columns:
            raise ValueError(f"Column '{col_name}' not found in source DataFrame")

        # Normalize key in source too
        src_key = src_df[key_column].astype(str).str.strip()
        src_map = pd.Series(
            pd.to_numeric(src_df[col_name], errors='coerce').fillna(fill_value).values,
            index=src_key
        )

        # Map and add
        mapped = target_key.map(src_map).fillna(fill_value)
        target[result_column] = target[result_column] + mapped

    return target

def subtract_column(
        df: pd.DataFrame,
        col1: str,
        col2: str,
        result_column: str = 'difference',
        inplace: bool = True
) -> pd.DataFrame:
    """
    Subtract one column from another and store the result in a new column.
    Creates the result column if it doesn't exist.

    Parameters:
        df (pd.DataFrame): The DataFrame to modify.
        col1 (str): Column to subtract from (minuend).
        col2 (str): Column to subtract (subtrahend). Result = col1 - col2.
        result_column (str): Name of the column to store the result.
        inplace (bool): Whether to modify the DataFrame in place (default True).

    Returns:
        pd.DataFrame: The modified DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    # Check both columns exist
    missing = [col for col in [col1, col2] if col not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in DataFrame: {missing}")

    # Work on a copy or inplace
    if inplace:
        target = df
    else:
        target = df.copy()

    # Perform subtraction and create/update column
    target[result_column] = target[col1] - target[col2]

    return target

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

def copy_column(
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        column_name: str,
        new_name: Optional[str] = None,
        key_column: Optional[str] = None,
        inplace: bool = True
) -> pd.DataFrame:
    """
    Copy a column from source_df to target_df, aligning on a key column (Year/Date).
    Creates the column if it doesn't exist.

    Parameters:
        source_df (pd.DataFrame): Source DataFrame
        target_df (pd.DataFrame): Target DataFrame
        column_name (str): Column to copy from source
        new_name (str, optional): Name to use in target (default = column_name)
        key_column (str, optional): Column to match on (auto-detects 'Year' or 'Date')
        inplace (bool): Modify target_df in place if True

    Returns:
        pd.DataFrame: Target DataFrame with the copied column
    """
    if column_name not in source_df.columns:
        raise KeyError(f"Column '{column_name}' not found in source DataFrame")

    # Auto-detect key column if not provided
    if key_column is None:
        for candidate in ['Year', 'Date', 'year', 'date']:
            if candidate in source_df.columns and candidate in target_df.columns:
                key_column = candidate
                break
        else:
            raise ValueError("No common key column (Year/Date) found. Please specify key_column.")

    if key_column not in source_df.columns or key_column not in target_df.columns:
        raise ValueError(f"Key column '{key_column}' not found in both DataFrames")

    # Use new name or original
    target_col_name = new_name if new_name is not None else column_name

    if inplace:
        target = target_df
    else:
        target = target_df.copy()

    # Create a mapping from source: key → value
    source_map = source_df.set_index(key_column)[column_name]

    # Assign to target (aligns on key_column)
    target[target_col_name] = target[key_column].map(source_map)

    # Optional: Warn if many values couldn't be matched
    missing = target[target_col_name].isna().sum()
    if missing > 0:
        print(f"Warning: {missing} rows in target could not be matched on '{key_column}'")

    return target