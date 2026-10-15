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
from typing import List, Optional, Tuple
from colorado.river_war import RiverWar
from api import df_utils
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
from et.openet import openet_json_file_to_dataframe
import wx
from source.nrcs_snotel import (get_snotel_data, get_snotel_stations, stations_in_county, stations_in_state,
                                stations_with_name, print_full_summary, get_sensor_history_years,
                                get_snotel_hourly_data, get_snotel_station_elements)
import source.usgs_gage as usgs
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

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
        self.smooth_days = 5

        self.snotel_name = 'Lizard Head Pass'
        self.snotel_name = 'El Diente'
        # self.snotel_name = 'Niwot'
        # self.snotel_name = 'Berthoud Summit'

        self.end_date = date.today()
        stations = get_snotel_stations("stations.csv")

        # stations_in_dolores = stations_in_county(stations, 'Dolores')
        # stations_in_montezuma = stations_in_county(stations, 'Montezuma')
        # stations_in_la_plata = stations_in_county(stations, 'La Plata')
        # stations_in_san_miguel= stations_in_county(stations, 'San Miguel')
        '''
            stations_in_co = stations_in_state(stations, 'CO')

            for station in stations_in_co:
                print(station)
                name = station.get('site_name_clean', '')
                station_id = station.get('station_id', '')
                state = station.get('state', '')
                df_summary = get_snotel_sensors_with_dates(station_id, state)
                print_full_summary(df_summary, title=f"{name} Sensor Summary:")
                if len(df_summary) > 9:
                    pass
        '''
        self.num_years = 1
        self.df_snotel, self.df_snotel_summary = self.load_snotel_station(stations, self.snotel_name)

        self.df_daily:Optional[pd.DataFrame] = None
        self.water_year_info = None

        self.df_open_et:Optional[pd.DataFrame] = None
        self.df_open_meteo:Optional[pd.DataFrame] = None

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


    def load_charts(self):
        graph_end_date = date.today()

        title = f'Dolores River - {self.snotel_name} SNOTEL'

        self.river_graph(graph_end_date, title=title)

        self.precipitation_swe_graph(graph_end_date, show_x_labels=True)

        # self.soil_moisture_graph(graph_end_date)

        # self.open_et_graph(graph_end_date)

        # self.precipitation_increment_graph(graph_end_date)

        # self.air_temperature_graph(graph_end_date, "air_temperature_maximum", "temperature_2m_max", title="")
        self.air_temperature_graph(graph_end_date, "air_temperature_average", "temperature_2m_mean", show_x_labels=True)
        # self.air_temperature_graph(graph_end_date, "air_temperature_minimum", "temperature_2m_min")

        # self.soil_temperature_graph(graph_end_date)

    def river_graph(self, graph_end_date, title:str=""):
        usgs.daily_to_df(self.df_daily, '09165000', 'Dolores River Below Rico, CO', self.start_date, self.end_date)
        usgs.daily_to_df(self.df_daily, '09166500', 'Dolores River at Dolores, CO', self.start_date, self.end_date)
        # usgs.daily_to_df(self.df_daily, '09166950', 'Lost Canyon Creek Near Dolores, CO', self.start_date, self.end_date)

        time_series = [
            (self.df_daily, 'Dolores River at Dolores, CO', 'darkred'),
            (self.df_daily, 'Dolores River Below Rico, CO', 'royalblue'),
            # (self.df_daily, 'Lost Canyon Creek Near Dolores, CO', 'darkgreen')
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    def open_et_graph(self, graph_end_date, show_x_labels:bool = False, title:str=""):
        time_series = [
            #(self.df_open_et, f'eeMETRIC_smooth_{self.smooth_days}d', 'royalblue'),
            (self.df_open_et, f'DisALEXI_smooth_{self.smooth_days}d', 'darkred'),
            # (self.df_open_et, f'DisALEXI', 'darkred'),
            # (self.df_open_et, f'ensemble_smooth_{self.smooth_days}d', 'darkgreen'),
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels=show_x_labels,
            percentage=0.20,
            y_units='in',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    @staticmethod
    def accumulate_precipitation(
            df: pd.DataFrame,
            precip_col: str = 'precipitation_sum',
            date_col: str = 'Date',
            reset_month: int = 10,
            reset_day: int = 1,
            output_col: str = 'precipitation_accumulation'
    ) -> pd.DataFrame:
        """
        Accumulate daily precipitation, resetting on a specific month/day each year.

        Default: Water year (resets on October 1)
        """
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)

        # Create water year / custom year identifier
        def get_custom_year(dt):
            if dt.month < reset_month or (dt.month == reset_month and dt.day < reset_day):
                return dt.year - 1
            return dt.year

        df['CustomYear'] = df[date_col].apply(get_custom_year)

        # Cumulative sum within each custom year
        df[output_col] = df.groupby('CustomYear')[precip_col].cumsum()

        # Optional: drop helper column
        # df = df.drop(columns=['CustomYear'])

        return df

    def precipitation_swe_graph(self, graph_end_date, show_x_labels:bool = False, title:str=""):
        self.df_open_meteo = Snotel.accumulate_precipitation(self.df_open_meteo)
        time_series = [
            # (self.df_snotel, 'snow_depth', 'darkgreen'),
            (self.df_open_meteo, 'precipitation_accumulation', 'darkred'),
            (self.df_snotel, 'precipitation_accumulation', 'royalblue'),
            (self.df_snotel, 'snow_water_equivalent', 'darkgreen'),
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = show_x_labels,
            percentage=0.20,
            y_units='in',
            y_min=0.0
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    def precipitation_increment_graph(self, graph_end_date, show_x_labels: bool = False, title: str = ""):
        time_series = [
            (self.df_open_meteo, 'precipitation_sum', 'darkgreen'),
            (self.df_snotel, 'precipitation_increment', 'goldenrod'),
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels=show_x_labels,
            percentage=0.20,
            y_units='in',
            # y_max=2
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    def air_temperature_graph(self, graph_end_date, snotel_name:str, open_meteo_name:str,  show_x_labels:bool = False, title:str=""):
        rolling_avg_days = 5
        self.df_snotel[f'{snotel_name}_{rolling_avg_days}d'] = (
            self.df_snotel[snotel_name]
            .rolling(window=rolling_avg_days, center=True, min_periods=3)
            .mean()
        )
        time_series = [
            (self.df_open_meteo, open_meteo_name, 'darkred'),
            (self.df_snotel, f'{snotel_name}_{rolling_avg_days}d', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels=show_x_labels,
            percentage=0.20,
            y_units='°F',
            # y_max=85,
            # y_min=60
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    def soil_moisture_graph(self, graph_end_date, show_x_labels:bool = False, title:str=""):
        time_series = [
            (self.df_snotel, 'soil_moisture_percent_2in', 'royalblue'),
            (self.df_snotel, 'soil_moisture_percent_8in', 'darkgreen'),
            (self.df_snotel, 'soil_moisture_percent_20in', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = show_x_labels,
            percentage=0.20,
            y_units='%',
            # y_min=0.0
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    def soil_temperature_graph(self, graph_end_date, show_x_labels:bool = False, title:str=""):
        time_series = [
            (self.df_snotel, 'soil_temperature_observed_2in', 'royalblue'),
            (self.df_snotel, 'soil_temperature_observed_8in', 'darkgreen'),
            (self.df_snotel, 'soil_temperature_observed_20in', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = show_x_labels,
            percentage=0.20,
            y_units='°F',
            y_min=22
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

    def right_axis_annotations(self):
        pass

    def load_snotel_station(self, stations:pd.DataFrame, name)->Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
        station_matches = stations_with_name(stations, name)
        for station in station_matches:
            station_id = station.get('station_id', '')
            state = station.get('state', '')
            df_summary = get_snotel_station_elements(station_id, state)
            # df_summary = get_snotel_sensors_with_dates(station_id, state)
            print_full_summary(df_summary, title=f"{name} Sensor Summary:")
            self.num_years = get_sensor_history_years(df_summary)
            # self.num_years = 7
            self.start_date = self.end_date.replace(year=self.end_date.year - self.num_years)
            begin_date = self.start_date.strftime("%Y-%m-%d")
            # begin_date = "2026-01-01"
            # end_date = "2026-07-02"
            file_name = name.replace(" ", "_")
            daily_file_name = file_name +  '_daily.csv'
            elements = [
                "TAVG::value", "TMAX::value", "TMIN::value", "TOBS::value",
                "WTEQ::value", "SNWD::value", "PREC::value", "PRCP::value",
                "SMS:-2:value", "SMS:-8:value", "SMS:-20:value",
                "STO:-2:value", "STO:-8:value", "STO:-20:value"
            ]
            df = get_snotel_data(station_id, state, elements, "daily", begin_date=begin_date, file_name=daily_file_name)

            hourly_file_name = file_name + '_hourly.csv'
            elements = [
                "WSPDV::value",
                "WSPDX::value",
                "WDIRV::value",
                # "SWINV::value",
                "SWOTV:-2:value",     # Albedo, New 7-31-2024 on Lizard Head
                # "RHUMV::value"
                "RHUM::value"
            ]
            df_hourly = get_snotel_data(station_id, state, elements, "hourly", file_name=hourly_file_name)
            return df, df_summary

        print(f'load_snotel_station {name} not found')
        return None

    @staticmethod
    def smooth_openet_daily(df: pd.DataFrame, window: int = 3, model_cols=None) -> pd.DataFrame:
        """
        Apply running average to daily ET columns.
        """
        df = df.copy()
        df = df.sort_values('Date').reset_index(drop=True)

        if model_cols is None:
            # Auto-detect ET columns (everything except Date)
            model_cols = [col for col in df.columns if col != 'Date']

        for col in model_cols:
            df[f'{col}_smooth_{window}d'] = df[col].rolling(window=window, min_periods=1, center=True).mean()

        return df

    # Recommended Corrections (based on studies in CO/Utah Rockies)Situation
    # Suggested Correction        Notes
    # eeMETRIC alone in dense forest
    #         Multiply by 0.75 – 0.85 during Jul–Aug      Most common adjustment
    # eeMETRIC + DisALEXI hybrid
    #         Weight 60–70% eeMETRIC,30–40% DisALEXI      Good compromise
    # Using Ensemble
    #         Light correction: 0.90 – 0.95               Ensemble already reduces the bias
    # Winter months
    #         Usually no correction or slight upward
    #        eeMETRIC can be low in winter
    @staticmethod
    def apply_bias_correction(df):
        df = df.copy()

        # Extract month
        df['month'] = pd.to_datetime(df['Date']).dt.month

        # Bias correction factor
        df['eeMETRIC_adj'] = df['eeMETRIC'].copy()

        # Strong correction in peak summer for forests
        summer_mask = df['month'].isin([7, 8])
        df.loc[summer_mask, 'eeMETRIC_adj'] = df.loc[summer_mask, 'eeMETRIC'] * 0.82  # 0.78-0.85 range is typical

        # Optional: lighter correction in June/September
        shoulder_mask = df['month'].isin([6, 9])
        df.loc[shoulder_mask, 'eeMETRIC_adj'] = df.loc[shoulder_mask, 'eeMETRIC'] * 0.92

        return df

    def load_data(self) -> Optional[date]:
        self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

        lizard_hwad = 'data/OpenMeteo/lizard_head_37.799991_-107.933968_1940-01-01_2026-07-10_daily.csv'
        el_diente = 'data/OpenMeteo/el_diente_37.79_-108.02_1940-01-01_2026-07-10_daily.csv'
        rico = "data/OpenMeteo/rico_37.7_-108.0_1940-01-01_2026-07-10_daily.csv"
        df = pd.read_csv(el_diente)
        self.df_open_meteo = df.rename(columns={'time': 'Date'})

        self.df_open_et = openet_json_file_to_dataframe('/opt/dev/gis/OpenET/lizard_head/lizard_head_2016-08-01_2026-06-30_ensemble_in_daily.json',)
        paths = [
            '/opt/dev/gis/OpenET/lizard_head/lizard_head_2016-08-01_2026-06-30_eeMETRIC_in_daily.json',
            '/opt/dev/gis/OpenET/lizard_head/lizard_head_2016-08-01_2026-06-30_DisALEXI_in_daily.json',
        ]

        for path in paths:
            self.df_open_et = openet_json_file_to_dataframe(path, self.df_open_et)

        self.df_open_et = Snotel.smooth_openet_daily(self.df_open_et, self.smooth_days)

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

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    frame = Snotel(notebook_frame)
    frame.Show()

    notebook_frame.Show()
    app.MainLoop()