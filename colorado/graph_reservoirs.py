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
import numpy as np
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import datetime as dt
import colorado.lb as lb


class ReservoirChart:
    """Complete ReservoirChart class with all original legends and deduplication"""

    def __init__(self, reservoirs, start_month=10, start_year=2025,
                 current_month=4, current_year=2026,
                 end_month=10, end_year=2026,
                 power_head_zones=None, reserved_zones=None):

        self.reservoirs = reservoirs
        self.start_month = start_month
        self.start_year = start_year
        self.current_month = current_month
        self.current_year = current_year
        self.end_month = end_month
        self.end_year = end_year
        self.power_head_zones = power_head_zones or []
        self.reserved_zones = reserved_zones or []

        self.width_inch = 14.8
        self.height_inch = 6.5
        self.fig = None

        self._create_figure()

    def _create_figure(self, width_inch=None, height_inch=None):
        if width_inch is not None and width_inch > 0:
            self.width_inch = width_inch
        if height_inch is not None and height_inch > 0:
            self.height_inch = height_inch

        title = f'Reservoir Active Capacity - {self.month_to_short_name(self.current_month)} {self.current_year}'

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=100)
        ax = fig.add_subplot(111)

        self.create_reservoir_chart(ax, title)

        fig.tight_layout(pad=1.2)
        fig.subplots_adjust(left=0.06, right=0.97, bottom=0.12, top=0.89)

        self.fig = fig
        return fig

    def update_dates(self, start_month=None, start_year=None,
                     current_month=None, current_year=None,
                     end_month=None, end_year=None):
        if start_month is not None: self.start_month = start_month
        if start_year is not None: self.start_year = start_year
        if current_month is not None: self.current_month = current_month
        if current_year is not None: self.current_year = current_year
        if end_month is not None: self.end_month = end_month
        if end_year is not None: self.end_year = end_year

        return self._create_figure()

    def get_figure(self, width_inch=None, height_inch=None):
        return self._create_figure(width_inch, height_inch)

    @staticmethod
    def month_to_short_name(month: int) -> str:
        if not 1 <= month <= 12:
            return "???"
        return dt.date(2026, month, 1).strftime("%b")

    def create_reservoir_chart(self, ax, title):
        """Full original logic with seen() deduplication"""
        if not self.reservoirs:
            raise ValueError("Reservoir list cannot be empty")

        active_reservoirs = [r for r in self.reservoirs if getattr(r, 'active_capacity_af', 0) > 0]
        if not active_reservoirs:
            raise ValueError("No reservoirs with active capacity > 0")

        reservoirs = active_reservoirs
        names = [r.name for r in reservoirs]
        capacities_maf = [r.active_capacity_af / 1_000_000 for r in reservoirs]
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
                main_bar_maf = capacities_maf[i]
                reserved_bottom = main_bar_maf - total_reserved_maf

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
                                        xy=(bar.get_x() + bar.get_width() / 2,
                                            current_bottom + amount_maf / 2 + 0.13),
                                        ha='center', va='center',
                                        fontsize=8, fontweight='bold', color='black')

                        ax.annotate(f'{amount_maf:.3f}',
                                    xy=(bar.get_x() + bar.get_width() / 2,
                                        current_bottom + amount_maf / 2 - 0.11),
                                    ha='center', va='center',
                                    fontsize=8.5, fontweight='bold', color='black')

                        current_bottom += amount_maf

                reserved_x_center = x_pos[i] - (main_width / 2) - (reserved_width / 2)

                ax.annotate(f'{total_reserved_maf:.3f}',
                            xy=(reserved_x_center, main_bar_maf),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=10.5, fontweight='bold', color='black')

        # ==================== MAIN STACKED BARS ====================
        for i, r in enumerate(reservoirs):
            crit_points = getattr(r, 'critical_elevations_feet', [])
            segments = []
            prev_cap_maf = 0.0
            for item in crit_points:
                if isinstance(item, (list, tuple)) and len(item) >= 4:
                    name, elev_ft, cap_af, color = item[:4]
                    cap_maf = cap_af / 1_000_000
                    if cap_maf > prev_cap_maf:
                        segment_height_maf = cap_maf - prev_cap_maf
                        segments.append((segment_height_maf, color, name, cap_maf, elev_ft))
                        prev_cap_maf = cap_maf

            if capacities_maf[i] > prev_cap_maf:
                segment_height_maf = capacities_maf[i] - prev_cap_maf
                color = Reservoir.high_power_pool_color if elevations_feet[i] > 0 else Reservoir.non_power_pool_color
                segments.append((segment_height_maf, color, 'Above Highest Critical',
                               capacities_maf[i], elevations_feet[i]))

            current_bottom = 0.0
            for height_maf, color, label, total_cap_maf, elev_ft in segments:
                bar = ax.bar(x_pos[i], height_maf, width=main_width,
                             bottom=current_bottom, color=color, alpha=0.85, edgecolor='navy')[0]

                if height_maf >= 0.3:
                    mid_y = current_bottom + height_maf / 2
                    ax.annotate(f'{height_maf:.3f}',
                                xy=(bar.get_x() + bar.get_width() / 2, mid_y),
                                ha='center', va='center',
                                fontsize=9, fontweight='bold', color='black')

                if "Above Highest Critical" not in label:
                    ax.annotate(f'{elev_ft:,.0f}\'',
                                xy=(x_pos[i] + main_width * 0.52, current_bottom + height_maf),
                                ha='left', va='center',
                                fontsize=9, fontweight='bold', color='darkblue',
                                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))

                current_bottom += height_maf

        # Special levels and top annotations (your original code)
        for i, r in enumerate(reservoirs):
            special_levels = getattr(r, 'special_levels', [])
            if not special_levels:
                continue
            x = x_pos[i]
            right_x = x + main_width * 0.52 + 0.04
            for elev_ft, cap_af, label in special_levels:
                cap_maf = cap_af / 1_000_000
                ax.plot(x + main_width/2 - 0.035, cap_maf, marker='<', markersize=8.5,
                        color='black', markeredgecolor='black', markerfacecolor='white')
                annot_text = f'{elev_ft:,.0f}\'\n{label}'
                ax.annotate(annot_text, xy=(right_x, cap_maf),
                            ha='left', va='center', fontsize=9.5, fontweight='bold', color='black')

        for i in range(len(names)):
            ax.annotate(f'{capacities_maf[i]:.3f}',
                        xy=(x_pos[i], capacities_maf[i]),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='black')

            if elevations_feet[i]:
                ax.annotate(f'{elevations_feet[i]:,.2f}\'',
                            xy=(x_pos[i] + main_width * 0.52, capacities_maf[i]),
                            ha='left', va='center', fontsize=9.5, color='darkgreen', fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.25", facecolor="lightyellow", alpha=0.9))

        # ==================== LEGENDS WITH seen() DEDUPLICATION ====================
        # Power Head Zones
        if self.power_head_zones:
            power_patches = [mpatches.Patch(color=color, label=label) for color, label in self.power_head_zones]
            leg_power = ax.legend(handles=power_patches, title="Power Head Zones",
                                  loc='upper right', bbox_to_anchor=(0.98, 1.0),
                                  fontsize=9, title_fontsize=10, framealpha=0.95)

        # ICS / Reserved Zones
        if self.reserved_zones:
            state_patches = [mpatches.Patch(color=color, label=label) for color, label in self.reserved_zones]
            leg_ics = ax.legend(handles=state_patches, title="ICS 2024 EoY",
                                loc='upper right', bbox_to_anchor=(0.79, 1.0),
                                fontsize=9, title_fontsize=10, framealpha=0.95)

        # Aquifer Legend
        aquifer_patches = [
            mpatches.Patch(color=lb.TUCSON_COLOR, label='Tucson AMA'),
            mpatches.Patch(color=lb.PINAL_COLOR, label='Pinal AMA'),
            mpatches.Patch(color=lb.PHX_COLOR, label='Phoenix AMA')
        ]
        leg_aquifer = ax.legend(handles=aquifer_patches, title="AZ Aquifer LTSC 2023 EOY",
                                loc='upper left', bbox_to_anchor=(0.15, 1.0),
                                fontsize=9, title_fontsize=10, framealpha=0.95)

        # Bring main legends to front
        if self.power_head_zones:
            ax.add_artist(leg_power)
        if self.reserved_zones:
            ax.add_artist(leg_ics)

        ax.set_ylabel('Volume (Million Acre-Feet)', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10.5)
        ax.grid(axis='y', linestyle='--', alpha=0.6)