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
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import numpy as np
from PIL import Image
import pandas as pd
import io
from datetime import date, timedelta
from typing import List, Optional, Literal


class Chart:
    def __init__(self,
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 show_title: bool = False,
                 percentage: float = 0.0,
                 y_label: str = "",
                 y_units: Literal['MAF', 'TAF', 'AF', 'FT', 'CFS'] = 'MAF',
                 y_divisor: float | None = None):

        self.percentage = percentage
        self.show_title = show_title
        self.canvas = None
        self.panel = None

        self.data_series = None

        self.report_name = ''

        # Dates
        self.start_date = start_date or date(2025, 10, 1)
        self.current_date = current_date or date(2026, 4, 1)
        self.end_date = end_date or date(2026, 9, 30)

        self.width_inch = 14.8
        self.height_inch = 6.5
        self.fig = None

        # Y-axis configuration
        self.y_label = y_label.strip()
        self.y_units = y_units

        # Set divisor - use provided value or auto from units
        if y_divisor is not None:
            self.y_divisor = y_divisor
        else:
            self.y_divisor = self._get_divisor_for_units(y_units)

        self.y_max = 10.0

    @staticmethod
    def _get_divisor_for_units(units: str) -> float:
        """Centralized divisor logic"""
        if units == 'MAF':
            return 1_000_000
        elif units == 'TAF':
            return 1_000
        elif units in ['AF', 'FT', 'CFS']:
            return 1.0
        return 1_000_000  # safe fallback

    def scaled_formatter(self, x, pos):
        if self.y_divisor <= 1:
            return f'{x:,.0f}'
        else:
            return f'{x / self.y_divisor:,.2f}'

    def setup_yaxis(self, ax):
        """Smart Y-axis with good label visibility on small values."""
        ax.set_ylabel(self.y_units, fontsize=11.5, fontweight='bold')
        formatter = ticker.FuncFormatter(self.scaled_formatter)
        ax.yaxis.set_major_formatter(formatter)

        if not self.data_series:
            return

        # Get data range
        all_values = []
        for item in self.data_series:
            # Take only the first three elements (df, col, color); ignore any extra flags
            df, col, *_ = item
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors='coerce').dropna()
                if not vals.empty:
                    all_values.extend(vals)

        if not all_values:
            return

        data_min = min(all_values)
        data_max = max(all_values)
        data_range = data_max - data_min if data_max > data_min else 1.0

        # Tick strategy (your existing logic)
        if data_range <= 1.0:
            major_step = 0.1
            minor_step = 0.05
        elif data_range <= 5.0:
            major_step = 0.5
            minor_step = 0.1
        elif data_range <= 20.0:
            major_step = 1.0
            minor_step = 0.25
        elif data_range <= 50.0:
            major_step = 5.0
            minor_step = 1.0
        elif data_range <= 200.0:
            major_step = 10.0
            minor_step = 2.0
        else:
            major_step = round(data_range / 8 / 10) * 10 or 100
            minor_step = major_step / 5

        from matplotlib.ticker import MultipleLocator
        ax.yaxis.set_major_locator(MultipleLocator(major_step))
        ax.yaxis.set_minor_locator(MultipleLocator(minor_step))

        if data_range <= 5.0:
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        elif data_range <= 20.0:
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

        # Tick appearance
        ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=10)
        ax.tick_params(axis='y', which='minor', length=3, width=0.7, labelsize=8.5)

        ax.grid(True, which='major', axis='y', linestyle='-', linewidth=1.2, color='black', alpha=0.7)
        ax.grid(True, which='minor', axis='y', linestyle='--', linewidth=0.6, color='gray', alpha=0.5)

        if data_min >= 0:
            ax.set_ylim(ymin=0)

    def create_chart(self, ax: Axes, title: str):
        pass

    def final_layout(self, ax, title: str, names: List[str], x_pos: np.ndarray):
        pass

    def create_figure(
            self,
            width_inch: Optional[int] = None,
            height_inch: Optional[int] = None
    ) -> Optional[Figure]:
        return None

    def get_figure(self, width_inch=None, height_inch=None):
        return self.create_figure(width_inch, height_inch)

    def save_figure(self) -> Image.Image:
        buffer = io.BytesIO()
        self.canvas.figure.savefig(buffer, dpi=180, bbox_inches='tight', format='png')
        buffer.seek(0)
        image = Image.open(buffer)
        return image

    def update_report(self, report_name: str):
        self.report_name = report_name

    def create_panel(self, parent: wx.SplitterWindow | wx.Panel):
        self.panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.canvas = FigureCanvas(self.panel, -1, self.get_figure(None, None))
        sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, border=2)
        self.panel.SetSizer(sizer)

    def update_canvas(self, w: Optional[float] = None, h: Optional[float] = None):
        if w is None:
            w = max(8.0, self.panel.GetClientSize().GetWidth() / 100.0)
        if h is None:
            h = max(4.0, self.panel.GetClientSize().GetHeight() / 100.0)
        new_fig = self.get_figure(w, h)
        self.canvas.figure = new_fig
        self.canvas.draw()
        self.canvas.Refresh()

    def update_dates(self, start_date=None,
                     current_date=None,
                     end_date=None) -> None:
        if start_date is not None:
            self.start_date = start_date
        if current_date is not None:
            self.current_date = current_date
        if end_date is not None:
            self.end_date = end_date

    @staticmethod
    def last_day_of_month(year: int, month: int) -> date:
        """Return a date object set to the last day of the given month/year."""
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        first_of_next_month = date(next_year, next_month, 1)
        last_day = first_of_next_month - timedelta(days=1)
        return last_day

    @staticmethod
    def date_to_string(date_in: date) -> str:
        return f"{Chart.month_to_short_name(date_in.month)} {date_in.day} {date_in.year}"

    @staticmethod
    def month_to_short_name(month: int) -> str:
        if not 1 <= month <= 12:
            return "???"
        return date(2026, month, 1).strftime("%b")

class BarChart(Chart):
    def __init__(self,
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 y_units:Literal['MAF', 'TAF', 'AF', 'FT', 'CFS']='MAF',
                 show_title:bool=False,
                 percentage: float = 0.0,
                 ):
        super().__init__(start_date, current_date, end_date, y_units=y_units,
                         show_title=show_title, percentage=percentage)

    def final_layout(self, ax, title:Optional[str], names:List[str], x_pos:np.ndarray):
        ax.set_ylabel(self.y_units, fontsize=11.5, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10.5)
        ax.grid(axis='y', linestyle='--', alpha=0.65)
        ax.set_axisbelow(True)
        ax.set_ylim(0, self.y_max)