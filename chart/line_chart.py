from reservoirs.reservoir import Reservoir
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.cm as cm
import pandas as pd
from datetime import date
from typing import List, Optional, Tuple, Literal, Union
from chart.chart import Chart


class LineChart(Chart):
    """
    Line chart for multiple time series with short two-digit year X-axis.

    Enhanced features:
    - custom_year_start + overlay_years: Overlay multiple years on one seasonal cycle (month/day only).
      Excellent for water years (Oct 1 start) or calendar years.
    - color_by_year=True: Each custom year gets its own colored line (great for 10-30+ years).
    - year_colors: Optional list of colors. Auto-generates nice viridis colormap if omitted.
    """

    def __init__(self,
                 data_series: List[Union[
                     Tuple[pd.DataFrame, str, str],
                     Tuple[pd.DataFrame, str, str, str]
                 ]],
                 percentage: float = 0.0,
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 show_x_labels: bool = True,
                 y_label: str = "",
                 y_units: Literal['MAF', 'TAF', 'AF', 'FT', 'CFS', '°F', '°C', 'in', 'ft', 'mm', '%'] = 'MAF',
                 y_divisor: float | None = None,
                 y_max: Optional[float] = None,
                 y_min: Optional[float] = None,
                 # === NEW OVERLAY / COLOR-BY-YEAR PARAMETERS ===
                 custom_year_start: Optional[Tuple[int, int]] = None,
                 overlay_years: bool = False,
                 color_by_year: bool = False,
                 year_colors: Optional[List[str]] = None,
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

        if y_divisor is not None:
            self.y_divisor = y_divisor
        else:
            self.y_divisor = self._get_divisor_for_units(y_units)

        self.height_inch = 5.5
        self.width_inch = 10.5

        # === NEW SETTINGS ===
        self.custom_year_start = custom_year_start
        self.overlay_years = overlay_years or (custom_year_start is not None)
        self.color_by_year = color_by_year and self.overlay_years
        self.year_colors = year_colors
        self.overlay_date_map = {}

        # === Data normalization (original) ===
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

        # Apply overlay normalization if requested
        if self.overlay_years and self.custom_year_start:
            self._normalize_to_overlay_dates()

    # ==================== NEW CORE METHOD ====================
    def _normalize_to_overlay_dates(self):
        """Map all data to a single seasonal cycle using the first custom year's date structure.
        Optionally splits into per-year segments when color_by_year=True.
        """
        if not self.data_series or not self.custom_year_start:
            return

        year_start_month, year_start_day = self.custom_year_start

        # Find earliest date to determine reference custom year
        all_dates = []
        for item in self.data_series:
            df = item[0]
            if 'Date' in df.columns and not df.empty:
                all_dates.extend(df['Date'].dropna().tolist())

        if not all_dates:
            return

        earliest = min(all_dates)
        if (earliest.month > year_start_month or
            (earliest.month == year_start_month and earliest.day >= year_start_day)):
            first_cy_year = earliest.year
        else:
            first_cy_year = earliest.year - 1

        # Full reference date range for the first custom year (handles leap years automatically)
        try:
            cy_start = pd.Timestamp(year=first_cy_year, month=year_start_month, day=year_start_day)
        except ValueError:
            cy_start = pd.Timestamp(year=first_cy_year, month=year_start_month, day=year_start_day - 1)

        cy_end = cy_start + pd.DateOffset(years=1) - pd.Timedelta(days=1)
        reference_dates = pd.date_range(start=cy_start, end=cy_end, freq='D')
        self.overlay_date_map = {(d.month, d.day): d for d in reference_dates}

        # Auto-generate colors if color_by_year and none provided
        if self.color_by_year and not self.year_colors:
            cmap = cm.get_cmap('viridis')
            self.year_colors = [cmap(i / 40) for i in range(40)]  # generous for many years

        # Process each series
        new_series = []
        color_idx = 0

        for item in self.data_series:
            if len(item) == 4:
                df, col, base_color, linestyle = item
            else:
                df, col, color = item
                linestyle = None
                base_color = color

            if df is None or df.empty or 'Date' not in df.columns:
                new_series.append((df, col, base_color))
                continue

            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Compute custom year for grouping
            df['custom_year'] = df['Date'].apply(
                lambda d: d.year if (d.month > year_start_month or
                                   (d.month == year_start_month and d.day >= year_start_day))
                else d.year - 1
            )

            if self.color_by_year:
                # Split into one segment per custom year
                for cy, group in df.groupby('custom_year'):
                    if group.empty:
                        continue
                    g = group.copy()
                    g['Date'] = g['Date'].apply(
                        lambda d: self.overlay_date_map.get((d.month, d.day), pd.NaT)
                    )
                    g = g.dropna(subset=['Date'])
                    g['_year'] = cy   # internal for nice legend labels

                    if self.year_colors:
                        color = self.year_colors[color_idx % len(self.year_colors)]
                        color_idx += 1
                    else:
                        color = base_color

                    # Always 3-tuple for full compatibility with parent Chart class
                    new_series.append((g, col, color))
            else:
                # Standard overlay - all years on one line
                df['Date'] = df['Date'].apply(
                    lambda d: self.overlay_date_map.get((d.month, d.day), pd.NaT)
                )
                df = df.dropna(subset=['Date'])
                new_series.append((df, col, base_color))

        self.data_series = new_series

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
        all_values = []

        for item in self.data_series:
            # Support both 3-tuple and 4-tuple
            if len(item) == 4:
                df, col, color, linestyle = item
            else:
                df, col, color = item
                linestyle = None

            if df.empty or col not in df.columns:
                continue

            df[col] = pd.to_numeric(df[col], errors='coerce')
            valid = df[col].dropna()

            all_dates.extend(df['Date'].dropna().tolist())
            all_values.extend(valid.tolist())

            # Nice label for color-by-year mode
            if self.color_by_year and '_year' in df.columns:
                year_val = int(df['_year'].iloc[0])
                plot_label = f"{year_val} {col.replace('_', ' ')}"
            else:
                plot_label = col.replace('_', ' ')

            ax.plot(df['Date'], df[col],
                    label=plot_label,
                    linewidth=1.7 if self.color_by_year else 2.2,
                    color=color,
                    linestyle=linestyle or '-',
                    alpha=0.82 if self.color_by_year else 1.0)

        if not all_dates or not all_values:
            return

        # ==================== X-AXIS ====================
        if self.overlay_years and self.overlay_date_map:
            ref_dates = list(self.overlay_date_map.values())
            ax.set_xlim(min(ref_dates), max(ref_dates))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        else:
            data_min = min(all_dates)
            data_max = max(all_dates)
            x_start = self.start_date if self.start_date is not None else data_min
            x_end = self.end_date if self.end_date is not None else data_max
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

        # Tick styling
        ax.tick_params(axis='x', which='minor', length=3, width=0.7, labelsize=8.5, pad=2)
        ax.tick_params(axis='x', which='major', length=6, width=1.2, labelsize=10, pad=4)

        if not self.show_x_labels:
            ax.set_xticklabels([])

        if self.title and str(self.title).strip():
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=6)

        # Grid
        ax.grid(True, which='major', linestyle='-', linewidth=1.0, color='gray', alpha=1, zorder=0)
        ax.grid(True, which='minor', linestyle='--', linewidth=0.7, color='gray', alpha=0.75, zorder=0)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)
        ax.axhline(y=0, color='black', linewidth=1.0, linestyle='-', alpha=1, zorder=3)

        self.setup_yaxis(ax)

        # ==================== Y-LIMITS - TIGHTER AUTO SCALE ====================
        data_min = min(all_values)
        data_max = max(all_values)
        data_range = data_max - data_min
        pad = max(data_range * 0.04, 1.5)  # Reduced padding (4%)

        auto_min = data_min - pad
        auto_max = data_max + pad

        # Temperature-friendly floor
        if self.y_units in ('°F', '°C'):
            auto_min = max(auto_min, -5)

        # Honor explicit limits, otherwise use calculated padded range
        if self.y_max is not None and self.y_min is not None:
            ax.set_ylim(self.y_min, self.y_max)
        elif self.y_max is not None:
            ax.set_ylim(auto_min, self.y_max)
        elif self.y_min is not None:
            ax.set_ylim(self.y_min, auto_max)
        else:
            # Default: clean padded auto-scale
            ax.set_ylim(auto_min, auto_max)

        ax.legend(fontsize=9 if self.color_by_year else 10.5, loc='best',
                  ncol=2 if self.color_by_year else 1)

    # ==================== HELPER (full original) ====================
    def _get_divisor_for_units(self, units: str) -> float:
        """Extended divisor logic (identical to your original)."""
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
            '%': 1,
        }
        return unit_map.get(units, 1.0)