"""
Copyright (c) 2025 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in allimport pandas as pd

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
import io
from PIL import Image
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib
import pandas as pd
from datetime import date
import os
import wx.lib.buttons as buttons
from typing import List
from reservoirs.reservoir import Reservoir
from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
from colorado.chart import Chart
import colorado.lb as lb

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


class MonthYearNavigator(wx.Panel):
    """Reusable single month/year navigator with smaller raised buttons"""
    def __init__(self, parent:wx.Panel, current_date:date, on_changed=None, name:str=""):
        super().__init__(parent, style=wx.BORDER_NONE)

        self.name = name
        self.current_date = current_date
        self.on_changed = on_changed

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)
        arrow_fg = wx.Colour(160, 160, 160)

        self.btn_left = buttons.GenButton(self, label="◀", size=wx.Size(34, 32))
        self.btn_left.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_left.SetForegroundColour(arrow_fg)
        self.btn_left.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.btn_left.SetBezelWidth(3)
        self.btn_left.SetUseFocusIndicator(False)
        self.btn_left.Bind(wx.EVT_BUTTON, self._on_left)
        sizer.Add(self.btn_left, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)

        self.date_text = wx.StaticText(self, label="")
        self.date_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.date_text.SetForegroundColour(wx.Colour(230, 230, 230))
        sizer.Add(self.date_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=12)

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
        self.date_text.SetLabel(Chart.date_to_string(self.current_date))

    def _on_left(self, event):
        month = self.current_date.month - 1
        year = self.current_date.year
        if month < 1:
            month = 12
            year -= 1
        self.current_date = date(year, month, 1)
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_date)

    def _on_right(self, event):
        month = self.current_date.month + 1
        year = self.current_date.year
        if month > 12:
            month = 1
            year += 1
        self.current_date = date(year, month, 1)
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_date)


# ==================== MAIN FRAME ====================
class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):

        screen_w, screen_h = wx.DisplaySize()
        window_height = screen_h - 64
        window_width = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.reservoirs = reservoir_list
        self.report_list = report_list

        # ====================== RECORDING STATE ======================
        self.saving_pdf = False
        self.saving_gif = False
        self.gif_frames: List[Image.Image] = []
        self.pdf_pages: List[Image.Image] = []
        self.gif_filename: str | None = None
        self.pdf_filename: str | None = None

        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ==================== TOP TOOLBAR ====================
        top_toolbar = wx.Panel(self.panel, style=wx.BORDER_NONE)
        top_toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_text = wx.StaticText(top_toolbar, label=f"Displaying {len(reservoir_list)} reservoirs")
        tb_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=15)
        tb_sizer.AddStretchSpacer(1)

        # Report selector
        report_str:str = ''
        if report_list and len(report_list) > 0:
            dir_names = [Path(p).name for p in report_list]
            self.report_choice = wx.Choice(top_toolbar, choices=dir_names)
            self.report_choice.SetSelection(len(dir_names) - 2)
            self.report_path = self.report_list[len(dir_names) - 2]
            self.report_choice.SetToolTip("Select report directory")
            self.report_choice.Bind(wx.EVT_CHOICE, self.on_report_selected)
            tb_sizer.Add(self.report_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=15)
        else:
            self.report_choice = None

        # Date navigators
        self.current_nav = MonthYearNavigator(top_toolbar, date(2026, 4, 1), self.on_date_changed, name="current")
        tb_sizer.Add(self.current_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        separator = wx.StaticText(top_toolbar, label="[")
        separator.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        # separator.SetForegroundColour(wx.Colour(100, 100, 100))  # Dark gray
        tb_sizer.Add(separator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=6)

        self.start_nav = MonthYearNavigator(top_toolbar, date(2025, 10, 1), self.on_date_changed, name="start")
        tb_sizer.Add(self.start_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        separator = wx.StaticText(top_toolbar, label="-")
        separator.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(separator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=6)

        self.end_nav = MonthYearNavigator(top_toolbar, Chart.last_day_of_month(2026, 9), self.on_date_changed, name="end")
        tb_sizer.Add(self.end_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        separator = wx.StaticText(top_toolbar, label="]")
        separator.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(separator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=6)

        # tb_sizer.AddSpacer(25)

        # Global arrows
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

        # Recording buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_pdf_btn = wx.ToggleButton(top_toolbar, label="PDF Record", size=wx.Size(-1, 28))
        self.save_pdf_btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_pdf)
        btn_sizer.Add(self.save_pdf_btn, 0, wx.RIGHT, border=8)

        self.save_gif_btn = wx.ToggleButton(top_toolbar, label="GIF Record", size=wx.Size(-1, 28))
        self.save_gif_btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_gif)
        btn_sizer.Add(self.save_gif_btn, 0, wx.RIGHT, border=8)

        self.stop_btn = wx.Button(top_toolbar, label="Stop Recording", size=wx.Size(-1, 28))
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop_recording)
        self.stop_btn.Enable(False)
        btn_sizer.Add(self.stop_btn, 0)

        tb_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=15)

        top_toolbar.SetSizer(tb_sizer)
        top_toolbar.SetMinSize(wx.Size(-1, 42))

        # ==================== CHARTS ====================
        power_zones = [
            ('#ffffff', 'Available Head'),
            (Reservoir.high_power_pool_color, 'Normal Power Head'),
            (Reservoir.low_power_pool_color, 'Low Power Head'),
            (Reservoir.non_power_pool_color, 'Limited Access')
        ]

        reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]

        current_time_from_usbr = self.load_reservoirs()
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        self.reservoir_chart = ReservoirChart(
            reservoirs, start_date=start, current_date=current_time_from_usbr, end_date=end,
            power_head_zones=power_zones, reserved_zones=reserved_zones
        )

        self.inflow_chart = InflowOutflowChart(
            reservoirs, start_date=start, current_date=current, end_date=end
        )
        self.set_report(self.report_path)

        # Notebook + Splitter
        self.notebook = wx.Notebook(self.panel)
        self.combined_panel = wx.Panel(self.notebook)
        self.splitter = wx.SplitterWindow(self.combined_panel,
                                          style=wx.SP_THIN_SASH | wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        self.splitter.SetMinimumPaneSize(200)

        self.reservoir_panel = wx.Panel(self.splitter)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)
        self.reservoir_canvas = FigureCanvas(self.reservoir_panel, -1,
                                             self.reservoir_chart.get_figure(None, None))
        cap_sizer.Add(self.reservoir_canvas, 1, wx.EXPAND | wx.ALL, border=6)
        self.reservoir_panel.SetSizer(cap_sizer)

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

        self.notebook.AddPage(self.combined_panel, 'Reservoirs')

        main_sizer.Add(top_toolbar, 0, wx.EXPAND)
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=4)

        self.panel.SetSizer(main_sizer)
        self.SetMinSize(wx.Size(1100, 900))
        self.Centre()
        wx.CallAfter(self.panel.Layout)

    def load_reservoirs(self)->date|None:
        date_time_as_date = None
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date
        for reservoir in self.reservoirs:
            reservoir.load_data(Path(self.report_path), start, current, end)
            if reservoir.name == 'Lake Powell':
                date_time_as_date = pd.Timestamp(reservoir.date_time)
        return date_time_as_date

    # ==================== EVENT HANDLERS ====================
    def set_report(self, report_str:str):
        self.report_path = report_str
        self.reservoir_chart.update_report(Path(self.report_path).name)
        self.inflow_chart.update_report(Path(self.report_path).name)

    def on_report_selected(self, event):
        if self.report_choice is None:
            return


        idx = self.report_choice.GetSelection()
        self.set_report(self.report_list[idx])

        print(f"Selected report: {Path(self.report_path).name}")
        self.load_reservoirs()
        self.reservoir_chart.update_dates(start_date=self.start_nav.current_date,
                                          current_date=self.current_nav.current_date,
                                          end_date=self.end_nav.current_date)
        self.inflow_chart.update_dates(start_date=self.start_nav.current_date,
                                       current_date=self.current_nav.current_date,
                                       end_date=self.end_nav.current_date)
        self._update_reservoir_canvas()
        self._update_inflow_canvas()
        self._take_snapshot()

    def on_date_changed(self, which: str, date_val: date):
        self.load_reservoirs()

        if which == "start":
            self.reservoir_chart.update_dates(start_date=date_val)
            self.inflow_chart.update_dates(start_date=date_val)
        elif which == "current":
            self.reservoir_chart.update_dates(current_date=date_val)
            self.inflow_chart.update_dates(current_date=date_val)
        elif which == "end":
            self.reservoir_chart.update_dates(end_date=date_val)
            self.inflow_chart.update_dates(end_date=date_val)

        self._update_reservoir_canvas()
        self._update_inflow_canvas()
        self._take_snapshot()

    def _update_reservoir_canvas(self):
        if not hasattr(self, 'reservoir_canvas'): return
        w = max(8.0, self.in_panel.GetClientSize().GetWidth() / 100.0)
        h = max(4.0, self.in_panel.GetClientSize().GetHeight() / 100.0)
        new_fig = self.reservoir_chart.get_figure(w, h)
        self.reservoir_canvas.figure = new_fig
        self.reservoir_canvas.draw()
        self.reservoir_canvas.Refresh()

    def _update_inflow_canvas(self):
        if not hasattr(self, 'inflow_canvas'): return
        w = max(8.0, self.in_panel.GetClientSize().GetWidth() / 100.0)
        h = max(4.0, self.in_panel.GetClientSize().GetHeight() / 100.0)
        new_fig = self.inflow_chart.get_figure(w, h)
        self.inflow_canvas.figure = new_fig
        self.inflow_canvas.draw()
        self.inflow_canvas.Refresh()

    def _on_global_change(self, delta: int):
        for nav in (self.start_nav, self.current_nav, self.end_nav):
            month = nav.current_date.month + delta
            year = nav.current_date.year
            if delta < 0:
                if month < 1: month, year = 12, year - 1
            else:
                if month > 12: month, year = 1, year + 1
            if nav == self.end_nav:
                nav.current_date = Chart.last_day_of_month(year, month)
            else:
                nav.current_date = date(year, month, 1)
            nav._update_display()

        self.load_reservoirs()
        self.inflow_chart.update_dates(start_date=self.start_nav.current_date,
                                       current_date=self.current_nav.current_date,
                                       end_date=self.end_nav.current_date)
        self.reservoir_chart.update_dates(start_date=self.start_nav.current_date,
                                          current_date=self.current_nav.current_date,
                                          end_date=self.end_nav.current_date)
        self._update_inflow_canvas()
        self._update_reservoir_canvas()
        self._take_snapshot()

    def _on_global_left(self, event):
        self._on_global_change(-1)

    def _on_global_right(self, event):
        self._on_global_change(1)

    # ==================== RECORDING ====================

    def on_toggle_pdf(self, event):
        if self.save_pdf_btn.GetValue():
            self._start_pdf_recording()
        else:
            self.save_pdf_btn.SetValue(True)
            wx.MessageBox("Use **Stop Recording** to finish.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_toggle_gif(self, event):
        if self.save_gif_btn.GetValue():
            self._start_gif_recording()
        else:
            self.save_gif_btn.SetValue(True)
            wx.MessageBox("Use **Stop Recording** to finish.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_stop_recording(self, event):
        stopped = False
        if self.saving_pdf and self.pdf_pages:
            self._save_pdf_final()
            stopped = True
        if self.saving_gif and self.gif_frames:
            self._save_gif_final()
            stopped = True

        self.save_pdf_btn.SetValue(False)
        self.save_gif_btn.SetValue(False)
        self.saving_pdf = False
        self.saving_gif = False
        self.gif_frames.clear()
        self.pdf_pages.clear()
        self.gif_filename = None
        self.pdf_filename = None
        self.stop_btn.Enable(False)

        if stopped:
            wx.MessageBox("Recording finished!\nFile(s) saved successfully.", "Success", wx.OK | wx.ICON_INFORMATION)

    def _start_pdf_recording(self):
        default_name = f"Reservoir_Dashboard_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"
        with wx.FileDialog(self, "Save PDF Recording As", defaultDir=os.getcwd(),
                           defaultFile=default_name, wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                self.save_pdf_btn.SetValue(False)
                return
            self.pdf_filename = dlg.GetPath()
            if not self.pdf_filename.lower().endswith('.pdf'):
                self.pdf_filename += '.pdf'

        self.pdf_pages = []
        self.saving_pdf = True
        self.stop_btn.Enable(True)
        self._take_snapshot()

    def _start_gif_recording(self):
        default_name = f"Reservoir_Dashboard_{date.today().strftime('%Y%m%d_%H%M%S')}.gif"
        with wx.FileDialog(self, "Save GIF Recording As", defaultDir=os.getcwd(),
                           defaultFile=default_name, wildcard="GIF files (*.gif)|*.gif",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                self.save_gif_btn.SetValue(False)
                return
            self.gif_filename = dlg.GetPath()
            if not self.gif_filename.lower().endswith('.gif'):
                self.gif_filename += '.gif'

        self.gif_frames = []
        self.saving_gif = True
        self.stop_btn.Enable(True)
        self._take_snapshot()

    def _take_snapshot(self):
        if not (self.saving_pdf or self.saving_gif):
            return
        if not hasattr(self, 'reservoir_canvas') or not hasattr(self, 'inflow_canvas'):
            return

        try:
            fig_top = self.reservoir_canvas.figure
            fig_bottom = self.inflow_canvas.figure

            buf_top = io.BytesIO()
            buf_bottom = io.BytesIO()
            fig_top.savefig(buf_top, dpi=180, bbox_inches='tight', format='png')
            fig_bottom.savefig(buf_bottom, dpi=180, bbox_inches='tight', format='png')
            buf_top.seek(0)
            buf_bottom.seek(0)

            img_top = Image.open(buf_top)
            img_bottom = Image.open(buf_bottom)

            total_h = img_top.height + img_bottom.height
            combined = Image.new('RGB', (img_top.width, total_h), (255, 255, 255))
            combined.paste(img_top, (0, 0))
            combined.paste(img_bottom, (0, img_top.height))

            if self.saving_pdf:
                self.pdf_pages.append(combined.copy())
            if self.saving_gif:
                self.gif_frames.append(combined.copy())

        except Exception as e:
            print(f"[Snapshot Error] {e}")

    def _save_pdf_final(self):
        if not self.pdf_pages: return
        self.pdf_pages[0].save(self.pdf_filename, "PDF", resolution=200,
                               save_all=True, append_images=self.pdf_pages[1:])

    def _save_gif_final(self):
        if not self.gif_frames:
            return

        self.gif_frames[0].save(
            self.gif_filename,
            "GIF",
            save_all=True,
            append_images=self.gif_frames[1:],
            duration=GIF_FRAME_DELAY_MS,
            loop=0 if not GIF_LOOP_ENABLED else 0,   # 0 = infinite loop in PIL
            optimize=True
        )

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