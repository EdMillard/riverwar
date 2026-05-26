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
from datetime import date
from typing import List, Optional, Tuple, Literal
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
                 show_x_labels: bool = True,
                 y_label: str = "",                    # kept for future flexibility
                 y_units: Literal['MAF', 'TAF', 'AF', 'FT', 'CFS'] = 'MAF',
                 y_divisor: float | None = None,
                 y_max: Optional[float] = None,
                 y_min: Optional[float] = None
                 ):

        super().__init__(start_date, current_date, end_date, y_divisor=y_divisor, y_units=y_units, percentage=percentage)

        self.data_series = data_series
        self.title = title
        self.show_x_labels = show_x_labels
        self.y_label = y_label.strip()
        self.y_units = y_units
        self.y_max = y_max
        self.y_min = y_min
        self.ax = None

        # Auto-determine divisor
        if y_divisor is not None:
            self.y_divisor = y_divisor
        else:
            self.y_divisor = self._get_divisor_for_units(y_units)

        self.height_inch = 5.5
        self.width_inch = 10.5

        # Normalize DataFrames
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)

    # ==================== SETTERS ====================
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
        self.ax = fig.add_subplot(111)

        self.create_line_chart(self.ax)

        left_margin = 0.07
        right_margin = 0.95
        top_margin = 0.92 if self.title and self.title.strip() else 1
        bottom_margin = 0.1 if self.show_x_labels else 0.01

        fig.tight_layout(pad=1.0)
        fig.subplots_adjust(left=left_margin, right=right_margin, bottom=bottom_margin, top=top_margin)

        # fig.tight_layout(pad=1.3)
        # fig.subplots_adjust(left=0.08, right=0.95, bottom=0.085, top=top_margin)

        self.fig = fig
        return fig

    def create_line_chart(self, ax):
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

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

        if self.title and str(self.title).strip():
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)

        # ==================== X-AXIS ====================
        ax.set_xlim(x_start, x_end)

        # Main ticks: Years
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%y'))

        # Minor ticks: Months (first letter)
        years_span = (x_end - x_start).days / 365.25
        if years_span >= 0.5:
            ax.xaxis.set_minor_locator(mdates.MonthLocator())

        # if self.show_x_labels:
        def month_first_letter(x, pos):
            return mdates.DateFormatter('%b')(x, pos)[0]

        ax.xaxis.set_minor_formatter(month_first_letter)

        ax.tick_params(axis='x', which='minor', length=3, width=0.7, labelsize=8.5, rotation=0, pad=2)
        ax.tick_params(axis='x', which='major', length=6, width=1.2, labelsize=10, pad=4)

        if not self.show_x_labels:
            ax.set_xticklabels([])
            # ax.tick_params(axis='x', which='major', length=0)

        # ==================== GRID LINES ====================
        # Major grid (years) - darker
        ax.grid(True, which='major', linestyle='-', linewidth=1.0, color='gray', alpha=1, zorder=0)

        # Minor grid (months) - lighter subgrid
        ax.grid(True, which='minor', linestyle='--', linewidth=0.7, color='gray', alpha=0.75, zorder=0)

        # Y grid (kept as before)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)

        ax.axhline(y=0, color='black', linewidth=1.0, linestyle='-', alpha=1, zorder=3)

        # Y-AXIS
        self.setup_yaxis(ax)

        ax.legend(fontsize=10.5, loc='best')

        if self.y_max is not None and self.y_min is not None:
            ax.set_ylim(self.y_min, self.y_max)
        elif self.y_max is not None :
            ax.set_ylim(ymax=self.y_max)
        elif self.y_min is not None :
            ax.set_ylim(ymin=self.y_min)