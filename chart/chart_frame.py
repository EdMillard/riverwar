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
from PIL import Image
import wx
import pandas as pd
from datetime import date
import os
import wx.lib.buttons as buttons
from typing import List, Optional

from Xlib.Xcursorfont import top_tee

from reservoirs.reservoir import Reservoir
from chart.chart import Chart
from colorado.month_nav import MonthYearNavigator

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

class ChartFrame(wx.Frame):
    def __init__(
            self,
            reservoirs: Optional[List[Reservoir]] = None,
            reports: List[str] | None = None,
            title: str = "Colorado River War",
            page_name: str = "Chart"
    ):
        screen_w, screen_h = wx.DisplaySize()
        window_height:int = screen_h - 64
        window_width:int = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.reservoirs:List[Reservoir] = reservoirs
        self.reports:List[str] = reports
        self.report_path:str = ''

        self.charts:List[Chart] = []

        # ====================== RECORDING STATE ==================
        self.saving_pdf = False
        self.saving_gif = False
        self.gif_frames: List[Image.Image] = []
        self.pdf_pages: List[Image.Image] = []
        self.gif_filename: str | None = None
        self.pdf_filename: str | None = None

        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ==================== NOTEBOOK / CHARTS ==================
        self.notebook = wx.Notebook(self.panel)
        self.combined_panel = wx.Panel(self.notebook)

        # ======================== TOP TOOLBAR ====================
        top_toolbar:wx.Panel|None = None
        if self.reports:
            top_toolbar = self._init_toolbar(self.reservoirs, self.reports)

        # ======================== RESERVOIRS ====================
        self.current_time_from_usbr = None
        if self.reservoirs is not None:
            self.current_time_from_usbr = self.load_reservoirs()

        # ========================= CHARTS ========================
        self.load_charts()

        if self.report_path:
            self.set_report(self.report_path)

        if len(self.charts) == 2:
            # === 2 CHARTS: Use Splitter (draggable) ===
            self.splitter = wx.SplitterWindow(self.combined_panel,
                                              style=wx.SP_THIN_SASH | wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
            self.splitter.SetMinimumPaneSize(200)

            # Important: Create panels with splitter as parent
            for chart in self.charts:
                chart.create_panel(self.splitter)

            self.splitter.SplitHorizontally(self.charts[0].panel, self.charts[1].panel)

            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, border=1)
            self.combined_panel.SetSizer(sizer)

        elif len(self.charts) == 1:
            # === Single chart ===
            self.charts[0].create_panel(self.combined_panel)

            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.charts[0].panel, 1, wx.EXPAND | wx.ALL, border=5)
            self.combined_panel.SetSizer(sizer)

        else:
            # === 3 or more charts: Manual layout ===
            for chart in self.charts:
                chart.create_panel(self.combined_panel)

            self.combined_panel.Bind(wx.EVT_SIZE, self.on_combined_panel_resize)
            self.do_manual_chart_layout()  # initial layout

        # Add page to notebook
        self.notebook.AddPage(self.combined_panel, page_name)

        # Put nav toolbar in combined panel sizer
        if top_toolbar:
            page_sizer = self.combined_panel.GetSizer()
            if page_sizer:
                page_sizer.Insert(0, top_toolbar, 0, wx.EXPAND | wx.ALL, border=1)
                self.combined_panel.Layout()

        # Put notebook in main sizer
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=1)

        self.panel.SetSizer(main_sizer)
        self.SetMinSize(wx.Size(1100, 900))
        self.Centre()

        # wx.CallAfter(self.final_layout_pass)
        # self.final_layout_pass()

    def final_layout_pass(self):
        """One last strong layout pass after everything is visible"""
        if len(self.charts) > 2:
            self.do_manual_chart_layout()
        self.combined_panel.Layout()
        self.notebook.Layout()
        self.panel.Layout()
        self.Layout()
        self.Refresh()

    def on_combined_panel_resize(self, event):
        """Called whenever the combined_panel is resized"""
        event.Skip()  # Important: allow normal processing
        wx.CallAfter(self.do_manual_chart_layout)  # Do layout after resize completes

    def do_manual_chart_layout(self):
        """Manually position and size each chart equally + force matplotlib resize"""
        if len(self.charts) == 0 or not self.combined_panel:
            return

        client_size = self.combined_panel.GetClientSize()
        width = client_size.width
        height = client_size.height

        if width < 300 or height < 200:
            return

        n = len(self.charts)
        border = 6
        total_borders = border * (n + 1)
        available_height = max(150, height - total_borders)  # reduced minimum

        chart_height = available_height // n

        y_offset = border
        for chart in self.charts:
            if hasattr(chart, 'panel') and chart.panel:
                # Set new size
                new_width = width - 2 * border
                new_height = chart_height

                chart.panel.SetSize(border, y_offset, new_width, new_height)
                chart.panel.Refresh()

                # === CRITICAL: Force matplotlib canvas to resize ===
                if hasattr(chart, 'canvas') and chart.canvas:
                    # Resize the canvas widget itself
                    chart.canvas.SetSize(new_width, new_height)

                    # Resize the figure to match new dimensions
                    dpi = chart.fig.dpi
                    chart.fig.set_size_inches(new_width / dpi, new_height / dpi)

                    # Redraw
                    chart.canvas.draw_idle()
                    chart.canvas.Refresh()

                y_offset += chart_height + border

    def load_charts(self):
        pass

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

    def _init_toolbar(self, reservoirs:List[Reservoir], reports:List[str])->wx.Panel:
        top_toolbar = wx.Panel(self.combined_panel, style=wx.BORDER_NONE)
        top_toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_text = wx.StaticText(top_toolbar, label=f"Displaying {len(reservoirs)} reservoirs")
        tb_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=15)
        tb_sizer.AddStretchSpacer(1)

        # Report selector
        if reports and len(reports) > 0:
            dir_names = [Path(p).name for p in reports]
            self.report_choice = wx.Choice(top_toolbar, choices=dir_names)
            last_report = reports[-1]
            self.report_choice.SetSelection(len(dir_names) - 1 )
            self.report_path = last_report
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

        self.end_nav = MonthYearNavigator(top_toolbar, Chart.last_day_of_month(2026, 9), self.on_date_changed,
                                          name="end")
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

        return top_toolbar

    # ==================== EVENT HANDLERS ====================
    def set_report(self, report_str:str):
        self.report_path = report_str
        for chart in self.charts:
            chart.update_report(Path(self.report_path).name)

    def on_report_selected(self, _):
        if self.report_choice is None:
            return


        idx = self.report_choice.GetSelection()
        self.set_report(self.reports[idx])

        print(f"Selected report: {Path(self.report_path).name}")
        self.load_reservoirs()
        for chart in self.charts:
            chart.update_dates(start_date=self.start_nav.current_date,
                                              current_date=self.current_nav.current_date,
                                              end_date=self.end_nav.current_date)
            chart.update_canvas()
        self._take_snapshot()

    def on_date_changed(self, which: str, date_val: date):
        self.load_reservoirs()

        if which == "start":
            for chart in self.charts:
                chart.update_dates(start_date=date_val)
        elif which == "current":
            for chart in self.charts:
                chart.update_dates(current_date=date_val)
        elif which == "end":
            for chart in self.charts:
                chart.update_dates(end_date=date_val)

        for chart in self.charts:
            chart.update_canvas()

        self._take_snapshot()

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
            nav.update_display()

        self.load_reservoirs()
        for chart in self.charts:
            chart.update_dates(start_date=self.start_nav.current_date,
                                       current_date=self.current_nav.current_date,
                                       end_date=self.end_nav.current_date)
            chart.update_canvas()
        self._take_snapshot()

    def _on_global_left(self, _):
        self._on_global_change(-1)

    def _on_global_right(self, _):
        self._on_global_change(1)

    # ==================== RECORDING ====================

    def on_toggle_pdf(self, _):
        if self.save_pdf_btn.GetValue():
            self._start_pdf_recording()
        else:
            self.save_pdf_btn.SetValue(True)
            wx.MessageBox("Use **Stop Recording** to finish.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_toggle_gif(self, _):
        if self.save_gif_btn.GetValue():
            self._start_gif_recording()
        else:
            self.save_gif_btn.SetValue(True)
            wx.MessageBox("Use **Stop Recording** to finish.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_stop_recording(self, _):
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
        try:
            images:List[Image] = []
            for chart in self.charts:
                images.append(chart.save_figure())
            if images:
                total_h = 0
                for image in images:
                    total_h += image.height
                combined = Image.new('RGB', (images[0].width, total_h), (255, 255, 255))
                y = 0
                for image in images:
                    combined.paste(image, (0, y))
                    y += image.height

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