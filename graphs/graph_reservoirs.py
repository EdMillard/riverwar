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
from pathlib import Path
import wx
from typing import List, Tuple
from reservoirs.reservoir import Reservoir, ReservoirGroup
import colorado.lb as lb
from chart.chart import BarChart
import numpy as np
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

arrow_fg = wx.Colour(150, 150, 150)

def find_directories_with_file(root_dir: str, filename: str) -> List[str]:
    """Return list of directories containing the given filename."""
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    matching_dirs = []
    for dir_path in root.rglob("*"):
        if dir_path.is_dir() and (dir_path / filename).is_file():
            matching_dirs.append(str(dir_path.resolve()))
    return sorted(set(matching_dirs))


# ==================== RESERVOIR CHART ====================
class ReservoirChart(BarChart):
    def __init__(self, reservoirs: List[Reservoir], start_date=None, current_date=None, end_date=None,
                 reservoir_totals:List[ReservoirGroup]=None,
                 power_head_zones:List[Tuple]=None, reserved_names:List[Tuple]=None, aquifer_zones:List[Tuple]=None,
                 y_max:float=14.0, percentage:float = 0.0):
        super().__init__(start_date, current_date, end_date, percentage=percentage)
        self.version = 0.4
        self.reservoirs = reservoirs

        self.reservoir_totals:List[ReservoirGroup] = reservoir_totals
        self.power_head_zones = power_head_zones
        self.aquifer_zones = aquifer_zones
        self.reserved_zones = reserved_names

        self.height_inch = 6.5
        self.y_max = y_max

    def create_figure(self, width_inch=None, height_inch=None):
        if width_inch is not None and width_inch > 0:
            self.width_inch = width_inch
        if height_inch is not None:
            self.height_inch = height_inch

        title = f'Colorado River Reservoir Reality\u2122 - {self.month_to_short_name(self.current_date.month)} ' \
                f'{self.current_date.day}, {self.current_date.year}   v{self.version}'

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=100)
        self.ax = fig.add_subplot(111)

        self.create_reservoir_chart(self.ax, title)

        fig.tight_layout(pad=0.8)
        if self.percentage < 0.2 and self.percentage != 0:
            top_margin = 0.92
            bottom_margin = 0.18
        else:
            top_margin = 0.96
            bottom_margin = 0.04
        fig.subplots_adjust(left=0.06, right=0.97, bottom=bottom_margin, top=top_margin)

        self.fig = fig
        return fig

    @staticmethod
    def create_custom_bars(ax, segments, font_size, font_size_inside_bar, format_maf, x_pos, main_width):
        parsed = []
        total_af = 0.0
        for item in segments:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue
            label, cap_af, color = item[:3]
            if cap_af is None or cap_af <= 0:
                continue
            parsed.append((label, cap_af, color))
            total_af += cap_af

        if total_af <= 0:
            return 0.0

        bottom = 0.0
        for label, cap_af, color in parsed:
            draw_h = cap_af / 1_000_000
            bar = ax.bar(x_pos, draw_h, width=main_width, bottom=bottom,
                         color=color, alpha=0.85, edgecolor='navy')[0]
            x = bar.get_x() + bar.get_width() / 2
            y = bottom + draw_h / 2

            ax.annotate(f'{cap_af / 1_000_000:.{format_maf}f}',
                        xy=(x, y),
                        ha='center', va='center',
                        fontsize=font_size_inside_bar,
                        fontweight='bold',
                        color='black')
            ax.annotate(str(label),
                        xy=(bar.get_x() + bar.get_width(), y),
                        xytext=(4, 0),
                        textcoords='offset points',
                        ha='left', va='center',
                        fontsize=font_size,
                        fontweight='bold',
                        color='black')
            bottom += draw_h

        ax.annotate(f'{total_af / 1_000_000:.{format_maf}f}',
                    xy=(x_pos, bottom),
                    xytext=(0, 2),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=font_size_inside_bar,
                    fontweight='bold',
                    color='black')

        return total_af / 1_000_000

    @staticmethod
    def create_main_bars(ax, reservoirs, font_size, font_size_inside_bar, format_maf, current_maf, x_pos,
                         main_width, elevations_feet, min_full_af_to_draw):
        for i, r in enumerate(reservoirs):
            if not r.show_in_chart:
                continue
            custom_bar = getattr(r, 'custom_bar', None)
            if custom_bar is not None:
                r.annotation_drawn_in_bar = ReservoirChart.create_custom_bars(
                    ax, custom_bar, font_size, font_size_inside_bar, format_maf, x_pos[i], main_width)
                continue

            full_af = getattr(r, 'full_af', None)
            if full_af is None:
                continue

            current_cap_maf = current_maf[i]
            if current_cap_maf <= 0:
                continue

            crit_points = getattr(r, 'critical_elevations_feet', [])

            # ==================== OPTIONAL DEAD POOL BAR AT BOTTOM ====================
            dead_pool_maf = 0.0
            dead_pool_color = None
            filtered_crit = []
            for item in crit_points:
                if isinstance(item, (list, tuple)) and len(item) >= 4:
                    name = item[0]
                    if name == "Dead Pool":
                        dead_pool_maf = item[2] / 1_000_000
                        dead_pool_color = item[3]
                    else:
                        filtered_crit.append(item)
                else:
                    filtered_crit.append(item)

            # Draw dead pool bar if present and positive
            bottom = 0.0
            if dead_pool_maf > 0 and dead_pool_color is not None:
                draw_h = min(dead_pool_maf, current_cap_maf)
                if draw_h > 0:
                    bar = ax.bar(x_pos[i], draw_h, width=main_width, bottom=0.0,
                                 color=dead_pool_color, alpha=0.85, edgecolor='navy')[0]
                    x = bar.get_x() + bar.get_width() / 2
                    y = draw_h / 2
                    ax.annotate(f'{draw_h:.{format_maf}f}',
                                xy=(x, y),
                                ha='center', va='center',
                                fontsize=font_size_inside_bar,
                                fontweight='bold',
                                color='black')
                    bottom = draw_h
                    r.annotation_drawn_in_bar = draw_h

            # Build zones from remaining critical points (starting above dead pool)
            zones = []
            prev = dead_pool_maf
            for item in filtered_crit:
                if isinstance(item, (list, tuple)) and len(item) >= 4:
                    name, elev, cap_af, color = item[:4]
                    cap = cap_af / 1_000_000
                    if cap > prev:
                        zones.append((cap - prev, color, name, cap, elev))
                        prev = cap

            if r.custom_color:
                top_color = r.custom_color
            else:
                top_color = Reservoir.high_power_pool_color
            if current_cap_maf > prev:
                zones.append((current_cap_maf - prev, top_color, 'Above Highest Critical',
                              current_cap_maf, elevations_feet[i]))

            # Draw remaining stacked zones above the dead pool (or from 0 if none)
            for n, (h, color, label, total_cap, elev) in enumerate(zones):
                draw_h = min(h, current_cap_maf - bottom)
                if draw_h <= 0:
                    break
                annotation_value = draw_h
                if 0 < full_af < min_full_af_to_draw:
                    draw_h = 0
                bar = ax.bar(x_pos[i], draw_h, width=main_width, bottom=bottom,
                             color=color, alpha=0.85, edgecolor='navy')[0]
                x = bar.get_x() + bar.get_width() / 2

                # Current Storage annotation
                r.annotation_drawn_in_bar = bottom + draw_h
                y = bottom + draw_h / 2
                if 0 < full_af < min_full_af_to_draw:
                    is_last = (n == len(zones) - 1)
                    if is_last:
                        y += 0.08
                        ax.annotate(f'{annotation_value:.{format_maf}f}', xy=(x, y),
                                    ha='center', va='center', fontsize=font_size_inside_bar, fontweight='bold',
                                    color='black')
                    else:
                        continue
                else:
                    ax.annotate(f'{annotation_value:.{format_maf}f}', xy=(x, y),
                                ha='center', va='center', fontsize=font_size_inside_bar, fontweight='bold',
                                color='black')

                # Critical Elevation annotation (disabled)
                if 0 and "Above Highest Critical" not in label and r.show_elevations:
                    ax.annotate(f'{elev:,.0f}\'',
                                xy=(x_pos[i] + main_width * 0.52, bottom + draw_h),
                                ha='left', va='center',
                                fontsize=font_size,
                                fontweight='bold',
                                color='darkblue',
                                bbox=dict(boxstyle="square",
                                          facecolor="white",
                                          edgecolor="none",
                                          pad=0,
                                          alpha=1)
                                )

                bottom += draw_h
                if bottom >= current_cap_maf:
                    break

            # ==================== SPECIAL LEVELS WITH DASHED LINES ("above" / "below" / "both") ====================
            special_levels = getattr(r, 'special_levels', [])
            if special_levels:
                normalized = []
                for item in special_levels:
                    if not isinstance(item, (list, tuple)) or len(item) < 3:
                        continue
                    elev_ft = item[0]
                    cap_af = item[1]
                    label = item[2]
                    mode = item[3] if len(item) >= 4 else None
                    if isinstance(mode, bool):  # backward compat with old True
                        mode = "above" if mode else None
                    if cap_af is None or cap_af <= 0:
                        continue
                    normalized.append((elev_ft, cap_af / 1_000_000, label, mode))

                # Sort by capacity so "next up" is well-defined
                normalized.sort(key=lambda t: t[1])

                bar_top_maf = current_cap_maf

                # Horizontal center of the gap between this bar and the next bar to the right
                if i + 1 < len(x_pos):
                    right_edge = x_pos[i] + main_width / 2
                    left_edge_next = x_pos[i + 1] - main_width / 2
                    gap_center_x = (right_edge + left_edge_next) / 2
                else:
                    # Last bar — fall back to a small offset to the right
                    gap_center_x = x_pos[i] + main_width / 2 + 0.15

                # Right edge of the current main bar
                bar_right_x = x_pos[i] + main_width / 2

                def draw_dashed_segment(low_maf, high_maf):
                    if high_maf <= low_maf or high_maf - low_maf < 0.000001:
                        return
                    # Vertical dashed line
                    ax.plot([gap_center_x, gap_center_x], [low_maf, high_maf],
                            color='darkred', linestyle='--', linewidth=1.4, alpha=0.85, zorder=5)

                    mid_y = (low_maf + high_maf) / 2
                    displayed = high_maf - low_maf

                    # White erasure starting just right of the bar so teacup is not covered
                    erase_left = bar_right_x + 0.03
                    erase_right = gap_center_x + 0.12
                    erase_bottom = mid_y - 0.12
                    erase_height = 0.24
                    ax.add_patch(mpatches.Rectangle(
                        (erase_left, erase_bottom),
                        erase_right - erase_left, erase_height,
                        facecolor='white', edgecolor='none', zorder=6
                    ))
                    ax.annotate(
                        f'{displayed:.{format_maf}f}',
                        xy=(gap_center_x, mid_y),
                        ha='center', va='center',
                        fontsize=font_size, fontweight='bold', color='black', zorder=7
                    )

                    # Short horizontal caps drawn AFTER the annotation so they aren't erased
                    cap_half_width = 0.06
                    ax.plot([gap_center_x - cap_half_width, gap_center_x + cap_half_width],
                            [low_maf, low_maf],
                            color='darkred', linestyle='-', linewidth=1.6, alpha=0.9, zorder=8)
                    ax.plot([gap_center_x - cap_half_width, gap_center_x + cap_half_width],
                            [high_maf, high_maf],
                            color='darkred', linestyle='-', linewidth=1.6, alpha=0.9, zorder=8)

                for idx, (elev_ft, cap_maf, label, mode) in enumerate(normalized):
                    if mode not in ("above", "below", "both"):
                        continue

                    # ---------- ABOVE ----------
                    if mode in ("above", "both"):
                        if cap_maf < bar_top_maf:
                            next_up_maf = bar_top_maf
                            if idx + 1 < len(normalized):
                                next_up_maf = min(normalized[idx + 1][1], bar_top_maf)
                            if next_up_maf > cap_maf:
                                draw_dashed_segment(cap_maf, next_up_maf)

                    # ---------- BELOW (ruler down to bottom of bar) ----------
                    if mode in ("below", "both"):
                        if cap_maf > 0:
                            draw_dashed_segment(0.0, cap_maf)

    @staticmethod
    def create_reserved_bars(ax, reservoirs, font_size, format_maf, current_maf, x_pos, main_width, reserved_width):
        for i, r in enumerate(reservoirs):
            if not r.show_in_chart:
                continue
            reserved_parts = getattr(r, 'reserved_parts', [])
            if not reserved_parts:
                continue

            total_reserved_af = sum(amount for _, amount, _ in reserved_parts)
            total_reserved_maf = total_reserved_af / 1_000_000
            main_bar_maf = current_maf[i]
            reserved_bottom = main_bar_maf - total_reserved_maf

            # ==================== RESERVED STACKED BARS ====================
            current_bottom = reserved_bottom
            for owner, amount, color in reserved_parts:
                if amount > 0:
                    amount_maf = amount / 1_000_000
                    reserved_x = x_pos[i] - (main_width / 2) - (reserved_width / 2)
                    bar = ax.bar(reserved_x, amount_maf, width=reserved_width,
                                 bottom=current_bottom, color=color, alpha=0.92,
                                 edgecolor='darkgoldenrod')[0]

                    if amount_maf >= 0.45:
                        ax.annotate(owner[:8],
                                    xy=(bar.get_x() + bar.get_width() / 2, current_bottom + amount_maf / 2 + 0.13),
                                    ha='center', va='center', fontsize=8, fontweight='bold', color='black')
                    ax.annotate(f'{amount_maf:.{format_maf}f}',
                                xy=(bar.get_x() + bar.get_width() / 2, current_bottom + amount_maf / 2 - 0.11),
                                ha='center', va='center', fontsize=8.5, fontweight='bold', color='black')
                    current_bottom += amount_maf

            # ==================== ORIGINAL DASHED LINE + ANNOTATION ====================
            dash_to_y = 0.0
            crit_points = getattr(r, 'critical_elevations_feet', [])

            if crit_points:
                for item in crit_points:
                    if isinstance(item, (list, tuple)) and len(item) >= 3:
                        cap_maf = item[2] / 1_000_000
                        if reserved_bottom >= cap_maf > dash_to_y:
                            dash_to_y = cap_maf

            if total_reserved_maf > 0:
                reserved_x = x_pos[i] - (main_width / 2) - (reserved_width / 2)

                ax.plot([reserved_x, reserved_x],
                        [reserved_bottom, dash_to_y],
                        color='darkred', linestyle='--', linewidth=1.4, alpha=0.85, zorder=5)

                mid_y = (reserved_bottom + dash_to_y) / 2
                displayed_value = reserved_bottom - dash_to_y
                if displayed_value > 0.000001:
                    ax.add_patch(mpatches.Rectangle(
                        (reserved_x - 0.115, mid_y - 0.115),
                        0.23, 0.23,
                        facecolor='white', edgecolor='none', zorder=6
                    ))

                    ax.annotate(
                        f'{displayed_value:.{format_maf}f}',
                        xy=(reserved_x, mid_y),
                        ha='center', va='center',
                        fontsize=font_size, fontweight='bold', color='black', zorder=7
                    )

                ax.annotate(f'{total_reserved_maf:.{format_maf}f}',
                            xy=(x_pos[i] - (main_width/2) - (reserved_width/2), main_bar_maf),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=font_size, fontweight='bold', color='black')

            # ==================== FULL-WIDTH SOLID BAR + LABEL ====================
            lowest_critical_maf = 0.0
            for item in crit_points:
                if isinstance(item, (list, tuple)) and len(item) >= 3:
                    cap_maf = item[2] / 1_000_000
                    if cap_maf > 0 and (lowest_critical_maf == 0 or cap_maf < lowest_critical_maf):
                        lowest_critical_maf = cap_maf

            in_the_red_maf = max(0.0, lowest_critical_maf - reserved_bottom)

            if in_the_red_maf > 0.001:
                red_bottom = lowest_critical_maf - in_the_red_maf

                # Full-width solid bar
                ax.bar(x_pos[i], in_the_red_maf, width=main_width,
                       bottom=red_bottom,
                       color='red', alpha=1.0, edgecolor='darkred', linewidth=1.5, zorder=10)

                # Numeric value inside bar
                ax.annotate(f'{in_the_red_maf:.{format_maf}f}',
                            xy=(x_pos[i], red_bottom + in_the_red_maf / 2),
                            ha='center', va='center',
                            fontsize=font_size, fontweight='bold', color='white', zorder=11)

                # === TWO-LINE "ICS Deficit"===
                ax.annotate('ICS\nDeficit',
                            xy=(x_pos[i] + main_width * 0.55, red_bottom + in_the_red_maf / 2 - 0.12),
                            ha='left', va='center',
                            fontsize=font_size, fontweight='bold', color='red',
                            linespacing=0.95, zorder=12)

    @staticmethod
    def create_teacup_bars(ax, reservoirs, font_size, format_maf, x_pos, y_max, main_width, min_full_af_to_draw):
        teacup_color = '#1f1f1f'
        teacup_alpha = 0.40
        teacup_linewidth = 1.5

        for i, r in enumerate(reservoirs):
            if not r.show_in_chart:
                continue
            curr_af = getattr(r, 'active_capacity_af', 0)
            full_af = getattr(r, 'full_af', None)
            if full_af is None or full_af <= curr_af or curr_af <= 0:
                continue

            curr_maf = curr_af / 1_000_000
            full_maf = full_af / 1_000_000
            empty = full_maf - curr_maf
            if empty <= 0:
                continue

            # Teacup bar
            if full_af > min_full_af_to_draw:
                container = ax.bar(x_pos[i], empty, width=main_width, bottom=curr_maf,
                                   color='white', alpha=0.0,
                                   edgecolor=teacup_color, linewidth=teacup_linewidth)

                for patch in container:
                    patch.set_alpha(teacup_alpha)

                top_y = min(full_maf, y_max)
                ax.plot([x_pos[i] - main_width / 2, x_pos[i] + main_width / 2], [top_y, top_y],
                        color=teacup_color, linewidth=teacup_linewidth, alpha=teacup_alpha)

                # ==================== 1-YR / 1-MO ARROWS ON TEACUP EDGES ====================
                left_x = x_pos[i] - main_width / 2
                right_x = x_pos[i] + main_width / 2

                # 1 year ago — left edge, right-pointing arrow
                yr_af = getattr(r, 'storage_one_year_ago', None)
                if yr_af is not None and yr_af > 0:
                    yr_maf = yr_af / 1_000_000
                    color = 'green' if curr_maf > yr_maf else 'red'
                    ax.plot(left_x, yr_maf, marker='>', markersize=8.5,
                            color=color, markeredgecolor='black', markeredgewidth=0.8,
                            markerfacecolor=color, zorder=12)

                # 1 month ago — right edge, left-pointing arrow
                mo_af = getattr(r, 'storage_one_month_ago', None)
                if mo_af is not None and mo_af > 0:
                    mo_maf = mo_af / 1_000_000
                    color = 'green' if curr_maf > mo_maf else 'red'
                    ax.plot(right_x, mo_maf, marker='<', markersize=8.5,
                            color=color, markeredgecolor='black', markeredgewidth=0.8,
                            markerfacecolor=color, zorder=12)

            # ==================== PRACTICAL AVAILABLE ABOVE LOWEST NON-ZERO CRITICAL ====================
            lowest_crit_cap_af = 0
            crit_points = getattr(r, 'critical_elevations_feet', [])

            if crit_points:
                # Only consider critical elevations with positive capacity
                valid_caps = [item[2] for item in crit_points
                              if len(item) >= 3 and item[2] > 0]
                if valid_caps:
                    lowest_crit_cap_af = min(valid_caps)

            # Practical available capacity above the lowest valid critical
            practical_available_af = full_af - lowest_crit_cap_af
            if practical_available_af <= 0:
                practical_available_af = full_af  # fallback

            practical_available_maf = practical_available_af / 1_000_000

            # Percentage of practical available
            percent_practical = round(((curr_af - lowest_crit_cap_af) / practical_available_af) * 100) \
                if practical_available_af > 0 else 100

            # Positioning
            if full_maf > y_max:
                label_y = y_max
                offset_y = 0.5
            else:
                label_y = full_maf
                offset_y = 9.5

            # Acre-feet and percent full centered over top of bar
            ax.annotate(f'{practical_available_maf:.{format_maf}f}  {percent_practical}%',
                        xy=(x_pos[i], label_y),
                        xytext=(0, offset_y),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=font_size, fontweight='bold', color='darkred')

    def create_reservoir_chart(self, ax, title):
        if not self.reservoirs:
            raise ValueError("Reservoir list cannot be empty")

        active_reservoirs = []
        for r in self.reservoirs:
            if getattr(r, 'active_capacity_af', 0) > 0:
                if r.show_in_chart:
                    active_reservoirs.append(r)
            else:
                print(f"reservoir inactive {r.name}")

        reservoirs = active_reservoirs
        names = [r.name for r in reservoirs]
        current_maf = [r.active_capacity_af / 1_000_000 for r in reservoirs]
        elevations_feet = [r.elevation_feet for r in reservoirs]

        x_pos = np.arange(len(names))
        reserved_width = 0.26
        main_width = 0.55
        font_size = 10
        font_size_above_bar = 11
        font_size_inside_bar = 13
        format_maf = 3
        min_full_af_to_draw = 350_000

        # ==================== MAIN STACKED BARS ====================
        ReservoirChart.create_main_bars(ax, reservoirs, font_size, font_size_inside_bar, format_maf, current_maf, x_pos,
                                        main_width, elevations_feet, min_full_af_to_draw)

        # ==================== TEACUP HOLLOW BAR ====================
        ReservoirChart.create_teacup_bars(ax, reservoirs, font_size, format_maf, x_pos, self.y_max,
                                          main_width, min_full_af_to_draw)

        # ==================== RESERVED BARS ====================
        ReservoirChart.create_reserved_bars(ax, reservoirs, font_size, format_maf, current_maf, x_pos,
                                            main_width, reserved_width)

        # ==================== ANNOTATIONS ====================
        # Totals
        self.add_total_annotations()

        # Special levels
        for i, r in enumerate(reservoirs):
            if not r.show_in_chart:
                continue
            for item in getattr(r, 'special_levels', []):
                if not isinstance(item, (list, tuple)) or len(item) < 3:
                    continue
                elev_ft, cap_af, label = item[0], item[1], item[2]
                cap_maf = cap_af / 1_000_000
                if cap_maf <= current_maf[i]:
                    ax.plot(x_pos[i] + main_width/2 - 0.025, cap_maf, marker='<', markersize=8.5,
                            color='black', markeredgecolor='black', markerfacecolor='white')
                    if label:
                        s = f'{elev_ft:,.0f}\'\n{label}'
                    else:
                        s = f'{elev_ft:,.0f}\''

                    ax.annotate(s, xy=(x_pos[i] + main_width*0.52 + 0.015, cap_maf),
                                ha='left', va='center',
                                fontsize=font_size,
                                fontweight='bold',
                                color='black',
                                bbox=dict(boxstyle="round",
                                          edgecolor='none',
                                          facecolor="white",
                                          pad=0,
                                          alpha=1)
                                )

        # ==================== FINAL ANNOTATIONS ====================
        for i in range(len(names)):
            r = reservoirs[i]
            current_maf_val = current_maf[i]

            # Calculate practical available
            crit_points = getattr(r, 'critical_elevations_feet', None)
            has_critical = False
            practical_available_maf = current_maf_val   # fallback

            if crit_points:
                valid_caps = [item[2] for item in crit_points
                              if isinstance(item, (list, tuple)) and len(item) >= 3 and item[2] > 0]
                if valid_caps:
                    has_critical = True
                    lowest_crit_af = min(valid_caps)
                    practical_available_af = getattr(r, 'active_capacity_af', 0) - lowest_crit_af
                    if practical_available_af > 0:
                        practical_available_maf = practical_available_af / 1_000_000

            # === Two-line annotation with " of" ===
            if 0 and r.show_elevations:
                if has_critical and abs(practical_available_maf - current_maf_val) > 0.001:
                    top_line = f'{practical_available_maf:.{format_maf}f} of'
                    bottom_line = f'{current_maf_val:.{format_maf}f}'

                    ax.annotate(f'{top_line}\n{bottom_line}',
                                xy=(x_pos[i], current_maf_val),
                                xytext=(0, 1.0),           # adjust height if needed
                                textcoords="offset points",
                                ha='center',
                                va='bottom',
                                fontsize=font_size_above_bar,
                                fontweight='bold',
                                color='black',
                                linespacing=1.08,
                                bbox=dict(boxstyle="round",
                                          edgecolor='none',
                                          facecolor="white",
                                          pad=0,
                                          alpha=1)
                                )
                else:
                    # Single line fallback
                    if r.annotation_drawn_in_bar > 0 and r.annotation_drawn_in_bar == current_maf_val:
                        pass
                    else:
                        ax.annotate(f'{current_maf_val:.{format_maf}f}',
                                    xy=(x_pos[i], current_maf_val),
                                    xytext=(0, 0.6),
                                    textcoords="offset points",
                                    ha='center', va='bottom',
                                    fontsize=font_size,
                                    fontweight='bold',
                                    color='black',
                                    bbox=dict(boxstyle="round",
                                              edgecolor='none',
                                              facecolor="white",
                                              pad=0,
                                              alpha=1)
                                    )

            # === Current elevation just above the bar ===
            if r.show_elevations and elevations_feet[i]:
                bar_top = current_maf_val
                if getattr(r, 'custom_bar', None) and getattr(r, 'annotation_drawn_in_bar', 0):
                    bar_top = r.annotation_drawn_in_bar
                ax.annotate(f'{elevations_feet[i]:,.2f}\'',
                            xy=(x_pos[i], bar_top),
                            xytext=(0, 2),
                            textcoords='offset points',
                            ha='center', va='bottom',
                            fontsize=font_size,
                            color='darkgreen',
                            fontweight='bold')

        # ==================== ANNOTATIONS ====================
        if self.power_head_zones:
            power_patches = []
            teacup_index = -1

            for idx, (c, l) in enumerate(self.power_head_zones):
                if str(c).lower() in ('#ffffff', 'white', 'w'):
                    teacup_index = idx
                    # Special teacup patch
                    patch = mpatches.Patch(
                        facecolor='white',
                        edgecolor='#1f1f1f',
                        linewidth=1.8,
                        alpha=0.55,
                        label=l
                    )
                else:
                    patch = mpatches.Patch(color=c, label=l)
                power_patches.append(patch)

            leg_power = ax.legend(handles=power_patches, title="Power Head Zones",
                                  loc='upper right', bbox_to_anchor=(0.98, 1.0),
                                  fontsize=9, title_fontsize=10, framealpha=0.95)
            ax.add_artist(leg_power)

            # Change text color ONLY for the teacup (white) entry
            if 0 <= teacup_index < len(leg_power.get_texts()):
                teacup_text = leg_power.get_texts()[teacup_index]
                teacup_text.set_color('darkred')
                teacup_text.set_fontweight('bold')

        if self.reserved_zones:
            ics_patches = [mpatches.Patch(color=c, label=l) for c, l in self.reserved_zones]
            leg = ax.legend(handles=ics_patches, title="ICS 2025 EoY",
                            loc='upper right', bbox_to_anchor=(0.45, 1.0),
                            fontsize=9, title_fontsize=10, framealpha=0.95)
            ax.add_artist(leg)

        if self.aquifer_zones:
            aquifer_patches = [
                mpatches.Patch(color=lb.TUCSON_COLOR, label='Tucson AMA'),
                mpatches.Patch(color=lb.PINAL_COLOR, label='Pinal AMA'),
                mpatches.Patch(color=lb.PHX_COLOR, label='Phoenix AMA')
            ]
            ax.legend(handles=aquifer_patches, title="AZ Aquifer LTSC 2023 EOY",
                      loc='upper left', bbox_to_anchor=(0.15, 1.0),
                      fontsize=9, title_fontsize=10, framealpha=0.95)

        ax.set_xlim(-0.65, len(names) - 0.35)

        # Title
        if self.percentage > 0.5 or self.percentage == 0:
            ax.set_title(title, fontsize=14.5, fontweight='bold', pad=10)

        self.final_layout(ax, title, names, x_pos)

    def add_total_annotations(self):
        if not self.reservoir_totals:
            return

        rows = []
        num_groups_with_legends = 0
        x, y = (0.77, 1.0)
        for i, reservoir_group in enumerate(self.reservoir_totals):
            name = reservoir_group.name
            reservoir_group.reservoir_total()
            if reservoir_group.legend_position is None:
                continue
            num_groups_with_legends += 1
            x, y = reservoir_group.legend_position
            rows.append((reservoir_group.accessible_total / 1_000_000, name, Reservoir.high_power_pool_color, 'black'))
            #rows.append((reservoir_group.below_critical_total / 1_000_000, 'Below Critical', Reservoir.low_power_pool_color, 'gray')),
            #rows.append((reservoir_group.limited_access_total / 1_000_000, 'Inaccessible', Reservoir.non_power_pool_color, 'gray')),

        title = ""
        if num_groups_with_legends > 1:
            accessible_total = 0
            for i, reservoir_group in enumerate(self.reservoir_totals):
                accessible_total += reservoir_group.accessible_total
            rows.append((accessible_total / 1_000_000, "Total", Reservoir.high_power_pool_color, 'black'))
            title = "System Water"

        handles = [
            mpatches.Patch(facecolor=color, edgecolor='#555555', linewidth=0.8,
                           label=f'{maf:4.2f} MAF {label}')
            for maf, label, color, _ in rows
        ]
        leg = self.ax.legend(
            handles=handles,
            title=title,
            loc='upper left',
            bbox_to_anchor=(x, y),
            fontsize=16,
            title_fontsize=14,
            framealpha=0.95,
            handlelength=1.2,
            handleheight=1.0,
            borderpad=0.6,
            labelspacing=0.4,
        )
        leg.get_title().set_fontweight('bold')
        for text in leg.get_texts():
            text.set_fontfamily('monospace')
            text.set_fontweight('semibold')
        for text, row in zip(leg.get_texts(), rows):
            text.set_color(row[3])
        self.ax.add_artist(leg)