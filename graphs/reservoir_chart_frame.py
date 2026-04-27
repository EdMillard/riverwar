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
from typing import Optional
from dateutil.utils import today
from reservoirs.reservoir import Reservoir
from chart.line_chart import LineChart
from chart.multi_bar_chart import MultiBarChart
from chart.chart_frame import ChartFrame, NotebookFrame
import colorado.allb as all_b

class ReservoirChartFrame(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.start_year = 1971
        self.end_year = 2024
        self.multi_bar_chart: Optional[MultiBarChart] = None
        super().__init__(notebook_frame, page_name='Pie Chart')

    def create_toolbar(self):
        super().create_toolbar()

        reservoir_names = self.notebook_frame.reservoir_registry.list_all()
        self.reservoir_choice = wx.Choice(self.toolbar, choices=reservoir_names)

        if reservoir_names:
            self.reservoir_choice.SetSelection(0)  # Select first item by default

        self.reservoir_choice.SetMinSize(wx.Size(180, -1))
        self.reservoir_choice.Bind(wx.EVT_CHOICE, self.on_reservoir_selected)
        self.toolbar.GetSizer().Add(self.reservoir_choice, 0, wx.ALL | wx.CENTER, border=8)

    def on_reservoir_selected(self, event):
        """Called when user chooses a reservoir from the option menu"""
        selection = self.reservoir_choice.GetStringSelection()
        if not selection:
            return

        reservoir = self.notebook_frame.river_war.reservoir.get(selection)
        if not reservoir:
            wx.MessageBox(f"Failed to load {selection}", "Error", wx.ICON_ERROR)
            return

        # Just load it — let your existing method do the work
        self.load_reservoir(reservoir)

        # Then rebuild the visual layout
        self.rebuild_chart_layout()

        # Final refresh
        wx.CallAfter(self.final_full_layout)

        print(f"Switched to reservoir: {selection}")

    def load_charts(self):
        reservoir:Reservoir = self.notebook_frame.river_war.reservoir.get('Lake Powell')
        self.load_reservoir(reservoir)

    def load_reservoir(self, reservoir:Reservoir) -> None:

        self.charts.clear()
        df = reservoir.load_data_annual()

        # ============= INFLOW OUTFLOW BAR CHART ==============
        bar_groups = [
            ('Release', [
                (df, all_b.RELEASE, 'darkred'),
                (df, all_b.EVAPORATION, 'goldenrod')
            ]),
            ('Inflow', [
                (df, all_b.INFLOW, 'royalblue')
            ]),
        ]
        self.multi_bar_chart = MultiBarChart(
            percentage=0.30,
            groups=bar_groups,
            # underlay_lines=underlay_lines,
            # overlay_lines=overlay_lines,
            title=f"{reservoir.name} Inflow Outflow",
            start_year=self.start_year,
            end_year=self.end_year,
            # x_min=1999,
            # y_max=16.0
        )
        self.charts.append(self.multi_bar_chart)

        date_today = today()
        df_daily = reservoir.load_data_daily(start_year=2021, end_year=2026)
        time_series = [
            (df_daily, all_b.STORAGE, 'royalblue')
        ]
        line_chart = LineChart(
            time_series, title='',
            percentage=0.25,
            start_date=reservoir.start_date,
            current_date=date_today,
            end_date=date_today,
            show_x_labels=False
        )
        self.charts.append(line_chart)

        time_series = [
            (df_daily, all_b.RELEASE, 'darkred'),
            (df_daily, all_b.INFLOW, 'royalblue'),
            # (df_daily, all_b.EVAPORATION, 'goldenrod')
        ]
        line_chart = LineChart(
            time_series, title='',
            percentage=0.25,
            y_units='CFS',
            start_date=reservoir.start_date,
            current_date=date_today,
            end_date=date_today,
            show_x_labels=False
        )
        self.charts.append(line_chart)

        time_series = [
            (df_daily, all_b.STORAGE_DELTA, 'royalblue'),
            # (df_daily, all_b.INFLOW, 'royalblue'),
            # (df_daily, all_b.EVAPORATION, 'goldenrod')
        ]
        line_chart = LineChart(
            time_series, title='',
            percentage=0.25,
            start_date=reservoir.start_date,
            current_date=date_today,
            end_date=date_today,
        )
        self.charts.append(line_chart)