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
from reservoirs.reservoir import Reservoir
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import date
from typing import List, Optional, Tuple
from chart.chart import Chart

class MultiBarChart(Chart):
    def __init__(self,
                 left_series: List[Tuple[pd.DataFrame, str, str]],
                 right_series: List[Tuple[pd.DataFrame, str, str]],
                 title: str = "",
                 left_label: str = "Left",
                 right_label: str = "Right",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None,
                 value_divisor: float = 1_000_000,
                 annotations: List[Tuple[float, float, List[Tuple[str, Tuple[pd.DataFrame, str]]]]] | None = None
    ):

        super().__init__(reservoirs or [], start_date, current_date, end_date)

        self.left_series = left_series
        self.right_series = right_series
        self.title = title
        self.left_label = left_label
        self.right_label = right_label
        self.value_divisor = value_divisor
        self.annotations = annotations or []

        self.height_inch = 8.0
        self.width_inch = 14.0          # Wider to fit many years
        self.ax = None
        self.fig = None

        # Store originals
        self.original_left_series = [(df.copy(), col, color) for df, col, color in left_series]
        self.original_right_series = [(df.copy(), col, color) for df, col, color in right_series]

    def _get_yearly_stacked_data(self, series: List[Tuple[pd.DataFrame, str, str]]) -> dict:
        """Return {year: [(value, label, color), ...]} for all years"""
        yearly = {}
        all_years = set()

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
                all_years.add(year)

        return yearly, sorted(all_years)

    def create_bar_chart(self, ax):
        """Draw stacked bars for every year 1971–2024 with minimal dead space"""
        if not self.left_series and not self.right_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        ax.clear()

        left_data, years = self._get_yearly_stacked_data(self.left_series)
        right_data, _ = self._get_yearly_stacked_data(self.right_series)

        if not years:
            ax.text(0.5, 0.5, "No valid yearly data", ha='center', va='center', fontsize=14)
            return

        years = [y for y in years if 1971 <= y <= 2024]
        x = np.arange(len(years))

        bar_width = 0.38
        left_x = x - bar_width / 2 - 0.02
        right_x = x + bar_width / 2 + 0.02

        # Plot Left Bars
        for i, year in enumerate(years):
            bottom = 0.0
            for val, label, color in left_data.get(year, []):
                height = val / self.value_divisor
                ax.bar(left_x[i], height, width=bar_width, bottom=bottom,
                       color=color, edgecolor='white', linewidth=0.8, label=label)
                bottom += height

        # Plot Right Bars
        for i, year in enumerate(years):
            bottom = 0.0
            for val, label, color in right_data.get(year, []):
                height = val / self.value_divisor
                ax.bar(right_x[i], height, width=bar_width, bottom=bottom,
                       color=color, edgecolor='white', linewidth=0.8)
                bottom += height

        # Tight X limits (no side dead space)
        ax.set_xlim(x[0] - 0.55, x[-1] + 0.55)

        # === FIXED: Let matplotlib auto-scale Y with only small padding ===
        ax.autoscale(axis='y')
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(0, y_max * 1.06)  # Just 6% padding on top

        # Formatting
        ax.set_xticks(x)
        ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right', fontsize=10)

        ax.set_ylabel("Value (MAF)", fontsize=12)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_title(f"{self.title or 'Annual Comparison'} — 1971 to 2024",
                     fontsize=15, fontweight='bold', pad=20)

        # Legend
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(),
                  loc='upper left', fontsize=9, frameon=True, ncol=2)

        ax.grid(axis='y', linestyle='--', alpha=0.35)

        # Total labels on top
        for i, year in enumerate(years):
            total_left = sum(v[0] for v in left_data.get(year, [])) / self.value_divisor
            total_right = sum(v[0] for v in right_data.get(year, [])) / self.value_divisor

            if total_left > 1:
                ax.text(left_x[i], total_left + 0.12, f"{total_left:.1f}",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')
            if total_right > 1:
                ax.text(right_x[i], total_right + 0.12, f"{total_right:.1f}",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=120)
        self.ax = fig.add_subplot(111)

        self.create_bar_chart(self.ax)

        fig.tight_layout(pad=3.0)
        self.fig = fig
        return fig

    def add_total_annotations(self, annotations, divisor: float = 1_000_000):
        """Same as before"""
        x = annotations[0]
        y = annotations[1]
        annotations_list = annotations[2]

        lines = []
        for label, (df, col) in annotations_list:
            # For full chart we can show latest year or average, etc.
            # Here showing the most recent year as example
            matching = df[df['Year'] == df['Year'].max()]
            value = pd.to_numeric(matching[col].iloc[0], errors='coerce') / divisor \
                    if not matching.empty else 0.0
            lines.append(f"{value:7.2f} MAF {label} (Latest)")

        text_block = "\n".join(lines)

        self.ax.text(
            x=x, y=y, s=text_block,
            transform=self.ax.transAxes,
            fontsize=11,
            fontfamily='monospace',
            fontweight='semibold',
            ha='left', va='top',
            zorder=15
        )