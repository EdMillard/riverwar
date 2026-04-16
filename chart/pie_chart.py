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
from chart.chart import Chart


class PieChart(Chart):
    def __init__(self,
                 data_series: List[Tuple[pd.DataFrame, str, str]],
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None):

        super().__init__(reservoirs or [], start_date, current_date, end_date)

        self.data_series = data_series
        self.title = title

        self.height_inch = 7.0
        self.width_inch = 8.0

        self.year = 2024

        # Normalize DataFrames
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)

    def create_figure(
            self,
            width_inch: Optional[float] = None,
            height_inch: Optional[float] = None
    ) -> Optional[Figure]:

        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=110)
        ax = fig.add_subplot(111)

        self.create_pie_chart(ax)

        fig.tight_layout(pad=2.0)
        self.fig = fig
        return fig

    def create_pie_chart(self, ax):
        """Create the pie chart using current data"""
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        values = []
        labels = []
        colors = []

        for df, col, color in self.data_series:
            matching = df['Year'] == self.year
            row_for_year = matching[matching].index[0]
            if df.empty or col not in df.columns:
                print(f'create_pie_chart column not found {col}')
                continue

            val = pd.to_numeric(df[col], errors='coerce').iloc[row_for_year]  # Current value (will be updated by year)
            if pd.notna(val):
                values.append(val)
                labels.append(col.replace('_', ' '))
                colors.append(color)

        if not values:
            ax.text(0.5, 0.5, "No valid data", ha='center', va='center', fontsize=14)
            return

        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11}
        )

        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_fontweight('bold')

        ax.set_title(self.title or "Distribution", fontsize=14, fontweight='bold', pad=20)
        ax.axis('equal')  # Equal aspect ratio ensures pie is circular

    def update_for_year(self, year: int) -> bool:
        """
        Updates the data_series to use values from the specified year.
        Returns True if successful.
        Call this before redrawing the figure for animation.
        """
        updated = False
        for i, (df, col, color) in enumerate(self.data_series):
            if df.empty or col not in df.columns:
                continue

            # Try to find row for this year
            if 'Date' in df.columns:
                df['Year'] = pd.to_datetime(df['Date']).dt.year
                row = df[df['Year'] == year]
            elif 'Year' in df.columns:
                row = df[df['Year'] == year]
            else:
                continue

            if not row.empty:
                # Update the dataframe in place with only this year's row
                self.data_series[i] = (row.copy(), col, color)
                updated = True

        return updated

    def update_data(self, new_data_series: List[Tuple[pd.DataFrame, str, str]]):
        """Update with new list of tuples"""
        self.data_series = new_data_series
        # Re-normalize
        for i, (df, col, color) in enumerate(self.data_series):
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                self.data_series[i] = (df.sort_values('Date').reset_index(drop=True), col, color)