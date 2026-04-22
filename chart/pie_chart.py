"""
Copyright (c) 2026 Ed Millard

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
from datetime import date
from typing import List, Optional, Tuple
import numpy as np
from chart.chart import Chart


class PieChart(Chart):
    def __init__(self,
                 data_series: List[Tuple[pd.DataFrame, str, str]],
                 year: int = 2024,
                 title: str = "",
                 percentage:float = 0.0,
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None,
                 value_divisor: float = 1_000_000,
                 outer_annotations: List[Tuple[str, float, Tuple[pd.DataFrame, str]]] | None = None,
                 annotations: List[Tuple[float, float, List[Tuple[str, Tuple[pd.DataFrame, str]]]]] | None = None
    ):

        super().__init__(reservoirs or [], start_date, current_date, end_date, percentage=percentage)

        self.data_series = data_series
        self.title = title
        self.value_divisor = value_divisor
        self.year = year
        self.outer_annotations = outer_annotations or []
        self.annotations = annotations or []

        self.height_inch = 7.5
        self.width_inch = 8.5
        self.ax = None
        self.fig = None

        # Store original full DataFrames (important for animation)
        self.original_data_series = [ (df.copy(), col, color) for df, col, color in data_series ]

    def create_pie_chart(self, ax):
        """Core pie drawing logic - used by both initial creation and updates"""
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        values = []
        labels = []
        colors = []

        for df, col, color in self.data_series:
            if df.empty or col not in df.columns:
                continue

            # Find value for current year
            matching = df[df['Year'] == self.year]
            if not matching.empty:
                val = pd.to_numeric(matching[col].iloc[0], errors='coerce')
                if pd.notna(val) and val > 0:
                    values.append(val)
                    labels.append(col.replace('_', ' '))
                    colors.append(color)

        if not values:
            ax.text(0.5, 0.5, "No valid data for this year", ha='center', va='center', fontsize=14)
            return

        total = sum(values)
        total_maf = total / self.value_divisor

        def autopct_format(pct):
            absolute = (pct * total / 100) / self.value_divisor
            return f'{pct:.1f}%\n{absolute:,.2f}'

        ax.clear()   # ← Important for redraw

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct_format,
            startangle=90,
            pctdistance=0.75,
            labeldistance=1.02,
            textprops={'fontsize': 10},
            wedgeprops=dict(linewidth=1.5, edgecolor='white')
        )

        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_color('black')

        for text in texts:
            text.set_fontsize(9.5)
            text.set_fontweight('semibold')

        main_title = self.title or "Distribution"
        ax.set_title(f"{main_title} — {self.year}", fontsize=15, fontweight='bold', pad=15)
        ax.axis('equal')

        # Annotations
        for ann in self.annotations:
            self.add_total_annotations(ann)

        # Outer annotations (if any)
        if self.outer_annotations:
            radius = 1.25
            for name, degrees, (df, col) in self.outer_annotations:
                matching = df[df['Year'] == self.year]
                if not matching.empty:
                    val = pd.to_numeric(matching[col].iloc[0], errors='coerce')
                    if pd.notna(val) and val > 0:
                        percentage = (val / total * 100) if total > 0 else 0
                        formatted = f"{val / self.value_divisor:,.2f}"
                        rad = np.deg2rad(degrees)
                        x = radius * np.cos(rad)
                        y = radius * np.sin(rad)
                        ha = 'left' if -90 < (degrees % 360) < 90 else 'right'

                        ax.text(x, y, f"{name}\n{formatted} MAF   {percentage:.1f}%",
                                ha=ha, va='center', fontsize=9.5, fontweight='bold',
                                bbox=dict(boxstyle="round,pad=0.45", facecolor="white", alpha=0.9))

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=120)
        self.ax = fig.add_subplot(111)

        self.create_pie_chart(self.ax)

        fig.tight_layout(pad=2.5)
        self.fig = fig
        return fig

    def update_for_year(self, year: int):
        """This is the method called by the timer — now fully working"""
        self.year = year

        if self.ax is None:
            return

        self.create_pie_chart(self.ax)        # Redraw everything

        # Refresh the canvas if it exists (wx + matplotlib)
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas.draw()
            self.canvas.Refresh()

    def add_total_annotations(self, annotations, divisor=1_000_000):
        """Your existing annotation method (unchanged)"""
        lines = []
        x = annotations[0]
        y = annotations[1]
        annotations_list = annotations[2]

        for label, (df, col) in annotations_list:
            matching = df[df['Year'] == self.year]
            value = pd.to_numeric(matching[col].iloc[0], errors='coerce') / divisor if not matching.empty else 0.0
            lines.append(f"{value:7.2f} MAF {label}")

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