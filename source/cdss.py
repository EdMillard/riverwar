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
import requests
from pathlib import Path
import numpy as np
from source.water_year_info import WaterYearInfo


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


def telemetry_station_time_series(logger, abbrev, parameter, water_year_info=None, update=False, alias='',
                                  start_date=None, end_date=None):
    time_series = None

    if water_year_info is not None:
        water_year_string = '_' + str(water_year_info.year)
        start_date = str(water_year_info.start_date)
        end_date = str(water_year_info.end_date)
        if water_year_info.is_current_water_year:
            update = True
    else:
        water_year_string = ''

    file_name = cache_file_name(abbrev, water_year_string=water_year_string)
    if file_name.exists() and not update:
        time_series = load_json(file_name, value_name='measValue')
        if water_year_info is not None and water_year_info.is_current_water_year:
            last_date = time_series[-1][0]
            update = WaterYearInfo.is_current_datetime_greater(last_date, hours_offset=48)
        print_last_value(abbrev, time_series, alias=alias)
        if not update:
            return time_series

    # api_key = None  # Replace with your CDSS API key (optional for limited queries)
    base_url = "https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrytimeseriesday/"
    url = f"{base_url}?abbrev={abbrev}&parameter={parameter}"
    if start_date:
        url += f'&startDate={start_date}'
    if end_date:
        url += f'&endDate={end_date}'

    fields = ['measDate', 'measValue', 'modified']
    url += f'&fields='
    for field in fields:
        url += f'{field},'
    url = url[:-1]

    #     'https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrytimeseriesday/?fields=measDate%2CmeasValue%2Cmodified&abbrev=GRORESCO&parameter=STORAGE&startDate=11%2F01%2F2024'
    try:
        print(f'CDSS telemetry:  {url}')
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        json_data = response.json()
        if json_data["ResultList"]:
            write_json(file_name, response)
            time_series = data_from_json(json_data, value_name='measValue')
            print_last_value(abbrev, time_series, alias=alias)
    except requests.exceptions.RequestException as e:
        msg = f"Error querying CDSS telemetry station {abbrev} info: {e}"
        logger.log_message(msg)
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
        water_year_string = '_' + str(water_year_info.year)
        start_date = str(water_year_info.start_date)
        end_date = str(water_year_info.end_date)
        # cdss_start_date = pd.Timestamp(start_datetime64).strftime('%m-%d-%Y')
        if water_year_info.is_current_water_year:
            update = True
    else:
        logger.log_message(f'CDSS surface water request has no info: {abbrev}')
        return None

    file_name = cache_file_name(abbrev, meas_type=meas_type, water_year_string=water_year_string, file_prefix=file_prefix)
    if file_name.exists() and not update:
        time_series = load_json(file_name, value_name='value')
        if water_year_info is not None and water_year_info.is_current_water_year:
            last_date = time_series[-1][0]
            update = WaterYearInfo.is_current_datetime_greater(last_date, hours_offset=48)
        print_last_value(abbrev, time_series, alias=alias)
        if not update:
            return time_series

    time_series = request_surface_waters_day(logger, abbrev, file_name, start_date=start_date, end_date=end_date,
                                             meas_type=meas_type, alias=alias)
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
    # if water_class_num:
    #    url += f'{base_url}&waterClassNum={water_class_num}'
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
        logger.log_message(msg)
    return time_series


def structures_divrec(logger, wdid:str, water_year_info, meas_type:str='divrecday', water_class_num:str='',
                      update=False, file_prefix='', alias:str='', analyze=False):
    print(f'CDSS {wdid} {alias}')
    if water_year_info is not None:
        water_year_string = '_' + str(water_year_info.year)
        start_date = str(water_year_info.start_date)
        end_date = str(water_year_info.end_date)
        # cdss_start_date = pd.Timestamp(start_datetime64).strftime('%m-%d-%Y')
        if water_year_info.is_current_water_year:
            update = True
    else:
        logger.log_message(f'CDSS structure divrec request has no info: {wdid}')
        return None

    file_name = cache_file_name(wdid, meas_type=meas_type, water_year_string=water_year_string, file_prefix=file_prefix)
    if file_name.exists() and not update:
        if meas_type == 'stagevolume':
            value_name='volume'
        elif meas_type == 'divrecday':
            value_name = 'dataValue'
        else:
            print(f'cdss structures_divrec unknown meas_type: {meas_type}')
            return None
        time_series = load_json(file_name, value_name=value_name, date_name='dataMeasDate',
                                water_class_num=water_class_num, analyze=analyze)
        if water_year_info is not None and water_year_info.is_current_water_year:
            last_date = time_series[-1][0]
            update = WaterYearInfo.is_current_datetime_greater(last_date, hours_offset=48)
        # print_last_value(wdid, time_series, alias=alias)
        if not update:
            return time_series

    time_series = request_structures_divrec(logger, wdid, file_name, start_date=start_date, end_date=end_date,
                                             meas_type=meas_type, water_class_num=water_class_num, alias=alias, analyze=analyze)
    return time_series