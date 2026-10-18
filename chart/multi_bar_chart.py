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


@dataclass
class BarSeries:
    """One stacked series inside a BarGroup."""
    df: pd.DataFrame
    col: str
    color: str
    color_overrides: Optional[List[Tuple[float, str]]] = None   # (value, color)
    label: Optional[str] = None                                 # optional display override


@dataclass
class BarGroup:
    """A labeled group of stacked bar series."""
    label: str
    series: List[BarSeries] = field(default_factory=list)

    @classmethod
    def from_tuples(cls, label: str, series_list: List[Tuple]) -> "BarGroup":
        series = []
        for item in series_list:
            if len(item) == 3:
                df, col, color = item
                series.append(BarSeries(df=df, col=col, color=color))
            elif len(item) == 4:
                df, col, color, overrides = item
                series.append(BarSeries(df=df, col=col, color=color, color_overrides=overrides))
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
                 annotations: List[Tuple[float, float, List[Tuple[str, Tuple[pd.DataFrame, str]]]]] | None = None
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
        elif data_range <= 5.0:
            major_step = 0.5
            minor_step = 0.1
        elif data_range <= 12.0:
            major_step = 1.0
            minor_step = 0.5
        elif data_range <= 25.0:
            major_step = 2.0
            minor_step = 1
        elif data_range <= 50.0:
            major_step = 5.0
            minor_step = 1.0
        elif data_range <= 200.0:
            major_step = 10.0
            minor_step = 2.0
        else:
            major_step = round(data_range / 8 / 10) * 10 or 100
            minor_step = major_step / 5

        ax.yaxis.set_major_locator(MultipleLocator(major_step))
        ax.yaxis.set_minor_locator(MultipleLocator(minor_step))

        if data_range <= 5.0:
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        elif data_range <= 20.0:
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

        # Tick appearance
        ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=10)
        ax.tick_params(axis='y', which='minor', length=3, width=0.7, labelsize=8.5)

        ax.grid(True, which='major', axis='y', linestyle='-', linewidth=1.2, color='black', alpha=0.7)
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

        years = sorted(y for y in all_years if self.start_year <= y <= self.end_year)
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
        for g_idx, (_, yearly_data) in enumerate(group_data):
            bar_positions = x - 0.4 + (g_idx + 0.5) * group_width
            for i, year in enumerate(years):
                if self.x_min is not None and year < self.x_min:
                    continue
                if self.x_max is not None and year > self.x_max:
                    continue
                bottom = 0.0
                for val, label, color, overrides in yearly_data.get(year, []):
                    # Per-bar color override by value match
                    bar_color = color
                    if overrides:
                        for ov_val, ov_color in overrides:
                            if abs(val - ov_val) < 1e-6:
                                bar_color = ov_color
                                break

                    height = val / self.y_divisor
                    ax.bar(bar_positions[i], height, width=group_width - spacing,
                           bottom=bottom, color=bar_color, edgecolor='none',
                           linewidth=0.8, label=label, zorder=5)
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
                display_label = f"{group.label} {clean_label}"

                proxy = Rectangle((0, 0), 1, 1,
                                  fc=s.color,
                                  ec='white',
                                  linewidth=0.8)

                if display_label not in unique_legend:
                    unique_legend[display_label] = proxy

        if unique_legend:
            ax.legend(unique_legend.values(), unique_legend.keys(),
                      loc='best',
                      fontsize=9,
                      frameon=True,
                      ncol=1)

        # Y-axis
        self.setup_yaxis(ax)

        ax.set_title(f"{self.title or ''}", fontsize=13.5, fontweight='bold', pad=12)

        ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=10)
        ax.tick_params(axis='y', which='minor', length=3, width=0.7, labelsize=8.5)
        # Grid is fully controlled inside setup_yaxis (no override here)

        for ann in self.annotations:
            self.add_total_annotations(ann)

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

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=145)
        self.ax = fig.add_subplot(111)

        self.create_bar_chart(self.ax)

        # Smart top margin based on title
        top_margin = 0.88 if self.title and self.title.strip() else 1
        bottom_margin = 0.15 if self.show_x_labels else 0.05

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
                if pd.notna(val) and val > 0:
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

    def annotate_value(self, ax, year, value, color,
                       position='above_top',          # 'above_top', 'below_top', 'above_bottom', 'below_bottom'
                       draw_line=True, draw_text=True,
                       text=None, fontsize=9):
        """
        Annotate a single year/value on the top or bottom x-axis.
        year: calendar year (will be mapped to the chart’s x-index)
        value: y-coordinate of the marker (data units)
        """
        if not hasattr(self, 'year_to_idx') or year not in self.year_to_idx:
            return

        x = self.year_to_idx[year]
        label = text if text is not None else str(value)

        # Vertical line (optional)
        if draw_line:
            ax.axvline(x, color=color, linestyle='--', linewidth=1.2,
                       alpha=0.8, zorder=3)

        if not draw_text:
            return

        # Position relative to the x-axis
        trans = ax.get_xaxis_transform()   # x in data, y in axes fraction
        if position == 'above_top':
            y_frac, va = 1.02, 'bottom'
        elif position == 'below_top':
            y_frac, va = 0.98, 'top'
        elif position == 'above_bottom':
            y_frac, va = 0.02, 'bottom'
        elif position == 'below_bottom':
            y_frac, va = -0.04, 'top'      # may collide with tick labels
        else:
            y_frac, va = 1.02, 'bottom'

        ax.text(x, y_frac, label,
                transform=trans,
                ha='center', va=va,
                fontsize=fontsize, color=color, fontweight='bold',
                clip_on=False,
                bbox=dict(boxstyle="round,pad=0.25",
                          facecolor="white", alpha=0.95,
                          edgecolor=color, linewidth=0.8),
                zorder=10)

    def annotate_range(self, ax, start_year, end_year, label,
                       line_color, text_color=None,
                       position='above_top',
                       linewidth=1.4, cap_length=0.8,
                       fontsize=9,
                       show_delta=False):
        """
        Draw a dashed horizontal bracket between two years with end caps
        and a centered label.
        show_delta=True: append the change in total bar height
                     (end_year total − start_year total) on a new line.
        """
        if not hasattr(self, 'year_to_idx'):
            return
        if start_year not in self.year_to_idx or end_year not in self.year_to_idx:
            return

        if text_color is None:
            text_color = line_color

        x1 = self.year_to_idx[start_year]
        x2 = self.year_to_idx[end_year]
        if x1 > x2:
            x1, x2 = x2, x1
            start_year, end_year = end_year, start_year

        # --- optional delta calculation ---
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
        ax.plot([x1, x2], [y_line, y_line],
                transform=trans,
                color=line_color, linestyle='--', linewidth=linewidth,
                solid_capstyle='butt', clip_on=False, zorder=4)

        # End caps
        cap = cap_length * 0.01
        ax.plot([x1, x1], [y_line - cap, y_line + cap],
                transform=trans, color=line_color, linewidth=linewidth,
                clip_on=False, zorder=4)
        ax.plot([x2, x2], [y_line - cap, y_line + cap],
                transform=trans, color=line_color, linewidth=linewidth,
                clip_on=False, zorder=4)

        # Center label (borderless white bubble)
        mid = (x1 + x2) / 2
        ax.text(mid, y_text, full_label,
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