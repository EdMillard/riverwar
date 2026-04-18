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
import wx
import matplotlib
from datetime import date
import os
from typing import List
from reservoirs.reservoir import Reservoir
from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
from chart.chart_frame import ChartFrame
from chart.line_chart import LineChart
import colorado.lb as lb
import colorado.ub as ub

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

def find_directories_with_file(root_dir: str, filename: str) -> List[str]:
    """Return list of directories containing the given filename."""
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    matching_dirs = []
    for dir_path in root.rglob("*"):
        if dir_path.is_dir():
            if (dir_path / filename).is_file():
                matching_dirs.append(str(dir_path.resolve()))

    return sorted(set(matching_dirs))


# ==================== MAIN FRAME ====================

class ReservoirChartFrame(ChartFrame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):
        super().__init__(reservoir_list, date_time, report_list, title, page_name='Reservoirs')

    def load_charts(self):
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        reservoir_chart = ReservoirChart(
            self.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end
        )
        self.charts.append(reservoir_chart)

        inflow_chart = InflowOutflowChart(
            self.reservoirs, start_date=start, current_date=current, end_date=end
        )
        self.charts.append(inflow_chart)

class TimeSeriesChartFrame(ChartFrame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):
        super().__init__(reservoir_list, date_time, report_list, title, page_name='Reservoirs')

    def load_charts(self):
        time_series = []
        for reservoir in self.reservoirs:
            if reservoir.name == 'Lake Powell':
                time_series.append((reservoir.df_daily, ub.POWELL_MOST, '#a0a0ff'))
                time_series.append((reservoir.df_daily, ub.POWELL_ABOVE_3500, 'dodgerblue'))
            elif reservoir.name == 'Lake Mead':
                time_series.append((reservoir.df_daily, lb.MEAD_MOST, '#ffa0a0'))
                time_series.append((reservoir.df_daily, lb.MEAD_ABOVE_1000, 'darkred'))
            elif reservoir.name == 'Flaming Gorge':
                time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_MOST, '#50a050'))
                time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))
        line_chart = LineChart(
            time_series, title='MAR26 24 Month Reservoir Storage Above Critical Elevation',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date
        )
        self.charts.append(line_chart)

