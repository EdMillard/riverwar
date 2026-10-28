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
        group_width = 0.78 / n_groups if n_groups > 0 else 0.6
        spacing = 0.04

        max_height = 0.0

        # Underlay lines
        self._plot_lines(ax, self.underlay_lines, self.year_to_idx, zorder=1, linewidth=2.8, alpha=0.85)

        # Bars
        for g_idx, (group, yearly_data) in enumerate(zip(self.groups, group_data)):
            # group_data currently stores (label, yearly) — adjust if you keep the old tuple form
            # Prefer walking the original groups so we have access to the BarSeries objects
            yearly_data = MultiBarChart._get_yearly_stacked_data(group.series)
            bar_positions = x - 0.4 + (g_idx + 0.5) * group_width

            for i, year in enumerate(years):
                if self.x_min is not None and year < self.x_min:
                    continue
                if self.x_max is not None and year > self.x_max:
                    continue

                bottom = 0.0
                for s_idx, (val, label, color, overrides) in enumerate(yearly_data.get(year, [])):
                    # Per-bar color override by value match
                    bar_color = color
                    if overrides:
                        for ov_val, ov_color in overrides:
                            if abs(val - ov_val) < 1e-6:
                                bar_color = ov_color
                                break

                    # Recover the owning BarSeries so we can apply its style
                    # (yearly data does not currently carry the series object)
                    series_obj = None
                    if s_idx < len(group.series):
                        series_obj = group.series[s_idx]

                    height = val / self.y_divisor

                    # Defaults
                    edge = 'none'
                    lw = 0.0
                    hatch = None
                    hatch_color = bar_color

                    if series_obj is not None:
                        if series_obj.edgecolor is not None:
                            edge = series_obj.edgecolor
                        if series_obj.linewidth is not None:
                            lw = series_obj.linewidth
                        hatch = series_obj.hatch
                        hatch_color = series_obj.hatch_color or series_obj.color

                    bar_kwargs = dict(
                        width=group_width - spacing,
                        bottom=bottom,
                        color=bar_color,
                        edgecolor=edge,
                        linewidth=lw,
                        label=None if self.custom_legend is not None else label,
                        zorder=5,
                    )

                    if hatch:
                        bar_kwargs['hatch'] = hatch
                        # Prefer hatch color for the edge when a hatch is present
                        # (matches pie-chart behavior) unless an explicit edgecolor was given
                        if series_obj is None or series_obj.edgecolor is None:
                            bar_kwargs['edgecolor'] = hatch_color

                    ax.bar(bar_positions[i], height, **bar_kwargs, antialiased=False)

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
        if year not in self.year_to_idx:
            return None
        if offset_lines not in (0, 1, 2, 3):
            raise ValueError("offset_lines must be 0, 1, 2, or 3")

        x = self.year_to_idx[year]
        trans = ax.get_xaxis_transform()

        # Approximate one font height in axes-fraction units
        line_height_frac = (fontsize / 72.0) / ax.figure.get_figheight() * 1.15

        # Extra space needed when x-axis tick labels are visible
        label_clearance = 0.0
        if position == 'below_bottom' and getattr(self, 'show_x_labels', True):
            # Just clear the tick labels (about half a font height)
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
            # Fixed marker sits just below the axis, or further down
            # if tick labels are present
            fixed_marker_y = -0.012 - label_clearance
        else:
            base_y, va = 1.025, 'bottom'
            arrow_dir = 'down'
            offset_sign = +1
            fixed_marker_y = 1.012

        # Only the text is offset
        y_frac = base_y + offset_sign * offset_lines * line_height_frac

        vline = None
        marker = None
        connector = None

        if draw_line:
            vline = ax.axvline(x, color=color, linestyle='--', linewidth=1.2,
                               alpha=0.8, zorder=3)
        else:
            # Short fixed arrow — stays next to the axis (or below labels)
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

            # Connector starts from the fixed marker (which already accounts for labels)
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
        """
        ...
        If show_bar_values=True, labels are drawn in the middle of each stacked
        segment for the year the line is on (value of that segment only).

        If dual_side_lines=True, the single center line is hidden and two
        vertical lines are drawn at the outer left and right edges of the
        annotation bubbles.
        """
        if self.ax is None or self.year_to_idx is None:
            raise RuntimeError("Call create_figure() before enabling the draggable line")

        # Starting position
        if initial_year is not None and initial_year in self.year_to_idx:
            x0 = float(self.year_to_idx[initial_year])
        else:
            xlim = self.ax.get_xlim()
            x0 = float(round((xlim[0] + xlim[1]) / 2))

        self._vline = self.ax.axvline(
            x0, color=color, linewidth=linewidth, alpha=alpha,
            linestyle='-', zorder=20, picker=8
        )
        self._vline_callback = callback
        self._vline_dragging = False
        self._show_year_label = show_year_label
        self._year_label_color = year_label_color or color
        self._year_label_fontsize = year_label_fontsize
        self._year_label = None

        self._bar_value_color = bar_value_color  # default white
        self._bar_value_fontsize = bar_value_fontsize
        self._bar_value_texts = []
        self._bar_values_split_label = bar_values_split_label
        self._bar_value_bgcolor = bar_value_bgcolor  # default black
        self._bar_value_bg_alpha = bar_value_bg_alpha
        self._show_bar_values = show_bar_values
        self._dual_side_lines = dual_side_lines
        self._side_lines = []
        self._top_total_columns = set(top_total_columns or [])
        self._top_total_texts = []

        if dual_side_lines:
            # Keep the center line for picking/interaction but make it invisible
            self._vline.set_visible(False)
            # Create two side lines (positioned later)
            for _ in range(2):
                line = self.ax.axvline(
                    x0, color=color, linewidth=linewidth, alpha=alpha,
                    linestyle='-', zorder=19, visible=False
                )
                self._side_lines.append(line)

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

        # Jump the line to the click location immediately
        idx = int(round(event.xdata))

        # Clamp to valid year range
        if self.year_to_idx:
            min_idx = min(self.year_to_idx.values())
            max_idx = max(self.year_to_idx.values())
            idx = max(min_idx, min(max_idx, idx))

        self._vline.set_xdata([idx, idx])
        self._update_year_label(idx)
        self._update_bar_value_labels(idx)
        self._report(idx)

        # Start dragging so further motion continues to move it
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
        if hasattr(self, '_vline') and self._vline in self.ax.lines:
            self._vline.remove()
        if hasattr(self, '_side_lines'):
            for line in self._side_lines:
                if line in self.ax.lines:
                    line.remove()
            self._side_lines = []
        self._vline_dragging = False
        self.fig.canvas.draw_idle()

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
        """
        ...
        If show_bar_values=True, labels are drawn in the middle of each stacked
        segment for the year the line is on (value of that segment only).

        If dual_side_lines=True, the single center line is hidden and two
        vertical lines are drawn at the outer left and right edges of the
        annotation bubbles.
        """
        if self.ax is None or self.year_to_idx is None:
            raise RuntimeError("Call create_figure() before enabling the draggable line")

        # Starting position
        if initial_year is not None and initial_year in self.year_to_idx:
            x0 = float(self.year_to_idx[initial_year])
        else:
            xlim = self.ax.get_xlim()
            x0 = float(round((xlim[0] + xlim[1]) / 2))

        self._vline = self.ax.axvline(
            x0, color=color, linewidth=linewidth, alpha=alpha,
            linestyle='-', zorder=20, picker=8
        )
        self._vline_callback = callback
        self._vline_dragging = False
        self._show_year_label = show_year_label
        self._year_label_color = year_label_color or color
        self._year_label_fontsize = year_label_fontsize
        self._year_label = None

        self._bar_value_color = bar_value_color  # default white
        self._bar_value_fontsize = bar_value_fontsize
        self._bar_value_texts = []
        self._bar_values_split_label = bar_values_split_label
        self._bar_value_bgcolor = bar_value_bgcolor  # default black
        self._bar_value_bg_alpha = bar_value_bg_alpha
        self._show_bar_values = show_bar_values
        self._dual_side_lines = dual_side_lines
        self._side_lines = []
        self._top_total_columns = set(top_total_columns or [])
        self._top_total_texts = []

        if dual_side_lines:
            # Keep the center line for picking/interaction but make it invisible
            self._vline.set_visible(False)
            # Create two side lines (positioned later)
            for _ in range(2):
                line = self.ax.axvline(
                    x0, color=color, linewidth=linewidth, alpha=alpha,
                    linestyle='-', zorder=19, visible=False
                )
                self._side_lines.append(line)

        # These must run regardless of dual_side_lines
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

    def _update_bar_value_labels(self, idx):
        """Place labels for the year under the vline.
        Bubbles sit completely outside the bars.
        Values: always black background + white text.
        Labels: adaptive background biased strongly toward black.

        When dual_side_lines is enabled, places two vertical lines at the
        inner edges of the annotation bubbles (right edge of left bubbles,
        left edge of right bubbles).

        When top_total_columns is set, places a cumulative total (that segment
        plus everything stacked under it) at the top of each matching series.
        """
        if not self._show_bar_values:
            return

        year = self._index_to_year(int(idx))
        if year is None:
            for t in self._bar_value_texts:
                t.set_visible(False)
            for t in getattr(self, '_top_total_texts', []):
                t.set_visible(False)
            return

        n_groups = len(self.groups)
        if n_groups == 0:
            return

        group_width = 0.78 / n_groups
        # Left side pulled a bit further off the bar
        label_gap = 0.22
        value_gap = 0.35

        y_bottom, y_top = self.ax.get_ylim()
        font_height_frac = (self._bar_value_fontsize / 72.0) / self.ax.figure.get_figheight()
        special_y = y_top - (y_top - y_bottom) * (0.04 + font_height_frac * 1.6)

        needed = []  # (x, y, text, ha, text_color, bgcolor)

        def is_dark(hex_color: str) -> bool:
            """Return True for colors that need a light background for readability.
            More sensitive to dark greens than the plain luminance threshold.
            """
            if not hex_color or not isinstance(hex_color, str):
                return False
            h = hex_color.lstrip('#')
            if len(h) == 3:
                h = ''.join(c * 2 for c in h)
            if len(h) != 6:
                return False
            try:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            except ValueError:
                return False

            # Standard relative luminance
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

            # Extra penalty for greens: if the green channel dominates and overall
            # luminance is still modest, treat it as dark.
            if g > r + 40 and g > b + 40 and luminance < 160:
                return True

            return luminance < 140

        for g_idx, group in enumerate(self.groups):
            yearly = MultiBarChart._get_yearly_stacked_data(group.series)
            segments = yearly.get(year, [])
            if not segments:
                continue

            bar_center = idx - 0.4 + (g_idx + 0.5) * group_width
            bar_half = (group_width - 0.04) / 2.0
            bar_left = bar_center - bar_half
            bar_right = bar_center + bar_half

            bottom = 0.0
            for val, label, color, overrides in segments:
                height = val / self.y_divisor
                if abs(val) < 1e-6 or height <= 0:
                    bottom += max(height, 0.0)
                    continue

                top = bottom + height
                if bottom < y_top and top > y_top:
                    mid_y = special_y
                else:
                    geometric_mid = bottom + height / 2.0
                    nudge = min(height * 0.04, 0.08)
                    mid_y = geometric_mid - nudge

                txt = (f"{val / self.y_divisor:.3f}"
                       if abs(val / self.y_divisor) < 10
                       else f"{val / self.y_divisor:.1f}")

                dark = is_dark(color)

                # Label: adaptive background (now biased strongly toward black)
                # lighter bar → black bg; only quite dark bars → light gray bg
                label_bg = '#222222' if not dark else '#e0e0e0'

                # Label bubble: right-justified, left of the bar
                label_x = bar_left - label_gap
                needed.append((label_x, mid_y, label, 'right', color, label_bg))

                # Value bubble: always black background + white text, further right
                value_x = bar_right + value_gap
                needed.append((value_x, mid_y, txt, 'left', '#ffffff', '#000000'))

                bottom += height

        # Reuse / create Text artists for side bubbles
        for i, (x, y, txt, ha, text_color, bgcolor) in enumerate(needed):
            if i < len(self._bar_value_texts):
                text = self._bar_value_texts[i]
                text.set_position((x, y))
                text.set_text(txt)
                text.set_ha(ha)
                text.set_color(text_color)
                text.set_visible(True)
                text.set_bbox(dict(
                    boxstyle="round,pad=0.18",
                    facecolor=bgcolor,
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
                        facecolor=bgcolor,
                        alpha=0.92,
                        edgecolor="none",
                        linewidth=0,
                    ),
                )
                self._bar_value_texts.append(text)

        for j in range(len(needed), len(self._bar_value_texts)):
            self._bar_value_texts[j].set_visible(False)

        # --- Cumulative top totals for selected columns ---
        if getattr(self, '_top_total_columns', None):
            for t in getattr(self, '_top_total_texts', []):
                t.set_visible(False)

            top_needed = []  # (x, y, text)

            for g_idx, group in enumerate(self.groups):
                # Build a year → value map for every series in this group
                series_values = []
                for s in group.series:
                    val = 0.0
                    if not s.df.empty and 'Year' in s.df.columns and s.col in s.df.columns:
                        match = s.df[s.df['Year'] == year]
                        if not match.empty:
                            val = pd.to_numeric(match[s.col].iloc[0], errors='coerce')
                            if pd.isna(val):
                                val = 0.0
                    series_values.append((s.col, val))

                if not any(v > 0 for _, v in series_values):
                    continue

                bar_center = idx - 0.4 + (g_idx + 0.5) * group_width
                bottom = 0.0
                cumulative = 0.0

                for col_name, raw_val in series_values:
                    height = raw_val / self.y_divisor
                    cumulative += height

                    print(f"[top-total] year={year} group={group.label!r} "
                          f"col={col_name!r} height={height:.4f} cumulative={cumulative:.4f} "
                          f"in_list={col_name in self._top_total_columns}")

                    if col_name in self._top_total_columns and height > 0:
                        top_y = bottom + height
                        label_y = top_y + (y_top - y_bottom) * 0.025
                        total_txt = (f"{cumulative:.3f}" if abs(cumulative) < 10 else f"{cumulative:.1f}")
                        print(f"  --> placing '{total_txt}' at x={bar_center:.3f} y={label_y:.3f}")
                        top_needed.append((bar_center, label_y, total_txt))

                    bottom += max(height, 0.0)

            if not hasattr(self, '_top_total_texts'):
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
                        ha='center', va='bottom',
                        fontsize=self._bar_value_fontsize + 0.5,
                        color='black',
                        fontweight='bold',
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
        else:
            for t in getattr(self, '_top_total_texts', []):
                t.set_visible(False)

        # --- Dual side lines: place them at the INNER edges of the bubbles ---
        # Left line  = right edge of left (label) bubbles
        # Right line = left edge of right (value) bubbles
        if getattr(self, '_dual_side_lines', False) and self._side_lines and self._bar_value_texts:
            # Force a draw so get_window_extent() is valid
            self.fig.canvas.draw()

            renderer = self.fig.canvas.get_renderer()
            left_inner = float('-inf')  # right edge of label bubbles
            right_inner = float('inf')  # left edge of value bubbles

            for text in self._bar_value_texts:
                if not text.get_visible():
                    continue
                bbox = text.get_window_extent(renderer=renderer)
                inv = self.ax.transData.inverted()
                x_left_data = inv.transform((bbox.x0, 0))[0]
                x_right_data = inv.transform((bbox.x1, 0))[0]

                ha = text.get_ha()
                if ha == 'right':
                    # Left (label) bubble → we want its right edge
                    left_inner = max(left_inner, x_right_data)
                elif ha == 'left':
                    # Right (value) bubble → we want its left edge
                    right_inner = min(right_inner, x_left_data)

            if left_inner > float('-inf') and right_inner < float('inf'):
                # Left line gets a little extra gap so it sits further off the bar
                left_pad = 0.025
                right_pad = 0.015
                self._side_lines[0].set_xdata([left_inner + left_pad, left_inner + left_pad])
                self._side_lines[0].set_visible(True)
                self._side_lines[1].set_xdata([right_inner - right_pad, right_inner - right_pad])
                self._side_lines[1].set_visible(True)
            else:
                for line in self._side_lines:
                    line.set_visible(False)
        elif getattr(self, '_side_lines', None):
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