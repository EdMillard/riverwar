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
from datetime import date
from typing import List, Optional
from source import cdss
from api import df_utils
import pandas as pd
from chart.chart import Chart
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import wx
import colorado.ub as ub
import colorado.allb as all_b
from reservoirs.green_mountain import GreenMountain
from reservoirs.lake_granby import LakeGranby
from reservoirs.dillon import Dillon
from reservoirs.wolford import Wolford
from reservoirs.williams_fork import WilliamsFork

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class GrandValley(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        # reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.end_date = date.today()
        self.start_date = self.end_date.replace(year=self.end_date.year - 5)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.maps:List[str] = [
        ]

        reservoirs = [
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name='Grand Valley')
        self.right_axis_annotations()


    def right_axis_annotations(self):
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                pass

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])
        # https://dwr.state.co.us/Tools/Stations/ADATUNCO?params=DISCHRG
        cdss.telemetry_station_daily_to_df(self.df_daily, ub.CDSS_CO_ADAMS_TUNNEL_ABBREV, ub.CDSS_CO_ADAMS_TUNNEL, 'DISCHRG', self.start_date, self.end_date)

        # return self.load_reservoirs()

    def load_charts(self):
        graph_end_date = date.today()
        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Lake Granby':
                    #time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkred'))
                    pass

        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'Grand Valley - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            y_units='TAF',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            # (self.df_daily, ub.CDSS_CO_ADAMS_TUNNEL, 'darkred'),
        ]
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            percentage=0.2,
            y_units='CFS',
            # y_max=700
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)