"""
Copyright (c) 2025 Ed Millard

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
from pathlib import Path
from datetime import datetime
import wx
import matplotlib
from datetime import date
import os
import api.df_utils as df_utils
from typing import List
from chart.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import colorado.lb as lb
import colorado.ub as ub
from reservoirs.reservoir import Reservoir
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class TimeSeriesChartFrame(ChartFrame):
    def __init__(self,
                 notebook_frame: NotebookFrame):
        reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')

        flaming_gorge = FlamingGorge()
        lake_powell = LakePowell(upstream=[flaming_gorge])
        lake_mead = LakeMead(upstream=[lake_powell])

        reservoirs = [
            flaming_gorge,
            lake_powell,
            lake_mead,
        ]
        super().__init__(notebook_frame, reservoirs=reservoirs, reports=reports,page_name='APR26 24-Month')

    def load_charts(self):
        powell_df = None
        fg_df = None
        start_mod_date = date(2026, 5, 1)
        end_powell_mod_date = date(2026, 9, 30)
        end_fg_mod_date = date(2027, 4, 1)
        time_series = []
        for reservoir in self.reservoirs:
            if reservoir.name == 'Lake Powell':
                #  Apply 1.5 MAF cut in release to Powell storage level
                powell_df = reservoir.df_daily
                df_utils.add_cumulative_daily_delta(powell_df, 'Cut Powell Release', start_mod_date, end_powell_mod_date, 1_480_000)
                # df_utils.add_cumulative_daily_delta(powell_df, 'Cut Powell Release', start_mod_date, end_powell_mod_date, 0)
                reservoir.df_daily[ub.POWELL_MOST] = reservoir.df_daily[ub.POWELL_MOST] + powell_df['Cut Powell Release']
                reservoir.df_daily[ub.POWELL_MOST] = reservoir.df_daily[ub.POWELL_MOST] + fg_df['Flaming Gorge DROA']

                time_series.append((reservoir.df_daily, ub.POWELL_MOST, '#a0a0ff'))
                time_series.append((reservoir.df_daily, ub.POWELL_ABOVE_3500, 'dodgerblue'))
                prev_path = previous_month_path(Path(reservoir.report_path))
                df_24_month_prev, df_24_wy_prev = prev = reservoir.load_24_month(prev_path, reservoir.name)
                reservoir.get_projection(df_24_month_prev, 'Powell Most MAR26')
                # time_series.append((reservoir.df_daily, 'Powell Most MAR26', '#6060ff'))
                df_utils.subtract_column(reservoir.df_daily, ub.POWELL_MOST, 'Powell Most MAR26', "Diff")
            elif reservoir.name == 'Lake Mead':
                reservoir.df_daily[lb.MEAD_MOST] = reservoir.df_daily[lb.MEAD_MOST] - powell_df['Cut Powell Release']

                time_series.append((reservoir.df_daily, lb.MEAD_MOST, '#ffa0a0'))
                time_series.append((reservoir.df_daily, lb.MEAD_ABOVE_1000, 'darkred'))
            elif reservoir.name == 'Flaming Gorge':
                fg_df = reservoir.df_daily
                df_utils.add_cumulative_daily_delta(fg_df, 'Flaming Gorge DROA', start_mod_date, end_fg_mod_date, 1_000_000)
                reservoir.df_daily[ub.FLAMING_GORGE_MOST] = reservoir.df_daily[ub.FLAMING_GORGE_MOST] - fg_df['Flaming Gorge DROA']
                time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_MOST, '#50a050'))
                time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))
        line_chart = LineChart(
            time_series, title='Reservoir Storage Above Critical Elevation',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date.month,
            show_x_labels = False
        )
        line_chart.set_end_date(date(2027, 5, 1))
        self.charts.append(line_chart)

        time_series = []
        for reservoir in self.reservoirs:
            if reservoir.name == 'Lake Powell':
                if reservoir.report_path is not None:
                    #time_series.append((reservoir.df_daily, 'Diff', 'maroon'))
                    pass
        time_series.append((powell_df, 'Cut Powell Release', 'gold'))
        time_series.append((fg_df, 'Flaming Gorge DROA', 'green'))

        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date
        )
        line_chart.set_end_date(date(2027, 5, 1))
        self.charts.append(line_chart)


def previous_month_path(path: Path) -> Path:
    """
    Takes a path like: /.../2026/APR26
    Returns:          /.../2026/MAR26

    Handles year rollover: JAN26 → DEC25
    """
    path_str = str(path)

    # Match the year and month code (e.g. 2026/APR26)
    import re
    match = re.search(r'/(\d{4})/([A-Z]{3}\d{2})$', path_str)
    if not match:
        raise ValueError(f"Could not find month-year pattern in path: {path}")

    year_str = match.group(1)
    month_code = match.group(2)  # e.g. APR26

    # Parse to datetime
    dt = datetime.strptime(month_code, '%b%y')
    dt = dt.replace(year=int(year_str))

    # Go to previous month
    if dt.month == 1:
        prev_dt = dt.replace(year=dt.year - 1, month=12, day=1)
    else:
        prev_dt = dt.replace(month=dt.month - 1, day=1)

    # Format back to APR26 style
    new_month_code = prev_dt.strftime('%b%y').upper()

    # Replace in the original path
    new_path_str = re.sub(r'/(\d{4})/[A-Z]{3}\d{2}$',
                          f'/{prev_dt.year}/{new_month_code}',
                          path_str)

    return Path(new_path_str)

