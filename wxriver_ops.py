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
from pathlib import Path
import wx
import matplotlib
from datetime import date
import os
import pandas as pd
from typing import List
from sheet import sheet
from colorado.lb_mainstream_cul import LBMainstreamCUL
from colorado.lb_reservoir_cul import LBReservoirCUL
from colorado.lb_tributary_cul import LBTributaryCUL
from reservoirs.reservoir import Reservoir
from colorado.graph_inflow_outflow import InflowOutflowChart
from colorado.graph_reservoirs import ReservoirChart
from chart.chart_frame import ChartFrame
from chart.line_chart import LineChart
from chart.pie_chart import PieChart
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

def find_directories_with_file(root_dir: str, filename: str) -> List[str]:
    """Return list of directories containing the given filename."""
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    matching_dirs = []
    for dir_path in root.rglob("*"):
        if dir_path.is_dir():
            if (dir_path / filename).is_file():
                matching_dirs.append(str(dir_path.resolve()))

    return sorted(set(matching_dirs))


# ==================== MAIN FRAME ====================

class ReservoirChartFrame(ChartFrame):
    def __init__(self, reservoir_list: List[Reservoir], date_time: date,
                 report_list: List[str] | None = None,
                 title: str = "Colorado River War"):
        super().__init__(reservoir_list, date_time, report_list, title, page_name='Reservoirs')

    def chart_pie(self):
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

        pie_wedges = []
        pie_wedges.append((df_ub_cul, ub.CU_CO, '#6060ff'))
        pie_wedges.append((df_ub_cul, ub.CU_UT, '#8080ff'))
        pie_wedges.append((df_ub_cul, ub.CU_NM, '#a0a0ff'))
        pie_wedges.append((df_ub_cul, ub.CU_WY, '#c0c0ff'))

        pie_wedges.append((lb_reservoirs_cul.df, lb.LAKE_MEAD_CUL, '#ffff80'))

        pie_wedges.append((lb_mainstream_cul.df, lb.CA_OUTSIDE_SYSTEM, '#ff80ff'))
        pie_wedges.append((lb_mainstream_cul.df, lb.CA_AGRICULTURE, '#ffa0ff'))

        pie_wedges.append((lb_mainstream_cul.df, lb.AZ_WITHIN_SYSTEM, '#ffa0a0'))
        pie_wedges.append((lb_mainstream_cul.df, lb.AZ_AGRICULTURE, '#ff8080'))
        pie_wedges.append((lb_tributary_cul.df, lb.AZ_GILA_CUL, '#ff4040'))

        pie_wedges.append((lb_mainstream_cul.df, lb.NV_M_I_OTHER, '#ffc080'))

        pie_chart = PieChart(
            pie_wedges, title='CUL',
        )
        self.charts.append(pie_chart)

    def chart_line(self):
        time_series = []
        for reservoir in reservoirs:
            if reservoir.name == 'Lake Powell':
                time_series.append((reservoir.df_daily, ub.POWELL_MOST, '#a0a0ff'))
                time_series.append((reservoir.df_daily, ub.POWELL_ABOVE_3500, 'dodgerblue'))
            elif reservoir.name == 'Lake Mead':
                time_series.append((reservoir.df_daily, lb.MEAD_MOST, '#ffa0a0'))
                time_series.append((reservoir.df_daily, lb.MEAD_ABOVE_1000, 'darkred'))
        line_chart = LineChart(
            time_series, title='MAR26 24 Month Reservoir Storage Above Critical Elevation',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date
        )
        self.charts.append(line_chart)

    def chart_reservoir(self):
        start = self.start_nav.current_date
        current = self.current_nav.current_date
        end = self.end_nav.current_date

        reservoir_chart = ReservoirChart(
            reservoirs, start_date=start, current_date=self.current_time_from_usbr, end_date=end
        )
        self.charts.append(reservoir_chart)

        inflow_chart = InflowOutflowChart(
            reservoirs, start_date=start, current_date=current, end_date=end
        )
        self.charts.append(inflow_chart)

    def load_charts(self):
        chart_type = 'line'
        chart_type = 'reservoir'
        chart_type = 'pie'
        if chart_type == 'pie':
            self.chart_pie()
        elif chart_type == 'line':
            self.chart_line()
        else:
            self.chart_reservoir()

# ==================== RUN ====================
if __name__ == "__main__":
    from reservoirs.reservoir import Reservoir
    from reservoirs.imperial import Imperial
    from reservoirs.lake_havasu import LakeHavasu
    from reservoirs.lake_mohave import LakeMohave
    from reservoirs.aquifers import Aquifers
    from reservoirs.lake_mead import LakeMead
    from reservoirs.lake_powell import LakePowell
    from reservoirs.flaming_gorge import FlamingGorge
    from reservoirs.blue_mesa import BlueMesa
    from reservoirs.navajo import Navajo

    reports = find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')

    flaming_gorge = FlamingGorge()
    navajo = Navajo()
    blue_mesa = BlueMesa()
    lake_powell = LakePowell(upstream=[flaming_gorge, blue_mesa, navajo])
    lake_mead = LakeMead(upstream=[lake_powell])
    lake_mohave = LakeMohave(upstream=[lake_mead])
    lake_havasu = LakeHavasu(upstream=[lake_mohave])
    imperial = Imperial(upstream=[lake_havasu])
    aquifers = Aquifers(upstream=[])

    reservoirs = [
        imperial, aquifers, lake_havasu, lake_mohave,
        lake_mead, lake_powell, flaming_gorge, navajo, blue_mesa
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs, lake_powell.date_time, reports)
    frame.Show()
    app.MainLoop()