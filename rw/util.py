import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from graph.water import WaterGraph

debug = False
current_last_year = 2021


def reach_index_for_name(reaches, name):
    n = 0
    for reach in reaches:
        if reach.name == name:
            return n
        n += 1
    return None


def reach_for_name(reaches, name):
    for reach in reaches:
        if reach.name == name:
            return reach
    return None


def state_total_vs_user_total_graph(state_abbreviation, data, y_formatter='maf'):
    year_interval = 3
    graph = WaterGraph(nrows=2)

    if y_formatter == 'maf':
        format_func = WaterGraph.format_maf
    elif y_formatter == 'kaf':
        format_func = WaterGraph.format_kaf
    else:
        format_func = WaterGraph.format_af

    state_total_diversion_af = data[0]['data']
    users_total_diversion_af = data[1]['data']
    bar_data = [
        {'data': state_total_diversion_af, 'label': 'State Total', 'color': 'red'},
        {'data': users_total_diversion_af, 'label': 'Users', 'color': 'darkmagenta'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0,
                       title=state_abbreviation+' State Total Diversion vs User Total',
                       ymin=data[0]['y_min'], ymax=data[0]['y_max'], yinterval=data[0]['y_interval'],
                       xlabel='', xinterval=year_interval,
                       ylabel=y_formatter, format_func=format_func, vertical=False)
    graph.running_average(state_total_diversion_af, 10, sub_plot=0)
    graph.running_average(users_total_diversion_af, 10, sub_plot=0)

    difference = subtract_annual(state_total_diversion_af, users_total_diversion_af)
    graph.bars(difference, sub_plot=1, title=state_abbreviation+' State Total Diversion minus User Total',
               color='red', ymin=data[2]['y_min'], ymax=data[2]['y_max'], yinterval=data[2]['y_interval'],
               xlabel='Calendar Year', xinterval=4,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()

    graph = WaterGraph(nrows=2)
    state_total_cu_af = data[3]['data']
    users_total_cu_af = data[4]['data']
    bar_data = [
        {'data': state_total_cu_af, 'label': 'State', 'color': 'red'},
        {'data': users_total_cu_af, 'label': 'Users', 'color': 'firebrick'},
    ]
    graph.bars_stacked(bar_data, sub_plot=0,
                       title=state_abbreviation+' State Total Consumptive Use vs Users Total Consumptive Use',
                       ymin=data[3]['y_min'], ymax=data[3]['y_max'], yinterval=data[3]['y_interval'],
                       xlabel='', xinterval=year_interval,
                       ylabel=y_formatter, format_func=format_func, vertical=False)
    graph.running_average(state_total_cu_af, 10, sub_plot=0)
    graph.running_average(users_total_cu_af, 10, sub_plot=0)

    difference = subtract_annual(state_total_cu_af, users_total_cu_af)
    graph.bars(difference, sub_plot=1, title=state_abbreviation+' State Total Consumptive Use minus User Total',
               color='red', ymin=data[5]['y_min'], ymax=data[5]['y_max'], yinterval=data[5]['y_interval'],
               xlabel='Calendar Year', xinterval=4,
               ylabel='kaf', format_func=WaterGraph.format_kaf)
    graph.date_and_wait()


def subtract_annual(minuend, subtrahend, start_year=0, end_year=0):
    subtrahend = reshape_annual_range_to(subtrahend, minuend)
    difference = np.zeros(len(minuend), [('dt', 'i'), ('val', 'f')])
    difference['dt'] = minuend['dt']
    difference['val'] = minuend['val'] - subtrahend['val']
    if start_year and end_year:
        difference = reshape_annual_range(difference, start_year, end_year)
    return difference


def subtract_vector_from_annual(minuend, subtrahend):
    difference = np.zeros(len(minuend), [('dt', 'i'), ('val', 'f')])
    if len(minuend) == len(subtrahend):
        difference['dt'] = minuend['dt']
        difference['val'] = minuend['val'] - subtrahend
    else:
        print('subtract_vector_from_annual failed, length mismatch')
    return difference


def flow_for_year(a, year):
    for target in a:
        if target['dt'] == year:
            return target['val']
    return 0


def multiply_annual(a, multiplier, start_year=0, end_year=0):
    result = np.zeros(len(a), [('dt', 'i'), ('val', 'f')])
    result['dt'] = a['dt']
    result['val'] = a['val'] * multiplier
    if start_year and end_year:
        result = reshape_annual_range(result, start_year, end_year)
    return result


def add_annuals(arrays):
    if len(arrays) > 1:
        result = add_annual(arrays[0], arrays[1])
        n = 2
        while n < len(arrays):
            result = add_annual(result, arrays[n])
            n += 1
        return result
    elif len(arrays):
        return arrays[0]
    else:
        print('add_annuals failed, no data')
        return []


def add_annual(augend, addend, start_year=0, end_year=0):
    addend = reshape_annual_range_to(addend, augend)
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


def annual_is_zero(a):
    if a is not None:
        for value in a:
            if value['val'] != 0:
                return False
    return True


def vector_is_zero(a):
    if a is not None:
        for value in a:
            if value != 0:
                return False
    return True


def replace_annual(a, b):
    for source in b:
        source_dt = source['dt']
        for target in a:
            if target['dt'] == source_dt:
                target['val'] = source['val']
                break


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


def annual_zeroed_for_years(year_min, year_max):
    years = year_max - year_min + 1
    a = np.zeros(years, [('dt', 'i'), ('val', 'f')])
    for year in range(year_min, year_max + 1):
        year_index = year - year_min
        a[year_index][0] = year
        a[year_index][1] = 0
    return a


def vector_zeroed_for_years(year_min, year_max):
    years = year_max - year_min + 1
    a = [0] * years
    return a


def annual_set_to_constant_for_years(year_min, year_max, constant):
    years = year_max - year_min + 1
    a = np.zeros(years, [('dt', 'i'), ('val', 'f')])
    for year in range(year_min, year_max + 1):
        year_index = year - year_min
        a[year_index][0] = year
        a[year_index][1] = constant
    return a


def avg_annual(a):
    total = 0
    if a is not None:
        for y in a:
            total += y[1]
    avg = total / len(a)
    return avg


def af_as_str(af, plus_minus=False):
    s = "{:,}".format(round(af))
    if plus_minus:
        if af > 0:
            s = '+' + s
        elif af < 0:
            s = '-' + s
    s = "{:>12}".format(s)
    return s


def number_as_str(number):
    s = "{:,}".format(round(number))
    s = "{:>12}".format(s)
    return s


def right_justified(in_str, width):
    format_str = '{:>' + str(width) + '}'
    s = format_str.format(in_str)
    return s


def left_justified(in_str, width):
    format_str = '{:<' + str(width) + '}'
    s = format_str.format(in_str)
    return s


def percent_as_str(percent):
    s = "{:5.1f}".format(percent*100)
    s += '%'
    return s


def annual_as_str(a, with_year=False):
    s = ''
    if a is not None:
        for y in a:
            if with_year:
                s1 = str(int(y[1])) + ' ' + "{:,}".format(int(y[1])) + ' '
            else:
                s1 = "{:,}".format(round(y[1]))
                s1 = "{:>12}".format(s1)
            s += s1
    return s


def vector_as_str(a):
    s = ''
    if a is not None:
        for y in a:
            s1 = "{:,}".format(int(y))
            s1 = "{:>12}".format(s1)
            s += s1
    return s


def generate_year_header(year_begin, year_end):
    s = ''
    for year in range(year_begin, year_end + 1):
        s += '    '
        s += str(year)
        s += '    '

    return s


def reshape_annual_range_to(a, to):
    if len(a) == 0:
        return annual_zeroed_for_years(to[0][0], to[-1][0])
    if a['dt'][0] == to['dt'][0] and a['dt'][-1] == to['dt'][-1]:
        return a
    else:
        return reshape_annual_range(a, to['dt'][0], to['dt'][-1])


def reshape_annual_range(a, year_min, year_max):
    b = annual_zeroed_for_years(year_min, year_max)
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
        elif debug:
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
