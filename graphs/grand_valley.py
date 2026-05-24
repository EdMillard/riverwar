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
import colorado.ub as ub
import source.usgs_gage as usgs

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
        self.start_date = self.end_date.replace(year=self.end_date.year - 7)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.maps:List[str] = [
            'https://www.grandvalleyirrigation.com/providers/',
            'https://www.grandvalleyirrigation.com/about/history/,'
            'https://thedrainagedistrict.org/gvdd-gis-map/',
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
        # Above Shoshone and Roaring Fork, Below Eagle River
        usgs.daily_to_df(self.df_daily, '09070500', 'Colorado River Near Dotsero, CO', self.start_date, self.end_date)
        # Below Shoshone and Roaring Fork
        usgs.daily_to_df(self.df_daily, '09085100', 'Colorado River Below Glenwood Springs, CO', self.start_date, self.end_date)
        # Below Cameo
        usgs.daily_to_df(self.df_daily, '09105000', 'Plateau Creek Near Cameo, CO', self.start_date, self.end_date)
        # Above Grand Valley and Plateau Creek
        usgs.daily_to_df(self.df_daily, '09095500', 'Colorado River Near Cameo, CO', self.start_date, self.end_date)

        # Upto Oct 1,2024
        usgs.daily_to_df(self.df_daily, '09106150', 'Colo River Below Grand Valley Div NR Palisade, CO', self.start_date, self.end_date)
        # After Oct 1 2024
        usgs.daily_to_df(self.df_daily, '09106485', 'Colo River Below Grand Valley Div NR Palisade, CO', self.start_date, self.end_date)
        df_utils.subtract_column(self.df_daily, 'Colorado River Near Cameo, CO', 'Colo River Below Grand Valley Div NR Palisade, CO', "Grand Valley Diversion")
        usgs.daily_to_df(self.df_daily, '09152500', 'Gunnison River Near Grand Junction, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09163492', 'Salt Creek Near Mouth Near Mack, Co', self.start_date, self.end_date)

        usgs.daily_to_df(self.df_daily, '09163500', 'Colorado River Near Colorado-Utah State Line', self.start_date, self.end_date)
        df_utils.subtract_column(self.df_daily, 'Colorado River Near Colorado-Utah State Line', 'Gunnison River Near Grand Junction, CO', "Grand Valley Depletion")
        df_utils.add_column_sum(self.df_daily,
                                ['Colorado River Near Cameo, CO',
                                 'Plateau Creek Near Cameo, CO',
                                 'Gunnison River Near Grand Junction, CO',
                                 'Salt Creek Near Mouth Near Mack, Co'], 'Inflow')

        df_utils.subtract_column(self.df_daily, "Inflow",  "Colorado River Near Colorado-Utah State Line", "Outflow")


        # return self.load_reservoirs()
        pass

    def load_charts(self):
        graph_end_date = date.today()
        '''
        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Lake Granby':
                    #time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkred'))
                    pass
        '''
        today = datetime.today().date()
        time_series = [
            (self.df_daily, 'Colorado River Near Cameo, CO', 'darkred'),
            (self.df_daily, 'Colo River Below Grand Valley Div NR Palisade, CO', 'darkgreen'),
            # (self.df_daily, 'Colorado R. Abv Gunnison R. at Grand Junction, CO', 'green'),
        ]

        self.line_chart = LineChart(
            time_series,
            title=f'Grand Valley - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.33,
            y_units='CFS',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_daily, 'Gunnison River Near Grand Junction, CO', 'royalblue'),
            (self.df_daily, 'Colorado River Near Colorado-Utah State Line', 'darkred'),
            (self.df_daily, 'Inflow', 'darkgreen'),
        ]
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            percentage=0.33,
            y_units='CFS',
            # y_max=700
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)
        
        time_series = [
            (self.df_daily, "Grand Valley Diversion", 'purple'),
            (self.df_daily, "Outflow", 'darkgray'),
        ]
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels=False,
            percentage=0.33,
            y_units='CFS',
            # y_max=700
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)

