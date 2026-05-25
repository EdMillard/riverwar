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
from reservoirs.blue_mesa import BlueMesa
from reservoirs.morrow_point import MorrowPoint
from reservoirs.taylor_park import TaylorPark
from reservoirs.ridgway import Ridgway
from reservoirs.paonia import Paonia

import source.usgs_gage as usgs

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class Uncompahgre(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.end_date = date.today()
        self.start_date = self.end_date.replace(year=self.end_date.year - 7)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.maps:List[str] = [
            'https://storymaps.arcgis.com/stories/f83f2faf88d24684bd69330277ee0529',
            'https://storymaps.arcgis.com/stories/7a04d822017944fa98bbedbe0874b3f6',
            'https://www.uncompahgrewatershed.org/wp-content/uploads/2022/01/Uncompahgre-Watershed-Plan-2022.pdf',
        ]

        reservoirs = [
            BlueMesa(),
            MorrowPoint(),
            TaylorPark(),
            Ridgway(),
            Paonia()
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name='Uncompahgre')
        self.right_axis_annotations()

    def right_axis_annotations(self):
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                pass

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        usgs.daily_to_df(self.df_daily, '09070500', 'Uncompahgre River at Colona, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09149500', 'Uncompahgre River at Delta, CO', self.start_date, self.end_date)
        # Uncompahgre at ridgway and ouray also
        usgs.daily_to_df(self.df_daily, '09127000', 'Cimarron River Blw Cimarron Creek at Cimarron, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09114500', 'Gunnison River Near Gunnison, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '383103106594200', 'Gunnison River at Cnty RD 32 Below Gunnison, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09128000', 'Gunnison River Below Gunnison Tunnel, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09144250', 'Gunnison River at Delta, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09152500', 'Gunnison River Near Grand Junction, CO', self.start_date, self.end_date)


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
                if reservoir.name == 'Blue Mesa':
                    time_series.append((reservoir.df_daily, ub.BLUE_MESA_WY, 'royalblue'))
                if reservoir.name == 'Morrow Point':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkgray'))
                    df_utils.copy_column(reservoir.df_daily, self.df_daily, reservoir.name+'.'+all_b.RELEASE)
                if reservoir.name == 'Taylor Park':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkred'))
                elif reservoir.name == 'Ridgway':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkgreen'))
                elif reservoir.name == 'Paonia':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'goldenrod'))

        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'Uncompahgre - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='TAF',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Uncompahgre River at Colona, CO', 'darkred'),
            (self.df_daily, 'Uncompahgre River at Delta, CO', 'red'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Gunnison River at Cnty RD 32 Below Gunnison, CO', 'dodgerblue'),
            (self.df_daily, 'Gunnison River Below Gunnison Tunnel, CO', 'royalblue'),
            (self.df_daily, 'Cimarron River Blw Cimarron Creek at Cimarron, CO', 'purple'),
            (self.df_daily, 'Morrow Point' + '.' + all_b.RELEASE, 'darkgray')
        ]
        df_utils.add_column_sum(self.df_daily,
                                [ 'Morrow Point'+'.'+all_b.RELEASE,
                                  'Cimarron River Blw Cimarron Creek at Cimarron, CO'],
                                'Gunnison above Tunnel')
        df_utils.subtract_column(self.df_daily, 'Gunnison above Tunnel',
                                 'Gunnison River Below Gunnison Tunnel, CO',
                                 "Gunnison Tunnel")
        df_utils.zero_out_column_seasonal(self.df_daily, "Gunnison Tunnel", start_date='10-31', end_date='03-10')
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            percentage=0.25,
            y_units='CFS',
            # y_max=700
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)

        time_series = [
            (self.df_daily,  "Gunnison Tunnel", 'dodgerblue'),
            # (self.df_daily, 'Gunnison River at Delta, CO', 'dodgerblue'),
            # (self.df_daily, 'Gunnison River Near Grand Junction, CO', 'purple'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.25,
            y_units='CFS',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)