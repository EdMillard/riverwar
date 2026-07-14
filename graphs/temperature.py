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
from typing import Optional
from colorado.river_war import RiverWar
from graphs.chart_frame import ChartFrame, NotebookFrame
import wx
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def load_data(self) -> Optional[date]:
    # self.df_daily: pd.DataFrame = df_utils.create_daily_df(self.start_date, self.end_date, [])

    lizard_hwad = 'data/OpenMeteo/lizard_head_37.799991_-107.933968_1940-01-01_2026-07-10_daily.csv'
    el_diente = 'data/OpenMeteo/el_diente_37.79_-108.02_1940-01-01_2026-07-10_daily.csv'
    rico = "data/OpenMeteo/rico_37.7_-108.0_1940-01-01_2026-07-10_daily.csv"
    df = pd.read_csv(el_diente)
    self.df_open_meteo = df.rename(columns={'time': 'Date'})

def load_reservoirs(self) -> Optional[date]:
    date_time_as_date = None
    start = self.start_date
    current = self.end_date
    end = self.end_date

    for reservoir_list in self.reservoir_lists:
        for reservoir in reservoir_list:
            reservoir.load_data(None, start, current, end)
    return date_time_as_date

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


class TemperatureChartFrame(ChartFrame):
    """
    Derived from ChartFrame to show SNOTEL temperature analysis (TMAX, TAVG, TMIN on separate pages).
    """

    def __init__(self,
                 notebook_frame: NotebookFrame,
                 csv_path: str,
                 temp_col: str = 'air_temperature_average',  # added
                 page_name: str = "Temperature Analysis"):
        self.notebook_frame = notebook_frame
        # super().__init__(
        #    notebook_frame=notebook_frame,
        #    reservoir_lists=None,
        #    reports=None,
        #    page_name=page_name
        # )

        self.csv_path = csv_path
        self.temp_col = temp_col

        self.create_all_temperature_pages()

    def create_all_temperature_pages(self):
        """Create three separate notebook pages for TMAX, TAVG, TMIN."""
        self._create_temp_page('TMAX', "Maximum Temperature")
        self._create_temp_page('TAVG', "Average Temperature")
        self._create_temp_page('TMIN', "Minimum Temperature")

    def _create_temp_page(self, temp_col: str, page_title: str):
        """Create one temperature analysis page."""
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

        yearly, fig = self.analyze_snotel_temperature(
            csv_path=self.csv_path,
            temp_col=temp_col,
            year_start_month=1  # 1 = Jan (default), change to 10 for water year
        )

        page = wx.Panel(self.notebook_frame.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        canvas = FigureCanvas(page, -1, fig)
        sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 5)
        page.SetSizer(sizer)

        self.notebook_frame.notebook.AddPage(page, page_title)

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

    temperature_page = TemperatureChartFrame(
        notebook_frame=notebook_frame,
        csv_path="data/NRCS/SNOTEL/El_Diente_daily.csv",
    )


    notebook_frame.Show()
    app.MainLoop()