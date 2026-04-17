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
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None,
                 value_divisor: float = 1_000_000,
                 outer_annotations: List[Tuple[str, float, Tuple[pd.DataFrame, str]]] | None = None):

        super().__init__(reservoirs or [], start_date, current_date, end_date)

        self.data_series = data_series
        self.title = title
        self.value_divisor = value_divisor
        self.year = year
        self.outer_annotations = outer_annotations or []   # (name, degrees, (df, col))

        self.height_inch = 7.5
        self.width_inch = 8.5

        # Normalize main data series
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)

    def create_pie_chart(self, ax):
        """Pie chart with closer wedge labels + outer annotations"""
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        values = []
        labels = []
        colors = []

        for df, col, color in self.data_series:
            if df.empty or col not in df.columns:
                continue

            matching = df['Year'] == self.year
            if matching.any():
                row_idx = matching.idxmax()
                val = pd.to_numeric(df[col].iloc[row_idx], errors='coerce')
                if pd.notna(val) and val > 0:
                    values.append(val)
                    labels.append(col.replace('_', ' '))
                    colors.append(color)

        if not values:
            ax.text(0.5, 0.5, "No valid data", ha='center', va='center', fontsize=14)
            return

        total = sum(values)
        total_maf = total / self.value_divisor

        def autopct_format(pct):
            absolute = (pct * total / 100) / self.value_divisor
            return f'{pct:.1f}%\n{absolute:,.2f}'

        # Create the pie
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct_format,
            startangle=90,
            pctdistance=0.75,
            labeldistance=1.02,          # ← Only change I made (wedge labels closer)
            textprops={'fontsize': 10},
            wedgeprops=dict(linewidth=1.5, edgecolor='white')
        )

        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_color('black')

        for text in texts:               # wedge labels styling
            text.set_fontsize(9.5)
            text.set_fontweight('semibold')

        # ==================== TITLE + SUBTITLE ====================
        main_title = self.title or "Distribution"
        ax.set_title(main_title, fontsize=15, fontweight='bold', pad=10)

        subtitle = f"{self.year}     Total: {total_maf:,.2f} MAF"
        ax.text(0.85, 1.0, subtitle,
                transform=ax.transAxes,
                ha='left', va='top',
                fontsize=12,
                fontweight='semibold',
                color='darkblue')

        ax.axis('equal')

        # ====================== OUTER ANNOTATIONS (Unchanged) ======================
        if self.outer_annotations:
            radius = 1.25

            for name, degrees, data_tuple in self.outer_annotations:
                df_ann, col_ann = data_tuple

                val = None
                if not df_ann.empty and col_ann in df_ann.columns:
                    matching = df_ann['Year'] == self.year
                    if matching.any():
                        row_idx = matching.idxmax()
                        val = pd.to_numeric(df_ann[col_ann].iloc[row_idx], errors='coerce')

                if pd.isna(val) or val <= 0:
                    continue

                percentage = (val / total * 100) if total > 0 else 0
                formatted_value = f"{val / self.value_divisor:,.2f}"

                rad = np.deg2rad(degrees)
                x = radius * np.cos(rad)
                y = radius * np.sin(rad)

                ha = 'left' if -90 < (degrees % 360) < 90 else 'right'
                va = 'center'

                annotation_text = f"{name}\n{formatted_value} MAF   {percentage:.1f}%"

                ax.text(
                    x, y,
                    annotation_text,
                    ha=ha,
                    va=va,
                    fontsize=9.5,
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.45",
                              facecolor="white",
                              alpha=0.9,
                              edgecolor='gray')
                )

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=120)
        ax = fig.add_subplot(111)

        self.create_pie_chart(ax)

        fig.tight_layout(pad=2.5)
        self.fig = fig
        return fig

    # update_for_year and update_data methods remain unchanged...
    def update_for_year(self, year: int) -> bool:
        updated = False
        for i, (df, col, color) in enumerate(self.data_series):
            if df.empty or col not in df.columns:
                continue

            if 'Date' in df.columns:
                df['Year'] = pd.to_datetime(df['Date']).dt.year
                row = df[df['Year'] == year]
            elif 'Year' in df.columns:
                row = df[df['Year'] == year]
            else:
                continue

            if not row.empty:
                self.data_series[i] = (row.copy(), col, color)
                updated = True

        return updated

    def update_data(self, new_data_series: List[Tuple[pd.DataFrame, str, str]]):
        self.data_series = new_data_series
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)