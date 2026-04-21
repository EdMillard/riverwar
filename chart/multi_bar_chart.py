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
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import date
from typing import List, Optional, Tuple, Dict, Any
from chart.chart import Chart
from collections import defaultdict


class MultiBarChart(Chart):
    def __init__(self,
                 groups: List[Tuple[str, List[Tuple[pd.DataFrame, str, str]]]],
                 underlay_lines: List[Tuple[pd.DataFrame, str, str] |
                                   Tuple[pd.DataFrame, str, str, Dict[str, Any]]] | None = None,
                 overlay_lines: List[Tuple[pd.DataFrame, str, str] |
                                   Tuple[pd.DataFrame, str, str, Dict[str, Any]]] | None = None,
                 title: str = "",
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
                 value_divisor: float = 1_000_000,
                 annotations: List[Tuple[float, float, List[Tuple[str, Tuple[pd.DataFrame, str]]]]] | None = None
    ):

        super().__init__([], start_date, current_date, end_date)

        self.groups = groups
        self.underlay_lines = underlay_lines or []
        self.overlay_lines = overlay_lines or []
        self.show_totals = show_totals

        self.title = title
        if start_year is None:
            self.start_year = 1971
        else:
            self.start_year = start_year
        if end_year is None:
            self.end_year = 2026
        else:
            self.end_year = end_year
        self.y_max = y_max
        self.y_min = y_min
        self.x_max = x_max
        self.x_min = x_min

        self.value_divisor = value_divisor
        self.annotations = annotations or []

        self.height_inch = 6.2
        self.width_inch = 9.0

        self.ax = None
        self.fig = None

        self.original_groups = [
            (label, [(df.copy(), col, color) for df, col, color in series_list])
            for label, series_list in groups
        ]

    def create_bar_chart(self, ax):
        if not self.groups:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        ax.clear()

        group_data = []
        all_years = set()

        for group_label, series_list in self.groups:
            yearly = MultiBarChart._get_yearly_stacked_data(series_list)
            group_data.append((group_label, yearly))
            for year in yearly:
                all_years.add(year)

        years = sorted(y for y in all_years if self.start_year <= y <= self.end_year)
        if not years:
            ax.text(0.5, 0.5, "No valid yearly data", ha='center', va='center', fontsize=14)
            return

        x = np.arange(len(years))
        year_to_idx = {year: idx for idx, year in enumerate(years)}

        n_groups = len(self.groups)
        group_width = 0.78 / n_groups if n_groups > 0 else 0.6
        spacing = 0.04

        max_height = 0.0

        # Underlay lines
        #
        self._plot_lines(ax, self.underlay_lines, year_to_idx, zorder=1, linewidth=2.8, alpha=0.85)

        # Bars
        #
        for g_idx, (_, yearly_data) in enumerate(group_data):
            bar_positions = x - 0.4 + (g_idx + 0.5) * group_width
            for i, year in enumerate(years):
                if self.x_min is not None and year < self.x_min:
                    continue
                if self.x_max is not None and year > self.x_max:
                    continue
                bottom = 0.0
                for val, label, color in yearly_data.get(year, []):
                    height = val / self.value_divisor
                    ax.bar(bar_positions[i], height, width=group_width - spacing,
                           bottom=bottom, color=color, edgecolor='white',
                           linewidth=0.8, label=label, zorder=5)
                    bottom += height
                    max_height = max(max_height, bottom)

                if self.show_totals:
                    total = sum(v[0] for v in yearly_data.get(year, [])) / self.value_divisor
                    if total > 1:
                        ax.text(bar_positions[i], total + 0.12, f"{total:.1f}",
                                ha='center', va='bottom', fontsize=8.5, fontweight='bold', zorder=6)

        # Overlay Lines
        #
        self._plot_lines(ax, self.overlay_lines, year_to_idx, zorder=12, linewidth=3.2, alpha=0.95)

        # Y limits
        ax.set_ylim(self.y_min if self.y_min is not None else 0.0,
                    self.y_max if self.y_max is not None else max(max_height * 1.13, 0.1))

        # X limits
        x_left = x[0] - 0.55
        x_right = x[-1] + 0.55

        if self.x_min is not None:
            if self.x_min >= self.start_year-1:  # year
                x_left = year_to_idx.get(int(self.x_min), x[0]) - 0.6
            else:
                x_left = float(self.x_min)

        if self.x_max is not None:
            if self.x_max >= self.start_year-1:  # year
                x_right = year_to_idx.get(int(self.x_max), x[-1]) + 1.2
            else:
                x_right = float(self.x_max)

        # Legend & labels
        #
        handles, labels = ax.get_legend_handles_labels()
        unique_legend = dict(zip(labels, handles))
        ax.legend(unique_legend.values(), unique_legend.keys(),
                  loc='upper left', fontsize=9, frameon=True, ncol=2,
                  # title="Components", title_fontsize=10
                  )

        ax.set_xticks(x)
        ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right', fontsize=10)
        ax.set_xlim(x_left, x_right)

        ax.set_ylabel("Value (MAF)", fontsize=11.5)
        ax.set_xlabel("Year", fontsize=11.5)
        ax.set_title(f"{self.title or ''}", fontsize=13.5, fontweight='bold', pad=12)

        ax.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)

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
                    series_dict[label]['y'].append(val / self.value_divisor)
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

        fig.tight_layout(pad=1.8)
        fig.subplots_adjust(left=0.09, right=0.96, bottom=0.15, top=0.87)

        self.fig = fig
        return fig

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
    def _get_yearly_stacked_data(series: List[Tuple[pd.DataFrame, str, str]]) -> dict:
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
                if pd.notna(val) and val > 0:
                    if year not in yearly:
                        yearly[year] = []
                    yearly[year].append((val, col.replace('_', ' '), color))
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