import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib
import datetime as dt
import os
import pandas as pd
import wx.lib.buttons as buttons
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
        self.current_month = initial_month
        self.current_year = initial_year
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
        month_name = dt.date(self.current_year, self.current_month, 1).strftime("%b")
        self.date_text.SetLabel(f"{month_name} {self.current_year}")

    def _on_left(self, event):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_month, self.current_year)

    def _on_right(self, event):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_month, self.current_year)


# ==================== MAIN FRAME ====================
class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoirs, date_time, title="Reservoir Analysis Dashboard"):
        screen_w, screen_h = wx.DisplaySize()
        window_height = screen_h - 64
        window_width = min(1580, screen_w - 40)

        super().__init__(None, title=title, size=wx.Size(window_width, window_height))

        self.reservoirs = reservoirs

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

        self.start_nav = MonthYearNavigator(top_toolbar, 10, 2025, self.on_date_changed, name="start")
        tb_sizer.Add(self.start_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        tb_sizer.AddSpacer(25)

        self.current_nav = MonthYearNavigator(top_toolbar, 4, 2026, self.on_date_changed, name="current")
        tb_sizer.Add(self.current_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        tb_sizer.AddSpacer(25)

        self.end_nav = MonthYearNavigator(top_toolbar, 10, 2026, self.on_date_changed, name="end")
        tb_sizer.Add(self.end_nav, 0, wx.ALIGN_CENTER_VERTICAL)

        # Global arrows (unchanged)
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

        self.save_btn = wx.Button(top_toolbar, label="Save Combined Dashboard as PNG", size=wx.Size(-1, 28))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_combined)
        tb_sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=15)

        top_toolbar.SetSizer(tb_sizer)
        top_toolbar.SetMinSize(wx.Size(-1, 42))

        # ==================== CREATE CHARTS ====================
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

        self.reservoir_chart = ReservoirChart(reservoirs, power_head_zones=power_zones, reserved_zones=reserved_zones)   # New class

        self.inflow_chart = InflowOutflowChart(reservoirs)

        # ==================== NOTEBOOK ====================
        self.notebook = wx.Notebook(self.panel)

        self.combined_panel = wx.Panel(self.notebook)
        self.splitter = wx.SplitterWindow(self.combined_panel,
                                          style=wx.SP_THIN_SASH | wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        self.splitter.SetMinimumPaneSize(200)

        # Capacity panel (now using new class)
        self.cap_panel = wx.Panel(self.splitter)
        self.cap_panel.Layout()
        cap_width_inch = self.cap_panel.GetClientSize().GetWidth() / 100.0

        cap_sizer = wx.BoxSizer(wx.VERTICAL)
        self.capacity_canvas = FigureCanvas(self.cap_panel, -1,
                                            self.reservoir_chart.get_figure(cap_width_inch))
        cap_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, border=6)
        self.cap_panel.SetSizer(cap_sizer)

        # Inflow panel
        self.in_panel = wx.Panel(self.splitter)
        self.in_panel.Layout()
        inflow_width_inch = self.in_panel.GetClientSize().GetWidth() / 100.0

        in_sizer = wx.BoxSizer(wx.VERTICAL)
        self.inflow_canvas = FigureCanvas(self.in_panel, -1,
                                          self.inflow_chart.get_figure(inflow_width_inch))
        in_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, border=6)
        self.in_panel.SetSizer(in_sizer)

        self.splitter.SplitHorizontally(self.cap_panel, self.in_panel)

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

    def on_date_changed(self, which: str, month: int = None, year: int = None):
        """One single redraw for ANY date change"""
        print(f"Date changed → {which}")

        if which == "start":
            self.inflow_chart.update_dates(start_month=month, start_year=year)
        elif which == "current":
            self.inflow_chart.update_dates(current_month=month, current_year=year)
        elif which == "end":
            self.inflow_chart.update_dates(end_month=month, end_year=year)
        # "global" does nothing extra - it just triggers the final redraw

        self._update_inflow_canvas()

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
    def _on_global_left(self, event):
        """Shift all three dates back by one month - single redraw"""
        for nav in (self.start_nav, self.current_nav, self.end_nav):
            nav.current_month -= 1
            if nav.current_month < 1:
                nav.current_month = 12
                nav.current_year -= 1
            nav._update_display()

        # Now update the chart with the new values from all three
        self.inflow_chart.update_dates(
            start_month=self.start_nav.current_month,
            start_year=self.start_nav.current_year,
            current_month=self.current_nav.current_month,
            current_year=self.current_nav.current_year,
            end_month=self.end_nav.current_month,
            end_year=self.end_nav.current_year
        )

        self._update_inflow_canvas()


    def _on_global_right(self, event):
        """Shift all three dates forward by one month - single redraw"""
        for nav in (self.start_nav, self.current_nav, self.end_nav):
            nav.current_month += 1
            if nav.current_month > 12:
                nav.current_month = 1
                nav.current_year += 1
            nav._update_display()

        # Update the chart with all new values
        self.inflow_chart.update_dates(
            start_month=self.start_nav.current_month,
            start_year=self.start_nav.current_year,
            current_month=self.current_nav.current_month,
            current_year=self.current_nav.current_year,
            end_month=self.end_nav.current_month,
            end_year=self.end_nav.current_year
        )

        self._update_inflow_canvas()

    # ==================== SAVE CALLBACKS ====================
    def on_save_combined(self, event):
        default_name = f"Reservoir_Dashboard_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with wx.FileDialog(self, "Save Combined Dashboard as PNG",
                           defaultDir=os.getcwd(), defaultFile=default_name,
                           wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    self.capacity_fig.savefig(dlg.GetPath(), dpi=200, bbox_inches='tight')
                    wx.MessageBox("Dashboard saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    wx.MessageBox(str(e), "Save Error", wx.OK | wx.ICON_ERROR)


def datetime64_to_str(dt64) -> str:
    if pd.isna(dt64):
        return ""
    dt = pd.to_datetime(dt64)
    return dt.strftime("%b %d, %Y")


# ==================== RUN ====================
if __name__ == "__main__":
    # Your reservoir imports (add the missing ones as needed)
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


    lake_powell = LakePowell()

    reservoirs = [
        Imperial(),
        Aquifers(),
        LakeHavasu(),
        LakeMohave(),
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