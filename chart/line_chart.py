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
import matplotlib.dates as mdates
import matplotlib.cm as cm
import math
from matplotlib.ticker import MultipleLocator, FuncFormatter
import pandas as pd
from datetime import date
from typing import List, Optional, Tuple, Literal, Union
from chart.chart import Chart


class TimeSeries:
    """Container for a single time series used by LineChart.

    Accepts either direct construction or conversion from the old tuple formats.
    """
    def __init__(self,
                 df: pd.DataFrame,
                 col: str,
                 color: str,
                 linestyle: Optional[str] = None,
                 do_stack: bool = True,
                 linewidth: float = 2.0,
                 label: Optional[str] = None):
        self.df = df
        self.col = col
        self.color = color
        self.linestyle = linestyle
        self.do_stack = do_stack
        self.linewidth = linewidth
        self.label = label if label is not None else col.replace('_', ' ')

    @classmethod
    def from_tuple(cls, item: Union[tuple, 'TimeSeries']) -> 'TimeSeries':
        """Convert old-style tuple (or already a TimeSeries) into a TimeSeries."""
        if isinstance(item, TimeSeries):
            return item

        if not isinstance(item, tuple):
            raise TypeError(f"Expected tuple or TimeSeries, got {type(item)}")

        n = len(item)
        if n == 3:
            df, col, color = item
            return cls(df, col, color)
        elif n == 4:
            df, col, color, linestyle = item
            return cls(df, col, color, linestyle=linestyle)
        elif n == 5:
            df, col, color, linestyle, do_stack = item
            return cls(df, col, color, linestyle=linestyle, do_stack=do_stack)
        elif n == 6:
            df, col, color, linestyle, do_stack, linewidth = item
            return cls(df, col, color, linestyle=linestyle, do_stack=do_stack, linewidth=linewidth)
        else:
            raise ValueError(f"Unsupported tuple length {n} for TimeSeries")

    def __repr__(self):
        return (f"TimeSeries(col={self.col!r}, color={self.color!r}, "
                f"linestyle={self.linestyle!r}, do_stack={self.do_stack}, "
                f"linewidth={self.linewidth})")


class LineChart(Chart):
    """
    Line chart for multiple time series with short two-digit year X-axis.

    Enhanced features:
    - custom_year_start + overlay_years: Overlay multiple years on one seasonal cycle (month/day only).
      Excellent for water years (Oct 1 start) or calendar years.
    - color_by_year=True: Each custom year gets its own colored line (great for 10-30+ years).
    - year_colors: Optional list of colors. Auto-generates nice viridis colormap if omitted.
    - stacked: Stacked area chart support.
    - Accepts either old-style tuples or TimeSeries objects.
    """

    def __init__(self,
                 data_series: List[Union[tuple, TimeSeries]],
                 percentage: float = 0.0,
                 title: str = "",
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None,
                 show_x_labels: bool = True,
                 show_right_labels: bool = False,
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
                 stacked: bool = False,
                 compact_legend: bool = False,
                 legend_variables: Optional[List[Tuple[str, str]]] = None,
                 legend_studies: Optional[List[Tuple[str, str]]] = None,
                 ):

        super().__init__(start_date, current_date, end_date, y_divisor=y_divisor, y_units=y_units,
                         percentage=percentage)

        self.title = title
        self.show_x_labels = show_x_labels
        self.show_right_labels = show_right_labels
        self.y_label = y_label.strip()
        self.y_units = y_units
        self.y_max = y_max
        self.y_min = y_min
        self.ax = None
        self.stacked = stacked

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

        self.compact_legend = compact_legend
        self.legend_variables = legend_variables or []
        self.legend_studies = legend_studies or []

        # === Data normalization (accepts tuples or TimeSeries) ===
        self.data_series: list[TimeSeries] = []
        for item in data_series:
            ts = TimeSeries.from_tuple(item)
            if ts.df is None or ts.df.empty:
                continue

            df = ts.df.copy()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.sort_values('Date').reset_index(drop=True)
            ts.df = df
            self.data_series.append(ts)

        # Apply overlay normalization if requested
        if self.overlay_years and self.custom_year_start:
            self._normalize_to_overlay_dates()

    def _normalize_to_overlay_dates(self):
        """Map all data to a single seasonal cycle using the first custom year's date structure.
        Optionally splits into per-year segments when color_by_year=True.
        """
        if not self.data_series or not self.custom_year_start:
            return

        year_start_month, year_start_day = self.custom_year_start

        # Find earliest date to determine reference custom year
        all_dates = []
        for ts in self.data_series:
            if 'Date' in ts.df.columns and not ts.df.empty:
                all_dates.extend(ts.df['Date'].dropna().tolist())

        if not all_dates:
            return

        earliest = min(all_dates)
        if (earliest.month > year_start_month or
            (earliest.month == year_start_month and earliest.day >= year_start_day)):
            first_cy_year = earliest.year
        else:
            first_cy_year = earliest.year - 1

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
            self.year_colors = [cmap(i / 40) for i in range(40)]

        new_series: list[TimeSeries] = []
        color_idx = 0

        for ts in self.data_series:
            df = ts.df.copy()
            if 'Date' not in df.columns:
                new_series.append(ts)
                continue

            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Compute custom year for grouping
            df['custom_year'] = df['Date'].apply(
                lambda d: d.year if (d.month > year_start_month or
                                     (d.month == year_start_month and d.day >= year_start_day))
                else d.year - 1
            )

            if self.color_by_year:
                for cy, group in df.groupby('custom_year'):
                    if group.empty:
                        continue
                    g = group.copy()
                    g['Date'] = g['Date'].apply(
                        lambda d: self.overlay_date_map.get((d.month, d.day), pd.NaT)
                    )
                    g = g.dropna(subset=['Date'])
                    g['_year'] = cy

                    color = ts.color
                    if self.year_colors:
                        color = self.year_colors[color_idx % len(self.year_colors)]
                        color_idx += 1

                    new_ts = TimeSeries(
                        df=g,
                        col=ts.col,
                        color=color,
                        linestyle=ts.linestyle,
                        do_stack=ts.do_stack,
                        linewidth=ts.linewidth,
                        label=f"{int(cy)} {ts.label}"
                    )
                    new_series.append(new_ts)
            else:
                # Standard overlay - all years on one line
                df['Date'] = df['Date'].apply(
                    lambda d: self.overlay_date_map.get((d.month, d.day), pd.NaT)
                )
                df = df.dropna(subset=['Date'])
                new_ts = TimeSeries(
                    df=df,
                    col=ts.col,
                    color=ts.color,
                    linestyle=ts.linestyle,
                    do_stack=ts.do_stack,
                    linewidth=ts.linewidth,
                    label=ts.label
                )
                new_series.append(new_ts)

        self.data_series = new_series

    # ==================== SETTERS ====================
    def create_figure(self, width_inch: Optional[float] = None, height_inch: Optional[float] = None):
        if width_inch is not None:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=110)
        self.ax = fig.add_subplot(111)

        self.create_line_chart(self.ax)

        left_margin = 0.05
        right_margin = 0.96

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

        # ==================== STACKED AREA PATH ====================
        if self.stacked:
            stack_series = []
            stack_colors = []
            stack_labels = []

            for ts in self.data_series:
                if not ts.do_stack:
                    continue
                if ts.df is None or ts.df.empty or ts.col not in ts.df.columns:
                    continue

                s = ts.df[['Date', ts.col]].copy()
                s[ts.col] = pd.to_numeric(s[ts.col], errors='coerce').fillna(0)
                stack_series.append(s.set_index('Date')[ts.col])
                stack_colors.append(ts.color)
                stack_labels.append(ts.label)

            if stack_series:
                stacked_df = pd.concat(stack_series, axis=1, keys=stack_labels).fillna(0)
                cumulative = stacked_df.cumsum(axis=1)

                prev = pd.Series(0.0, index=cumulative.index)
                for i, col_name in enumerate(cumulative.columns):
                    ax.fill_between(
                        cumulative.index,
                        prev,
                        cumulative[col_name],
                        color=stack_colors[i],
                        alpha=0.55,
                        label=col_name,
                        zorder=2
                    )
                    ax.plot(
                        cumulative.index,
                        cumulative[col_name],
                        color=stack_colors[i],
                        linewidth=1.3,
                        alpha=0.95,
                        zorder=3
                    )
                    prev = cumulative[col_name]

                all_dates = cumulative.index.tolist()
                all_values = cumulative.iloc[:, -1].tolist()

        # ==================== OVERLAY LINES (non-stacked) ====================
        for ts in self.data_series:
            if self.stacked and ts.do_stack:
                continue  # already drawn as part of the stack

            if ts.df is None or ts.df.empty or ts.col not in ts.df.columns:
                continue

            df = ts.df.copy()
            df[ts.col] = pd.to_numeric(df[ts.col], errors='coerce')
            valid = df[ts.col].dropna()

            all_dates.extend(df['Date'].dropna().tolist())
            all_values.extend(valid.tolist())

            plot_label = ts.label
            if self.color_by_year and '_year' in df.columns:
                year_val = int(df['_year'].iloc[0])
                plot_label = f"{year_val} {ts.label}"

            ax.plot(
                df['Date'],
                df[ts.col],
                label=plot_label,
                linewidth=ts.linewidth,
                color=ts.color,
                linestyle=ts.linestyle or '-',
                alpha=0.95,
                zorder=4 if self.stacked else 2
            )

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
            ax.tick_params(axis='x', which='minor', labelbottom=False)

        if self.title and str(self.title).strip():
            ax.set_title(self.title, fontsize=14, fontweight='bold', pad=6)

        # Grid
        ax.grid(True, which='major', linestyle='-', linewidth=1.0, color='gray', alpha=1, zorder=0)
        ax.grid(True, which='minor', linestyle='--', linewidth=0.7, color='gray', alpha=0.75, zorder=0)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)
        ax.axhline(y=0, color='black', linewidth=1.0, linestyle='-', alpha=1, zorder=3)

        self.setup_yaxis(ax)

        # ==================== Y-LIMITS ====================
        data_min = min(all_values)
        data_max = max(all_values)
        data_range = data_max - data_min
        pad = max(data_range * 0.04, 0.05 if self.y_units == 'MAF' else 1.5)

        auto_min = data_min - pad
        auto_max = data_max + pad

        if self.y_units in ('°F', '°C'):
            auto_min = max(auto_min, -5)

        if self.y_max is not None and self.y_min is not None:
            ax.set_ylim(self.y_min, self.y_max)
        elif self.y_max is not None:
            ax.set_ylim(auto_min, self.y_max)
        elif self.y_min is not None:
            ax.set_ylim(self.y_min, auto_max)
        else:
            ax.set_ylim(auto_min, auto_max)

        if self.y_units in ('MAF', 'TAF', 'AF') and self.y_divisor:
            y0, y1 = ax.get_ylim()
            span = (y1 - y0) / self.y_divisor
            if span > 0:
                if span <= 20:
                    step = 1
                elif span <= 40:
                    step = 2
                else:
                    raw_step = span / 8
                    magnitude = 10 ** math.floor(math.log10(raw_step))
                    step = magnitude
                    for mult in (1, 2, 5, 10):
                        if mult * magnitude >= raw_step:
                            step = mult * magnitude
                            break

                major = step * self.y_divisor
                minor = 0.1 * self.y_divisor

                ax.yaxis.set_major_locator(MultipleLocator(major))
                ax.yaxis.set_minor_locator(MultipleLocator(minor))
                ax.tick_params(axis='y', which='minor', length=3, width=0.6)

                decimals = 0 if step >= 1 else 1
                ax.yaxis.set_major_formatter(
                    FuncFormatter(lambda v, pos, d=decimals, div=self.y_divisor: f"{v / div:.{d}f}")
                )

        # Legend
        if self.compact_legend and (self.legend_variables or self.legend_studies):
            from matplotlib.lines import Line2D

            handles = []
            labels = []

            for label, color in self.legend_variables:
                handles.append(Line2D([0], [0], color=color, linewidth=2.5, linestyle='-'))
                labels.append(label)

            for label, ls in self.legend_studies:
                handles.append(Line2D([0], [0], color='0.25', linewidth=2.0, linestyle=ls))
                labels.append(label)

            ax.legend(handles, labels,
                      fontsize=9,
                      loc='best',
                      ncol=2,
                      framealpha=0.92,
                      handlelength=2.5)
        else:
            ncol = 2 if (self.color_by_year or self.stacked) else 1
            fontsize = 9 if (self.color_by_year or self.stacked) else 10.5
            ax.legend(fontsize=fontsize, loc='best', ncol=ncol)