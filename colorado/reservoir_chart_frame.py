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
from chart.chart_frame import ChartFrame, NotebookFrame
import colorado.ub as ub
import colorado.allb as all_b
from api import df_utils

class ReservoirChartFrame(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.start_year = 1971
        self.end_year = 2024

        super().__init__(notebook_frame, page_name='Pie Chart')

    def create_toolbar(self):
        super().create_toolbar()

    def load_charts(self):

        # ====================== LAKE POWELL ======================
        df_powell: pd.DataFrame = df_utils.create_df(self.start_year, self.end_year,
                                                     [ub.POWELL, ub.GLEN_CANYON_RELEASE_WY, ub.POWELL_EVAPORATION, ub.INFLOW])

        usbr_lake_powell_release_total_af = 4354
        sheet.usbr_annuals(df_powell, usbr_lake_powell_release_total_af, self.start_year, self.end_year, month=all_b.WY,
                           title=ub.GLEN_CANYON_RELEASE_WY, divisor=1)

        usbr_lake_powell_storage_af = 509
        sheet.usbr_last_value(df_powell, usbr_lake_powell_storage_af, self.start_year, self.end_year, month=all_b.WY,
                              title=ub.POWELL, divisor=1)

        usbr_lake_powell_evap_af = 510
        sheet.usbr_annuals(df_powell, usbr_lake_powell_evap_af, self.start_year, self.end_year, month=all_b.WY,
                           title=ub.POWELL_EVAPORATION, divisor=1)

        usbr_lake_powell_regulated_inflow_af = 4288
        sheet.usbr_annuals(df_powell, usbr_lake_powell_regulated_inflow_af, self.start_year, self.end_year, month=all_b.WY,
                           title=ub.INFLOW, divisor=1)

        # ============= POWELL INFLOW OUTFLOW BAR CHART ==============
        bar_groups = [
            ('Release', [
                (df_powell, ub.GLEN_CANYON_RELEASE_WY, 'darkred')
            ]),
            ('Inflow', [
                (df_powell, ub.INFLOW, 'royalblue')
            ]),
        ]
        powell_inflow_outflow = MultiBarChart(
            groups=bar_groups,
            # underlay_lines=underlay_lines,
            # overlay_lines=overlay_lines,
            title="Powell Inflow Outflow",
            start_year=self.start_year,
            end_year=self.end_year,
            x_min=1999,
            y_max=16.0
        )
        self.charts.append(powell_inflow_outflow)