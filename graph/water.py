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
import math
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.dates import YearLocator


class WaterGraph(object):
    """
    Essential paramaters
  """

    def __init__(self, nrows=1, ncols=1, gage=''):
        default_font_size = 18
        self.gage = gage

        plt.rc('font', size=default_font_size)  # controls default text size
        # plt.rc('axes', titlesize=40)  # fontsize of the title
        # plt.rc('axes', labelsize=40)  # fontsize of the x and y labels
        plt.rc('xtick', labelsize=default_font_size)  # fontsize of x tick labels
        plt.rc('ytick', labelsize=default_font_size)  # fontsize of y tick labels
        # plt.rc('legend', fontsize=40)  # fontsize of the legend

        self.fig, self.ax = plt.subplots(nrows=nrows, ncols=ncols)  # sharex='col'
        self.fig.set_figwidth(30)
        self.fig.set_figheight(20)

        if nrows * ncols > 1:
            for ax in self.ax:
                ax.grid(True)
        else:
            self.ax.grid(True)

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

    def annotate_vertical_arrow(self, x, text, sub_plot=0, offset_percent=0.025, color='black'):
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax
        y_lim = ax.get_ylim()
        y_axis_range = y_lim[1] - y_lim[0]
        offset = y_axis_range * (offset_percent*0.01)
        ax.annotate(text, xy=(x, 0), xycoords='data', color=color,
                    xytext=(x, y_lim[1] - offset), textcoords='data', horizontalalignment='center',
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color=color))

    def annotate_horizontal_line(self, y, text, sub_plot=0, color='black'):
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax
        x_lim = ax.get_xlim()
        # x_axis_range = x_lim[1] - x_lim[0]
        # offset = x_axis_range * (offset_percent*0.01)
        ax.annotate(text, xy=(x_lim[0], y), xycoords='data', color=color,
                    xytext=(x_lim[1], y), textcoords='data', verticalalignment='center',
                    arrowprops=dict(arrowstyle="-", connectionstyle="arc3", color=color))

    def bars(self, a, sub_plot=0, title='', color='royalblue', label=None, running_average_years=10,
             ymin=0, ymax=0, yinterval=1,
             xlabel='', xmin=0, xmax=0, xinterval=1, bar_width=0.9,
             ylabel='', format_func=format_af):
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax

        ax.set_title(label=title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        if xmin == 0:
            xmin = a[0][0] - 1
        if xmax == 0:
            xmax = a[-1][0] + 1

        labels_x = np.arange(xmin, xmax, xinterval)
        ax.set_xticks(labels_x)
        ax.set_xlim([xmin, xmax])

        if ymax > 0 and yinterval > 0:
            labels_y = np.arange(ymin, ymax+yinterval, yinterval)
            ax.set_yticks(labels_y)
        ax.set_ylim([ymin, ymax])

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        x = a['dt']
        y = a['val']
        if label:
            ax.bar(x, y, width=bar_width, color=color, label=label)
        else:
            ax.bar(x, y, width=bar_width, color=color)

        if running_average_years > 0:
            self.running_average(a, running_average_years, sub_plot=sub_plot)

    def bars_two(self, a, b, sub_plot=0, label_a='', label_b='', title='', color_a='royalblue', color_b='limegreen',
                 ylabel='', ymin=0, ymax=0, yinterval=1,
                 xlabel='', xmin=0, xmax=0, xinterval=1, format_func=format_af):
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax

        ax.set_title(label=title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        if xmin == 0:
            xmin = a[0][0] - 1
        if xmax == 0:
            xmax = a[-1][0] + 1
        labels_x = np.arange(xmin, xmax, xinterval)
        ax.set_xticks(labels_x)
        ax.set_xlim([xmin, xmax])

        if ymax > 0 and yinterval > 0:
            label_y = np.arange(ymin, ymax+yinterval, yinterval)
            ax.set_yticks(label_y)
        ax.set_ylim([ymin, ymax])

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        x = a['dt']
        y = a['val']
        ax.bar(x-0.2, y, width=0.4, color=color_a, label=label_a)

        b_x = b['dt']
        b_y = b['val']
        ax.bar(b_x+0.2, b_y, width=0.4, color=color_b, label=label_b)
        ax.legend()

    def bars_stacked(self, bar_data, sub_plot=0, title='',
                     ylabel='', ymin=0, ymax=0, yinterval=1,
                     xlabel='', xmin=0, xmax=0, xinterval=1, format_func=format_af, vertical=True):
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax

        ax.set_title(label=title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        t_min = 10000
        t_max = 0
        for bar in bar_data:
            a = bar['data']
            bar_min = a[0][0] - 1
            bar_max = a[-1][0] + 1
            if bar_min <= t_min:
                t_min = bar_min
            if bar_max >= t_max:
                t_max = bar_max
            labels_x = np.arange(t_min, t_max, xinterval)
            ax.set_xticks(labels_x)
            if xmin != 0:
                x_min = xmin
            else:
                x_min = t_min
            if xmax != 0:
                x_max = xmax
            else:
                x_max = t_max

            ax.set_xlim([x_min, x_max])

        if ymax > 0 and yinterval > 0:
            label_y = np.arange(ymin, ymax+yinterval, yinterval)
            ax.set_yticks(label_y)
        ax.set_ylim([ymin, ymax])

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        first = True
        bottom = None
        for bar in bar_data:
            a = bar['data']
            color = bar['color']
            label = bar['label']
            x = a['dt']
            y = a['val']
            if vertical:
                if first:
                    ax.bar(x, y, width=0.9, color=color, label=label)
                    first = False
                    bottom = y
                else:
                    ax.bar(x, y, bottom=bottom, width=0.9, color=color, label=label)
                    bottom = bottom + positive_values(y)
            else:
                ax.bar(x, y, width=0.9, color=color, label=label)
        ax.legend()

    def plot(self, a, sub_plot=0, title='', color='royalblue',
             xlabel='', xmin=0, xmax=0, xinterval=5,
             ylabel='', ymin=0, ymax=0, yinterval=1, label=None,
             format_func=format_af):
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax
        if len(title) > 0:
            ax.set_title(label=title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        if xmin == 0:
            xmin = a[0][0] - 1
        if xmax == 0:
            xmax = a[-1][0] + 1
        if ymax == 0:
            ymax = float(math.ceil(a['val'].max()))
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])

        if ymin != ymax and yinterval > 0:
            label_y = np.arange(ymin, ymax+1, yinterval)
            ax.set_yticks(label_y)

        # graph.fig.gca().yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
        # graph.fig.gca().xaxis.set_major_locator(YearLocator(xinterval))

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_func))
        ax.xaxis.set_major_locator(YearLocator(xinterval))

        x = a['dt']
        y = a['val']
        ax.plot(x, y, linestyle='-', marker='None', color=color, label=label)
        if label:
            ax.legend()

    def plot_gage(self, gage):
        daily_discharge_cfs = gage.daily_discharge()

        self.plot(daily_discharge_cfs, title=gage.site_name, sub_plot=0, ylabel='CFS',
                  ymin=gage.cfs_min, ymax=gage.cfs_max, yinterval=gage.cfs_interval,
                  format_func=WaterGraph.format_discharge, color=gage.color)

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

        self.bars(annual_af, sub_plot=1, title=gage.site_name, color=gage.color,
                  ylabel=gage.annual_unit, ymin=gage.annual_min, ymax=gage.annual_max,
                  yinterval=gage.annual_interval, format_func=y_format,
                  xlabel='Water Year', xmin=start_year, xmax=end_year,
                  xinterval=gage.year_interval, running_average_years=10)

        self.fig.waitforbuttonpress()

    def running_average(self, annual_af, window, sub_plot=0, label=None):
        running_average = np.zeros(len(annual_af), [('dt', 'i'), ('val', 'f')])
        if len(self.fig.axes) > 1:
            ax = self.ax[sub_plot]
        else:
            ax = self.ax

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
        if label:
            ax.plot(x, y, linestyle='-', linewidth=3, marker='None', color='goldenrod', label=label)
            ax.legend()
        else:
            ax.plot(x, y, linestyle='-', linewidth=3, marker='None', color='goldenrod')
        return running_average

    @staticmethod
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

        a = np.zeros(len(result), [('dt', 'i'), ('val', 'f')])
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

        a = np.zeros(len(result), [('dt', 'i'), ('val', 'f')])
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
        af = np.zeros(len(cfs), [('dt', 'datetime64[s]'), ('val', 'f')])
        for l in cfs:
            af[day][0] = l['dt']
            af[day][1] = l[1] * 1.983459
            day += 1
        return af

    @staticmethod
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
