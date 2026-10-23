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
import pandas as pd

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

        self.storage_chart = None
        self.powell_storage_time_series = None
        self.powell_storage_projection_time_series = None
        self.flaming_gorge_storage_time_series = None
        self.flaming_gorge_storage_projection_time_series = None
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
        ax = self.storage_chart.ax
        today = datetime.date.today()
        ReservoirsBig3.add_two_series_delta_annotation(ax,
                                                       self.powell_storage_time_series,
                                                       self.powell_storage_projection_time_series,
                                                       color='black',
                                                       text_offset=-0.02,
                                                       date=today)

        ReservoirsBig3.add_delta_annotation(ax, self.powell_storage_time_series,
                               start_date="2026-09-15", end_date=today,
                                            # color='black',
                                            linewidth=3.0,
                                            annotation_side='right')

        ReservoirsBig3.add_delta_annotation(ax, self.flaming_gorge_storage_time_series,
                               start_date="2026-04-20", end_date=today,
                                            # color='black',
                                            linewidth=3.0,
                                            annotation_side='right')


        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if  reservoir.name == 'Lake Powell':
                    crit_points = getattr(reservoir, 'critical_elevations_feet', [])
                    if crit_points:
                        if hasattr(self.storage_chart, 'ax') and self.storage_chart.ax is not None:
                            min_capacity = 0
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
                    self.powell_storage_time_series = (reservoir.df_daily, ub.POWELL_ABOVE_3490, 'dodgerblue')
                    time_series.append(self.powell_storage_time_series)
                    legend_variables.append((ub.POWELL_ABOVE_3490, 'dodgerblue'))
                    legend_studies = ReservoirsBig3.add_report_series(reservoir, time_series, 'End Of Month Storage', "#a0a0ff",
                                                     subtract=reservoir.power_head_min_af, is_storage=True, linewidth=2.5)
                    self.powell_storage_projection_time_series = time_series[0]
                elif reservoir.name == 'Flaming Gorge':
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))
                    legend_variables.append(( ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))
                    ReservoirsBig3.add_report_series(reservoir, time_series, 'Live Storage', "#50a050",
                                                     subtract=reservoir.power_head_min_af, is_storage=True, linewidth=2.5)
                    self.flaming_gorge_storage_time_series = time_series[0]

        self.storage_chart = LineChart(
            time_series,
            title=f'Colorado River {self.name} 24 Month={self.report_name} - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = True,
            show_right_labels = True,
            percentage=0.50,
            y_min = 750_000,
            y_max = 3_000_000,
            compact_legend=True,
            legend_variables=legend_variables,
            legend_studies=legend_studies
        )
        self.storage_chart.set_start_date(graph_start_date)
        self.storage_chart.set_end_date(graph_end_date)
        self.charts.append(self.storage_chart)

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
            show_x_labels=False,
            percentage=0.20,
            y_units='CFS',
            y_max=30_000,
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
    def add_two_series_delta_annotation(
            ax,
            ts1,
            ts2,
            date,
            column1: str = None,
            column2: str = None,
            color: str = None,
            linestyle: str = "--",
            linewidth: float = 1.5,
            text_offset: float = 0.0,  # now a vertical offset (fraction of y-span)
            annotation_side: str = "right",  # "right" or "left"
    ):
        """
        Draw a vertical dashed line (with solid end-caps) at `date` between the
        values of two different time series on that date, and annotate the delta.

        text_offset : float
            Vertical offset as a fraction of the current y-axis span.
            Positive moves the text up, negative moves it down.

        annotation_side:
            "right" → text to the right of the vertical line, left-justified
            "left"  → text to the left of the vertical line, right-justified

        Delta = value(ts1) - value(ts2).
        """
        if not isinstance(ts1, TimeSeries):
            ts1 = TimeSeries.from_tuple(ts1)
        if not isinstance(ts2, TimeSeries):
            ts2 = TimeSeries.from_tuple(ts2)

        col1 = column1 or ts1.col
        col2 = column2 or ts2.col
        line_color = color or ts1.color

        def prepare(ts, col, name):
            if ts.df is None or ts.df.empty or col not in ts.df.columns:
                print(f"[add_two_series_delta_annotation] {name}: missing DataFrame or column '{col}' → returning None")
                return None
            df = ts.df.copy()
            if "Date" not in df.columns:
                print(f"[add_two_series_delta_annotation] {name}: no 'Date' column → returning None")
                return None
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date").sort_index()
            return df

        df1 = prepare(ts1, col1, "ts1")
        df2 = prepare(ts2, col2, "ts2")
        if df1 is None or df2 is None:
            print(
                "[add_two_series_delta_annotation] Could not prepare both series → returning None (no annotation drawn)")
            return

        dt = pd.Timestamp(date)

        def nearest_value(df, col, label):
            if df.empty:
                print(f"[add_two_series_delta_annotation] {label}: DataFrame is empty → returning None")
                return None

            idx = df.index.get_indexer([dt], method="nearest")[0]
            if idx == -1:
                print(f"[add_two_series_delta_annotation] {label}: no nearest index for {dt.date()} → returning None")
                return None

            candidates = list(range(idx, -1, -1)) + list(range(idx + 1, len(df)))
            for i in candidates:
                val = df.iloc[i][col]
                if pd.notna(val):
                    try:
                        numeric = float(val)
                        matched_date = df.index[i]
                        if matched_date.date() != dt.date():
                            print(f"[add_two_series_delta_annotation] WARNING {label}: "
                                  f"requested {dt.date()} but using {matched_date.date()} "
                                  f"(value={numeric})")
                        return numeric
                    except (TypeError, ValueError):
                        continue

            print(
                f"[add_two_series_delta_annotation] {label}: no non-NaN value found near {dt.date()} → returning None")
            return None

        v1 = nearest_value(df1, col1, "ts1")
        v2 = nearest_value(df2, col2, "ts2")
        if v1 is None or v2 is None:
            print(
                "[add_two_series_delta_annotation] Could not obtain both values → returning None (no annotation drawn)")
            return

        delta = v1 - v2

        # Vertical dashed line
        ax.plot(
            [dt, dt],
            [v1, v2],
            color=line_color,
            linestyle=linestyle,
            linewidth=linewidth,
            zorder=6,
        )

        # Short solid end-caps (same color)
        x_span_days = (pd.Timestamp(ax.get_xlim()[1]) - pd.Timestamp(ax.get_xlim()[0])).days
        cap_width_days = max(1, int(x_span_days * 0.008))
        cap = pd.Timedelta(days=cap_width_days)

        ax.plot([dt - cap, dt + cap], [v1, v1],
                color=line_color, linestyle="-", linewidth=linewidth,
                solid_capstyle="butt", zorder=6)
        ax.plot([dt - cap, dt + cap], [v2, v2],
                color=line_color, linestyle="-", linewidth=linewidth,
                solid_capstyle="butt", zorder=6)

        # Annotation with vertical offset
        mid_y = (v1 + v2) / 2.0
        y0, y1 = ax.get_ylim()
        y_span = y1 - y0
        y_offset = y_span * text_offset

        sign = "+" if delta >= 0 else ""
        label = f"{sign}{delta:,.1f}"

        x_clearance = pd.Timedelta(days=max(1, int(x_span_days * 0.008)))

        if annotation_side.lower() == "left":
            xytext = (dt - x_clearance, mid_y + y_offset)
            ha = "right"
        else:
            xytext = (dt + x_clearance, mid_y + y_offset)
            ha = "left"

        ax.annotate(
            label,
            xy=(dt, mid_y),
            xytext=xytext,
            textcoords="data",
            ha=ha,
            va="center",
            fontsize=9,
            fontweight="bold",
            color=line_color,
            zorder=7,
        )

    @staticmethod
    def add_delta_annotation(
            ax,
            ts,
            start_date,
            end_date,
            column: str = None,
            color: str = None,
            linestyle: str = "--",
            linewidth: float = 1.5,
            text_offset: float = 0.0,  # now a vertical offset (fraction of y-span)
            annotation_side: str = "right",  # "right" or "left"
    ):
        """
        Draw a vertical dashed line at end_date between the values of the series
        on start_date and end_date, with solid end-caps in the same color,
        and annotate the delta.

        text_offset : float
            Vertical offset as a fraction of the current y-axis span.
            Positive moves the text up, negative moves it down.
            Use this to keep multiple annotations from overlapping.

        annotation_side:
            "right" → text to the right of the vertical line, left-justified
            "left"  → text to the left of the vertical line, right-justified
        """
        if not isinstance(ts, TimeSeries):
            ts = TimeSeries.from_tuple(ts)

        col = column or ts.col
        line_color = color or ts.color

        if ts.df is None or ts.df.empty or col not in ts.df.columns:
            print(f"[add_delta_annotation] Missing DataFrame or column '{col}' → returning None")
            return

        df = ts.df.copy()
        if "Date" not in df.columns:
            print("[add_delta_annotation] No 'Date' column → returning None")
            return
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        def nearest_value(dt, label="value"):
            if df.empty:
                print(f"[add_delta_annotation] {label}: DataFrame is empty → returning None")
                return None, None

            idx = df.index.get_indexer([dt], method="nearest")[0]
            if idx == -1:
                print(f"[add_delta_annotation] {label}: no nearest index for {dt.date()} → returning None")
                return None, None

            candidates = list(range(idx, -1, -1)) + list(range(idx + 1, len(df)))
            for i in candidates:
                val = df.iloc[i][col]
                if pd.notna(val):
                    try:
                        numeric = float(val)
                        matched_date = df.index[i]
                        if matched_date.date() != dt.date():
                            print(f"[add_delta_annotation] WARNING {label}: "
                                  f"requested {dt.date()} but using {matched_date.date()} "
                                  f"(value={numeric})")
                        return numeric, matched_date
                    except (TypeError, ValueError):
                        continue

            print(f"[add_delta_annotation] {label}: no non-NaN value found near {dt.date()} → returning None")
            return None, None

        v_start, matched_start = nearest_value(start, label="start")
        v_end, matched_end = nearest_value(end, label="end")
        if v_start is None or v_end is None:
            print(
                "[add_delta_annotation] Could not obtain both start and end values → returning None (no annotation drawn)")
            return

        delta = v_end - v_start
        vertical_x = end

        # Vertical dashed line
        ax.plot(
            [vertical_x, vertical_x],
            [v_start, v_end],
            color=line_color,
            linestyle=linestyle,
            linewidth=linewidth,
            zorder=6,
        )

        # Solid end-cap from actual start time/value to the vertical line
        ax.plot(
            [matched_start, vertical_x],
            [v_start, v_start],
            color=line_color,
            linestyle="-",
            linewidth=linewidth,
            solid_capstyle="butt",
            zorder=6,
        )

        # Short solid cap at the end value
        x_span_days = (pd.Timestamp(ax.get_xlim()[1]) - pd.Timestamp(ax.get_xlim()[0])).days
        cap_width_days = max(1, int(x_span_days * 0.008))
        cap = pd.Timedelta(days=cap_width_days)

        ax.plot(
            [vertical_x - cap, vertical_x + cap],
            [v_end, v_end],
            color=line_color,
            linestyle="-",
            linewidth=linewidth,
            solid_capstyle="butt",
            zorder=6,
        )

        # Annotation with vertical offset
        mid_y = (v_start + v_end) / 2.0
        y0, y1 = ax.get_ylim()
        y_span = y1 - y0
        y_offset = y_span * text_offset  # positive = up, negative = down

        sign = "+" if delta >= 0 else ""
        label = f"{sign}{delta:,.1f}"

        # Small fixed horizontal clearance so text doesn't sit on the line
        x_clearance = pd.Timedelta(days=max(1, int(x_span_days * 0.008)))

        if annotation_side.lower() == "left":
            xytext = (vertical_x - x_clearance, mid_y + y_offset)
            ha = "right"
        else:  # "right"
            xytext = (vertical_x + x_clearance, mid_y + y_offset)
            ha = "left"

        ax.annotate(
            label,
            xy=(vertical_x, mid_y),
            xytext=xytext,
            textcoords="data",
            ha=ha,
            va="center",
            fontsize=9,
            fontweight="bold",
            color=line_color,
            zorder=7,
        )

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