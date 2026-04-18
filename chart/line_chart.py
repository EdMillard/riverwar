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
    Line chart for multiple time series with Month-Year X-axis.
    """
    def __init__(self,
                 data_series: List[Tuple[pd.DataFrame, str, str]],
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None,
                 show_x_labels: bool = True,
                 y_label: str = 'Volume (Million Acre-Feet)',
                 y_divisor: float = 1_000_000):           # ← New option

        super().__init__(reservoirs or [], start_date, current_date, end_date)

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

    def create_line_chart(self, ax):
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
        ax.set_ylabel(self.y_label, fontsize=12, fontweight='bold')

        if self.title and str(self.title).strip():
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)

        # === X-AXIS ===
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

        if not self.show_x_labels:
            ax.set_xticklabels([])
            ax.tick_params(axis='x', which='major', length=0)

        # === Y-AXIS: Scaled by y_divisor ===
        def scaled_formatter(x, pos):
            if self.y_divisor == 1:
                return f'{x:,.0f}'
            else:
                return f'{x / self.y_divisor:,.2f}'

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(scaled_formatter))
        ax.yaxis.set_major_locator(ticker.AutoLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        # === TIGHTER BOTTOM MARGIN WHEN X LABELS ARE HIDDEN ===
        fig = ax.get_figure()
        if not self.show_x_labels:
            fig.subplots_adjust(bottom=0.08)   # Much tighter bottom
        else:
            fig.subplots_adjust(bottom=0.15)   # Normal spacing with labels

        fig.autofmt_xdate(rotation=45, ha='right')

        ax.grid(True, linestyle='--', alpha=0.7)

        # Bold Y=0 origin line
        ax.axhline(y=0, color='black', linewidth=2.5, linestyle='-', alpha=0.9, zorder=3)

        ax.legend(fontsize=10.5, loc='best')

        if self.y_max is not None:
            ax.set_ylim(0, self.y_max)