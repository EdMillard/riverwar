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

def create_inflow_outflow_chart(reservoirs, title="Reservoir Inflow Loss Outflow"):
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    # Filter out reservoirs with no inflow or outflow data
    active_reservoirs = []
    for r in reservoirs:
        inflow = getattr(r, 'inflow_parts', [])
        outflow = getattr(r, 'outflow_parts', [])
        if (inflow and len(inflow) > 0) or (outflow and len(outflow) > 0):
            active_reservoirs.append(r)

    if not active_reservoirs:
        raise ValueError("No reservoirs with inflow or outflow data")

    reservoirs = active_reservoirs

    names = [r.name for r in reservoirs]
    x_pos = np.arange(len(names))
    bar_width = 0.33

    fig = Figure(figsize=(14.2, 5.4), dpi=100)
    ax = fig.add_subplot(111)

    edge_color = 'black'

    # ==================== DRAW BARS ====================
    for i, r in enumerate(reservoirs):
        _draw_outflow_bar(ax, i, r, x_pos, bar_width, edge_color)
        _draw_inflow_bar(ax, i, r, x_pos, bar_width, edge_color)

    # ==================== DIFFERENCE GAP CONNECTOR ====================
    for i, r in enumerate(reservoirs):
        total_left = (sum(a for _, a, _ in getattr(r, 'outflow_parts', [])) +
                      sum(a for _, a, _ in getattr(r, 'pump_parts', [])) +
                      sum(a for _, a, _ in getattr(r, 'evap_parts', [])))

        total_right = (sum(a for _, a, _ in getattr(r, 'inflow_parts', [])) +
                       sum(a for _, a, _ in getattr(r, 'side_inflow_parts', [])))

        _draw_difference_connector(ax, i, total_left, total_right, x_pos, bar_width)

    # ==================== LEGENDS ====================
    main_handles = [
        mpatches.Patch(color=Reservoir.outflow_actual_color, label='Outflow Actual'),
        mpatches.Patch(color=Reservoir.outflow_projected_color, label='Outflow Projected'),
        mpatches.Patch(color=Reservoir.evap_actual_color, label='Evaporation Actual'),
        mpatches.Patch(color=Reservoir.evap_projected_color, label='Evaporation Projected'),
        mpatches.Patch(color=Reservoir.inflow_actual_color, label='Inflow Actual'),
        mpatches.Patch(color=Reservoir.inflow_projected_color, label='Inflow Projected'),
        mpatches.Patch(color=Reservoir.side_inflow_actual_color, label='Side Inflow Actual'),
        mpatches.Patch(color=Reservoir.side_inflow_projected_color, label='Side Inflow Projected')
    ]
    leg_main = ax.legend(handles=main_handles, loc='upper right',
                         title="Main Components", title_fontsize=10.5,
                         fontsize=10, framealpha=0.95, bbox_to_anchor=(0.98, 1.0))

    pump_handles = []
    seen = set()
    for r in reservoirs:
        for full_label, amount, color in getattr(r, 'pump_parts', []):
            if amount > 0 and full_label not in seen:
                seen.add(full_label)
                pump_handles.append(mpatches.Patch(color=color, label=full_label))

    if pump_handles:
        leg_pump = ax.legend(handles=pump_handles, loc='upper right',
                             title="Pumping Plants", title_fontsize=10.5,
                             fontsize=10, framealpha=0.95, bbox_to_anchor=(0.124, 1.0))
        ax.add_artist(leg_main)

    # Layout matching reservoir chart
    ax.set_xlabel('')
    ax.set_ylabel('Volume (Million Acre-Feet)', fontsize=11.5, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10.5)
    ax.grid(axis='y', linestyle='--', alpha=0.65)
    ax.set_axisbelow(True)

    fig.tight_layout(pad=1.2)
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.12, top=0.89)

    return fig


# ====================== HELPER FUNCTIONS ======================

def _draw_outflow_bar(ax, i, r, x_pos, bar_width, edge_color):
    """Left bar: Outflow + Pumps + Evaporation"""
    bottom = 0.0
    outflow_only_total = 0.0
    left_x = x_pos[i] - 0.18 - bar_width/2 - 0.11

    # ==================== OUTFLOW ====================
    outflow_parts = getattr(r, 'outflow_parts', [])
    j = 0
    while j < len(outflow_parts):
        label, amount, color = outflow_parts[j]
        if amount > 0:
            current_bottom = bottom
            maf = amount / 1_000_000

            bar = ax.bar(x_pos[i] - 0.18, amount, width=bar_width,
                         bottom=current_bottom, color=color, alpha=0.92, edgecolor=edge_color)[0]

            if maf >= 0.35:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, current_bottom + amount / 2),
                            ha='center', va='center',
                            fontsize=10, fontweight='bold', color='black')

            if "Actual" in label and j + 1 < len(outflow_parts):
                next_label, next_amount, next_color = outflow_parts[j + 1]
                if "Projected" in next_label:
                    proj_bottom = current_bottom + amount
                    proj_bar = ax.bar(x_pos[i] - 0.18, next_amount, width=bar_width,
                                      bottom=proj_bottom, color=next_color, alpha=0.92, edgecolor=edge_color)[0]

                    if (next_amount / 1_000_000) >= 0.35:
                        ax.annotate(f'{(next_amount / 1_000_000):.2f}',
                                    xy=(proj_bar.get_x() + proj_bar.get_width() / 2, proj_bottom + next_amount / 2),
                                    ha='center', va='center',
                                    fontsize=10, fontweight='bold', color='black')

                    actual_bottom = current_bottom
                    projected_top = proj_bottom + next_amount

                    _draw_vertical_connector(ax, left_x, actual_bottom, projected_top)

                    total_maf = (amount + next_amount) / 1_000_000
                    ax.annotate(f'{total_maf:.2f}',
                                xy=(left_x, (actual_bottom + projected_top) / 2),
                                ha='center', va='center',
                                fontsize=9.8, fontweight='bold', color='black')

                    bottom = projected_top
                    outflow_only_total += (amount + next_amount)
                    j += 2
                    continue

            bottom += amount
            outflow_only_total += amount
        j += 1

    # ==================== PUMPS ====================
    pump_parts = getattr(r, 'pump_parts', [])
    j = 0
    while j < len(pump_parts):
        label, amount, color = pump_parts[j]
        if "Actual" in label and j + 1 < len(pump_parts):
            next_label, next_amount, next_color = pump_parts[j + 1]
            if "Projected" in next_label:
                actual_bottom = bottom
                projected_top = bottom + amount + next_amount

                ax.bar(x_pos[i] - 0.18, amount, width=bar_width,
                       bottom=actual_bottom, color=color, alpha=0.90, edgecolor=edge_color)
                ax.bar(x_pos[i] - 0.18, next_amount, width=bar_width,
                       bottom=actual_bottom + amount, color=next_color, alpha=0.90, edgecolor=edge_color)

                if amount / 1_000_000 >= 0.35:
                    ax.annotate(f'{(amount / 1_000_000):.2f}',
                                xy=(x_pos[i] - 0.18, actual_bottom + amount / 2),
                                ha='center', va='center', fontsize=10, fontweight='bold', color='black')
                if next_amount / 1_000_000 >= 0.35:
                    ax.annotate(f'{(next_amount / 1_000_000):.2f}',
                                xy=(x_pos[i] - 0.18, actual_bottom + amount + next_amount / 2),
                                ha='center', va='center', fontsize=10, fontweight='bold', color='black')

                _draw_vertical_connector(ax, left_x, actual_bottom, projected_top)

                total_maf = (amount + next_amount) / 1_000_000
                draw_pump_name = getattr(r, 'draw_pump_name', True)
                if draw_pump_name:
                    pump_name = label.replace(" Actual", "").replace(" Projected", "").strip()
                    note = f"{pump_name} {total_maf:.2f}"
                else:
                    note = f"{total_maf:.2f}"

                ax.annotate(note,
                            xy=(left_x+0.1, (actual_bottom + projected_top) / 2),
                            ha='right', va='center',
                            fontsize=9.7, fontweight='bold', color='black')

                bottom = projected_top
                j += 2
                continue

        # Single pump entry (fallback)
        if amount > 0:
            ax.bar(x_pos[i] - 0.18, amount, width=bar_width, bottom=bottom,
                   color=color, alpha=0.90, edgecolor=edge_color)
            bottom += amount
        j += 1

    # ==================== EVAPORATION ====================
    evap_total = 0.0
    for label, amount, color in getattr(r, 'evap_parts', []):
        if amount > 0:
            maf = amount / 1_000_000
            bar = ax.bar(x_pos[i] - 0.18, amount, width=bar_width,
                         bottom=bottom, color=color, alpha=0.88,
                         edgecolor=edge_color)[0]

            if maf >= 0.4:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, bottom + amount / 2),
                            ha='center', va='center',
                            fontsize=10, fontweight='bold', color='black')
            bottom += amount
            evap_total += amount

    # Total left annotation
    total_left = outflow_only_total + evap_total + sum(a for _, a, _ in getattr(r, 'pump_parts', []))
    if total_left > 0:
        ax.annotate(f'{total_left / 1_000_000:.2f}',
                    xy=(x_pos[i] - 0.18, total_left),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=11.5, fontweight='bold', color='black')


def _draw_inflow_bar(ax, i, r, x_pos, bar_width, edge_color):
    """Right bar: Inflow + Side Inflow + Gap Water"""
    bottom = 0.0

    # Main Inflow
    for label, amount, color in getattr(r, 'inflow_parts', []):
        if amount > 0:
            maf = amount / 1_000_000
            bar = ax.bar(x_pos[i] + 0.18, amount, width=bar_width,
                         bottom=bottom, color=color, alpha=0.92, edgecolor='darkgreen')[0]

            if maf >= 0.4:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, bottom + amount / 2),
                            ha='center', va='center',
                            fontsize=10, fontweight='bold', color='black')
            bottom += amount

    # Side Inflow
    for label, amount, color in getattr(r, 'side_inflow_parts', []):
        if amount > 0:
            maf = amount / 1_000_000
            bar = ax.bar(x_pos[i] + 0.18, amount, width=bar_width,
                         bottom=bottom, color=color, alpha=0.85, edgecolor=edge_color)[0]

            if maf >= 0.35:
                ax.annotate(f'{maf:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, bottom + amount / 2),
                            ha='center', va='center',
                            fontsize=10, fontweight='bold', color='black')
            bottom += amount

    # Gap Water
    gap_water_parts = getattr(r, 'gap_water_parts', [])
    if gap_water_parts:
        gap_x = x_pos[i] + 0.18 + bar_width/2 + 0.13
        current_bottom = bottom

        for label, amount, color in gap_water_parts:
            if amount > 0:
                maf = amount / 1_000_000
                bar = ax.bar(gap_x, amount, width=bar_width * 0.65,
                             bottom=current_bottom, color=color, alpha=0.92,
                             edgecolor='darkgoldenrod')[0]

                if maf >= 0.35:
                    ax.annotate(f'{maf:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, current_bottom + amount / 2),
                                ha='center', va='center',
                                fontsize=9.5, fontweight='bold', color='black')

                ax.annotate(label,
                            xy=(gap_x + bar_width*0.65/2 + 0.09, current_bottom + amount / 2),
                            ha='left', va='center',
                            fontsize=9.5, fontweight='bold', color='black')

                current_bottom += amount

        total_gap = sum(a for _, a, _ in gap_water_parts)
        if total_gap > 0:
            ax.annotate(f'{total_gap / 1_000_000:.2f}',
                        xy=(gap_x, current_bottom),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10.5, fontweight='bold', color='black')

    # Total inflow annotation
    total_in = (sum(a for _, a, _ in getattr(r, 'inflow_parts', [])) +
                sum(a for _, a, _ in getattr(r, 'side_inflow_parts', [])))
    if total_in > 0:
        ax.annotate(f'{total_in / 1_000_000:.2f}',
                    xy=(x_pos[i] + 0.18, total_in),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=11.5, fontweight='bold', color='black')


def _draw_vertical_connector(ax, x, bottom, top):
    ax.plot([x, x], [bottom, top], color='black', linewidth=1.0, linestyle='--', alpha=0.75)
    if bottom > 0:
        ax.plot([x - 0.05, x + 0.05], [bottom, bottom], color='black', linewidth=1.0, alpha=0.75)
    ax.plot([x - 0.05, x + 0.05], [top, top], color='black', linewidth=1.0, alpha=0.75)


def _draw_difference_connector(ax, i, total_left, total_right, x_pos, bar_width):
    diff_af = abs(total_left - total_right)
    diff_maf = diff_af / 1_000_000
    if diff_maf <= 0.4:
        return

    if total_left < total_right:
        smaller_total = total_left
        larger_total = total_right
        smaller_center_x = x_pos[i] - 0.18
        diff_color = 'darkgreen'
    else:
        smaller_total = total_right
        larger_total = total_left
        smaller_center_x = x_pos[i] + 0.18
        diff_color = 'darkred'

    top_y = larger_total
    bottom_y = smaller_total
    gap_center_y = (top_y + bottom_y) / 2
    gap_offset = 800

    ax.plot([smaller_center_x, smaller_center_x], [bottom_y, gap_center_y - gap_offset],
            color='black', linewidth=1.0, alpha=0.75, linestyle='--')
    ax.plot([smaller_center_x, smaller_center_x], [gap_center_y + gap_offset, top_y],
            color='black', linewidth=1.0, alpha=0.75, linestyle='--')

    horiz_left = smaller_center_x - bar_width / 2
    horiz_right = smaller_center_x + bar_width / 2
    ax.plot([horiz_left, horiz_right], [bottom_y, bottom_y],
            color='black', linewidth=1.0, alpha=0.75, linestyle='--')
    ax.plot([horiz_left, horiz_right], [top_y, top_y],
            color='black', linewidth=1.0, alpha=0.75, linestyle='--')

    if diff_maf < 0.6:
        ax.annotate(f'{diff_maf:.2f}', xy=(smaller_center_x, top_y),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=diff_color)
    else:
        ax.annotate(f'{diff_maf:.2f}', xy=(smaller_center_x, gap_center_y),
                    ha='center', va='center', fontsize=9.5, fontweight='bold', color=diff_color)