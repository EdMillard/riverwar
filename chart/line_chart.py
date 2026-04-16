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
from reservoirs.reservoir import Reservoir
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import pandas as pd
from datetime import date, timedelta
from typing import List, Optional, Tuple
from chart.chart import Chart

class LineChart(Chart):
    """
    Line chart for multiple time series with Month-Year X-axis.
    """
    def __init__(self,
                 data_series: List[Tuple[pd.DataFrame, str, str]],
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None):

        super().__init__(reservoirs or [], start_date, current_date, end_date)

        self.data_series = data_series
        self.title = title

        self.height_inch = 6.0
        self.width_inch = 10.5   # Slightly wider for better month labels
        self.y_max = None

        # Normalize DataFrames
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=110)
        ax = fig.add_subplot(111)

        self.create_line_chart(ax)

        fig.tight_layout(pad=2.0)
        self.fig = fig
        return fig

    def create_line_chart(self, ax, y_label='Volume (Million Acre-Feet)'):
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        for df, col, color in self.data_series:
            if df.empty or col not in df.columns:
                continue

            df[col] = pd.to_numeric(df[col], errors='coerce')

            ax.plot(df['Date'], df[col],
                    label=col.replace('_', ' '),
                    linewidth=2.2,
                    color=color)

        # ==================== FORMATTING ====================
        ax.set_title(self.title or "Daily Values", fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("Date", fontsize=12, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=12, fontweight='bold')

        # === MONTH YEAR LABELS (What you wanted) ===
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))        # One label per month
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))        # "Apr 2025"

        # Optional: Show every 2 or 3 months if too crowded
        # ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

        fig = ax.get_figure()
        fig.autofmt_xdate(rotation=45, ha='right')

        ax.grid(True, linestyle='--', alpha=0.7)

        # ==================== BOLD Y=0 ORIGIN LINE ====================
        ax.axhline(y=0, color='black', linewidth=2.5, linestyle='-', alpha=0.9, zorder=3)

        ax.legend(fontsize=10.5, loc='best')

        if self.y_max is not None:
            ax.set_ylim(0, self.y_max)

    def update_data(self, new_data_series: List[Tuple[pd.DataFrame, str, str]]):
        """Update with new list of tuples"""
        self.data_series = new_data_series
        # Re-normalize dates
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)