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

        if self.toolbar is not None:
            self.toolbar.Hide()

    def create_reservoir_bar_chart(self, show_x_labels=True):
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
            show_x_labels=show_x_labels,
            legend_loc='upper left',
        )
        self.charts.append(self.multi_bar_chart)

    def on_line_moved(self, year, shift=False):
        if getattr(self, '_syncing_lines', False):
            return
        if not shift and year == self.current_year:
            return

        self.current_year = year
        self._syncing_lines = True
        try:
            for chart in self.charts:
                if chart is None:
                    continue
                year_to_idx = getattr(chart, 'year_to_idx', None)
                if not year_to_idx or year not in year_to_idx:
                    continue

                if shift and hasattr(chart, 'add_annotation_set'):
                    chart.add_annotation_set(year)
                else:
                    idx = year_to_idx[year]
                    if hasattr(chart, '_vline') and chart._vline is not None:
                        chart._vline.set_xdata([idx, idx])
                    if getattr(chart, '_show_year_label', False):
                        chart._update_year_label(idx)
                    if getattr(chart, '_show_bar_values', False):
                        chart._update_bar_value_labels(idx)
                    if hasattr(chart, 'fig') and chart.fig is not None:
                        chart.fig.canvas.draw_idle()
        finally:
            self._syncing_lines = False