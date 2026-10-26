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
from data_sets.demand import Demand, Colors
from demand_chart_frame import DemandChartFrame
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
from colorado.river_war import RiverWar
import colorado.lb as lb

class Compact1922(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame, demand,
                         name='Compact', start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        series = [
            (7_500_000, "Upper Basin", Colors.UT),
            (750_000, "Mexico", lb.MX_COLOR),
            (7_500_000, "Lower Basin", Colors.CA1),
            (1_000_000, "III(b)", Colors.CA2),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River Compact {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1922)

class Compact1929(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame, demand,
                         name='Boulder Canyon Project Act',  start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        series = [
            (7_500_000, "Upper Basin", Colors.UT),
            (750_000, "Mexico", lb.MX_COLOR),
            (4_400_000, "CA", Colors.CA1),
            (1_000_000, "III(b)", Colors.CA2),
            (300_000, "NV", Colors.NV2),
            (2_800_000, "AZ", Colors.AZ1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1929)

class Compact1944(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame, demand,
                         name='Mexico Treaty',  start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        series = [
            (7_500_000, "Upper Basin", Colors.UT),
            (1_500_000, "Mexico", lb.MX_COLOR),
            (4_400_000, "CA", Colors.CA1),
            (1_000_000, "III(b)", Colors.CA2),
            (300_000, "NV", Colors.NV2),
            (2_800_000, "AZ", Colors.AZ1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1944)


if __name__ == "__main__":
    app = wx.App(False)

    rw = RiverWar()
    nf = NotebookFrame([], rw)

    # d = Demand(rw, show_tributaries=False)

    Compact1922(nf, None)
    Compact1929(nf, None)
    Compact1944(nf, None)

    nf.Show()
    app.MainLoop()