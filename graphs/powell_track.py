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
import datetime
import re
import wx
from colorado.river_war import RiverWar
from chart.chart import Chart
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart, TimeSeries
import colorado.ub as ub
from reservoirs.reservoir import Reservoir
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from typing import List,Tuple

from pdf_reader.pdf_reader import download_usbr_24mo_reports
# from source.crbfc import request_esplist, request_forecast

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class ReservoirsBig3(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Powell Track'
        self.version = 0.4

        self.report_name, reports_latest = ChartFrame.get_latest_reports(path='/opt/dev/riverwar/data/USBR_24Month_Reports/2026/SEP26_MIN')

        self.line_chart = None
        self.inflow_outflow_chart = None
        self.fg_inflow_outflow_chart = None
        self.powell_inflows = None
        self.powell_release_chart = None

        flaming_gorge = FlamingGorge()
        lake_powell = LakePowell(upstream=[flaming_gorge])
        reservoirs = [
            flaming_gorge,
            lake_powell,
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=reports_latest, page_name=self.name)
        self.right_axis_annotations()

    def right_axis_annotations(self):
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if  reservoir.name == 'Lake Powell':
                    crit_points = getattr(reservoir, 'critical_elevations_feet', [])
                    if crit_points:
                        if hasattr(self.line_chart, 'ax') and self.line_chart.ax is not None:
                            min_capacity = 0
                            ax = self.line_chart.ax
                            for item in crit_points:
                                if isinstance(item, (list, tuple)) and len(item) >= 3:
                                    if item[0] == 'Safe Power Head':
                                        min_capacity = item[2]
                                        ChartFrame.annotate_level(ax, 0.0, str(round(item[1])),
                                                                      'royalblue', draw_text=True, draw_line=True,
                                                                      left_of_axis=True)

                            elevation_3510_ft = getattr(reservoir, 'power_head_target_feet', 0)
                            elevation_3510_af = getattr(reservoir, 'power_head_target_af', 0)
                            if elevation_3510_af:
                                ax = self.line_chart.ax
                                ChartFrame.annotate_level(ax, elevation_3510_af-min_capacity, elevation_3510_ft,
                                                              'royalblue', draw_text=True, left_of_axis=True)

    def load_charts(self):
        powell_df = None

        today = datetime.date.today()
        graph_start_date = datetime.date(2026, 3, 1)
        graph_end_date = datetime.date(2027, 3, 1)

        # Powell and Flaming Gorge Storage
        #
        time_series = []
        legend_studies = []
        legend_variables = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Lake Powell':
                    powell_df = reservoir.df_daily
                    time_series.append((reservoir.df_daily, ub.POWELL_ABOVE_3490, 'dodgerblue'))
                    legend_variables.append((ub.POWELL_ABOVE_3490, 'dodgerblue'))
                    legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'End Of Month Storage', "#a0a0ff",
                                                     subtract=reservoir.power_head_min_af, is_storage=True, linewidth=2.5)
                elif reservoir.name == 'Flaming Gorge':
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))
                    legend_variables.append(( ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))
                    ReservoirsBig3.add_report_series(reservoir, time_series, 'Live Storage', "#50a050",
                                                     subtract=reservoir.power_head_min_af, is_storage=True, linewidth=2.5)

        self.line_chart = LineChart(
            time_series,
            title=f'Colorado River {self.name} 24 Month={self.report_name} - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = False,
            show_right_labels = True,
            percentage=0.50,
            y_min = 750_000,
            y_max = 3_000_000,
            compact_legend=True,
            legend_variables=legend_variables,
            legend_studies=legend_studies
        )
        self.line_chart.set_start_date(graph_start_date)
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        # Powell Inflows
        #
        legend_studies = []
        time_series: List[Tuple] = [
            (powell_df, 'Colorado River Near Cisco UT', 'royalblue'),
            (powell_df, 'Green River Near Green River, UT', 'darkgreen'),
            (powell_df, 'San Juan River Near Bluff, UT', 'goldenrod'),
            (powell_df, 'Dirty Devil Near Hanksville, UT', 'purple')
        ]
        legend_variables = [('Colorado River Near Cisco UT', 'royalblue'),
                            ('Green River Near Green River, UT', 'darkgreen'),
                            ('San Juan River Near Bluff, UT', 'goldenrod'),
                            ('Dirty Devil Near Hanksville, UT', 'purple')]
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Powell':
                    legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'Regulated Inflow', "blue")

        self.powell_inflows = LineChart(
            time_series, title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels=True,
            percentage=0.20,
            y_units='CFS',
            y_max=18_000,
            y_min = 0,
            stacked=True,
            compact_legend=True,
            legend_variables=legend_variables,
            legend_studies=legend_studies
        )
        self.powell_inflows.set_start_date(graph_start_date)
        self.powell_inflows.set_end_date(graph_end_date)
        self.charts.append(self.powell_inflows)

        # Powell Inflows
        #
        time_series = []
        legend_studies = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Powell':
                    time_series.append((reservoir.df_daily, ub.POWELL_INFLOW_CFS, 'royalblue'))
                    legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'Regulated Inflow', "blue")

        self.inflow_outflow_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = False,
            percentage=0.10,
            y_min=0,
            y_units='CFS',
            legend_studies=legend_studies,
        )
        self.inflow_outflow_chart.set_start_date(graph_start_date)
        self.inflow_outflow_chart.set_end_date(graph_end_date)
        self.charts.append(self.inflow_outflow_chart)

        # Flaming Gorge Inflow/Outflow
        #
        time_series = []
        legend_studies = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Flaming Gorge':
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_INFLOW_CFS, 'darkgreen'))
                    # legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'Regulated Inflow', "green")
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_RELEASE_CFS, '#50a050'))
                    legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'Total Release', "green")

        self.fg_inflow_outflow_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = False,
            percentage=0.10,
            y_min=0,
            y_units='CFS',
            legend_studies=legend_studies,
        )
        self.fg_inflow_outflow_chart.set_start_date(graph_start_date)
        self.fg_inflow_outflow_chart.set_end_date(graph_end_date)
        self.charts.append(self.fg_inflow_outflow_chart)

        # Powell Release and Evap
        #
        time_series = []
        legend_studies = []
        legend_variables = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Powell':
                    time_series.append((reservoir.df_daily, ub.POWELL_RELEASE_CFS, 'dodgerblue'))
                    legend_variables.append((ub.POWELL_RELEASE_CFS, 'dodgerblue'))
                    for i, (report_name, dfs) in enumerate(reservoir.reports.items()):
                        pass
                    legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'Total Release', "blue")

        self.powell_release_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = False,
            percentage=0.10,
            y_max=10_000,
            y_min=5_000,
            y_units='CFS',
            compact_legend=True,
            legend_variables=legend_variables,
            legend_studies=legend_studies
        )
        self.powell_release_chart.set_start_date(graph_start_date)
        self.powell_release_chart.set_end_date(graph_end_date)
        self.charts.append(self.powell_release_chart)

    @staticmethod
    def add_report_series(
            reservoir,
            time_series: list,
            column_name: str,
            color: str,
            linewidth: float = 2,
            convert_af_to_cfs: bool = True,
            subtract_col: str | None = None,
            subtract: float = 0.0,
            is_storage: bool = False
    ) -> List[Tuple[str, str]]:
        """
        For each report on the reservoir, distribute the given monthly column
        to daily, then insert a line-series tuple into time_series.
        Line style cycles by report index: solid, dotted, dashed, ...

        If is_storage=True, uses interpolate_monthly_storage_to_daily
        instead of monthly_total_to_daily_smooth.

        If subtract_col is provided, that daily column is subtracted from the
        interpolated result.
        If subtract != 0, that constant is also subtracted.
        """
        legend_studies = []
        styles = ["dotted", "--", "-", "-."]

        for i, (report_name, dfs) in enumerate(reservoir.reports.items()):
            line_style = styles[i % len(styles)]
            name = f"{report_name}.{column_name}"
            df, df_wy = dfs

            if is_storage:
                Reservoir.interpolate_monthly_storage_to_daily(
                    df,
                    reservoir.df_daily,
                    monthly_value_col=column_name,
                    daily_target_col=name
                )
            else:
                Reservoir.monthly_total_to_daily_smooth(
                    df,
                    reservoir.df_daily,
                    monthly_value_col=column_name,
                    daily_target_col=name,
                    convert_af_to_cfs=convert_af_to_cfs
                )

            if subtract_col and subtract_col in reservoir.df_daily.columns:
                reservoir.df_daily[name] = (
                        reservoir.df_daily[name] - reservoir.df_daily[subtract_col]
                )

            if subtract:
                reservoir.df_daily[name] = reservoir.df_daily[name] - subtract

            legend_studies.append((report_name, line_style))
            ts = TimeSeries(
                df=reservoir.df_daily,
                col=name,
                color=color,
                linestyle=line_style,
                do_stack=False,
                linewidth=linewidth
            )
            time_series.insert(0, ts)
        return legend_studies

def previous_month_path(path: Path) -> Path:
    """
    Takes a path like: /.../2026/APR26
    Returns:          /.../2026/MAR26

    Handles year rollover: JAN26 → DEC25
    """
    path_str = str(path)

    # Match year and month code (e.g. 2026/APR26), ignoring an optional _SUFFIX such as _MIN
    match = re.search(r'/(\d{4})/([A-Z]{3}\d{2})(?:_.*)?$', path_str)
    if not match:
        raise ValueError(f"Could not find month-year pattern in path: {path}")
    year_str = match.group(1)
    month_code = match.group(2)  # e.g. APR26

    # Parse to datetime
    dt = datetime.strptime(month_code, '%b%y')
    dt = dt.replace(year=int(year_str))

    # Go to previous month
    if dt.month == 1:
        prev_dt = dt.replace(year=dt.year - 1, month=12, day=1)
    else:
        prev_dt = dt.replace(month=dt.month - 1, day=1)

    # Format back to APR26 style
    new_month_code = prev_dt.strftime('%b%y').upper()

    # Replace in the original path
    new_path_str = re.sub(r'/(\d{4})/[A-Z]{3}\d{2}$',
                          f'/{prev_dt.year}/{new_month_code}',
                          path_str)

    return Path(new_path_str)

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    # years = [2026]
    # download_usbr_24mo_reports(years=years)

    ReservoirsBig3( notebook_frame=notebook_frame)

    notebook_frame.Show()
    app.MainLoop()