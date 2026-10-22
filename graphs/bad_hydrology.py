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
#from datetime import date
import wx
import colorado.ub as ub
from sheet import sheet
from graphs.chart_frame import ChartFrame, NotebookFrame
from chart.multi_bar_chart import MultiBarChart, BarGroup, BarSeries
from colorado.river_war import RiverWar
import colorado.allb as all_b
import colorado.lb as lb
from reservoirs.lake_powell import LakePowell
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_havasu import LakeHavasu
from typing import Optional
from api import df_utils
import pandas as pd

class BadHydrology(ChartFrame):
    def __init__(self, notebook_frame: NotebookFrame):
        self.name = 'Bad Hydrology'
        self.report_name, reports_latest = ChartFrame.get_latest_reports()

        self.df_mean = None
        self.df_powell = None
        self.start_year = 1991
        self.end_year = 2026
        self.current_year = self.start_year
        self.timer = None
        self.animation_interval = 1000
        self.version = 0.4
        self.play_btn = None
        self.year_slider = None
        self.toolbar_status = None
        self.range_ann = None
        self.year_prev = 0
        self.moving_average_years = 20
        self.moving_average_label = f'Lee Ferry {self.moving_average_years} yr moving avg'

        self.supply_demand_chart:Optional[MultiBarChart] = None
        self.lees_ferry_chart:Optional[MultiBarChart] = None
        self.storage_chart:Optional[MultiBarChart] = None

        self.lake_powell = LakePowell(upstream=[])
        self.lake_mead = LakeMead(upstream=[self.lake_powell])
        self.lake_havasu = LakeHavasu(upstream=[self.lake_powell])

        reservoirs = [
            self.lake_powell,
            self.lake_mead,
            self.lake_havasu
        ]
        super().__init__(notebook_frame, reservoir_lists=[reservoirs], reports=reports_latest, page_name=self.name)

        self.right_axis_annotations()
        self.lees_ferry_chart.enable_draggable_vline(
            callback=self.on_line_moved,
            color='black',
            initial_year=2026,
        )

    def load_charts(self):

        # ====================== NATURAL FLOW ======================
        #  river_war = self.notebook_frame.river_war
        # natural_flow_data = river_war.dataset.get('Natural Flow')

        self.df_powell = self.lake_powell.load_data_annual(start_year=self.start_year)
        sheet.usgs_annuals(self.df_powell,  '09380000', self.start_year, self.end_year,
                           month=all_b.WY,
                           title=ub.LEES_FERRY_USGS, divisor=1)

        sheet.usgs_annuals(self.df_powell,  '09382000', self.start_year, self.end_year,
                           month=all_b.WY,
                           title=ub.PARIA_RIVER_USGS, divisor=1)

        self.df_mead = self.lake_mead.load_data_annual(start_year=self.start_year)
        df_mx = sheet.read_csv('data/USBR_Reports/mx/usbr_mx_satisfaction_of_treaty.csv', sep='\s+')
        sheet.merge_annual_column(self.df_mead, df_mx, lb.MEXICO, divisor=1)

        self.df_powell = BadHydrology.expand_years(self.df_powell, 2)
        self.df_mead = BadHydrology.expand_years(self.df_mead, 2)

        for i, (report_name, dfs) in enumerate(self.lake_powell.reports.items()):
            if report_name.endswith('_MIN'):
                df, df_wy = dfs
                col_map = {
                    "Lees Ferry Gage": ub.LEES_FERRY_USGS,
                    "Regulated Inflow": all_b.INFLOW,
                    "Total Release": all_b.RELEASE,
                }
                BadHydrology.copy_columns_for_years(
                    src=df_wy,
                    dst=self.df_powell,
                    start_year=2027,
                    stop_year=2028,
                    col_map=col_map,
                )
                col_map = {
                    "End Of Month Storage": all_b.STORAGE,
                }
                BadHydrology.copy_columns_for_water_years(
                    src=df,
                    dst=self.df_powell,
                    start_year=2027,
                    stop_year=2028,
                    col_map=col_map,
                    wy_start_month=10
                )
                pass
            for i, (report_name, dfs) in enumerate(self.lake_mead.reports.items()):
                if report_name.endswith('_MIN'):
                    df, df_wy = dfs
                    col_map = {
                        "Total Release": all_b.RELEASE,
                    }
                    BadHydrology.copy_columns_for_years(
                        src=df_wy,
                        dst=self.df_mead,
                        start_year=2027,
                        stop_year=2028,
                        col_map=col_map,
                    )
                    col_map = {
                        "End Of Month Storage": all_b.STORAGE,
                    }
                    BadHydrology.copy_columns_for_water_years(
                        src=df,
                        dst=self.df_mead,
                        start_year=2027,
                        stop_year=2028,
                        col_map=col_map,
                        wy_start_month=10  # THis might be a problem
                    )
                for i, (report_name, dfs) in enumerate(self.lake_havasu.reports.items()):
                    if report_name.endswith('_MIN'):
                        df, df_wy = dfs
                        col_map = {
                            "Flow To Mexico": lb.MEXICO,
                        }
                        BadHydrology.copy_columns_for_years(
                            src=df_wy,
                            dst=self.df_mead,
                            start_year=2027,
                            stop_year=2028,
                            col_map=col_map,
                        )
        df_utils.subtract_column(self.df_mead, all_b.RELEASE, lb.MEXICO, result_column="Lower Basin")

        # ============= POWELL INFLOW, MEAD RELEASE  ==============
        powell_inflow_bar = BarGroup(
            label="Powell", series=[BarSeries(df=self.df_powell, col=all_b.INFLOW, color="royalblue", label="")]
        )
        hoover_release_bar = BarGroup(
            label = "", series = [
                BarSeries(df=self.df_mead, col="Mexico", color=lb.MX_COLOR, label="Mexico"),
                BarSeries(df=self.df_mead, col="Lower Basin", color="maroon", label="Lower Basin"),
            ]
        )

        graph_start_year = 1999
        self.supply_demand_chart = MultiBarChart(
            title=f'Colorado River {self.name}',
            percentage=0.33,
            groups=[hoover_release_bar, powell_inflow_bar],
            start_year=graph_start_year,
            end_year=2028,
            y_max=17,
            y_min=0,
            show_x_labels=True
        )
        self.charts.append(self.supply_demand_chart)

        df_utils.add_column_sum(
            self.df_powell,
            cols_to_sum=[ub.LEES_FERRY_USGS, ub.PARIA_RIVER_USGS],
            sum_column_name='Lee Ferry Compact'
        )
        df_utils.subtract_column(
            self.df_powell,
            col1='Lee Ferry Compact',  # column to subtract from
            col2=all_b.RELEASE,  # column to subtract
            result_column='Lee Ferry Overage'
        )
        sum_overage = BadHydrology.sum_lee_ferry_overage(self.df_powell,  2000, 2015, 'Lee Ferry Overage')
        df_utils.moving_average(self.df_powell, 'Lee Ferry Compact',
                                self.moving_average_label,
                                window=self.moving_average_years)
        overlay_moving_average_year = [
            (
                self.df_powell,
                self.moving_average_label,
                "goldenrod",
                {
                    "label": self.moving_average_label,
                    "linewidth": 2.5,
                    "linestyle": "-",
                    "marker": "", # "o"
                    # "markersize": 5,
                    # "markerfacecolor": 'black',
                    # "markeredgecolor": 'red',
                }
            ),
        ]
        glen_canypn__bar = BarGroup(
            label="Glen Canyon", series=[BarSeries(df=self.df_powell, col=all_b.RELEASE, color="dodgerblue", label="")]
        )
        lees_ferry_bar = BarGroup(
            label="", series=[BarSeries(df=self.df_powell, col=ub.LEES_FERRY_USGS, color="royalblue"),
                              BarSeries(df=self.df_powell, col=ub.PARIA_RIVER_USGS, color=ub.PARIA_COLOR)]
        )
        self.lees_ferry_chart = MultiBarChart(
            percentage=0.33,
            groups=[glen_canypn__bar, lees_ferry_bar],
            overlay_lines=overlay_moving_average_year,
            start_year=graph_start_year,
            end_year=2028,
            y_max=10.5,
            y_min=5,
            show_x_labels=True
        )
        self.charts.append(self.lees_ferry_chart)

        # ============= RESERVOIR STORAGE ==============

        powell_bar = BarGroup(
            label="Powell", series=[BarSeries(df=self.df_powell, col=all_b.STORAGE, color="royalblue")]
        )
        mead_bar = BarGroup(
            label="Mead",series=[BarSeries(df=self.df_mead, col=all_b.STORAGE, color="maroon")]
        )

        self.storage_chart = MultiBarChart(
            percentage=0.33,
            groups=[mead_bar, powell_bar],
            start_year=graph_start_year,
            end_year=2028,
            y_max=25.5,
            y_min=3,
            show_x_labels=False,
        )
        self.charts.append(self.storage_chart)

    @staticmethod
    def sum_lee_ferry_overage(df, start_year, end_year, column_name):
        """
        Sum the values in the 'Lee Ferry Overage' column for years
        between start_year and end_year (inclusive).

        Expects a 'Year' column.
        """
        if 'Year' not in df.columns:
            raise KeyError("DataFrame must contain a 'Year' column")
        if column_name not in df.columns:
            raise KeyError(f"Column '{column_name}' not found")

        mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
        return df.loc[mask, column_name].sum()

    @staticmethod
    def value_for_year(df, year, col, year_col='Year'):
        """Return the value in `col` for the given `year`, or None if not found."""
        if df.empty or year_col not in df.columns or col not in df.columns:
            return None
        match = df.loc[pd.to_numeric(df[year_col], errors='coerce') == year, col]
        if match.empty:
            return None
        return pd.to_numeric(match.iloc[0], errors='coerce')

    @staticmethod
    def compute_iiic(df, column_name, start_year, end_year, constant=7.5, moving_average_window=10):
        """
        Sum the values in `column_name` for rows whose Year is between
        start_year and end_year (inclusive), divide by 2, then add `constant`.

        Expects a 'Year' column.
        """
        if 'Year' not in df.columns:
            raise KeyError("DataFrame must contain a 'Year' column")

        mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
        total = df.loc[mask, column_name].sum()

        return (((total / moving_average_window)  / 1_000_000) / 2.0) + constant

    @staticmethod
    def sum_minus_constant(df, start_year, end_year, col, constant):
        """Sum of (value - constant) for rows where Year is in [start_year, end_year]."""
        mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
        values = pd.to_numeric(df.loc[mask, col], errors='coerce').dropna()
        return (values - constant).sum()

    def right_axis_annotations(self):

        # Supply Demand Annotations
        #
        demand_floor = 8_250_000

        ax = self.supply_demand_chart.ax
        ChartFrame.annotate_level(ax, demand_floor/1_000_000, f'{demand_floor/1_000_000:.2f}',
                                  'maroon', draw_text=True, draw_line=True,
                                  left_of_axis=False)
        ChartFrame.annotate_level(ax, 1.5, f'{1.5:.2f}',
                                  lb.MX_COLOR, draw_text=True, draw_line=True,
                                  left_of_axis=False)

        self.supply_demand_chart.annotate_value(
            ax,
            year=2003,
            label="QSA",
            color="maroon",
            position="above_top",
            draw_line=False,
            draw_outline=False
        )
        self.supply_demand_chart.annotate_value(
            ax,
            year=2007,
            label="2007 ROD",
            color="black",
            position="above_top",
            draw_line=False,
            draw_outline=False
        )

        self.supply_demand_chart.annotate_value(
            ax,
            year=2026,
            label="2026 ROD",
            color="black",
            position="above_top",
            draw_line=False,
            draw_outline=False
        )

        overuse = BadHydrology.sum_minus_constant(self.df_mead, 1999, 2004, all_b.RELEASE, demand_floor) / 1_000_000
        self.supply_demand_chart.annotate_range(
            ax,
            start_year=1999,
            end_year=2004,
            label=f"Lower Basin Overuse\n{-overuse:.2f}",
            line_color="black",
            text_color="red",
            position="below_top",
        )

        overuse = BadHydrology.sum_minus_constant(self.df_mead, 2005, 2005, all_b.RELEASE, demand_floor) / 1_000_000
        self.supply_demand_chart.annotate_range(
            ax,
            start_year=2005,
            end_year=2005,
            label=f"2005\n{-overuse:.2f}",
            line_color="black",
            text_color="darkgreen",
            position="below_top",
        )

        overuse = BadHydrology.sum_minus_constant(self.df_mead, 2006, 2019, all_b.RELEASE, demand_floor) / 1_000_000
        self.supply_demand_chart.annotate_range(
            ax,
            start_year=2006,
            end_year=2019,
            label=f"Overuse\n{-overuse:.2f}",
            line_color="black",
            text_color="red",
            position="below_top",
        )

        overuse = BadHydrology.sum_minus_constant(self.df_mead, 2020, 2026, all_b.RELEASE, demand_floor) / 1_000_000
        self.supply_demand_chart.annotate_range(
            ax,
            start_year=2020,
            end_year=2026,
            label=f"Conservation\n{-overuse:.2f}",
            line_color="black",
            text_color="darkgreen",
            position="below_top",
        )
        legend = ax.get_legend()
        if legend is not None:
            # Option A – named location
            # legend.set_loc('upper left')

            # Option B – precise position (axes fraction)
            legend.set_bbox_to_anchor((0.85, 0.88))

        # Moving average year annotations
        #
        ax = self.lees_ferry_chart.ax
        ChartFrame.annotate_level(ax, 7.5, '7.5',
                                      'dodgerblue', draw_text=True, draw_line=True,
                                      left_of_axis=False)
        ChartFrame.annotate_level(ax, 8.25, '8.25',
                                      'red', draw_text=True, draw_line=True,
                                      left_of_axis=False)
        year = 2026
        avg = BadHydrology.value_for_year(self.df_powell, year, self.moving_average_label)
        self.range_ann  = self.storage_chart.annotate_range(
            ax,
            start_year=2017,
            end_year=2026,
            label='',
            #label=f"{self.moving_average_years} Year Average\n{year} {avg/1_000_000:.3f}",
            line_color="black",
            text_color="royalblue",
            position="below_top",
        )
        legend = ax.get_legend()
        if legend is not None:
            # Option A – named location
            # legend.set_loc('upper left')

            # Option B – precise position (axes fraction)
            legend.set_bbox_to_anchor((0.10, 0.88))

        self.on_line_moved(year)

        # Storage annotations
        #
        ax = self.storage_chart.ax
        self.storage_chart.annotate_value(
            ax,
            year=2004,
            label="Letters",
            color="royalblue",
            position="below_bottom",
            draw_line=False,
            draw_outline=False
        )
        self.storage_chart.annotate_value(
            ax,
            year=2018,
            label="DCP",
            color="black",
            position="below_bottom",
            draw_line=False,
            draw_outline=False
        )
        self.storage_chart.annotate_value(
            ax,
            year=2024,
            label="2024 Interim ROD",
            color="black",
            position="below_bottom",
            draw_line=False,
            draw_outline=False
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=1999,
            end_year=2004,
            label="The Fall",
            line_color="black",
            text_color="red",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2004,
            end_year=2011,
            label="Surplus",
            line_color="black",
            text_color="green",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2011,
            end_year=2014,
            label="Deficit",
            line_color="black",
            text_color="red",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2014,
            end_year=2019,
            label="Sweet Spot Gaming",
            line_color="black",
            text_color="darkgoldenrod",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2019,
            end_year=2022,
            label="Deficit",
            line_color="black",
            text_color="red",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2022,
            end_year=2024,
            label="Surplus",
            line_color="black",
            text_color="green",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2024,
            end_year=2026,
            label="Deficit",
            line_color="black",
            text_color="red",
            position="below_top",
            show_delta=True
        )
        self.storage_chart.annotate_range(
            ax,
            start_year=2026,
            end_year=2028,
            label="Future",
            line_color="black",
            text_color="red",
            position="below_top",
            show_delta=True
        )

    def on_line_moved(self, year):
        if self.range_ann is None:
            return

        if year == self.year_prev:
            return
        self.year_prev = year
        # Example: keep a fixed-width window ending at the dragged year
        start = year - (self.moving_average_years-1)
        end = year
        if start not in self.storage_chart.year_to_idx or end not in self.storage_chart.year_to_idx:
            return

        iii_c =  BadHydrology.compute_iiic(self.df_mead, lb.MEXICO, start, end,
                                           constant=7.5, moving_average_window=self.moving_average_years)

        x1 = self.storage_chart.year_to_idx[start]
        x2 = self.storage_chart.year_to_idx[end]
        y_line = self.range_ann['y_line']
        y_text = self.range_ann['y_text']
        cap = self.range_ann['cap']

        # Move the horizontal line
        self.range_ann['line'].set_xdata([x1, x2])
        self.range_ann['line'].set_ydata([y_line, y_line])

        # Move the caps
        self.range_ann['cap1'].set_xdata([x1, x1])
        self.range_ann['cap1'].set_ydata([y_line - cap, y_line + cap])
        self.range_ann['cap2'].set_xdata([x2, x2])
        self.range_ann['cap2'].set_ydata([y_line - cap, y_line + cap])

        # Move and update the text
        mid = (x1 + x2) / 2
        avg = BadHydrology.value_for_year(self.df_powell, year, self.moving_average_label) / 1_000_000
        label = f"{self.moving_average_years} Year Average\n{year} "
        if avg is not None:
            if avg < 7.5:
                label += f"{avg:.3f} - {7.5:.3f} = {avg-7.5:.3f}"
            else:
                label += f"{avg:.3f} - {iii_c:.3f} = {avg-iii_c:.3f}"
        else:
            label = f"{self.moving_average_years} Year Average\n{year}"
        self.range_ann['text'].set_position((mid, y_text))
        self.range_ann['text'].set_text(label)

        self.storage_chart.fig.canvas.draw_idle()

    @staticmethod
    def copy_columns_for_water_years(src, dst, start_year, stop_year, col_map,
                                     wy_start_month, date_col='Date', year_col='Year'):
        """
        Copy end-of-water-year values from monthly src into yearly dst.

        src date column format: "Mon Year"  (e.g. "Sep 2024", "Dec 2023")
        wy_start_month: month the water year begins (1=Jan … 12=Dec)

        For a water year labeled Y:
          - start month 10 → uses September of Y
          - start month 1  → uses December of Y
          - generally: last month of the water year in calendar year Y

        Modifies dst in place and returns it.
        """
        if src.empty or dst.empty:
            return dst

        # Month abbreviation → number
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

        # Determine the ending month of the water year
        end_month = 12 if wy_start_month == 1 else wy_start_month - 1

        # Parse src dates
        src = src.copy()
        parts = src[date_col].astype(str).str.strip().str.split(n=1, expand=True)
        src['_mon'] = parts[0].str.lower().map(month_map)
        src['_yr'] = pd.to_numeric(parts[1], errors='coerce')

        # Keep only the end-of-water-year rows
        src_eow = src[(src['_mon'] == end_month) & src['_yr'].notna()].copy()
        src_eow = src_eow.set_index('_yr')

        # Destination years in range
        dst_year = pd.to_numeric(dst[year_col], errors='coerce')
        dst_mask = (dst_year >= start_year) & (dst_year <= stop_year)
        dst_index = dst.loc[dst_mask, year_col]

        for src_col, dst_col in col_map.items():
            if src_col not in src_eow.columns:
                continue
            # Align on the water-year label and write into dst
            aligned = src_eow[src_col].reindex(dst_index)
            dst.loc[dst_mask, dst_col] = aligned.values

        return dst

    @staticmethod
    def copy_columns_for_years(src, dst, start_year, stop_year, col_map, year_col='Year'):
        """
        Copy columns from src to dst for years in [start_year, stop_year].
        Modifies dst in place and also returns it.
        """
        if src.empty or dst.empty:
            return dst

        # Work on numeric Year without copying the whole frames
        src_year = pd.to_numeric(src[year_col], errors='coerce')
        dst_year = pd.to_numeric(dst[year_col], errors='coerce')

        src_mask = (src_year >= start_year) & (src_year <= stop_year)
        dst_mask = (dst_year >= start_year) & (dst_year <= stop_year)

        src_subset = src.loc[src_mask].set_index(year_col)
        dst_index = dst.loc[dst_mask, year_col]

        for src_col, dst_col in col_map.items():
            if src_col not in src_subset.columns:
                continue
            # Align on Year and write directly into the original dst
            aligned = src_subset[src_col].reindex(dst_index)
            dst.loc[dst_mask, dst_col] = aligned.values

        return dst

    @staticmethod
    def expand_years(df, n_years, year_col='Year'):
        """
        Return a new DataFrame with n_years additional rows appended.
        New years continue from the last existing year.
        All other columns are NaN for the new rows.
        """
        if df.empty or year_col not in df.columns:
            return df.copy()

        last_year = int(pd.to_numeric(df[year_col], errors='coerce').max())
        new_years = range(last_year + 1, last_year + 1 + n_years)

        # Build the extra rows (only the year column is filled)
        extra = pd.DataFrame({year_col: list(new_years)})

        # Align columns and concatenate
        return pd.concat([df, extra], ignore_index=True)

if __name__ == "__main__":
    app = wx.App(False)

    river_war = RiverWar()
    notebook_frame = NotebookFrame([], river_war)

    BadHydrology(notebook_frame=notebook_frame)

    notebook_frame.Show()
    app.MainLoop()