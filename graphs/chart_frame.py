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
from pptx import Presentation
from pptx.util import Inches
from io import BytesIO
from PIL import Image
import wx
import pandas as pd
from datetime import date, timedelta
import os
import wx.lib.buttons as buttons
from typing import List, Optional, Callable, Tuple, Union
from reservoirs.reservoir import Reservoir
from chart.chart import Chart
from colorado.month_nav import MonthYearNavigator
from colorado.river_war import RiverWar
from datetime import datetime
from pathlib import Path
from source.water_year_info import WaterYearInfo
from chart.line_chart import TimeSeries
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
                 callables: List[Tuple[str, Callable]],
                 river_war: RiverWar,
                 title: str = "Colorado River War"):
        self.callables: List[Tuple[str, Callable]] = callables
        self.river_war = river_war

        screen_w, screen_h = wx.DisplaySize()
        window_height: int = screen_h - 64
        window_width: int = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self.panel)

        self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=0)

        # ---------- Export recording controls (upper-right of tab bar) ----------
        self.export_toggle = wx.ToggleButton(self.panel, label="Export", size=wx.Size(72, 22),
                                             style=wx.BU_EXACTFIT)
        self.export_toggle.SetToolTip("Toggle export recording on/off")
        self.export_toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_export_toggle)

        self.capture_btn = wx.Button(self.panel, label="Capture", size=wx.Size(72, 22),
                                    style=wx.BU_EXACTFIT)
        self.capture_btn.SetToolTip("Capture current tab into the export")
        self.capture_btn.Bind(wx.EVT_BUTTON, self.on_capture)
        self.capture_btn.Enable(False)

        self.export_toggle.Raise()
        self.capture_btn.Raise()

        # Recording state
        self.export_recording = False
        self.export_pages: List[Image.Image] = []
        self.export_pdf_path: str | None = None
        self.export_page_w_in = 11.0
        self.export_page_h_in = 8.5

        self.panel.SetSizer(self.sizer)
        self.SetMinSize(wx.Size(1100, 900))
        self.Centre()

        self.panel.Bind(wx.EVT_SIZE, self._position_overlay_button)
        self.notebook.Bind(wx.EVT_SIZE, self._position_overlay_button)
        wx.CallAfter(self._position_overlay_button)

    def _position_overlay_button(self, event=None):
        if not getattr(self, 'export_toggle', None):
            if event:
                event.Skip()
            return

        nb_size = self.notebook.GetSize()
        if nb_size.width < 50 or nb_size.height < 30:
            if event:
                event.Skip()
            return

        # ---- robust tab height ----
        tab_height = 28
        try:
            if self.notebook.GetPageCount() > 0:
                rect = self.notebook.GetTabRect(0) # type: ignore[attr-defined]
                if rect.height > 0:
                    tab_height = rect.height
        except Exception:
            pass  # keep default 28

        # Position the two buttons side-by-side
        toggle_w, toggle_h = self.export_toggle.GetSize()
        cap_w, cap_h = self.capture_btn.GetSize()
        gap = 8

        x_cap = nb_size.width - cap_w - 6
        x_toggle = x_cap - toggle_w - gap
        y = max(2, (tab_height - max(toggle_h, cap_h)) // 2)

        nb_pos = self.notebook.GetPosition()
        self.export_toggle.SetPosition(wx.Point((nb_pos.x + x_toggle, nb_pos.y + y)))
        self.capture_btn.SetPosition(wx.Point((nb_pos.x + x_cap, nb_pos.y + y)))

        self.export_toggle.Raise()
        self.capture_btn.Raise()

        if event:
            event.Skip()

    def on_capture(self, _event):
        if not self.export_recording:
            return

        idx = self.notebook.GetSelection()
        if idx < 0:
            return

        page = self.notebook.GetPage(idx)
        if isinstance(page, ChartFrame):
            img = page.get_combined_snapshot()
            if img:
                self.export_pages.append(img)
                wx.MessageBox(
                    f"Captured tab: {self.notebook.GetPageText(idx)}\n"
                    f"Total pages: {len(self.export_pages)}",
                    "Captured",
                    wx.OK | wx.ICON_INFORMATION
                )
            else:
                wx.MessageBox("Failed to capture this tab.", "Capture",
                              wx.OK | wx.ICON_WARNING)
        else:
            wx.MessageBox("Current tab is not a chart page.", "Capture",
                          wx.OK | wx.ICON_INFORMATION)

    def on_export_toggle(self, _event):
        if self.export_toggle.GetValue():
            # --- Start recording ---
            choices = ["Letter (8.5 × 11 in)", "Legal (8.5 × 14 in)"]
            dlg = wx.SingleChoiceDialog(
                self,
                "Choose paper size for landscape pages:",
                "Start Export Recording",
                choices
            )
            if dlg.ShowModal() != wx.ID_OK:
                self.export_toggle.SetValue(False)
                dlg.Destroy()
                return
            paper = dlg.GetStringSelection()
            dlg.Destroy()

            if paper.startswith("Legal"):
                self.export_page_w_in, self.export_page_h_in = 14.0, 8.5
            else:
                self.export_page_w_in, self.export_page_h_in = 11.0, 8.5

            # Build filename from currently selected tab + today’s date
            idx = self.notebook.GetSelection()
            if idx >= 0:
                tab_name = self.notebook.GetPageText(idx)
                safe_name = tab_name.replace(" ", "_")
                safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in safe_name)
            else:
                safe_name = "Notebook"

            date_suffix = date.today().strftime("%b_%d_%Y").lower()
            default_name = f"{safe_name}_{date_suffix}.pdf"

            pdf_dir = os.path.join(os.getcwd(), "pdf")
            os.makedirs(pdf_dir, exist_ok=True)

            with wx.FileDialog(
                    self,
                    "Save export as",
                    defaultDir=pdf_dir,
                    defaultFile=default_name,
                    wildcard="PDF files (*.pdf)|*.pdf",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as file_dlg:
                if file_dlg.ShowModal() != wx.ID_OK:
                    self.export_toggle.SetValue(False)
                    return
                path = file_dlg.GetPath()
                if not path.lower().endswith('.pdf'):
                    path += '.pdf'
                self.export_pdf_path = path  # <-- exact user path

            self.export_pages = []
            self.export_recording = True
            self.capture_btn.Enable(True)
            self.export_toggle.SetLabel("Stop")
        else:
            # --- Stop & save ---
            self._finish_export()

    def _finish_export(self):
        self.export_recording = False
        self.capture_btn.Enable(False)
        self.export_toggle.SetLabel("Export")
        self.export_toggle.SetValue(False)

        if not self.export_pages or not self.export_pdf_path:
            wx.MessageBox("No pages captured.", "Export", wx.OK | wx.ICON_INFORMATION)
            return

        # Build scaled pages (same logic as before)
        dpi = 200
        page_w_px = int(self.export_page_w_in * dpi)
        page_h_px = int(self.export_page_h_in * dpi)
        margin_px = int(0.05 * dpi)

        pdf_images: List[Image.Image] = []
        for src in self.export_pages:
            max_w = page_w_px - 2 * margin_px
            max_h = page_h_px - 2 * margin_px
            scale = min(max_w / src.width, max_h / src.height)
            new_w = max(1, int(src.width * scale))
            new_h = max(1, int(src.height * scale))
            resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

            page_img = Image.new('RGB', (page_w_px, page_h_px), (255, 255, 255))
            x = (page_w_px - new_w) // 2
            y = (page_h_px - new_h) // 2
            page_img.paste(resized, (x, y))
            pdf_images.append(page_img)

        # Save PDF
        pdf_images[0].save(
            self.export_pdf_path,
            "PDF",
            resolution=dpi,
            save_all=True,
            append_images=pdf_images[1:]
        )

        # Save PowerPoint
        pptx_path = os.path.splitext(self.export_pdf_path)[0] + ".pptx"
        prs = Presentation()
        prs.slide_width = Inches(self.export_page_w_in)
        prs.slide_height = Inches(self.export_page_h_in)
        blank_layout = prs.slide_layouts[6]

        for img in pdf_images:
            slide = prs.slides.add_slide(blank_layout)
            bio = BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            slide.shapes.add_picture(
                bio, Inches(0), Inches(0),
                width=Inches(self.export_page_w_in),
                height=Inches(self.export_page_h_in)
            )
        prs.save(pptx_path)

        wx.MessageBox(
            f"Saved {len(pdf_images)} page(s) to:\n"
            f"{self.export_pdf_path}\n"
            f"{pptx_path}",
            "Export Complete",
            wx.OK | wx.ICON_INFORMATION
        )

        # Clean up
        self.export_pages.clear()
        self.export_pdf_path = None

# ==================== MAIN FRAME ====================
class ChartFrame(wx.Panel):
    def __init__(self,
                 notebook_frame: NotebookFrame,
                 reservoir_lists: Optional[List[List[Reservoir]]] = None,
                 reports: List[Path] | None = None,
                 page_name: str = "Chart"
    ):
        self.notebook_frame = notebook_frame
        self.reservoir_lists:List[List[Reservoir]] = reservoir_lists or []
        self.report_paths: List[Path] = reports or []
        self.report_path: str = ''

        self.start_nav = None
        self.current_nav = None
        self.end_nav = None

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

        if self.report_paths:
            self.toolbar = self._init_toolbar(self.report_paths)
            self.toolbar.Hide()
            self.main_sizer.Add(self.toolbar, 0, wx.EXPAND | wx.ALL, border=2)
        else:
            self.create_toolbar()

        self.chart_panel = wx.Panel(self, style=wx.BORDER_NONE)
        self.chart_panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.main_sizer.Add(self.chart_panel, 1, wx.EXPAND | wx.ALL, border=2)

        self.chart_panel.Bind(wx.EVT_SIZE, self.on_chart_panel_resize)

        self.current_time_from_usbr = None
        # if self.reservoir_lists:
        self.current_time_from_usbr = self.load_data()

        self.load_charts()
        self.layout_charts()

        wx.CallAfter(self.final_full_layout)

        self.notebook_frame.notebook.AddPage(self, page_name)

    def get_combined_snapshot(self) -> Optional[Image.Image]:
        """Return a single PIL Image of all charts on this page stacked vertically.
        Titles are rendered only on the top chart."""
        try:
            images: List[Image.Image] = []
            for idx, chart in enumerate(self.charts):
                original_percentage = getattr(chart, 'percentage', 0.0)
                try:
                    img = chart.save_figure()
                finally:
                    chart.percentage = original_percentage  # restore

                if img:
                    images.append(img)

            if not images:
                return None

            total_h = sum(img.height for img in images)
            combined = Image.new('RGB', (images[0].width, total_h), (255, 255, 255))
            y = 0
            for image in images:
                combined.paste(image, (0, y))
                y += image.height
            return combined
        except Exception as e:
            print(f"[Snapshot Error] {e}")
            return None

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

    @staticmethod
    def annotate_level(ax, y, feet, color, draw_text=True, left_of_axis=True, draw_line=True):
        """Draw an optional level line and label on the right y-axis.

        y is the plotted coordinate (for example acre_feet - min_capacity).
        feet is the elevation shown in the label.
        left_of_axis=True:  right-justified text just to the left of the right y-axis
        left_of_axis=False: left-justified text just to the right of the right y-axis
        """
        if draw_line:
            ax.axhline(
                y=y,
                color=color,
                linestyle='--',
                linewidth=1.5,
                alpha=0.85,
                zorder=3,
            )

        if not draw_text:
            return

        if left_of_axis:
            x, ha = 0.995, 'right'
        else:
            x, ha = 1.005, 'left'

        ax.text(
            x, y,
            str(feet),
            transform=ax.get_yaxis_transform(),
            va='center',
            ha=ha,
            fontsize=10,
            color=color,
            fontweight='bold',
            clip_on=False,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                alpha=1,
                edgecolor=color,
            ),
        )

    @staticmethod
    def get_latest_reports(path='')-> Tuple[str, List[Path]]:
        reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv', '')
        reports_latest = []
        if len(reports):
            if path:
                report_name,  reports_latest = ChartFrame.paths_matching_month_year_root(path, reports)
            else:
                report_name,  reports_latest = ChartFrame.paths_matching_month_year_root(reports[-1], reports)
        else:
            report_name = ''
        return report_name, reports_latest

    def _init_toolbar(self, report_paths: List[Path]) -> wx.Panel:
        top_toolbar = wx.Panel(self, style=wx.BORDER_NONE)
        top_toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_text = wx.StaticText(top_toolbar, label=f"Displaying reservoirs")
        tb_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=0)
        tb_sizer.AddStretchSpacer(1)

        if report_paths and len(report_paths) > 0:
            dir_names = [p.name for p in report_paths]
            self.report_choice = wx.Choice(top_toolbar, choices=dir_names)
            last_report = report_paths[-1]
            self.report_choice.SetSelection(len(dir_names) - 1)
            self.report_path = last_report
            self.report_choice.SetToolTip("Select report directory")
            self.report_choice.Bind(wx.EVT_CHOICE, self.on_report_selected)
            tb_sizer.Add(self.report_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=0)

        yesterday = date.today() - timedelta(days=1)
        self.current_nav = MonthYearNavigator(top_toolbar, yesterday, self.on_date_changed, name="current")
        tb_sizer.Add(self.current_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        separator = wx.StaticText(top_toolbar, label="[")
        separator.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(separator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=6)

        now = datetime.now()
        water_year_start_date = date(now.year - 1, now.month, 1)
        water_year_end_date = Chart.last_day_of_month(now.year+2, now.month)

        self.start_nav = MonthYearNavigator(top_toolbar, water_year_start_date, self.on_date_changed, name="start")
        tb_sizer.Add(self.start_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        separator = wx.StaticText(top_toolbar, label="-")
        separator.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(separator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=6)

        self.end_nav = MonthYearNavigator(top_toolbar, water_year_end_date, self.on_date_changed, name="end")
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

    @staticmethod
    def get_water_year_info(year:int, month:int=10):
        if month == 1:
            start_date = date(year, month, 1)
        else:
            start_date = date(year-1, month, 1)
        water_year_info = WaterYearInfo.get_water_year(start_date, month=month)
        return water_year_info

    def load_data(self) -> Optional[date]:
        return self.load_reservoirs()

    def load_reservoirs(self) -> Optional[date]:
        date_time_as_date = None
        if self.start_nav is not None:
            start = self.start_nav.current_date
            current = self.current_nav.current_date
            end = self.end_nav.current_date
        else:
            start = current = end = date.today()

        for reservoir_list in self.reservoir_lists:
            for reservoir in reservoir_list:
                reservoir.load_reports(self.report_paths)
                reservoir.load_data(Path(self.report_path), start, current, end)
                if reservoir.name == 'Lake Powell':
                    date_time_as_date = pd.Timestamp(reservoir.date_time)
        return date_time_as_date

    def load_charts(self):
        pass

    def set_report(self, report_path: Path):
        self.report_path = report_path
        for chart in self.charts:
            chart.update_report(Path(self.report_path).name)

    def on_report_selected(self, _):
        if self.report_choice is None:
            return
        idx = self.report_choice.GetSelection()
        self.set_report(self.report_paths[idx])

        print(f"Selected report: {Path(self.report_path).name}")
        self.load_data()

        for chart in self.charts:
            chart.update_dates(start_date=self.start_nav.current_date,
                               current_date=self.current_nav.current_date,
                               end_date=self.end_nav.current_date)
            chart.update_canvas()

        self._take_snapshot()
        wx.CallAfter(self.final_full_layout)

    def on_date_changed(self, which: str, date_val: date):
        self.load_data()

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

        self.load_data()
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
    def paths_matching_month_year_root(
            reference_path: Union[str, Path],
            paths: List[Union[str, Path]]
    ) -> Tuple[str, List[Path]]:
        """
        Extract the month-year root (e.g. 'JUL26') from reference_path
        and return every path in `paths` that contains the same root.
        Always returns a list of Path objects.
        """
        ref = str(reference_path)
        match = re.search(r'/(\d{4})/([A-Z]{3}\d{2})', ref)
        if not match:
            return '', []

        root = match.group(2)  # e.g. 'JUL26'

        # Match /YYYY/ROOT (followed by _ . or end)
        pattern = re.compile(rf'/\d{{4}}/{re.escape(root)}(?:_|$|\.)')
        return root, [Path(p) for p in paths if pattern.search(str(p))]

    @staticmethod
    def find_directories_with_file(root_dir: str, filename: str, suffix: str='') -> List[str]:
        """Return list of directories containing the given filename."""
        root = Path(root_dir)
        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {root_dir}")

        matching_dirs = []
        for dir_path in root.rglob("*"):
            if dir_path.is_dir():
                if (dir_path / filename).is_file():
                    matching_dirs.append(str(dir_path.resolve()))

        return ChartFrame.filter_and_sort_usbr_reports(matching_dirs, suffix=suffix)

    @staticmethod
    def filter_and_sort_usbr_reports(paths, suffix=''):
        def get_sort_key(path_str):
            path = str(path_str)
            if suffix:
                # Require exact suffix match at end of path
                pattern = rf'/(\d{{4}})/([A-Z]{{3}}\d{{2}}){re.escape(suffix)}$'
            else:
                # No suffix required; just match year + month code
                pattern = r'/(\d{4})/([A-Z]{3}\d{2})'

            match = re.search(pattern, path)
            if not match:
                return datetime.min, path

            year = int(match.group(1))
            month_code = match.group(2)

            try:
                dt = datetime.strptime(month_code, '%b%y').replace(year=year)
            except ValueError:
                dt = datetime.min

            return dt, path

        # Keep only paths that match /YYYY/MONYY (plus optional suffix)
        if suffix:
            pattern = re.compile(rf'/(\d{{4}})/[A-Z]{{3}}\d{{2}}{re.escape(suffix)}$')
        else:
            pattern = re.compile(r'/(\d{4})/[A-Z]{3}\d{2}')

        filtered = [p for p in paths if pattern.search(str(p))]

        return sorted(filtered, key=get_sort_key)

    @staticmethod
    def add_two_series_delta_annotation(
            ax,
            ts1,
            ts2,
            date,
            column1: str = None,
            column2: str = None,
            color: str = None,
            linestyle: str = "--",
            linewidth: float = 1.5,
            text_offset: float = 0.0,  # now a vertical offset (fraction of y-span)
            annotation_side: str = "right",  # "right" or "left"
    ):
        """
        Draw a vertical dashed line (with solid end-caps) at `date` between the
        values of two different time series on that date, and annotate the delta.

        text_offset : float
            Vertical offset as a fraction of the current y-axis span.
            Positive moves the text up, negative moves it down.

        annotation_side:
            "right" → text to the right of the vertical line, left-justified
            "left"  → text to the left of the vertical line, right-justified

        Delta = value(ts1) - value(ts2).
        """
        if not isinstance(ts1, TimeSeries):
            ts1 = TimeSeries.from_tuple(ts1)
        if not isinstance(ts2, TimeSeries):
            ts2 = TimeSeries.from_tuple(ts2)

        col1 = column1 or ts1.col
        col2 = column2 or ts2.col
        line_color = color or ts1.color

        def prepare(ts, col, name):
            if ts.df is None or ts.df.empty or col not in ts.df.columns:
                print(f"[add_two_series_delta_annotation] {name}: missing DataFrame or column '{col}' → returning None")
                return None
            df = ts.df.copy()
            if "Date" not in df.columns:
                print(f"[add_two_series_delta_annotation] {name}: no 'Date' column → returning None")
                return None
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date").sort_index()
            return df

        df1 = prepare(ts1, col1, "ts1")
        df2 = prepare(ts2, col2, "ts2")
        if df1 is None or df2 is None:
            print(
                "[add_two_series_delta_annotation] Could not prepare both series → returning None (no annotation drawn)")
            return

        dt = pd.Timestamp(date)

        def nearest_value(df, col, label):
            if df.empty:
                print(f"[add_two_series_delta_annotation] {label}: DataFrame is empty → returning None")
                return None

            idx = df.index.get_indexer([dt], method="nearest")[0]
            if idx == -1:
                print(f"[add_two_series_delta_annotation] {label}: no nearest index for {dt.date()} → returning None")
                return None

            candidates = list(range(idx, -1, -1)) + list(range(idx + 1, len(df)))
            for i in candidates:
                val = df.iloc[i][col]
                if pd.notna(val):
                    try:
                        numeric = float(val)
                        matched_date = df.index[i]
                        if matched_date.date() != dt.date():
                            print(f"[add_two_series_delta_annotation] WARNING {label}: "
                                  f"requested {dt.date()} but using {matched_date.date()} "
                                  f"(value={numeric})")
                        return numeric
                    except (TypeError, ValueError):
                        continue

            print(
                f"[add_two_series_delta_annotation] {label}: no non-NaN value found near {dt.date()} → returning None")
            return None

        v1 = nearest_value(df1, col1, "ts1")
        v2 = nearest_value(df2, col2, "ts2")
        if v1 is None or v2 is None:
            print(
                "[add_two_series_delta_annotation] Could not obtain both values → returning None (no annotation drawn)")
            return

        delta = v1 - v2

        # Vertical dashed line
        ax.plot(
            [dt, dt],
            [v1, v2],
            color=line_color,
            linestyle=linestyle,
            linewidth=linewidth,
            zorder=6,
        )

        # Short solid end-caps (same color)
        x_span_days = (pd.Timestamp(ax.get_xlim()[1]) - pd.Timestamp(ax.get_xlim()[0])).days
        cap_width_days = max(1, int(x_span_days * 0.008))
        cap = pd.Timedelta(days=cap_width_days)

        ax.plot([dt - cap, dt + cap], [v1, v1],
                color=line_color, linestyle="-", linewidth=linewidth,
                solid_capstyle="butt", zorder=6)
        ax.plot([dt - cap, dt + cap], [v2, v2],
                color=line_color, linestyle="-", linewidth=linewidth,
                solid_capstyle="butt", zorder=6)

        # Annotation with vertical offset
        mid_y = (v1 + v2) / 2.0
        y0, y1 = ax.get_ylim()
        y_span = y1 - y0
        y_offset = y_span * text_offset

        sign = "+" if delta >= 0 else ""
        label = f"{sign}{delta:,.1f}"

        x_clearance = pd.Timedelta(days=max(1, int(x_span_days * 0.008)))

        if annotation_side.lower() == "left":
            xytext = (dt - x_clearance, mid_y + y_offset)
            ha = "right"
        else:
            xytext = (dt + x_clearance, mid_y + y_offset)
            ha = "left"

        ax.annotate(
            label,
            xy=(dt, mid_y),
            xytext=xytext,
            textcoords="data",
            ha=ha,
            va="center",
            fontsize=9,
            fontweight="bold",
            color=line_color,
            zorder=7,
        )

    @staticmethod
    def add_delta_annotation(
            ax,
            ts,
            start_date,
            end_date,
            column: str = None,
            color: str = None,
            linestyle: str = "--",
            linewidth: float = 1.5,
            text_offset: float = 0.0,  # now a vertical offset (fraction of y-span)
            annotation_side: str = "right",  # "right" or "left"
    ):
        """
        Draw a vertical dashed line at end_date between the values of the series
        on start_date and end_date, with solid end-caps in the same color,
        and annotate the delta.

        text_offset : float
            Vertical offset as a fraction of the current y-axis span.
            Positive moves the text up, negative moves it down.
            Use this to keep multiple annotations from overlapping.

        annotation_side:
            "right" → text to the right of the vertical line, left-justified
            "left"  → text to the left of the vertical line, right-justified
        """
        if not isinstance(ts, TimeSeries):
            ts = TimeSeries.from_tuple(ts)

        col = column or ts.col
        line_color = color or ts.color

        if ts.df is None or ts.df.empty or col not in ts.df.columns:
            print(f"[add_delta_annotation] Missing DataFrame or column '{col}' → returning None")
            return

        df = ts.df.copy()
        if "Date" not in df.columns:
            print("[add_delta_annotation] No 'Date' column → returning None")
            return
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        def nearest_value(dt, label="value"):
            if df.empty:
                print(f"[add_delta_annotation] {label}: DataFrame is empty → returning None")
                return None, None

            idx = df.index.get_indexer([dt], method="nearest")[0]  # type: ignore[arg-type]
            if idx == -1:
                print(f"[add_delta_annotation] {label}: no nearest index for {dt.date()} → returning None")
                return None, None

            candidates = list(range(idx, -1, -1)) + list(range(idx + 1, len(df)))
            for i in candidates:
                val = df.iloc[i][col]
                if pd.notna(val):
                    try:
                        numeric = float(val) # type: ignore[arg-type]
                        matched_date = pd.Timestamp(df.index[i])
                        if matched_date.date() != dt.date():
                            print(f"[add_delta_annotation] WARNING {label}: "
                                  f"requested {dt.date()} but using {matched_date.date()} "
                                  f"(value={numeric})")
                        return numeric, matched_date
                    except (TypeError, ValueError):
                        continue

            print(f"[add_delta_annotation] {label}: no non-NaN value found near {dt.date()} → returning None")
            return None, None

        v_start, matched_start = nearest_value(start, label="start")
        v_end, matched_end = nearest_value(end, label="end")
        if v_start is None or v_end is None:
            print(
                "[add_delta_annotation] Could not obtain both start and end values → returning None (no annotation drawn)")
            return

        delta = v_end - v_start
        vertical_x = end

        # Vertical dashed line
        ax.plot(
            [vertical_x, vertical_x],
            [v_start, v_end],
            color=line_color,
            linestyle=linestyle,
            linewidth=linewidth,
            zorder=6,
        )

        # Solid end-cap from actual start time/value to the vertical line
        ax.plot(
            [matched_start, vertical_x],
            [v_start, v_start],
            color=line_color,
            linestyle="-",
            linewidth=linewidth,
            solid_capstyle="butt",
            zorder=6,
        )

        # Short solid cap at the end value
        x_span_days = (pd.Timestamp(ax.get_xlim()[1]) - pd.Timestamp(ax.get_xlim()[0])).days
        cap_width_days = max(1, int(x_span_days * 0.008))
        cap = pd.Timedelta(days=cap_width_days)

        ax.plot(
            [vertical_x - cap, vertical_x + cap],
            [v_end, v_end],
            color=line_color,
            linestyle="-",
            linewidth=linewidth,
            solid_capstyle="butt",
            zorder=6,
        )

        # Annotation with vertical offset
        mid_y = (v_start + v_end) / 2.0
        y0, y1 = ax.get_ylim()
        y_span = y1 - y0
        y_offset = y_span * text_offset  # positive = up, negative = down

        sign = "+" if delta >= 0 else ""
        label = f"{sign}{delta:,.1f}"

        # Small fixed horizontal clearance so text doesn't sit on the line
        x_clearance = pd.Timedelta(days=max(1, int(x_span_days * 0.008)))

        if annotation_side.lower() == "left":
            xytext = (vertical_x - x_clearance, mid_y + y_offset)
            ha = "right"
        else:  # "right"
            xytext = (vertical_x + x_clearance, mid_y + y_offset)
            ha = "left"

        ax.annotate(
            label,
            xy=(vertical_x, mid_y),
            xytext=xytext,
            textcoords="data",
            ha=ha,
            va="center",
            fontsize=9,
            fontweight="bold",
            color=line_color,
            zorder=7,
        )

    @staticmethod
    def add_report_series(
            reservoir,
            time_series: list,
            column_name: str,
            color: str,
            linewidth: float = 2,
            convert_af_to_cfs: bool = True,
            subtract_col: str | None = None,
            subtract: float = 0.0,
            is_storage: bool = False
    ) -> List[Tuple[str, str]]:
        """
        For each report on the reservoir, distribute the given monthly column
        to daily, then insert a line-series tuple into time_series.
        Line style cycles by report index: solid, dotted, dashed, ...

        If is_storage=True, uses interpolate_monthly_storage_to_daily
        instead of monthly_total_to_daily_smooth.

        If subtract_col is provided, that daily column is subtracted from the
        interpolated result.
        If subtract != 0, that constant is also subtracted.
        """
        legend_studies = []
        styles = ["dotted", "--", "-", "-."]

        for i, (report_name, dfs) in enumerate(reservoir.reports.items()):
            line_style = styles[i % len(styles)]
            name = f"{report_name}.{column_name}"
            df, df_wy = dfs

            if is_storage:
                Reservoir.interpolate_monthly_storage_to_daily(
                    df,
                    reservoir.df_daily,
                    monthly_value_col=column_name,
                    daily_target_col=name
                )
            else:
                Reservoir.monthly_total_to_daily_smooth(
                    df,
                    reservoir.df_daily,
                    monthly_value_col=column_name,
                    daily_target_col=name,
                    convert_af_to_cfs=convert_af_to_cfs
                )

            if subtract_col and subtract_col in reservoir.df_daily.columns:
                reservoir.df_daily[name] = (
                        reservoir.df_daily[name] - reservoir.df_daily[subtract_col]
                )

            if subtract:
                reservoir.df_daily[name] = reservoir.df_daily[name] - subtract

            legend_studies.append((report_name, line_style))
            ts = TimeSeries(
                df=reservoir.df_daily,
                col=name,
                color=color,
                linestyle=line_style,
                do_stack=False,
                linewidth=linewidth
            )
            time_series.insert(0, ts)
        return legend_studies

def previous_month_path(path: Path) -> Path:
    """
    Takes a path like: /.../2026/APR26
    Returns:          /.../2026/MAR26

    Handles year rollover: JAN26 → DEC25
    """
    path_str = str(path)

    # Match year and month code (e.g. 2026/APR26), ignoring an optional _SUFFIX such as _MIN
    match = re.search(r'/(\d{4})/([A-Z]{3}\d{2})(?:_.*)?$', path_str)
    if not match:
        raise ValueError(f"Could not find month-year pattern in path: {path}")
    year_str = match.group(1)
    month_code = match.group(2)  # e.g. APR26

    # Parse to datetime
    dt = datetime.strptime(month_code, '%b%y')
    dt = dt.replace(year=int(year_str))

    # Go to previous month
    if dt.month == 1:
        prev_dt = dt.replace(year=dt.year - 1, month=12, day=1)
    else:
        prev_dt = dt.replace(month=dt.month - 1, day=1)

    # Format back to APR26 style
    new_month_code = prev_dt.strftime('%b%y').upper()

    # Replace in the original path
    new_path_str = re.sub(r'/(\d{4})/[A-Z]{3}\d{2}$',
                          f'/{prev_dt.year}/{new_month_code}',
                          path_str)

    return Path(new_path_str)