"""
Copyright (c) 2025 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:from api import df_utils


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
from datetime import date
import pandas as pd
from typing import List, Optional
from sheet import sheet
from colorado.lb_mainstream_cul import LBMainstreamCUL
from colorado.lb_reservoir_cul import LBReservoirCUL
from colorado.lb_tributary_cul import LBTributaryCUL
from reservoirs.reservoir import Reservoir
from chart.chart_frame import ChartFrame
from chart.pie_chart import PieChart
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils

class PieChartFrame(ChartFrame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):
        self.start_year = 1971
        self.end_year = 2025
        super().__init__(reservoir_list, date_time, report_list, title, page_name='Reservoirs')


    def load_charts(self):
        headers = [ub.III_A_UB, ub.CU_CO, ub.CU_UT, ub.CU_WY, ub.CU_NM, ub.AZ_CU,
                   ub.POWELL_EVAPORATION, ub.FLAMING_GORGE_EVAPORATION_WY,
                   ub.BLUE_MESA_EVAPORATION_WY, ub.MORROW_EVAPORATION_WY]
        df_ub_cul: pd.DataFrame = df_utils.create_df(self.start_year, self.end_year, headers)
        show_tributaries = False

        pie_wedges = []

        # Upper Basin
        #
        sheet.upper_basin_cul_from_excel(df_ub_cul, row_offset=0, divisor=1)
        pie_wedges.append((df_ub_cul, ub.CU_CO, '#6060ff'))
        pie_wedges.append((df_ub_cul, ub.CU_UT, '#8080ff'))
        pie_wedges.append((df_ub_cul, ub.CU_WY, '#a0a0ff'))
        pie_wedges.append((df_ub_cul, ub.CU_NM, '#c0c0ff'))
        df_utils.add_column_sum(df_ub_cul,
                                [ub.POWELL_EVAPORATION, ub.FLAMING_GORGE_EVAPORATION_WY,
                                 ub.BLUE_MESA_EVAPORATION_WY, ub.MORROW_EVAPORATION_WY],
                                ub.UB_RESERVOIR_EVAP)
        pie_wedges.append((df_ub_cul, ub.UB_RESERVOIR_EVAP, 'gold'))

        # Lower Basin
        #
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
        pie_wedges.append((lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP, 'gold'))

        # California
        #
        # Imperial Valley
        #
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
        pie_wedges.append((lb_mainstream_cul.df, lb.SALTON_INFLOW, 'gold'))

        # Mexico
        #
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_mx, lb.MEXICO, divisor=1)
        pie_wedges.append((lb_mainstream_cul.df, lb.MEXICO, '#40a040'))

        # California
        #
        pie_wedges.append((lb_mainstream_cul.df, lb.IMPERIAL_VALLEY_CU, '#c040c0'))
        pie_wedges.append((lb_mainstream_cul.df, lb.CA_OUTSIDE_SYSTEM, '#e080e0'))
        pie_wedges.append((lb_mainstream_cul.df, lb.CA_MAINSTEM, '#ffa0ff'))

        df_utils.add_column_sum(lb_mainstream_cul.df,
                                [lb.CA_OUTSIDE_SYSTEM, lb.CA_MAINSTEM, lb.SALTON_INFLOW, lb.IMPERIAL_VALLEY_CU],
                                lb.CA_TOTAL)
        # Nevada
        #
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
        pie_wedges.append((lb_mainstream_cul.df, lb.NV_TOTAL, 'orange'))

        # Arizona Mainstem
        #
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.AZ_M_I_OTHER, lb.AZ_AGRICULTURE, lb.AZ_POWER], lb.AZ_MAINSTEM)
        df_utils.rename_column(lb_mainstream_cul.df, lb.AZ_WITHIN_SYSTEM, lb.AZ_CAP, inplace=True)
        df_utils.add_column_sum(lb_mainstream_cul.df, [lb.AZ_CAP, lb.AZ_MAINSTEM], lb.AZ_COLORADO_RIVER_TOTAL)

        pie_wedges.append((lb_mainstream_cul.df, lb.AZ_MAINSTEM, '#ffa0a0'))
        pie_wedges.append((lb_mainstream_cul.df, lb.AZ_CAP,  '#ff8080'))

        # Arizona Tributary
        #
        if show_tributaries:
            pie_wedges.append((lb_tributary_cul.df, lb.AZ_GILA_CUL, '#ff4040'))
            df_utils.add_column_sum(lb_tributary_cul.df,
                                    [lb.AZ_LITTLE_COLORADO_CUL,
                                     lb.AZ_VIRGIN_CUL,
                                     lb.AZ_BILL_WILLIAMS_CUL,
                                     lb.AZ_TRIB_BELOW_LAKE_MEAD_CUL],
                                    lb.AZ_TRIBUTARY_CUL)
            pie_wedges.append((lb_tributary_cul.df, lb.AZ_TRIBUTARY_CUL, '#ff4040'))
            df_utils.add_columns_across_dfs([
                (lb_mainstream_cul.df, lb.AZ_COLORADO_RIVER_TOTAL),
                (lb_tributary_cul.df, lb.AZ_GILA_CUL),
                (lb_tributary_cul.df, lb.AZ_TRIBUTARY_CUL)],
                lb_mainstream_cul.df, lb.AZ_TOTAL)
        else:
            df_utils.add_columns_across_dfs([
                (lb_mainstream_cul.df, lb.AZ_COLORADO_RIVER_TOTAL)],
                lb_mainstream_cul.df, lb.AZ_TOTAL)

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
            (df_ub_cul, ub.III_A_UB),
            (lb_mainstream_cul.df, lb.LB_TOTAL),
            (lb_mainstream_cul.df, lb.MEXICO)],
            lb_mainstream_cul.df, all_b.COLORADO_RIVER_TOTAL)
        totals = (0.0, 0.99, [
            ("Lower Basin", (lb_mainstream_cul.df, lb.LB_TOTAL)),
            ("Upper Basin", (df_ub_cul, ub.III_A_UB)),
            ("Mexico", (lb_mainstream_cul.df, lb.MEXICO)),
            ("Total", (lb_mainstream_cul.df, all_b.COLORADO_RIVER_TOTAL))
        ])

        lb_totals = (0.9, 0.99, [
            ("CA", (lb_mainstream_cul.df, lb.CA_TOTAL)),
            ("AZ", (lb_mainstream_cul.df, lb.AZ_TOTAL)),
            ("NV", (lb_mainstream_cul.df, lb.NV_TOTAL)),
            ("LB Evap", (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP)),
            ("Total", (lb_mainstream_cul.df, lb.LB_TOTAL))
        ])

        evap_totals = (0.0, 0.05, [
            ("UB Evap", (df_ub_cul, ub.UB_RESERVOIR_EVAP)),
            ("LB Evap", (lb_reservoirs_cul.df, lb.LB_RESERVOIR_EVAP)),
            ("Salton Evap", (lb_mainstream_cul.df, lb.SALTON_INFLOW)),
            ("Total", (lb_mainstream_cul.df, all_b.EVAP_TOTAL))
        ])

        pie_chart = PieChart(
            pie_wedges,
            title='Colorado River Consumptive Use Losses',
            year=2018,
            annotations=[totals, lb_totals, evap_totals]
        )
        self.charts.append(pie_chart)
