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
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.dates
import numpy as np
import pandas as pd
from PIL import Image
import io
from datetime import date, timedelta
from typing import List, Optional

class Chart:
    def __init__(self,
                 reservoirs: List[Reservoir],
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 percentage: float = 0.0
                 ):
        self.percentage = percentage
        self.canvas = None
        self.panel = None

        self.reservoirs = reservoirs

        self.report_name = ''

        # Default values
        self.start_date = start_date or date(2025, 10, 1)
        self.current_date = current_date or date(2026, 4, 1)
        self.end_date = end_date or date(2026, 9, 30)

        self.width_inch = 14.8
        self.height_inch = 6.5
        self.fig = None

        self.y_max = 10.0

    def create_chart(self, ax:Axes, title:str):
        pass

    def final_layout(self, ax, title:str, names:List[str], x_pos:np.ndarray):
        pass

    def create_figure(
            self,
            width_inch: Optional[int] = None,
            height_inch: Optional[int] = None
    ) -> Optional[Figure]:
        return None

    def get_figure(self, width_inch=None, height_inch=None):
        return self.create_figure(width_inch, height_inch)

    def save_figure(self)->Image.Image:
        buffer = io.BytesIO()
        self.canvas.figure.savefig(buffer, dpi=180, bbox_inches='tight', format='png')
        buffer.seek(0)
        image = Image.open(buffer)
        return image

    def update_report(self, report_name:str):
        self.report_name = report_name

    def create_panel(self, parent:wx.SplitterWindow|wx.Panel):
        self.panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.canvas = FigureCanvas(self.panel, -1,  self.get_figure(None, None))
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
                     end_date=None) ->None:
        if start_date is not None: self.start_date = start_date
        if current_date is not None: self.current_date = current_date
        if end_date is not None: self.end_date = end_date


    @staticmethod
    def last_day_of_month(year: int, month: int) -> date:
        """Return a date object set to the last day of the given month/year."""
        # Start with first day of next month, then subtract 1 day
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
    def date_to_string(date_in:date)->str:
        return f"{Chart.month_to_short_name(date_in.month)} {date_in.day} {date_in.year}"

    @staticmethod
    def month_to_short_name(month: int) -> str:
        if not 1 <= month <= 12:
            return "???"
        return date(2026, month, 1).strftime("%b")

class BarChart(Chart):
    def __init__(self,
                 reservoirs: List[Reservoir],
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None
                 ):
        super().__init__(reservoirs, start_date, current_date, end_date)

    def final_layout(self, ax, title:str, names:List[str], x_pos:np.ndarray):
        ax.set_ylabel('Volume (Million Acre-Feet)', fontsize=11.5, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10.5)
        ax.grid(axis='y', linestyle='--', alpha=0.65)
        ax.set_axisbelow(True)
        ax.set_ylim(0, self.y_max)