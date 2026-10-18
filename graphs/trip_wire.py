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
import wx
import colorado.ub as ub
from sheet import sheet
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.multi_bar_chart import MultiBarChart, BarGroup, BarSeries
from colorado.river_war import RiverWar
import colorado.allb as all_b
import colorado.lb as lb
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from typing import Optional
from api import df_utils


class TripWire(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Trip Wire'
        self.report_name, reports_latest = ChartFrame.get_latest_reports()

        self.start_year = 1991
        self.end_year = 2026
        self.current_year = self.start_year
        self.timer = None
        self.animation_interval = 1000
        self.version = 0.4
        self.play_btn = None
        self.year_slider = None
        self.toolbar_status = None
        self.supply_demand_chart:Optional[MultiBarChart] = None
        self.lees_ferry_chart:Optional[MultiBarChart] = None
        self.multi_bar_chart:Optional[MultiBarChart] = None
        super().__init__(notebook_frame, page_name=self.name)
        self.right_axis_annotations()

    def right_axis_annotations(self):
        ax = self.supply_demand_chart.ax
        ChartFrame.annotate_level(ax, 9.0, '9.0',
                                  lb.MX_COLOR, draw_text=True, draw_line=True,
                                  left_of_axis=False)

        ax = self.lees_ferry_chart.ax
        ChartFrame.annotate_level(ax, 7.5, '7.5',
                                      'dodgerblue', draw_text=True, draw_line=True,
                                      left_of_axis=False)
        ChartFrame.annotate_level(ax, 8.25, '8.25',
                                      'red', draw_text=True, draw_line=True,
                                      left_of_axis=False)

    def load_charts(self):
        river_war = self.notebook_frame.river_war

        # ====================== LAKE POWELL ======================
        powell = river_war.reservoir.get('Lake Powell')
        powell.load_data_annual(self.start_year, self.end_year)

        # ====================== NATURAL FLOW ======================
        #natural_flow_data = river_war.dataset.get('Natural Flow')

        lake_powell = LakePowell(upstream=[])
        lake_mead = LakeMead(upstream=[lake_powell])

        df_powell = lake_powell.load_data_annual(start_year=self.start_year)
        sheet.usgs_annuals(df_powell,  '09380000', self.start_year, self.end_year,
                           month=all_b.WY,
                           title=ub.LEES_FERRY_USGS, divisor=1)
        df_utils.moving_average(df_powell, ub.LEES_FERRY_USGS, 'Lees Ferry 10 yr avg')

        # sheet.usgs_annuals(df_powell, '09380000', self.start_year, self.end_year, title=ub.LEES_FERRY_USGS, divisor=1)
        df_mead = lake_mead.load_data_annual(start_year=self.start_year)
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(df_mead, df_mx, lb.MEXICO, divisor=1)

        df_utils.subtract_column(df_mead, all_b.RELEASE, lb.MEXICO, result_column="Lower Basin")

        # ============= POWELL INFLOW, MEAD RELEASE  ==============
        powell_inflow_bar = BarGroup(
            label="Powell Inflow", series=[BarSeries(df=df_powell, col=all_b.INFLOW, color="royalblue", label="Regulated")]
        )
        hoover_release_bar = BarGroup(
            label = "Hoover", series = [
                BarSeries(df=df_mead, col="Mexico", color=lb.MX_COLOR, label="Mexico"),
                BarSeries(df=df_mead, col="Lower Basin", color="maroon", label="Lower Basin")
            ]
        )

        graph_start_year = 1999
        today = date.today()
        graph_end_year = today.year
        self.supply_demand_chart = MultiBarChart(
            title=f'Colorado River {self.name}',
            percentage=0.33,
            groups=[hoover_release_bar, powell_inflow_bar],
            start_year=graph_start_year,
            end_year=graph_end_year,
            y_max=16,
            y_min=0,
            show_x_labels=False
        )
        self.charts.append(self.supply_demand_chart)

        # ============= LEES FERRY ==============
        overlay_10_year = [
            (
                df_powell,
                "Lees Ferry 10 yr avg",
                "goldenrod",
                {
                    "label": "Lees Ferry 10 yr avg",
                    "linewidth": 2.5,
                    "linestyle": "-",
                    "marker": "", # "o"
                    # "markersize": 5,
                    # "markerfacecolor": 'black',
                    # "markeredgecolor": 'red',
                }
            ),
        ]
        lees_ferry_bar = BarGroup(
            label="", series=[BarSeries(df=df_powell, col=ub.LEES_FERRY_USGS, color="royalblue")]
        )
        self.lees_ferry_chart = MultiBarChart(
            percentage=0.33,
            groups=[lees_ferry_bar],
            overlay_lines=overlay_10_year,
            start_year=graph_start_year,
            end_year=graph_end_year,
            y_max=13,
            y_min=4,
            show_x_labels=True
        )
        self.charts.append(self.lees_ferry_chart)
        # graph_end_date = date(2028, 12, 31)
        # self.lees_ferry_chart.set_start_date(graph_end_date)

        # ============= RESERVOIR STORAGE ==============

        powell_bar = BarGroup(
            label="Powell", series=[BarSeries(df=df_powell, col=all_b.STORAGE, color="royalblue")]
        )
        mead_bar = BarGroup(
            label="Mead",series=[BarSeries(df=df_mead, col=all_b.STORAGE, color="maroon")]
        )

        self.multi_bar_chart = MultiBarChart(
            percentage=0.33,
            groups=[mead_bar, powell_bar],
            start_year=graph_start_year,
            end_year=graph_end_year,
            y_max=26,
            y_min=3,
            show_x_labels=False
        )
        self.charts.append(self.multi_bar_chart)

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    TripWire(notebook_frame=notebook_frame)

    notebook_frame.Show()
    app.MainLoop()