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
from typing import List, Optional
from reservoirs.reservoir import Reservoir
from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
from chart.chart_frame import ChartFrame, NotebookFrame

class ReservoirsChartFrame(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame,
                 reservoirs: Optional[List[Reservoir] | None] = None,
                 reports: List[str] | None = None):
        super().__init__(notebook_frame, reservoirs=reservoirs, reports=reports, page_name='Reservoirs')

    def load_charts(self):
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        reservoir_chart = ReservoirChart(
            self.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end
        )
        self.charts.append(reservoir_chart)

        inflow_chart = InflowOutflowChart(
            self.reservoirs, start_date=start, current_date=current, end_date=end
        )
        self.charts.append(inflow_chart)
