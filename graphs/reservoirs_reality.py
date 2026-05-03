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
# from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
from chart.chart_frame import ChartFrame, NotebookFrame
from reservoirs.imperial import Imperial
from reservoirs.roosevelt import Roosevelt
from reservoirs.lake_pleasant import LakePleasant
from reservoirs.lake_havasu import LakeHavasu
from reservoirs.lake_mohave import LakeMohave
from reservoirs.aquifers import Aquifers
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from reservoirs.blue_mesa import BlueMesa
from reservoirs.navajo import Navajo

class ReservoirsReality(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')

        flaming_gorge = FlamingGorge()
        navajo = Navajo()
        blue_mesa = BlueMesa()
        lake_powell = LakePowell(upstream=[flaming_gorge, blue_mesa, navajo])
        lake_mead = LakeMead(upstream=[lake_powell])
        lake_mohave = LakeMohave(upstream=[lake_mead])
        lake_havasu = LakeHavasu(upstream=[lake_mohave])
        imperial = Imperial(upstream=[lake_havasu])
        lake_pleasant = LakePleasant(upstream=[])
        roosevelt = Roosevelt(upstream=[])
        aquifers = Aquifers(upstream=[])

        reservoirs = [
            imperial, aquifers, roosevelt, lake_pleasant, lake_havasu, lake_mohave,
            lake_mead, lake_powell, flaming_gorge, navajo, blue_mesa
        ]

        super().__init__(notebook_frame, reservoirs=reservoirs, reports=reports, page_name='Reservoir Reality')

    def load_charts(self):
        start = self.start_nav.current_date
        # current = self.current_nav.current_date
        end = self.end_nav.current_date

        reservoir_chart = ReservoirChart(
            self.reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end
        )
        self.charts.append(reservoir_chart)

        # inflow_chart = InflowOutflowChart(
        #    self.reservoirs, start_date=start, current_date=current, end_date=end
        # )
        # self.charts.append(inflow_chart)
