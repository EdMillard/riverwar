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
import colorado.lb as lb
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_mohave import LakeMohave
from reservoirs.lake_havasu import LakeHavasu
from reservoirs.senator_wash import SenatorWash
from reservoirs.brock import Brock
import source.usgs_gage as usgs

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class LowerColorado(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Lower Colorado'
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.end_date = date.today()
        self.start_date = self.end_date.replace(year=self.end_date.year - 10)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.maps:List[str] = [
        ]

        reservoirs = [
            LakeMead(),
            LakeMohave(),
            LakeHavasu(),
            SenatorWash(),
            Brock()
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name=self.name)
        self.right_axis_annotations()

    def right_axis_annotations(self):
         pass

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        # https://waterdata.usgs.gov/monitoring-location/USGS-09424150

        usgs.daily_to_df(self.df_daily, '09426650', 'Central Arizona Project Canal at Havasu Pumping Plant', self.start_date, self.end_date, month=1)
        # Metropolitan Whitsett pumps from Lake Havasu
        # usgs.daily_to_df(self.df_daily, '09424150', 'Colorado River Aqueduct Near Parker Dam, AZ-CA', self.start_date, self.end_date, month=1) # Ends 2022
        usgs.daily_to_df(self.df_daily, '09428500', 'Crir Main Canal Near Parker, AZ', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '09429000', 'Palo Verde Canal Near Blythe, CA', self.start_date, self.end_date, month=1)

        usgs.daily_to_df(self.df_daily, '09523000', 'All-American Canal NR Imperial Dam, CA-AZ', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '09522500', 'Gila Gravity Main Canal at Imperial Dam, AZ-CA', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '09522000', 'Colorado River at Nib, Above Morelos Dam, AZ', self.start_date, self.end_date, month=1)

        # Drain 8-B Near Winterhaven, CA - USGS-09530500

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
                # if reservoir.name == 'Lake Mead':
                # time_series.append((reservoir.df_daily, lb.MEAD_ABOVE_1000, 'darkred'))
                if reservoir.name == 'Lake Mohave':
                    time_series.append((reservoir.df_daily, lb.MOHAVE, 'royalblue'))
                elif reservoir.name == 'Lake Havasu':
                    time_series.append((reservoir.df_daily, lb.HAVASU, 'darkgreen'))
        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'{self.name} - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='TAF',
            y_min=450_000
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Lake Mead':
                    time_series.append((reservoir.df_daily, lb.MEAD_RELEASE_CFS, 'darkred'))
                if reservoir.name == 'Lake Mohave':
                    time_series.append((reservoir.df_daily, lb.MOHAVE_RELEASE_CFS, 'royalblue'))
                elif reservoir.name == 'Lake Havasu':
                    time_series.append((reservoir.df_daily, lb.HAVASU_RELEASE_CFS, 'darkgreen'))
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = True,
            percentage=0.25,
            y_units='CFS',
            y_min=0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Central Arizona Project Canal at Havasu Pumping Plant', 'darkred'),
            # (self.df_daily, 'Colorado River Aqueduct Near Parker Dam, AZ-CA', 'royalblue'),
            (self.df_daily,'Crir Main Canal Near Parker, AZ', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'CRIR Main Canal Near Parker, AZ', 'darkred'),
            (self.df_daily, 'Palo Verde Canal Near Blythe, CA', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'All-American Canal NR Imperial Dam, CA-AZ', 'royalblue'),
            (self.df_daily, 'Gila Gravity Main Canal at Imperial Dam, AZ-CA', 'darkgreen'),
            (self.df_daily, 'Colorado River at Nib, Above Morelos Dam, AZ', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        # self.charts.append(self.line_chart)