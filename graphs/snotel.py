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
from datetime import date, datetime
from typing import List, Optional, Tuple
from colorado.river_war import RiverWar
from api import df_utils
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import wx
from source.nrcs_snotel import (get_snotel_data, get_snotel_stations, stations_in_county, stations_in_state,
                                stations_with_name, print_full_summary,
                                get_snotel_hourly_data, get_snotel_station_elements)
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

        self.snotel_name = 'Lizard Head Pass'
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

    @staticmethod
    def get_sensor_history_years(sensors_df: pd.DataFrame) -> int:
        """
        Returns years of history from the oldest sensor.
        Works with both old Report Generator format and new REST format.
        """
        if sensors_df.empty:
            return 0

        # Support both column names
        date_col = None
        for col in ['sensor_start_date', 'begin_date']:
            if col in sensors_df.columns:
                date_col = col
                break

        if date_col is None:
            print("No date column found in sensor DataFrame.")
            return 0

        earliest_date = pd.to_datetime(sensors_df[date_col]).min()
        current_year = datetime.now().year

        years_back = current_year - earliest_date.year

        print(f"Earliest sensor date: {earliest_date.date()}")
        print(f"Years of history: {years_back}")

        return years_back

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
            self.num_years = Snotel.get_sensor_history_years(df_summary)
            # self.num_years = 16
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

    def load_data(self) -> Optional[date]:
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
            (self.df_daily, 'Dolores River at Dolores, CO', 'darkred'),
            (self.df_daily, 'Dolores River Below Rico, CO', 'royalblue'),
            # (self.df_daily, 'Lost Canyon Creek Near Dolores, CO', 'darkgreen')
        ]
        self.line_chart = LineChart(
            time_series,
            title=f'Dolores River - {self.snotel_name} SNOTEL',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='CFS',
            y_min=0.0,
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            # (self.df_snotel, 'snow_depth', 'darkgreen'),
            (self.df_snotel, 'precipitation_accumulation', 'royalblue'),
            (self.df_snotel, 'snow_water_equivalent', 'darkgreen'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = True,
            percentage=0.20,
            y_units='in',
            y_min=0.0
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = [
            (self.df_snotel, 'soil_moisture_percent_2in', 'royalblue'),
            (self.df_snotel, 'soil_moisture_percent_8in', 'darkgreen'),
            (self.df_snotel, 'soil_moisture_percent_20in', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='%',
            # y_min=0.0
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        # 'air_temperature_minimum',
        # 'air_temperature_maximum',
        # 'air_temperature_observed',
        rolling_avg_days = 10
        self.df_snotel[f'air_temperature_average_{rolling_avg_days}d'] = (
            self.df_snotel['air_temperature_average']
            .rolling(window=rolling_avg_days, center=True, min_periods=3)
            .mean()
        )
        time_series = [
            (self.df_snotel, f'air_temperature_average_{rolling_avg_days}d', 'royalblue'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='°F',
            # y_max=85,
            # y_min=60
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)


        time_series = [
            (self.df_snotel, 'soil_temperature_observed_2in', 'royalblue'),
            (self.df_snotel, 'soil_temperature_observed_8in', 'darkgreen'),
            (self.df_snotel, 'soil_temperature_observed_20in', 'darkred'),
        ]
        self.line_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels = False,
            percentage=0.20,
            y_units='°F',
            y_min=22
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    frame = Snotel(notebook_frame)
    frame.Show()

    notebook_frame.Show()
    app.MainLoop()