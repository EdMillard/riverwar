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
#
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
# USGS Colorado River Water Supply Its Magnitude and  Distribution 1969
#   https://pubs.usgs.gov/pp/0486d/report.pdf
#
# USGS Surface waters 1945
#   https://pubs.usgs.gov/wsp/1039/report.pdf
#
# USGS Surface waters 1949
#   https://pubs.usgs.gov/wsp/1149/report.pdf
#
# USGS Compilation of Records of Surface Waters of the United States, October 1950 to September 1960
#   https://pubs.usgs.gov/wsp/1733/report.pdf
#
# USGS Compilation of Records of Surface Waters of the United States 1890-1950
#   https://pubs.usgs.gov/wsp/1313/report.pdf

# Coachella
# https://www.cvwd.org/DocumentCenter/View/1193/Final-Coachella-Valley-Water-Management-Plan--September-2002--PDF
#
# Statements to L Ward Bannister
#  https://www.varuna.io/LOTR/1935/Bannister_Report_1935.pdf

# My Lower Colorado Annual Report digitization 1964-2021
# This gets me LB individual users and through 2025 (no LB tributaries)
# https://github.com/EdMillard/riverwar/tree/main/data/USBR_Reports
#
import pandas as pd
import wx

from api.df_utils import divide_by_constant
from data_sets.demand import Demand, Colors
from demand_chart_frame import DemandChartFrame
from sheet import sheet
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.pie_chart import PieChart
from chart.multi_bar_chart import MultiBarChart, BarSeries, BarGroup
from colorado.river_war import RiverWar
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils
from typing import Optional

class SupplyVDemandPie(DemandChartFrame):
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

class SupplyVDemand(DemandChartFrame):
    def __init__(self, notebook_frame: NotebookFrame, demand: Demand):
        self.natural_flow_chart = None
        self.ub_demand_chart = None
        self.lb_demand_chart = None
        self.lb_trib_chart = None

        self.ub_bar_group:Optional[BarGroup] = None
        self.lb_bar_group:Optional[BarGroup] = None

        self.df: Optional[pd.DataFrame] = None
        self._syncing_lines = False  # prevent re-entrancy

        super().__init__(notebook_frame, demand,
                         name='Demand', start_year=1904, end_year=2025, version=0.5)
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

    @staticmethod
    def load_annual_report(df:pd.DataFrame, directory:str, path:str, column:str):
        df_tmp = sheet.read_csv(f'data/USBR_Reports/{directory}/usbr_{directory}_{path}.csv', sep='\s+')
        sheet.merge_annual_column(df, df_tmp, column, divisor=1)

    def load_annual_reports(self):
        SupplyVDemand.load_annual_report(self.df, "ca", "total_consumptive_use", 'CA')
        SupplyVDemand.load_annual_report(self.df, "az", "total_consumptive_use", 'AZ')
        SupplyVDemand.load_annual_report(self.df, "nv", "total_consumptive_use", 'NV')
        df_utils.add_column_sum(self.df, ["AZ", "CA",  "NV"], 'LB')

        SupplyVDemand.load_annual_report(self.df, "ca", "imperial_irrigation_consumptive_use", lb.IMPERIAL_CU)
        # SupplyVDemand.load_annual_report(self.df, "ca", "imperial_irrigation_diversion", lb.IMPERIAL_CU)
        SupplyVDemand.load_annual_report(self.df, "ca", "coachella_consumptive_use", lb.COACHELLA_CU)
        # SupplyVDemand.load_annual_report(self.df, "ca", "coachella_diversion", lb.COACHELLA_CU)

        SupplyVDemand.load_annual_report(self.df, "ca", "yuma_project_sum_consumptive_use", "Yuma Project")

        df_utils.copy_column(self.demand.df_lb_cul, self.df,  lb.CA_MAINSTEM, lb.CA_MAINSTEM)
        # FIXME, Yuma project doesn't seem to be in mainstem, maybe because its diverted out of All American
        # Mainstem jumps a bunch in 2003, maybe due to return flow account tightening after QSA
        # df_utils.subtract_column_by_year(self.df, lb.CA_MAINSTEM, "Yuma Project", 2003, 2025, "CA Mainstem estimated")

        df_utils.add_column_sum(self.df, [lb.IMPERIAL_CU, lb.COACHELLA_CU], lb.IMPERIAL_VALLEY_CU)

        sheet.usgs_annuals(self.df, '09523000', 1940, self. end_year, title="All American USGS",divisor=1) # 1960 is partial
        sheet.usgs_annuals(self.df, '09527000', 1943, self. end_year, title="Pilot Knob Power USGS",divisor=1) # 1960 is partial
        sheet.usgs_annuals(self.df, '09527500', 1961, self. end_year, title="Below Pilot Knob USGS",divisor=1) # 1960 is partial

        # sheet.usgs_annuals(self.df, '09527590', 1940, self. end_year, title="Coachella USGS",divisor=1) # 1960 is partial

        SupplyVDemand.load_annual_report(self.df, "ca", "metropolitan_consumptive_use", lb.METROPOLITAN_CU)
        df_tmp = sheet.read_csv(f'data/USGS_Surface_Waters/colorado_river_aquaduct_1939_1965.csv', sep=',')
        sheet.merge_annual_column(self.df, df_tmp, lb.METROPOLITAN_CU, divisor=1)

        self.load_palo_verde()

        df_utils.add_column_sum(self.df, [lb.IMPERIAL_VALLEY_CU, lb.METROPOLITAN_CU, "Palo Verde", "Yuma Project"], "CA Big Users")
        df_utils.subtract_column(self.df, "CA", "CA Big Users", "CA")

        SupplyVDemand.load_annual_report(self.df, "az", "crit_consumptive_use", lb.AZ_CRIT_CU)
        SupplyVDemand.load_annual_report(self.df, "az", "wellton_mohawk_consumptive_use", lb.WELLTON_MOHAWK_CU)

        #SupplyVDemand.load_annual_report(self.df, "nv", "snwa_griffith_diversion", lb.NV_SNWA)
        pass

    def load_palo_verde(self):
        # Palo Verde 1922-1938
        df_palo_verde_1922_1938 = sheet.read_csv('data/USGS_Surface_Waters/palo_verde_1922_1938.csv', sep=',')
        palo_verde_column_map = { "Net_WY_Runoff_AF": "Palo Verde" }
        df_utils.copy_columns_by_key(df_palo_verde_1922_1938, self.df, palo_verde_column_map, overwrite=True)

        df_palo_verde_1922_1850 = sheet.read_csv('data/USGS_Surface_Waters/palo_verde_discharge_1922_1950.csv', sep=',')
        palo_verde_column_map = { "Runoff acre-feet (WY ending Sept. 30)": "Palo Verde" }
        df_utils.copy_columns_by_key(df_palo_verde_1922_1850, self.df, palo_verde_column_map, overwrite=True)

        df_palo_verde_1950_1960 = sheet.read_csv('data/USGS_Surface_Waters/palo_verde_discharge_1950_1960.csv', sep=',')
        palo_verde_column_map = { "Total": "Palo Verde" }
        df_utils.copy_columns_by_key(df_palo_verde_1950_1960, self.df, palo_verde_column_map, overwrite=True)
        df_utils,divide_by_constant(self.df, "Palo Verde", 2, "Palo Verde")

        df_palo_verde_1961_1963 = sheet.read_csv('data/USGS_Surface_Waters/palo_verde_discharge_1961_1965.csv', sep=',')
        palo_verde_column_map = { "Total": "Palo Verde" }
        df_utils.copy_columns_by_key(df_palo_verde_1961_1963, self.df, palo_verde_column_map, overwrite=True)

        SupplyVDemand.load_annual_report(self.df, "ca", "palo_verde_consumptive_use", "Palo Verde")

    def load_charts(self):

        # Bureau estimated diversions/consumptive use 1906-2006 (Fairly trustworthy)
        #
        self.df = sheet.read_csv('data/Colorado_River/usbr_colorado_river_use_since_1906.csv',
                                         sep='\s+', na_values=["---", "-", "*******"])
        self.df = df_utils.extend_years(self.df, min_year=1904, max_year=2026)
        df_utils.copy_column(self.df, self.df, "Upper Basin", "UB 06", insert_before="Upper Basin")
        df_utils.copy_column(self.df, self.df, "Lower Basin", "LB 06", insert_before="Lower Basin")
        df_utils.copy_column(self.df, self.df, "AZ", "AZ 06", insert_before="AZ")
        df_utils.copy_column(self.df, self.df, "AZ", "AZ 06", insert_before="AZ")
        df_utils.copy_column(self.df, self.df, "CA", "CA 06", insert_before="CA")
        df_utils.copy_column(self.df, self.df, "NV", "NV 06", insert_before="NV")
        df_utils.copy_column(self.df, self.df, "Mexico", "MX 06", insert_before="Mexico")

        self.load_annual_reports()

        # Gila at Dome confluence 1 mile above Yuma
        df_gila = sheet.read_csv('data/USGS_Surface_Waters/gila_dome_1903_1950.csv', sep=',')
        df_utils.multiply_constant(df_gila, "Total", "Gila Dome", 1000)
        df_utils.copy_column(df_gila, self.df, "Gila Dome")

        sheet.usgs_annuals(self.df, '09520500', 1929, self.end_year, title=lb.AZ_GILA_DOME_USGS, divisor=1) # Has missing years1
        df_utils.copy_column(self.df, self.df, "Gila Dome")

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
        df_alamo = sheet.read_csv('data/USGS_Surface_Waters//alamo_1909_1938.csv', sep=',')
        alamo_column_map = { "CY_Runoff_acre_ft": "Alamo" }
        df_utils.copy_columns_by_key(df_alamo, self.df, alamo_column_map, overwrite=True)
        df_utils.divide_by_constant(self.df, "Alamo", 2.0, 'Alamo Split')

        # Volcano Island Supplement to Imperial on top of Alamo 1916-1921
        df_volcano = sheet.read_csv('data/USGS_Surface_Waters//volcano_lake_1916_1921.csv', sep=',')
        volcano_column_map = { "Water_Year_Runoff_AF": "Volcano" }
        df_utils.copy_columns_by_key(df_volcano, self.df, volcano_column_map, overwrite=True)

        # Delta early years is Yuma Gage - ALamo - Volcano - Small Yuma diversion
        #
        df_utils.subtract_column(self.df, "Yuma USGS", "Alamo", "Delta", clip_negative_to_zero=True)
        df_utils.subtract_column(self.df, "Delta", "Volcano", "Delta")
        # df_utils.zero_out_column(self.df, "Delta", 1939, 1965, date_col='Year', use_nan=True)

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

        self.pre_lb_demand_bar_chart(self.df, use_cul=True)

        self.ub_bar_group = SupplyVDemand.build_ub_demand(self.df, self.demand.df_ub_cul, self.end_year)
        self.lb_bar_group = SupplyVDemand.build_lb_demand_series(self.df, self.demand.df_lb_cul, self.demand.az_ltsc_data.df)

        self.create_natural_flow_bar_chart()
        self.create_ub_demand_bar_chart(self.df)
        # self.create_lb_trib_bar_chart(self.df)
        self.create_lb_demand_bar_chart(self.df)
        #self.create_demand_pie_chart(self.df)

        # self.create_reservoir_bar_chart(show_x_labels=False)
        self.on_line_moved(1922)

    def pre_lb_demand_bar_chart(self, df_cu_1906_2024: pd.DataFrame, use_cul:bool=True):
        if use_cul:
            df_lb_cul = self.demand.df_lb_cul

            df_utils.zero_out_column(df_cu_1906_2024,  "CA", 1971, 2024, date_col='Year', use_nan=True)
            df_utils.zero_out_column(df_cu_1906_2024,  "AZ", 1971, 2024, date_col='Year', use_nan=True)
            df_utils.zero_out_column(df_cu_1906_2024,  "NV", 1971, 2024, date_col='Year', use_nan=True)

            lb_column_map = {
                "Imperial CU": "Imperial",
                "Palo Verde CU": "Palo Verde"
            }
            df_utils.copy_columns_by_key(df_lb_cul, df_cu_1906_2024, lb_column_map, overwrite=False)

            # df_utils.subtract_column_by_year(df_cu_1906_2024, "CA", lb.SALTON_INFLOW, result_column="CA",
            #                                 start_year=1961, end_year=1963)
            # df_utils.subtract_column_by_year(df_cu_1906_2024, lb.IMPERIAL_VALLEY_CU, lb.SALTON_INFLOW, result_column=lb.IMPERIAL_VALLEY_CU,
            #                                  start_year=1964, end_year=1970)

    def create_natural_flow_bar_chart(self):
        df_utils.add_column_sum(self.df, ["LB Total", "UB Total", "Cienega", "Mexico Treaty"], 'Demand')
        df_utils.copy_column(self.demand.natural_flow_data.df, self.df, "Natural Lees Ferry", "Natural Lees Ferry")
        df_utils.add_column_sum(self.df, ["Natural Lees Ferry", "Gila Dome"], 'Supply')

        df_utils.subtract_column(self.df, "Supply", 'Demand', "Diff")
        df_utils.split_column_by_sign(self.df, "Diff", "Deficit", "Surplus", drop_original=True)

        df_utils.add_column_sum(self.df, ["Demand", "Delta"], 'Expected')
        df_utils.subtract_column(self.df, "Expected", "Supply", "Diff")
        df_utils.split_column_by_sign(self.df, "Diff", "Fill", "Overflow", drop_original=True)
        df_utils.subtract_column(self.df, "Overflow", "Deficit", "Overflow")

        demand = BarGroup(
            label="",
            series=[
                BarSeries(df=self.df, col="LB Total", color=Colors.LB),
                BarSeries(df=self.df, col="UB Total", color=Colors.UB),
                BarSeries(df=self.df, col="Cienega", color=Colors.MX_CIENEGA),
                BarSeries(df=self.df, col="Mexico Treaty", color=Colors.MX),
                BarSeries(df=self.df, col="Delta", color=Colors.MX_DELTA),
                BarSeries(df=self.df, col="Fill", color=Colors.FILL),
            ],
        )
        supply = BarGroup(
            label="",
            series=[
                BarSeries(df=self.df, col="Natural Lees Ferry", color=Colors.NATURAL_FLOW),
                BarSeries(df=self.df, col="Gila Dome", color=Colors.AZ),
                BarSeries(df=self.df, col="Deficit", color="#ff0000"),
                BarSeries(df=self.df, col="Overflow", color="#00ff00"),
            ],
        )
        self.natural_flow_chart = MultiBarChart(
            percentage=0.20,
            groups=[demand, supply],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min=0,
            y_max=25.0,
            y_min=0.0,
            show_x_labels=False,
            custom_legend=[("Natural", Colors.NATURAL_FLOW), ("Gila Dome", Colors.AZ), ("Fill", Colors.FILL)],
            legend_loc='upper center',
        )
        self.charts.append(self.natural_flow_chart)

    @staticmethod
    def build_ub_demand(df:pd.DataFrame, df_ub_cul:pd.DataFrame, end_year:int, use_cul:bool=True)->BarGroup:
            if use_cul:
                df_utils.zero_out_column(df, "Upper Basin", 1971, end_year, date_col='Year',use_nan=True)
                df_utils.copy_column(df_ub_cul, df_ub_cul, ub.UB_RESERVOIR_EVAP, 'Evap')
                ub_bar_group = BarGroup(
                    label="",
                    series=[
                        BarSeries(df=df, col="Upper Basin", color=Colors.UB),
                        BarSeries(df=df_ub_cul, col=ub.CO_WEST_SLOPE, color=Colors.CO),
                        BarSeries(df=df_ub_cul, col=ub.CU_UT, color=Colors.UT),
                        BarSeries(df=df_ub_cul, col=ub.CU_WY, color=Colors.WY),
                        BarSeries(df=df_ub_cul, col=ub.CU_NM, color=Colors.NM),
                        BarSeries(df=df_ub_cul, col='Evap', color=Colors.EVAPORATION),
                    ],
                )
            else:
                ub_bar_group = BarGroup(
                    label="",
                    series=[
                        BarSeries(df=df, col="Upper Basin", color=Colors.UB),
                    ],
                )

            MultiBarChart.compute_stack_totals(df, ub_bar_group, "Evap", "UB Total")

            return ub_bar_group

    def create_ub_demand_bar_chart(self, df_cu_1906_2024: pd.DataFrame, use_cul: bool = True):
        self.ub_demand_chart = MultiBarChart(
            title="",
            percentage=0.20,
            groups=[self.ub_bar_group],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min=0,
            y_max=5.0,
            y_min=0,
            show_x_labels=False,
            custom_legend=[("Upper Basin", Colors.UB)],
            legend_loc='upper left',
        )
        self.charts.append(self.ub_demand_chart)

    @staticmethod
    def build_lb_demand_series(df:pd.DataFrame, df_lb_cul:pd.DataFrame, ltsc_df:pd.DataFrame, use_cul:bool=True)->BarGroup:
        if use_cul:
            lb_bar_group = BarGroup(
                label="",
                series=[
                    # CA
                    BarSeries(df=df, col="CA", color=Colors.CA),
                    BarSeries(df=df, col="Alamo", color=Colors.CA_ALAMO),
                    BarSeries(df=df, col="Volcano", color=Colors.CA_VOLCANO),
                    BarSeries(df=df, col=lb.IMPERIAL_VALLEY_CU, color=Colors.CA_IMPERIAL,
                              label='Imperial'),
                    BarSeries(df=df, col="Yuma Project", color=Colors.CA4),
                    BarSeries(df=df, col="Palo Verde", color=Colors.CA_PALO_VERDE),
                    BarSeries(df=df, col=lb.CA_MAINSTEM, color=Colors.CA4, label='CA Misc'),
                    BarSeries(df=df, col=lb.METROPOLITAN_CU, color=Colors.CA_MWD, label='MWD'),

                    # NV
                    BarSeries(df=df, col="NV", color=Colors.NV1),
                    BarSeries(df=df_lb_cul, col=lb.NV_COLORADO_RIVER_TOTAL, color=Colors.NV2, label='NV'),

                    # AZ
                    BarSeries(df=df, col="AZ", color=Colors.AZ),
                    BarSeries(df=df_lb_cul, col=lb.AZ_MAINSTEM, color=Colors.AZ, label='AZ Misc'),
                    BarSeries(df=df, col=lb.AZ_CRIT_CU, color=Colors.AZ, label='CRIT'),
                    BarSeries(df=df, col=lb.WELLTON_MOHAWK_CU, color=Colors.AZ, label='Wellton'),
                    BarSeries(df=df_lb_cul, col=lb.AZ_CAP, color=Colors.AZ1, label='CAP'),
                    BarSeries(df=ltsc_df, col=lb.AZ_LTSC_STORED, color=Colors.AZ2, label='AZ Aquifer'),

                    BarSeries(df=df, col="Cienega", color=Colors.MX_CIENEGA),
                    BarSeries(df=df, col="Mexico Treaty", color=Colors.MX, label='MX'),
                    BarSeries(df=df, col="LB Evap", color=Colors.EVAPORATION, label='Evap'),
                    BarSeries(df=df, col="Delta", color=Colors.MX_DELTA),
                ],
            )
        else:
            lb_bar_group = BarGroup(
                label="",
                series=[
                    BarSeries(df=df, col="CA", color=Colors.CA),
                    BarSeries(df=df, col="NV", color=Colors.NV1),
                    BarSeries(df=df, col="AZ", color=Colors.AZ),
                    BarSeries(df=df, col="Mexico Treaty", color=Colors.MX),
                    BarSeries(df=df, col="Cienega", color=Colors.MX_CIENEGA),
                    BarSeries(df=df, col="LB Evap", color=Colors.EVAPORATION),
                    BarSeries(df=df, col="Delta", color=Colors.MX_DELTA),
                ],
            )

        MultiBarChart.compute_stack_totals(df, lb_bar_group, "Cienega", "LB Total")

        return lb_bar_group

    def create_lb_demand_bar_chart(self, df_cu_1906_2024: pd.DataFrame, use_cul: bool = True):
        if use_cul:
            df_lb_cul = self.demand.df_lb_cul
            ltsc_df = self.demand.az_ltsc_data.df
            series = BarGroup(
                label="",
                series=[
                    # CA
                    BarSeries(df=df_cu_1906_2024, col="CA", color=Colors.CA),
                    BarSeries(df=df_cu_1906_2024, col="Alamo", color=Colors.CA_ALAMO),
                    BarSeries(df=df_cu_1906_2024, col="Volcano", color=Colors.CA_VOLCANO),
                    BarSeries(df=df_cu_1906_2024, col=lb.IMPERIAL_VALLEY_CU, color=Colors.CA_IMPERIAL,
                              label='Imperial'),
                    BarSeries(df=df_cu_1906_2024, col="Yuma Project", color=Colors.CA4),
                    BarSeries(df=df_cu_1906_2024, col="Palo Verde", color=Colors.CA_PALO_VERDE),
                    BarSeries(df=df_cu_1906_2024, col=lb.CA_MAINSTEM, color=Colors.CA4, label='CA Misc'),
                    BarSeries(df=df_cu_1906_2024, col=lb.METROPOLITAN_CU, color=Colors.CA_MWD, label='MWD'),

                    # NV
                    BarSeries(df=df_cu_1906_2024, col="NV", color=Colors.NV1),
                    BarSeries(df=df_lb_cul, col=lb.NV_COLORADO_RIVER_TOTAL, color=Colors.NV2, label='NV'),

                    # AZ
                    BarSeries(df=df_cu_1906_2024, col="AZ", color=Colors.AZ),
                    BarSeries(df=df_lb_cul, col=lb.AZ_MAINSTEM, color=Colors.AZ, label='AZ Misc'),
                    BarSeries(df=self.df, col=lb.AZ_CRIT_CU, color=Colors.AZ, label='CRIT'),
                    BarSeries(df=self.df, col=lb.WELLTON_MOHAWK_CU, color=Colors.AZ, label='Wellton'),
                    BarSeries(df=df_lb_cul, col=lb.AZ_CAP, color=Colors.AZ1, label='CAP'),
                    BarSeries(df=ltsc_df, col=lb.AZ_LTSC_STORED, color=Colors.AZ2, label='AZ Aquifer'),

                    BarSeries(df=df_cu_1906_2024, col="Cienega", color=Colors.MX_CIENEGA),
                    BarSeries(df=df_cu_1906_2024, col="Mexico Treaty", color=Colors.MX, label='MX'),
                    BarSeries(df=df_cu_1906_2024, col="LB Evap", color=Colors.EVAPORATION, label='Evap'),
                    BarSeries(df=df_cu_1906_2024, col="Delta", color=Colors.MX_DELTA),
                ],
            )
        else:
            series = BarGroup(
                label="",
                series=[
                    BarSeries(df=df_cu_1906_2024, col="CA", color=Colors.CA),
                    BarSeries(df=df_cu_1906_2024, col="NV", color=Colors.NV1),
                    BarSeries(df=df_cu_1906_2024, col="AZ", color=Colors.AZ),
                    BarSeries(df=df_cu_1906_2024, col="Mexico Treaty", color=Colors.MX),
                    BarSeries(df=df_cu_1906_2024, col="Cienega", color=Colors.MX_CIENEGA),
                    BarSeries(df=df_cu_1906_2024, col="LB Evap", color=Colors.EVAPORATION),
                    BarSeries(df=df_cu_1906_2024, col="Delta", color=Colors.MX_DELTA),
                ],
            )

        legend = [
            ("MX", Colors.MX),
            ("AZ", Colors.AZ),
            ("NV", Colors.NV1),
            ("CA", Colors.CA),
            ("Alamo", Colors.CA_ALAMO),
        ]
        self.lb_demand_chart = MultiBarChart(
            title='',
            percentage=0.60,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min=0,
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
        series = BarGroup(
            label="",
            series=[
                BarSeries(df=df_cu_1906_2024, col="LB Tributary CU", color='orange'),
            ],
        )
        self.lb_trib_chart = MultiBarChart(
            title='',
            percentage=0.20,
            groups=[series],
            start_year=self.start_year,
            end_year=self.end_year,
            x_min=0,
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
            self._annotate_bottom(ax, 1882, "GVIC'82", offset_lines=-1, color=Colors.UB) # Water rights 1882, formed 1894
            self._annotate_bottom(ax, 1885, "Montezuma'85", offset_lines=0, color=Colors.UB) # 1885
            self._annotate_bottom(ax, 1882, "Uncompaghre'82", offset_lines=1, color=Colors.UB) # 1882
            self._annotate_bottom(ax, 1901, "Alamo'01", offset_lines=2, color=Colors.LB) # California Development Company (CDC) 1896
            # self._annotate_bottom(ax, 1902, "UVWUA", offset_lines=0, color=Colors.UB)

            # self._annotate_bottom(ax, 1906, "Alamo Fixed", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1908, "Palo Verde", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1909, "Gunnison", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1911, "IID", offset_lines=-1, color=Colors.LB)
            self._annotate_bottom(ax, 1910, "SRP", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1922, "Compact")
            self._annotate_bottom(ax, 1923, "PVID", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1915, "Grand\nValley", color=Colors.UB)
            self._annotate_bottom(ax, 1929, "BCPA", offset_lines=0)
            self._annotate_bottom(ax, 1931, "AZ v CA", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1936, "Moffat", offset_lines=1, color=Colors.UB)
            self._annotate_bottom(ax, 1933, "Depression", offset_lines=2)
            self._annotate_bottom(ax, 1937, "Asalto", offset_lines=0, color=Colors.MX)
            self._annotate_bottom(ax, 1944, "MX Treaty", offset_lines=0, color=Colors.MX)
            self._annotate_bottom(ax, 1939, "MWD", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1940, "All Am", offset_lines=2, color=Colors.LB)
            self._annotate_bottom(ax, 1947, "Coachella", offset_lines=1, color=Colors.LB)
            self._annotate_bottom(ax, 1947, "Northern", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1951, "Wellton", color=Colors.LB)
            self._annotate_bottom(ax, 1959, "MWD\u2191", offset_lines=2, color=Colors.LB)
            self._annotate_bottom(ax, 1964, "Roberts", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1964, "AZ v CA", color=Colors.LB)
            self._annotate_bottom(ax, 1972, "Fryark", color=Colors.UB)
            self._annotate_bottom(ax, 1971, "CUP", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1971, "LV", offset_lines=1, color=Colors.LB)  # LVVWD
            self._annotate_bottom(ax, 1968, "CRBPA", offset_lines=1)
            self._annotate_bottom(ax, 1984, "Dolores", offset_lines=2, color=Colors.UB)
            self._annotate_bottom(ax, 1982, "El Niño", offset_lines=1)
            self._annotate_bottom(ax, 1985, "CAP", color=Colors.LB)
            self._annotate_bottom(ax, 1992, "AZ Aquifers", offset_lines=0, color=Colors.LB)
            self._annotate_bottom(ax, 1991, "SNWA", offset_lines=2, color=Colors.LB)
            self._annotate_bottom(ax, 1990, "Yuma Project", offset_lines=1, color=Colors.LB)
            # self._annotate_bottom(ax, 1990, "Cienega", offset_lines=2, color=Colors.MX_CIENEGA)
            self._annotate_bottom(ax, 2003, "QSA", color=Colors.LB)
            self._annotate_bottom(ax, 2007, "2007\nGuidelines", offset_lines=1)
            self._annotate_bottom(ax, 2014, "Delta\nPulse", color=Colors.LB)
            self._annotate_bottom(ax, 2018, "DCP")

if __name__ == "__main__":
    app = wx.App(False)

    rw = RiverWar()
    nf = NotebookFrame([], rw)

    d = Demand(rw, show_tributaries=False)

    # SupplyVDemandPie(nf, d)
    SupplyVDemand(nf, d)

    nf.Show()
    app.MainLoop()