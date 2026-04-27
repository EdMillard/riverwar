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
from chart.multi_bar_chart import MultiBarChart
from chart.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils

class FlowChartFrame(ChartFrame):
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
        df_utils.moving_average(natural_flow_data.df, ub.NATURAL_LEES_FERRY, 'Supply 10 yr avg')

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

        # ====================== DEMAND PIE CHART ======================
        totals = (0.0, 0.99, [
            ("Lower Basin", (df_lb_cul, lb.LB_TOTAL)),
            ("Upper Basin", (df_ub_cul, ub.UB_TOTAL)),
            ("Mexico", (df_lb_cul, lb.MEXICO)),
            ("Demand", (df_lb_cul, all_b.DEMAND))
        ])

        lb_totals = (0.9, 0.99, [
            ("CA", (df_lb_cul, lb.CA_TOTAL)),
            ("AZ", (df_lb_cul, lb.AZ_TOTAL)),
            ("NV", (df_lb_cul, lb.NV_TOTAL)),
            ('UT Trib', (df_lb_cul,  lb.UT_TRIBUTARY_CUL)),
            ('NM Trib', (df_lb_cul, lb.NM_TRIBUTARY_CUL)),
            ("LB Evap", (df_lb_cul, lb.LB_RESERVOIR_EVAP)),
            ("LB Demand", (df_lb_cul, lb.LB_TOTAL))
        ])

        evap_totals = (0.0, 0.05, [
            ("UB Evap", (df_ub_cul, ub.UB_RESERVOIR_EVAP)),
            ("LB Evap", (df_lb_cul, lb.LB_RESERVOIR_EVAP)),
            ("Salton Evap", (df_lb_cul, lb.SALTON_INFLOW)),
            ("Total", (df_lb_cul, all_b.EVAP_TOTAL))
        ])

        pie_wedges = [
            (df_ub_cul, ub.CU_CO, '#6060ff'),
            (df_ub_cul, ub.CU_UT, '#8080ff'),
            (df_ub_cul, ub.CU_WY, '#a0a0ff'),
            (df_ub_cul, ub.CU_NM, '#c0c0ff'),
            (df_ub_cul, ub.UB_RESERVOIR_EVAP, 'gold'),
            (df_lb_cul, lb.MEXICO, '#40a040'),
            (df_lb_cul, "UB State Tributaries in LB", 'darkblue'),
            (df_lb_cul, lb.LB_RESERVOIR_EVAP, 'gold'),
            (df_lb_cul, lb.SALTON_INFLOW, 'gold'),
            (df_lb_cul, lb.IMPERIAL_VALLEY_CU, '#c040c0'),
            (df_lb_cul, lb.CA_OUTSIDE_SYSTEM, '#e080e0'),
            (df_lb_cul, lb.CA_MAINSTEM, '#ffa0ff'),
            (df_lb_cul, lb.NV_TOTAL, 'orange'),
            (df_lb_cul, lb.AZ_CAP, '#ff8080'),
            (df_lb_cul, lb.AZ_MAINSTEM, '#ff4040'),
        ]
        if show_tributaries:
            pie_wedges.append((df_lb_cul, lb.AZ_GILA_CUL, '#c02020'))
            pie_wedges.append((df_lb_cul, lb.AZ_TRIBUTARY_CUL, 'maroon'))

        # ====================== SUPPLY BAR CHART ======================
        overlay_lines = [
            (df_lb_cul, all_b.DEMAND, 'darkred'),
            (natural_flow_data.df, 'Supply 10 yr avg', 'goldenrod', {"marker": "", "linewidth": 2.0}),
        ]
        underlay_lines = [
            (powell.df_annual, all_b.STORAGE, 'darkblue',  {"linestyle": "dotted", "marker": "", "linewidth": 2.0, "label": "Lake Powell"}),
        ]
        bar_groups = [
            ('Natural Flow', [(natural_flow_data.df, ub.NATURAL_LEES_FERRY, 'royalblue')])]

        a = [('Demand', [
                (df_lb_cul, lb.MEXICO, '#40a040'),
                (df_lb_cul, lb.CA_TOTAL, '#c040c0'),
                (df_ub_cul, ub.UB_TOTAL, 'royalblue'),
                (df_lb_cul, lb.AZ_TOTAL, '#ff0000'),
                (df_lb_cul, lb.NV_TOTAL, 'orange')])
            ]
        supply_demand = MultiBarChart(
            groups=bar_groups,
            underlay_lines=underlay_lines,
            overlay_lines=overlay_lines,
            title="Colorado River Supply vs Demand",
            start_year = 1906,
            # start_year=self.start_year,
            end_year=self.end_year,
            # y_max=25.0,
        )
        self.charts.append(supply_demand)

        # ====================== NATURAL FLOW BAR CHART ======================
        df_maf = powell.df_annual

        overlay_lines = [
            (natural_flow_data.df, 'Supply 10 yr avg', 'goldenrod', {"marker": "", "linewidth": 2.0}),
        ]
        df_utils.subtract_columns_by_year(natural_flow_data.df, ub.NATURAL_LEES_FERRY, 'Lost', [(df_ub_cul, ub.UB_TOTAL), (df_maf, all_b.INFLOW_UNREGULATED)])
        bar_groups = [
            ('Natural', [(natural_flow_data.df, ub.NATURAL_LEES_FERRY, 'green')]),
            # ('Actual', [(df_ub_cul, ub.UB_TOTAL, 'darkred'), (df_maf, all_b.INFLOW, 'royalblue')]),
            ('Actual', [(df_ub_cul, ub.UB_TOTAL, 'darkred'), (df_maf, all_b.INFLOW_UNREGULATED, 'royalblue')]),
        ]
        supply_demand = MultiBarChart(
            groups=bar_groups,
            underlay_lines=underlay_lines,
            overlay_lines=overlay_lines,
            title="",
            start_year = 1999,
            # start_year=self.start_year,
            end_year=self.end_year,
            # y_min=1999,
        )
        # self.charts.append(supply_demand)

        # ============= POWELL INFLOW OUTFLOW BAR CHART ==============
        bar_groups = [
            ('Release', [(df_maf, all_b.RELEASE, 'darkred')]),
            ('Inflow', [(df_maf, all_b.INFLOW, 'royalblue')]),
        ]
        powell_inflow_outflow = MultiBarChart(
            groups=bar_groups,
            # underlay_lines=underlay_lines,
            # overlay_lines=overlay_lines,1
            title="Powell Inflow Outflow",
            start_year=self.start_year,
            end_year=self.end_year,
            # x_min=1999,
            # y_max=16.0,
            # y_units='MAF'
        )
        # self.charts.append(powell_inflow_outflow)

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