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
import matplotlib.ticker as ticker
import pandas as pd
from datetime import date
from typing import List, Optional, Tuple
from chart.chart import Chart


class LineChart(Chart):
    """
    Line chart for multiple time series with short two-digit year X-axis.
    """
    def __init__(self,
                 data_series: List[Tuple[pd.DataFrame, str, str]],
                 percentage: float = 0.0,
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None,
                 show_x_labels: bool = True,
                 y_label: str = 'Volume (Million Acre-Feet)',
                 y_divisor: float = 1_000_000):

        super().__init__(reservoirs or [], start_date, current_date, end_date, percentage=percentage)

        self.data_series = data_series
        self.title = title
        self.show_x_labels = show_x_labels
        self.y_divisor = y_divisor
        self.y_label = y_label

        self.height_inch = 5.5
        self.width_inch = 10.5
        self.y_max = None

        # Normalize DataFrames
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)

    def set_start_date(self, start_date: date | None):
        self.start_date = start_date

    def set_end_date(self, end_date: date | None):
        self.end_date = end_date

    def set_current_date(self, current_date: date | None):
        self.current_date = current_date

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=110)
        ax = fig.add_subplot(111)

        self.create_line_chart(ax)

        # Dynamic top margin
        has_title = bool(self.title and str(self.title).strip())
        top_margin = 0.88 if has_title else 0.96

        fig.tight_layout(pad=1.3)
        fig.subplots_adjust(left=0.08, right=0.95, bottom=0.085, top=top_margin)

        self.fig = fig
        return fig

    def create_line_chart(self, ax):
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        # === Plot lines ===
        all_dates = []
        for df, col, color in self.data_series:
            if df.empty or col not in df.columns:
                continue
            df[col] = pd.to_numeric(df[col], errors='coerce')
            all_dates.extend(df['Date'])

            ax.plot(df['Date'], df[col],
                    label=col.replace('_', ' '),
                    linewidth=2.2,
                    color=color)

        if not all_dates:
            return

        data_min = min(all_dates)
        data_max = max(all_dates)

        x_start = self.start_date if self.start_date is not None else data_min
        x_end = self.end_date if self.end_date is not None else data_max

        ax.set_ylabel(self.y_label, fontsize=12, fontweight='bold')

        if self.title and str(self.title).strip():
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)

        # === X-AXIS: Short two-digit years, no slant ===
        ax.set_xlim(x_start, x_end)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%y'))   # '75, '80, etc.

        if not self.show_x_labels:
            ax.set_xticklabels([])
            ax.tick_params(axis='x', which='major', length=0)

        # === Y-AXIS ===
        def scaled_formatter(x, pos):
            if self.y_divisor == 1:
                return f'{x:,.0f}'
            else:
                return f'{x / self.y_divisor:,.2f}'

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(scaled_formatter))
        ax.yaxis.set_major_locator(ticker.AutoLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        ax.grid(True, linestyle='--', alpha=0.7)
        ax.axhline(y=0, color='black', linewidth=2.5, linestyle='-', alpha=0.9, zorder=3)

        ax.legend(fontsize=10.5, loc='best')

        if self.y_max is not None:
            ax.set_ylim(0, self.y_max)