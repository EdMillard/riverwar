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
from datetime import date
from typing import List, Optional
from api import df_utils
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import wx
from source.nrcs_snotel import get_snotel_data, get_snotel_stations, stations_in_county, stations_in_state, stations_with_name
import source.usgs_gage as usgs
import pandas as pd

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class Snotel(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Snotel'
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.end_date = date.today()
        self.start_date = self.end_date.replace(year=self.end_date.year - 15)
        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.df_black_mesa:Optional[pd.DataFrame] = None
        self.df_lizard_head:Optional[pd.DataFrame] = None
        self.df_el_diente:Optional[pd.DataFrame] = None
        self.df_scotch_creek:Optional[pd.DataFrame] = None
        self.df_sharkstooth:Optional[pd.DataFrame] = None
        self.df_lone_cone:Optional[pd.DataFrame] = None

        self.maps:List[str] = [
        ]

        self.crbfc:List[str] = [
        ]
        reservoirs = [
            # Mcphee(),
            # Groundhog(),
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=None, page_name='San Juan')
        self.right_axis_annotations()

    def right_axis_annotations(self):
        pass

    @staticmethod
    def load_snotel_station(stations:pd.DataFrame, name)->Optional[pd.DataFrame]:
        station_matches = stations_with_name(stations, name)
        for station in station_matches:
            station_id = station.get('station_id', '')
            state = station.get('state', '')
            file_name = name.replace(" ", "_")
            file_name += '.csv'
            df = get_snotel_data(station_id, state, file_name=file_name)
            return df
        print(f'load_snotel_station {name} not found')
        return None

    def load_data(self) -> Optional[date]:
        stations = get_snotel_stations("stations.csv")

        # stations_in_dolores = stations_in_county(stations, 'Dolores')
        # stations_in_montezuma = stations_in_county(stations, 'Montezuma')
        # stations_in_la_plata = stations_in_county(stations, 'La Plata')
        # stations_in_san_miguel= stations_in_county(stations, 'San Miguel')

        # stations_in_co = stations_in_state(stations, 'CO')

        self.df_black_mesa = Snotel.load_snotel_station(stations, 'Black Mesa')
        self.df_lizard_head = Snotel.load_snotel_station(stations, 'Lizard Head Pass')
        self.df_el_diente = Snotel.load_snotel_station(stations, 'El Diente Peak')
        self.df_scotch_creek = Snotel.load_snotel_station(stations, 'Scotch Creek')
        self.df_sharkstooth = Snotel.load_snotel_station(stations, 'Sharkstooth')
        self.df_lone_cone = Snotel.load_snotel_station(stations, 'Lone Cone')

        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        usgs.daily_to_df(self.df_daily, '09165000', 'Dolores River Below Rico, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09166950', 'Lost Canyon Creek Near Dolores, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09166500', 'Dolores River at Dolores, CO', self.start_date, self.end_date)

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

        time_series = [
            (self.df_black_mesa, 'air_temperature_average', 'darkgreen'),
            (self.df_black_mesa, 'air_temperature_minimum', 'royalblue'),
            (self.df_black_mesa, 'air_temperature_maximum', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='CFS',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_black_mesa, 'snow_depth', 'darkgreen'),
            (self.df_black_mesa, 'snow_water_equivalent', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = True,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_black_mesa, 'precipitation_accumulation', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = True,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)