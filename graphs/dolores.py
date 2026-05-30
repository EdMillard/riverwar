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
from datetime import datetime
from datetime import date
from typing import List, Optional
from api import df_utils
import pandas as pd
from chart.chart import Chart
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import wx
import colorado.allb as all_b
import colorado.ub as ub
from reservoirs.mcphee import Mcphee
from reservoirs.groundhog import Groundhog
import source.usgs_gage as usgs
import source.cdss as cdss

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class Dolores(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Dolores'
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.end_date = date.today()
        self.start_date = self.end_date.replace(year=self.end_date.year - 1)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.maps:List[str] = [
        ]

        self.crbfc:List[str] = [
        ]
        reservoirs = [
            Mcphee(),
            Groundhog(),
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name='San Juan')
        self.right_axis_annotations()

    def right_axis_annotations(self):
        pass

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        usgs.daily_to_df(self.df_daily, '09165000', 'Dolores River Below Rico, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09166950', 'Lost Canyon Creek Near Dolores, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09166500', 'Dolores River at Dolores, CO', self.start_date, self.end_date)
        # usgs.daily_to_df(self.df_daily, '09167500', 'Dolores River Near McPhee, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09172500', 'San Miguel River at Uravan, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09180000', 'Dolores River Near Cisco, UT', self.start_date, self.end_date)

        cdss.telemetry_station_daily_to_df(self.df_daily, 'DOLBMCCO', 'Dolores River Below Mcphee, CO', 'DISCHRG', self.start_date, self.end_date)

        self.load_reservoirs()

    def load_reservoirs(self) -> Optional[date]:
        date_time_as_date = None
        start = self.start_date
        current = self.end_date
        end = self.end_date

        for reservoir_list in self.reservoir_lists:
            for reservoir in reservoir_list:
                reservoir.load_data(None, start, current, end)
        return date_time_as_date

    def load_charts(self):
        graph_end_date = date.today()

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Mcphee':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'royalblue'))

        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'{self.name} - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='TAF',
            y_min=150_000
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Groundhog':
                    time_series.append((reservoir.df_daily,  reservoir.name+'.'+all_b.STORAGE, 'darkred'))
        self.line_chart = LineChart(
            time_series,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = True,
            percentage=0.20,
            y_units='TAF',
            y_min = 0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Dolores River Below Rico, CO', 'royalblue'),
            (self.df_daily, 'Dolores River at Dolores, CO', 'darkred'),
            (self.df_daily, 'Lost Canyon Creek Near Dolores, CO', 'darkgreen')
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [(self.df_daily, 'San Miguel River at Uravan, CO', 'royalblue'),
                       (self.df_daily, 'Dolores River Near Cisco, UT', 'darkred'),
                       (self.df_daily, 'Dolores River Below Mcphee, CO', 'darkgreen')
                       ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)