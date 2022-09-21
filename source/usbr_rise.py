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
import datetime
import json
import numpy as np
import requests
from pathlib import Path


class USBRRise(object):
    """
    Essential paramaters to load USBR Rise data
        https://data.usbr.gov/rise-api
        https://data.usbr.gov/time-series
    """

    def __init__(self):
        pass

def daily_to_water_year(a):
    water_year_month = 10
    dt = datetime.date(1, water_year_month, 1)
    total = 0
    result = []
    for o in a:
        obj = o['dt'].astype(object)
        if obj.month == 10 and obj.day == 1:
            if total > 0:
                result.append([dt, total])
                total = 0
            dt = datetime.date(obj.year+1, water_year_month, 1)
        elif dt.year == 1:
            if obj.month < water_year_month:
                dt = datetime.date(obj.year, water_year_month, 1)
            else:
                dt = datetime.date(obj.year+1, water_year_month, 1)

        if not np.isnan(o['val']):
            total += o['val']
        else:
            print('daily_to_water_year not a number:', o)

    if total > 0:
        result.append([dt, total])

    a = np.zeros(len(result), [('dt', 'i'), ('val', 'f')])
    day = 0
    for l in result:
        # a[day][0] = np.datetime64(l[0])
        a[day][0] = l[0].year
        a[day][1] = l[1]
        day += 1

    return a


def annual_af(item_id, start_date='', end_date='', csv=False):
    info, daily_inflow_af = load(item_id, start_date=start_date, end_date=end_date, csv=csv)
    return daily_to_water_year(daily_inflow_af)


def load(item_id, start_date='', end_date='', csv=False):
    item_id_str = str(item_id)
    data_path = Path('data/USBR_RISE')
    data_path.mkdir(parents=True, exist_ok=True)
    if csv:
        file_name = data_path.joinpath(item_id_str + '.csv')
    else:
        file_name = data_path.joinpath(item_id_str + '.json')
    if file_name.exists():
        return load_json(file_name)

    return request(item_id, file_name, start_date, end_date, csv)


def request(item_id, file_name, start_date='', end_date='', csv=False):
    item_id_str = str(item_id)
    url = 'https://data.usbr.gov/rise/api/result/download'
    url += '?itemId='
    url += item_id_str

    if csv:
        url += '&type=csv'
    else:
        url += '&type=json'

    if len(start_date) > 0:
        url += '&after='
        url += start_date

    url += '&before='
    if len(end_date) > 0:
        url += end_date
    else:
        now = datetime.date.today()
        url += str(now)

    # url += '&order=ASC'
    # url += '&referred_module=sw'
    # url += '&period='

    r = requests.get(url)
    if r.status_code == 200:
        try:
            f = file_name.open(mode='w')
            f.write(r.content.decode("utf-8"))
            f.close()

            if csv:
                # FIXME
                print("FIXME USBR RISE csv load")
            else:
                f = file_name.open(mode='w')
                f.write(r.content.decode("utf-8"))
                f.close()
                return load_json(file_name)
        except FileNotFoundError:
            print("usbr_rise request cache file open failed for item id: ", item_id_str)
    else:
        print('usbr_rise request failed with response: ', r.status_code, ' ', r.reason)


def load_catalog(catalog_path, unified_region_id, theme_id=0):
    if not catalog_path.exists():
        records = request_catalog(catalog_path, unified_region_id, theme_id)
        f = catalog_path.open(mode='w')
        json_str = json.dumps(records, indent=4)
        f.write(json_str)
        f.close()
    else:
        f = catalog_path.open(mode='r')
        records = json.load(f)
        f.close()

    return records


def request_catalog(catalog_path, unified_region_id, theme_id=0):
    records = {}
    page_no = 1
    num_items = 0
    total_items = 100
    while num_items < total_items:
        url = 'https://data.usbr.gov/rise/api/catalog-record'

        url += '?page='
        url += str(page_no)
        url += '&itemsPerPage=100'

        unified_region_id_str = str(unified_region_id)
        url += '&unifiedRegionId='
        url += unified_region_id_str

        if theme_id > 0:
            theme_id_str = str(theme_id)
            url += '&themeId='
            url += theme_id_str

        r = requests.get(url)
        if r.status_code == 200:
            try:
                # catalog_page_path = catalog_path.joinpath('page_' + str(page_no) + '.json')
                # f = catalog_page_path.open(mode='w')
                # f.write(r.content.decode("utf-8"))
                # f.close()
                # f = catalog_page_path.open(mode='r')

                dictionary = json.loads(r.content.decode("utf-8"))
                data = dictionary['data']
                if page_no == 1:
                    records = data
                else:
                    records.extend(data)

                meta = dictionary['meta']
                # print(meta)
                total_items = meta['totalItems']
                num_items += meta['itemsPerPage']
                current_page = meta['currentPage']
                page_no = current_page + 1
            except FileNotFoundError:
                print("usbr request catalog file open error: ", catalog_path)
            except KeyError:
                print("usbr request catalog key error: ", catalog_path)
        else:
            print('usbr request catalog failed with response: ', r.status_code, ' ', r.reason)
            break
    return records


def load_catalog_items(catalog_record, prefix=''):
    try:
        attributes = catalog_record['attributes']
        print(attributes['_id'], attributes['recordTitle'])
        relationships = catalog_record['relationships']
        catalog_items = relationships['catalogItems']
        for catalog_item in catalog_items['data']:
            catalog_item_id_str = catalog_item['id']
            request_catalog_item(catalog_item_id_str, prefix)
    except KeyError:
        print("usbr request catalog item key error: ")
        return {}


def request_catalog_item(catalog_item_id_str, prefix=''):
    catalog_item = {}
    url = 'https://data.usbr.gov'
    url += catalog_item_id_str

    r = requests.get(url)
    if r.status_code == 200:
        try:
            catalog_item = json.loads(r.content.decode("utf-8"))
            data = catalog_item['data']
            attributes = data['attributes']
            parameter_name = attributes['parameterName']
            parameter_name = parameter_name.replace('Lake/Reservoir ', '')
            parameter_name = parameter_name.replace(' - ', '_')
            parameter_name = parameter_name.replace(' ', '_')
            # parameter_name += '_' + attributes['parameterTimestep']
            parameter_name += '_' + attributes['parameterUnit']
            parameter_name = parameter_name.lower()
            parameter_name = prefix + '_' + parameter_name

            print('\t', parameter_name, '=', attributes['_id'])
            # attributes['temporalStartDate'], attributes['temporalEndDate'])
        except KeyError:
            print("usbr request catalog item key error: ", catalog_item_id_str)
    else:
        print('usbr request catalog item failed with response: ', r.status_code, ' ', r.reason)
    return catalog_item


def load_json(file_path):
    f = file_path.open(mode='r')
    data = json.load(f)
    info = {'Location': data['Location'],
            'Parameter Name': data['Parameter Name:'],
            'Timestep': data['Timestep'],
            'Units': data['Units']}

    try:
        location = data['Location']
        print('units:  {0}  timestep: {1}   {2:<50} {3}'.format(data['Units'], data['Timestep'],
                                                                data['Parameter Name:'], location['Name']))
    except KeyError:
        print("usbr_rise JSON invalid key", file_path)

    days = 0
    while 1:
        try:
            # noinspection PyUnusedLocal
            value = data[str(days)]
            days += 1
        except KeyError:
            break

    a = np.zeros(days, [('dt', 'datetime64[s]'), ('val', 'f')])
    for day in range(days):
        try:
            value = data[str(day)]
            # print(value)
            a[day][0] = value['dateTime']
            a[day][1] = value['result']
        except KeyError:
            break
        day += 1
    f.close()
    return info, a
