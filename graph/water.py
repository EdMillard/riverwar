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
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.dates import YearLocator


class WaterGraph(object):
    """
    Essential paramaters
  """

    def __init__(self, title, xlabel='', ylabel='', gage=''):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.gage = gage
        self.fig, self.ax = plt.subplots()
        self.fig.clear(True)
        self.fig.set_figwidth(30)
        self.fig.set_figheight(20)
        plt.rc('font', size=30)  # controls default text size
        # plt.rc('axes', titlesize=40)  # fontsize of the title
        # plt.rc('axes', labelsize=40)  # fontsize of the x and y labels
        plt.rc('xtick', labelsize=30)  # fontsize of t x tick labels
        plt.rc('ytick', labelsize=30)  # fontsize of the y tick labels
        # plt.rc('legend', fontsize=40)  # fontsize of the legend
        plt.grid(True)
        plt.title(self.title)
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)

    # noinspection PyUnusedLocal
    @staticmethod
    def format_10maf(value, pos=None):
        return '{0:3.0f}'.format(value/1000000)
        # return '{-"(value, 'af', significant_digits=6)

    # noinspection PyUnusedLocal
    @staticmethod
    def format_maf(value, pos=None):
        return '{0:4.1f}'.format(value/1000000)
        # return '{-"(value, 'af', significant_digits=6)

    # noinspection PyUnusedLocal
    @staticmethod
    def format_af(value, pos=None):
        return '{0:>10}'.format(value)

    # noinspection PyUnusedLocal
    @staticmethod
    def format_kaf(value, pos=None):
        return '{0:>5}'.format(value/1000)

    # noinspection PyUnusedLocal
    @staticmethod
    def format_elevation(value, pos=None):
        return '{0:>10}'.format(value)

    # noinspection PyUnusedLocal
    @staticmethod
    def format_discharge(value, pos=None):
        return '{0:>6}'.format(value)

    @staticmethod
    def bars(a, title='', color='royalblue',
             ylabel='', ymin=0, ymax=0, yinterval=1,
             xlabel='', xmin=0, xmax=0, xinterval=1, format_func=format_af):
        water_graph = WaterGraph(title=title, xlabel=xlabel, ylabel=ylabel)

        if xmin == 0:
            xmin = a[0][0] - 1
        if xmax == 0:
            xmax = a[-1][0] + 1
        labels_x = np.arange(xmin, xmax, xinterval)
        plt.xticks(labels_x)
        plt.xlim([xmin, xmax])

        if ymax > 0 and yinterval > 0:
            labels_y = np.arange(ymin, ymax+yinterval, yinterval)
            plt.yticks(labels_y)
        plt.ylim([ymin, ymax])

        water_graph.fig.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        x = a['dt']
        y = a['val']
        plt.bar(x, y, width=0.9, color=color)

        return water_graph

    @staticmethod
    def bars_two(a, b, label_a='', label_b='', title='', color_a='royalblue', color_b='limegreen',
                    ylabel='', ymin=0, ymax=0, yinterval=1,
                    xlabel='', xmin=0, xmax=0, xinterval=1, format_func=format_af):
        water_graph = WaterGraph(title=title, xlabel=xlabel, ylabel=ylabel)

        if xmin == 0:
            xmin = a[0][0] - 1
        if xmax == 0:
            xmax = a[-1][0] + 1
        labels_x = np.arange(xmin, xmax, xinterval)
        plt.xticks(labels_x)
        plt.xlim([xmin, xmax])

        if ymax > 0 and yinterval > 0:
            label_y = np.arange(ymin, ymax+yinterval, yinterval)
            plt.yticks(label_y)
        plt.ylim([ymin, ymax])

        water_graph.fig.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        x = a['dt']
        y = a['val']
        plt.bar(x-0.2, y, width=0.4, color=color_a, label=label_a)

        b_x = b['dt']
        b_y = b['val']
        plt.bar(b_x+0.2, b_y, width=0.4, color=color_b, label=label_b)

        water_graph.fig.show()
        water_graph.fig.waitforbuttonpress()

        return water_graph

    @staticmethod
    def plot(a, title='', color='royalblue',
             xlabel='', xmin=0, xmax=0, xinterval=5,
             ylabel='', ymin=0, ymax=0, yinterval=1,
             format_func=format_af):
        water_graph = WaterGraph(title=title, xlabel=xlabel, ylabel=ylabel)

        if xmin == 0:
            xmin = a[0][0] - 1
        if xmax == 0:
            xmax = a[-1][0] + 1
        plt.xlim([xmin, xmax])

        plt.ylim([ymin, ymax])

        if ymin != ymax and yinterval > 0:
            label_y = np.arange(ymin, ymax+1, yinterval)
            plt.yticks(label_y)

        water_graph.fig.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
        water_graph.fig.gca().xaxis.set_major_locator(YearLocator(xinterval))

        x = a['dt']
        y = a['val']
        plt.plot(x, y, linestyle='-', marker='None', color=color)

        return water_graph

    @staticmethod
    def plot_gage(gage):
        daily_discharge_cfs = gage.daily_discharge()

        water_graph_cfs = WaterGraph.plot(daily_discharge_cfs, gage.site_name, ylabel='CFS',
                                          ymin=gage.cfs_min, ymax=gage.cfs_max, yinterval=gage.cfs_interval,
                                          format_func=WaterGraph.format_discharge, color=gage.color)
        water_graph_cfs.fig.waitforbuttonpress()

        daily_discharge_af = WaterGraph.convert_cfs_to_af_per_day(daily_discharge_cfs)
        annual_af = WaterGraph.daily_to_water_year(daily_discharge_af)
        date_format = "%Y-%m-%d"
        start_year = datetime.datetime.strptime(gage.start_date, date_format).year
        end_year = datetime.datetime.strptime(gage.end_date, date_format).year

        if gage.annual_unit == 'af':
            y_format = WaterGraph.format_af
        elif gage.annual_unit == 'kaf':
            y_format = WaterGraph.format_kaf
        elif gage.annual_unit == 'maf':
            y_format = WaterGraph.format_maf
        else:
            y_format = WaterGraph.format_kaf

        water_graph_annual = WaterGraph.bars(annual_af, title=gage.site_name, color=gage.color,
                                             ylabel=gage.annual_unit, ymin=gage.annual_min, ymax=gage.annual_max,
                                             yinterval=gage.annual_interval, format_func=y_format,
                                             xlabel='Water Year', xmin=start_year, xmax=end_year,
                                             xinterval=gage.year_interval)

        running_average = WaterGraph.running_average(annual_af, 10)
        x = running_average['dt']
        y = running_average['val']
        plt.plot(x, y, linestyle='-', linewidth=3, marker='None',
                 color='goldenrod', label='10Y Running Average')
        # water_graph_annual.fig.legend()

        water_graph_annual.fig.show()
        water_graph_annual.fig.waitforbuttonpress()
        return water_graph_cfs, water_graph_annual

    @staticmethod
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

        a = np.empty(len(result), [('dt', 'i'), ('val', 'f')])
        day = 0
        for l in result:
            # a[day][0] = np.datetime64(l[0])
            a[day][0] = l[0].year
            a[day][1] = l[1]
            day += 1

        return a

    @staticmethod
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

        a = np.empty(len(result), [('dt', 'i'), ('val', 'f')])
        day = 0
        for l in result:
            # a[day][0] = np.datetime64(l[0])
            a[day][0] = l[0].year
            a[day][1] = l[1]
            day += 1

        return a

    @staticmethod
    def convert_cfs_to_af_per_day(cfs):
        day = 0
        af = np.empty(len(cfs), [('dt', 'datetime64[s]'), ('val', 'f')])
        for l in cfs:
            af[day][0] = l['dt']
            af[day][1] = l[1] * 1.983459
            day += 1
        return af

    @staticmethod
    def array_in_time_range(array, start_date, end_date):
        difference_in_years = relativedelta(end_date, start_date).years + 1
        a = np.empty(difference_in_years, [('dt', 'i'), ('val', 'f')])

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

    @staticmethod
    def running_average(annual_af, window):
        running_average = np.empty(len(annual_af), [('dt', 'i'), ('val', 'f')])

        total = 0.0
        n = 0
        for x in annual_af:
            running_average[n]['dt'] = x['dt']
            if n >= window:
                total -= annual_af[n - window]['val']
                total += x['val']
                running_average[n]['val'] = total / window
            else:
                total += x['val']
                running_average[n]['val'] = total / (n+1)
            n += 1

        x = running_average['dt']
        y = running_average['val']
        plt.plot(x, y, linestyle='-', linewidth=3, marker='None', color='goldenrod', label='10Y Running Average')
        plt.legend()
        return running_average
