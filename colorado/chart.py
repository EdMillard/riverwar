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
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from datetime import date
from typing import List

class Chart:
    """Complete ReservoirChart class with all original legends and deduplication"""

    def __init__(self,
                 reservoirs: List[Reservoir],
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 power_head_zones=None,
                 reserved_zones=None):

        self.reservoirs = reservoirs

        # Default values
        self.start_date = start_date or date(2025, 10, 1)
        self.current_date = current_date or date(2026, 4, 1)
        self.end_date = end_date or date(2026, 10, 1)
        self.power_head_zones = power_head_zones or []
        self.reserved_zones = reserved_zones or []

        self.width_inch = 14.8
        self.height_inch = 6.5
        self.fig = None

    def create_chart(self, ax:Axes, title:str):
        pass

    def _create_figure(self, width_inch=int | None, height_inch=int | None):
        if width_inch is not None and width_inch > 0:
            self.width_inch = width_inch
        # if height_inch is not None and height_inch > 0:
        #     self.height_inch = height_inch

        title = f'Reservoir Active Capacity - {self.month_to_short_name(self.current_month)} {self.current_year}'

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=100)
        ax = fig.add_subplot(111)

        self.create_chart(ax, title)

        fig.tight_layout(pad=1.2)
        fig.subplots_adjust(left=0.06, right=0.97, bottom=0.12, top=0.89)

        self.fig = fig
        return fig

    def update_dates(self, start_date=None,
                     current_date=None,
                     end_date=None) ->None:
        if start_date is not None: self.start_date = start_date
        if current_date is not None: self.current_date = current_date
        if end_date is not None: self.end_date = end_date

    def get_figure(self, width_inch=None, height_inch=None):
        return self._create_figure(width_inch, height_inch)

    @staticmethod
    def month_to_short_name(month: int) -> str:
        if not 1 <= month <= 12:
            return "???"
        return date(2026, month, 1).strftime("%b")