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
from PIL import Image
import wx
import pandas as pd
from datetime import date
import os
import wx.lib.buttons as buttons
from typing import List, Optional, Callable, Tuple
from reservoirs.reservoir import Reservoir
from chart.chart import Chart
from colorado.month_nav import MonthYearNavigator
from colorado.river_war import RiverWar
from datetime import datetime
from pathlib import Path
import re

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

class NotebookFrame(wx.Frame):
    def __init__(self,
                 callables:List[Tuple[str, Callable]],
                 river_war:RiverWar,
                 title: str = "Colorado River War"):
        self.callables:List[Tuple[str, Callable]] = callables
        self.river_war = river_war

        screen_w, screen_h = wx.DisplaySize()
        window_height:int = screen_h - 64
        window_width:int = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self.panel)

        self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=0)

        self.panel.SetSizer(self.sizer)
        self.SetMinSize(wx.Size(1100, 900))
        self.Centre()

# ==================== MAIN FRAME ====================
class ChartFrame(wx.Panel):
    def __init__(self,
                 notebook_frame: NotebookFrame,
                 reservoirs: Optional[List[Reservoir]] = None,
                 reports: List[str] | None = None,
                 page_name: str = "Chart"
    ):
        self.notebook_frame = notebook_frame
        self.reservoirs: List[Reservoir] = reservoirs or []
        self.reports: List[str] = reports or []
        self.report_path: str = ''

        self.charts: List[Chart] = []
        self.toolbar: Optional[wx.Panel] = None
        self.chart_panel: Optional[wx.Panel] = None
        self.charts_btn: Optional[wx.Button] = None

        # Recording state
        self.saving_pdf = False
        self.saving_gif = False
        self.gif_frames: List[Image.Image] = []
        self.pdf_pages: List[Image.Image] = []
        self.gif_filename: str | None = None
        self.pdf_filename: str | None = None

        self._layout_pending = False

        screen_w, screen_h = wx.DisplaySize()
        window_height: int = screen_h - 64
        window_width: int = min(1580, screen_w - 40)

        super().__init__(self.notebook_frame.notebook,
                        size=wx.Size(window_width, window_height),
                        style=wx.TAB_TRAVERSAL)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)

        if self.reports:
            self.toolbar = self._init_toolbar(self.reservoirs, self.reports)
            self.main_sizer.Add(self.toolbar, 0, wx.EXPAND | wx.ALL, border=2)
        else:
            self.create_toolbar()

        self.chart_panel = wx.Panel(self, style=wx.BORDER_NONE)
        self.chart_panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.main_sizer.Add(self.chart_panel, 1, wx.EXPAND | wx.ALL, border=2)

        self.chart_panel.Bind(wx.EVT_SIZE, self.on_chart_panel_resize)

        self.current_time_from_usbr = None
        if self.reservoirs:
            self.current_time_from_usbr = self.load_reservoirs()

        self.load_charts()
        self.layout_charts()

        wx.CallAfter(self.final_full_layout)

        self.notebook_frame.notebook.AddPage(self, page_name)

    def layout_charts(self):
        self.rebuild_chart_layout()

    def rebuild_chart_layout(self):
        self.chart_panel.DestroyChildren()

        if not self.charts:
            self.chart_panel.Layout()
            return

        for chart in self.charts:
            chart.create_panel(self.chart_panel)

        self.do_manual_chart_layout()

    def do_manual_chart_layout(self):
        if self._layout_pending or not self.charts or not self.chart_panel:
            return

        self._layout_pending = True
        try:
            client_size = self.chart_panel.GetClientSize()
            if client_size.width < 300 or client_size.height < 200:
                return

            n = len(self.charts)
            border = 0
            available_h = max(150, client_size.height - border * (n + 1))

            # Collect percentages from each chart
            percentages = []
            for chart in self.charts:
                pct = getattr(chart, 'percentage', 0.0)
                if pct <= 0:
                    pct = 1.0 / n          # default equal share
                percentages.append(pct)

            # Normalize so they sum to 1.0
            total = sum(percentages)
            if total > 0:
                percentages = [p / total for p in percentages]
            else:
                percentages = [1.0 / n] * n

            y = border
            for i, chart in enumerate(self.charts):
                if hasattr(chart, 'panel') and chart.panel:
                    pct = percentages[i]
                    chart_h = int(available_h * pct)

                    w = client_size.width - 2 * border
                    chart.panel.SetSize(border, y, w, chart_h)
                    chart.panel.Refresh()

                    if hasattr(chart, 'canvas') and chart.canvas and hasattr(chart, 'fig'):
                        chart.canvas.SetSize(w, chart_h)
                        dpi = chart.fig.dpi
                        chart.fig.set_size_inches(w / dpi, chart_h / dpi)
                        chart.canvas.draw_idle()

                    y += chart_h + border

            self.chart_panel.Layout()
            self.Layout()
        finally:
            self._layout_pending = False

    def on_chart_panel_resize(self, event):
        event.Skip()
        if not self._layout_pending:
            wx.CallAfter(self.do_manual_chart_layout)

    def final_full_layout(self):
        self.Layout()
        self.chart_panel.Layout()
        if self.GetParent():
            self.GetParent().Layout()
        if self.notebook_frame:
            self.notebook_frame.Layout()
        self.do_manual_chart_layout()
        self.Refresh()

    def _init_toolbar(self, reservoirs: List[Reservoir], reports: List[str]) -> wx.Panel:
        top_toolbar = wx.Panel(self, style=wx.BORDER_NONE)
        top_toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_text = wx.StaticText(top_toolbar, label=f"Displaying {len(reservoirs)} reservoirs")
        tb_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=0)
        tb_sizer.AddStretchSpacer(1)

        if reports and len(reports) > 0:
            dir_names = [Path(p).name for p in reports]
            self.report_choice = wx.Choice(top_toolbar, choices=dir_names)
            last_report = reports[-1]
            self.report_choice.SetSelection(len(dir_names) - 1)
            self.report_path = last_report
            self.report_choice.SetToolTip("Select report directory")
            self.report_choice.Bind(wx.EVT_CHOICE, self.on_report_selected)
            tb_sizer.Add(self.report_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=0)

        self.current_nav = MonthYearNavigator(top_toolbar, date(2026, 4, 1), self.on_date_changed, name="current")
        tb_sizer.Add(self.current_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        separator = wx.StaticText(top_toolbar, label="[")
        separator.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
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

        tb_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=0)

        top_toolbar.SetSizer(tb_sizer)
        top_toolbar.SetMinSize(wx.Size(-1, 48))

        return top_toolbar

    def create_toolbar(self):
        if self.toolbar is None:
            self.toolbar = wx.Panel(self, style=wx.BORDER_NONE)
            self.toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

            sizer = wx.BoxSizer(wx.HORIZONTAL)

            self.charts_btn = wx.Button(self.toolbar, label="Charts ▼", style=wx.BU_EXACTFIT)
            self.charts_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            self.charts_btn.Bind(wx.EVT_BUTTON, self.on_charts_menu)

            sizer.Add(self.charts_btn, 0, wx.ALL | wx.CENTER, border=0)

            self.toolbar.SetSizer(sizer)

        self.insert_toolbar()

    def insert_toolbar(self):
        if self.toolbar and self.main_sizer:
            if self.main_sizer.GetItem(self.toolbar):
                self.main_sizer.Remove(self.toolbar.GetSizer())
            self.main_sizer.Insert(0, self.toolbar, 0, wx.EXPAND | wx.ALL, border=0)
            self.Layout()

    def _create_chart_menu(self):
        menu = wx.Menu()
        for label, func in self.notebook_frame.callables:
            item = menu.Append(wx.ID_ANY, label)

            def make_handler(f):
                return lambda event: f(self.notebook_frame)
            menu.Bind(wx.EVT_MENU, make_handler(func), item)
        return menu

    def on_charts_menu(self, _):
        menu = self._create_chart_menu()
        pos = self.charts_btn.GetPosition()
        pos.y += self.charts_btn.GetSize().height + 2
        self.charts_btn.GetParent().PopupMenu(menu, pos)
        menu.Destroy()

    def load_reservoirs(self) -> Optional[date]:
        date_time_as_date = None
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        for reservoir in self.reservoirs:
            reservoir.load_data(Path(self.report_path), start, current, end)
            if reservoir.name == 'Lake Powell':
                date_time_as_date = pd.Timestamp(reservoir.date_time)
        return date_time_as_date

    def load_charts(self):
        pass

    def set_report(self, report_str: str):
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
        wx.CallAfter(self.final_full_layout)

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
        wx.CallAfter(self.final_full_layout)

    def _on_global_change(self, delta: int):
        for nav in (self.start_nav, self.current_nav, self.end_nav):
            month = nav.current_date.month + delta
            year = nav.current_date.year
            if delta < 0:
                if month < 1:
                    month, year = 12, year - 1
            else:
                if month > 12:
                    month, year = 1, year + 1

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
        wx.CallAfter(self.final_full_layout)

    def _on_global_left(self, _):
        self._on_global_change(-1)

    def _on_global_right(self, _):
        self._on_global_change(1)

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
            images: List[Image.Image] = []
            for chart in self.charts:
                images.append(chart.save_figure())

            if images:
                total_h = sum(img.height for img in images)
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
        if not self.pdf_pages:
            return
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
            loop=0 if not GIF_LOOP_ENABLED else 0,
            optimize=True
        )

    @staticmethod
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

        return ChartFrame.filter_and_sort_usbr_reports(matching_dirs)

    @staticmethod
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