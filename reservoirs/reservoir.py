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
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from api.registry import Registry
import json
from pathlib import Path
import numpy as np
from ruamel.yaml.timestamp import TimeStamp
from typing import List, Tuple, Literal, Optional, Dict
from sheet import sheet
from source import usbr_rise
import colorado.allb as all_b
from graph.water import WaterGraph
import calendar
from pandas.tseries.offsets import MonthEnd
from api import df_utils
import pytz
from data_sets.data_set import DataSet
from source.usgs_gage import USGSGage
from source import cdss
import pandas as pd
from source.water_year_info import WaterYearInfo

# Head and tail USBR JSON Files for verification
# find . -name '*2026.json' -type f -printf '%T@ %p\0' | sort -zn | cut -zd' ' -f2- | xargs -0 -I {} sh -c 'echo "=== {} ==="; head -n 10 "{}"; echo "..."; tail -n 8 "{}"; echo "────────────────────────────────────────"'
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

    def __init__(self, name:str, headers:List[str], catalog_id:int=0, upstream:Optional[List[Reservoir]]=None, month=10):
        self.name:str = name
        self.catalog_id = catalog_id
        self.upstream = upstream
        self.water_year_month = month
        start_year = self.water_year = 2026
        self.start_year_data = 0
        self.water_year_info = self.get_water_year_info(start_year, month=month)

        # USBR RISE ID's
        #
        self.usbr_rise_elevation_ft_id = 0
        self.usbr_rise_storage_af_id = 0
        self.end_of_month_storage_str = 'End Of Month Storage'
        self.usbr_rise_inflow_af_id = 0
        self.usbr_rise_evap_af_id = 0
        self.usbr_rise_release_af_id = 0
        self.usbr_rise_release_cfs_id = 0

        self.usbr_item_ids = {}
        if self.catalog_id:
            path = Path(f'data/USBR_RISE/catalog/{self.name_as_file_name()}.json')
            if path.exists():
                f = path.open(mode='r')
                self.usbr_item_ids = json.load(f)
            else:
                data = usbr_rise.load_catalog(Path(f'data/USBR_RISE/catalog/{self.catalog_id}'), f'{self.catalog_id}')
                attributes = data.get('attributes', None)
                record_title = attributes.get('recordTitle', None)
                if record_title is not None:
                    print(record_title)
                relationships = data.get('relationships', None)
                if relationships is not None:
                    location = relationships.get('location', None)
                    if location is not None:
                        location_name, states = usbr_rise.request_location(location)
                        self.usbr_item_ids['location_name'] = location_name
                        self.usbr_item_ids['states'] = states

                    catalog_items = relationships.get('catalogItems', None)
                    catalog_data = catalog_items.get('data', None)
                    for item in catalog_data:
                        data_id = item.get('id', None)
                        if data_id:
                            name, item_id = usbr_rise.request_catalog_item(data_id)
                            self.usbr_item_ids[name] = item_id

                    f = path.open(mode='w')
                    json_str = json.dumps(self.usbr_item_ids, indent=4)
                    f.write(json_str)
                    f.close()

            if self.usbr_item_ids:
                self.location_name = self.usbr_item_ids.get('location_name', '')
                if not self.location_name.startswith(self.name):
                    print(f'Reservoir nane mismatch {self.name} {self.location_name}')
                self.states = self.usbr_item_ids.get('states', None)
                self.usbr_rise_elevation_ft_id = self.usbr_item_ids.get('elevation_ft', 0)
                self.usbr_rise_storage_af_id = self.usbr_item_ids.get('storage_af', 0)
                self.usbr_change_in_storage_af_id = self.usbr_item_ids.get('change_in_storage_af', 0)
                self.usbr_rise_inflow_af_id = self.usbr_item_ids.get('inflow_af', 0)
                self.usbr_rise_inflow_cfs_id = self.usbr_item_ids.get('inflow_cfs', 0)
                self.usbr_rise_inflow_unregulated_af_id = 0
                self.usbr_rise_inflow_unregulated_cfs_id = 0
                self.usbr_rise_evap_af_id = self.usbr_item_ids.get('evaporation_af', 0)
                self.usbr_rise_release_af_id = self.usbr_item_ids.get('release_total_af', 0)
                self.usbr_rise_release_cfs_id = self.usbr_item_ids.get('release_total_cfs', 0)
                self.usbr_rise_area_acres_id = self.usbr_item_ids.get('area_acres', 0)
            else:
                self.location_name = ''
                self.states = []

        # DataFrames
        self.headers = headers
        self.df: Optional[pd.DataFrame] = df_utils.create_df(self.water_year, self.water_year, self.headers)
        self.df_daily: Optional[pd.DataFrame] = None
        self.df_annual: Optional[pd.DataFrame] = None

        self.report_path: Optional[str|None] = ''
        self.df_24_month: Optional[pd.DataFrame] = None
        self.df_24_wy: Optional[pd.DataFrame] = None
        self.date_time:TimeStamp = TimeStamp(1970, 1, 1)

        # Annual Range
        #
        self.start_year:Optional[int] = None
        self.end_year:Optional[int] = None

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

        # Elevations
        #
        self.elevation_feet:float = 0
        self.active_capacity_af:float = 0
        self.storage_one_month_ago: float = 0
        self.storage_two_months_ago: float = 0
        self.evap_af:float = 0
        self.inflow_af:float = 0
        self.inflow_cfs:float = 0
        self.release_af:float = 0
        self.release_cfs:float = 0

        self.inflow_unregulated_af = 0
        self.inflow_unregulated_cfs = 0

        self.full_feet:float = 0
        self.power_head_target_feet:float = 0
        self.power_head_min_af:float = 0
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

    def name_as_file_name(self) -> str:
        return self.name.replace(' ', '_')

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
            if self.report_path != report_path:
                self.df_24_month, self.df_24_wy =  self.load_24_month(report_path, self.name)
                if self.df_24_month is not None:
                    start_str = self.df_24_month['Date'].iloc[0]
                    end_str = self.df_24_month['Date'].iloc[-1]
                    self.report_start_date = pd.to_datetime(start_str, format="%b %Y").date()
                    end_date = pd.to_datetime(end_str, format="%b %Y").date()
                    self.report_end_date = Reservoir.get_end_of_month(end_date)
                    self.df_daily = df_utils.create_daily_df(self.report_start_date, self.report_end_date, self.headers)
                    self.report_path = report_path
                else:
                    self.df_daily = df_utils.create_daily_df(self.start_date, self.end_date, self.headers)
                    self.report_start_date = self.start_date
                    self.report_end_date = self.end_date
        else:
            self.df_daily = df_utils.create_daily_df(self.start_date, self.end_date, self.headers)
            self.report_start_date = self.start_date
            self.report_end_date = self.end_date

    def annual_maf(self)->pd.DataFrame:
        df = self.df_annual.copy()
        exclude_cols = ['Year', all_b.ELEVATION]
        cols_to_scale = [col for col in df.columns if col not in exclude_cols]
        df[cols_to_scale] = df[cols_to_scale] / 1_000_000
        return df

    def load_data_annual(self, start_year:Optional[int]=None, end_year:Optional[int]=None)->pd.DataFrame:
        if start_year is None or start_year < self.start_year:
            start_year = self.start_year
        if end_year is None:
            end_year = date.today().year
        if self.df_annual is None or start_year != self.start_year or self.end_year != end_year:
            self.start_year = start_year
            self.end_year = end_year
            self.df_annual: pd.DataFrame = df_utils.create_df(self.start_year, self.end_year,
                                                         [all_b.STORAGE, all_b.ELEVATION, all_b.RELEASE, all_b.EVAPORATION,
                                                          all_b.INFLOW])
            if self.usbr_rise_storage_af_id:
                sheet.usbr_last_value(self.df_annual, self.usbr_rise_storage_af_id, self.start_year, self.end_year, month=all_b.WY,
                                      title=all_b.STORAGE, divisor=1)
            if self.usbr_rise_elevation_ft_id:
                sheet.usbr_last_value(self.df_annual, self.usbr_rise_elevation_ft_id, self.start_year, self.end_year, month=all_b.WY,
                                      title=all_b.ELEVATION, divisor=1)
            if self.usbr_rise_release_af_id:
                sheet.usbr_annuals(self.df_annual,self.usbr_rise_release_af_id, self.start_year, self.end_year, month=all_b.WY,
                                   title=all_b.RELEASE, divisor=1)
            if  self.usbr_rise_evap_af_id:
                sheet.usbr_annuals(self.df_annual, self.usbr_rise_evap_af_id, self.start_year, self.end_year, month=all_b.WY,
                                   title=all_b.EVAPORATION, divisor=1)
            if self.usbr_rise_inflow_af_id:
                sheet.usbr_annuals(self.df_annual, self.usbr_rise_inflow_af_id, self.start_year, self.end_year, month=all_b.WY,
                                   title=all_b.INFLOW, divisor=1)
            if self.usbr_rise_inflow_unregulated_af_id:
                sheet.usbr_annuals(self.df_annual, self.usbr_rise_inflow_unregulated_af_id, self.start_year, self.end_year, month=all_b.WY,
                                   title=all_b.INFLOW_UNREGULATED, divisor=1)
        return self.df_annual

    def load_cdss_daily(self, wdid: str, start_year: int, end_year: int, water_class_num: str = '',
                   title: str = '',
                   month: int = 10, divisor: int = 1, analyze: bool = False):
        for year in range(start_year, end_year + 1):
            if month != 1:
                ts = pd.Timestamp(f'{year - 1}-{month}-01 00:00:00')
            else:
                ts = pd.Timestamp(f'{year}-{month}-01 00:00:00')
            water_year_info = WaterYearInfo.get_water_year(ts, month=month)
            daily = cdss.structures_divrec(None, wdid, water_year_info, water_class_num=water_class_num,
                                              analyze=analyze)
            df_utils.fill_df_from_structured_array(self.df_daily, daily, date_column_name='Date', value_column_name=title)
            pass

    def load_data_daily(self, start_year:Optional[int]=None, end_year:Optional[int]=None)->pd.DataFrame:
        water_year_info = self.water_year_info
        if self.df_daily is None or water_year_info.start_date != self.start_date or water_year_info.end_date != self.end_date:
            self.start_date = date(start_year-1, 10, 1)
            self.end_date = date(end_year, 9, 30)
            self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date,
                                                         [all_b.STORAGE, all_b.STORAGE_DELTA, all_b.ELEVATION,
                                                          all_b.RELEASE, all_b.EVAPORATION, all_b.INFLOW])
            if self.usbr_rise_storage_af_id:
                self.usbr_rise_load_daily(self.usbr_rise_storage_af_id, all_b.STORAGE, start_year=start_year, end_year=end_year)
                df_utils.compute_delta(self.df_daily, all_b.STORAGE, all_b.STORAGE_DELTA)
            if self.usbr_rise_elevation_ft_id:
                self.usbr_rise_load_daily(self.usbr_rise_elevation_ft_id, all_b.ELEVATION, start_year=start_year, end_year=end_year)
            if self.usbr_rise_release_af_id:
                self.usbr_rise_load_daily(self.usbr_rise_release_af_id, all_b.RELEASE, start_year=start_year, end_year=end_year)
            if  self.usbr_rise_evap_af_id:
                self.usbr_rise_load_daily(self.usbr_rise_evap_af_id, all_b.EVAPORATION, start_year=start_year, end_year=end_year)
            if self.usbr_rise_inflow_af_id:
                self.usbr_rise_load_daily(self.usbr_rise_inflow_af_id, all_b.INFLOW, start_year=start_year, end_year=end_year)
        return self.df_daily

    def load_data(self, report_path:Optional[Path], start_date:date, current_date:date, end_date:date):
        self.load_date(report_path, start_date, current_date, end_date)
        if self.usbr_rise_storage_af_id:
            self.active_capacity_af, daily_storage_af = self.get_storage(self.usbr_rise_storage_af_id,  self.name+'.'+all_b.STORAGE)
        if self.usbr_rise_elevation_ft_id:
            self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, all_b.ELEVATION)
        if self.usbr_rise_release_cfs_id:
             self.release_cfs = self.get_daily_and_last(self.usbr_rise_release_cfs_id, self.name+'.'+all_b.RELEASE)
        # if self.usbr_rise_inflow_cfs_id:
        #      self.release_cfs = self.get_daily_and_last(self.usbr_rise_inflow_cfs_id, all_b.INFLOW)
        if self.usbr_rise_evap_af_id:
             self.evap_af = self.get_daily_and_last(self.usbr_rise_evap_af_id, all_b.EVAPORATION)

    def get_projection(self, df_monthly:pd.DataFrame, column_name:str, monthly_column_name:str ='End Of Month Storage'):
        # initial_value = self.df_daily[ub.POWELL_WY].iloc[0]
        Reservoir.interpolate_monthly_storage_to_daily(df_monthly, self.df_daily,
                                                       monthly_value_col=monthly_column_name,
                                                       daily_target_col=column_name)
        df_utils.subtract_constant(self.df_daily, column_name, column_name, self.power_head_min_af)

    def get_projection_new(self,
                       df_monthly: pd.DataFrame,
                       column_name: str,  # <-- Required, no Powell default
                       monthly_column_name: str = 'End Of Month Storage',
                       subtract_min_af: float | None = None):  # Optional subtraction

        # === Ensure daily has DatetimeIndex ===
        daily_df = self.df_daily
        if not isinstance(daily_df.index, pd.DatetimeIndex):
            for possible_date_col in ['date', 'datetime', 'Date', 'Datetime']:
                if possible_date_col in daily_df.columns:
                    daily_df = daily_df.set_index(possible_date_col).copy()
                    break
            daily_df.index = pd.to_datetime(daily_df.index)
            daily_df = daily_df.sort_index()

        # === Prepare monthly data ===
        monthly = df_monthly[[monthly_column_name]].copy()

        if not isinstance(monthly.index, pd.DatetimeIndex):
            for possible_date_col in ['date', 'datetime', 'Date', 'Month', 'End of Month']:
                if possible_date_col in monthly.columns:
                    monthly = monthly.set_index(possible_date_col).copy()
                    break
            monthly.index = pd.to_datetime(monthly.index)
            monthly = monthly.sort_index()

        # === Interpolate to daily ===
        self.df_daily[column_name] = (
            monthly[monthly_column_name]
            .reindex(daily_df.index)
            .interpolate(method='time')
            .ffill()
            .bfill()
        )

        # === Optional subtraction (for Powell power head, etc.) ===
        if subtract_min_af is not None:
            df_utils.subtract_constant(
                self.df_daily,
                column_name,
                column_name,
                subtract_min_af
            )
        elif hasattr(self, 'power_head_min_af') and column_name.startswith('Powell'):
            # Only auto-subtract for Powell if you still want that behavior
            df_utils.subtract_constant(
                self.df_daily, column_name, column_name, self.power_head_min_af
            )

        print(f"✅ Projected {column_name} from monthly data")
    def copy(self):
        return copy.copy(self)

    def __str__(self)->str:
        string = f" '\'{self.name}\'"
        string += f" '\'{self.elevation_feet} ft\'"
        string += f" '\'{self.active_capacity_af} af\'"

        return string

    def usbr_rise_load_daily(self, usbr_rise_id:int, column_name:str, start_year:int=0, end_year:int=0):
        daily = 0
        if self.report_start_date is not None:
            start_year = self.report_start_date.year
        if self.report_end_date is not None:
            end_year = self.report_end_date.year
        if not end_year or end_year > date.today().year:
            end_year = date.today().year

        for year in range(start_year, end_year+1):
            self.water_year_info = self.get_water_year_info(year, month=self.water_year_month)
            info, daily = usbr_rise.load(usbr_rise_id, water_year_info=self.water_year_info, alias=column_name)
            df_utils.fill_df_from_structured_array(self.df_daily, daily, date_column_name='Date', value_column_name=column_name)
        return daily

    def usgs_load_daily(self, gage_id:str, column_name:str, start_year:int=0, end_year:int=0, parameterCd='00060', statCd='00003', month=1):
        daily = 0
        if self.report_start_date is not None:
            start_year = self.report_start_date.year
        if self.report_end_date is not None:
            end_year = self.report_end_date.year
        if not end_year or end_year > date.today().year:
            end_year = date.today().year

        for year in range(start_year, end_year+1):
            water_year_info = self.get_water_year_info(year, month=self.water_year_month)
            gage = USGSGage(gage_id, water_year_info)
            daily_cfs = gage.daily_discharge(water_year_info=water_year_info, alias=column_name, parameterCd=parameterCd,
                                             statCd=statCd)
            df_utils.fill_df_from_structured_array(self.df_daily, daily_cfs, date_column_name='Date', value_column_name=column_name)
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

    @staticmethod
    def get_value_at_time(arr: np.ndarray, target_dt) -> float | None:
        """
        Return the 'val' for the given datetime from a structured array
        with dtype [('dt', '<M8[s]'), ('val', '<f4')].

        Parameters:
            arr: structured ndarray (must be sorted by 'dt' for best performance)
            target_dt: datetime-like (np.datetime64, datetime object, or string)

        Returns:
            float value if exact match found, else None
        """
        if len(arr) == 0:
            return None

        # Convert target to np.datetime64[s] for consistency
        if isinstance(target_dt, str):
            target = np.datetime64(target_dt)
        elif isinstance(target_dt, datetime):
            target = np.datetime64(target_dt)
        else:
            target = np.asarray(target_dt).astype('M8[s]')

        # Extract the datetime field (view as 1D array)
        dts = arr['dt']

        # Binary search for insertion point (assumes array is sorted by 'dt')
        idx = np.searchsorted(dts, target)

        # Check for exact match
        if idx < len(dts) and dts[idx] == target:
            return float(arr['val'][idx])

        return None  # No exact match

    @staticmethod
    def months_earlier(dt, months: int = 1):
        """
        Return a date/time that is N months earlier than the input.

        Parameters:
            dt: datetime, np.datetime64, or string (e.g. '2026-04-15')
            months: number of months to go back (positive integer, default=1)

        Returns:
            Same type as input (datetime or np.datetime64)
        """
        if months <= 0:
            raise ValueError("months must be a positive integer")

        # Convert input to Python datetime for easy manipulation
        original_type = type(dt)
        if isinstance(dt, str):
            dt = np.datetime64(dt).astype(datetime)
        elif isinstance(dt, np.datetime64):
            dt = dt.astype(datetime)
        elif not isinstance(dt, datetime):
            raise TypeError(f"Unsupported type: {type(dt)}")

        # Simple and reliable method (handles year rollover)
        year = dt.year
        month = dt.month - months

        # Adjust year and month
        while month <= 0:
            month += 12
            year -= 1

        # Clamp day to valid range for the new month (e.g. Jan 31 → Feb 28/29)
        day = min(dt.day,
                  [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
                   31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])

        result = dt.replace(year=year, month=month, day=day)

        # Return in the original input type
        if original_type is np.datetime64 or isinstance(dt, np.datetime64):
            return np.datetime64(result)
        return result

    def print_storage(self, daily_storage_af):
        current_dt = daily_storage_af['dt'][-1]
        one_month_ago_dt = Reservoir.months_earlier(current_dt)
        self.storage_one_month_ago = Reservoir.get_value_at_time(daily_storage_af, one_month_ago_dt)
        one_month_delta = self.active_capacity_af - self.storage_one_month_ago

        two_months_ago_dt = Reservoir.months_earlier(current_dt, months=2)
        self.storage_two_months_ago = Reservoir.get_value_at_time(daily_storage_af, two_months_ago_dt)
        two_month_delta = self.active_capacity_af - self.storage_two_months_ago

        three_months_ago_dt = Reservoir.months_earlier(current_dt, months=3)
        storage_three_months_ago = Reservoir.get_value_at_time(daily_storage_af, three_months_ago_dt)
        three_month_delta = self.active_capacity_af - storage_three_months_ago

        print(f'{self.name.ljust(16)} Storage {self.active_capacity_af/1_000_000:5.3f} MAF 1 mo {one_month_delta:9.0f}  2 mo {two_month_delta:9.0f} 3 mo {three_month_delta:9.0f}')

    def get_storage(self, usbr_rise_id: int, column_name:str, month=all_b.WY, divisor:int=1)->Tuple[float, np.ndarray]:
        active_capacity_af = 0
        daily_storage_af = None
        when = Reservoir.compare_to_today(self.current_date)
        if when == 'match':
            if usbr_rise_id:
                daily_storage_af = self.usbr_rise_load_daily(usbr_rise_id, column_name)
                # date_time = daily_storage_af['dt'][-1]
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

        return active_capacity_af, daily_storage_af

    def get_daily_and_last(self, usbr_rise_id: int, column_name:str, month=all_b.WY, divisor:int=1)->float:
        release = 0

        if usbr_rise_id:
            daily_release = self.usbr_rise_load_daily(usbr_rise_id, column_name)
            # date_time = daily_release['dt'][-1]
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
    def is_new_day(df:pd.DataFrame) -> bool:
        is_new_day = False

        if df is not None:
            mt_tz = pytz.timezone("US/Mountain")
            now_mt = datetime.now(mt_tz)
            date_time_str = df['Date'].iloc[-1]
            date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
            if date_time.year < now_mt.year or date_time.month < now_mt.month \
                    or date_time.day < now_mt.day:
                is_new_day = True
        else:
            is_new_day = True
        return is_new_day

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
        # mask = df['Date'].isin(monthly['month_label'])
        # filled = mask.sum()
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
                    print(f'fill_usbr_monthly_into_df failed: month-year not found -> {mon_year_str}')

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
        matching = df[df[date_column] == date_str]
        if matching.empty:
            print(f"Warning: '{target_month_year}' not found in column '{date_column}'")
            return None

        # Return the value (first match)
        value = matching[column_name].iloc[0]
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
        if df_monthly is None or df_monthly.empty:
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
            if path.exists():
                df_24_month, df_24_wy, units = Reservoir.read_usbr_24month_table(path)
                return df_24_month, df_24_wy
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

class ReservoirRegistry(Registry):
    def __init__(self, name: str = "reservoirs"):
        super().__init__(name)

    def get(self, name)-> Optional[Reservoir]:
        instance: Optional[Reservoir] = None
        reservoir_registry = self.registry[name]
        if reservoir_registry is not None:
            instance = reservoir_registry["instance"]
            if instance is None:
                constructor = reservoir_registry["constructor"]
                if constructor is not None:
                    instance = constructor(name)
                    reservoir_registry["instance"] = instance
        return instance

class SRPReservoir(Reservoir):
    def __init__(self, name: str, headers: List[str], catalog_id: int = 0, upstream: Optional[List[Reservoir]] = None,
                 month=10):
        super().__init__(name, headers)

    def load_data(self, report_path:Path, start_date: date, current_date: date, end_date: date):
        # self.load_date(report_path, start_date, current_date, end_date)

        # self.date_time, self.elevation_feet = self.get_elevation(self.usbr_rise_elevation_ft_id, ub.BLUE_MESA_ELEVATION_WY)
        if self.df_daily is not None:
            self.elevation_feet = self.df_daily.iloc[-1][all_b.ELEVATION]
            self.active_capacity_af = self.df_daily.iloc[-1][all_b.STORAGE]

    @staticmethod
    def receive_data(name: str, df: pd.DataFrame, dt: datetime, data: Dict):
        active_capacity_af = data.get('current_storage_af', 0)
        if active_capacity_af:
            df_utils.set_value_at_datetime(df, dt, all_b.STORAGE, active_capacity_af)
        elevation_feet = data.get('current_elevation_ft', 0)
        if elevation_feet:
            df_utils.set_value_at_datetime(df, dt, all_b.ELEVATION, elevation_feet)

        SRPReservoir.to_srp_csv(name, df)

    @staticmethod
    def to_srp_csv(name: str, df: pd.DataFrame):
        mt_tz = pytz.timezone("US/Mountain")
        dt = datetime.now(mt_tz)
        name_year = Registry.make_nodule_name(name) + '_' + str(dt.year)
        path = Path('data/SRP') / name_year
        path = path.with_suffix('.csv')
        DataSet.to_csv(path, df)

    @staticmethod
    def from_srp_csv(name: str, ) -> Optional[pd.DataFrame]:
        mt_tz = pytz.timezone("US/Mountain")
        dt = datetime.now(mt_tz)
        name_year = Registry.make_nodule_name(name) + '_' + str(dt.year)
        path = Path('data/SRP') / name_year
        path = path.with_suffix('.csv')
        if path.exists():
            df = pd.read_csv(
                path,
                dtype={'Year': 'object'},  # Read as string to avoid parsing error
                float_precision='high'
            )
            return df
        else:
            mt_tz = pytz.timezone("US/Mountain")
            dt = datetime.now(mt_tz)
            df: pd.DataFrame = df_utils.create_daily_df(dt, dt,
                                                        [all_b.STORAGE, all_b.ELEVATION, all_b.RELEASE,
                                                         all_b.EVAPORATION,
                                                         all_b.INFLOW])
            return df
