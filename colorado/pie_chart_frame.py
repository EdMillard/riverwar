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
import pandas as pd
from sheet import sheet
from chart.multi_bar_chart import MultiBarChart
from colorado.lb_mainstream_cul import LBMainstreamCUL
from colorado.lb_reservoir_cul import LBReservoirCUL
from colorado.lb_tributary_cul import LBTributaryCUL
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

    def on_play_pause(self, event):
        """Toggle animation"""
        if self.timer is None or not self.timer.IsRunning():
            self.start_animation()
            self.play_btn.SetLabel("⏸ Pause")
        else:
            self.stop_animation()
            self.play_btn.SetLabel("▶ Start Animation")

    def on_slider_changed(self, event):
        """Jump to selected year"""
        new_year = self.year_slider.GetValue()
        if new_year != self.current_year:
            self.current_year = new_year
            self.pie_chart.update_for_year(self.current_year)
            if hasattr(self, 'toolbar_status'):
                self.toolbar_status.SetLabel(f"Year: {self.current_year}")

    def load_charts(self):
        headers = [ub.UB_TOTAL, ub.CU_CO, ub.CU_UT, ub.CU_WY, ub.CU_NM, ub.AZ_CU,
                   ub.POWELL_EVAPORATION, ub.FLAMING_GORGE_EVAPORATION_WY,
                   ub.BLUE_MESA_EVAPORATION_WY, ub.MORROW_EVAPORATION_WY]

        df_ub_cul: pd.DataFrame = df_utils.create_df(self.start_year, self.end_year, headers)
        show_tributaries = False

        # ====================== UPPER BASIN ======================
        sheet.upper_basin_cul_from_excel(df_ub_cul, row_offset=0, divisor=1)

        df_utils.add_column_sum(df_ub_cul,
                                [ub.POWELL_EVAPORATION, ub.FLAMING_GORGE_EVAPORATION_WY,
                                 ub.BLUE_MESA_EVAPORATION_WY, ub.MORROW_EVAPORATION_WY],
                                ub.UB_RESERVOIR_EVAP)

        # ====================== LAKE POWELL ======================
        powell = self.notebook_frame.reservoir_registry.get('Lake Powell')
        powell.load_data_annual(self.start_year, self.end_year)

        # ====================== LOWER BASIN ======================
        df_empty = pd.DataFrame()

        lb_mainstream_cul = LBMainstreamCUL(all_b.LB_MAINSTEM_CUL_SHEET)
        lb_mainstream_cul.load_df(df_empty)

        # Lower Basin Reservoir Evap
        lb_reservoirs_cul = LBReservoirCUL(all_b.LB_RESERVOIRS_CUL_SHEET)
        lb_reservoirs_cul.load_df(df_empty)
        df_utils.add_column_sum(lb_reservoirs_cul.df,
                                [lb.LAKE_MEAD_CUL, lb.LAKE_MOHAVE_CUL, lb.LAKE_HAVASU_CUL,
                                 lb.SENATOR_WASH_CUL, lb.DIVERSION_DAMS_CUL],
                                lb.LB_RESERVOIR_EVAP)

        # California - Imperial Valley
        sheet.usgs_annuals(lb_mainstream_cul.df, '10254730', self.start_year, self.end_year, title=lb.ALAMO_RIVER, divisor=1)
        sheet.usgs_annuals(lb_mainstream_cul.df, '10255550', self.start_year, self.end_year, title=lb.NEW_RIVER, divisor=1)
        sheet.usgs_annuals(lb_mainstream_cul.df, '10259540', self.start_year, self.end_year, title=lb.WHITEWATER, divisor=1)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.ALAMO_RIVER, lb.NEW_RIVER, lb.WHITEWATER], lb.SALTON_INFLOW)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_imperial_irrigation_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.IMPERIAL_CU, divisor=1)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_coachella_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.COACHELLA_CU, divisor=1)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.IMPERIAL_CU, lb.COACHELLA_CU], lb.IMPERIAL_VALLEY_CU)

        df_cu = sheet.read_csv('data/USBR_Reports/ca/usbr_ca_metropolitan_consumptive_use.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_cu, lb.METROPOLITAN_CU, divisor=1)

        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.CA_M_I_OTHER, lb.CA_AGRICULTURE], lb.CA_MAINSTEM)

        df_utils.subtract_column(lb_mainstream_cul.df, lb.CA_OUTSIDE_SYSTEM, lb.IMPERIAL_VALLEY_CU, lb.CA_OUTSIDE_SYSTEM)
        df_utils.subtract_column(lb_mainstream_cul.df, lb.IMPERIAL_VALLEY_CU, lb.SALTON_INFLOW, lb.IMPERIAL_VALLEY_CU)

        # Mexico
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_mx, lb.MEXICO, divisor=1)

        # California continued
        df_utils.add_column_sum(lb_mainstream_cul.df,
                                [lb.CA_OUTSIDE_SYSTEM, lb.CA_MAINSTEM, lb.SALTON_INFLOW, lb.IMPERIAL_VALLEY_CU],
                                lb.CA_TOTAL)

        # Nevada
        lb_tributary_cul = None
        if show_tributaries:
            lb_tributary_cul = LBTributaryCUL(all_b.LB_TRIBUTARY_CUL_SHEET)
            lb_tributary_cul.load_df(df_empty)
            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.NV_VIRGIN_CUL,
                                     lb.NV_MUDDY_CUL,
                                     lb.NV_TRIB_ABOVE_LAKE_MEAD_CUL],
                                    lb.NV_TRIBUTARY_CUL)

        df_utils.add_columns_across_dfs([(lb_mainstream_cul.df, lb.NV_M_I_OTHER),
                                         (lb_mainstream_cul.df, lb.NV_AGRICULTURE),
                                         (lb_mainstream_cul.df, lb.NV_POWER)],
                                        lb_mainstream_cul.df, lb.NV_TOTAL)
        if show_tributaries:
            df_utils.add_columns_across_dfs([(lb_mainstream_cul.df, lb.NV_TOTAL),
                                             (lb_tributary_cul.df, lb.NV_TRIBUTARY_CUL)],
                                            lb_mainstream_cul.df, lb.NV_TOTAL)

        # Arizona Mainstem
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.AZ_M_I_OTHER, lb.AZ_AGRICULTURE, lb.AZ_POWER], lb.AZ_MAINSTEM)
        df_utils.rename_column(lb_mainstream_cul.df, lb.AZ_WITHIN_SYSTEM, lb.AZ_CAP, inplace=True)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.AZ_CAP, lb.AZ_MAINSTEM], lb.AZ_COLORADO_RIVER_TOTAL)

        # Arizona Tributary
        if show_tributaries:
            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_LITTLE_COLORADO_CUL,
                                     lb.AZ_VIRGIN_CUL,
                                     lb.AZ_BILL_WILLIAMS_CUL,
                                     lb.AZ_TRIB_BELOW_LAKE_MEAD_CUL],
                                    lb.AZ_TRIBUTARY_CUL)
            df_utils.add_columns_across_dfs([
                (lb_mainstream_cul.df, lb.AZ_COLORADO_RIVER_TOTAL),
                (lb_tributary_cul.df, lb.AZ_GILA_CUL),
                (lb_tributary_cul.df, lb.AZ_TRIBUTARY_CUL)],
                lb_mainstream_cul.df, lb.AZ_TOTAL)
        else:
            df_utils.add_columns_across_dfs([
                (lb_mainstream_cul.df, lb.AZ_COLORADO_RIVER_TOTAL)],
                lb_mainstream_cul.df, lb.AZ_TOTAL)

        # Final totals
        df_utils.add_columns_across_dfs([
            (df_ub_cul, ub.UB_RESERVOIR_EVAP),
            (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP),
            (lb_mainstream_cul.df, lb.SALTON_INFLOW)],
            lb_mainstream_cul.df, all_b.EVAP_TOTAL)

        df_utils.add_columns_across_dfs([
            (lb_mainstream_cul.df, lb.CA_TOTAL),
            (lb_mainstream_cul.df, lb.AZ_TOTAL),
            (lb_mainstream_cul.df, lb.NV_TOTAL),
            (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP)],
            lb_mainstream_cul.df, lb.LB_TOTAL)

        df_utils.add_columns_across_dfs([
            (df_ub_cul, ub.UB_TOTAL),
            (lb_mainstream_cul.df, lb.LB_TOTAL),
            (lb_mainstream_cul.df, lb.MEXICO)],
            lb_mainstream_cul.df, all_b.DEMAND)

        # ====================== DEMAND PIE CHART ======================
        totals = (0.0, 0.99, [
            ("Lower Basin", (lb_mainstream_cul.df, lb.LB_TOTAL)),
            ("Upper Basin", (df_ub_cul, ub.UB_TOTAL)),
            ("Mexico", (lb_mainstream_cul.df, lb.MEXICO)),
            ("Demand", (lb_mainstream_cul.df, all_b.DEMAND))
        ])

        lb_totals = (0.9, 0.99, [
            ("CA", (lb_mainstream_cul.df, lb.CA_TOTAL)),
            ("AZ", (lb_mainstream_cul.df, lb.AZ_TOTAL)),
            ("NV", (lb_mainstream_cul.df, lb.NV_TOTAL)),
            ("LB Evap", (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP)),
            ("LB Demand", (lb_mainstream_cul.df, lb.LB_TOTAL))
        ])

        evap_totals = (0.0, 0.05, [
            ("UB Evap", (df_ub_cul, ub.UB_RESERVOIR_EVAP)),
            ("LB Evap", (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP)),
            ("Salton Evap", (lb_mainstream_cul.df, lb.SALTON_INFLOW)),
            ("Total", (lb_mainstream_cul.df, all_b.EVAP_TOTAL))
        ])

        pie_wedges = [
            (df_ub_cul, ub.CU_CO, '#6060ff'),
            (df_ub_cul, ub.CU_UT, '#8080ff'),
            (df_ub_cul, ub.CU_WY, '#a0a0ff'),
            (df_ub_cul, ub.CU_NM, '#c0c0ff'),
            (df_ub_cul, ub.UB_RESERVOIR_EVAP, 'gold'),
            (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP, 'gold'),
            (lb_mainstream_cul.df, lb.MEXICO, '#40a040'),
            (lb_mainstream_cul.df, lb.SALTON_INFLOW, 'gold'),
            (lb_mainstream_cul.df, lb.IMPERIAL_VALLEY_CU, '#c040c0'),
            (lb_mainstream_cul.df, lb.CA_OUTSIDE_SYSTEM, '#e080e0'),
            (lb_mainstream_cul.df, lb.CA_MAINSTEM, '#ffa0ff'),
            (lb_mainstream_cul.df, lb.NV_TOTAL, 'orange'),
            (lb_mainstream_cul.df, lb.AZ_MAINSTEM, '#ffa0a0'),
            (lb_mainstream_cul.df, lb.AZ_CAP, '#ff8080')
        ]
        if show_tributaries:
            pie_wedges.append((lb_tributary_cul.df, lb.AZ_GILA_CUL, '#ff4040'))
            pie_wedges.append((lb_tributary_cul.df, lb.AZ_TRIBUTARY_CUL, '#ff4040'))

        demand_pie_chart = PieChart(
            pie_wedges,
            title='Colorado River Supply and Demand',
            year=self.current_year,
            annotations=[totals, lb_totals, evap_totals]
        )
        # self.charts.append(demand_pie_chart)

        # ====================== SUPPLY BAR CHART ======================
        # Natural Flow
        natural_flow_data = self.notebook_frame.dataset_registry.get('Natural Flow')
        df_utils.moving_average(natural_flow_data.df, ub.SUPPLY, 'Supply 10 yr avg')

        overlay_lines = [
            (lb_mainstream_cul.df, all_b.DEMAND, 'darkred'),
            (natural_flow_data.df, 'Supply 10 yr avg', 'goldenrod', {"marker": "", "linewidth": 2.0}),
        ]
        underlay_lines = [
            (powell.df_annual, all_b.STORAGE, 'darkblue',  {"linestyle": "dotted", "marker": "", "linewidth": 2.0, "label": "Lake Powell"}),
        ]
        bar_groups = [
            ('Supply', [(natural_flow_data.df, ub.SUPPLY, 'royalblue')])]

        a = [('Demand', [
                (lb_mainstream_cul.df, lb.MEXICO, '#40a040'),
                (lb_mainstream_cul.df, lb.CA_TOTAL, '#c040c0'),
                (df_ub_cul, ub.UB_TOTAL, 'royalblue'),
                (lb_mainstream_cul.df, lb.AZ_TOTAL, '#ff0000'),
                (lb_mainstream_cul.df, lb.NV_TOTAL, 'orange')])
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
        df_utils.subtract_columns_by_year(natural_flow_data.df, ub.SUPPLY, 'Lost', [(df_ub_cul, ub.UB_TOTAL), (df_maf, all_b.INFLOW)])
        bar_groups = [
            ('UB CUL', [(df_ub_cul, ub.UB_TOTAL, 'darkred')]),
            ('Inflow', [ (df_maf, all_b.INFLOW, 'royalblue')]),
            ('Supply', [(natural_flow_data.df, 'Surplus', 'darkgreen')])]
        supply_demand = MultiBarChart(
            groups=bar_groups,
            underlay_lines=underlay_lines,
            overlay_lines=overlay_lines,
            title="",
            start_year = 1964,
            # start_year=self.start_year,
            end_year=self.end_year,
            # y_max=25.0,
        )
        self.charts.append(supply_demand)

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
        self.charts.append(powell_inflow_outflow)

    def start_animation(self):
        if self.timer is None:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
            self.timer.Start(self.animation_interval)

    def stop_animation(self):
        if self.timer is not None:
            self.timer.Stop()
            self.timer = None

    def on_timer(self, event: wx.TimerEvent):
        """Called every 1 second to advance the year"""
        if self.current_year > self.end_year:
            self.stop_animation()
            return

        self.pie_chart.update_for_year(self.current_year)
        self.current_year += 1