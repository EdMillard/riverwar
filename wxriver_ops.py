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
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib
import datetime
import colorado.lb as lb
from datetime import datetime
import os
import pandas as pd
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
from reservoirs.lake_pleasant import LakePleasant
from colorado.graph_inflow_outflow import create_inflow_outflow_chart
from colorado.graph_reservoirs import create_reservoir_chart


os.environ['QT_QPA_PLATFORM'] = 'offscreen'      # Most important for Qt errors
os.environ['MPLBACKEND'] = 'Agg'                 # Non-interactive matplotlib backend
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'


def datetime64_to_str(dt64) -> str:
    """Convert pandas datetime64 to 'Mar 28, 2026' format"""
    if pd.isna(dt64):
        return ""
    dt = pd.to_datetime(dt64)
    return dt.strftime("%b %d, %Y")

class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoirs, date_time, title="Reservoir Analysis Dashboard"):
        # Get screen size platform-independently
        screen_w, screen_h = wx.DisplaySize()
        window_height = screen_h - 64
        window_width = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.reservoirs = reservoirs

        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self.panel)

        # ==================== CREATE FIGURES FIRST ====================
        date_str = datetime64_to_str(date_time)
        cap_title = f'Reservoir Storage - {date_str} AM - USBR RISE'

        power_zones = [
            (Reservoir.high_power_pool_color, 'Full Power Head'),
            (Reservoir.low_power_pool_color, 'Low Power Head'),
            (Reservoir.non_power_pool_color, 'Limited Access')
        ]

        reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]

        # Create figures BEFORE canvases
        self.capacity_fig = create_reservoir_chart(
            reservoirs,
            title=cap_title,
            power_head_zones=power_zones,
            reserved_zones=reserved_zones,
        )

        self.inflow_fig = create_inflow_outflow_chart(reservoirs)

        # ==================== COMBINED DASHBOARD PAGE ====================
        self.combined_panel = wx.Panel(self.notebook)
        splitter = wx.SplitterWindow(self.combined_panel, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        splitter.SetMinimumPaneSize(400)

        # Top: Capacity
        self.cap_panel = wx.Panel(splitter)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)
        self.capacity_canvas = FigureCanvas(self.cap_panel, -1, self.capacity_fig)
        cap_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.cap_panel.SetSizer(cap_sizer)

        # Bottom: Inflow/Outflow
        self.in_panel = wx.Panel(splitter)
        in_sizer = wx.BoxSizer(wx.VERTICAL)
        self.inflow_canvas = FigureCanvas(self.in_panel, -1, self.inflow_fig)
        in_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.in_panel.SetSizer(in_sizer)

        splitter.SplitHorizontally(self.cap_panel, self.in_panel)
        splitter.SetSashPosition(int(window_height * 0.52))

        combined_sizer = wx.BoxSizer(wx.VERTICAL)
        combined_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, border=8)
        self.combined_panel.SetSizer(combined_sizer)

        self.notebook.AddPage(self.combined_panel, "Reservoir Dashboard")

        # ==================== THIN BOTTOM TOOLBAR ====================
        bottom_toolbar = wx.Panel(self.panel, style=wx.BORDER_NONE)

        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.status_text = wx.StaticText(
            bottom_toolbar,
            label=f"Displaying {len(reservoirs)} reservoirs"
        )
        tb_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=15)

        tb_sizer.AddStretchSpacer(1)

        self.save_btn = wx.Button(bottom_toolbar, label="Save Combined Dashboard as PNG")
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_combined)
        tb_sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=15)

        bottom_toolbar.SetSizer(tb_sizer)

        # === Aggressive thin toolbar fix ===
        bottom_toolbar.SetMinSize(wx.Size(-1, 36))  # Fixed small height
        bottom_toolbar.SetMaxSize(wx.Size(-1, 42))
        bottom_toolbar.Layout()

        # Main layout
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(bottom_toolbar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=6)

        self.panel.SetSizer(main_sizer)

        self.CreateStatusBar()
        self.SetStatusText("")

        self.SetMinSize(wx.Size(1100, 900))
        self.Centre()

    def on_save_combined(self, event):
        default_name = f"Reservoir_Dashboard_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with wx.FileDialog(self, "Save Combined Dashboard as PNG",
                           defaultDir=os.getcwd(), defaultFile=default_name,
                           wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    # Save the notebook page (best quality)
                    self.capacity_fig.savefig(dlg.GetPath(), dpi=200, bbox_inches='tight')
                    wx.MessageBox("Dashboard saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    wx.MessageBox(str(e), "Save Error", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    # lake_pleasant = LakePleasant()
    lake_powell = LakePowell()

    reservoirs = [
        Imperial(),
        # lake_pleasant,
        LakeHavasu(),
        LakeMohave(),
        Aquifers(),
        LakeMead(),
        lake_powell,
        FlamingGorge(),
        Navajo(),
        BlueMesa()
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs, lake_powell.date_time)
    frame.Show()
    app.MainLoop()