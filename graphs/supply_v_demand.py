'''
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
'''
# Data Sources
# I started from:
# USBR Colorado River Uses 1906-2006
#    https://usbr.gov/lc/region/g4000/uses.html
#
# History and sources (from the page notes)
#     Upper Basin 1906–1970: Provided by the Colorado River Board of California.
#     Upper Basin 1971–1995: Bureau of Reclamation Revised Upper Colorado River Consumptive Uses and Losses Reports.
#     Upper Basin 1996–2000: Bureau of Reclamation Colorado River Consumptive Uses and Losses Report: 1996–2000.
#     Upper Basin 2001–2005: Provisional Consumptive Uses and Losses Report: 2001–2005.
#     (Related reports were historically linked at http://www.usbr.gov/uc/library/envdocs/reports/crs/crsul.html)
#     Lower Basin prior to 1914: Unavailable.
#     Lower Basin 1914–1963: Provided by individual users (agricultural districts, MWD, etc.).
#     Lower Basin after 1963: From Reclamation Article V Records (post-Arizona v. California decree accounting).
#        These figures are not reduced for unmeasured return-flow credits.
#
# Additions::
# Lower Basin CUL (1971–2024):
#     https://www.usbr.gov/lc/region/g4000/4200Rpts/CULReport/1971-2024%20Lower%20Colorado%20River%20System%20CUL%20Data.xlsx
#
# Upper Basin CUL (1971-2024):
#     https://www.usbr.gov/uc/DocLibrary/Reports/ConsumptiveUsesLosses/v24.5_CUL_ResultsCU_CY.xlsx
#     https://www.usbr.gov/uc/DocLibrary/Reports/ConsumptiveUsesLosses/v24.5_CUL_ResultsCU_WY_Annual.xlsx
#     https://www.usbr.gov/uc/DocLibrary/Reports/ConsumptiveUsesLosses/v24.5_CUL_ResultsCU.xlsx
#     https://www.usbr.gov/uc/DocLibrary/Reports/ConsumptiveUsesLosses/v24.5_UB_CU_WY_Annual.xlsx
#
# USGS Reports
#   Summary of Records of Surface Waters at Base Stations in Colorado River Basin 1891-1938
#   https://pubs.usgs.gov/wsp/0918/report.pdf
#
# Colorado River Water Supply Its Magnitude and  Distribution 1969
#   https://pubs.usgs.gov/pp/0486d/report.pdf
#
# Surface waters 1945
#   https://pubs.usgs.gov/wsp/1039/report.pdf
#
# Surface waters 1949
#   https://pubs.usgs.gov/wsp/1149/report.pdf
#
# My Lower Colorado Annual Report digitization 1964-2021 (Im update the files I need for 2022-2025)
# This gets me LB individual users and through 2025 (no LB tributaries)
# https://github.com/EdMillard/riverwar/tree/main/data/USBR_Reports
#
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
from typing import Optional

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
        self.natural_flow_chart = None
        self.ub_demand_chart = None
        self.lb_demand_chart = None
        self.lb_trib_chart = None

        self.df: Optional[pd.DataFrame] = None
        self._syncing_lines = False  # prevent re-entrancy

        super().__init__(notebook_frame, demand,
                         name='Demand', start_year=1904, end_year=2026, version=0.5)
        self.top_axis_annotations()
        if self.ub_demand_chart is not None:
            self.ub_demand_chart.set_custom_legend([("Upper Basin", Colors.UB)])
        self.right_axis_annotations()
        self.bottom_axis_annotations()

        # Enable draggable lines only on charts that support them
        for chart in self.charts:
            totals = []
            if chart == self.ub_demand_chart:
                bar_values_split_label = True
                totals = ["Evap"]
            elif chart == self.lb_demand_chart:
                bar_values_split_label = True
                totals = ["Mexico Treaty"]
            else:
                bar_values_split_label = False

            if hasattr(chart, 'enable_draggable_vline'):
                show_bar_values = True,
                show_label = (chart is self.natural_flow_chart) or (chart is self.lb_demand_chart)
                chart.enable_draggable_vline(
                    callback=self.on_line_moved,
                    color='#202020',
                    initial_year=1922,
                    show_year_label=show_label,
                    show_bar_values=show_bar_values,
                    bar_values_split_label=bar_values_split_label,
                    dual_side_lines=True,
                    top_total_columns=totals,
                )

    def load_charts(self):

        # Bureau estimated diversions/consumptive use 1906-2006 (Fairly trustworthy)
        #
        self.df = sheet.read_csv('data/Colorado_River/usbr_colorado_river_use_since_1906.csv',
                                         sep='\s+', na_values=["---", "-", "*******"])
        self.df = df_utils.extend_years(self.df, min_year=1904, max_year=2026)

        # Gila at Dome confluence 1 mile above Yuma
        sheet.usgs_annuals(self.df, '09520500', 1929, self.end_year, title=lb.AZ_GILA_DOME_USGS, divisor=1000000) # Has missing years
        # Yuma Gage 5-6 miles above Alamo
        sheet.usgs_annuals(self.df, '09521000', 1904, 1964, title="Yuma USGS", divisor=1)
        # Mexico border
        sheet.usgs_annuals(self.df, '09522000', 1950, self.end_year, title=lb.NIB_MORELOS_USGS)

        # Salton Sea
        sheet.usgs_annuals(self.df, '10254730', 1961, self. end_year, title=lb.ALAMO_RIVER,divisor=1) # 1960 is partial
        sheet.usgs_annuals(self.df, '10255550', 1961, self.end_year, title=lb.NEW_RIVER,divisor=1) # New goes back to 1943
        sheet.usgs_annuals(self.df, '10259540', 1961, self.end_year, title=lb.WHITEWATER,divisor=1)
        df_utils.add_column_sum(self.df, [lb.ALAMO_RIVER, lb.NEW_RIVER, lb.WHITEWATER], lb.SALTON_INFLOW)

        # Alamo Canal 1909-1938
        df_alamo = sheet.read_csv('data/Colorado_River/alamo_1909_1938.csv', sep=',')
        alamo_column_map = { "CY_Runoff_acre_ft": "Alamo" }
        df_utils.copy_columns_by_key(df_alamo, self.df, alamo_column_map, overwrite=True)
        df_utils.divide_by_constant(self.df, "Alamo", 2.0, 'Alamo Split')

        # Volcano Island Supplement to Imperial on top of Alamo 1916-1921
        df_volcano = sheet.read_csv('data/Colorado_River/volcamo_lake_1916_1921.csv', sep=',')
        volcano_column_map = { "Water_Year_Runoff_AF": "Volcano" }
        df_utils.copy_columns_by_key(df_volcano, self.df, volcano_column_map, overwrite=True)

        # Delta early years is Yume Gage - ALamo - Volcano - Small Yuma diversion
        #
        df_utils.subtract_column(self.df, "Yuma USGS", "Alamo", "Delta", clip_negative_to_zero=True)
        df_utils.subtract_column(self.df, "Delta", "Volcano", "Delta")
        # df_utils.zero_out_column(self.df, "Delta", 1939, 1965, date_col='Year', use_nan=True)

        # Palo Verde 1922-1938
        df_palo_verde = sheet.read_csv('data/Colorado_River/palo_verde_1922_1938.csv', sep=',')
        palo_verde_column_map = { "Net_WY_Runoff_AF": "Palo Verde" }
        df_utils.copy_columns_by_key(df_palo_verde, self.df, palo_verde_column_map, overwrite=True)

        # Estimated Mexico use 1907-1970 (Not trustworthy)
        #
        df_mexico_treaty_guess = sheet.read_csv('data/Colorado_River/mexico_guess_1907_1963.csv',
                                         sep='\s+', na_values=["---", "-", "*******"])
        df_utils.divide_columns(df_mexico_treaty_guess, 'estimated_AF', 'acres_approx', 'AF per acre')

        mexico_guess_column_map = { "estimated_AF": "Mexico Treaty",}
        df_utils.copy_columns_by_key(df_mexico_treaty_guess, self.df, mexico_guess_column_map, overwrite=True)

        # Bureau CUL data 1971-2024 (Very trustworthy)
        # Lower Basin CUL
        lb_column_map = {
            "AZ Colorado River": "AZ",
            "CA Total CUL": "CA",
            lb.NV_COLORADO_RIVER_TOTAL: "NV",
            "Mexico": "Mexico Treaty",
        }
        df_utils.copy_columns_by_key(self.demand.df_lb_cul, self.df, lb_column_map, overwrite=True)

        # Replace CA with Imperial and Palo Verde
        # df_utils.subtract_column(self.df, 'Alamo', "Alamo Split", "Imperial")
        # df_utils.subtract_column(self.df, 'CA', "Imperial", "Palo Verde")
        df_utils.zero_out_column(self.df, "CA", 1909, 1937, date_col='Year', use_nan=True)

        # Upper Basin CUL
        #
        ub_column_map = { "UB Total": "Upper Basin", }
        df_utils.copy_columns_by_key(self.demand.df_ub_cul, self.df, ub_column_map)

        # Mexico Delta, 2005 to present from annual reports
        #
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_in_excess.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_mx, "MX in excess", divisor=1)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_minute_319.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_mx, "MX minute 319", divisor=1)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_minute_242_bypass.csv', sep='\s+')
        sheet.merge_annual_column(self.df, df_mx, "Cienega", divisor=1)

        mexico_delta = ["MX in excess", "MX minute 319"]
        df_utils.add_column_sum(self.df, mexico_delta, "Mexico Delta")

        df_utils.subtract_column(self.df, 'Mexico', 'Mexico Treaty', 'Delta')
        delta_map = {
            "Mexico Delta": "Delta",
        }
        df_utils.copy_columns_by_key(self.df, self.df, delta_map)

        self.create_natural_flow_bar_chart(self.df)
        self.create_ub_demand_bar_chart(self.df)
        # self.create_lb_trib_bar_chart(self.df)
        self.create_lb_demand_bar_chart(self.df)
        #self.create_demand_pie_chart(self.df)

        # self.create_reservoir_bar_chart(show_x_labels=False)
        self.on_line_moved(1922)

    def create_natural_flow_bar_chart(self, df_cu_1906_2024: pd.DataFrame):
        series = ('', [
            (self.demand.natural_flow_data.df, "Natural Lees Ferry", Colors.NATURAL_FLOW),
        ])
        self.natural_flow_chart = MultiBarChart(
            # title=f'Colorado River {self.name}     ver={self.version}',
            percentage=0.20,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=25.0,
            y_min=4.0,
            show_x_labels=False,
            legend_loc = 'upper center',
        )
        self.charts.append(self.natural_flow_chart)

    def create_ub_demand_bar_chart(self, df_cu_1906_2024: pd.DataFrame, use_cul:bool=True):
        if use_cul:
            df_ub_cul = self.demand.df_ub_cul
            df_utils.zero_out_column(df_cu_1906_2024,  "Upper Basin", 1971, self.end_year, date_col='Year', use_nan=True)
            df_utils.copy_column(df_ub_cul, df_ub_cul, ub.UB_RESERVOIR_EVAP, 'Evap')
            series = ('', [
                (df_cu_1906_2024, "Upper Basin", Colors.UB),
                (df_ub_cul, ub.CO_WEST_SLOPE, Colors.CO),
                (df_ub_cul, ub.CU_UT, Colors.UT),
                (df_ub_cul, ub.CU_WY, Colors.WY),
                (df_ub_cul, ub.CU_NM, Colors.NM),
                (df_ub_cul, 'Evap', 'cornflowerblue'),
            ])
        else:
            series = ('', [
                (df_cu_1906_2024, "Upper Basin", Colors.UB),
            ])

        self.ub_demand_chart = MultiBarChart(
            # title=f'Colorado River {self.name}     ver={self.version}',
            title="",
            percentage=0.20,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=5.0,
            y_min=0,
            show_x_labels=False,
            custom_legend=[("Upper Basin", Colors.UB)],
            legend_loc = 'upper left',
        )
        self.charts.append(self.ub_demand_chart)

    def create_lb_demand_bar_chart(self, df_cu_1906_2024: pd.DataFrame, use_cul:bool=True):
        if use_cul:
            df_lb_cul = self.demand.df_lb_cul
            ltsc_df = self.demand.az_ltsc_data.df

            df_utils.zero_out_column(df_cu_1906_2024,  "CA", 1971, self.end_year, date_col='Year', use_nan=True)
            df_utils.zero_out_column(df_cu_1906_2024,  "AZ", 1971, self.end_year, date_col='Year', use_nan=True)
            df_utils.zero_out_column(df_cu_1906_2024,  "NV", 1971, self.end_year, date_col='Year', use_nan=True)

            lb_column_map = {
                "Imperial CU": "Imperial",
                "Palo Verde CU": "Palo Verde"
            }
            df_utils.copy_columns_by_key(df_lb_cul, df_cu_1906_2024, lb_column_map, overwrite=False)

            df_utils.subtract_column_by_year(df_cu_1906_2024, "CA", lb.SALTON_INFLOW, result_column="CA",
                                             start_year=1961, end_year=1970)
            series = ('', [
                # CA
                (df_cu_1906_2024, lb.SALTON_INFLOW, Colors.CA_SALTON, {'label': 'Salton'}),
                (df_cu_1906_2024, "CA", Colors.CA),
                (df_cu_1906_2024, "Alamo", Colors.CA_ALAMO ),
                (df_cu_1906_2024, "Volcano", Colors.CA_VOLCANO),
                (df_lb_cul, lb.IMPERIAL_VALLEY_CU, Colors.CA_IMPERIAL, {'label': 'Imperial'}),
                (df_lb_cul, lb.CA_OUTSIDE_SYSTEM, Colors.CA_MWD, {'label': 'MWD'}),
                (df_lb_cul, lb.CA_MAINSTEM, Colors.CA4, {'label': 'CA Misc'}),
                (df_cu_1906_2024, "Palo Verde", Colors.CA_PALO_VERDE),

                # NV
                (df_cu_1906_2024, "NV", Colors.NV1),
                (df_lb_cul, lb.NV_COLORADO_RIVER_TOTAL, Colors.NV2, {'label': 'NV'}),
                # (df_lb_cul, lb.NV_TRIBUTARY_CUL, Colors.NV1, {'label': 'NV Trib'}),

                # AZ
                (df_cu_1906_2024, "AZ", Colors.AZ),
                (df_lb_cul, lb.AZ_MAINSTEM, Colors.AZ, {'label': 'AZ Misc'}),
                (df_lb_cul, lb.AZ_CRIT_CU, Colors.AZ, {'label': 'CRIT'}),
                (df_lb_cul, lb.WELLTON_MOHAWK_CU, Colors.AZ, {'label': 'Wellton'}),
                (df_lb_cul, lb.AZ_CAP, Colors.AZ1, {'label': 'CAP'}),
                (ltsc_df, lb.AZ_LTSC_STORED, Colors.AZ2, {'label': 'AZ Aquifer'}),

                (df_cu_1906_2024, "Cienega", Colors.MX_CIENEGA),

                (df_cu_1906_2024, "Mexico Treaty",  Colors.MX, {'label': 'MX'}),
                (df_cu_1906_2024, "LB Evap", Colors.EVAP, {'label': 'Evap'}),
                (df_cu_1906_2024, "Delta", Colors.MX_DELTA),
            ])
        else:
            series = ('', [
                (df_cu_1906_2024, "CA", Colors.CA),
                (df_cu_1906_2024, "NV", Colors.NV1),
                (df_cu_1906_2024, "AZ", Colors.AZ),
                (df_cu_1906_2024, "Mexico Treaty",  Colors.MX),
                (df_cu_1906_2024, "Cienega", Colors.MX_CIENEGA),
                (df_cu_1906_2024, "LB Evap", Colors.EVAP),
                (df_cu_1906_2024, "Delta", Colors.MX_DELTA),
            ])
        legend = [
            ("CA", Colors.MX),
            ("AZ", Colors.AZ),
            ("NV", Colors.NV1),
            ("CA", Colors.CA),
            ("Alamo", Colors.CA_ALAMO)
        ]
        self.lb_demand_chart = MultiBarChart(
            title=f'',
            percentage=0.60,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=11,
            y_min=0,
            show_x_labels=True,
            custom_legend=legend,
            legend_loc='upper left',
        )
        self.charts.append(self.lb_demand_chart)

    def create_lb_trib_bar_chart(self, df_cu_1906_2024: pd.DataFrame):
        lb_trib_column_map = {
             lb.LB_TRIBUTARY_CUL: "LB Tributary CU",
        }
        df_utils.copy_columns_by_key(self.demand.df_lb_cul, df_cu_1906_2024, lb_trib_column_map)
        series = ('', [
            (df_cu_1906_2024, "LB Tributary CU", 'orange'),
        ])
        self.lb_trib_chart = MultiBarChart(
            title=f'',
            percentage=0.20,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min = 0,
            y_max=4.5,
            y_min=0,
            show_x_labels=True,
            legend_loc='upper left',
        )
        self.charts.append(self.lb_trib_chart)

    def create_demand_pie_chart(self, df_cu_1906_2024: pd.DataFrame):
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

    def right_axis_annotations(self):
        if self.lb_demand_chart is not None:
            ax = self.lb_demand_chart.ax
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
        self.lb_demand_chart.annotate_value(
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

    def top_axis_annotations(self):
        if self.ub_demand_chart is not None:
            legend_entries = [
                (Colors.Drought, "Drought"),
                (Colors.Wet, "Wet"),
                (Colors.Monsoon, "Monsoon"),
            ]
            self.ub_demand_chart.annotate_year_indicators(
                self.ub_demand_chart.ax,
                [Demand.wet_v_dry_years, Demand.monsoon_years],
                legend_entries=legend_entries,
                bar_height_frac=1,
                y_offset_frac=.01
            )

    def bottom_axis_annotations(self):
        if self.lb_demand_chart is not None:
            ax = self.lb_demand_chart.ax
            self._annotate_bottom(ax, 1906, "IID", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1908, "Palo Verde", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1909, "Gunnison", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1910, "SRP", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1922, "Compact")
            self._annotate_bottom(ax, 1923, "PVID", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1915, "Grand\nValley", color=Colors.UB)
            self._annotate_bottom(ax, 1929, "BCPA", offset_lines=0)
            self._annotate_bottom(ax, 1933, "Depression", offset_lines=1)
            self._annotate_bottom(ax, 1931, "AZ v CA", offset_lines=2)
            self._annotate_bottom(ax, 1936, "Moffat", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1944, "MX Treaty", offset_lines=0)
            self._annotate_bottom(ax, 1940, "All Am", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1941, "MWD", offset_lines=2, color=Colors.LB)
            self._annotate_bottom(ax, 1947, "Coachella", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1947, "Northern", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1951, "Wellton", color=Colors.LB)
            self._annotate_bottom(ax, 1959, "MWD\u2191", offset_lines=2, color=Colors.LB)
            self._annotate_bottom(ax, 1964, "Roberts", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1964, "AZ v CA")
            self._annotate_bottom(ax, 1972, "Fryark", color=Colors.UB)
            self._annotate_bottom(ax, 1971, "LV", offset_lines=1, color=Colors.LB)  # LVVWD
            self._annotate_bottom(ax, 1971, "CUP", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1968, "CRBPA", offset_lines=1)
            self._annotate_bottom(ax, 1984, "Dolores", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1985, "CAP", color=Colors.LB)
            self._annotate_bottom(ax, 1991, "SNWA", color=Colors.LB)
            self._annotate_bottom(ax, 2003, "QSA", color=Colors.LB)
            self._annotate_bottom(ax, 2007, "2007\nGuidelines", offset_lines=1)
            self._annotate_bottom(ax, 2014, "Delta\nPulse", color=Colors.LB)
            self._annotate_bottom(ax, 2018, "DCP")

if __name__ == "__main__":
    app = wx.App(False)

    rw = RiverWar()
    nf = NotebookFrame([], rw)

    d = Demand(rw, show_tributaries=False)

    # SupplyVDemand(nf, d)
    Demand1906To1971(nf, d)

    nf.Show()
    app.MainLoop()