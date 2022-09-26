import numpy as np
import datetime
from dateutil.relativedelta import relativedelta


def subtract_annual(minuend, subtrahend, start_year=0, end_year=0):
    difference = np.zeros(len(minuend), [('dt', 'i'), ('val', 'f')])
    difference['dt'] = minuend['dt']
    difference['val'] = minuend['val'] - subtrahend['val']
    if start_year and end_year:
        difference = reshape_annual_range(difference, start_year, end_year)
    return difference


def add_annual(augend, addend, start_year=0, end_year=0):
    summation = np.zeros(len(augend), [('dt', 'i'), ('val', 'f')])
    summation['dt'] = augend['dt']
    summation['val'] = augend['val'] + addend['val']
    if start_year and end_year:
        summation = reshape_annual_range(summation, start_year, end_year)
    return summation


def add3_annual(augend, addend, addend2, start_year=0, end_year=0):
    summation = np.zeros(len(augend), [('dt', 'i'), ('val', 'f')])
    summation['dt'] = augend['dt']
    summation['val'] = augend['val'] + addend['val']
    summation['val'] = summation['val'] + addend2['val']

    if start_year and end_year:
        summation = reshape_annual_range(summation, start_year, end_year)
    return summation


def running_average(annual_af, window):
    result = np.zeros(len(annual_af), [('dt', 'i'), ('val', 'f')])

    total = 0.0
    n = 0
    for x in annual_af:
        result[n]['dt'] = x['dt']
        if n >= window:
            total -= annual_af[n - window]['val']
            total += x['val']
            result[n]['val'] = total / window
        else:
            total += x['val']
            result[n]['val'] = total / (n+1)
        n += 1

    return result


def reshape_annual_range(a, year_min, year_max):
    years = year_max - year_min + 1
    b = np.zeros(years, [('dt', 'i'), ('val', 'f')])

    for year in range(year_min, year_max + 1):
        b[year - year_min][0] = year
        b[year - year_min][1] = 0

    for year_val in a:
        year = year_val[0]
        if year_min <= year <= year_max:
            b[year - year_min][1] = year_val[1]

    return b


def daily_to_calendar_year(a):
    dt = datetime.date(1, 1, 1)
    total = 0
    result = []
    for o in a:
        obj = o['dt'].astype(object)
        if dt.year != obj.year:
            if total > 0:
                result.append([dt, total])
                total = 0
            dt = datetime.date(obj.year, 12, 31)
        else:
            total += o['val']
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


def convert_cfs_to_af_per_day(cfs):
    day = 0
    af = np.zeros(len(cfs), [('dt', 'datetime64[s]'), ('val', 'f')])
    for l in cfs:
        af[day][0] = l['dt']
        af[day][1] = l[1] * 1.983459
        day += 1
    return af


def array_in_time_range(array, start_date, end_date):
    difference_in_years = relativedelta(end_date, start_date).years + 1
    a = np.zeros(difference_in_years, [('dt', 'i'), ('val', 'f')])

    x = array['dt']
    y = array['val']
    inp_index = 0
    out_index = 0
    for year in x:
        dt = datetime.datetime(year, 1, 1)
        if start_date <= dt <= end_date:
            a[out_index][0] = year
            a[out_index][1] = y[inp_index]
            out_index += 1
        inp_index += 1
    return a


def positive_values(a):
    b = np.zeros(len(a), 'f')

    idx = 0
    for val in a:
        if val > 0:
            b[idx] = val
        idx += 1

    return b
