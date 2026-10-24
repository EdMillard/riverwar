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
from data_sets.demand import Demand
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
from chart.multi_bar_chart import MultiBarChart, BarGroup, BarSeries
import colorado.allb as all_b
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from api import df_utils
from typing import Optional

class DemandChartFrame(ChartFrame):
    """Base class that centralizes common initialization for pie-chart frames."""

    def __init__(self, notebook: NotebookFrame, demand: Demand,
                 name: str, start_year:int, end_year:int, version: float = 0.4):
        self.name = name
        self.start_year = start_year
        self.current_year = self.start_year
        self.end_year = end_year
        self.demand: Optional[Demand] = demand

        self.timer = None
        self.animation_interval = 1000
        self.version = version
        self.play_btn = None
        self.year_slider = None
        self.toolbar_status = None
        self.year_prev = 0

        self.demand_pie_chart: Optional[PieChart] = None
        self.multi_bar_chart: Optional[MultiBarChart] = None

        super().__init__(notebook, page_name=self.name)

    def create_reservoir_bar_chart(self):
        lake_powell = LakePowell(upstream=[])
        df_powell = lake_powell.load_data_annual(start_year=self.start_year)
        df_powell = df_utils.extend_years_with_zero(df_powell, 1906)

        lake_mead = LakeMead(upstream=[lake_powell])
        df_mead = lake_mead.load_data_annual(start_year=self.start_year)
        df_mead = df_utils.extend_years_with_zero(df_mead, 1906)

        mead_bar = BarGroup(
            label="=", series=[BarSeries(df=df_mead, col=all_b.STORAGE, color="maroon", label="Mead")]
        )
        powell_bar = BarGroup(
            label="=", series=[BarSeries(df=df_powell, col=all_b.STORAGE, color="royalblue", label="Powell")]
        )
        self.multi_bar_chart = MultiBarChart(
            percentage=0.15,
            groups=[mead_bar, powell_bar],
            title="",
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=27,
            y_min=3,
            show_x_labels=True
        )
        self.charts.append(self.multi_bar_chart)

    def on_line_moved(self, year):
        if year == self.current_year:
            return
        self.current_year = year
        if self.demand_pie_chart is not None:
            self.demand_pie_chart.update_for_year(self.current_year)
        if hasattr(self, 'toolbar_status') and self.toolbar_status is not None:
            self.toolbar_status.SetLabel(f"Year: {self.current_year}")