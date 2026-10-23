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
# https://dwr.state.co.us/rest/get/help#Datasets&#SurfaceWaterController&#gettingstarted&#jsonxml

# https://dwr.state.co.us/Rest/GET/Help/Api/GET-api-v2-surfacewater-surfacewaterstations
# 'api/v2/surfacewater/surfacewaterstations'

# https://dwr.state.co.us/Rest/GET/Help/Api/GET-api-v2-surfacewater-surfacewaterstationdatatypes
# 'api/v2/surfacewater/surfacewaterstationdatatypes'

# https://dwr.state.co.us/Rest/GET/Help/Api/GET-api-v2-surfacewater-surfacewatertsday
# 'api/v2/surfacewater/surfacewatertsday'

# https://dwr.state.co.us/Rest/GET/Help/Api/GET-api-v2-surfacewater-surfacewatertsmonth
# 'api/v2/surfacewater/surfacewatertsmonth'

# https://dwr.state.co.us/Rest/GET/Help/Api/GET-api-v2-surfacewater-surfacewatertswateryear
# 'api/v2/surfacewater/surfacewatertswateryear'
import copy
import json
from api import df_utils
import pandas as pd
import requests
from pathlib import Path
import numpy as np
from source.water_year_info import WaterYearInfo
from datetime import date
from source.hydrologic_cache import WaterYearCache

def structure_info(wdid):
    json_info = None
    # api_key = None  # Replace with your CDSS API key (optional for limited queries)
    base_url = "https://dwr.state.co.us/Rest/GET/api/v2/structures/"
    url = f"{base_url}?wdid={wdid}"
    try:
        print(f'CDSS structure info:  {url}')
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        json_data = response.json()
        if json_data["ResultList"]:
            json_info = json_data["ResultList"][-1]
    except requests.exceptions.RequestException as e:
        print(f"Error querying struction info {wdid} info: {e}")
    return json_info

def water_class_info(wdid, water_class_num:str=''):
    json_info = None
    # api_key = None  # Replace with your CDSS API key (optional for limited queries)
    base_url = "https://dwr.state.co.us/Rest/GET/api/v2/structures/divrec/waterclasses"
    url = f"{base_url}?wdid={wdid}"
    if water_class_num:
        url += f'&waterClassNum={water_class_num}'
    try:
        print(f'CDSS water class info:  {url}')
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        json_data = response.json()
        if json_data["ResultList"]:
            json_info = json_data["ResultList"][-1]
    except requests.exceptions.RequestException as e:
        print(f"Error querying water class info {wdid} info: {e}")
    return json_info


# https://dwr.state.co.us/Rest/GET/Help
def telemetry_station_info(wdid):
    json_info = None
    # api_key = None  # Replace with your CDSS API key (optional for limited queries)
    base_url = "https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrystation/"
    url = f"{base_url}?wdid={wdid}"
    try:
        print(f'CDSS telemetry info:  {url}')
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        json_data = response.json()
        if json_data["ResultList"]:
            json_info = json_data["ResultList"][-1]
    except requests.exceptions.RequestException as e:
        print(f"Error querying telemetry station info {wdid} info: {e}")
    return json_info


def cache_file_name(name:str, meas_type:str='', water_class_num='', water_year_string:str='', file_prefix=''):
    data_path = Path('data/cdss')
    data_path.mkdir(parents=True, exist_ok=True)
    if file_prefix:
        name = file_prefix + '_' + name
    if meas_type:
        name = name + '_' + meas_type
    if water_class_num:
        name = name + '_' + water_class_num
    file_name = data_path.joinpath(name + water_year_string + '.json')
    return file_name


def write_json(file_path:Path, response:requests.Response):
    data = response.json()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)


def load_json(file_path, value_name='value', date_name='measDate',
              water_class_num='', analyze=False):
    f = file_path.open(mode='r')
    data = json.load(f)
    if analyze:
        analyze_water_class(data)
    return data_from_json(data, value_name=value_name, date_name=date_name, water_class_num=water_class_num)

def print_last_value(abbrev, a, alias=''):
    if a is not None and len(a['dt']) and len(a['val']):
        last_date = a['dt'][-1]
        last_val = a['val'][-1]
        print(f'\tCDSS - {abbrev} {last_date} {last_val} {alias}')
    else:
        print(f'\tCDSS no data - {abbrev} {alias}')

class WaterClass:
    def __init__(self, number:str, identifier:str,  start_date:str):
        self.number:str = number
        self.identifier:str = identifier
        self.start_date:str = start_date
        self.end_date:str = start_date
        self.num_samples = 1

    def copy(self):
        return copy.copy(self)

    def __str__(self):
        string = f'  {self.number:8d} {self.num_samples:4d} {self.start_date} {self.end_date}  \'{self.identifier}\''
        return string


def analyze_water_class(json_data, date_name:str='dataMeasDate'):
    measurements = json_data["ResultList"]
    if measurements:
        water_classes = {}
        for measurement in measurements:
                date = measurement.get(date_name)
                number = measurement.get('waterClassNum')
                identifier = measurement.get('wcIdentifier')
                if number is not None:
                    if number in water_classes:
                        water_class = water_classes[number]
                        if identifier == water_class.identifier:
                            if date > water_class.end_date:
                                water_class.end_date = date
                                water_class.num_samples += 1
                                # water_classes[number] = water_class
                            else:
                                pass
                        else:
                            pass
                    else:
                        water_classes[number] = WaterClass(number, identifier, date)
        for number, water_class in water_classes.items():
            print(water_class)
        pass

def data_from_json(json_data, value_name:str='value', date_name:str='measDate', water_class_num:str=''):
    measurements = json_data["ResultList"]
    if measurements:
        date_times = []
        values = []
        modifieds = []
        for measurement in measurements:
            if water_class_num:
                num = measurement.get('waterClassNum')
                if num is None or str(num) != water_class_num:
                    continue
            date_time = measurement.get(date_name)
            if date_time is not None:
                date_times.append(date_time)
            value = measurement.get(value_name)
            if value is not None:
                values.append(value)
            modified = measurement.get('modified')
            if modified is not None:
                modifieds.append(modified)
        if len(date_times) and len(values):
            dtype = [('dt', 'datetime64[D]'), ('val', float)]
            return np.array(list(zip(date_times, values)), dtype=dtype)
    return None

def get_water_year_info(year:int, month:int=10):
    if month == 1:
        start_date = date(year, month, 1)
    else:
        start_date = date(year-1, month, 1)
    water_year_info = WaterYearInfo.get_water_year(start_date, month=month)
    return water_year_info

def get_last_nonzero(df: pd.DataFrame, column: str):
    # Filter out NaN and zero values, then get the last one
    valid = df[column].replace(0, np.nan).dropna()

    if valid.empty:
        return None  # or np.nan, or raise an exception

    return valid.iloc[-1]

def limit_to_today(d: date) -> date:
    """Return the input date, but never later than today."""
    return min(d, date.today())

def telemetry_station_daily_to_df(df:pd.DataFrame, abbrev:str, name:str, measurement:str, start_date:date, end_date:date, month:int=10)->None:
    end_date = limit_to_today(end_date)
    if month > 1:
        if end_date.month >= month:
            end_date = end_date.replace(year=end_date.year + 1) # Need to add a year if in first months of water year
    for year in range(start_date.year, end_date.year + 1):
        water_year_info = get_water_year_info(year, month=month)
        time_series = telemetry_station_time_series(None, abbrev, measurement, water_year_info=water_year_info, alias=name)
        if time_series is not None:
            df_utils.fill_df_from_structured_array(df, time_series, date_column_name='Date', value_column_name=name)

def telemetry_station_time_series(logger, abbrev, parameter, water_year_info=None, update=False, alias='',
                                  start_date=None, end_date=None):
    if water_year_info is not None:
        start_date = str(water_year_info.start_date)
        end_date = str(water_year_info.end_date)

    cache = WaterYearCache.for_cdss()

    def fetch_fn(path: Path) -> None:
        base_url = "https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrytimeseriesday/"
        url = f"{base_url}?abbrev={abbrev}"
        if parameter:
            url += f"&parameter={parameter}"
        if start_date:
            url += f'&startDate={start_date}'
        if end_date:
            url += f'&endDate={end_date}'
        fields = ['measDate', 'measValue', 'modified']
        url += '&fields=' + ','.join(fields)
        try:
            print(f'CDSS telemetry:  {url}')
            response = requests.get(url)
            response.raise_for_status()
            if response.json().get("ResultList"):
                write_json(path, response)
        except requests.exceptions.RequestException as e:
            msg = f"Error querying CDSS telemetry station {abbrev} info: {e}"
            if logger is not None:
                logger.log_message(msg)
            else:
                print(msg)

    def parse_fn(path: Path):
        return load_json(path, value_name='measValue')

    time_series = cache.load_or_fetch(
        key=abbrev,
        water_year_info=water_year_info,
        fetch_fn=fetch_fn,
        parse_fn=parse_fn,
        suffix=parameter or "",
        extension='.json',
        force=update,               # only True when caller explicitly requests
        move_on_update=True,
        diff_on_update=True,
    )

    print_last_value(abbrev, time_series, alias=alias)
    return time_series

def request_surface_waters_day(logger, abbrev, file_name, start_date=None, end_date=None, meas_type=None, alias=None):
    time_series = None

    # api_key = None  # Replace with your CDSS API key (optional for limited queries)
    base_url = "https://dwr.state.co.us/Rest/GET/api/v2/surfacewater/surfacewatertsday/"
    url = f"{base_url}?abbrev={abbrev}"
    if meas_type:
        url += f'&measType={meas_type}'
    if start_date:
        url += f'&min-measDate={start_date}'
    if end_date:
        url += f'&max-measDate={end_date}'

    fields = ['measDate', 'value', 'modified']
    url += f'&fields='
    for field in fields:
        url += f'{field},'
    url = url[:-1]
    try:
        print(f'CDSS surface:  {url}')
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        json_data = response.json()
        if json_data["ResultList"]:
            write_json(file_name, response)
            measurements = json_data["ResultList"]
            if measurements:
                time_series = data_from_json(json_data, value_name='value')
                print_last_value(abbrev, time_series, alias=alias)

                '''
                date_times = []
                values = []
                for measurement in measurements:
                    date_times.append(measurement['measDate'])
                    values.append(measurement['value'])
                dtype = [('dt', 'datetime64[D]'), ('val', float)]
                time_series = np.array(list(zip(date_times, values)), dtype=dtype)
                '''
    except requests.exceptions.RequestException as e:
        msg = f"Error querying CDSS surface water {abbrev}: {e}"
        logger.log_message(msg)

    return time_series


def surface_waters_day(logger, abbrev, water_year_info, meas_type=None, update=False, alias='', file_prefix=''):
    if water_year_info is not None:
        start_date = str(water_year_info.start_date)
        end_date = str(water_year_info.end_date)
    else:
        logger.log_message(f'CDSS surface water request has no info: {abbrev}')
        return None

    cache = WaterYearCache.for_cdss()

    def fetch_fn(path: Path) -> None:
        request_surface_waters_day(logger, abbrev, path, start_date=start_date, end_date=end_date,
                                    meas_type=meas_type, alias=alias)

    def parse_fn(path: Path):
        return load_json(path, value_name='value')

    key = f"{file_prefix}_{abbrev}" if file_prefix else abbrev
    suffix = meas_type or ""

    time_series = cache.load_or_fetch(
        key=key,
        water_year_info=water_year_info,
        fetch_fn=fetch_fn,
        parse_fn=parse_fn,
        suffix=suffix,
        extension='.json',
        force=update,
        move_on_update=True,
        diff_on_update=True,
    )

    print_last_value(abbrev, time_series, alias=alias)
    return time_series

# https://dwr.state.co.us/Rest/GET/api/v2/structures/divrec/stagevolume?wdid=3203602
def request_structures_divrec(logger, wdid, file_name:Path, start_date:str|None=None, end_date:str|None=None,
                              meas_type:str|None=None, water_class_num:str|None=None, alias=None, analyze=False):
    time_series = None

    # Historical diversion records is a very spartan API.  you get the whole record
    # and have to clip it yourself

    # api_key = None  # Replace with your CDSS API key (optional for limited queries)
    base_url = "https://dwr.state.co.us/Rest/GET/api/v2/structures/divrec/"
    if meas_type is not None:
        base_url += meas_type
    url = f'{base_url}?wdid={wdid}'

    # Generates 404 response
    if water_class_num:
        url += f'&waterClassNum={water_class_num}'
    if start_date:
        url += f'&min-dataMeasDate={start_date}'
    if end_date:
        url += f'&max-dataMeasDate={end_date}'

    if meas_type == 'divrecday':
        # fields = ['dataMeasDate', 'dataValue', 'measUnits', 'modified', 'approvalStatus', 'obsCode']
        # Cortez needs these for NON PROJ, PROJ and UTE
        # fields.extend(['waterClassNum', 'wcIdentifier'])
        fields = []
    elif meas_type == 'stagevolume':
        # fields = ['dataMeasDate', 'stage', 'volume', 'modified', 'approvalStatus']
        fields = []
    else:
        fields = []
        print(f'cdss request_structures_divrec unknown meas_type: {meas_type}')
    if fields:
        url += f'&fields='
        for field in fields:
            url += f'{field},'
        url = url[:-1]

    try:
        print(f'CDSS divrec:  {url}')
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        json_data = response.json()
        if json_data["ResultList"]:
            write_json(file_name, response)
            measurements = json_data["ResultList"]
            if measurements:
                if meas_type == 'divrecday':
                    if analyze:
                        analyze_water_class(json_data)
                    time_series = data_from_json(json_data, value_name='dataValue', date_name='dataMeasDate',
                                                 water_class_num=water_class_num)
                elif meas_type == 'stagevolume':
                    time_series = data_from_json(json_data, date_name='dataMeasDate', value_name='volume')
                # print_last_value(wdid, time_series, alias=alias)

    except requests.exceptions.RequestException as e:
        msg = f"Error querying CDSS diversion records {wdid}: {e}"
        if logger is not None:
            logger.log_message(msg)
        else:
            print(msg)
    return time_series


def structures_divrec(logger, wdid:str, water_year_info, meas_type:str='divrecday', water_class_num:str='',
                      update=False, file_prefix='', alias:str='', analyze=False):
    if analyze:
        print(f'CDSS {wdid} {alias} {water_year_info.year}')
    if water_year_info is not None:
        start_date = str(water_year_info.start_date)
        end_date = str(water_year_info.end_date)
    else:
        logger.log_message(f'CDSS structure divrec request has no info: {wdid}')
        return None

    cache = WaterYearCache.for_cdss()

    def fetch_fn(path: Path) -> None:
        request_structures_divrec(logger, wdid, path, start_date=start_date, end_date=end_date,
                                   meas_type=meas_type, water_class_num=water_class_num,
                                   alias=alias, analyze=analyze)

    def parse_fn(path: Path):
        value_name = 'volume' if meas_type == 'stagevolume' else 'dataValue'
        return load_json(path, value_name=value_name, date_name='dataMeasDate',
                         water_class_num=water_class_num, analyze=analyze)

    key = f"{file_prefix}_{wdid}" if file_prefix else wdid
    suffix_parts = [p for p in (meas_type, water_class_num) if p]
    suffix = '_'.join(suffix_parts)

    time_series = cache.load_or_fetch(
        key=key,
        water_year_info=water_year_info,
        fetch_fn=fetch_fn,
        parse_fn=parse_fn,
        suffix=suffix,
        extension='.json',
        force=update,
        move_on_update=True,
        diff_on_update=True,
    )

    return time_series

def daily_to_water_year(a, water_year_start_month=10):
    """
    Convert daily values to water year totals.

    Water Year N:
        - Starts on water_year_start_month 1 of year (N-1)
        - Ends on water_year_start_month 1 of year N
        - Labeled as year N (standard USGS convention)

    Example: Water Year 2014 = Oct 1 2013 – Sep 30 2014
    """
    if len(a) == 0:
        return np.zeros(0, dtype=[('dt', 'i4'), ('val', 'f8')])

    sorted_a = np.sort(a, order='dt')

    result = []
    current_wy = None
    total = 0.0
    cfs_to_af = 1.983459

    for o in sorted_a:
        dt_obj = pd.Timestamp(o['dt']).to_pydatetime()
        val = o['val']

        # === Calculate correct Water Year label ===
        if dt_obj.month >= water_year_start_month:
            wy_year = dt_obj.year + 1
        else:
            wy_year = dt_obj.year

        # New water year started
        if current_wy is None or wy_year != current_wy:
            if current_wy is not None and total > 0:
                result.append((current_wy, total * cfs_to_af))

            current_wy = wy_year
            total = 0.0

        if not np.isnan(val):
            total += val

    # Last water year
    if current_wy is not None and total > 0:
        result.append((current_wy, total * cfs_to_af))

    return np.array(result, dtype=[('dt', 'i4'), ('val', 'f8')])