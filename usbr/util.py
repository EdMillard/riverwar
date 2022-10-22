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
from source import usbr_report
from graph.water import WaterGraph
from rw.util import subtract_annual, reshape_annual_range
current_last_year = 2021


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


def diversion_vs_consumptive(state_code, name, state_name,
                             ymin1=0, ymax1=1000000, yinterval1=100000, yformat1='maf',
                             ymin2=0, ymax2=1000000, yinterval2=100000, yformat2='kaf'):
    start_year = 1964
    year_interval = 4

    graph = WaterGraph(nrows=2)

    # Diversion
    diversion_file_name = state_code + '/usbr_' + state_code + '_' + name + '_diversion.csv'
    annual_diversion_af = usbr_report.annual_af(diversion_file_name)

    cu_file_name = state_code + '/usbr_' + state_code + '_' + name + '_consumptive_use.csv'
    annual_cu_af = usbr_report.annual_af(cu_file_name)

    measured_file_name = state_code + '/usbr_' + state_code + '_' + name + '_measured_returns.csv'
    annual_measured_af = usbr_report.annual_af(measured_file_name)
    annual_measured_af = reshape_annual_range(annual_measured_af, start_year, current_last_year)

    unmeasured_file_name = state_code + '/usbr_' + state_code + '_' + name + '_unmeasured_returns.csv'
    annual_unmeasured_af = usbr_report.annual_af(unmeasured_file_name)
    annual_unmeasured_af = reshape_annual_range(annual_unmeasured_af, start_year, current_last_year)

    annual_diversion_minus_cu = subtract_annual(annual_diversion_af, annual_cu_af)

    if yformat1 == 'maf':
        format_func = WaterGraph.format_maf
    elif yformat1 == 'kaf':
        format_func = WaterGraph.format_kaf
    else:
        format_func = WaterGraph.format_af
    graph.bars(annual_diversion_af, sub_plot=0, title=state_name+' Diversion & Consumptive Use (Annual)',
               ymin=ymin1, ymax=ymax1, yinterval=yinterval1, label='Diversion',
               xlabel='', xinterval=year_interval, color='darkmagenta',
               ylabel=yformat1, format_func=format_func)

    bar_data = [
                {'data': annual_cu_af, 'label': 'Consumptive Use', 'color': 'firebrick'},
                {'data': annual_measured_af, 'label': 'Measured Returns', 'color': 'darkorchid'},
                {'data': annual_unmeasured_af, 'label': 'Unmeasured Returns', 'color': 'mediumorchid'},
                ]
    graph.bars_stacked(bar_data, sub_plot=0, title=state_name+' Totals (Annual)',
                       ymin=ymin1, ymax=ymax1, yinterval=yinterval1,
                       xlabel='', xinterval=year_interval,
                       ylabel=yformat1, format_func=format_func)

    if yformat2 == 'maf':
        format_func = WaterGraph.format_maf
    elif yformat2 == 'kaf':
        format_func = WaterGraph.format_kaf
    else:
        format_func = WaterGraph.format_af
    graph.bars(annual_diversion_minus_cu, sub_plot=1, title='Diversion minus Consumptive Use (Annual)',
               ymin=ymin2, ymax=ymax2, yinterval=yinterval2,
               xlabel='', xinterval=year_interval, color='darkmagenta',
               ylabel=yformat1, format_func=format_func)

    graph.fig.waitforbuttonpress()
