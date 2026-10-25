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
import pandas as pd
import wx
from data_sets.demand import Demand, Colors
from demand_chart_frame import DemandChartFrame
from sheet import sheet
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
from chart.multi_bar_chart import MultiBarChart
from colorado.river_war import RiverWar
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils
from typing import Optional, List

class SupplyVDemand(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame,  demand, name='Supply v Demand',
                         start_year=1971, end_year=2024, version=0.4)

        self.multi_bar_chart.enable_draggable_vline(
            callback=self.on_line_moved,
            color='black',
            initial_year=2026,
            show_year_label=True,
        )

    def create_toolbar(self):
        super().create_toolbar()

        sizer = self.toolbar.GetSizer()
        self.play_btn = wx.Button(self.toolbar, label="▶ Start Animation")
        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play_pause)
        sizer.Add(self.play_btn, 0, wx.ALL | wx.CENTER, border=8)

        # Slider
        self.year_slider = wx.Slider(self.toolbar, value=self.current_year,
                                     minValue=self.start_year,
                                     maxValue=self.end_year,
                                     style=wx.SL_HORIZONTAL | wx.SL_LABELS)

        self.year_slider.SetMinSize(wx.Size(420, 24))
        self.year_slider.SetForegroundColour(wx.WHITE)
        self.year_slider.SetBackgroundColour(wx.Colour(80, 80, 80))
        self.year_slider.Bind(wx.EVT_SLIDER, self.on_slider_changed)
        sizer.Add(self.year_slider, 1, wx.ALL | wx.CENTER | wx.EXPAND, border=1)

        # Status
        self.toolbar_status = wx.StaticText(self.toolbar, label=f"Year: {self.current_year}")
        self.toolbar_status.SetForegroundColour(wx.WHITE)
        sizer.Add(self.toolbar_status, 0, wx.ALL | wx.CENTER, border=1)

    def on_play_pause(self, _):
        """Toggle animation"""
        if self.timer is None or not self.timer.IsRunning():
            self.start_animation()
            self.play_btn.SetLabel("⏸ Pause")
        else:
            self.stop_animation()
            self.play_btn.SetLabel("▶ Start Animation")

    def on_slider_changed(self, _):
        """Jump to selected year"""
        new_year = self.year_slider.GetValue()
        if new_year != self.current_year:
            self.current_year = new_year
            self.demand_pie_chart.update_for_year(self.current_year)
            if hasattr(self, 'toolbar_status'):
                self.toolbar_status.SetLabel(f"Year: {self.current_year}")

    def load_charts(self):
        df_ub_cul = self.demand.df_ub_cul
        df_lb_cul = self.demand.df_lb_cul
        natural_flow_data = self.demand.natural_flow_data

        radial_lines = [
            (df_lb_cul, 'LB Total with UB Tributaries', 'white'),
            (df_lb_cul, lb.MEXICO, 'white'),
            (df_ub_cul, ub.UB_TOTAL, 'white'),
        ]

        left_bar_series = [
            (df_lb_cul, all_b.DEMAND, 'maroon'),
            (natural_flow_data.df, all_b.SUPPLY_3_YEAR_AVG, 'green'),
        ]

        totals = [
            self.demand.totals,
            self.demand.lb_totals,
            self.demand.evap_totals,
            self.demand.trib_totals
        ]
        self.demand_pie_chart = PieChart(
            self.demand.demand_series,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            annotations=totals,
            radial_lines=radial_lines,
            left_bar_series=left_bar_series,
            left_bar_ymax=27.0,
            left_bar_ymin=10.0,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1971)

    def start_animation(self):
        if self.timer is None:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
            self.timer.Start(self.animation_interval)

    def stop_animation(self):
        if self.timer is not None:
            self.timer.Stop()
            self.timer = None

    def on_timer(self, _: wx.TimerEvent):
        """Called every 1 second to advance the year"""
        if self.current_year > self.end_year:
            self.stop_animation()
            return

        self.demand_pie_chart.update_for_year(self.current_year)
        self.current_year += 1

class Demand1906To1971(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand: Demand):
        self.demand_chart = None
        self.ub_demand_chart = None
        self.df_cu_1906_2006: Optional[pd.DataFrame] = None
        self._syncing_lines = False  # prevent re-entrancy

        super().__init__(notebook_frame, demand,
                         name='Demand', start_year=1906, end_year=2024, version=0.4)

        self.right_axis_annotations()
        self.bottom_axis_annotations()

        # Enable draggable lines only on charts that support them
        for chart in self.charts:
            if hasattr(chart, 'enable_draggable_vline'):
                show_bar_values = True,
                show_label = (chart is self.demand_chart)
                chart.enable_draggable_vline(
                    callback=self.on_line_moved,
                    color='black',
                    initial_year=1922,
                    show_year_label=show_label,
                    show_bar_values=show_bar_values
                )

    def load_charts(self):

        # Bureau estimated diversions/consumptive use 1906-2006 (Fairly trustworthy)
        #
        self.df_cu_1906_2006 = sheet.read_csv('data/Colorado_River/usbr_colorado_river_use_since_1906.csv',
                                         sep='\s+', na_values=["---", "-", "*******"])

        # Estimated Mexico use 1907-1970 (Not trustworthy)
        #
        df_mexico_treaty_guess = sheet.read_csv('data/Colorado_River/mexico_guess_1907_1963.csv',
                                         sep='\s+', na_values=["---", "-", "*******"])
        df_utils.divide_columns(df_mexico_treaty_guess, 'estimated_AF', 'acres_approx', 'AF per acre')

        df_cu_1906_2024 = df_utils.extend_years(self.df_cu_1906_2006, max_year=2024)
        mexico_guess_column_map = {
            "estimated_AF": "Mexico Treaty",
        }
        df_utils.copy_columns_by_key(df_mexico_treaty_guess, df_cu_1906_2024, mexico_guess_column_map, overwrite=True)

        # Bureau CUL data 1971-2024 (Very trustworthy)
        # Lower Basin CUL
        lb_column_map = {
            "AZ Colorado River": "AZ",
            "CA Total CUL": "CA",
            lb.NV_COLORADO_RIVER_TOTAL: "NV",
            "Mexico": "Mexico Treaty",
        }
        df_utils.copy_columns_by_key(self.demand.df_lb_cul, df_cu_1906_2024, lb_column_map, overwrite=True)

        # Upper Basin CUL
        #
        ub_column_map = {
            "UB Total": "Upper Basin",
        }
        df_utils.copy_columns_by_key(self.demand.df_ub_cul, df_cu_1906_2024, ub_column_map)

        # Mexico Delta, 2005 to present from annual reports
        #
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_in_excess.csv', sep='\s+')
        sheet.merge_annual_column(df_cu_1906_2024, df_mx, "MX in excess", divisor=1)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_minute_319.csv', sep='\s+')
        sheet.merge_annual_column(df_cu_1906_2024, df_mx, "MX minute 319", divisor=1)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_minute_242_bypass.csv', sep='\s+')
        sheet.merge_annual_column(df_cu_1906_2024, df_mx, "Cienega", divisor=1)

        mexico_delta = ["MX in excess", "MX minute 319"]
        df_utils.add_column_sum(df_cu_1906_2024, mexico_delta, "Mexico Delta")

        df_utils.subtract_column(df_cu_1906_2024, 'Mexico', 'Mexico Treaty', 'Delta')
        delta_map = {
            "Mexico Delta": "Delta",
        }
        df_utils.copy_columns_by_key(df_cu_1906_2024, df_cu_1906_2024, delta_map)

        if 0:
            series = [
                (df_cu_1906_2024, "Upper Basin", Colors.UB),
                (df_cu_1906_2024, "Mexico", lb.MX_COLOR),
                (df_cu_1906_2024, "CA", Colors.CA1),
                (df_cu_1906_2024, "AZ", Colors.AZ1),
                (df_cu_1906_2024, "NV", Colors.NV1),
            ]

            left_bar_series = []

            self.demand_pie_chart = PieChart(
                series,
                title=f'Colorado River {self.name}',
                year=self.current_year,
                left_bar_series=left_bar_series,
                version=self.version
            )
            self.charts.append(self.demand_pie_chart)

        self.create_demand_bar_chart(df_cu_1906_2024)
        self.create_reservoir_bar_chart(show_x_labels=False)
        self.on_line_moved(1922)

    def create_demand_bar_chart(self, df_cu_1906_2024: pd.DataFrame):
        series = ('', [
            (df_cu_1906_2024, "Upper Basin", Colors.UB),
        ])
        self.ub_demand_chart = MultiBarChart(
            title=f'Colorado River {self.name}     ver={self.version}',
            percentage=0.20,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=5.0,
            y_min=0,
            show_x_labels=False,
            legend_loc = 'upper left',
        )
        self.charts.append(self.ub_demand_chart)

        series = ('', [
            (df_cu_1906_2024, "CA", Colors.CA),
            (df_cu_1906_2024, "NV", Colors.NV1),
            (df_cu_1906_2024, "AZ", Colors.AZ),
            (df_cu_1906_2024, "Mexico Treaty",  Colors.MX),
            (self.demand.df_lb_cul, lb.LB_TRIBUTARY_CUL, 'orange'),
            (df_cu_1906_2024, "Cienega", Colors.MX_CIENEGA),
            (df_cu_1906_2024, "Delta", Colors.MX_DELTA),
        ])
        self.demand_chart = MultiBarChart(
            title=f'',
            percentage=0.60,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=15,
            y_min=0,
            show_x_labels=True,
            legend_loc='upper left',
        )
        self.charts.append(self.demand_chart)

    def on_line_moved(self, year):
        if self._syncing_lines or year == self.current_year:
            return

        self.current_year = year
        self._syncing_lines = True
        try:
            for chart in self.charts:
                if chart is None or not hasattr(chart, '_vline'):
                    continue
                if year in getattr(chart, 'year_to_idx', {}):
                    idx = chart.year_to_idx[year]
                    chart._vline.set_xdata([idx, idx])

                    # Year label (if this chart is showing one)
                    if getattr(chart, '_show_year_label', False):
                        chart._update_year_label(idx)

                    # Bar-segment value labels (if this chart is showing them)
                    if getattr(chart, '_show_bar_values', False):
                        chart._update_bar_value_labels(idx)

                    chart.fig.canvas.draw_idle()
        finally:
            self._syncing_lines = False

    def right_axis_annotations(self):
        if self.demand_chart is not None:
            ax = self.demand_chart.ax
            ChartFrame.annotate_level(ax, 9.0, '9.0',
                                          'black', draw_text=True, draw_line=True,
                                          left_of_axis=False)
            ChartFrame.annotate_level(ax, 8.25, '8.25',
                                          'black', draw_text=True, draw_line=True,
                                          left_of_axis=False)
            ChartFrame.annotate_level(ax, 7.5, '7.5',
                                          Colors.LB, draw_text=True, draw_line=True,
                                          left_of_axis=False)
            ChartFrame.annotate_level(ax, 4.4, '4.4',
                                          Colors.LB, draw_text=True, draw_line=True,
                                          left_of_axis=False)

    def _annotate_bottom(self, ax, year, label, offset_lines=0, color='black'):
        self.demand_chart.annotate_value(
            ax,
            year=year,
            label=label,
            color=color,
            position="below_bottom",
            draw_line=False,
            draw_outline=False,
            fontsize=7,
            offset_lines=offset_lines
        )

    def bottom_axis_annotations(self):
        if self.demand_chart is not None:
            ax = self.demand_chart.ax
            self._annotate_bottom(ax, 1906, "IID", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1908, "Palo Verde", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1909, "Gunnison", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1910, "SRP", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1922, "Compact")
            self._annotate_bottom(ax, 1915, "Grand\nValley", color=Colors.UB)
            self._annotate_bottom(ax, 1929, "BCPA", offset_lines=0)
            self._annotate_bottom(ax, 1931, "AZ v CA", offset_lines=2)
            self._annotate_bottom(ax, 1933, "Depression", offset_lines=1)
            self._annotate_bottom(ax, 1936, "Moffat", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1941, "MWD", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1944, "MX Treaty", offset_lines=1)
            self._annotate_bottom(ax, 1947, "Big Thompson", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1951, "Wellton", color=Colors.LB)
            self._annotate_bottom(ax, 1964, "Roberts", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1964, "AZ v CA")
            self._annotate_bottom(ax, 1971, "CUP", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1972, "Fryark", color=Colors.UB)
            self._annotate_bottom(ax, 1968, "CRBPA", offset_lines=1)
            self._annotate_bottom(ax, 1984, "Dolores", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1985, "CAP", color=Colors.LB)
            self._annotate_bottom(ax, 2003, "QSA", color=Colors.LB)
            self._annotate_bottom(ax, 2007, "2007\nGuidelines", offset_lines=1)
            self._annotate_bottom(ax, 2014, "Delta\nPulse", color=Colors.LB)
            self._annotate_bottom(ax, 2018, "DCP")

class Compact1922(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame, demand,
                         name='Boulder Canyon Project Act', start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        series = [
            (7_500_000, "Upper Basin", Colors.UT),
            (750_000, "Mexico", lb.MX_COLOR),
            (7_500_000, "Lower Basin", Colors.CA1),
            (1_000_000, "III(b)", Colors.CA2),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River Compact {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1929)

class Compact1929(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame, demand,
                         name='Boulder Canyon Project Act',  start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        series = [
            (7_500_000, "Upper Basin", Colors.UT),
            (750_000, "Mexico", lb.MX_COLOR),
            (4_400_000, "CA", Colors.CA1),
            (1_000_000, "III(b)", Colors.CA2),
            (300_000, "NV", Colors.NV2),
            (2_800_000, "AZ", Colors.AZ1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1929)

class Compact1944(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand:Demand):
        super().__init__(notebook_frame, demand,
                         name='Mexico Treaty',  start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        series = [
            (7_500_000, "Upper Basin", Colors.UT),
            (1_500_000, "Mexico", lb.MX_COLOR),
            (4_400_000, "CA", Colors.CA1),
            (1_000_000, "III(b)", Colors.CA2),
            (300_000, "NV", Colors.NV2),
            (2_800_000, "AZ", Colors.AZ1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1944)


if __name__ == "__main__":
    app = wx.App(False)

    rw = RiverWar()
    nf = NotebookFrame([], rw)

    d = Demand(rw, show_tributaries=False)

    # SupplyVDemand(nf, d)
    Demand1906To1971(nf, d)
    # Compact1922(nf, d)
    # Compact1929(nf, d)
    # Compact1944(nf, d)

    nf.Show()
    app.MainLoop()