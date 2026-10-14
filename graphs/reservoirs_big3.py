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
from datetime import datetime
import re
import wx
from colorado.river_war import RiverWar
from chart.chart import Chart
from datetime import date
import api.df_utils as df_utils
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import colorado.lb as lb
import colorado.ub as ub
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from pdf_reader.pdf_reader import download_usbr_24mo_reports
# from source.crbfc import request_esplist, request_forecast

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class ReservoirsBig3(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Big 3 Reservoirs'
        #reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')
        reports_min = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv', suffix="_MIN")

        flaming_gorge = FlamingGorge()
        lake_powell = LakePowell(upstream=[flaming_gorge])
        lake_mead = LakeMead(upstream=[lake_powell])
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.3

        reservoirs = [
            flaming_gorge,
            lake_powell,
            lake_mead,
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=reports_min, page_name=self.name)
        self.right_axis_annotations()

    @staticmethod
    def annotate_level(ax, y, feet, color, draw_text=True, left_of_axis=True, draw_line=True):
        """Draw an optional level line and label on the right y-axis.

        y is the plotted coordinate (for example acre_feet - min_capacity).
        feet is the elevation shown in the label.
        left_of_axis=True:  right-justified text just to the left of the right y-axis
        left_of_axis=False: left-justified text just to the right of the right y-axis
        """
        if draw_line:
            ax.axhline(
                y=y,
                color=color,
                linestyle='--',
                linewidth=1.5,
                alpha=0.85,
                zorder=3,
            )

        if not draw_text:
            return

        if left_of_axis:
            x, ha = 0.995, 'right'
        else:
            x, ha = 1.005, 'left'

        ax.text(
            x, y,
            str(feet),
            transform=ax.get_yaxis_transform(),
            va='center',
            ha=ha,
            fontsize=10,
            color=color,
            fontweight='bold',
            clip_on=False,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                alpha=1,
                edgecolor=color,
            ),
        )

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
                                        ReservoirsBig3.annotate_level(ax, 0.0, str(round(item[1])),
                                                                      'royalblue', draw_text=True, draw_line=True,
                                                                      left_of_axis=True)

                            elevation_3510_ft = getattr(reservoir, 'power_head_target_feet', 0)
                            elevation_3510_af = getattr(reservoir, 'power_head_target_af', 0)
                            if elevation_3510_af:
                                ax = self.line_chart.ax
                                ReservoirsBig3.annotate_level(ax, elevation_3510_af-min_capacity, elevation_3510_ft,
                                                              'royalblue', draw_text=True, left_of_axis=True)

                elif  reservoir.name == 'Lake Mead':
                    if hasattr(self.line_chart, 'ax') and self.line_chart.ax is not None:
                        ax = self.line_chart.ax
                        mead_consult_feet = getattr(reservoir, 'mead_consult_feet', 0)
                        mead_consult_af = getattr(reservoir, 'mead_consult_af', 0)
                        min_capacity = getattr(reservoir, 'power_head_min_af', 0)
                        ReservoirsBig3.annotate_level(ax, mead_consult_af - min_capacity, mead_consult_feet,
                                                      'darkred', draw_text=True, left_of_axis=False)

                        crit_points = getattr(reservoir, 'critical_elevations_feet', [])
                        if crit_points:
                            for item in crit_points:
                                if isinstance(item, (list, tuple)) and len(item) >= 3:
                                    if item[0] == 'Safe Power Head':
                                        ReservoirsBig3.annotate_level(ax, 0.0, f"{item[1]}'",'darkred',
                                                                      draw_text=True, draw_line=False, left_of_axis=False)
                                    else:
                                        cap_maf = (item[2] - min_capacity)
                                        elevation_ft = item[1]
                                        ReservoirsBig3.annotate_level(ax, cap_maf, elevation_ft,
                                                                      'darkred', draw_text=True, left_of_axis=False)

    def load_charts(self):
        do_adjustment = False
        powell_df = None
        fg_df = None
        start_mod_date = date(2026, 5, 1)
        end_powell_mod_date = date(2026, 9, 30)
        end_fg_mod_date = date(2027, 5, 1)
        graph_end_date = date(2027, 5, 1)
        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Lake Powell':
                    powell_df = reservoir.df_daily
                    if do_adjustment:
                        df_utils.add_cumulative_daily_delta(powell_df, 'Cut Powell Release', start_mod_date, end_powell_mod_date, 1_480_000)
                        reservoir.df_daily[ub.POWELL_MOST] = reservoir.df_daily[ub.POWELL_MOST] + powell_df['Cut Powell Release']
                        reservoir.df_daily[ub.POWELL_MOST] = reservoir.df_daily[ub.POWELL_MOST] + fg_df['Flaming Gorge DROA']
                    time_series.append((reservoir.df_daily, ub.POWELL_MOST, '#a0a0ff', 'solid'))
                    time_series.append((reservoir.df_daily, ub.POWELL_ABOVE_3490, 'dodgerblue'))
                    prev_path = previous_month_path(Path(reservoir.report_path))
                    df_24_month_prev, df_24_wy_prev = reservoir.load_24_month(prev_path, reservoir.name)
                    reservoir.get_projection(df_24_month_prev, 'Powell Most MAR26')
                    df_utils.subtract_column(reservoir.df_daily, ub.POWELL_MOST, 'Powell Most MAR26', "Diff")
                elif reservoir.name == 'Lake Mead':
                    if do_adjustment:
                        reservoir.df_daily[lb.MEAD_MOST] = reservoir.df_daily[lb.MEAD_MOST] - powell_df['Cut Powell Release']
                    time_series.append((reservoir.df_daily, lb.MEAD_MOST, '#ffa0a0', 'solid'))
                    time_series.append((reservoir.df_daily, lb.MEAD_ABOVE_950, 'darkred'))
                elif reservoir.name == 'Flaming Gorge':
                    fg_df = reservoir.df_daily
                    if do_adjustment:
                        df_utils.add_cumulative_daily_delta(fg_df, 'Flaming Gorge DROA', start_mod_date, end_fg_mod_date, 1_000_000)
                        reservoir.df_daily[ub.FLAMING_GORGE_MOST] = reservoir.df_daily[ub.FLAMING_GORGE_MOST] - fg_df['Flaming Gorge DROA']
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_MOST, '#50a050', 'solid'))
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_ABOVE_5868, 'darkgreen'))

        '''
        esp: Dict[str, str] = request_esplist()
        colorado_cisco_esp_id = esp.get('Colorado - Cisco  Nr', '')
        df_colorado_cisco = None
        if colorado_cisco_esp_id:
            df_colorado_cisco = request_forecast(colorado_cisco_esp_id, 2026)
        '''
        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'Colorado River {self.name} Storage Above Critical Elevations - May 24 Month - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = True,
            show_right_labels = True,
            # y_min = -800000,
            # y_max = 5_800_000
        )
        # self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Powell':
                    time_series.append((reservoir.df_daily, ub.POWELL_INFLOW_CFS, 'royalblue'))
                elif reservoir.name == 'Flaming Gorge':
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_INFLOW_CFS, 'darkgreen'))
                    time_series.append((reservoir.df_daily, ub.FLAMING_GORGE_RELEASE_CFS, '#50a050'))

        self.inflow_outflow_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = False,
            percentage=0.5,
            y_min=0,
            y_units='CFS',
        )
        self.inflow_outflow_chart.set_end_date(graph_end_date)
        # self.charts.append(self.inflow_outflow_chart)

        time_series = [
            (powell_df, 'Colorado River Near Cisco UT', 'royalblue'),
            (powell_df, 'Green River Near Green River, UT', 'darkgreen'),
            (powell_df, 'San Juan River Near Bluff, UT', 'goldenrod'),
            (powell_df, 'Dirty Devil Near Hanksville, UT', 'purple')
        ]
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels=False,
            percentage=0.25,
            y_units='CFS',
            # y_max=10_500,
            y_min = 0,
            stacked=True,
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)

        '''
        time_series = [
            (df_colorado_cisco, 'p50', 'royalblue', 'dotted'),
        ]
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            percentage=0.2,
            y_units='CFS',
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)
        '''
        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Powell':
                    time_series.append((reservoir.df_daily, ub.POWELL_INFLOW_CFS, 'royalblue'))
                    time_series.append((reservoir.df_daily, ub.POWELL_RELEASE_CFS, 'dodgerblue'))
                elif reservoir.name == 'Lake Mead':
                    time_series.append((reservoir.df_daily, lb.DIAMOND_CREEK, '#ffa0a0'))
                    time_series.append((reservoir.df_daily, lb.MEAD_RELEASE_CFS, 'darkred'))

        self.inflow_outflow_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            show_x_labels = False,
            percentage=0.25,
            y_min=1_000,
            y_units='CFS',
        )
        # self.inflow_outflow_chart.set_end_date(graph_end_date)
        self.charts.append(self.inflow_outflow_chart)

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