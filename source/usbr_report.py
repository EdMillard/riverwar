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
import numpy as np
from pathlib import Path
import calendar


class USBRReport(object):
    """
    Essential paramaters to load and display USBR annual report data
    monthly data in calendar years instead of compact water year
  """

    def __init__(self):
        pass


def pre_process_csv(strings, sep):
    line = 0
    years = 0
    headers = []
    for s in strings:
        if not len(s):
            continue
        if s.startswith('#'):
            continue
        elif line == 0:
            headers = s.split(sep)
            pass
        elif len(s) > 0:
            years += 1
        line += 1

    return headers, years


def load_monthly_csv(file_name, sep=' '):
    date_time_format = "%Y-%m-%d"

    file_path = Path('data/USBR_Reports').joinpath(file_name)
    f = file_path.open(mode='r')
    content = f.read()
    strings = content.split('\n')
    headers, years = pre_process_csv(strings, sep)

    a = np.empty(years*12, [('dt', 'datetime64[s]'), ('val', 'f')])
    months = 0

    line = 0
    for s in strings:
        if not len(s):
            continue
        if s.startswith('#'):
            continue
        elif line == 0:
            pass
        else:
            fields = s.strip().split(sep)
            if len(fields) > 1:
                month = 1
                year = fields[0]
                total = int(fields[-1].replace(',', ''))
                sum_year = 0
                for m in fields[1:-1]:
                    monthly_flow = int(m.replace(',', ''))
                    last_day = calendar.monthrange(int(year), month)[1]
                    year_month_last_day = str(year) + '-' + str(month) + '-' + str(last_day)
                    date_time = datetime.datetime.strptime(year_month_last_day, date_time_format)
                    a[months][0] = date_time
                    a[months][1] = monthly_flow
                    sum_year += monthly_flow
                    month += 1
                    months += 1
                if sum_year != total:
                    print('data error in report expected = ', total, ' got = ', sum_year, fields)
            elif len(fields) == 1:
                year = fields[0]
                monthly_flow = 0
                for month in range(1, 13):
                    last_day = calendar.monthrange(int(year), month)[1]
                    year_month_last_day = str(year) + '-' + str(month) + '-' + str(last_day)
                    date_time = datetime.datetime.strptime(year_month_last_day, date_time_format)
                    a[months][0] = date_time
                    a[months][1] = monthly_flow
                    months += 1
            else:
                break
        line += 1

    f.close()
    return headers, a


def load_ics_csv(file_name, sep=' '):
    file_path = Path('data/USBR_Reports').joinpath(file_name)
    f = file_path.open(mode='r')
    content = f.read()
    strings = content.split('\n')
    headers, years = pre_process_csv(strings, sep)

    results = {}
    for field in headers:
        if field != 'Year':
            results[field] = np.empty(years, [('dt', 'i'), ('val', 'f')])

    line = 0
    year_index = 0
    for s in strings:
        if not len(s):
            continue
        if s.startswith('#'):
            continue
        elif line == 0:
            pass
        else:
            value_strings = s.strip().split(sep)
            if len(value_strings) > 1:
                year_string = value_strings[0]
                year = int(year_string)
                value_index = 1
                for header in headers[1:-1]:
                    a = results[header]
                    value_string = value_strings[value_index]
                    value_index += 1
                    value = float(value_string.replace(',', ''))
                    a[year_index][0] = year
                    a[year_index][1] = value
                year_index += 1
            else:
                break
        line += 1

    f.close()
    return results


def ___convert_to_datetime(d):
    return datetime.datetime.strptime(np.datetime_as_string(d, unit='s'), '%Y-%m-%dT%H:%M:%S')


def negative_values(a):
    year_min = a[0][0]
    year_max = a[-1][0]
    years = year_max - year_min + 1
    b = np.zeros(years, [('dt', 'i'), ('val', 'f')])

    for year in range(year_min, year_max+1):
        year_index = year-year_min
        b[year_index][0] = year
        if a[year_index][1] < 0:
            b[year_index][1] = a[year_index][1]

    return b


def negative_values_as_positive(a):
    year_min = a[0][0]
    year_max = a[-1][0]
    years = year_max - year_min + 1
    b = np.zeros(years, [('dt', 'i'), ('val', 'f')])

    for year in range(year_min, year_max+1):
        year_index = year-year_min
        b[year_index][0] = year
        if a[year_index][1] < 0:
            b[year_index][1] = -a[year_index][1]

    return b


def positive_values(a):
    year_min = a[0][0]
    year_max = a[-1][0]
    years = year_max - year_min + 1
    b = np.zeros(years, [('dt', 'i'), ('val', 'f')])

    for year in range(year_min, year_max+1):
        year_index = year-year_min
        b[year_index][0] = year
        if a[year_index][1] > 0:
            b[year_index][1] = a[year_index][1]

    return b


def monthly_to_water_year(a, water_year_month=10):
    dt = datetime.date(1, water_year_month, 1)
    total = 0
    result = []
    for o in a:
        obj = o['dt'].astype(object)
        if obj.month == water_year_month:
            if total > 0:
                result.append([dt, total])
                total = 0
            dt = datetime.date(obj.year+1, water_year_month, 1)
        elif dt.year == 1:
            if obj.month < water_year_month:
                dt = datetime.date(obj.year, water_year_month, 1)
            else:
                dt = datetime.date(obj.year+1, water_year_month, 1)

        total += o['val']

    if total > 0:
        result.append([dt, total])

    a = np.empty(len(result), [('dt', 'i'), ('val', 'f')])
    year = 0
    if water_year_month == 1:
        offset = 1
    else:
        offset = 0
    for l in result:
        # a[day][0] = np.datetime64(l[0])
        a[year][0] = l[0].year - offset
        a[year][1] = l[1]
        year += 1

    return a


def monthly_to_calendar_year(a):
    dt = datetime.date(1, 1, 1)
    total = 0
    result = []
    previous_year = 1
    wrote_year = 1
    current_year = 1
    for o in a:
        obj = o['dt'].astype(object)
        current_year = obj.year
        if previous_year == 1:
            previous_year = current_year
            dt = datetime.date(current_year, 12, 31)
        elif previous_year != current_year:
            result.append([dt, total])
            wrote_year = previous_year
            total = 0
            dt = datetime.date(current_year, 12, 31)
            previous_year = current_year
        total += o['val']

    if current_year != wrote_year:
        result.append([dt, total])

    a = np.empty(len(result), [('dt', 'i'), ('val', 'f')])
    year = 0

    for l in result:
        a[year][0] = l[0].year
        a[year][1] = l[1]
        year += 1

    return a