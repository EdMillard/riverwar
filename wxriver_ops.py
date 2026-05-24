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
import matplotlib
import os
from graphs.chart_frame import NotebookFrame
from colorado.river_war import RiverWar
from data_sets.data_set import DataSetRegistry
from graphs.flow_chart_frame import FlowChartFrame
from graphs.front_range import FrontRange
from graphs.grand_valley import GrandValley
from graphs.supply_v_demand import SupplyVDemand
from graphs.reservoir_chart_frame import ReservoirChartFrame
from graphs.reservoirs_reality import ReservoirsReality
from graphs.time_series_chart_frame import TimeSeriesChartFrame
from graphs.reservoirs_big3 import ReservoirsBig3
from reservoirs.reservoir import ReservoirRegistry

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

def time_series_chart(notebook_frame:NotebookFrame):
    frame = TimeSeriesChartFrame(notebook_frame)
    frame.Show()

def reservoir_reality_chart(notebook_frame:NotebookFrame):
    frame = ReservoirsReality(notebook_frame)
    frame.Show()

def reservoirs_big3(notebook_frame:NotebookFrame):
    frame = ReservoirsBig3(notebook_frame)
    frame.Show()

def front_range(notebook_frame:NotebookFrame):
    frame = FrontRange(notebook_frame)
    frame.Show()

def grand_valley(notebook_frame:NotebookFrame):
    frame = GrandValley(notebook_frame)
    frame.Show()

def reservoir_chart(notebook_frame:NotebookFrame):
    frame = ReservoirChartFrame(notebook_frame)
    frame.Show()

def supply_v_demand(notebook_frame:NotebookFrame):
    frame = SupplyVDemand(notebook_frame)
    frame.Show()

def flow_chart(notebook_frame:NotebookFrame):
    frame = FlowChartFrame(notebook_frame)
    frame.Show()

# ==================== RUN ====================
if __name__ == "__main__":

    callables = [
        ("Reservoir", reservoir_chart),
        ("Reservoir Reality", reservoir_reality_chart),
        ("Supply v Demand", supply_v_demand),
        ("Flow", flow_chart),
        ("Reservoirs Big3", reservoirs_big3),
        ("Inflow Outflow", time_series_chart),
    ]

    reservoir_registry = ReservoirRegistry("reservoirs")
    dataset_registry = DataSetRegistry("data_sets")

    # print("\nLoaded Reservoirs:")
    # for name in reservoir_registry.list_all():
    #     print(f"   • {name}")
    # reservoir_registry.get("Lake Powell")

    app = wx.App(False)

    river_war = RiverWar(reservoir_registry, dataset_registry)
    nb = NotebookFrame(callables, river_war)

    # reservoir_chart(nb)
    # supply_v_demand(nb)
    # reservoir_reality_chart(nb)
    # reservoirs_big3(nb)
    # front_range(nb)
    grand_valley(nb)

    nb.Show()
    app.MainLoop()