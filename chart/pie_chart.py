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
from typing import List, Optional, Tuple, Union
import numpy as np
from chart.chart import Chart


class PieChart(Chart):
    def __init__(self,
                 data_series: List[Tuple],
                 year: int = 2024,
                 title: str = "",
                 percentage: float = 0.0,
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 reservoirs: List[Reservoir] | None = None,
                 value_divisor: float = 1_000_000,
                 outer_annotations: List | None = None,
                 annotations: List | None = None,
                 radial_lines: List | None = None,
                 left_bar_series: List | None = None,
                 left_bar_ymax: float | None = None,
                 left_bar_ymin: float | None = None,
                 version: float = 0.1):

        super().__init__(reservoirs or [], start_date, current_date, end_date, percentage=percentage)

        self.data_series = []
        self.original_data_series = []
        self.version = version

        for item in data_series:
            if len(item) == 3:
                a, b, c = item
                options = {}
            elif len(item) == 4:
                a, b, c, options = item
                options = options or {}
            else:
                raise ValueError(f"Each item in data_series must have 3 or 4 elements. Got {len(item)}")

            self.data_series.append((a, b, c, options))
            # Store original for safety (best-effort copy when it's a DataFrame)
            if isinstance(a, pd.DataFrame):
                self.original_data_series.append((a.copy(), b, c))
            else:
                self.original_data_series.append((a, b, c))

        self.title = title
        self.value_divisor = value_divisor
        self.year = year
        self.outer_annotations = outer_annotations or []
        self.annotations = annotations or []

        self.radial_lines = radial_lines or []

        # Left bar settings
        self.left_bar_series = left_bar_series or []
        self.left_bar_ymax = left_bar_ymax
        self.left_bar_ymin = left_bar_ymin

        self.height_inch = 7.5
        self.width_inch = 9.8

        self.ax = None
        self.ax_bar = None
        self.ax_pie = None
        self.fig = None

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=120)

        if self.left_bar_series:
            # Very skinny left bar (≈1/4 width)
            gs = fig.add_gridspec(1, 2, width_ratios=[0.22, 4.5], wspace=0.12)
            self.ax_bar = fig.add_subplot(gs[0])
            self.ax_pie = fig.add_subplot(gs[1])
            self.ax = self.ax_pie
        else:
            self.ax_bar = None
            self.ax_pie = None
            self.ax = fig.add_subplot(111)

        self._create_chart()
        fig.tight_layout(pad=2.8)
        self.fig = fig
        return fig

    def _create_chart(self):
        """Internal method to draw everything"""
        if self.ax_bar is not None:
            self._create_left_bar(self.ax_bar)
        if self.ax_pie is not None:
            self._create_pie(self.ax_pie)
        elif self.ax is not None:
            self._create_pie(self.ax)

    def _extract_value(self, item) -> Optional[Tuple[float, str, str, dict]]:
        """
        Extract (value, display_label, color, options) from either:
          - Direct numeric: (value, label, color) or (value, label, color, options)
          - DataFrame year lookup: (df, col, color) or (df, col, color, options)
        Returns None if invalid or non-positive.
        """
        if not item or len(item) < 3:
            return None

        # Direct numeric form
        if isinstance(item[0], (int, float, np.number)):
            val = float(item[0])
            label = str(item[1])
            color = item[2]
            options = item[3] if len(item) >= 4 and isinstance(item[3], dict) else {}
            if pd.notna(val) and val > 0:
                return val, options.get('label', label), color, options
            return None

        # Classic DataFrame form
        df = item[0]
        col = item[1]
        color = item[2]
        options = item[3] if len(item) >= 4 and isinstance(item[3], dict) else {}

        if not isinstance(df, pd.DataFrame) or df.empty or col not in df.columns:
            return None

        matching = df[df['Year'] == self.year]
        if matching.empty:
            return None

        val = pd.to_numeric(matching[col].iloc[0], errors='coerce')
        if pd.isna(val) or val <= 0:
            return None

        display_label = options.get('label', str(col).replace('_', ' '))
        return float(val), display_label, color, options

    def _create_left_bar(self, ax):
        """Tall skinny bar with legend moved down"""
        ax.clear()
        values, labels, colors = [], [], []

        for item in self.left_bar_series:
            extracted = self._extract_value(item)
            if extracted is None:
                continue
            val, display_label, color, _ = extracted
            values.append(val / self.value_divisor)
            labels.append(display_label)
            colors.append(color)

        if not values:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=10)
            return

        bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor='white')

        # === Y limits - now respects both ymin and ymax ===
        if self.left_bar_ymax is not None:
            ymax = self.left_bar_ymax
        else:
            ymax = max(values) * 1.12

        if self.left_bar_ymin is not None:
            ymin = self.left_bar_ymin
        else:
            ymin = 0.0

        ax.set_ylim(ymin, ymax)

        ax.set_ylabel("MAF", fontsize=10)
        ax.set_xticks([])
        ax.set_xlabel("")

        # === LEGEND MOVED DOWN ===
        legend_labels = [lab.replace('_', ' ') for lab in labels]

        ax.legend(bars, legend_labels,
                  loc='lower center',
                  bbox_to_anchor=(0.5, 1.01),
                  fontsize=9.2,
                  frameon=True,
                  fancybox=True,
                  handlelength=1.1,
                  handletextpad=0.5)

        # Value labels
        for bar in bars:
            height = bar.get_height()
            x = bar.get_x() + bar.get_width() / 2.

            if height >= ymax * 0.94:
                label_y = ymax * 0.92
                va = 'top'
            else:
                label_y = height * 1.01
                va = 'bottom'

            ax.text(x, label_y, f'{height:,.1f}',
                    ha='center', va=va, fontsize=9.5, fontweight='bold')

        ax.grid(axis='y', linestyle='--', alpha=0.3)

    def _create_pie(self, ax):
        """Hatch color protected + optional border color (default = white)"""
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        values = []
        labels = []
        colors = []
        hatches = []
        hatch_colors = []
        edgecolors = []

        for item in self.data_series:
            extracted = self._extract_value(item)
            if extracted is None:
                continue
            val, display_label, color, options = extracted
            values.append(val)
            labels.append(display_label)
            colors.append(color)
            hatches.append(options.get('hatch', ''))
            hatch_colors.append(options.get('hatch_color', color))
            edgecolors.append(options.get('edgecolor'))  # None = keep default white

        if not values:
            ax.text(0.5, 0.5, "No valid data for this year", ha='center', va='center', fontsize=14)
            return

        total = sum(values)

        def autopct_format(pct):
            absolute = (pct * total / 100) / self.value_divisor
            if absolute < 0.17:
                return ''
            else:
                return f'{absolute:,.2f}'

        ax.clear()

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct_format,
            startangle=90,
            pctdistance=0.75,
            labeldistance=1.02,
            textprops={'fontsize': 10},
        )

        # Apply properties carefully
        for wedge, hatch, hcolor, edgecolor in zip(wedges, hatches, hatch_colors, edgecolors):
            if hatch:
                wedge.set_hatch(hatch)
                wedge.set_edgecolor(hcolor)  # Protect pattern color

            # Only override border color if user specified it
            if edgecolor is not None:
                wedge.set_edgecolor(edgecolor)
                wedge.set_linewidth(2.0)

        # Styling
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_color('black')

        for text in texts:
            text.set_fontsize(9.5)
            text.set_fontweight('semibold')

        ax.set_title(f"{self.title or 'Distribution'} — {self.year}  v{self.version}",
                     fontsize=15, fontweight='bold', pad=15)
        ax.axis('equal')

        # === Dynamic Radial Lines (cumulative) ===
        if self.radial_lines:
            cumulative = 0.0
            for item in self.radial_lines:
                extracted = self._extract_value(item)
                if extracted is None:
                    continue
                val, _, color, _ = extracted
                cumulative += val
                self.draw_radial_line(
                    ax,
                    value=cumulative,
                    color=color,
                    linestyle='-',
                    linewidth=2.5
                )

        for ann in self.annotations:
            self.add_total_annotations(ann)

        if self.outer_annotations:
            radius = 1.25
            for name, degrees, source in self.outer_annotations:
                extracted = self._extract_value(source if isinstance(source, tuple) else (source,))
                # Support both (df, col) and (value, label, color) style, or raw number
                if isinstance(source, (int, float, np.number)):
                    val = float(source)
                else:
                    extracted = self._extract_value(source)
                    val = extracted[0] if extracted else None

                if val is not None and pd.notna(val) and val > 0:
                    percentage = (val / total * 100) if total > 0 else 0
                    formatted = f"{val / self.value_divisor:,.2f}"
                    rad = np.deg2rad(degrees)
                    x = radius * np.cos(rad)
                    y = radius * np.sin(rad)
                    ha = 'left' if -90 < (degrees % 360) < 90 else 'right'
                    ax.text(x, y, f"{name}\n{formatted} MAF   {percentage:.1f}%",
                            ha=ha, va='center', fontsize=9.5, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.45", facecolor="white", alpha=0.9))

    def draw_radial_line(self, ax, value: float,
                         color: str = 'black',
                         linewidth: float = 3.0,
                         linestyle: str = '--',
                         alpha: float = 0.95):
        """
        Draw a radial line from center to the edge of the pie at the given value.
        """
        # Calculate total for current year / series
        total = 0.0
        for item in self.data_series:
            extracted = self._extract_value(item)
            if extracted is not None:
                total += extracted[0]

        if total <= 0:
            return

        # Calculate angle (matplotlib pie starts at 90° and goes counter-clockwise)
        fraction = value / total
        angle_deg = 90 - (fraction * 360)  # 90° is the starting point

        rad = np.deg2rad(angle_deg)
        x = np.cos(rad)
        y = np.sin(rad)

        # Draw line from center (0,0) to edge (x,y)
        ax.plot([0, x], [0, y],
                color=color,
                linewidth=linewidth,
                linestyle=linestyle,
                alpha=alpha,
                zorder=10)  # on top of the pie

    def draw_radial_line_by_angle(self, ax, angle_deg: float,
                                  color: str = 'red',
                                  linewidth: float = 3.0,
                                  linestyle: str = '--',
                                  alpha: float = 0.95):
        """
        Draw radial line from center to edge at a specific angle in degrees.

        angle_deg:
            0°   = right side
           90°   = top
          180°   = left
          270°   = bottom
        """
        rad = np.deg2rad(angle_deg)
        x = np.cos(rad)
        y = np.sin(rad)

        ax.plot([0, x], [0, y], color=color, linewidth=linewidth,
                linestyle=linestyle, alpha=alpha, zorder=10)

    def update_for_year(self, year: int):
        self.year = year
        self._create_chart()
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas.draw()
            self.canvas.Refresh()

    def add_total_annotations(self, annotations, divisor=1_000_000):
        """Draw annotation table with a nice bordered box.

        Each item in annotations_list can be:
          - (label, (df, col))                  → default black
          - (label, (df, col), color)           → custom color for that line
          - (label, numeric_value)              → direct numeric (no year)
          - (label, numeric_value, color)
        """
        if not annotations or len(annotations) < 3:
            return

        x = annotations[0]
        y = annotations[1]
        annotations_list = annotations[2]

        if not annotations_list:
            return

        # Get total value (last item) for percentage calculation
        last_item = annotations_list[-1]
        if len(last_item) >= 2:
            source = last_item[1]
            if isinstance(source, (int, float, np.number)):
                total_value = float(source)
            else:
                extracted = self._extract_value(source if isinstance(source, tuple) else (source,))
                total_value = extracted[0] if extracted else 0.0
        else:
            total_value = 0.0

        # Build the text lines with individual colors
        text_lines = []
        colors = []

        for item in annotations_list:
            if len(item) >= 2:
                label = item[0]
                source = item[1]
                color = item[2] if len(item) >= 3 else 'black'

                if isinstance(source, (int, float, np.number)):
                    value = float(source)
                else:
                    extracted = self._extract_value(source if isinstance(source, tuple) else (source,))
                    value = extracted[0] if extracted else 0.0

                maf = value / divisor

                if total_value > 0:
                    percentage = (value / total_value) * 100
                    line = f"{maf:5.2f} MAF {percentage:5.1f}% {label}"
                else:
                    line = f"{maf:5.2f} MAF {label}"

                text_lines.append(line)
                colors.append(color)

        # Draw each line separately so we can color them individually
        line_height = 0.028
        for i, (line, color) in enumerate(zip(text_lines, colors)):
            self.ax.text(
                x=x,
                y=y - (i * line_height),
                s=line,
                transform=self.ax.transAxes,
                fontsize=11,
                fontfamily='monospace',
                fontweight='semibold',
                ha='left',
                va='top',
                color=color,
                zorder=15,
            )

        # Draw a single box around the whole block
        if text_lines:
            from matplotlib.patches import Rectangle
            box_height = len(text_lines) * line_height + 0.02
            box_width = 0.30
            left_pad = 0.005

            self.ax.add_patch(
                Rectangle(
                    (x - left_pad, y - box_height + 0.01),
                    box_width, box_height,
                    transform=self.ax.transAxes,
                    facecolor='white',
                    edgecolor='#aaaaaa',
                    alpha=0.95,
                    linewidth=1.1,
                    zorder=14,
                    clip_on=False
                )
            )