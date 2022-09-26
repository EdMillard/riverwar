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
from source import usbr_rise


def test():
    lake_mead()
    lake_mead_ics_by_state()
    lake_mohave()
    lake_havasu()


def lake_mead_load_ics():
    results = usbr_report.load_ics_csv('usbr_lake_mead_ics.csv', sep='\t')
    return results


def lake_mead_ics_by_state():
    ics = lake_mead_load_ics()
    ics_az_total = ics['AZ Total']
    ics_ca_total = ics['CA Total']
    ics_nv_total = ics['NV Total']

    bar_data = [{'data': ics_nv_total, 'label': 'NV ICS', 'color': 'maroon'},
                {'data': ics_az_total, 'label': 'AZ ICS', 'color': 'firebrick'},
                {'data': ics_ca_total, 'label': 'CA ICS', 'color': 'lightcoral'}
                ]
    graph = WaterGraph()
    graph.bars_stacked(bar_data, title='Lower Basin ICS By State',
                       ylabel='maf', ymin=0, ymax=3000000, yinterval=100000,
                       xlabel='Calendar Year', xinterval=1, format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def lake_mead():
    usbr_lake_mead_release_total_af = 6122
    # usbr_lake_mead_elevation_ft = 6123
    usbr_lake_mead_storage_af = 6124
    # usbr_lake_mead_release_total_cfs = 6125
    graph = WaterGraph(nrows=2)
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_mead_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mead Elevation', color='firebrick',
    #            ylabel='ft', ymin=900, ymax=1230, yinterval=20,
    #            format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_mead_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Mead Storage (Hoover Dam)', color='firebrick',
               ymax=32000000, yinterval=2000000,
               ylabel='maf', format_func=WaterGraph.format_10maf)
    # usbr.lake_mead.ics_by_state(graph)

    info, daily_release_af = usbr_rise.load(usbr_lake_mead_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=1, title='Lake Mead Release (Hoover Dam)', color='firebrick',
               ymin=3000000, ymax=22500000, yinterval=1000000,
               xlabel='Water Year', xinterval=5,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def lake_mohave():
    usbr_lake_mohave_release_total_af = 6131
    # usbr_lake_mohave_water_temperature_degf = 6132
    # usbr_lake_mohave_elevation_ft = 6133
    usbr_lake_mohave_storage_af = 6134
    # usbr_lake_mohave_release_total_cfs = 6135

    graph = WaterGraph(nrows=2)
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_mohave_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Mohave Elevation', color='firebrick',
    #            ymin=620, ymax=647, yinterval=2,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)
    info, daily_storage_af = usbr_rise.load(usbr_lake_mohave_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Mohave Storage (Davis Dam)', color='firebrick',
               ymin=1000000, ymax=1900000, yinterval=100000,
               ylabel='maf', format_func=WaterGraph.format_maf)

    info, daily_release_af = usbr_rise.load(usbr_lake_mohave_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=1, title='Lake Mohave Release (Davis Dam)', color='firebrick',
               ymin=6500000, ymax=23000000, yinterval=1000000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf', format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()


def lake_havasu():
    usbr_lake_havasu_release_total_af = 6126
    # usbr_lake_havasu_water_temperature_degf = 6127
    # usbr_lake_havasu_elevation_ft = 6128
    usbr_lake_havasu_storage_af = 6129
    # usbr_lake_havasu_release_total_cfs = 6130

    graph = WaterGraph(nrows=2)
    # info, daily_elevation_ft = usbr_rise.load(usbr_lake_havasu_elevation_ft)
    # graph.plot(daily_elevation_ft, sub_plot=0, title='Lake Havasu Elevation', color='firebrick',
    #            ymin=440, ymax=451, yinterval=1,
    #            ylabel='ft', format_func=WaterGraph.format_elevation)

    info, daily_storage_af = usbr_rise.load(usbr_lake_havasu_storage_af)
    graph.plot(daily_storage_af, sub_plot=0, title='Lake Havasu Storage (Parker Dam)', color='firebrick',
               ymax=700000, yinterval=50000,
               ylabel='kaf', format_func=WaterGraph.format_kaf)

    info, daily_release_af = usbr_rise.load(usbr_lake_havasu_release_total_af)
    annual_release_af = WaterGraph.daily_to_water_year(daily_release_af)
    graph.bars(annual_release_af, sub_plot=1, title='Lake Havasu Release (Parker Dam)', color='firebrick',
               ymin=4000000, ymax=19200000, yinterval=1000000,
               xlabel='Water Year', xinterval=4,
               ylabel='maf',  format_func=WaterGraph.format_maf)
    graph.fig.waitforbuttonpress()
