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
import colorado.lb as lb
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

class Imperial(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Imperial'
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.end_date = date.today()
        self.start_date = self.end_date.replace(year=self.end_date.year - 27)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.maps:List[str] = [
            'https://fishing-app.gpsnauticalcharts.com/i-boating-fishing-web-app/fishing-marine-charts-navigation.html?title=Salton+Sea+boating+app#11.62/33.1460/-115.7303',
        ]

        reservoirs = [
            LakeMohave(),
            LakeHavasu(),
            SenatorWash(),
            Brock()
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name=self.name)
        self.right_axis_annotations()

    def right_axis_annotations(self):
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                pass

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        # usgs.daily_to_df(self.df_daily, '09522990', 'All-American Canal Headworks at Imperial Dam, CA-AZ', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '09523000', 'All-American Canal NR Imperial Dam, CA-AZ', self.start_date, self.end_date, month=1)
        # usgs.daily_to_df(self.df_daily, '09526500', 'All-American Canal Above Pilot Knob Wasteway, CA', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '09527500', 'All-American Canal Below Pilot Knob Wasteway, CA', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '09527700', 'All-American Canal Below Drop 2 Reservoir Outlet', self.start_date, self.end_date, gage_start_year=2012, month=1)

        usgs.daily_to_df(self.df_daily, '09527630', 'Brock Reservoir Inlet Near Calexico, CA', self.start_date, self.end_date, gage_start_year=2013, month=1)
        usgs.daily_to_df(self.df_daily, '09527660', 'Brock Reservoir Outlet Near Calexico, CA', self.start_date, self.end_date, gage_start_year=2013, month=1)
        # usgs.daily_to_df(self.df_daily, '09526900', 'Pilot Knob Powerplant Inlet Diversion From Aac, CA', self.start_date, self.end_date, month=1) # Gage height only

        # Drain 8-B Near Winterhaven, CA - USGS-09530500

        usgs.daily_to_df(self.df_daily, '09527590', 'Coachella Canal Above All-american Canal Diversion', self.start_date, self.end_date, gage_start_year=2003, month=1)
        usgs.daily_to_df(self.df_daily, '09527594', 'Coachella Canal Near Niland, CA', self.start_date, self.end_date, gage_start_year=2009, month=1)
        usgs.daily_to_df(self.df_daily, '09527597', 'Coachella Canal Near Desert Beach, CA', self.start_date, self.end_date, gage_start_year=2009, month=1)

        usgs.daily_to_df(self.df_daily, '10254730', 'Alamo R NR Niland CA', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '10254970', 'New R at International Boundary at Calexico CA', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '10255550', 'New R NR Westmorland CA', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '10259540', 'Whitewater R NR Mecca', self.start_date, self.end_date, month=1)
        usgs.daily_to_df(self.df_daily, '10254050', 'Salt C NR Mecca', self.start_date, self.end_date, month=1)

        # https://waterdata.usgs.gov/monitoring-location/USGS-10254005
        usgs.daily_to_df(self.df_daily, '10254005', 'Salton Sea NR Westmorland CA', self.start_date, self.end_date,
                         parameterCd='62614', statCd='00003', month=1)

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
                if reservoir.name == 'Lake Mohave':
                    time_series.append((reservoir.df_daily, lb.MOHAVE, 'royalblue'))
                elif reservoir.name == 'Lake Havasu':
                    time_series.append((reservoir.df_daily, lb.HAVASU, 'darkred'))
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

        time_series = [
            (self.df_daily, 'Salton Sea NR Westmorland CA', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = True,
            percentage=0.25,
            y_units='FT',
            y_max=-225,
            y_min=-245,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'All-American Canal NR Imperial Dam, CA-AZ', 'royalblue'),
            (self.df_daily, 'All-American Canal Below Pilot Knob Wasteway, CA', 'darkgreen'),
            (self.df_daily, 'All-American Canal Below Drop 2 Reservoir Outlet', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
           #  y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Coachella Canal Above All-american Canal Diversion', 'royalblue'),
            (self.df_daily, 'Coachella Canal Near Niland, CA', 'darkred'),
            (self.df_daily, 'Coachella Canal Near Desert Beach, CA', 'darkgreen'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
           #  y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'New R at International Boundary at Calexico CA', 'dodgerblue'),
            (self.df_daily, 'New R NR Westmorland CA', 'royalblue'),
            (self.df_daily, 'Alamo R NR Niland CA', 'darkgreen'),
            (self.df_daily, 'Whitewater R NR Mecca', 'purple'),
            (self.df_daily, 'Salt C NR Mecca', 'goldenrod'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
           #  y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Brock Reservoir Inlet Near Calexico, CA', 'royalblue'),
            (self.df_daily, 'Brock Reservoir Outlet Near Calexico, CA', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
           #  y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        # self.charts.append(self.line_chart)