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
import wx
import colorado.ub as ub
from chart.chart import Chart
from datetime import date
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.line_chart import LineChart
import colorado.allb as all_b
from reservoirs.green_mountain import GreenMountain
from reservoirs.lake_granby import LakeGranby
from reservoirs.dillon import Dillon
from reservoirs.wolford import Wolford
from reservoirs.williams_fork import WilliamsFork

# Northern Water Reservoirs and Lakes
#   Boulder Lake
#   Carter Lake
#   Flatiron Reservoir
#   Grand Lake
#   Green Mountain Reservoir
#   Horsetooth Reservoir
#   Lake Estes
#   Lake Granby
#   Mary's Lake
#   Pinewood Reservoir
#   Shadow Mountain Reservoir
#   Willow Creek Reservoir
# Tunnels
#   Adans
#   Farr/Grand Pump/Canal
#   Moffat
#   Roberts
#   Gumlick
#   Vasquez
#   Dille
#   Hansen
#   North Poudre

# Arkansas Tunnels
#   Homestake
#   Boustead
#   Busk Ivanhoe
#   Twin Lakes

arrow_fg = wx.Colour(150, 150, 150)

# ====================== GIF SETTINGS ======================
GIF_FRAME_DELAY_MS = 750
GIF_LOOP_ENABLED = False

# ==================== MAIN FRAME ====================

class FrontRange(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        reports = ChartFrame.find_directories_with_file('data/USBR_24Month_Reports', 'Lake_Powell.csv')
        self.line_chart = None
        self.inflow_outflow_chart = None
        self.version = 0.1

        self.maps:List[str] = [
            # DWR - All TMD's
            # https://drive.google.com/drive/folders/1S1372jZGuZKswUI3Jbf0QtXHpZkW8u-e
            'https://drive.google.com/file/d/1cOEzBGVSAU7MyBlx92ZutKew6DtHBB5U/view'
            # Northern Water
            'https://www.northernwater.org/getmedia/3c15e504-54bf-4b2a-abd9-48e881e808d0/CBT-Project-Map.pdf'
            # Denver Water
            'https://www.denverwater.org/sites/default/files/2017-05/map-collection-system.pdf',
            # Fryark
            'https://www.roaringfork.org/media/1299/map-of-fryingpan-arkansas-project.pdf',
            'https://www.secwcd.org/content/fryingpan-arkansas-project-system-map',
        ]

        lake_granby = LakeGranby()
        dillon = Dillon()
        green_mountain = GreenMountain()
        williams_fork = WilliamsFork()
        wolford = Wolford()

        reservoirs = [
            lake_granby,
            dillon,
            green_mountain,
            williams_fork,
            wolford,
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=reports, page_name='APR26 24-Month')
        self.right_axis_annotations()

    def right_axis_annotations(self):
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                pass

    def load_charts(self):
        graph_end_date = date.today()
        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reservoirs:
                if reservoir.name == 'Lake Granby':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkred'))
                elif reservoir.name == 'Dillon':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'royalblue'))
                elif reservoir.name == 'Green Mountain':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'darkgreen'))
                elif reservoir.name == 'Wolford':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'gold'))
                elif reservoir.name == 'Williams Fork':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.STORAGE, 'purple'))

        today = datetime.today().date()
        self.line_chart = LineChart(
            time_series,
            title=f'Front Range - {Chart.month_to_short_name(today.month)} ' \
                f'{today.day}, {today.year}  v{self.version}',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date.month,
            show_x_labels = False,
            y_units='TAF',
        )
        self.line_chart.set_end_date(graph_end_date)
        self.charts.append(self.line_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Granby':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.RELEASE, 'darkred'))
                elif reservoir.name == 'Dillon':
                    pass
                elif reservoir.name == 'Green Mountain':
                    time_series.append((reservoir.df_daily, reservoir.name+'.'+all_b.RELEASE, 'green'))
                elif reservoir.name == 'Wolford':
                    pass
                elif reservoir.name == 'Williams Fork':
                    pass

        self.inflow_outflow_chart = LineChart(
            time_series,
            title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date.month,
            show_x_labels = False,
            percentage=0.2,
            # y_max=18000,
            y_units='CFS',
        )
        self.inflow_outflow_chart.set_end_date(graph_end_date)
        self.charts.append(self.inflow_outflow_chart)

        time_series = []
        for reservoirs in self.reservoir_lists:
            for reservoir in reversed(reservoirs):
                if reservoir.name == 'Lake Granby':
                    time_series.append((reservoir.df_daily, ub.CDSS_CO_ADAMS_TUNNEL, 'darkred'))
                elif reservoir.name == 'Dillon':
                    time_series.append((reservoir.df_daily, ub.CDSS_CO_MOFFAT_TUNNEL, 'royalblue'))
                    time_series.append((reservoir.df_daily, ub.CDSS_CO_ROBERTS_TUNNEL, 'dodgerblue'))
                elif reservoir.name == 'Green Mountain':
                    pass
        line_chart = LineChart(
            time_series, title='',
            start_date=self.start_nav.current_date, current_date=self.current_time_from_usbr, end_date=self.end_nav.current_date,
            percentage=0.2,
            y_units='CFS',
            # y_max=700
        )
        line_chart.set_end_date(graph_end_date)
        self.charts.append(line_chart)


def previous_month_path(path: Path) -> Path:
    """
    Takes a path like: /.../2026/APR26
    Returns:          /.../2026/MAR26

    Handles year rollover: JAN26 → DEC25
    """
    path_str = str(path)

    # Match the year and month code (e.g. 2026/APR26)
    import re
    match = re.search(r'/(\d{4})/([A-Z]{3}\d{2})$', path_str)
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

