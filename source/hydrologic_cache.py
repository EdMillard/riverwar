"""
hydrologic_cache.py

Shared water-year caching and aggregation helpers for hydrologic time-series data.
Returns structured numpy arrays for legacy compatibility with existing client code.
"""

from __future__ import annotations

import datetime
from datetime import date
from pathlib import Path
from typing import Callable, Any, Optional

import numpy as np
import pandas as pd

from source.water_year_info import WaterYearInfo


def daily_to_water_year(
    a: np.ndarray,
    water_year_start_month: int = 10,
    cfs_to_af: float = 1.983459,
) -> np.ndarray:
    """
    Convert daily values to water-year totals.

    Water Year N starts on ``water_year_start_month`` 1 of year (N-1)
    and is labeled as year N (standard convention).
    """
    if a is None or len(a) == 0:
        return np.zeros(0, dtype=[("dt", "i4"), ("val", "f8")])

    sorted_a = np.sort(a, order="dt")

    result: list[tuple[int, float]] = []
    current_wy: Optional[int] = None
    total = 0.0

    for row in sorted_a:
        dt_obj = pd.Timestamp(row["dt"]).to_pydatetime()
        val = row["val"]

        if dt_obj.month >= water_year_start_month:
            wy_year = dt_obj.year + 1
        else:
            wy_year = dt_obj.year

        if current_wy is None or wy_year != current_wy:
            if current_wy is not None and total > 0:
                result.append((current_wy, total * cfs_to_af))
            current_wy = wy_year
            total = 0.0

        if not np.isnan(val):
            total += val

    if current_wy is not None and total > 0:
        result.append((current_wy, total * cfs_to_af))

    return np.array(result, dtype=[("dt", "i4"), ("val", "f8")])


def daily_year_valid(
    daily: np.ndarray,
    water_year_info: WaterYearInfo,
    file_path: Path | str | None = None,
) -> bool:
    """Check whether a daily series covers the expected water-year window."""
    if daily is None or len(daily) == 0:
        return False

    start_dt = pd.Timestamp(daily[0]["dt"]).date()
    end_dt = pd.Timestamp(daily[-1]["dt"]).date()

    ok = (
        start_dt == water_year_info.start_date
        or end_dt == water_year_info.end_date
    )
    if not ok and file_path is not None:
        print(
            f"Misaligned water year, reloading: {file_path} "
            f"{start_dt} {water_year_info.start_date} "
            f"{end_dt} {water_year_info.end_date}"
        )
    return ok


class WaterYearCache:
    """
    Manages on-disk caching of hydrologic time series keyed by water year.

    Handles path construction, staleness checks, moving old files before
    overwrite, optional diffing of previous vs new data, and the
    load-or-fetch cycle. Provider-specific URL building and parsing
    are supplied via callbacks.
    """

    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Layout helpers (dual-directory for USGS / USBR, single for CDSS)
    # ------------------------------------------------------------------

    @classmethod
    def for_usgs(cls, water_year_info: WaterYearInfo | None = None) -> "WaterYearCache":
        """USGS layout: WY subdirectory when the series is a water year."""
        if water_year_info is not None and getattr(water_year_info, "is_water_year", False):
            root = Path("data/USGS_Gages/WY")
        else:
            root = Path("data/USGS_Gages")
        return cls(root)

    @classmethod
    def for_usbr(cls, water_year_info: WaterYearInfo | None = None) -> "WaterYearCache":
        """USBR RISE layout: WY subdirectory when the series is a water year."""
        if water_year_info is not None and getattr(water_year_info, "is_water_year", False):
            root = Path("data/USBR_RISE/WY")
        else:
            root = Path("data/USBR_RISE")
        return cls(root)

    @classmethod
    def for_cdss(cls) -> "WaterYearCache":
        """CDSS layout: single directory (upper-basin water years only)."""
        return cls(Path("data/cdss"))

    # ------------------------------------------------------------------
    # Path / staleness / load-or-fetch
    # ------------------------------------------------------------------

    def path_for(
        self,
        key: str,
        water_year_info: WaterYearInfo | None = None,
        suffix: str = "",
        extension: str = ".json",
    ) -> Path:
        """
        Build the cache file path.

        Form: ``base/key[_suffix][_YYYY].ext``
        """
        name = key
        if suffix:
            name = f"{name}_{suffix}"
        if water_year_info is not None:
            name = f"{name}_{water_year_info.year}"
        return self.base_dir / f"{name}{extension}"

    @staticmethod
    def is_stale(
        path: Path,
        water_year_info: WaterYearInfo | None,
        last_date: date | datetime.datetime | np.datetime64 | None,
        hours_offset: int = 48,
    ) -> bool:
        """Decide whether a cached file should be refreshed."""
        if not path.exists():
            return True
        if water_year_info is None:
            return False

        if water_year_info.is_current_water_year:
            if last_date is None:
                return True
            return WaterYearInfo.is_current_datetime_greater(
                last_date, hours_offset=hours_offset
            )

        if last_date is None:
            return True
        last = pd.Timestamp(last_date).date()
        end = pd.Timestamp(water_year_info.end_date).date()
        return end > last

    @staticmethod
    def _move_old_file(path: Path) -> Path | None:
        """Move an existing cache file aside before overwriting it."""
        if path.exists():
            return WaterYearInfo.move_file_with_mod_date(path)
        return None

    def load_or_fetch(
        self,
        key: str,
        water_year_info: WaterYearInfo | None,
        fetch_fn: Callable[[Path], Any],
        parse_fn: Callable[[Path], Optional[np.ndarray]],
        *,
        suffix: str = "",
        extension: str = ".json",
        force: bool = False,
        hours_offset: int = 48,
        move_on_update: bool = True,
        diff_on_update: bool = True,
    ) -> Optional[np.ndarray]:
        """
        Load data from cache or fetch it if missing or stale.
        """
        path = self.path_for(key, water_year_info, suffix=suffix, extension=extension)

        cached = None
        if path.exists() and not force:
            cached = parse_fn(path)
            last_date = None
            if cached is not None and len(cached):
                last_date = cached[-1]["dt"]

            if not self.is_stale(path, water_year_info, last_date, hours_offset):
                return cached

        # About to overwrite
        old_path = None
        if move_on_update and path.exists():
            old_path = self._move_old_file(path)

        # Fetch fresh data
        fetch_fn(path)

        # Re-parse
        new_data = None
        if path.exists():
            new_data = parse_fn(path)

        # Diff if we have both sides
        if diff_on_update and cached is not None and new_data is not None:
            WaterYearInfo.diff_data(cached, new_data, path, old_path)

        return new_data if new_data is not None else cached