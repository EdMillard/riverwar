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
from datetime import date
from chart.chart import Chart, BarChart
from typing import List, Optional


class InflowOutflowChart(BarChart):
    def __init__(self,
                 reservoirs: List[Reservoir],
                 start_date: date | None = None,
                 current_date: date | None = None,
                 end_date: date | None = None):
        super().__init__(reservoirs, start_date, current_date, end_date)
        self.height_inch = 5.6
        self.y_max = 10.0

    def create_figure(
            self,
            width_inch: Optional[int] = None,
            height_inch: Optional[int] = None
    ) -> Optional[Figure]:
        if width_inch is not None and width_inch > 0:
            self.width_inch = width_inch
        if height_inch is not None and height_inch > 0:
            self.height_inch = height_inch

        title = (f"{self.report_name}  Outflow Loss Inflow, "
                 f"{Chart.date_to_string(self.current_date)} "
                 f"[{Chart.date_to_string(self.start_date)}-"
                 f"{Chart.date_to_string(self.end_date)}]")

        fig = Figure(figsize=(self.width_inch, self.height_inch), dpi=100)
        ax = fig.add_subplot(111)

        self.create_inflow_outflow_chart(ax, title)

        fig.tight_layout(pad=1.2)
        fig.subplots_adjust(left=0.06, right=0.97, bottom=0.12, top=0.89)

        self.fig = fig
        return fig

    def create_inflow_outflow_chart(self, ax, title):
        if not self.reservoirs:
            raise ValueError("Reservoir list cannot be empty")

        active_reservoirs = [r for r in self.reservoirs
                           if getattr(r, 'inflow_parts', []) or getattr(r, 'outflow_parts', [])]

        if not active_reservoirs:
            raise ValueError("No reservoirs with inflow or outflow data")

        reservoirs = active_reservoirs
        names = [r.name for r in reservoirs]
        x_pos = np.arange(len(names))
        bar_width = 0.33

        edge_color = 'black'
        show_gap_water = True

        # Draw bars
        for i, r in enumerate(reservoirs):
            _draw_outflow_bar(ax, i, r, x_pos, bar_width, edge_color)
            _draw_inflow_bar(ax, i, r, show_gap_water, x_pos, bar_width, edge_color)

        # Difference connectors
        for i, r in enumerate(reservoirs):
            total_left_af = (sum(a for _, a, _ in getattr(r, 'outflow_parts', [])) +
                             sum(a for _, a, _ in getattr(r, 'pump_parts', [])) +
                             sum(a for _, a, _ in getattr(r, 'evap_parts', [])))

            total_right_af = (sum(a for _, a, _ in getattr(r, 'inflow_parts', [])) +
                              sum(a for _, a, _ in getattr(r, 'side_inflow_parts', [])))

            _draw_difference_connector(ax, i, total_left_af, total_right_af, x_pos, bar_width)

        # ==================== LEGENDS ====================
        main_handles = [
            mpatches.Patch(color=Reservoir.outflow_actual_color, label='Outflow Actual'),
            mpatches.Patch(color=Reservoir.outflow_projected_color, label='Outflow Projected'),
            mpatches.Patch(color=Reservoir.evap_actual_color, label='Evaporation Actual'),
            mpatches.Patch(color=Reservoir.evap_projected_color, label='Evaporation Projected'),
            mpatches.Patch(color=Reservoir.inflow_actual_color, label='Inflow Actual'),
            mpatches.Patch(color=Reservoir.inflow_projected_color, label='Inflow Projected'),
            mpatches.Patch(color=Reservoir.side_inflow_actual_color, label='Side Inflow Actual'),
            mpatches.Patch(color=Reservoir.side_inflow_projected_color, label='Side Inflow Projected'),
            mpatches.Patch(color=Reservoir.snwa_pump_actual_color, label='SNWA Actual'),
            mpatches.Patch(color=Reservoir.snwa_pump_projected_color, label='SNWA Projected')
        ]
        leg_main = ax.legend(handles=main_handles, loc='upper right',
                             title="Main Components", title_fontsize=10.5,
                             fontsize=10, framealpha=0.95, bbox_to_anchor=(0.98, 1.0))

        gap_handles = []
        leg_gap = None
        if show_gap_water:
            seen = set()
            for r in reservoirs:
                for full_label, amount, color in getattr(r, 'gap_water_parts', []):
                    if amount > 0:
                        clean_label = str(full_label).strip()
                        if clean_label not in seen:
                            seen.add(clean_label)
                            gap_handles.append(mpatches.Patch(color=color, label=clean_label))
            if gap_handles:
                leg_gap = ax.legend(handles=gap_handles, loc='upper right',
                                    title="Gap Water", title_fontsize=10.5,
                                    fontsize=10, framealpha=0.95,
                                    bbox_to_anchor=(0.82, 1.0))
                ax.add_artist(leg_main)

        ax.add_artist(leg_main)
        if show_gap_water and gap_handles and leg_gap is not None:
            ax.add_artist(leg_gap)

        # Final layout
        self.final_layout(ax, title, names, x_pos)


# ====================== HELPER FUNCTIONS ======================

def _draw_outflow_bar(ax, i, r, x_pos, bar_width, edge_color):
    bottom = 0.0
    outflow_only_total = 0.0
    left_x = x_pos[i] - 0.18 - bar_width/2 - 0.11

    # Outflow
    outflow_parts = getattr(r, 'outflow_parts', [])
    j = 0
    while j < len(outflow_parts):
        label, amount_af, color = outflow_parts[j]
        if amount_af > 0:
            maf = amount_af / 1_000_000
            current_bottom = bottom

            bar = ax.bar(x_pos[i] - 0.18, maf, width=bar_width,
                         bottom=current_bottom, color=color, alpha=0.92, edgecolor=edge_color)[0]

            if maf >= 0.35:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, current_bottom + maf / 2),
                            ha='center', va='center', fontsize=10, fontweight='bold', color='black')

            if "Actual" in label and j + 1 < len(outflow_parts):
                next_label, next_amount_af, next_color = outflow_parts[j + 1]
                if "Projected" in next_label:
                    next_maf = next_amount_af / 1_000_000
                    proj_bottom = current_bottom + maf
                    proj_bar = ax.bar(x_pos[i] - 0.18, next_maf, width=bar_width,
                                      bottom=proj_bottom, color=next_color, alpha=0.92, edgecolor=edge_color)[0]

                    if next_maf >= 0.35:
                        ax.annotate(f'{next_maf:.2f}',
                                    xy=(proj_bar.get_x() + proj_bar.get_width() / 2, proj_bottom + next_maf / 2),
                                    ha='center', va='center', fontsize=10, fontweight='bold', color='black')

                    _draw_vertical_connector(ax, left_x, current_bottom, proj_bottom + next_maf)

                    total_maf = maf + next_maf
                    ax.annotate(f'{total_maf:.2f}',
                                xy=(left_x, (current_bottom + proj_bottom + next_maf) / 2),
                                ha='center', va='center', fontsize=9.8, fontweight='bold', color='black')

                    bottom = proj_bottom + next_maf
                    outflow_only_total += (amount_af + next_amount_af)
                    j += 2
                    continue

            bottom += maf
            outflow_only_total += amount_af
        j += 1

    # Pumps
    pump_parts = getattr(r, 'pump_parts', [])
    j = 0
    while j < len(pump_parts):
        label, amount_af, color = pump_parts[j]
        if "Actual" in label and j + 1 < len(pump_parts):
            next_label, next_amount_af, next_color = pump_parts[j + 1]
            if "Projected" in next_label:
                maf = amount_af / 1_000_000
                next_maf = next_amount_af / 1_000_000
                actual_bottom = bottom
                projected_top = bottom + maf + next_maf

                ax.bar(x_pos[i] - 0.18, maf, width=bar_width,
                       bottom=actual_bottom, color=color, alpha=0.90, edgecolor=edge_color)
                ax.bar(x_pos[i] - 0.18, next_maf, width=bar_width,
                       bottom=actual_bottom + maf, color=next_color, alpha=0.90, edgecolor=edge_color)

                if maf >= 0.35:
                    ax.annotate(f'{maf:.2f}', xy=(x_pos[i] - 0.18, actual_bottom + maf / 2),
                                ha='center', va='center', fontsize=10, fontweight='bold', color='black')
                if next_maf >= 0.35:
                    ax.annotate(f'{next_maf:.2f}', xy=(x_pos[i] - 0.18, actual_bottom + maf + next_maf / 2),
                                ha='center', va='center', fontsize=10, fontweight='bold', color='black')

                _draw_vertical_connector(ax, left_x, actual_bottom, projected_top)

                total_maf = maf + next_maf
                draw_pump_name = getattr(r, 'draw_pump_name', True)
                note = f"{label.replace(' Actual', '').strip()} {total_maf:.2f}" if draw_pump_name else f"{total_maf:.2f}"
                ax.annotate(note, xy=(left_x + 0.1, (actual_bottom + projected_top) / 2),
                            ha='right', va='center', fontsize=9.7, fontweight='bold', color='black')

                bottom = projected_top
                j += 2
                continue

        if amount_af > 0:
            maf = amount_af / 1_000_000
            ax.bar(x_pos[i] - 0.18, maf, width=bar_width, bottom=bottom,
                   color=color, alpha=0.90, edgecolor=edge_color)
            bottom += maf
        j += 1

    # Evaporation
    for label, amount_af, color in getattr(r, 'evap_parts', []):
        if amount_af > 0:
            maf = amount_af / 1_000_000
            bar = ax.bar(x_pos[i] - 0.18, maf, width=bar_width,
                         bottom=bottom, color=color, alpha=0.88, edgecolor=edge_color)[0]

            if maf >= 0.4:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, bottom + maf / 2),
                            ha='center', va='center', fontsize=10, fontweight='bold', color='black')
            bottom += maf

    # Total left
    total_left_af = outflow_only_total + sum(a for _, a, _ in getattr(r, 'pump_parts', [])) + \
                    sum(a for _, a, _ in getattr(r, 'evap_parts', []))
    if total_left_af > 0:
        total_maf = total_left_af / 1_000_000
        ax.annotate(f'{total_maf:.2f}',
                    xy=(x_pos[i] - 0.18, total_maf),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='black')


def _draw_inflow_bar(ax, i, r, show_gap_water, x_pos, bar_width, edge_color):
    bottom = 0.0

    # Main Inflow
    for label, amount_af, color in getattr(r, 'inflow_parts', []):
        if amount_af > 0:
            maf = amount_af / 1_000_000
            bar = ax.bar(x_pos[i] + 0.18, maf, width=bar_width,
                         bottom=bottom, color=color, alpha=0.92, edgecolor='darkgreen')[0]

            if maf >= 0.4:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, bottom + maf / 2),
                            ha='center', va='center', fontsize=10, fontweight='bold', color='black')
            bottom += maf

    # Side Inflow
    for label, amount_af, color in getattr(r, 'side_inflow_parts', []):
        if amount_af > 0:
            maf = amount_af / 1_000_000
            bar = ax.bar(x_pos[i] + 0.18, maf, width=bar_width,
                         bottom=bottom, color=color, alpha=0.85, edgecolor=edge_color)[0]

            if maf >= 0.35:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, bottom + maf / 2),
                            ha='center', va='center', fontsize=10, fontweight='bold', color='black')
            bottom += maf

    # Gap Water
    if show_gap_water:
        gap_water_parts = getattr(r, 'gap_water_parts', [])
        if gap_water_parts:
            gap_x = x_pos[i] + 0.18 + bar_width/2 + 0.13
            current_bottom = bottom

            for label, amount_af, color in gap_water_parts:
                if amount_af > 0:
                    maf = amount_af / 1_000_000
                    bar = ax.bar(gap_x, maf, width=bar_width * 0.65,
                                 bottom=current_bottom, color=color, alpha=0.92,
                                 edgecolor='darkgoldenrod')[0]

                    if maf >= 0.35:
                        ax.annotate(f'{maf:.2f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, current_bottom + maf / 2),
                                    ha='center', va='center', fontsize=9.5, fontweight='bold', color='black')
                    current_bottom += maf

            total_gap_af = sum(a for _, a, _ in gap_water_parts)
            if total_gap_af > 0:
                ax.annotate(f'{total_gap_af / 1_000_000:.2f}',
                            xy=(gap_x, current_bottom),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='black')

    # Total inflow
    total_in_af = (sum(a for _, a, _ in getattr(r, 'inflow_parts', [])) +
                   sum(a for _, a, _ in getattr(r, 'side_inflow_parts', [])))
    if total_in_af > 0:
        ax.annotate(f'{total_in_af / 1_000_000:.2f}',
                    xy=(x_pos[i] + 0.18, total_in_af / 1_000_000),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='black')


def _draw_vertical_connector(ax, x, bottom, top):
    ax.plot([x, x], [bottom, top], color='black', linewidth=1.0, linestyle='--', alpha=0.75)
    if bottom > 0:
        ax.plot([x - 0.05, x + 0.05], [bottom, bottom], color='black', linewidth=1.0, alpha=0.75)
    ax.plot([x - 0.05, x + 0.05], [top, top], color='black', linewidth=1.0, alpha=0.75)


def _draw_difference_connector(ax, i, total_left_af, total_right_af, x_pos, bar_width):
    """Fixed version - scaled correctly in MAF"""
    diff_af = abs(total_left_af - total_right_af)
    diff_maf = diff_af / 1_000_000
    if diff_maf <= 0.4:
        return

    if total_left_af < total_right_af:
        smaller_maf = total_left_af / 1_000_000
        larger_maf = total_right_af / 1_000_000
        smaller_x = x_pos[i] - 0.18
        diff_color = 'darkgreen'
    else:
        smaller_maf = total_right_af / 1_000_000
        larger_maf = total_left_af / 1_000_000
        smaller_x = x_pos[i] + 0.18
        diff_color = 'darkred'

    top_y = larger_maf
    bottom_y = smaller_maf
    gap_center_y = (top_y + bottom_y) / 2

    # Adaptive gap that stays inside the plot
    gap_offset = max(0.3, diff_maf * 0.22)

    ax.plot([smaller_x, smaller_x], [bottom_y, gap_center_y - gap_offset],
            color='black', linewidth=1.0, linestyle='--', alpha=0.75)
    ax.plot([smaller_x, smaller_x], [gap_center_y + gap_offset, top_y],
            color='black', linewidth=1.0, linestyle='--', alpha=0.75)

    horizontal_left = smaller_x - bar_width / 2
    horizontal_right = smaller_x + bar_width / 2

    ax.plot([horizontal_left, horizontal_right], [bottom_y, bottom_y],
            color='black', linewidth=1.0, alpha=0.75, linestyle='--')
    ax.plot([horizontal_left, horizontal_right], [top_y, top_y],
            color='black', linewidth=1.0, alpha=0.75, linestyle='--')

    if diff_maf < 0.6:
        ax.annotate(f'{diff_maf:.2f}', xy=(smaller_x, top_y),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=diff_color)
    else:
        ax.annotate(f'{diff_maf:.2f}', xy=(smaller_x, gap_center_y),
                    ha='center', va='center', fontsize=9.5, fontweight='bold', color=diff_color)