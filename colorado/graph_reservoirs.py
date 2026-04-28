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
from typing import List
from reservoirs.reservoir import Reservoir
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
    def __init__(self, reservoirs: List[Reservoir], start_date=None, current_date=None, end_date=None):
        super().__init__(reservoirs, start_date, current_date, end_date)
        self.power_head_zones = [
            ('#ffffff', 'Available Head'),
            (Reservoir.high_power_pool_color, 'Normal Power Head'),
            (Reservoir.low_power_pool_color, 'Low Power Head'),
            (Reservoir.non_power_pool_color, 'Limited Access')
        ]

        self.reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]
        self.height_inch = 6.5
        self.y_max = 14.0

    def create_figure(self, width_inch=None, height_inch=None):
        if width_inch is not None and width_inch > 0:
            self.width_inch = width_inch

        title = f'Colorado River Storage - {self.month_to_short_name(self.current_date.month)} {self.current_date.day}, {self.current_date.year} '

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=100)
        ax = fig.add_subplot(111)
        self.create_reservoir_chart(ax, title)

        fig.tight_layout(pad=1.2)
        fig.subplots_adjust(left=0.06, right=0.97, bottom=0.12, top=0.89)
        self.fig = fig
        return fig

    def create_reservoir_chart(self, ax, title):
        if not self.reservoirs:
            raise ValueError("Reservoir list cannot be empty")

        active_reservoirs = [r for r in self.reservoirs if getattr(r, 'active_capacity_af', 0) > 0]
        reservoirs = active_reservoirs
        names = [r.name for r in reservoirs]
        current_maf = [r.active_capacity_af / 1_000_000 for r in reservoirs]
        elevations_feet = [r.elevation_feet for r in reservoirs]

        x_pos = np.arange(len(names))
        reserved_width = 0.26
        main_width = 0.55

        # ==================== RESERVED BARS ====================
        for i, r in enumerate(reservoirs):
            reserved_parts = getattr(r, 'reserved_parts', [])
            if reserved_parts:
                total_reserved_af = sum(amount for _, amount, _ in reserved_parts)
                total_reserved_maf = total_reserved_af / 1_000_000
                main_bar_maf = current_maf[i]
                reserved_bottom = main_bar_maf - total_reserved_maf  # ← this is the key value

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
                        ax.annotate(f'{amount_maf:.3f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, current_bottom + amount_maf / 2 - 0.11),
                                    ha='center', va='center', fontsize=8.5, fontweight='bold', color='black')
                        current_bottom += amount_maf

                # === Dashed vertical line + annotation in the middle ===
                if total_reserved_maf > 0:
                    reserved_x = x_pos[i] - (main_width / 2) - (reserved_width / 2)

                    # Dashed vertical line - dark red
                    ax.plot([reserved_x, reserved_x],
                            [reserved_bottom, 0],
                            color='darkred',
                            linestyle='--',
                            linewidth=1.4,
                            alpha=0.85,
                            zorder=5)

                    mid_y = reserved_bottom / 2

                    # Draw white background first (slightly oversized)
                    ax.add_patch(mpatches.Rectangle(
                        (reserved_x - 0.115, mid_y - 0.115),
                        0.23, 0.23,  # wide enough for the number
                        facecolor='white',
                        edgecolor='none',
                        zorder=6
                    ))

                    # Then draw the black text on top
                    ax.annotate(
                        f'{reserved_bottom:.3f}',
                        xy=(reserved_x, mid_y),
                        ha='center',
                        va='center',
                        fontsize=9.5,
                        fontweight='bold',
                        color='black',
                        zorder=7
                    )

                ax.annotate(f'{total_reserved_maf:.3f}',
                            xy=(x_pos[i] - (main_width/2) - (reserved_width/2), main_bar_maf),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='black')

        # ==================== MAIN STACKED BARS ====================
        for i, r in enumerate(reservoirs):
            current_cap_maf = current_maf[i]
            if current_cap_maf <= 0:
                continue

            crit_points = getattr(r, 'critical_elevations_feet', [])
            zones = []
            prev = 0.0
            for item in crit_points:
                if isinstance(item, (list, tuple)) and len(item) >= 4:
                    name, elev, cap_af, color = item[:4]
                    cap = cap_af / 1_000_000
                    if cap > prev:
                        zones.append((cap - prev, color, name, cap, elev))
                        prev = cap

            top_color = Reservoir.high_power_pool_color if elevations_feet[i] > 0 else Reservoir.non_power_pool_color
            if current_cap_maf > prev:
                zones.append((current_cap_maf - prev, top_color, 'Above Highest Critical',
                              current_cap_maf, elevations_feet[i]))

            bottom = 0.0
            for h, color, label, total_cap, elev in zones:
                draw_h = min(h, current_cap_maf - bottom)
                if draw_h <= 0:
                    break
                bar = ax.bar(x_pos[i], draw_h, width=main_width, bottom=bottom,
                             color=color, alpha=0.85, edgecolor='navy')[0]

                if draw_h >= 0.3:
                    ax.annotate(f'{draw_h:.3f}',
                                xy=(bar.get_x() + bar.get_width()/2, bottom + draw_h/2),
                                ha='center', va='center', fontsize=9, fontweight='bold', color='black')

                if "Above Highest Critical" not in label:
                    ax.annotate(f'{elev:,.0f}\'',
                                xy=(x_pos[i] + main_width*0.52, bottom + draw_h),
                                ha='left', va='center', fontsize=9, fontweight='bold', color='darkblue',
                                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))

                bottom += draw_h
                if bottom >= current_cap_maf:
                    break

        # ==================== TEACUP HOLLOW BAR ====================
        teacup_color = '#1f1f1f'
        teacup_alpha = 0.40
        teacup_linewidth = 1.5

        for i, r in enumerate(reservoirs):
            curr_af = getattr(r, 'active_capacity_af', 0)
            full_af = getattr(r, 'full_af', None)
            if full_af is None or full_af <= curr_af or curr_af <= 0:
                continue

            curr_maf = curr_af / 1_000_000
            full_maf = full_af / 1_000_000
            empty = full_maf - curr_maf
            if empty <= 0: continue

            # Teacup bar (visual height unchanged)
            container = ax.bar(x_pos[i], empty, width=main_width, bottom=curr_maf,
                               color='white', alpha=0.0,
                               edgecolor=teacup_color, linewidth=teacup_linewidth)

            for patch in container:
                patch.set_alpha(teacup_alpha)

            top_y = min(full_maf, self.y_max)
            ax.plot([x_pos[i]-main_width/2, x_pos[i]+main_width/2], [top_y, top_y],
                    color=teacup_color, linewidth=teacup_linewidth, alpha=teacup_alpha)

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
            if full_maf > self.y_max:
                label_y = self.y_max
                offset_y = 1.5
            else:
                label_y = full_maf
                offset_y = 9.5

            # Acre-feet (practical) — centered
            ax.annotate(f'{practical_available_maf:.3f}',
                        xy=(x_pos[i], label_y),
                        xytext=(0, offset_y),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9.5, fontweight='bold', color='darkred')

            # Percentage — right justified at elevation position
            ax.annotate(f'{percent_practical}%',
                        xy=(x_pos[i] + main_width * 0.52, label_y),
                        xytext=(0, offset_y),
                        textcoords="offset points",
                        ha='left', va='bottom',
                        fontsize=9.5, fontweight='bold', color='darkred')

        # ==================== ANNOTATIONS ====================
        # Special levels
        for i, r in enumerate(reservoirs):
            for elev_ft, cap_af, label in getattr(r, 'special_levels', []):
                cap_maf = cap_af / 1_000_000
                if cap_maf <= current_maf[i]:
                    ax.plot(x_pos[i] + main_width/2 - 0.035, cap_maf, marker='<', markersize=8.5,
                            color='black', markeredgecolor='black', markerfacecolor='white')
                    ax.annotate(f'{elev_ft:,.0f}\'\n{label}',
                                xy=(x_pos[i] + main_width*0.52 + 0.04, cap_maf),
                                ha='left', va='center', fontsize=9.5, fontweight='bold', color='black')

        for i in range(len(names)):
            # Active storage total on top of bar (lowered)
            ax.annotate(f'{current_maf[i]:.3f}',
                        xy=(x_pos[i], current_maf[i]),
                        xytext=(0, 0.6),           # lowered
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='black')

            # Current elevation on the right
            if elevations_feet[i]:
                ax.annotate(f'{elevations_feet[i]:,.2f}\'',
                            xy=(x_pos[i] + main_width * 0.52, current_maf[i]),
                            ha='left', va='center', fontsize=9.5, color='darkgreen', fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.25", facecolor="lightyellow", alpha=0.9))

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
            leg = ax.legend(handles=ics_patches, title="ICS 2024 EoY",
                            loc='upper right', bbox_to_anchor=(0.4, 1.0),
                            fontsize=9, title_fontsize=10, framealpha=0.95)
            ax.add_artist(leg)

        aquifer_patches = [
            mpatches.Patch(color=lb.TUCSON_COLOR, label='Tucson AMA'),
            mpatches.Patch(color=lb.PINAL_COLOR, label='Pinal AMA'),
            mpatches.Patch(color=lb.PHX_COLOR, label='Phoenix AMA')
        ]
        ax.legend(handles=aquifer_patches, title="AZ Aquifer LTSC 2023 EOY",
                  loc='upper left', bbox_to_anchor=(0.15, 1.0),
                  fontsize=9, title_fontsize=10, framealpha=0.95)

        self.final_layout(ax, title, names, x_pos)