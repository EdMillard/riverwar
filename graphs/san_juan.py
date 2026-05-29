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
from reservoirs.heron import Heron
from reservoirs.navajo import Navajo
from reservoirs.vallecito import Vallecito
from reservoirs.lake_nighthorse import LakeNighthorse
from reservoirs.lemon import Lemon
from reservoirs.jackson_gulch import JacksonGulch
import source.usgs_gage as usgs

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class SanJuan(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'San Juan'
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
            f'https://www.cbrfc.noaa.gov/wsup/graph/espgraph_hc.html?id=NVRN5&year={self.start_date.year}&qpf=0&db=&csv=1', # Navajo, Archuleta
            f'https://www.cbrfc.noaa.gov/wsup/graph/espgraph_hc.html?id=DRGC2&year{self.start_date.year}&qpf=0&db=&csv=1',  # Animas, Durango
            f'https://www.cbrfc.noaa.gov/wsup/graph/espgraph_hc.html?id=BFFU1&year={self.start_date.year}&qpf=0&db=&csv=1'  # San Juan,Bluff
       ]
        reservoirs = [
            Heron(),
            Navajo(),
            Vallecito(),
            LakeNighthorse(),
            Lemon(),
            JacksonGulch(),
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name='San Juan')
        self.right_axis_annotations()

    def right_axis_annotations(self):
        pass

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        usgs.daily_to_df(self.df_daily, '09346400', 'San Juan River Near Carracas, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09342500', 'San Juan River at Pagosa Springs, CO', self.start_date, self.end_date)
        # 09355500 — San Juan River Near Archuleta, NM (immediately below Navajo Dam; used for release monitoring)
        # 09365000 — San Juan River at Farmington, NM
        # 09368000 — San Juan River at Shiprock, NM
        usgs.daily_to_df(self.df_daily, '09379500', 'San Juan River Near Bluff, UT', self.start_date, self.end_date)

        # waterdata.usgs.gov/monitoring-location/09344400
        # usgs.daily_to_df(self.df_daily, '09344300', 'Navajo River Above Chromo, CO', self.start_date, self.end_date) # 1956-1970
        # usgs.daily_to_df(self.df_daily, '09344400', 'Below Oso Diversion Dam', self.start_date, self.end_date)  # 1971-1998
        # usgs.daily_to_df(self.df_daily, '09345500', 'Little Navajo River at Chromo, CO', self.start_date, self.end_date) # 1935-1952
        # usgs.daily_to_df(self.df_daily, '09346000', 'Navajo River at Edith, CO', self.start_date, self.end_date) # 1986-1996

        # Oso Diversion Dam (WDID 774635) — Major diversion for the San Juan-Chama Project (transmountain diversion to the Rio Grande Basin).
        # Little Oso Diversion Dam (WDID 774636) on the Little Navajo River.

        usgs.daily_to_df(self.df_daily, '09349800', 'Piedra River Near Pagosa Springs, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09349800', 'Piedra River Near Arboles, CO', self.start_date, self.end_date)

        usgs.daily_to_df(self.df_daily, '09352800', 'Los Pinos River Above Vallecito Reservoir nr Bayfield, CO', self.start_date, self.end_date)
        # usgs.daily_to_df(self.df_daily, '09353500', 'Los Pinos River Near Bayfield, CO', self.start_date, self.end_date) # 1927-1986
        usgs.daily_to_df(self.df_daily, '09353800', 'Los Pinos River Near Ignacio, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09354500', 'Los Pinos River at La Boca, CO', self.start_date, self.end_date)

        usgs.daily_to_df(self.df_daily, '09358000', 'Animas River at Silverton, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09361500', 'Animas River at Durango, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09364500', 'Animas River at Farmington, NM', self.start_date, self.end_date)
        # 09357500 Animas River at Howardsville, CO Upper basin, near Silverton Discharge, Gage Height
        # waterdata.usgs.gov/monitoring-location/09357500
        # 09359020 Animas River below Silverton, CO Just downstream of Silverton Discharge, Water Quality
        # waterdata.usgs.gov/monitoring-location/09359020
        # 09359500 Animas River at Tall Timber Resort (above Tacoma), CO Discharge
        # waterdata.usgs.gov/monitoring-location/09359500
        # 09362520 Animas River below Durango Pump Plant nr Durango, CO  Discharge, Precip
        # waterdata.usgs.gov/monitoring-location/09362520
        # 09363500 Animas River near Cedar Hill, NM Discharge
        # waterdata.usgs.gov/monitoring-location/09363500

        # usgs.daily_to_df(self.df_daily, '09362750', 'Florida River Above Lemon Reservoir', self.start_date, self.end_date) # 1955-1963
        # usgs.daily_to_df(self.df_daily, '09362900', 'Florida River Below Lemon Reservoir', self.start_date, self.end_date) # 1955-1963
        # usgs.daily_to_df(self.df_daily, '09363000', 'Florida River Near Durango', self.start_date, self.end_date) # 1910-1960
        # usgs.daily_to_df(self.df_daily, '09363200', 'Florida River at Bondad', self.start_date, self.end_date) # 1956-1983
        # Try CDSS

        # usgs.daily_to_df(self.df_daily, '09365500', 'La Plata River at Hesperus, CO', self.start_date, self.end_date) # 1917-2018
        # usgs.daily_to_df(self.df_daily, '09366500', 'La Plata River at Colorado-New Mexico State Line', self.start_date, self.end_date) # 1920-2018
        usgs.daily_to_df(self.df_daily, '09367000', 'La Plata River at La Plata, NM', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09367500', 'La Plata River Near Farmington, NM', self.start_date, self.end_date)

        # usgs.daily_to_df(self.df_daily, '09370000', 'Mancos River Near Mancos, CO', self.start_date, self.end_date) # 1931-1938
        # 09369000 — East Mancos River Near Mancos, CO
        # 09368500 — West Mancos River Near Mancos, CO
        # 09369500 — Middle Mancos River Near Mancos, CO
        # 372113108154001 — Mancos River Below East And West Forks (confluence)
        # 371613108213700 — Mancos River Above Canyon

        usgs.daily_to_df(self.df_daily, '09372000', 'McElmo Creek Near Colorado-Utah State Line', self.start_date, self.end_date)
        # usgs.daily_to_df(self.df_daily, '09372200', 'McElmo Creek Near Bluff, UT', self.start_date, self.end_date)  # Gage height only 2021-

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
                if reservoir.name == 'Navajo':
                    time_series.append((reservoir.df_daily, ub.NAVAJO_WY, 'royalblue'))
        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'{self.name} - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='TAF',
            y_min=800_000
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Heron':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'red'))
                if reservoir.name == 'Lake Nighthorse':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkred'))
                if reservoir.name == 'Vallecito':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkgray'))
                if reservoir.name == 'Lemon':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'goldenrod'))
                if reservoir.name == 'Jackson Gulch':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'purple'))

        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='TAF',
            y_min = 0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Heron':
                    time_series.append((reservoir.df_daily, ub.USBR_NM_SAN_JUAN_CHAMA_TUNNEL_CFS, 'red'))
                elif reservoir.name == 'Navajo':
                    time_series.append((reservoir.df_daily, 'Estimated CFS to Cutter', 'darkgreen'))
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0,
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)

        time_series = [
            (self.df_daily, 'San Juan River at Pagosa Springs, CO', 'darkred'),
            (self.df_daily, 'Piedra River Near Arboles, CO', 'red'),
            (self.df_daily, 'Los Pinos River at La Boca, CO', 'darkgreen'),
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

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Navajo':
                    time_series.append((reservoir.df_daily, 'Navajo.release_total_cfs', 'royalblue'))
        time_series.append((self.df_daily, 'Animas River at Durango, CO', 'darkgreen'))
        time_series.append((self.df_daily, 'La Plata River Near Farmington, NM', 'darkgray'))
        time_series.append((self.df_daily, "McElmo Creek Near Colorado-Utah State Line", 'dodgerblue'))
        time_series.append((self.df_daily, 'San Juan River Near Bluff, UT', 'darkred'))
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