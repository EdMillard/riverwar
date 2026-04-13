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
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib
from datetime import date
import os
import pandas as pd
import wx.lib.buttons as buttons
from typing import List
from reservoirs.reservoir import Reservoir
from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
import colorado.lb as lb

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

arrow_fg = wx.Colour(150, 150, 150)  # Darker gray

class MonthYearNavigator(wx.Panel):
    """Reusable single month/year navigator with smaller raised buttons"""
    def __init__(self, parent, initial_month: int, initial_year: int, on_changed=None, name=""):
        super().__init__(parent, style=wx.BORDER_NONE)

        self.name = name                    # "start", "current", or "end"
        self.current_date:date = date(initial_year, initial_month, 1)
        self.on_changed = on_changed

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)
        arrow_fg = wx.Colour(160, 160, 160)

        # Smaller buttons
        self.btn_left = buttons.GenButton(self, label="◀", size=wx.Size(34, 32))
        self.btn_left.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_left.SetForegroundColour(arrow_fg)
        self.btn_left.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.btn_left.SetBezelWidth(3)
        self.btn_left.SetUseFocusIndicator(False)
        self.btn_left.Bind(wx.EVT_BUTTON, self._on_left)
        sizer.Add(self.btn_left, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)

        # Smaller date text
        self.date_text = wx.StaticText(self, label="")
        self.date_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.date_text.SetForegroundColour(wx.Colour(230, 230, 230))
        sizer.Add(self.date_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=12)

        # Right arrow
        self.btn_right = buttons.GenButton(self, label="▶", size=wx.Size(34, 32))
        self.btn_right.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_right.SetForegroundColour(arrow_fg)
        self.btn_right.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.btn_right.SetBezelWidth(3)
        self.btn_right.SetUseFocusIndicator(False)
        self.btn_right.Bind(wx.EVT_BUTTON, self._on_right)
        sizer.Add(self.btn_right, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=6)

        self.SetSizer(sizer)
        self.SetBackgroundColour(bg)
        self._update_display()

    def _update_display(self):
        month_name = self.current_date.strftime("%b")
        self.date_text.SetLabel(f"{month_name} {self.current_date.year}")

    def _on_left(self, event):
        month = self.current_date.month - 1
        year = self.current_date.year
        if month < 1:
            month = 12
            year -= 1
        self.current_date = date(year, month, 1)
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name,  self.current_date)

    def _on_right(self, event):
        month = self.current_date.month + 1
        year = self.current_date.year

        if month > 12:
            month = 11
            year += 1
        self.current_date = date(year, month, 1)
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_date)


# ==================== MAIN FRAME ====================
class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Reservoir Analysis Dashboard"):

        screen_w, screen_h = wx.DisplaySize()
        window_height = screen_h - 64
        window_width = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.reservoirs = reservoir_list
        self.report_list = report_list  # Store for later use

        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ==================== TOP TOOLBAR ====================
        top_toolbar = wx.Panel(self.panel, style=wx.BORDER_NONE)
        top_toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_text = wx.StaticText(
            top_toolbar,
            label=f"Displaying {len(reservoirs)} reservoirs"
        )
        tb_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=15)

        tb_sizer.AddStretchSpacer(1)

        # ==================== REPORT DIRECTORY SELECTOR ====================
        if report_list and len(report_list) > 0:
            # Show only directory names (not full paths)
            dir_names = [Path(p).name for p in report_list]

            self.report_choice = wx.Choice(top_toolbar, choices=dir_names)
            self.report_choice.SetSelection(len(dir_names) - 2)
            self.report_path = self.report_list[len(dir_names) - 2]
            self.report_choice.SetToolTip("Select report directory")
            self.report_choice.Bind(wx.EVT_CHOICE, self.on_report_selected)

            tb_sizer.Add(self.report_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=15)
        else:
            self.report_choice = None

        # ==================== DATE NAVIGATORS ====================
        self.start_nav = MonthYearNavigator(top_toolbar, 10, 2025, self.on_date_changed, name="start")
        tb_sizer.Add(self.start_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        tb_sizer.AddSpacer(25)

        self.current_nav = MonthYearNavigator(top_toolbar, 4, 2026, self.on_date_changed, name="current")
        tb_sizer.Add(self.current_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        tb_sizer.AddSpacer(25)

        self.end_nav = MonthYearNavigator(top_toolbar, 10, 2026, self.on_date_changed, name="end")
        tb_sizer.Add(self.end_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        # ==================== GLOBAL ARROWS ====================
        global_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.global_left = buttons.GenButton(top_toolbar, label="◀◀", size=wx.Size(38, 32))
        self.global_left.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.global_left.SetForegroundColour(arrow_fg)
        self.global_left.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.global_left.SetBezelWidth(3)
        self.global_left.SetUseFocusIndicator(False)
        self.global_left.Bind(wx.EVT_BUTTON, self._on_global_left)
        global_sizer.Add(self.global_left, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=12)

        separator = wx.StaticLine(top_toolbar, style=wx.LI_VERTICAL)
        separator.SetSize(wx.Size(2, 28))
        global_sizer.Add(separator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=8)

        self.global_right = buttons.GenButton(top_toolbar, label="▶▶", size=wx.Size(38, 32))
        self.global_right.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.global_right.SetForegroundColour(arrow_fg)
        self.global_right.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.global_right.SetBezelWidth(3)
        self.global_right.SetUseFocusIndicator(False)
        self.global_right.Bind(wx.EVT_BUTTON, self._on_global_right)
        global_sizer.Add(self.global_right, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=12)

        tb_sizer.Add(global_sizer, 0, wx.ALIGN_CENTER_VERTICAL)

        tb_sizer.AddStretchSpacer(1)

        # Save Button
        self.save_btn = wx.Button(top_toolbar, label="Save", size=wx.Size(-1, 28))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_combined)
        tb_sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=15)

        top_toolbar.SetSizer(tb_sizer)
        top_toolbar.SetMinSize(wx.Size(-1, 42))

        # ==================== CREATE CHARTS ====================
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

        # Load reservoir data
        self.load_reservoirs()
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        self.reservoir_chart = ReservoirChart(
            reservoirs,
            start_date=start,
            current_date=current,
            end_date=end,
            power_head_zones=power_zones,
            reserved_zones=reserved_zones
        )

        self.inflow_chart = InflowOutflowChart(
            reservoirs,
            start_date=start,
            current_date=current,
            end_date=end
        )

        # ==================== NOTEBOOK & SPLITTER ====================
        self.notebook = wx.Notebook(self.panel)

        self.combined_panel = wx.Panel(self.notebook)
        self.splitter = wx.SplitterWindow(self.combined_panel,
                                          style=wx.SP_THIN_SASH | wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        self.splitter.SetMinimumPaneSize(200)

        # Reservoir panel
        self.reservoir_panel = wx.Panel(self.splitter)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)
        self.reservoir_canvas = FigureCanvas(self.reservoir_panel, -1,
                                             self.reservoir_chart.get_figure(None, None))
        cap_sizer.Add(self.reservoir_canvas, 1, wx.EXPAND | wx.ALL, border=6)
        self.reservoir_panel.SetSizer(cap_sizer)

        # Inflow panel
        self.in_panel = wx.Panel(self.splitter)
        in_sizer = wx.BoxSizer(wx.VERTICAL)
        self.inflow_canvas = FigureCanvas(self.in_panel, -1,
                                          self.inflow_chart.get_figure(None, None))
        in_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, border=6)
        self.in_panel.SetSizer(in_sizer)

        self.splitter.SplitHorizontally(self.reservoir_panel, self.in_panel)

        combined_sizer = wx.BoxSizer(wx.VERTICAL)
        combined_sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, border=4)
        self.combined_panel.SetSizer(combined_sizer)

        self.notebook.AddPage(self.combined_panel, "Reservoir Dashboard")

        # Main layout
        main_sizer.Add(top_toolbar, 0, wx.EXPAND | wx.ALL, border=0)
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=4)

        self.panel.SetSizer(main_sizer)
        self.panel.Layout()

        self.SetMinSize(wx.Size(1100, 900))
        self.Centre()

        wx.CallAfter(self.panel.Layout)

    def load_reservoirs(self)->None:
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date
        for reservoir in self.reservoirs:
            reservoir.load_data(Path(self.report_path), start, current, end)

    def on_report_selected(self, event):
        """Callback when user selects a different report directory"""
        if self.report_choice is None:
            return
        selected_index = self.report_choice.GetSelection()
        self.report_path = self.report_list[selected_index]
        print(f"Selected report directory: {Path(self.report_path).name}  ({self.report_path})")
        self.load_reservoirs()

    def on_date_changed(self, which: str, date: date | None):
        """One single redraw for ANY date change"""
        print(f"Date changed → {which}")
        self.load_reservoirs()

        if which == "start":
            self.reservoir_chart.update_dates(start_date=date)
            self.inflow_chart.update_dates(start_date=date)
        elif which == "current":
            self.reservoir_chart.update_dates(current_date=date)
            self.inflow_chart.update_dates(current_date=date)
        elif which == "end":
            self.reservoir_chart.update_dates(end_date=date)
            self.inflow_chart.update_dates(end_date=date)
        else:
            # "global" does nothing extra - it just triggers the final redraw
            pass
        self._update_reservoir_canvas()
        self._update_inflow_canvas()

    def _update_reservoir_canvas(self):
        """Redraw with current panel width"""
        if not hasattr(self, 'reservoir_canvas'):
            return

        panel_width_inch = max(8.0, self.in_panel.GetClientSize().GetWidth() / 100.0)
        panel_height_inch = max(4.0, self.in_panel.GetClientSize().GetHeight() / 100.0)

        new_fig = self.reservoir_chart.get_figure(panel_width_inch, panel_height_inch)

        self.reservoir_canvas.figure = new_fig
        self.reservoir_canvas.draw()
        self.reservoir_canvas.Refresh()

        self.in_panel.Layout()
        self.splitter.Layout()

    def _update_inflow_canvas(self):
        """Redraw with current panel width"""
        if not hasattr(self, 'inflow_canvas'):
            return

        panel_width_inch = max(8.0, self.in_panel.GetClientSize().GetWidth() / 100.0)
        panel_height_inch = max(4.0, self.in_panel.GetClientSize().GetHeight() / 100.0)

        new_fig = self.inflow_chart.get_figure(panel_width_inch, panel_height_inch)

        self.inflow_canvas.figure = new_fig
        self.inflow_canvas.draw()
        self.inflow_canvas.Refresh()

        self.in_panel.Layout()
        self.splitter.Layout()

    # ==================== GLOBAL ARROW CALLBACKS ====================

    def _on_global_change(self, delta:int):

        for nav in (self.start_nav, self.current_nav, self.end_nav):
            month = nav.current_date.month + delta
            year = nav.current_date.year
            if delta < 0:
                if month < 1:
                    month = 12
                    year -= 1
            else:
                if month > 12:
                    month = 1
                    year += 1
            nav.current_date = date(year, month, 1)
            nav._update_display()

        self.load_reservoirs()

        # Now update the chart with the new values from all three
        self.inflow_chart.update_dates(
            start_date=self.start_nav.current_date,
            current_date=self.current_nav.current_date,
            end_date=self.end_nav.current_date,
        )
        self._update_inflow_canvas()

        self.reservoir_chart.update_dates(
            start_date=self.start_nav.current_date,
            current_date=self.current_nav.current_date,
            end_date=self.end_nav.current_date,
        )
        self._update_reservoir_canvas()

    def _on_global_left(self, event):
        """Shift all three dates back by one month - single redraw"""
        self._on_global_change(-1)

    def _on_global_right(self, event):
        """Shift all three dates forward by one month - single redraw"""
        self._on_global_change(1)

    # ==================== SAVE CALLBACKS ====================
    def on_save_combined(self, event):
        default_name = f"Reservoir_Dashboard_{date.today().strftime('%Y%m%d_%H%M%S')}.png"
        with wx.FileDialog(self, "Save Combined Dashboard as PNG",
                           defaultDir=os.getcwd(), defaultFile=default_name,
                           wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    self.reservoir_canvas.figure.savefig(dlg.GetPath(), dpi=200, bbox_inches='tight')
                    self.inflow_canvas.figure.savefig(dlg.GetPath(), dpi=200, bbox_inches='tight')
                    wx.MessageBox("Dashboard saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    wx.MessageBox(str(e), "Save Error", wx.OK | wx.ICON_ERROR)

def find_directories_with_file(root_dir: str, filename: str) -> List[str]:
    """
    Return a list of all bottom-level (leaf) directories
    under root_dir that contain the given filename.

    Bottom-level means the deepest directories that actually contain the file.
    """
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    matching_dirs = []

    # Walk through all directories
    for dir_path in root.rglob("*"):
        if dir_path.is_dir():
            file_path = dir_path / filename
            if file_path.is_file():
                matching_dirs.append(str(dir_path.resolve()))

    # Optional: Remove duplicates and sort
    matching_dirs = sorted(set(matching_dirs))

    return matching_dirs

def datetime64_to_str(dt64) -> str:
    if pd.isna(dt64):
        return ""
    dt = pd.to_datetime(dt64)
    return dt.strftime("%b %d, %Y")


# ==================== RUN ====================
if __name__ == "__main__":
    from reservoirs.reservoir import Reservoir
    from reservoirs.imperial import Imperial
    from reservoirs.lake_pleasant import LakePleasant
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
    # lake_pleasant = LakePleasant(upstream=[lake_havasu])
    imperial = Imperial(upstream=[lake_havasu])
    aquifers = Aquifers(upstream=[])

    reservoirs = [
        imperial,
        aquifers,
        lake_havasu,
        lake_mohave,
        lake_mead,
        lake_powell,
        flaming_gorge,
        navajo,
        blue_mesa
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs, lake_powell.date_time, reports)
    frame.Show()
    app.MainLoop()