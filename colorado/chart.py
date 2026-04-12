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
from typing import List, Optional

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

    def create_figure(
            self,
            width_inch: Optional[int] = None,
            height_inch: Optional[int] = None
    ) -> Optional[Figure]:
        return None

    def update_dates(self, start_date=None,
                     current_date=None,
                     end_date=None) ->None:
        if start_date is not None: self.start_date = start_date
        if current_date is not None: self.current_date = current_date
        if end_date is not None: self.end_date = end_date

    def get_figure(self, width_inch=None, height_inch=None):
        return self.create_figure(width_inch, height_inch)

    @staticmethod
    def month_to_short_name(month: int) -> str:
        if not 1 <= month <= 12:
            return "???"
        return date(2026, month, 1).strftime("%b")