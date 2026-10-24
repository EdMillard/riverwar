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
from sheet import sheet
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
from chart.multi_bar_chart import MultiBarChart, BarGroup, BarSeries
from colorado.river_war import RiverWar
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from api import df_utils
from typing import Optional, List, Any, Tuple

CO_COLOR_1 = '#c050c0'
UT_COLOR = '#8080ff'
WY_COLOR = '#a0a0ff'
NM_COLOR = '#c0c0ff'
CA_COLOR_4 = '#ff8080'
CA_COLOR_3 = '#ff6060'
CA_COLOR_2 = '#ff4040'
CA_COLOR_1 = '#ef2828'
NV_COLOR_2 = 'lightgray'
NV_COLOR_1 = 'gray'
AZ_COLOR = '#cd5906'
AZ_COLOR_1 = '#ef5926'
AZ_COLOR_2 = '#ef6936'
AZ_COLOR_3 = '#ef7946'
AZ_COLOR_4 = '#ef8956'
AZ_COLOR_5 = '#ef9966'
AZ_COLOR_6 = '#efbb77'
AZ_COLOR_7 = '#efdd99'
UB_COLOR = '#8080ff'


class DemandData:
    def __init__(self):
        self.df_ub_cul: Optional[pd.DataFrame] = None
        self.df_lb_cul: Optional[pd.DataFrame] = None
        self.df_ub_users: Optional[pd.DataFrame] = None
        self.az_ltsc_data: Optional[pd.DataFrame] = None
        self.natural_flow_data: Optional[pd.DataFrame] = None

        self.totals: Optional[Tuple, List[Any]] = None
        self.lb_totals: Optional[Tuple, List[Any]] = None
        self.evap_totals: Optional[Tuple, List[Any]] = None
        self.trib_totals: Optional[Tuple, List[Any]] = None

    @staticmethod
    def build_demand_cul(df_ub_cul, df_lb_cul, ltsc_df, show_tributaries=False):
        series = [
            (df_ub_cul, ub.CO_WEST_SLOPE, CO_COLOR_1),
            (df_ub_cul, ub.CU_UT, UT_COLOR),
            (df_ub_cul, ub.CU_WY, WY_COLOR),
            (df_ub_cul, ub.CU_NM, NM_COLOR),
            (df_ub_cul, ub.UB_RESERVOIR_EVAP, all_b.EVAP_COLOR),
            (df_lb_cul, lb.MEXICO, lb.MX_COLOR),
            (df_lb_cul, lb.LB_RESERVOIR_EVAP, all_b.EVAP_COLOR),
            (df_lb_cul, lb.SALTON_INFLOW, all_b.EVAP_COLOR, {'hatch': '-', 'hatch_color': '#c040c0'}),
            (df_lb_cul, lb.IMPERIAL_VALLEY_CU, CA_COLOR_1, {'label': 'Imperial Valley'}),
            (df_lb_cul, lb.CA_OUTSIDE_SYSTEM, CA_COLOR_2, {'label': 'Metropolitan'}),
            (df_lb_cul, lb.CA_MAINSTEM, CA_COLOR_4),
            (df_lb_cul, lb.PALO_VERDE_CU, CA_COLOR_3, {'label': 'Palo Verde'}),
            (df_lb_cul, lb.NV_COLORADO_RIVER_TOTAL, NV_COLOR_2, {'label': 'NV'}),
            (df_lb_cul, lb.NV_TRIBUTARY_CUL, NV_COLOR_1, {'label': 'NV Trib'}),
            (ltsc_df, lb.AZ_LTSC_STORED, AZ_COLOR_7, {'label': 'CAP Aquifer Store', 'hatch': '|', 'hatch_color': '#ff8080'}),
            (df_lb_cul, lb.AZ_CAP, AZ_COLOR_6, {'label': 'CAP'}),
            (df_lb_cul, lb.AZ_CRIT_CU, AZ_COLOR_5, {'label': 'CRIT'}),
            (df_lb_cul, lb.WELLTON_MOHAWK_CU, AZ_COLOR_4, {'label': 'Wellton Mohawk'}),
            (df_lb_cul, lb.AZ_MAINSTEM, AZ_COLOR_3),
        ]
        if show_tributaries:
            series.append((df_lb_cul, lb.AZ_TRIBUTARY_CUL, AZ_COLOR_2, {'label': 'AZ Trib'}))
            series.append((df_lb_cul, lb.AZ_GILA_CUL, AZ_COLOR_1, {'label': 'AZ Gila'}))
            series.append((df_lb_cul, lb.UB_STATE_TRIB_IN_LB, 'darkblue'))
        return series

    def build_data(self, river_war, show_tributaries=False)->List:
        # ====================== UPPER BASIN ======================
        ub_cul = river_war.dataset.get('Upper Basin Cul')
        self.df_ub_cul = ub_cul.df

        ub_users = river_war.dataset.get('Upper Basin Users')
        self.df_ub_users = ub_users.df

        # ====================== LOWER BASIN ======================
        lb_cul = river_war.dataset.get('Lower Basin Cul')
        self.df_lb_cul = lb_cul.df

        # ====================== NATURAL FLOW ======================
        self.natural_flow_data = river_war.dataset.get('Natural Flow')

        # ====================== AZ Aquifer ======================
        self.az_ltsc_data = river_war.dataset.get('Az Ltsc')

        series = self.build_totals(show_tributaries)
        return series

    def build_totals(self, show_tributaries=False):
        # Final totals
        df_utils.add_columns_across_dfs([
            (self.df_ub_cul, ub.UB_RESERVOIR_EVAP),
            (self.df_lb_cul, lb.LB_RESERVOIR_EVAP),
            (self.df_lb_cul, lb.SALTON_INFLOW)],
            self.df_lb_cul, all_b.EVAP_TOTAL)

        df_utils.add_columns_across_dfs([
            (self.df_lb_cul, lb.CA_TOTAL),
            (self.df_lb_cul, lb.AZ_TOTAL),
            (self.df_lb_cul, lb.NV_TOTAL),
            (self.df_lb_cul, lb.LB_RESERVOIR_EVAP)],
            self.df_lb_cul, lb.LB_TOTAL)

        df_utils.add_columns_across_dfs([
            (self.df_ub_cul, ub.UB_TOTAL),
            (self.df_lb_cul, lb.LB_TOTAL),
            (self.df_lb_cul, lb.MEXICO)],
            self.df_lb_cul, all_b.DEMAND)

        df_utils.add_columns_across_dfs([
            (self.df_lb_cul, lb.UT_TRIBUTARY_CUL),
            (self.df_lb_cul, lb.NM_TRIBUTARY_CUL)],
            self.df_lb_cul, lb.UB_STATE_TRIB_IN_LB)

        df_utils.add_columns_across_dfs([
            (self.natural_flow_data.df, ub.NATURAL_LEES_FERRY)],
            self.natural_flow_data.df, all_b.SUPPLY)

        if show_tributaries:
            df_utils.add_columns_across_dfs([
                (self.df_lb_cul, lb.GILA_CUL)],
                self.natural_flow_data.df, all_b.SUPPLY)
            df_utils.moving_average(self.natural_flow_data.df, ub.SUPPLY, all_b.SUPPLY_3_YEAR_AVG, window=3)

        # ====================== DEMAND PIE CHART ======================
        self.totals = (0.0, 0.99, [
            ("Lower Basin", (self.df_lb_cul, lb.LB_TOTAL), 'maroon'),
            ("Upper Basin", (self.df_ub_cul, ub.UB_TOTAL), 'royalblue'),
            ("Mexico", (self.df_lb_cul, lb.MEXICO), 'darkgreen'),
            ("Demand", (self.df_lb_cul, all_b.DEMAND))
        ])

        self.lb_totals = (0.85, 0.99, [
            ("CA", (self.df_lb_cul, lb.CA_TOTAL), CA_COLOR_1),
            ("AZ", (self.df_lb_cul, lb.AZ_TOTAL), AZ_COLOR),
            ("NV", (self.df_lb_cul, lb.NV_TOTAL), 'darkgray'),
            ("LB Evap", (self.df_lb_cul, lb.LB_RESERVOIR_EVAP), '#c5a67a'),
            ("LB Demand", (self.df_lb_cul, lb.LB_TOTAL), 'maroon')
        ])

        self.evap_totals = (0.0, 0.02, [
            ("UB Evap", (self.df_ub_cul, ub.UB_RESERVOIR_EVAP), '#c5a67a'),
            ("LB Evap", (self.df_lb_cul, lb.LB_RESERVOIR_EVAP), '#c5a67a'),
            ("Salton Evap", (self.df_lb_cul, lb.SALTON_INFLOW), '#c5a67a'),
            ("Total", (self.df_lb_cul, all_b.EVAP_TOTAL))
        ])

        self.trib_totals = (0.85, 0.07, [
            ("AZ Gila", (self.df_lb_cul, lb.AZ_GILA_CUL), AZ_COLOR),
            ("AZ Trib", (self.df_lb_cul, lb.AZ_TRIBUTARY_CUL), AZ_COLOR),
            ("NV Trib", (self.df_lb_cul, lb.NV_TRIBUTARY_CUL), 'darkgray'),
            ("UT Trib", (self.df_lb_cul, lb.UT_TRIBUTARY_CUL), UT_COLOR),
            ("NM Trib", (self.df_lb_cul, lb.NM_TRIBUTARY_CUL), NM_COLOR),
            ("Total", (self.df_lb_cul, lb.LB_TRIBUTARY_CUL))
        ])

        # AZ CAP/Aquifer LTSC
        ltsc_df = self.az_ltsc_data.df
        df_utils.subtract_columns_across_dfs(self.df_lb_cul, lb.AZ_MAINSTEM,
                                             [(self.df_lb_cul, lb.AZ_CRIT_CU),
                                              (self.df_lb_cul, lb.WELLTON_MOHAWK_CU)], result_column=lb.AZ_MAINSTEM)
        df_utils.subtract_columns_across_dfs(self.df_lb_cul, lb.AZ_CAP, [(ltsc_df, lb.AZ_LTSC_STORED)],
                                             result_column=lb.AZ_CAP)

        # CA Mainstem
        df_utils.subtract_columns_across_dfs(self.df_lb_cul, lb.CA_MAINSTEM, [(self.df_lb_cul, lb.PALO_VERDE_CU)],
                                             result_column=lb.CA_MAINSTEM)

        series = DemandData.build_demand_cul(self.df_ub_cul, self.df_lb_cul, ltsc_df, show_tributaries=True)

        if show_tributaries:
            df_utils.add_columns_across_dfs([
                (self.df_lb_cul, lb.UB_STATE_TRIB_IN_LB),
                (self.df_lb_cul, lb.LB_TOTAL)
            ], self.df_lb_cul, 'LB Total with UB Tributaries')
        return series

class PieChartFrame(ChartFrame):
    """Base class that centralizes common initialization for pie-chart frames."""

    def __init__(self, notebook: NotebookFrame, demand_data_: DemandData, pie_wedges_,
                 name: str, start_year:int, end_year:int, version: float = 0.4):
        self.name = name
        self.start_year = start_year
        self.current_year = self.start_year
        self.end_year = end_year
        self.demand_data: Optional[DemandData] = demand_data_
        self.pie_wedges = pie_wedges_

        self.timer = None
        self.animation_interval = 1000
        self.version = version
        self.play_btn = None
        self.year_slider = None
        self.toolbar_status = None
        self.year_prev = 0

        # self.start_year = 0
        # self.current_year = 0
        # self.end_year = 0

        self.demand_pie_chart: Optional[PieChart] = None
        self.multi_bar_chart: Optional[MultiBarChart] = None

        super().__init__(notebook, page_name=self.name)

    def create_reservoir_bar_chart(self):
        # ============= BIG 2 RESERVOIR BAR CHART ==============
        lake_powell = LakePowell(upstream=[])
        df_powell = lake_powell.load_data_annual(start_year=self.start_year)
        df_powell = df_utils.extend_years_with_zero(df_powell, 1906)

        lake_mead = LakeMead(upstream=[lake_powell])
        df_mead = lake_mead.load_data_annual(start_year=self.start_year)
        df_mead = df_utils.extend_years_with_zero(df_mead, 1906)

        mead_bar = BarGroup(
            label="=", series=[BarSeries(df=df_mead, col=all_b.STORAGE, color="maroon", label="Mead")]
        )
        powell_bar = BarGroup(
            label="=", series=[BarSeries(df=df_powell, col=all_b.STORAGE, color="royalblue", label="Powell")]
        )
        # today = datetime.today().date()
        self.multi_bar_chart = MultiBarChart(
            percentage=0.15,
            groups=[mead_bar, powell_bar],
            title="",
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=27,
            y_min=3,
            show_x_labels=True
        )
        self.charts.append(self.multi_bar_chart)

    def on_line_moved(self, year):
        if year == self.current_year:
            return
        self.current_year = year
        if self.demand_pie_chart is not None:
            self.demand_pie_chart.update_for_year(self.current_year)
        if hasattr(self, 'toolbar_status') and self.toolbar_status is not None:
            self.toolbar_status.SetLabel(f"Year: {self.current_year}")

class SupplyVDemand(PieChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand_data_:DemandData, pie_wedges_):
        super().__init__(notebook_frame,  demand_data_, pie_wedges_, name='Supply v Demand',
                         start_year=1971, end_year=2024, version=0.4)

        self.multi_bar_chart.enable_draggable_vline(
            callback=self.on_line_moved,
            color='black',
            initial_year=2026,
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
        df_ub_cul = self.demand_data.df_ub_cul
        df_lb_cul = self.demand_data.df_lb_cul
        natural_flow_data = self.demand_data.natural_flow_data

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
            self.demand_data.totals,
            self.demand_data.lb_totals,
            self.demand_data.evap_totals,
            self.demand_data.trib_totals
        ]
        self.demand_pie_chart = PieChart(
            self.pie_wedges,
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

class Compact1906To1971(PieChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand_data_:DemandData, pie_wedges_:List[Tuple]):
        self.demand_chart = None
        self.df_cu_1906_2006:Optional[pd.DataFrame] = None

        super().__init__(notebook_frame, demand_data_, pie_wedges_,
                         name='Compact', start_year=1906, end_year=2024, version=0.4)

        self.right_axis_annotations()
        self.multi_bar_chart.enable_draggable_vline(
            callback=self.on_line_moved,
            color='black',
            initial_year=1922,
        )

    def load_charts(self):
        self.df_cu_1906_2006 = sheet.read_csv('data/Colorado_River/usbr_colorado_river_use_since_1906.csv',
                                         sep='\s+', na_values=["---", "-", "*******"])
        series = [
            (self.df_cu_1906_2006, "Upper Basin", UB_COLOR),
            (self.df_cu_1906_2006, "Mexico", lb.MX_COLOR),
            # (1_000_000, "III(b)", CA_COLOR_2),
            (self.df_cu_1906_2006, "CA", CA_COLOR_1),
            (self.df_cu_1906_2006, "AZ", AZ_COLOR_1),
            (self.df_cu_1906_2006, "NV", NV_COLOR_1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            series,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        # self.charts.append(self.demand_pie_chart)

        self.create_demand_bar_chart()
        self.create_reservoir_bar_chart()
        self.on_line_moved(1922)

    def create_demand_bar_chart(self):
        wedges_cul = self.pie_wedges
        df_ub_cul = self.demand_data.df_ub_cul
        df_lb_cul = self.demand_data.df_lb_cul
        # df_ub_users = self.demand_data.df_ub_users
        # az_ltsc_data =  self.demand_data.az_ltsc_data
        # natural_flow_data = self.demand_data.natural_flow_data

        demand_bar = BarGroup(
            label="", series=[
                BarSeries(df=self.df_cu_1906_2006, col="CA", color="maroon", label=""),
                BarSeries(df=self.df_cu_1906_2006, col="NV", color=NV_COLOR_1, label=""),
                BarSeries(df=self.df_cu_1906_2006, col="AZ", color=AZ_COLOR_1, label=""),
                BarSeries(df=self.df_cu_1906_2006, col="Upper Basin", color=UB_COLOR, label=""),
                BarSeries(df=self.df_cu_1906_2006, col="Mexico", color='darkgreen', label=""),
            ])

        demand_cul_bar = BarGroup.from_tuples("", wedges_cul)
        demand_cul_bar.rotate_left(7)
        self.demand_chart = MultiBarChart(
            title=f'Colorado River {self.name}',
            percentage=0.75,
            groups=[demand_cul_bar],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=17,
            y_min=0,
            show_x_labels=True
        )
        self.charts.append(self.demand_chart)

    def right_axis_annotations(self):
        ax = self.demand_chart.ax
        ChartFrame.annotate_level(ax, 7.5, '7.5',
                                      'maroon', draw_text=True, draw_line=True,
                                      left_of_axis=False)

        ax = self.demand_chart.ax
        ChartFrame.annotate_level(ax, 4.4, '4.4',
                                      'maroon', draw_text=True, draw_line=True,
                                      left_of_axis=False)

class Compact1922(PieChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand_data_:DemandData, pie_wedges_:List[Tuple]):
        super().__init__(notebook_frame, demand_data_, pie_wedges_,
                         name='Boulder Canyon Project Act', start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        pie_wedges = [
            (7_500_000, "Upper Basin", UT_COLOR),
            (750_000, "Mexico", lb.MX_COLOR),
            (7_500_000, "Lower Basin", CA_COLOR_1),
            (1_000_000, "III(b)", CA_COLOR_2),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            pie_wedges,
            title=f'Colorado River Compact {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1929)

class Compact1929(PieChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand_data_:DemandData, pie_wedges_:List[Tuple]):
        super().__init__(notebook_frame, demand_data_, pie_wedges_,
                         name='Boulder Canyon Project Act',  start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        # 1929
        # Upper Basin total: ~2,206,000
        # Lower Basin total: ~3,245,500
        # Arizona: ~195,200
        # California: ~3,050,300
        # Nevada: 0

        # 1944
        # Upper Basin total: ~1,934,000
        # `Lower Basin total: ~3,250,725
        # Arizona: ~403,876
        # California: ~2,834,049
        # Nevada: ~12,800

        # 1948
        # Upper Basin total ~1,926,000
        # Lower Basin total 3,875,000
        # – Arizona 517,000
        # – California 3,353,000
        # – Nevada 5,000
        # Mexico column ~6,261,000

        pie_wedges = [
            (7_500_000, "Upper Basin", UT_COLOR),
            (750_000, "Mexico", lb.MX_COLOR),
            (4_400_000, "CA", CA_COLOR_1),
            (1_000_000, "III(b)", CA_COLOR_2),
            (300_000, "NV", NV_COLOR_2),
            (2_800_000, "AZ", AZ_COLOR_1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            pie_wedges,
            title=f'Colorado River {self.name}',
            year=self.current_year,
            left_bar_series=left_bar_series,
            version=self.version
        )
        self.charts.append(self.demand_pie_chart)

        self.create_reservoir_bar_chart()
        self.on_line_moved(1929)

class Compact1944(PieChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand_data_:DemandData, pie_wedges_:List[Tuple]):
        super().__init__(notebook_frame, demand_data_, pie_wedges_,
                         name='Mexico Treaty',  start_year=1906, end_year=2024, version=0.4)

    def load_charts(self):
        pie_wedges = [
            (7_500_000, "Upper Basin", UT_COLOR),
            (1_500_000, "Mexico", lb.MX_COLOR),
            (4_400_000, "CA", CA_COLOR_1),
            (1_000_000, "III(b)", CA_COLOR_2),
            (300_000, "NV", NV_COLOR_2),
            (2_800_000, "AZ", AZ_COLOR_1),
        ]
        left_bar_series = []

        self.demand_pie_chart = PieChart(
            pie_wedges,
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

    demand_data = DemandData()
    pie_wedges = demand_data.build_data(rw, show_tributaries=True)

    SupplyVDemand(nf, demand_data, pie_wedges)
    Compact1906To1971(nf, demand_data, pie_wedges)
    # Compact1922(nf, demand_data, pie_wedges)
    # Compact1929(nf, demand_data, pie_wedges)
    # Compact1944(nf, demand_data, pie_wedges)

    nf.Show()
    app.MainLoop()