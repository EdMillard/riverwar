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
from util import subtract_annual, reshape_annual_range
current_last_year = 2021


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
