from reservoirs.reservoir import Reservoir
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import pandas as pd
from datetime import date
from typing import List, Optional, Tuple, Literal, Union
from chart.chart import Chart


class LineChart(Chart):
    """
    Line chart for multiple time series with short two-digit year X-axis.
    """
    def __init__(self,
                 data_series: List[Union[
                     Tuple[pd.DataFrame, str, str],  # df, column, color
                     Tuple[pd.DataFrame, str, str, str]  # df, column, color, linestyle
                 ]],
                 percentage: float = 0.0,
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 show_x_labels: bool = True,
                 y_label: str = "",
                 y_units: Literal['MAF', 'TAF', 'AF', 'FT', 'CFS', '°F', '°C', 'in', 'ft', 'mm'] = 'MAF',
                 y_divisor: float | None = None,
                 y_max: Optional[float] = None,
                 y_min: Optional[float] = None
                 ):

        super().__init__(start_date, current_date, end_date, y_divisor=y_divisor, y_units=y_units, percentage=percentage)

        self.data_series = data_series
        self.title = title
        self.show_x_labels = show_x_labels
        self.y_label = y_label.strip()
        self.y_units = y_units
        self.y_max = y_max
        self.y_min = y_min
        self.ax = None

        # Auto-determine divisor (extended for new units)
        if y_divisor is not None:
            self.y_divisor = y_divisor
        else:
            self.y_divisor = self._get_divisor_for_units(y_units)

        self.height_inch = 5.5
        self.width_inch = 10.5

        # === Data normalization (unchanged) ===
        normalized_series = []
        for item in self.data_series:
            if len(item) == 4:
                df, col, color, linestyle = item
            else:
                df, col, color = item
                linestyle = None

            if df is None or df.empty:
                continue

            df = df.copy()

            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.sort_values('Date').reset_index(drop=True)

            if linestyle is not None:
                normalized_series.append((df, col, color, linestyle))
            else:
                normalized_series.append((df, col, color))

        self.data_series = normalized_series

    # ==================== SETTERS ====================
    def set_start_date(self, start_date: date | None):
        self.start_date = start_date

    def set_end_date(self, end_date: date | None):
        self.end_date = end_date

    def set_current_date(self, current_date: date | None):
        self.current_date = current_date

    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=110)
        self.ax = fig.add_subplot(111)

        self.create_line_chart(self.ax)

        left_margin = 0.05
        right_margin = 0.98
        top_margin = 0.90 if self.title and self.title.strip() else 0.99
        bottom_margin = 0.12 if self.show_x_labels else 0.03

        fig.tight_layout(pad=1.0)
        fig.subplots_adjust(left=left_margin, right=right_margin,
                            bottom=bottom_margin, top=top_margin)

        self.fig = fig
        return fig

    def create_line_chart(self, ax):
        if not self.data_series:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            return

        all_dates = []
        for item in self.data_series:
            if len(item) == 4:
                df, col, color, linestyle = item
            else:
                df, col, color = item
                linestyle = '-'

            if df.empty or col not in df.columns:
                continue
            df[col] = pd.to_numeric(df[col], errors='coerce')
            all_dates.extend(df['Date'])

            ax.plot(df['Date'], df[col],
                    label=col.replace('_', ' '),
                    linewidth=2.2,
                    color=color,
                    linestyle=linestyle)

        if not all_dates:
            return

        data_min = min(all_dates)
        data_max = max(all_dates)

        x_start = self.start_date if self.start_date is not None else data_min
        x_end = self.end_date if self.end_date is not None else data_max

        if self.title and str(self.title).strip():
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=6)   # ← smaller pad

        # ==================== X-AXIS ====================
        ax.set_xlim(x_start, x_end)

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%y'))

        if self.show_x_labels:
            years_span = (x_end - x_start).days / 365.25
            if years_span < 10:
                ax.xaxis.set_minor_locator(mdates.MonthLocator())

                def month_first_letter(x, pos):
                    return mdates.DateFormatter('%b')(x, pos)[0]

                ax.xaxis.set_minor_formatter(month_first_letter)

        ax.tick_params(axis='x', which='minor', length=3, width=0.7, labelsize=8.5, rotation=0, pad=2)
        ax.tick_params(axis='x', which='major', length=6, width=1.2, labelsize=10, pad=4)

        if not self.show_x_labels:
            ax.set_xticklabels([])

        # ==================== GRID & Y-AXIS ====================
        ax.grid(True, which='major', linestyle='-', linewidth=1.0, color='gray', alpha=1, zorder=0)
        ax.grid(True, which='minor', linestyle='--', linewidth=0.7, color='gray', alpha=0.75, zorder=0)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)

        ax.axhline(y=0, color='black', linewidth=1.0, linestyle='-', alpha=1, zorder=3)

        self.setup_yaxis(ax)

        if self.y_max is not None and self.y_min is not None:
            ax.set_ylim(self.y_min, self.y_max)
        elif self.y_max is not None:
            ax.set_ylim(ymax=self.y_max)
        elif self.y_min is not None:
            ax.set_ylim(ymin=self.y_min)

        ax.legend(fontsize=10.5, loc='best')

    # ==================== HELPER FOR NEW UNITS ====================
    def _get_divisor_for_units(self, units: str) -> float:
        """Extended divisor logic (you can also put this in the parent Chart class)."""
        unit_map = {
            'MAF': 1_000_000,
            'TAF': 1_000,
            'AF': 1,
            'FT': 1,
            'ft': 1,
            'CFS': 1,
            '°F': 1,
            '°C': 1,
            'in': 1,
            'mm': 1,
        }
        return unit_map.get(units, 1.0)