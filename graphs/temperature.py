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
from typing import Optional, Tuple
from colorado.river_war import RiverWar
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import wx
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from source.nrcs_snotel import (get_snotel_data, get_snotel_stations,
                                stations_with_name, print_full_summary, get_sensor_history_years,
                                get_snotel_hourly_data, get_snotel_station_elements)



class TemperatureChartFrame(ChartFrame):
    """
    Derived from ChartFrame to show SNOTEL temperature analysis (TMAX, TAVG, TMIN on separate pages).
    """

    def __init__(self,
                 notebook_frame: NotebookFrame,
                 snotel_name: str):
        self.snotel_name = snotel_name
        self.start_date = date.today()
        self.end_date = date.today()

        # self.snotel_name = 'El Diente'
        # self.snotel_name = 'Black Mesa'
        # self.snotel_name = 'Scotch Creek'
        # self.snotel_name = 'Sharkstooth'
        # self.snotel_name = 'Lone Cone'
        # self.snotel_name = 'Lizard Head'

        self.end_date = date.today()
        stations = get_snotel_stations("stations.csv")
        self.df_snotel, self.df_snotel_summary = self.load_snotel_station(stations, self.snotel_name)

        super().__init__(
           notebook_frame=notebook_frame,
           reservoir_lists=None,
           reports=None,
           page_name=snotel_name
        )


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

    def load_data(self) -> Optional[pd.DataFrame]:
        """
        Load raw SNOTEL data and build a master DataFrame with multiple variables.
        """
        # Start with first variable (creates the base df)
        self.df = TemperatureChartFrame.analyze_snotel_variable(
            df_snotel=self.df_snotel,
            existing_df=None,
            variable='TMAX',
            year_start_month=10,
            min_days_per_year=300,
            compute_trend=True,
            agg='mean'
        )

        # Add more variables (they merge into self.df)
        self.df = TemperatureChartFrame.analyze_snotel_variable(
            df_snotel=self.df_snotel,
            existing_df=self.df,
            variable='TMIN',
            year_start_month=10,
            min_days_per_year=300,
            compute_trend=True,
            agg='mean'
        )

        if 0:
            # Set start/end dates from the master DataFrame
            if not self.df.empty:
                self.start_date = self.df['Date'].iloc[0].date()
                self.end_date = self.df['Date'].iloc[-1].date()
            else:
                self.start_date = date.today()
                self.end_date = date.today()

        return self.df

    def load_charts(self):
        graph_end_date = date.today()

        title = f'Dolores River - {self.snotel_name} SNOTEL'

        time_series = [
            (self.df, 'TMAX', 'royalblue'),
            (self.df, 'TMAX_Trend', 'red'),
        ]
        self.create_line_chart(time_series, title=title)

        time_series = [
            (self.df, 'TMIN', 'royalblue'),
            (self.df, 'TMIN_Trend', 'red'),
        ]
        self.create_line_chart(time_series)

    def create_line_chart(self, time_series:list, title:str=""):
        line_chart = LineChart(
            time_series,
            title=title,
            start_date=self.start_date, current_date=self.end_date, end_date=self.end_date,
            show_x_labels=True,
            percentage=0.20,
            y_units='°F',
        )
        # self.line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)

    def load_reservoirs(self) -> Optional[date]:
        date_time_as_date = None
        start = self.start_date
        current = self.end_date
        end = self.end_date

        for reservoir_list in self.reservoir_lists:
            for reservoir in reservoir_list:
                reservoir.load_data(None, start, current, end)
        return date_time_as_date
    @staticmethod
    def analyze_snotel_variable(
            df_snotel: pd.DataFrame,
            existing_df: Optional[pd.DataFrame] = None,
            variable: str = 'TAVG',
            year_start_month: int = 10,
            min_days_per_year: int = 300,
            compute_trend: bool = True,
            agg: str = 'mean'
    ) -> pd.DataFrame:
        """
        Keeps all full years + the most recent (possibly partial) year.
        """
        # Normalize variable name
        short_to_long = {
            'TMAX': 'air_temperature_maximum',
            'TAVG': 'air_temperature_average',
            'TMIN': 'air_temperature_minimum',
            'TOBS': 'air_temperature_observed',
            'WTEQ': 'snow_water_equivalent',
            'PREC': 'precipitation',
            'SNWD': 'snow_depth',
        }
        long_to_short = {v: k for k, v in short_to_long.items()}

        if variable in short_to_long:
            short_var = variable
            long_var = short_to_long[variable]
        elif variable in long_to_short:
            short_var = long_to_short[variable]
            long_var = variable
        else:
            short_var = variable
            long_var = variable

        if long_var not in df_snotel.columns:
            raise KeyError(f"Column '{long_var}' (from '{short_var}') not found.")

        # Process raw data
        df = df_snotel.copy()
        df = df.rename(columns={long_var: 'Value'})
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna(subset=['Date', 'Value']).copy()
        df = df.set_index('Date').sort_index()

        if df.empty:
            raise ValueError(f"No valid data for '{short_var}'.")

        def get_year(d):
            if d.month >= year_start_month:
                return d.year
            else:
                return d.year - 1

        df['Year'] = df.index.map(get_year)

        # Aggregate
        if agg == 'mean':
            yearly = df.groupby('Year')['Value'].mean()
        elif agg == 'max':
            yearly = df.groupby('Year')['Value'].max()
        elif agg == 'min':
            yearly = df.groupby('Year')['Value'].min()
        elif agg == 'sum':
            yearly = df.groupby('Year')['Value'].sum()
        else:
            raise ValueError(f"Unsupported aggregation: {agg}")

        days_per_year = df.groupby('Year').size()

        if not days_per_year.empty:
            max_year = days_per_year.index.max()

            # Keep:
            # - All years that meet the minimum days requirement
            # - PLUS the most recent year (even if partial)
            valid_years = days_per_year[
                (days_per_year >= min_days_per_year) | (days_per_year.index == max_year)
            ].index

            yearly = yearly.loc[valid_years]

        if yearly.empty:
            raise ValueError(f"No valid years for '{short_var}'.")

        # Linear trend
        slope = intercept = r_squared = p_value = std_err = None
        trend_series = pd.Series(index=yearly.index, dtype=float)

        if compute_trend and len(yearly) >= 3:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                yearly.index, yearly.values
            )
            trend_series = intercept + slope * yearly.index
            r_squared = r_value ** 2

        # Build new data
        new_data = pd.DataFrame({
            'Date': pd.to_datetime(yearly.index.astype(str) + '-01-01'),
            short_var: yearly.values,
            f"{short_var}_Trend": trend_series.values
        })

        # Merge into master
        if existing_df is not None and not existing_df.empty:
            master = existing_df.copy()
            master = pd.merge(master, new_data, on='Date', how='outer')
            master = master.sort_values('Date').reset_index(drop=True)
        else:
            master = new_data.copy()

        # Metadata
        master.attrs.update({
            'variable': short_var,
            'year_start_month': year_start_month,
            'agg': agg,
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'p_value': p_value,
            'std_err': std_err
        })

        return master

    def analyze_snotel_temperature(self, csv_path: str, temp_col: str = 'air_temperature_average', year_start_month: int = 1):
        df = pd.read_csv(csv_path, parse_dates=['Date'])

        # Mapping short -> long names
        short_to_long = {
            'TMAX': 'air_temperature_maximum',
            'TAVG': 'air_temperature_average',
            'TMIN': 'air_temperature_minimum',
            'TOBS': 'air_temperature_observed',
            'WTEQ': 'snow_water_equivalent',
            # add more as needed
        }

        original = temp_col
        if temp_col in short_to_long:
            temp_col = short_to_long[temp_col]

        if temp_col not in df.columns:
            raise KeyError(f"Could not find column '{original}'. Available: {list(df.columns)}")

        df = df.rename(columns={'Date': 'Date', temp_col: 'Temp'})

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()

        def get_custom_year(d):
            if d.month >= year_start_month:
                return d.year
            else:
                return d.year - 1

        df['CustomYear'] = df.index.map(get_custom_year)
        yearly = df.groupby('CustomYear')['Temp'].mean()

        if not yearly.empty:
            first_year = yearly.index.min()
            if len(df[df['CustomYear'] == first_year]) < 300:
                yearly = yearly.drop(first_year)

        plt.figure(figsize=(11, 6))
        plt.plot(yearly.index, yearly.values, label='Yearly Avg Temp', color='darkblue', marker='o', markersize=4)

        if len(yearly) >= 3:
            slope, intercept = np.polyfit(yearly.index, yearly.values, 1)
            plt.plot(yearly.index, intercept + slope * yearly.index, 'r--',
                     label=f'Trend: {slope:.3f} °F/yr')

        ax = plt.gca()
        ax.yaxis.set_minor_locator(plt.MultipleLocator(0.2))
        ax.grid(True, which='major', linestyle='-', linewidth=1.0, color='gray', alpha=0.85)
        ax.grid(True, which='minor', linestyle='--', linewidth=0.6, color='gray', alpha=0.5)

        year_type = "Water Year" if year_start_month == 10 else "Calendar Year"
        plt.title(f"{original} - {year_type}")
        plt.xlabel('Year')
        plt.ylabel('Temperature (°F)')
        plt.legend()
        plt.tight_layout()

        fig = plt.gcf()
        return yearly, fig

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    TemperatureChartFrame(notebook_frame=notebook_frame, snotel_name='Lizard Head')
    TemperatureChartFrame( notebook_frame=notebook_frame,snotel_name='El Diente')
    TemperatureChartFrame( notebook_frame=notebook_frame,snotel_name='Lone Cone')
    TemperatureChartFrame( notebook_frame=notebook_frame,snotel_name='Scotch Creek')
    TemperatureChartFrame( notebook_frame=notebook_frame,snotel_name='Sharkstooth')
    TemperatureChartFrame( notebook_frame=notebook_frame,snotel_name='Black Mesa')

    notebook_frame.Show()
    app.MainLoop()


    # Not used

    def analyze_lizard_head_temp_with_correction(csv_path: str):
        """
        Analyze Lizard Head SNOTEL temperature with sensor upgrade correction.
        """
        df = pd.read_csv(csv_path, parse_dates=['Date'])
        df = df.set_index('Date').sort_index()

        # Rename long columns
        rename_map = {
            'air_temperature_average': 'TAVG',
            'air_temperature_maximum': 'TMAX',
            'air_temperature_minimum': 'TMIN',
            'air_temperature_observed': 'TOBS'
        }
        df = df.rename(columns=rename_map)

        if 'TAVG' not in df.columns:
            df['TAVG'] = (df['TMAX'] + df['TMIN']) / 2

        temp_series = df['TAVG'].dropna()

        # Water year
        df['WaterYear'] = (
            pd.DatetimeIndex(df.index).year.where(
                pd.DatetimeIndex(df.index).month < 10,
                pd.DatetimeIndex(df.index).year + 1
            )
        )
        water_year = df.groupby('WaterYear')['TAVG'].mean()

        # === Sensor upgrade correction (approximate) ===
        # Based on known inhomogeneity ~2004 at many SNOTEL sites
        # New sensor tends to read warmer at cold temps → we apply a simple adjustment to pre-upgrade data
        pre_upgrade = water_year[water_year.index < 2004]
        post_upgrade = water_year[water_year.index >= 2004]

        if not pre_upgrade.empty and not post_upgrade.empty:
            offset = pre_upgrade.mean() - post_upgrade.mean() * 0.7  # rough empirical adjustment
            water_year_corrected = water_year.copy()
            water_year_corrected[water_year_corrected.index < 2004] += offset
            print(f"Applied approximate sensor correction offset: {offset:.2f} °F to pre-2004 data")
        else:
            water_year_corrected = water_year

        # Trend on corrected series
        years = water_year_corrected.index.values
        temps = water_year_corrected.values
        slope, intercept, r, p, se = stats.linregress(years, temps)
        print(f"\nWater Year Trend (with correction):")
        print(f"  Slope: {slope:.3f} °F/year (p = {p:.4f})")
        print(f"  R²: {r ** 2:.3f}")

        # Plot
        plt.figure(figsize=(11, 6))
        plt.plot(water_year.index, water_year.values, 'b-', alpha=0.6, label='Raw Water Year Avg')
        plt.plot(water_year_corrected.index, water_year_corrected.values, 'g-', label='Corrected')
        plt.plot(years, intercept + slope * years, 'r--', label=f'Trend: {slope:.3f} °F/yr')
        plt.axvline(2004, color='orange', linestyle='--', alpha=0.7, label='~2004 sensor upgrade')
        plt.title('Lizard Head Pass - Temperature Trend with Sensor Correction')
        plt.xlabel('Water Year')
        plt.ylabel('Temperature (°F)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        return water_year, water_year_corrected