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
from datetime import date
import pandas as pd
from typing import List
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

class PieChartFrame(ChartFrame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):
        super().__init__(reservoir_list, date_time, report_list, title, page_name='Reservoirs')

    def load_charts(self):
        headers = [ub.III_A_UB, ub.CU_CO, ub.CU_UT, ub.CU_WY, ub.CU_NM, ub.AZ_CU]
        df_ub_cul: pd.DataFrame = sheet.create_df(1964, 2024, headers)
        sheet.upper_basin_cul_from_excel(df_ub_cul)
        df_ub_cul[ub.CU_CO] = df_ub_cul[ub.CU_CO] * 1_000_000
        df_ub_cul[ub.CU_WY] = df_ub_cul[ub.CU_WY] * 1_000_000
        df_ub_cul[ub.CU_UT] = df_ub_cul[ub.CU_UT] * 1_000_000
        df_ub_cul[ub.CU_NM] = df_ub_cul[ub.CU_NM] * 1_000_000



        df_empty = pd.DataFrame()
        lb_tributary_cul = LBTributaryCUL(all_b.LB_TRIBUTARY_CUL_SHEET)
        lb_tributary_cul.load_df(df_empty)
        lb_reservoirs_cul = LBReservoirCUL(all_b.LB_RESERVOIRS_CUL_SHEET)
        lb_reservoirs_cul.load_df(df_empty)
        lb_mainstream_cul = LBMainstreamCUL(all_b.LB_MAINSTEM_CUL_SHEET)
        lb_mainstream_cul.load_df(df_empty)

        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(lb_mainstream_cul.df, df_mx, lb.MEXICO, divisor=1)

        pie_wedges = []

        pie_wedges.append((df_ub_cul, ub.CU_CO, '#6060ff'))
        pie_wedges.append((df_ub_cul, ub.CU_UT, '#8080ff'))
        pie_wedges.append((df_ub_cul, ub.CU_NM, '#a0a0ff'))
        pie_wedges.append((df_ub_cul, ub.CU_WY, '#c0c0ff'))

        pie_wedges.append((lb_mainstream_cul.df, lb.MEXICO, '#40ff40'))

        pie_wedges.append((lb_reservoirs_cul.df, lb.LAKE_MEAD_CUL, 'gold'))

        pie_wedges.append((lb_mainstream_cul.df, lb.NV_M_I_OTHER, 'orange'))

        pie_wedges.append((lb_mainstream_cul.df, lb.CA_OUTSIDE_SYSTEM, '#ff80ff'))
        pie_wedges.append((lb_mainstream_cul.df, lb.CA_AGRICULTURE, '#ffa0ff'))

        pie_wedges.append((lb_mainstream_cul.df, lb.AZ_WITHIN_SYSTEM, '#ffa0a0'))
        pie_wedges.append((lb_mainstream_cul.df, lb.AZ_AGRICULTURE, '#ff8080'))
        pie_wedges.append((lb_tributary_cul.df, lb.AZ_GILA_CUL, '#ff4040'))


        pie_chart = PieChart(
            pie_wedges, title='Colorado River Consumptive Use Losses',
        )
        self.charts.append(pie_chart)

