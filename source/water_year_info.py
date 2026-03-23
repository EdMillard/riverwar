"""
Copyright (c) 2022 Ed Millard

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
import calendar
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from pathlib import Path
import pytz
from typing import List, Tuple, Union, Any



class WaterYearInfo:
    format_float = '12.6f'
    verify_tolerance = 1e-9

    def __init__(self, year:int, start_date:date, end_date:date):
        self.year = year
        self.start_date = start_date
        self.end_date = end_date
        self.is_current_water_year = WaterYearInfo.is_date_within_range(start_date, end_date)
        self.is_water_year = self.start_date.month != 1
        if self.is_current_water_year:
            pass

    @staticmethod
    def is_date_within_range(
            start_date: date | str,
            end_date: date | str,
            current_date: date | str | None = None,
            inclusive: bool = True
    ) -> bool:
        """
        Check if the current date is within the specified date range.

        Parameters:
        -----------
        start_date : date, datetime, or str (YYYY-MM-DD)
            The start of the range
        end_date : date, datetime, or str (YYYY-MM-DD)
            The end of the range
        current_date : date, datetime, str, or None, optional
            The date to check. If None, uses today's date.
        inclusive : bool, default True
            If True, includes both start_date and end_date in the range.
            If False, excludes them (open interval).

        Returns:
        --------
        bool
            True if current_date is within the range, False otherwise.

        Examples:
        --------
        >>> is_date_within_range("2025-10-01", "2026-09-30")  # today = 2026-03-22
        True

        >>> is_date_within_range(date(2026, 1, 1), date(2026, 6, 30), inclusive=False)
        False  # March 22 is after Jan 1 but before July 1 → excluded if not inclusive

        >>> is_date_within_range("2027-01-01", "2027-12-31")
        False
        """
        # Normalize current_date
        if current_date is None:
            today = date.today()
        else:
            today = WaterYearInfo._to_date(current_date)

        # Normalize start and end
        start = WaterYearInfo._to_date(start_date)
        end = WaterYearInfo._to_date(end_date)

        # Basic validation
        if start > end:
            raise ValueError("start_date must be before or equal to end_date")

        if inclusive:
            return start <= today <= end
        else:
            return start < today < end

    @staticmethod
    def _to_date(value: date | datetime | str) -> date:
        """Helper to convert various inputs to date object."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            # Try common formats
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse date string: {value!r}. Use YYYY-MM-DD format.")
        raise TypeError(f"Unsupported type for date: {type(value)}")

    @staticmethod
    def get_water_year(input_date:date | datetime, month:int=1):
        """
        Calculate the water year and its start/end dates for a given date.
        Water year starts on Nov 1 and ends on Oct 31.
        Returns a tuple: (water_year, start_date, end_date)

        Args:
            input_date: datetime.date or datetime.datetime object

        Returns:
            WaterYearInfp
        """
        # Ensure input is a date object
        if isinstance(input_date, datetime):
            input_date = input_date.date()
        elif isinstance(input_date, np.datetime64):
            input_date = input_date.astype('datetime64[s]').astype(datetime)

        # Determine water year
        if month == 1:
            water_year = input_date.year
            start_date = date(water_year, 1, 1)
            end_date = date(water_year, 12, 31)
        else:
            if input_date.month >= month:
                water_year = input_date.year + 1
            else:
                water_year = input_date.year
            start_date = date(water_year - 1, month, 1)
            last_day_of_month  = WaterYearInfo.last_day_of_month(water_year, month-1)
            end_date = date(water_year, month-1, last_day_of_month)

        water_year_info = WaterYearInfo(water_year, start_date, end_date)
        return water_year_info

    @staticmethod
    def last_day_of_month(year: int, month: int) -> int:
        """
        Returns the last day of the given month/year.
        Handles leap years automatically.
        """
        return calendar.monthrange(year, month)[1]

    @staticmethod
    def is_current_datetime_greater(given_date, hours_offset=24):
        """
        Check if current datetime is greater than given numpy.datetime64 plus 24 hours in America/Denver timezone.

        Args:
            given_date (np.datetime64): Datetime in numpy.datetime64 format
            hours_offset (int) Number of hours to add to given_date
        Returns:
            bool: True if current datetime is greater than given datetime + 24 hours, False otherwise
        """
        # Convert numpy.datetime64 to pandas Timestamp
        given_date = pd.Timestamp(given_date)

        # Convert to timezone-aware datetime in America/Denver
        denver_tz = pytz.timezone('America/Denver')
        given_date_tz = given_date.tz_localize(denver_tz)

        # Add 24 hours
        target_date = given_date_tz + timedelta(hours=hours_offset)

        # Get current datetime in America/Denver
        current_date = pd.Timestamp.now(tz=denver_tz)

        # Return comparison result
        return current_date > target_date

    @staticmethod
    def compare_ndarray_containers(
            container1: Any,
            container2: Any
    ) -> List[Tuple[str, Union[float, None], Union[float, None]]]:
        """
        Compare two NdArrayItemContainers with (datetime64, float) tuples and return dates where
        float values differ or one container has a datetime the other doesn't.

        Args:
            container1: NdArrayItemContainer with (np.datetime64, float) tuples
            container2: NdArrayItemContainer with (np.datetime64, float) tuples

        Returns:
            List of tuples (date_str, float1, float2) where float values differ or one is None
        """

        def extract_items(container: Any) -> dict:
            """Extract datetime64 and float pairs into a dictionary, handling NdArrayItemContainer."""
            items = {}
            try:
                for item in container:
                    # Ensure item has two elements (datetime64, float)
                    if len(item) != 2:
                        continue  # Skip malformed items to avoid errors
                    date, value = item
                    # Convert to np.datetime64 if not already
                    date = np.datetime64(date)
                    # Ensure value is float or None
                    value = float(value) if value is not None else None
                    items[date] = value
            except (TypeError, ValueError) as e:
                # Log warning but continue processing
                print(f"Warning: Error processing item in container: {e}")
            return items

        # Extract items from both containers
        dict1 = extract_items(container1)
        dict2 = extract_items(container2)

        # Get all unique dates
        all_dates = set(dict1.keys()).union(set(dict2.keys()))

        # List to store differences
        differences = []

        for date in sorted(all_dates):
            val1 = dict1.get(date, None)
            val2 = dict2.get(date, None)

            # Check if values differ or one is missing
            if val1 != val2:
                # Convert datetime64 to string, removing microseconds
                date_str = str(pd.Timestamp(date)).split('.')[0]
                differences.append((date_str, val1, val2))

        return differences

    @staticmethod
    def diff_data(previous_data, new_data, file_path, old_file_moved_path):
        has_diffs = False
        has_updates = False

        diffs = WaterYearInfo.compare_ndarray_containers(previous_data, new_data)
        if diffs:
            for diff in diffs:
                if diff[1] is not None:
                    has_diffs = True
                else:
                    has_updates = True
            if has_diffs:
                print(f'\t{file_path} differ, backed up to {old_file_moved_path}: {diffs}')
            else:
                print(f'usbr rise load {file_path} updated: {diffs}')
                if old_file_moved_path is not None and old_file_moved_path.exists():
                    old_file_moved_path.unlink(missing_ok=True)
        else:
            if old_file_moved_path is not None and old_file_moved_path.exists():
                old_file_moved_path.unlink(missing_ok=True)

        return has_diffs, has_updates

    @staticmethod
    def move_file_with_mod_date(file_path: Path, tz_name: str = 'America/Denver') -> Path:
        """
        Move a file to a new file with the same name, appending the modification date to the stem.
        Retains the original suffix and uses a command-line-friendly date format.

        Args:
            file_path (Path): Path to the original file
            tz_name (str): Timezone name for modification date (default: 'America/Denver')

        Returns:
            Path: Path to the new file location

        Raises:
            FileNotFoundError: If the file does not exist
            OSError: If the file move operation fails
        """
        # Verify the file exists
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get the file's modification time
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)

        # Localize to specified timezone
        tz = pytz.timezone(tz_name)
        mod_time = tz.localize(mod_time)

        # Format date as YYYYMMDD_HHMMSS (command-line friendly)
        date_str = mod_time.strftime('%Y%m%d_%H%M%S')

        # Get file components
        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        # Create new file name with date appended to stem
        new_file_name = f"{stem}_{date_str}{suffix}"
        new_file_path = parent / new_file_name

        # Move the file
        try:
            file_path.rename(new_file_path)
            return new_file_path
        except OSError as e:
            raise OSError(f"Failed to move file {file_path} to {new_file_path}: {e}")

    @staticmethod
    def index_for_month_day(datetime_arr, target_month, target_day):
        dt_objects = [np.datetime64(dt).astype(object) for dt in datetime_arr]
        months = np.array([dt.month for dt in dt_objects])
        days = np.array([dt.day for dt in dt_objects])
        match_idx = np.where((months == target_month) & (days == target_day))[0]
        if len(match_idx) == 0:
            idx = None
        else:
            idx = match_idx[0]
        return idx

    @staticmethod
    def day_for_date(datetime_arr, date_str):
        if date_str == 'Feb-29':
            dt = datetime.strptime('Feb-28', '%b-%d')
            day_of_month = 29
        else:
            dt = datetime.strptime(date_str, '%b-%d')
            day_of_month = dt.day
        month = dt.month
        day = WaterYearInfo.index_for_month_day(datetime_arr, month, day_of_month)
        if day is None:
            day = len(datetime_arr)
        return day

    @staticmethod
    def format_to_month_day(dt64, leading_zeroes=True):
        ts = pd.to_datetime(dt64)
        if leading_zeroes:
            string = f"{ts.strftime('%b')}-{ts.day:02d}"
        else:
            string = f"{ts.strftime('%b')}-{ts.day}"
        return string
