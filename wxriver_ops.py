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
from pathlib import Path
import wx
import matplotlib
from datetime import date
import os
from typing import List
from reservoirs.reservoir import Reservoir
from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
from chart.chart_frame import ChartFrame

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

def find_directories_with_file(root_dir: str, filename: str) -> List[str]:
    """Return list of directories containing the given filename."""
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    matching_dirs = []
    for dir_path in root.rglob("*"):
        if dir_path.is_dir():
            if (dir_path / filename).is_file():
                matching_dirs.append(str(dir_path.resolve()))

    return sorted(set(matching_dirs))


# ==================== MAIN FRAME ====================

class ReservoirChartFrame(ChartFrame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):
        super().__init__(reservoir_list, date_time, report_list, title)

    def load_charts(self):
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        reservoir_chart = ReservoirChart(
            reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end
        )
        self.charts.append(reservoir_chart)

        inflow_chart = InflowOutflowChart(
            reservoirs, start_date=start, current_date=current, end_date=end
        )
        self.charts.append(inflow_chart)

# ==================== RUN ====================
if __name__ == "__main__":
    from reservoirs.reservoir import Reservoir
    from reservoirs.imperial import Imperial
    from reservoirs.lake_havasu import LakeHavasu
    from reservoirs.lake_mohave import LakeMohave
    from reservoirs.aquifers import Aquifers
    from reservoirs.lake_mead import LakeMead
    from reservoirs.lake_powell import LakePowell
    from reservoirs.flaming_gorge import FlamingGorge
    from reservoirs.blue_mesa import BlueMesa
    from reservoirs.navajo import Navajo

    reports = find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')

    flaming_gorge = FlamingGorge()
    navajo = Navajo()
    blue_mesa = BlueMesa()
    lake_powell = LakePowell(upstream=[flaming_gorge, blue_mesa, navajo])
    lake_mead = LakeMead(upstream=[lake_powell])
    lake_mohave = LakeMohave(upstream=[lake_mead])
    lake_havasu = LakeHavasu(upstream=[lake_mohave])
    imperial = Imperial(upstream=[lake_havasu])
    aquifers = Aquifers(upstream=[])

    reservoirs = [
        imperial, aquifers, lake_havasu, lake_mohave,
        lake_mead, lake_powell, flaming_gorge, navajo, blue_mesa
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs, lake_powell.date_time, reports)
    frame.Show()
    app.MainLoop()