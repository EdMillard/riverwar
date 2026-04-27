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
from datetime import datetime
from pathlib import Path
import re
import wx
import matplotlib
import os
from typing import List
from chart.chart_frame import NotebookFrame
from colorado.river_war import RiverWar
from data_sets.data_set import DataSetRegistry
from colorado.flow_chart_frame import FlowChartFrame
from colorado.pie_chart_frame import PieChartFrame
from colorado.reservoir_chart_frame import ReservoirChartFrame
from colorado.reservoirs_chart_frame import ReservoirsChartFrame
from colorado.time_series_chart_frame import TimeSeriesChartFrame
from reservoirs.reservoir import ReservoirRegistry
from reservoirs.imperial import Imperial
from reservoirs.lake_havasu import LakeHavasu
from reservoirs.lake_mohave import LakeMohave
from reservoirs.aquifers import Aquifers
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from reservoirs.blue_mesa import BlueMesa
from reservoirs.navajo import Navajo

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

    return filter_and_sort_usbr_reports(matching_dirs)


def filter_and_sort_usbr_reports(paths):
    def get_sort_key(path_str):
        path = str(path_str)
        # Extract year and month code (only for main reports)
        match = re.search(r'/(\d{4})/([A-Z]{3}\d{2})$', path)  # Note: $ ensures nothing after month code
        if not match:
            return datetime.min, path

        year = int(match.group(1))
        month_code = match.group(2)

        try:
            dt = datetime.strptime(month_code, '%b%y').replace(year=year)
        except ValueError:
            dt = datetime.min

        return dt, path

    # First filter: keep only paths that do NOT have _XXX after the month/year
    filtered = [p for p in paths if re.search(r'/(\d{4})/[A-Z]{3}\d{2}$', str(p))]

    # Then sort chronologically
    return sorted(filtered, key=get_sort_key)

def time_series_chart(notebook_frame:NotebookFrame):
    reports = find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')

    flaming_gorge = FlamingGorge()
    lake_powell = LakePowell(upstream=[flaming_gorge])
    lake_mead = LakeMead(upstream=[lake_powell])

    reservoirs = [
        flaming_gorge,
        lake_powell,
        lake_mead,
    ]
    frame = TimeSeriesChartFrame(notebook_frame, reservoirs, lake_powell.date_time, reports)
    frame.Show()

def reservoir_chart(notebook_frame:NotebookFrame):
    frame = ReservoirChartFrame(notebook_frame)
    frame.Show()

def reservoirs_chart(notebook_frame:NotebookFrame):
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

    frame = ReservoirsChartFrame(notebook_frame, reservoirs=reservoirs, reports=reports)
    frame.Show()

def pie_chart(notebook_frame:NotebookFrame):
    frame = PieChartFrame(notebook_frame)
    frame.Show()

def flow_chart(notebook_frame:NotebookFrame):
    frame = FlowChartFrame(notebook_frame)
    frame.Show()

# ==================== RUN ====================
if __name__ == "__main__":

    callables = [
        ("Reservoir", reservoir_chart),
        ("Reservoirs", reservoirs_chart),
        ("Demand", pie_chart),
        ("Flow", flow_chart),
        ("Inflow Outflow", time_series_chart),
    ]

    reservoir_registry = ReservoirRegistry("reservoirs")
    dataset_registry = DataSetRegistry("data_sets")

    # print("\nLoaded Reservoirs:")
    # for name in reservoir_registry.list_all():
    #     print(f"   • {name}")
    reservoir_registry.get("Lake Powell")

    app = wx.App(False)

    river_war = RiverWar(reservoir_registry, dataset_registry)
    nb = NotebookFrame(callables, river_war)

    # reservoir_chart(nb)
    pie_chart(nb)
    # reservoirs_chart(nb)
    # time_series_chart(nb)

    nb.Show()
    app.MainLoop()