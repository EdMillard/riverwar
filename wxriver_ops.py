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
        super().__init__(None, title=title, size=wx.Size(1580, 1020))

        self.reservoirs = reservoirs

        # Main panel and notebook
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self.panel)

        # ==================== CAPACITY TAB ====================
        self.cap_panel = wx.Panel(self.notebook)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)

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

        self.capacity_fig = create_reservoir_chart(
            reservoirs,
            title=cap_title,
            power_head_zones=power_zones,
            reserved_zones=reserved_zones,
        )

        self.capacity_canvas = FigureCanvas(self.cap_panel, -1, self.capacity_fig)
        cap_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.cap_panel.SetSizer(cap_sizer)

        self.notebook.AddPage(self.cap_panel, "Capacity")

        # ==================== INFLOW / OUTFLOW TAB ====================
        self.in_panel = wx.Panel(self.notebook)
        in_sizer = wx.BoxSizer(wx.VERTICAL)

        self.inflow_fig = create_inflow_outflow_chart(reservoirs)

        self.inflow_canvas = FigureCanvas(self.in_panel, -1, self.inflow_fig)
        in_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.in_panel.SetSizer(in_sizer)

        self.notebook.AddPage(self.in_panel, "Inflow / Outflow")

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_cap_btn = wx.Button(self.panel, label="Save Capacity Chart as PNG")
        save_in_btn = wx.Button(self.panel, label="Save Inflow/Outflow Chart as PNG")

        save_cap_btn.Bind(wx.EVT_BUTTON, self.on_save_capacity)
        save_in_btn.Bind(wx.EVT_BUTTON, self.on_save_inflow)

        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(save_cap_btn, 0, wx.ALL, 10)
        btn_sizer.Add(save_in_btn, 0, wx.ALL, 10)
        btn_sizer.AddStretchSpacer(1)

        # Main layout
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=12)

        self.panel.SetSizer(main_sizer)

        self.CreateStatusBar()
        self.SetStatusText(f"Displaying {len(reservoirs)} reservoirs")
        self.SetMinSize(wx.Size(1220, 820))
        self.Centre()

        # Resize handling
        self.panel.Bind(wx.EVT_SIZE, self.on_panel_resize)
        wx.CallAfter(self.force_resize)
        wx.CallLater(100, self.force_resize)

    def force_resize(self):
        """Force canvases to resize properly inside notebook tabs"""
        for canvas, panel in [(self.capacity_canvas, self.cap_panel),
                              (self.inflow_canvas, self.in_panel)]:
            if canvas and panel:
                size = panel.GetClientSize()
                if size[0] > 200 and size[1] > 150:
                    canvas.SetClientSize(size)
                    canvas.draw()
                    canvas.Refresh()

    def on_panel_resize(self, event):
        wx.CallAfter(self.force_resize)
        event.Skip()

    def on_save_capacity(self, event):
        self.save_figure(self.capacity_fig, "Capacity_Chart")

    def on_save_inflow(self, event):
        self.save_figure(self.inflow_fig, "Inflow_Outflow_Chart")

    def save_figure(self, fig, base_name):
        default_name = f"{base_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        wildcard = "PNG files (*.png)|*.png|All files (*.*)|*.*"
        with wx.FileDialog(self, "Save chart as PNG",
                           defaultDir=os.getcwd(), defaultFile=default_name,
                           wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    fig.savefig(dlg.GetPath(), dpi=200, bbox_inches='tight')
                    wx.MessageBox("Chart saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    wx.MessageBox(str(e), "Save Error", wx.OK | wx.ICON_ERROR)


# Keep your existing create_capacity_chart and create_inflow_outflow_chart functions unchanged
# (They are already defined above in your original code)

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