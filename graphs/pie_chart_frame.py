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
from chart.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils

class PieChartFrame(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.start_year = 1971
        self.end_year = 2024
        self.current_year = self.start_year
        self.timer = None
        self.animation_interval = 1000

        super().__init__(notebook_frame, page_name='Pie Chart')

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
        river_war = self.notebook_frame.river_war
        show_tributaries = True

        # ====================== UPPER BASIN ======================
        ub_cul = river_war.dataset.get('Upper Basin Cul')
        df_ub_cul = ub_cul.df

        # ====================== LAKE POWELL ======================
        powell = river_war.reservoir.get('Lake Powell')
        powell.load_data_annual(self.start_year, self.end_year)

        # ====================== LOWER BASIN ======================
        lb_cul = river_war.dataset.get('Lower Basin Cul')
        df_lb_cul = lb_cul.df

        # ====================== NATURAL FLOW ======================
        natural_flow_data = river_war.dataset.get('Natural Flow')

        # ====================== AZ Aquifter ======================
        az_ltsc_data = river_war.dataset.get('Az Ltsc')

        # Final totals
        df_utils.add_columns_across_dfs([
            (df_ub_cul, ub.UB_RESERVOIR_EVAP),
            (df_lb_cul, lb.LB_RESERVOIR_EVAP),
            (df_lb_cul, lb.SALTON_INFLOW)],
            df_lb_cul, all_b.EVAP_TOTAL)

        df_utils.add_columns_across_dfs([
            (df_lb_cul, lb.CA_TOTAL),
            (df_lb_cul, lb.AZ_TOTAL),
            (df_lb_cul, lb.NV_TOTAL),
            (df_lb_cul, lb.LB_RESERVOIR_EVAP)],
            df_lb_cul, lb.LB_TOTAL)

        df_utils.add_columns_across_dfs([
            (df_ub_cul, ub.UB_TOTAL),
            (df_lb_cul, lb.LB_TOTAL),
            (df_lb_cul, lb.MEXICO)],
            df_lb_cul, all_b.DEMAND)

        df_utils.add_columns_across_dfs([
            (df_lb_cul, lb.UT_TRIBUTARY_CUL),
            (df_lb_cul, lb.NM_TRIBUTARY_CUL)],
            df_lb_cul, "UB State Tributaries in LB")

        df_utils.add_columns_across_dfs([
            (natural_flow_data.df, ub.NATURAL_LEES_FERRY)],
            natural_flow_data.df, all_b.SUPPLY)

        if show_tributaries:
            df_utils.add_columns_across_dfs([
                (df_lb_cul, lb.GILA_CUL)],
                natural_flow_data.df, all_b.SUPPLY)
            df_utils.moving_average(natural_flow_data.df, ub.SUPPLY, all_b.SUPPLY_3_YEAR_AVG, window=3)

        # ====================== DEMAND PIE CHART ======================
        totals = (0.0, 0.99, [
            ("Lower Basin", (df_lb_cul, lb.LB_TOTAL)),
            ("Upper Basin", (df_ub_cul, ub.UB_TOTAL)),
            ("Mexico", (df_lb_cul, lb.MEXICO)),
            ("Demand", (df_lb_cul, all_b.DEMAND))
        ])

        lb_totals = (0.85, 0.99, [
            ("CA", (df_lb_cul, lb.CA_TOTAL)),
            ("AZ", (df_lb_cul, lb.AZ_TOTAL)),
            ("NV", (df_lb_cul, lb.NV_TOTAL)),
            ('UT Trib', (df_lb_cul,  lb.UT_TRIBUTARY_CUL)),
            ('NM Trib', (df_lb_cul, lb.NM_TRIBUTARY_CUL)),
            ("LB Evap", (df_lb_cul, lb.LB_RESERVOIR_EVAP)),
            ("LB Demand", (df_lb_cul, lb.LB_TOTAL))
        ])

        evap_totals = (0.0, 0.02, [
            ("UB Evap", (df_ub_cul, ub.UB_RESERVOIR_EVAP)),
            ("LB Evap", (df_lb_cul, lb.LB_RESERVOIR_EVAP)),
            ("Salton Evap", (df_lb_cul, lb.SALTON_INFLOW)),
            ("Total", (df_lb_cul, all_b.EVAP_TOTAL))
        ])

        ltsc_df = az_ltsc_data.df
        df_utils.subtract_columns_across_dfs(df_lb_cul, lb.AZ_MAINSTEM, [(df_lb_cul, lb.AZ_CRIT_CU), (df_lb_cul, lb.WELLTON_MOHAWK_CU)], result_column=lb.AZ_MAINSTEM)
        df_utils.subtract_columns_across_dfs(df_lb_cul, lb.AZ_CAP, [(ltsc_df, 'Stored')], result_column=lb.AZ_CAP)
        df_utils.subtract_columns_across_dfs(df_lb_cul, lb.CA_MAINSTEM, [(df_lb_cul, lb.PALO_VERDE_CU)], result_column=lb.CA_MAINSTEM)
        pie_wedges = [
            (df_ub_cul, ub.CU_CO, '#6060ff'),
            (df_ub_cul, ub.CU_UT, '#8080ff'),
            (df_ub_cul, ub.CU_WY, '#a0a0ff'),
            (df_ub_cul, ub.CU_NM, '#c0c0ff'),
            (df_ub_cul, ub.UB_RESERVOIR_EVAP, 'gold'),
            (df_lb_cul, lb.MEXICO, '#40a040'),
            (df_lb_cul, lb.LB_RESERVOIR_EVAP, 'gold'),
            (df_lb_cul, lb.SALTON_INFLOW, 'gold', {'hatch': '-','hatch_color': '#c040c0'}),
            (df_lb_cul, lb.IMPERIAL_VALLEY_CU, '#c040c0', {'label': 'Imperial Valley'}),
            (df_lb_cul, lb.CA_OUTSIDE_SYSTEM, '#e080e0', {'label': 'Metropolitan'}),
            (df_lb_cul, lb.CA_MAINSTEM, '#f070f0'),
            (df_lb_cul, lb.PALO_VERDE_CU, '#ffa0ff', {'label': 'Palo Verde'}),
            (df_lb_cul, lb.NV_TOTAL, 'orange', {'label': 'NV'}),
            (ltsc_df, 'Stored', 'gold', {'label': 'CAP Aquifer Store', 'hatch': '|', 'hatch_color': '#ff8080'}),
            (df_lb_cul, lb.AZ_CAP, '#ff8080', {'label': 'CAP'}),
            (df_lb_cul, lb.AZ_CRIT_CU, '#ff6060', {'label': 'CRIT'}),
            (df_lb_cul, lb.WELLTON_MOHAWK_CU, '#ff4040', {'label': 'Wellton Mohawk'}),
            (df_lb_cul, lb.AZ_MAINSTEM, '#ef0000'),
        ]
        if show_tributaries:
            pie_wedges.append((df_lb_cul, lb.AZ_TRIBUTARY_CUL, '#d03030', {'label': 'AZ Trib'}))
            pie_wedges.append((df_lb_cul, lb.AZ_GILA_CUL, '#c02020', {'label': 'AZ Gila'}))
            pie_wedges.append((df_lb_cul, "UB State Tributaries in LB", 'darkblue'))

            df_utils.add_columns_across_dfs([
                (df_lb_cul, "UB State Tributaries in LB"),
                (df_lb_cul, lb.LB_TOTAL)
            ],
                df_lb_cul, 'LB Total with UB Tributaries')
        radial_lines = [
            (df_lb_cul, 'LB Total with UB Tributaries', 'white'),
            (df_lb_cul, lb.MEXICO, 'white'),
            (df_ub_cul, ub.UB_TOTAL, 'white'),
        ]

        left_bar_series = [
            (df_lb_cul, all_b.DEMAND, 'maroon'),
            (natural_flow_data.df, all_b.SUPPLY_3_YEAR_AVG, 'green'),
        ]

        self.demand_pie_chart = PieChart(
            pie_wedges,
            title='Colorado River Supply v Demand',
            year=self.current_year,
            annotations=[totals, lb_totals, evap_totals],
            radial_lines=radial_lines,
            left_bar_series=left_bar_series,
            left_bar_ymax=27.0,
            left_bar_ymin=10.0
        )
        self.charts.append(self.demand_pie_chart)

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