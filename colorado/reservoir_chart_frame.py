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
from reservoirs.reservoir import ReservoirRegistry, Reservoir
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

        reservoir = self.notebook_frame.reservoir_registry.get(selection)

        if reservoir:
            self.load_reservoir(reservoir)
            self.layout_charts()
            for chart in self.charts:
                chart.update_canvas(chart.width_inch, chart.height_inch)
            self.layout_charts()

            # Optional: Show a small status message
            #self.toolbar_status.SetLabel(f"Year: {self.current_year} | {selection}")
        else:
            wx.MessageBox(f"Failed to load {selection}", "Error", wx.ICON_ERROR)

    def load_charts(self):
        reservoir:Reservoir = self.notebook_frame.reservoir_registry.get('Lake Powell')
        self.load_reservoir(reservoir)

    def load_reservoir(self, reservoir:Reservoir) -> None:
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
        if  self.multi_bar_chart is None:
            self.multi_bar_chart = MultiBarChart(
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
        else:
            self.multi_bar_chart.groups = bar_groups
            self.multi_bar_chart.title = f"{reservoir.name} Inflow Outflow"