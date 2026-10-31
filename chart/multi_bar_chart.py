# Copyright (c) 2025 Ed Millard
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from matplotlib.patches import Patch
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
import pandas as pd
import numpy as np
from datetime import date
from typing import List, Optional, Tuple, Dict, Any, Literal
from dataclasses import dataclass, field
from collections import defaultdict
from chart.chart import Chart
import time


class _AnnotationSet:
    """One complete set of draggable annotation artists."""
    def __init__(self):
        self.vline = None
        self.year_label = None
        self.bar_value_texts = []
        self.side_lines = []
        self.top_total_texts = []
        self.idx = None


@dataclass
class BarSeries:
    """One stacked series inside a BarGroup."""
    df: pd.DataFrame
    col: str
    color: str
    color_overrides: Optional[List[Tuple[float, str]]] = None   # (value, color)
    label: Optional[str] = None                                 # optional display override
    hatch: Optional[str] = None
    hatch_color: Optional[str] = None
    edgecolor: Optional[str] = None
    linewidth: Optional[float] = None

@dataclass
class BarGroup:
    """A labeled group of stacked bar series."""
    label: str
    series: List[BarSeries] = field(default_factory=list)

    def rotate_left(self, n: int) -> None:
        """Move the first n elements to the end of the list."""
        if not self.series or n <= 0:
            return
        n = n % len(self.series)
        self.series = self.series[n:] + self.series[:n]

    @classmethod
    def from_tuples(cls, label: str, series_list: List[Tuple]) -> "BarGroup":
        series = []
        for item in series_list:
            if len(item) == 3:
                df, col, color = item
                series.append(BarSeries(df=df, col=col, color=color))
            elif len(item) == 4:
                df, col, color, options = item
                options = options or {}
                series.append(BarSeries(
                    df=df,
                    col=col,
                    color=color,
                    label=options.get('label'),
                    hatch=options.get('hatch'),
                    hatch_color=options.get('hatch_color'),
                    edgecolor=options.get('edgecolor'),
                    linewidth=options.get('linewidth'),
                ))
            else:
                raise ValueError(f"Unexpected series tuple length: {len(item)}")
        return cls(label=label, series=series)

class MultiBarChart(Chart):
    def __init__(self,
                 groups: List[Tuple[str, List[Tuple]] | BarGroup],
                 underlay_lines: List[Tuple[pd.DataFrame, str, str] |
                                   Tuple[pd.DataFrame, str, str, Dict[str, Any]]] | None = None,
                 overlay_lines: List[Tuple[pd.DataFrame, str, str] |
                                   Tuple[pd.DataFrame, str, str, Dict[str, Any]]] | None = None,
                 title: str = "",
                 percentage: float = 0.0,
                 start_year: Optional[int] = None,
                 end_year: Optional[int] = None,
                 y_max: Optional[float] = None,
                 y_min: Optional[float] = None,
                 x_max: Optional[float] = None,
                 x_min: Optional[float] = None,
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 show_totals: bool = False,
                 show_x_labels: bool = True,
                 y_label: str = "",
                 y_units: Literal['MAF', 'TAF', 'AF', 'FT', 'CFS'] = 'MAF',
                 y_divisor: float | None = None,
                 annotations: List[Tuple[float, float, List[Tuple[str, Tuple[pd.DataFrame, str]]]]] | None = None,
                 legend_loc: str = 'best',
                 custom_legend: Optional[List[Tuple[str, str]]] = None,
    ):
        self.year_to_idx = None
        super().__init__([], start_date, current_date, end_date, y_label=y_label, y_units=y_units, y_divisor=y_divisor, percentage=percentage)

        # Normalize groups to BarGroup (backward compatible with old tuples)
        self.groups: List[BarGroup] = []
        for item in groups:
            if isinstance(item, BarGroup):
                self.groups.append(item)
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                label, series_list = item
                self.groups.append(BarGroup.from_tuples(label, series_list))
            else:
                raise TypeError(f"groups items must be BarGroup or (label, series_list) tuple, got {type(item)}")

        self.underlay_lines = underlay_lines or []
        self.overlay_lines = overlay_lines or []
        self.show_totals = show_totals

        self.title = title
        self.show_x_labels = show_x_labels
        self.y_units = y_units
        self.y_max = y_max
        self.y_min = y_min
        self.x_max = x_max
        self.x_min = x_min

        if start_year is None:
            self.start_year = 1971
        else:
            self.start_year = start_year
        if end_year is None:
            self.end_year = 2026
        else:
            self.end_year = end_year

        self.annotations = annotations or []

        self.height_inch = 6.2
        self.width_inch = 9.0

        self.ax = None
        self.fig = None

        self.original_groups = self.groups
        self.legend_loc = legend_loc
        self.custom_legend = custom_legend

    def setup_year_xaxis(self, ax, years: List[int], max_ticks: int = 25, fontsize: int = 10):
        """Standalone reusable X-axis setup for year-based charts."""
        if not years:
            return

        n_years = len(years)

        if n_years > max_ticks * 2:
            step = max(1, n_years // max_ticks)
            tick_positions = np.arange(0, n_years, step)
            tick_labels = [f"{y % 100:02d}" for y in years[::step]]
            fontsize = max(8, fontsize - 1)
        elif n_years > max_ticks:
            step = 1
            tick_positions = np.arange(0, n_years, step)
            tick_labels = [f"{y % 100:02d}" for y in years[::step]]
            fontsize = max(9, fontsize - 0.5)
        else:
            tick_positions = np.arange(n_years)
            tick_labels = [f"{y % 100:02d}" for y in years]

        if not self.show_x_labels:
            ax.set_xticklabels([])
            ax.tick_params(axis='x', which='major', length=0)
        else:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=0, ha='center', fontsize=fontsize)
            ax.tick_params(axis='x', which='major', pad=-(fontsize * 0.05))

    def setup_yaxis(self, ax):
        """Smart Y-axis with good label visibility on small values.
        Works with BarGroup structure; operates on scaled values."""
        ax.set_ylabel(self.y_units, fontsize=11.5, fontweight='bold')
        formatter = ticker.FuncFormatter(self.scaled_formatter)
        ax.yaxis.set_major_formatter(formatter)

        if not self.groups:
            return

        # Collect all scaled values from the stacked bar groups
        all_values = []
        for group in self.groups:
            for s in group.series:
                if s.df is None or s.col not in s.df.columns:
                    continue
                vals = pd.to_numeric(s.df[s.col], errors='coerce').dropna()
                if not vals.empty:
                    all_values.extend(vals / self.y_divisor)

        if not all_values:
            return

        data_min = min(all_values)
        data_max = max(all_values)
        data_range = data_max - data_min if data_max > data_min else 1.0

        # Tick strategy (operating on scaled data)
        if data_range <= 1.0:
            major_step = 0.1
            minor_step = 0.05
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        elif data_range <= 5.0:
            major_step = 0.5
            minor_step = 0.1
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
        elif data_range <= 12.0:
            major_step = 1.0
            minor_step = 0.5
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        elif data_range <= 25.0:
            major_step = 2.0
            minor_step = 1
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        elif data_range <= 50.0:
            major_step = 5.0
            minor_step = 1.0
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        elif data_range <= 200.0:
            major_step = 10.0
            minor_step = 2.0
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        else:
            major_step = round(data_range / 8 / 10) * 10 or 100
            minor_step = major_step / 5
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))


        ax.yaxis.set_major_locator(MultipleLocator(major_step))
        ax.yaxis.set_minor_locator(MultipleLocator(minor_step))

        # Tick appearance
        ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=10)
        ax.tick_params(axis='y', which='minor', length=3, width=0.7, labelsize=8.5)

        ax.grid(True, which='major', axis='y', linestyle='-', linewidth=0.6, color='black', alpha=0.6)
        ax.grid(True, which='minor', axis='y', linestyle='--', linewidth=0.6, color='gray', alpha=0.5)

        if data_min >= 0 and self.y_min is None:
            ax.set_ylim(ymin=0)

    def create_bar_chart(self, ax):
        if not self.groups:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        ax.clear()

        group_data = []
        all_years = set()

        for group in self.groups:
            yearly = MultiBarChart._get_yearly_stacked_data(group.series)
            group_data.append((group.label, yearly))
            for year in yearly:
                all_years.add(year)

        years = list(range(self.start_year, self.end_year + 1))
        if not years:
            ax.text(0.5, 0.5, "No valid yearly data", ha='center', va='center', fontsize=14)
            return

        x = np.arange(len(years))
        self.year_to_idx = {year: idx for idx, year in enumerate(years)}

        n_groups = len(self.groups)
        # Controls the gap between years. Smaller value = bigger gap.
        group_width = 0.82 / n_groups if n_groups > 0 else 0.82
        spacing = 0.0

        max_height = 0.0

        # Underlay lines
        self._plot_lines(ax, self.underlay_lines, self.year_to_idx, zorder=1, linewidth=2.8, alpha=0.85)

        # Force a draw so bbox is valid for pixel calculations
        ax.figure.canvas.draw()

        # Pixels per data unit (for snapping)
        xlim = ax.get_xlim()
        pixel_per_data = ax.bbox.width / (xlim[1] - xlim[0]) if xlim[1] != xlim[0] else 1.0

        # Bars
        for g_idx, group in enumerate(self.groups):
            yearly_data = MultiBarChart._get_yearly_stacked_data(group.series)
            if n_groups == 1:
                bar_positions = x
            else:
                bar_positions = x - 0.4 + (g_idx + 0.5) * group_width

            for i, year in enumerate(years):
                if self.x_min is not None and year < self.x_min:
                    continue
                if self.x_max is not None and year > self.x_max:
                    continue

                bottom = 0.0
                for s_idx, (val, label, color, overrides) in enumerate(yearly_data.get(year, [])):
                    bar_color = color
                    if overrides:
                        for ov_val, ov_color in overrides:
                            if abs(val - ov_val) < 1e-6:
                                bar_color = ov_color
                                break

                    series_obj = group.series[s_idx] if s_idx < len(group.series) else None
                    height = val / self.y_divisor

                    # Snap width to whole pixels
                    raw_width = group_width - spacing
                    snapped_width = round(raw_width * pixel_per_data) / pixel_per_data

                    bar_kwargs = dict(
                        bottom=bottom,
                        color=bar_color,
                        edgecolor=bar_color,
                        linewidth=0,
                        label=None if self.custom_legend is not None else label,
                        zorder=5,
                    )

                    if series_obj is not None and series_obj.hatch:
                        bar_kwargs['hatch'] = series_obj.hatch
                        bar_kwargs['edgecolor'] = series_obj.hatch_color or bar_color

                    ax.bar(
                        bar_positions[i],
                        height,
                        width=snapped_width,
                        **bar_kwargs,
                        antialiased=False,
                    )

                    bottom += height
                    max_height = max(max_height, bottom)

                if self.show_totals:
                    total = sum(v[0] for v in yearly_data.get(year, [])) / self.y_divisor
                    if total > 1:
                        ax.text(bar_positions[i], total + 0.12, f"{total:.1f}",
                                ha='center', va='bottom', fontsize=8.5, fontweight='bold', zorder=6)

        # Overlay Lines
        self._plot_lines(ax, self.overlay_lines, self.year_to_idx, zorder=12, linewidth=3.2, alpha=0.95)

        # Y limits
        ax.set_ylim(self.y_min if self.y_min is not None else 0.0,
                    self.y_max if self.y_max is not None else max(max_height * 1.13, 0.1))

        # X limits
        x_left = x[0] - 0.55
        x_right = x[-1] + 0.55

        if self.x_min is not None:
            if self.x_min >= self.start_year - 1:
                x_left = self.year_to_idx.get(int(self.x_min), x[0]) - 0.6
            else:
                x_left = float(self.x_min)

        if self.x_max is not None:
            if self.x_max >= self.start_year - 1:
                x_right = self.year_to_idx.get(int(self.x_max), x[-1]) + 1.2
            else:
                x_right = float(self.x_max)

        ax.set_xlim(x_left, x_right)

        # X-axis labels
        self.setup_year_xaxis(ax, years, max_ticks=20, fontsize=10)

        # Legend with group names
        unique_legend = {}

        for group in self.groups:
            for s in group.series:
                clean_label = s.label or s.col.replace('_', ' ')
                display_label = f"{group.label} {clean_label}".strip()

                proxy = Rectangle((0, 0), 1, 1,
                                  fc=s.color,
                                  ec=s.edgecolor or 'white',
                                  linewidth=s.linewidth or 0.8,
                                  hatch=s.hatch)

                if display_label not in unique_legend:
                    unique_legend[display_label] = proxy

        # Legend
        if self.custom_legend is not None:
            handles = [
                Patch(facecolor=color, edgecolor='none', alpha=0.85, label=label)
                for label, color in self.custom_legend
            ]
            ax.legend(
                handles,
                [label for label, _ in self.custom_legend],
                loc=self.legend_loc,
                fontsize=9,
                frameon=True,
                ncol=1,
            )
        elif unique_legend:
            ax.legend(
                unique_legend.values(),
                unique_legend.keys(),
                loc=self.legend_loc,
                fontsize=9,
                frameon=True,
                ncol=1,
            )

        # Y-axis
        self.setup_yaxis(ax)

        ax.set_title(f"{self.title or ''}", fontsize=13.5, fontweight='bold', pad=12)

        ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=10)
        ax.tick_params(axis='y', which='minor', length=3, width=0.7, labelsize=8.5)

        # Kill any x-grid lines
        ax.xaxis.grid(False)
        for gl in ax.get_xgridlines():
            gl.set_visible(False)

        for ann in self.annotations:
            self.add_total_annotations(ann)

    def set_custom_legend(self, entries: List[Tuple[str, str]], loc: Optional[str] = None):
        """Replace the legend with a manual list of (label, color) pairs."""
        if self.ax is None:
            raise RuntimeError("Call create_figure() first")
        handles = [
            Patch(facecolor=color, edgecolor='none', alpha=0.85, label=label)
            for label, color in entries
        ]
        self.ax.legend(
            handles,
            [label for label, _ in entries],
            loc=loc or self.legend_loc,
            fontsize=9,
            frameon=True,
            ncol=1,
        )
        self.fig.canvas.draw_idle()

    def _plot_lines(self, ax, line_list, year_to_idx, zorder=10, linewidth=3.0, alpha=0.95):
        if not line_list:
            return

        series_dict = defaultdict(lambda: {'x': [], 'y': [], 'color': None, 'options': {}})

        for item in line_list:
            if len(item) == 4:
                df, col, color, options = item
            else:
                df, col, color = item
                options = {}

            yearly = MultiBarChart._get_yearly_line_data([(df, col, color)])
            for year, items in yearly.items():
                if year not in year_to_idx:
                    continue
                idx = year_to_idx[year]
                for val, default_label, c in items:
                    label = options.get('label', default_label)
                    series_dict[label]['x'].append(idx)
                    series_dict[label]['y'].append(val / self.y_divisor)
                    series_dict[label]['color'] = c or color
                    series_dict[label]['options'] = options

        for label, data in series_dict.items():
            if not data['x']:
                continue
            sorted_idx = np.argsort(data['x'])
            plot_x = np.array(data['x'])[sorted_idx]
            plot_y = np.array(data['y'])[sorted_idx]

            opts = data['options']
            marker = opts.get('marker', 'o')
            if marker in ["", "None", None]:
                marker = None

            ax.plot(plot_x, plot_y,
                    color=data['color'],
                    linewidth=opts.get('linewidth', linewidth),
                    linestyle=opts.get('linestyle', opts.get('ls', '-')),
                    marker=marker,
                    markersize=opts.get('markersize', 7),
                    markerfacecolor=opts.get('markerfacecolor', data['color']),
                    markeredgecolor=opts.get('markeredgecolor', 'white'),
                    markeredgewidth=opts.get('markeredgewidth', 1.5),
                    label=label,
                    zorder=zorder,
                    alpha=alpha)

    def create_figure(
            self,
            width_inch: Optional[float] = None,
            height_inch: Optional[float] = None,
            dpi: int = 145,
    ):
        target_pixel_width = 1200  # whatever you liked before
        if width_inch is not None:
            width_inch = target_pixel_width / dpi
            self.width_inch = width_inch
        if height_inch is not None:
            height_inch = target_pixel_width / dpi
            self.height_inch = height_inch

        # Option A: just pass a smaller figsize when you want higher dpi
        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=dpi)

        self.ax = fig.add_subplot(111)

        self.create_bar_chart(self.ax)

        # Smart top margin based on title
        top_margin = 0.88 if self.title and self.title.strip() else 1
        bottom_margin = 0.10 if self.show_x_labels else 0.05

        fig.tight_layout(pad=1.0)
        fig.subplots_adjust(left=0.09, right=0.96, bottom=bottom_margin, top=top_margin)

        self.fig = fig
        return fig

    def scaled_formatter(self, x, pos):
        if self.y_divisor <= 1:
            return f'{x:,.0f}'
        else:
            return f'{x:,.2f}'

    def add_total_annotations(self, annotations, divisor: float = 1_000_000):
        x = annotations[0]
        y = annotations[1]
        annotations_list = annotations[2]

        lines = []
        for label, (df, col) in annotations_list:
            matching = df[df['Year'] == df['Year'].max()]
            value = pd.to_numeric(matching[col].iloc[0], errors='coerce') / divisor \
                    if not matching.empty else 0.0
            lines.append(f"{value:7.2f} MAF {label} (Latest)")

        self.ax.text(
            x=x, y=y, s="\n".join(lines),
            transform=self.ax.transAxes,
            fontsize=10.8,
            fontfamily='monospace',
            fontweight='semibold',
            ha='left', va='top',
            zorder=15
        )

    @staticmethod
    def _get_yearly_stacked_data(series: List[BarSeries]) -> dict:
        yearly = {}
        for s in series:
            if s.df.empty or 'Year' not in s.df.columns or s.col not in s.df.columns:
                continue
            df = s.df.copy()
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            df = df.dropna(subset=['Year'])
            display_label = s.label or s.col.replace('_', ' ')
            for _, row in df.iterrows():
                year = int(row['Year'])
                val = pd.to_numeric(row[s.col], errors='coerce')
                if pd.notna(val):
                    yearly.setdefault(year, []).append(
                        (val, display_label, s.color, s.color_overrides)
                    )
        return yearly

    @staticmethod
    def _get_yearly_line_data(series: List[Tuple[pd.DataFrame, str, str]]) -> dict:
        yearly = {}
        for df, col, color in series:
            if df.empty or 'Year' not in df.columns or col not in df.columns:
                continue
            df = df.copy()
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            df = df.dropna(subset=['Year'])
            for _, row in df.iterrows():
                year = int(row['Year'])
                val = pd.to_numeric(row[col], errors='coerce')
                if pd.notna(val):
                    if year not in yearly:
                        yearly[year] = []
                    yearly[year].append((val, col.replace('_', ' '), color))
        return yearly

    def annotate_value(self, ax, year, label, color,
                       position='above_top',
                       draw_line=True,
                       draw_outline=True,
                       fontsize=9,
                       offset_lines=0):
        if not hasattr(self, 'year_to_idx') or self.year_to_idx is None:
            return None
        if offset_lines not in (-1, 0, 1, 2, 3):
            raise ValueError("offset_lines must be -1, 0, 1, 2, or 3")

        in_mapping = year in self.year_to_idx
        if in_mapping:
            x = self.year_to_idx[year]
        else:
            x = None

        fig = ax.figure
        # Blended: figure x + axes y  (so labels sit on the canvas edge
        # while keeping the same vertical placement as the other annotations)
        from matplotlib.transforms import blended_transform_factory
        fig_axes_trans = blended_transform_factory(fig.transFigure, ax.transAxes)

        trans = ax.get_xaxis_transform()
        xlim = ax.get_xlim()
        xmin, xmax = xlim

        if not in_mapping:
            if not self.year_to_idx:
                return None
            min_year = min(self.year_to_idx.keys())
            max_year = max(self.year_to_idx.keys())
            if year < min_year:
                is_out_left = True
                is_out_right = False
                edge_x = xmin
            elif year > max_year:
                is_out_left = False
                is_out_right = True
                edge_x = xmax
            else:
                return None
        else:
            is_out_left = x < xmin
            is_out_right = x > xmax
            edge_x = xmin if is_out_left else xmax

        line_height_frac = (fontsize / 72.0) / ax.figure.get_figheight() * 1.15

        label_clearance = 0.0
        if position == 'below_bottom' and getattr(self, 'show_x_labels', True):
            label_clearance = 0.025

        if position == 'above_top':
            base_y, va = 1.025, 'bottom'
            arrow_dir = 'down'
            offset_sign = +1
            fixed_marker_y = 1.012
        elif position == 'below_top':
            base_y, va = 0.975, 'top'
            arrow_dir = 'up'
            offset_sign = -1
            fixed_marker_y = 0.988
        elif position == 'above_bottom':
            base_y, va = 0.025, 'bottom'
            arrow_dir = 'down'
            offset_sign = +1
            fixed_marker_y = 0.012
        elif position == 'below_bottom':
            base_y, va = -0.045, 'top'
            arrow_dir = 'up'
            offset_sign = -1
            fixed_marker_y = -0.012 - label_clearance
        else:
            base_y, va = 1.025, 'bottom'
            arrow_dir = 'down'
            offset_sign = +1
            fixed_marker_y = 1.012

        y_frac = base_y + offset_sign * offset_lines * line_height_frac

        if is_out_left or is_out_right:
            # Place against the edge of the whole figure/canvas
            if is_out_left:
                text_x = 0.005  # figure fraction — flush left
                ha = 'left'
                edge_frac = 0.0  # left edge of axes in figure coords (approx)
            else:
                text_x = 0.995  # figure fraction — flush right
                ha = 'right'
                edge_frac = 1.0

            # print(f"[OUT-OF-RANGE] year={year} label='{label}' "
            #       f"left={is_out_left} right={is_out_right} "
            #       f"text_x={text_x} ha={ha} y_frac={y_frac:.3f}")

            edge = color if draw_outline else "none"

            text = ax.text(text_x, y_frac, label,
                           transform=fig_axes_trans,
                           ha=ha, va=va,
                           fontsize=fontsize, color=color, fontweight='bold',
                           clip_on=False,
                           bbox=dict(boxstyle="round,pad=0.12",
                                     facecolor="white", alpha=0.95,
                                     edgecolor=edge, linewidth=0.8),
                           zorder=10)

            # Horizontal line to label
            # Create the label first so we can measure it
            edge = color if draw_outline else "none"
            text = ax.text(text_x, y_frac, label,
                           transform=fig_axes_trans,
                           ha=ha, va=va,
                           fontsize=fontsize, color=color, fontweight='bold',
                           clip_on=False,
                           bbox=dict(boxstyle="round,pad=0.12",
                                     facecolor="white", alpha=0.95,
                                     edgecolor=edge, linewidth=0.8),
                           zorder=10)

            # Measure the label in figure coordinates
            fig.canvas.draw()
            bbox_disp = text.get_window_extent()
            bbox_fig = bbox_disp.transformed(fig.transFigure.inverted())

            # Axes edge in figure x
            ax_pos = ax.get_position()
            vert_x = ax_pos.x0 if is_out_left else ax_pos.x1

            if is_out_left:
                # left-justified → right edge of the label
                label_edge_x = bbox_fig.x1
                # Tiny stub only when it would otherwise be zero-length
                if abs(label_edge_x - vert_x) < 0.004:
                    label_edge_x = vert_x - 0.008
            else:
                # right-justified → left edge of the label
                label_edge_x = bbox_fig.x0
                if abs(label_edge_x - vert_x) < 0.004:
                    label_edge_x = vert_x + 0.008

            # Vertical center of the label in figure y
            h_y_fig = (bbox_fig.y0 + bbox_fig.y1) / 2.0

            # Start y in figure coordinates
            if position in ('above_bottom', 'below_bottom'):
                start_y_fig = ax_pos.y0
            else:
                disp_pt = ax.transAxes.transform((0.0, fixed_marker_y))
                start_y_fig = fig.transFigure.inverted().transform(disp_pt)[1]

            # print(f"[LINE DEBUG] year={year} pos={position} "
            #       f"vert_x={vert_x:.3f} h_y_fig={h_y_fig:.3f} "
            #       f"label_edge_x={label_edge_x:.3f} delta={label_edge_x - vert_x:.3f}")

            # Vertical segment
            ax.plot([vert_x, vert_x],
                    [start_y_fig, h_y_fig],
                    transform=fig.transFigure,
                    color=color, linestyle='-', linewidth=0.8,
                    alpha=0.85, clip_on=False, zorder=12)

            # Horizontal segment
            ax.plot([vert_x, label_edge_x],
                    [h_y_fig, h_y_fig],
                    transform=fig.transFigure,
                    color=color, linestyle='-', linewidth=0.8,
                    alpha=0.85, clip_on=False, zorder=12)

            return {'vline': None, 'marker': None, 'text': text, 'connector': None}

        # ---------- original in-range path (unchanged) ----------
        if not in_mapping:
            return None

        vline = None
        marker = None
        connector = None

        if draw_line:
            vline = ax.axvline(x, color=color, linestyle='--', linewidth=1.2,
                               alpha=0.8, zorder=3)
        else:
            length = 0.010
            if arrow_dir == 'up':
                start_y = fixed_marker_y
                end_y = fixed_marker_y + length
            else:
                start_y = fixed_marker_y
                end_y = fixed_marker_y - length

            marker = ax.annotate(
                '', xy=(x, end_y), xytext=(x, start_y),
                xycoords=trans, textcoords=trans,
                arrowprops=dict(arrowstyle='-|>', color=color,
                                lw=1.0, mutation_scale=8),
                annotation_clip=False,
                zorder=5,
            )

            if offset_lines > 0:
                connector = ax.annotate(
                    '', xy=(x, y_frac), xytext=(x, fixed_marker_y),
                    xycoords=trans, textcoords=trans,
                    arrowprops=dict(arrowstyle='-', color=color, lw=1.0,
                                    linestyle='--', alpha=0.55),
                    annotation_clip=False,
                    zorder=4,
                )

        edge = color if draw_outline else "none"

        text = ax.text(x, y_frac, label,
                       transform=trans,
                       ha='center', va=va,
                       fontsize=fontsize, color=color, fontweight='bold',
                       clip_on=False,
                       bbox=dict(boxstyle="round,pad=0.12",
                                 facecolor="white", alpha=0.95,
                                 edgecolor=edge, linewidth=0.8),
                       zorder=10)

        return {'vline': vline, 'marker': marker, 'text': text, 'connector': connector}


    def annotate_range(self, ax, start_year, end_year, label,
                       line_color, text_color=None,
                       position='above_top',
                       linewidth=1.4, cap_length=0.8,
                       fontsize=9,
                       show_delta=False):
        """
        Draw a dashed horizontal bracket between two years with end caps
        and a centered label.
        Returns a dict of artists so the caller can move/update them later:
            {
                'line': Line2D,      # the dashed horizontal line
                'cap1': Line2D,      # left end cap
                'cap2': Line2D,      # right end cap
                'text': Text,        # the label
            }
        """
        if not hasattr(self, 'year_to_idx') or self.year_to_idx is None:
            return None
        if start_year not in self.year_to_idx or end_year not in self.year_to_idx:
            return None

        if text_color is None:
            text_color = line_color

        x1 = self.year_to_idx[start_year]
        x2 = self.year_to_idx[end_year]
        if x1 > x2:
            x1, x2 = x2, x1
            start_year, end_year = end_year, start_year

        # --- optional delta ---
        full_label = label
        if show_delta:
            def total_for_year(year):
                total = 0.0
                for group in self.groups:
                    yearly = MultiBarChart._get_yearly_stacked_data(group.series)
                    for val, _, _, _ in yearly.get(year, []):
                        total += val / self.y_divisor
                return total

            start_val = total_for_year(start_year)
            end_val = total_for_year(end_year)
            delta = end_val - start_val
            sign = "+" if delta >= 0 else ""
            full_label = f"{label}\n{sign}{delta:.1f}"

        # Text y-position
        pixel_up = 0.0025
        if position == 'above_top':
            y_text = 1.03 + pixel_up
            va = 'bottom'
            line_shift = 0.007
        elif position == 'below_top':
            y_text = 0.97 + pixel_up
            va = 'top'
            line_shift = -0.012
        elif position == 'above_bottom':
            y_text = 0.03 + pixel_up
            va = 'bottom'
            line_shift = 0.007
        elif position == 'below_bottom':
            y_text = -0.05 + pixel_up
            va = 'top'
            line_shift = -0.012
        else:
            y_text = 1.03 + pixel_up
            va = 'bottom'
            line_shift = 0.007

        y_line = y_text + line_shift
        trans = ax.get_xaxis_transform()

        # Dashed line
        line, = ax.plot([x1, x2], [y_line, y_line],
                        transform=trans,
                        color=line_color, linestyle='--', linewidth=linewidth,
                        solid_capstyle='butt', clip_on=False, zorder=4)

        # End caps
        cap = cap_length * 0.01
        cap1, = ax.plot([x1, x1], [y_line - cap, y_line + cap],
                        transform=trans, color=line_color, linewidth=linewidth,
                        clip_on=False, zorder=4)
        cap2, = ax.plot([x2, x2], [y_line - cap, y_line + cap],
                        transform=trans, color=line_color, linewidth=linewidth,
                        clip_on=False, zorder=4)

        # Center label
        mid = (x1 + x2) / 2
        text = ax.text(mid, y_text, full_label,
                       transform=trans,
                       ha='center', va=va,
                       fontsize=fontsize, color=text_color, fontweight='bold',
                       clip_on=False,
                       bbox=dict(
                           boxstyle="round,pad=0.25",
                           facecolor="white",
                           alpha=1.0,
                           edgecolor="none",
                       ),
                       zorder=10)

        return {
            'line': line,
            'cap1': cap1,
            'cap2': cap2,
            'text': text,
            'y_line': y_line,
            'y_text': y_text,
            'cap': cap,
        }

    def enable_draggable_vline(self, callback=None, color='#d62728', linewidth=1.6,
                               alpha=0.9, initial_year=None,
                               show_year_label=False, year_label_color=None,
                               year_label_fontsize=9,
                               show_bar_values=False, bar_value_color='white',
                               bar_value_fontsize=7.5,
                               bar_values_split_label=False,
                               bar_value_bgcolor='black',
                               bar_value_bg_alpha=0.85,
                               dual_side_lines: bool = False,
                               top_total_columns: Optional[List[str]] = None):
        if self.ax is None or self.year_to_idx is None:
            raise RuntimeError("Call create_figure() before enabling the draggable line")

        # Starting position
        if initial_year is not None and initial_year in self.year_to_idx:
            x0 = float(self.year_to_idx[initial_year])
        else:
            xlim = self.ax.get_xlim()
            x0 = float(round((xlim[0] + xlim[1]) / 2))

        # Shared settings
        self._vline_callback = callback
        self._vline_dragging = False
        self._show_year_label = show_year_label
        self._year_label_color = year_label_color or color
        self._year_label_fontsize = year_label_fontsize
        self._bar_value_color = bar_value_color
        self._bar_value_fontsize = bar_value_fontsize
        self._bar_values_split_label = bar_values_split_label
        self._bar_value_bgcolor = bar_value_bgcolor
        self._bar_value_bg_alpha = bar_value_bg_alpha
        self._show_bar_values = show_bar_values
        self._dual_side_lines = dual_side_lines
        self._top_total_columns = set(top_total_columns or [])
        self._vline_color = color
        self._vline_linewidth = linewidth
        self._vline_alpha = alpha

        # Multi-set support
        self._annotation_sets: List[_AnnotationSet] = []
        self._active_set: Optional[_AnnotationSet] = None

        # Create the primary set
        primary = self._create_annotation_set(x0)
        self._annotation_sets.append(primary)
        self._active_set = primary

        # Back-compat aliases so existing update methods still work
        self._vline = primary.vline
        self._year_label = primary.year_label
        self._bar_value_texts = primary.bar_value_texts
        self._side_lines = primary.side_lines
        self._top_total_texts = primary.top_total_texts

        if self._show_year_label:
            self._update_year_label(x0)
        if self._show_bar_values:
            self._update_bar_value_labels(x0)

        canvas = self.fig.canvas
        self._vline_cids = [
            canvas.mpl_connect('button_press_event', self._on_vline_press),
            canvas.mpl_connect('motion_notify_event', self._on_vline_motion),
            canvas.mpl_connect('button_release_event', self._on_vline_release),
            canvas.mpl_connect('scroll_event', self._on_vline_scroll),
            canvas.mpl_connect('key_press_event', self._on_vline_key),
        ]
        self.fig.canvas.draw_idle()

    def _create_annotation_set(self, x0: float) -> _AnnotationSet:
        """Create a fresh set of artists at the given x position."""
        s = _AnnotationSet()
        s.idx = int(round(x0))

        s.vline = self.ax.axvline(
            x0, color=self._vline_color, linewidth=self._vline_linewidth,
            alpha=self._vline_alpha, linestyle='-', zorder=20, picker=8
        )

        if self._dual_side_lines:
            s.vline.set_visible(False)
            for _ in range(2):
                line = self.ax.axvline(
                    x0, color=self._vline_color, linewidth=self._vline_linewidth,
                    alpha=self._vline_alpha, linestyle='-', zorder=19, visible=False
                )
                s.side_lines.append(line)

        return s

    def _remove_annotation_set(self, s: _AnnotationSet):
        """Remove all artists belonging to a set."""
        if s.vline is not None and s.vline in self.ax.lines:
            s.vline.remove()
        for line in s.side_lines:
            if line in self.ax.lines:
                line.remove()
        for t in s.bar_value_texts + s.top_total_texts:
            try:
                t.remove()
            except Exception:
                pass
        if s.year_label is not None:
            try:
                s.year_label.remove()
            except Exception:
                pass

    def _index_to_year(self, idx):
        """Reverse lookup: integer index → year."""
        for year, i in self.year_to_idx.items():
            if i == idx:
                return year
        return None

    def _report(self, idx):
        if self._vline_callback is None:
            return
        year = self._index_to_year(idx)
        if year is not None:
            self._vline_callback(year)

    def _on_vline_press(self, event):
        if event.inaxes != self.ax or event.button != 1 or event.xdata is None:
            return

        idx = int(round(event.xdata))
        if self.year_to_idx:
            min_idx = min(self.year_to_idx.values())
            max_idx = max(self.year_to_idx.values())
            idx = max(min_idx, min(max_idx, idx))

        shift = event.key == 'shift' or (hasattr(event, 'modifiers') and 'shift' in event.modifiers)

        if shift:
            if self._vline_callback is not None:
                try:
                    self._vline_callback(self._index_to_year(idx), shift=True)
                except TypeError:
                    # Fallback if the callback doesn’t accept shift yet
                    self._vline_callback(self._index_to_year(idx))
            return
        else:
            # Normal click: keep only the primary set and move it
            primary = self._annotation_sets[0]
            # Remove every set except the primary
            for extra in self._annotation_sets[1:]:
                self._remove_annotation_set(extra)
            self._annotation_sets = [primary]
            self._active_set = primary
            # Restore back-compat pointers
            self._vline = primary.vline
            self._year_label = primary.year_label
            self._bar_value_texts = primary.bar_value_texts
            self._side_lines = primary.side_lines
            self._top_total_texts = primary.top_total_texts

            primary.vline.set_xdata([idx, idx])
            primary.idx = idx

        # Update the (new) active set
        self._update_year_label(idx)
        self._update_bar_value_labels(idx)
        self._report(idx)
        self._vline_dragging = True
        self.fig.canvas.draw_idle()

    def _on_vline_scroll(self, event):
        if event.inaxes != self.ax or not hasattr(self, '_vline'):
            return

        current_x = self._vline.get_xdata()[0]
        step = 1 if event.button == 'up' else -1
        new_idx = int(round(current_x + step))

        if not self.year_to_idx:
            return
        min_idx = min(self.year_to_idx.values())
        max_idx = max(self.year_to_idx.values())
        new_idx = max(min_idx, min(max_idx, new_idx))

        if new_idx == int(round(current_x)):
            return

        self._vline.set_xdata([new_idx, new_idx])
        if self._active_set is not None:
            self._active_set.idx = new_idx
        self._update_year_label(new_idx)
        self._update_bar_value_labels(new_idx)
        self._report(new_idx)

        # Throttle: only draw every ~30 ms
        if not hasattr(self, '_last_draw_time'):
            self._last_draw_time = 0
        now = time.time()
        if now - self._last_draw_time > 0.03:
            self.fig.canvas.draw_idle()
            self._last_draw_time = now

    def _on_vline_motion(self, event):
        if not self._vline_dragging or event.inaxes != self.ax or event.xdata is None:
            return
        idx = int(round(event.xdata))
        self._vline.set_xdata([idx, idx])
        if self._active_set is not None:
            self._active_set.idx = idx
        self._update_year_label(idx)
        self._update_bar_value_labels(idx)
        self._report(idx)
        self.fig.canvas.draw_idle()

    def _on_vline_key(self, event):
        """Move the vline exactly one year with left/right arrow keys."""
        if not hasattr(self, '_vline') or self._vline is None:
            return
        if event.key not in ('left', 'right'):
            return

        current_x = self._vline.get_xdata()[0]
        step = -1 if event.key == 'left' else 1
        new_idx = int(round(current_x + step))

        if not self.year_to_idx:
            return
        min_idx = min(self.year_to_idx.values())
        max_idx = max(self.year_to_idx.values())
        new_idx = max(min_idx, min(max_idx, new_idx))

        if new_idx == int(round(current_x)):
            return

        self._vline.set_xdata([new_idx, new_idx])
        if self._active_set is not None:
            self._active_set.idx = new_idx
        self._update_year_label(new_idx)
        self._update_bar_value_labels(new_idx)
        self._report(new_idx)
        self.fig.canvas.draw_idle()

    def _on_vline_release(self, event):
        if not self._vline_dragging:
            return
        self._vline_dragging = False
        if event.xdata is not None:
            idx = int(round(event.xdata))
            self._vline.set_xdata([idx, idx])
            if self._active_set is not None:
                self._active_set.idx = idx
            self._update_year_label(idx)
            self._update_bar_value_labels(idx)
            self._report(idx)
        self.fig.canvas.draw_idle()

    def disable_draggable_vline(self):
        """Remove the line and disconnect events."""
        if hasattr(self, '_vline_cids'):
            for cid in self._vline_cids:
                self.fig.canvas.mpl_disconnect(cid)
            self._vline_cids = []
        if hasattr(self, '_annotation_sets'):
            for s in self._annotation_sets:
                self._remove_annotation_set(s)
            self._annotation_sets = []
        self._active_set = None
        self._vline_dragging = False
        self.fig.canvas.draw_idle()

    def _update_bar_value_labels(self, idx):
        """Place labels for the year under the vline."""
        if not self._show_bar_values:
            return

        year = self._index_to_year(int(idx))
        if year is None:
            self._hide_bar_value_texts()
            return

        n_groups = len(self.groups)
        if n_groups == 0:
            return

        group_width = 0.78 / n_groups
        label_gap = 0.38
        value_gap = 0.38

        y_bottom, y_top = self.ax.get_ylim()
        y_span = y_top - y_bottom
        font_height_frac = (self._bar_value_fontsize / 72.0) / self.ax.figure.get_figheight()
        margin = y_span * (0.02 + font_height_frac)

        needed = self._collect_bar_label_positions(
            idx, year, group_width, label_gap, value_gap,
            y_bottom, y_top, margin
        )

        # Stack only when y values actually collide; keep label+value pairs together
        needed = self._stack_labels_vertically(needed, y_span, y_top)

        self._apply_bar_value_texts(needed)

        self._update_top_total_labels(idx, year, group_width, y_span)

        self._update_side_lines(idx, year, group_width)

    def _hide_bar_value_texts(self):
        for t in self._bar_value_texts:
            t.set_visible(False)
        for t in getattr(self, '_top_total_texts', []):
            t.set_visible(False)

    def _collect_bar_label_positions(self, idx, year, group_width, label_gap, value_gap,
                                     y_bottom, y_top, margin):
        needed = []
        n_groups = len(self.groups)
        two_bars = (n_groups == 2)

        for g_idx, group in enumerate(self.groups):
            yearly = MultiBarChart._get_yearly_stacked_data(group.series)
            segments = yearly.get(year, [])
            if not segments:
                continue

            bar_center = idx - 0.4 + (g_idx + 0.5) * group_width
            bar_half = (group_width - 0.04) / 2.0
            bar_left = bar_center - bar_half
            bar_right = bar_center + bar_half

            # Count visible segments
            visible_count = 0
            tmp_bottom = 0.0
            for v, _, _, _ in segments:
                h = v / self.y_divisor
                if abs(v) < 1e-6 or h <= 0:
                    tmp_bottom += max(h, 0.0)
                    continue
                seg_b = tmp_bottom
                seg_t = tmp_bottom + h
                if seg_t > y_bottom and seg_b < y_top:
                    visible_count += 1
                tmp_bottom += h
            only_one = (visible_count == 1)

            if two_bars and g_idx == 0:
                place_both_left = True
                place_both_right = False
            elif two_bars and g_idx == 1:
                place_both_left = False
                place_both_right = True
            else:
                place_both_left = False
                place_both_right = False

            bottom = 0.0
            for val, label, color, overrides in segments:
                height = val / self.y_divisor
                if abs(val) < 1e-6 or height <= 0:
                    bottom += max(height, 0.0)
                    continue

                seg_bottom = bottom
                seg_top = bottom + height

                if seg_top <= y_bottom or seg_bottom >= y_top:
                    bottom += height
                    continue

                vis_bottom = max(seg_bottom, y_bottom)
                vis_top = min(seg_top, y_top)
                if vis_top <= vis_bottom:
                    bottom += height
                    continue

                mid_y = (vis_bottom + vis_top) / 2.0
                mid_y = max(y_bottom + margin, min(y_top - margin, mid_y))

                txt = (f"{val / self.y_divisor:.3f}"
                       if abs(val / self.y_divisor) < 10
                       else f"{val / self.y_divisor:.1f}")

                # bgcolor is ignored by _apply_bar_value_texts; pass a dummy
                if place_both_left:
                    value_x = bar_left - 0.06
                    needed.append((value_x, mid_y, txt, 'right', '#ffffff', '#000000'))
                    if not only_one:
                        label_x = value_x - 0.50
                        needed.append((label_x, mid_y, label, 'right', color, '#000000'))
                elif place_both_right:
                    value_x = bar_right + 0.06
                    needed.append((value_x, mid_y, txt, 'left', '#ffffff', '#000000'))
                    if not only_one:
                        label_x = value_x + 0.50
                        needed.append((label_x, mid_y, label, 'left', color, '#000000'))
                else:
                    if not only_one:
                        label_x = bar_left - label_gap
                        needed.append((label_x, mid_y, label, 'right', color, '#000000'))
                    value_x = bar_right + value_gap
                    needed.append((value_x, mid_y, txt, 'left', '#ffffff', '#000000'))

                bottom += height

        return needed

    def _apply_bar_value_texts(self, needed):
        from matplotlib.colors import to_hex

        def relative_luminance(hex_color: str) -> float:
            if not hex_color or not isinstance(hex_color, str):
                return 1.0
            h = hex_color.lstrip('#')
            if len(h) == 3:
                h = ''.join(c * 2 for c in h)
            if len(h) != 6:
                return 1.0
            try:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            except ValueError:
                return 1.0
            def channel(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            R, G, B = channel(r), channel(g), channel(b)
            return 0.2126 * R + 0.7152 * G + 0.0722 * B

        # First pass: create/update all texts and force background from text color
        for i, (x, y, txt, ha, text_color, bgcolor) in enumerate(needed):
            # Normalize whatever color format we received to hex
            try:
                norm_color = to_hex(text_color)
            except Exception:
                norm_color = '#000000'

            if norm_color.lower() == '#ffffff':
                final_bg = '#000000'
            else:
                lum = relative_luminance(norm_color)
                #final_bg = '#e0e0e0' if lum < 0.40 else '#222222'
                final_bg = '#e0e0e0' if lum < 0.25 else '#222222'

            if i < len(self._bar_value_texts):
                text = self._bar_value_texts[i]
                text.set_position((x, y))
                text.set_text(txt)
                text.set_ha(ha)
                text.set_color(text_color)
                text.set_visible(True)
                text.set_bbox(dict(
                    boxstyle="round,pad=0.18",
                    facecolor=final_bg,
                    alpha=0.92,
                    edgecolor="none",
                    linewidth=0,
                ))
            else:
                text = self.ax.text(
                    x, y, txt,
                    ha=ha, va='center',
                    fontsize=self._bar_value_fontsize,
                    color=text_color,
                    fontweight='bold',
                    zorder=25,
                    clip_on=True,
                    bbox=dict(
                        boxstyle="round,pad=0.18",
                        facecolor=final_bg,
                        alpha=0.92,
                        edgecolor="none",
                        linewidth=0,
                    ),
                )
                self._bar_value_texts.append(text)

        for j in range(len(needed), len(self._bar_value_texts)):
            self._bar_value_texts[j].set_visible(False)

        # Second pass: only for two-bar mode — measure value bubbles and push labels past them
        n_groups = len(self.groups)
        if n_groups == 2:
            self.fig.canvas.draw()
            renderer = self.fig.canvas.get_renderer()
            inv = self.ax.transData.inverted()

            value_texts = []
            for text in self._bar_value_texts:
                if not text.get_visible():
                    continue
                if text.get_color() == '#ffffff':
                    value_texts.append(text)

            for text in self._bar_value_texts:
                if not text.get_visible():
                    continue
                if text.get_color() == '#ffffff':
                    continue

                text_y = text.get_position()[1]
                text_ha = text.get_ha()

                matching_value = None
                for vt in value_texts:
                    if vt.get_ha() != text_ha:
                        continue
                    if abs(vt.get_position()[1] - text_y) < 1e-4:
                        matching_value = vt
                        break
                if matching_value is None:
                    continue

                bbox = matching_value.get_window_extent(renderer=renderer)
                x0 = inv.transform((bbox.x0, 0))[0]
                x1 = inv.transform((bbox.x1, 0))[0]
                value_width = x1 - x0

                if text_ha == 'right':
                    new_x = matching_value.get_position()[0] - value_width - 0.04
                    text.set_position((new_x, text_y))
                elif text_ha == 'left':
                    new_x = matching_value.get_position()[0] + value_width + 0.04
                    text.set_position((new_x, text_y))

    def _stack_labels_vertically(self, needed, y_span, y_top, min_gap_frac=0.028):
        def stack_side(items):
            if len(items) < 2:
                return items
            # Group by nearly-identical y so label+value pairs stay together
            items = sorted(items, key=lambda t: t[1])
            groups = []
            current_group = [items[0]]
            y_tol = y_span * 0.005
            for item in items[1:]:
                if abs(item[1] - current_group[-1][1]) < y_tol:
                    current_group.append(item)
                else:
                    groups.append(current_group)
                    current_group = [item]
            groups.append(current_group)

            # Stack the groups
            min_gap = y_span * min_gap_frac
            result = []
            prev_group_y = None
            for group in groups:
                group_y = group[0][1]
                if prev_group_y is not None and group_y < prev_group_y + min_gap:
                    group_y = prev_group_y + min_gap
                    group_y = min(group_y, y_top - y_span * 0.01)
                for item in group:
                    result.append((item[0], group_y, item[2], item[3], item[4], item[5]))
                prev_group_y = group_y
            return result

        left_items = [t for t in needed if t[3] == 'right']
        right_items = [t for t in needed if t[3] == 'left']
        return stack_side(left_items) + stack_side(right_items)

    def _update_top_total_labels(self, idx, year, group_width, y_span):
        if not getattr(self, "_top_total_columns", None):
            for t in getattr(self, "_top_total_texts", []):
                t.set_visible(False)
            return

        for t in getattr(self, "_top_total_texts", []):
            t.set_visible(False)

        # Match the exact width used when the bars are drawn
        n_groups = len(self.groups)
        group_width = 0.82 / n_groups if n_groups else 0.82

        top_needed = []

        for g_idx, group in enumerate(self.groups):
            series_values = []
            for s in group.series:
                val = 0.0
                if s.df is not None and not s.df.empty and "Year" in s.df.columns and s.col in s.df.columns:
                    match = s.df[s.df["Year"] == year]
                    if not match.empty:
                        v = pd.to_numeric(match[s.col].iloc[0], errors="coerce")
                        if pd.notna(v):
                            val = float(v)
                series_values.append((s.col, val))

            if not any(v != 0 for _, v in series_values):
                continue

            bar_center = idx - 0.4 + (g_idx + 0.5) * group_width
            bottom = 0.0
            cumulative = 0.0
            place_at = None
            found = False

            for col_name, raw_val in series_values:
                height = raw_val / self.y_divisor
                cumulative += height
                bottom += max(height, 0.0)

                if col_name in self._top_total_columns:
                    # Include this column; place label at its top
                    place_at = bottom
                    found = True
                    break

            # If the named column was never found, skip this group
            if not found:
                continue

            if abs(cumulative) > 1e-6:
                label_y = place_at + y_span * 0.025
                total_txt = f"{cumulative:.3f}" if abs(cumulative) < 10 else f"{cumulative:.1f}"
                top_needed.append((bar_center, label_y, total_txt))

        if not hasattr(self, "_top_total_texts"):
            self._top_total_texts = []

        for i, (x, y, txt) in enumerate(top_needed):
            if i < len(self._top_total_texts):
                text = self._top_total_texts[i]
                text.set_position((x, y))
                text.set_text(txt)
                text.set_visible(True)
            else:
                text = self.ax.text(
                    x, y, txt,
                    ha="center", va="bottom",
                    fontsize=self._bar_value_fontsize + 0.5,
                    color="black",
                    fontweight="bold",
                    zorder=30,
                    clip_on=False,
                    bbox=dict(
                        boxstyle="round,pad=0.2",
                        facecolor="white",
                        alpha=0.95,
                        edgecolor="#333333",
                        linewidth=0.8,
                    ),
                )
                self._top_total_texts.append(text)

        for j in range(len(top_needed), len(self._top_total_texts)):
            self._top_total_texts[j].set_visible(False)

    def _update_side_lines(self, idx, year, group_width):
        if not getattr(self, '_dual_side_lines', False) or not self._side_lines:
            if getattr(self, '_side_lines', None):
                for line in self._side_lines:
                    line.set_visible(False)
            return

        left_edge = float('inf')
        right_edge = float('-inf')

        for g_idx, group in enumerate(self.groups):
            yearly = MultiBarChart._get_yearly_stacked_data(group.series)
            if yearly.get(year):
                bar_center = idx - 0.4 + (g_idx + 0.5) * group_width
                bar_half = (group_width - 0.04) / 2.0
                left_edge = min(left_edge, bar_center - bar_half)
                right_edge = max(right_edge, bar_center + bar_half)

        if left_edge < float('inf') and right_edge > float('-inf'):
            left_pad = 0.12
            right_pad = 0.12
            self._side_lines[0].set_xdata([left_edge - left_pad, left_edge - left_pad])
            self._side_lines[0].set_visible(True)
            self._side_lines[1].set_xdata([right_edge + right_pad, right_edge + right_pad])
            self._side_lines[1].set_visible(True)
        else:
            for line in self._side_lines:
                line.set_visible(False)

    def _update_year_label(self, idx):
        """Create or move the year label centered on the vline, just below the top."""
        if not self._show_year_label:
            return

        year = self._index_to_year(int(idx))
        if year is None:
            return

        trans = self.ax.get_xaxis_transform()
        y_frac = 0.975  # just below the top of the axes

        if self._year_label is None:
            self._year_label = self.ax.text(
                idx, y_frac, str(year),
                transform=trans,
                ha='center', va='top',
                fontsize=self._year_label_fontsize,
                color=self._year_label_color,
                fontweight='bold',
                clip_on=False,
                bbox=dict(boxstyle="round,pad=0.15",
                          facecolor="white", alpha=0.9,
                          edgecolor=self._year_label_color, linewidth=0.6),
                zorder=21
            )
            # Store it on the active set as well
            if self._active_set is not None:
                self._active_set.year_label = self._year_label
        else:
            self._year_label.set_position((idx, y_frac))
            self._year_label.set_text(str(year))


    def annotate_year_indicators(self, ax, indicators: List[List[Tuple[int, str, str]]],
                                 bar_height_frac: float = 0.5,
                                 y_offset_frac: float = 0.035,
                                 row_spacing_frac: float = 0.0,
                                 legend_entries: Optional[List[Tuple[str, str]]] = None):
        if not hasattr(self, 'year_to_idx') or self.year_to_idx is None:
            return

        # Remove previous indicator patches
        if hasattr(self, '_indicator_patches'):
            for p in self._indicator_patches:
                try:
                    p.remove()
                except Exception:
                    pass
        self._indicator_patches = []

        # Approximate one font height in axes-fraction units
        fontsize = 10
        fig_height = ax.figure.get_figheight()
        font_height_frac = (fontsize / 72.0) / fig_height
        bar_height = font_height_frac * bar_height_frac

        trans = ax.get_xaxis_transform()

        # Group indicators by year so we can decide stacking per year
        from collections import defaultdict
        year_indicators = defaultdict(list)  # year -> list of (color, label, preferred_row)

        for row_idx, row in enumerate(indicators):
            for year, color, label in row:
                if year in self.year_to_idx:
                    year_indicators[year].append((color, label, row_idx))

        # Draw: for each year, place on lowest available rows (prefer row 0 if free)
        # Widen so adjacent years of the same color touch and form a continuous bar
        for year, items in year_indicators.items():
            x = self.year_to_idx[year]
            width = 1.0  # full year width so neighbors touch

            # Sort so preferred row 0 comes first; if multiple, stack them
            items.sort(key=lambda t: t[2])

            for stack_idx, (color, _label, _preferred_row) in enumerate(items):
                # stack_idx 0 sits highest (closest to top), later ones lower
                # row_spacing_frac = 0 so rows touch
                y_top = 1.0 - y_offset_frac - (stack_idx * (bar_height + row_spacing_frac))
                y_bottom = y_top - bar_height

                rect = Rectangle(
                    (x - width / 2, y_bottom),
                    width,
                    bar_height,
                    transform=trans,
                    facecolor=color,
                    edgecolor='none',
                    alpha=0.85,
                    zorder=15,
                    clip_on=False,
                )
                ax.add_patch(rect)
                self._indicator_patches.append(rect)

        # Legend handling (deduplicated)
        if legend_entries is not None:
            handles, labels = ax.get_legend_handles_labels()

            seen = set()
            clean_handles = []
            clean_labels = []
            for h, lab in zip(handles, labels):
                if lab not in seen:
                    seen.add(lab)
                    clean_handles.append(h)
                    clean_labels.append(lab)

            for color, label in legend_entries:
                if label not in seen:
                    clean_handles.append(
                        Patch(facecolor=color, edgecolor='none', alpha=0.85, label=label)
                    )
                    clean_labels.append(label)
                    seen.add(label)

            ax.legend(
                clean_handles,
                clean_labels,
                loc='upper left',
                fontsize=9,
                frameon=True,
                ncol=1,
            )

        ax.figure.canvas.draw_idle()

    def add_annotation_set(self, year: int):
        """Create a new annotation set at the given year and make it the active one.
        Used by shift-click so all linked charts stay in sync.
        """
        if not hasattr(self, '_annotation_sets') or year not in self.year_to_idx:
            return
        idx = self.year_to_idx[year]
        new_set = self._create_annotation_set(idx)
        self._annotation_sets.append(new_set)
        self._active_set = new_set

        # Point the back-compat attributes at the new set
        self._vline = new_set.vline
        self._year_label = new_set.year_label
        self._bar_value_texts = new_set.bar_value_texts
        self._side_lines = new_set.side_lines
        self._top_total_texts = new_set.top_total_texts

        self._update_year_label(idx)
        self._update_bar_value_labels(idx)
        self.fig.canvas.draw_idle()

    @staticmethod
    def compute_stack_totals(
            series: List[BarSeries] | BarGroup,
            top_col: str,
            total_col_name: str = "Total",
    ) -> pd.DataFrame:
        """
        Sum every series from the bottom of the stack up to and including top_col.
        Series above top_col are excluded. NaNs are treated as 0.
        Returns DataFrame with columns ['Year', total_col_name].
        """
        if isinstance(series, BarGroup):
            series = series.series

        if not series:
            return pd.DataFrame(columns=["Year", total_col_name])

        # Find the index of the cutoff column (inclusive)
        cutoff = None
        for i, s in enumerate(series):
            if s.col == top_col:
                cutoff = i
                break
        if cutoff is None:
            return pd.DataFrame(columns=["Year", total_col_name])

        included = series[:cutoff + 1]  # bottom through and including top_col

        all_years = set()
        for s in included:
            if s.df is not None and not s.df.empty and "Year" in s.df.columns:
                years = pd.to_numeric(s.df["Year"], errors="coerce").dropna()
                all_years.update(int(y) for y in years)

        if not all_years:
            return pd.DataFrame(columns=["Year", total_col_name])

        rows = []
        for year in sorted(all_years):
            total = 0.0
            for s in included:
                if s.df is None or s.df.empty or s.col not in s.df.columns:
                    continue
                match = s.df[s.df["Year"] == year]
                if match.empty:
                    continue
                val = pd.to_numeric(match[s.col].iloc[0], errors="coerce")
                if pd.notna(val):
                    total += val
            rows.append({"Year": year, total_col_name: total})

        return pd.DataFrame(rows)