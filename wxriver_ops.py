"""
Reservoir Dashboard - Stacked bar annotations restored + compact heights
"""

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib
import datetime
import colorado.lb as lb
from datetime import datetime
import os
import pandas as pd
from reservoirs.reservoir import Reservoir
from reservoirs.lake_havasu import LakeHavasu
from reservoirs.lake_mohave import LakeMohave
from reservoirs.aquifers import Aquifers
from reservoirs.lake_mead import LakeMead
from reservoirs.lake_powell import LakePowell
from reservoirs.flaming_gorge import FlamingGorge
from reservoirs.blue_mesa import BlueMesa
from reservoirs.navajo import Navajo
from reservoirs.lake_pleasant import LakePleasant

import numpy as np
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

os.environ['QT_QPA_PLATFORM'] = 'offscreen'      # Most important for Qt errors
os.environ['MPLBACKEND'] = 'Agg'                 # Non-interactive matplotlib backend
matplotlib.use('Agg')
os.environ['QT_SILENT'] = '1'

def create_capacity_chart(
    reservoirs,
    title="Reservoir Active Capacity",
    power_head_zones=None,
    reserved_zones=None,
    show_reserved_connector=True
):
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    if power_head_zones is None:
        power_head_zones = [(Reservoir.high_power_pool_color, 'FIXME')]

    if reserved_zones is None:
        reserved_zones = [('darkgoldenrod', 'Reserved')]

    names = [r.name for r in reservoirs]
    capacities_maf = [r.active_capacity_af / 1_000_000 for r in reservoirs]
    elevations_feet = [r.elevation_feet for r in reservoirs]

    fig = Figure(figsize=(14.8, 6.5), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    reserved_width = 0.26
    main_width = 0.55

    # ==================== RESERVED BARS (Aquifers) ====================
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

            # Gap logic...
            crit_points = getattr(r, 'critical_elevations_feet', [])
            lower_critical_maf = 0.0
            for item in crit_points:
                if isinstance(item, (list, tuple)) and len(item) >= 4:
                    cap_maf = item[2] / 1_000_000
                    if cap_maf <= reserved_bottom:
                        lower_critical_maf = cap_maf
                    else:
                        break

            gap_delta = reserved_bottom - lower_critical_maf
            if gap_delta > 0:
                gap_center_y = (reserved_bottom + lower_critical_maf) / 2
                gap_offset = 0.18

                ax.plot([reserved_x_center, reserved_x_center],
                        [reserved_bottom, gap_center_y + gap_offset],
                        color='black', linewidth=1.0, alpha=0.75, linestyle='--')
                ax.plot([reserved_x_center, reserved_x_center],
                        [gap_center_y - gap_offset, lower_critical_maf],
                        color='black', linewidth=1.0, alpha=0.75, linestyle='--')

                ax.annotate(f'{gap_delta:.3f}',
                            xy=(reserved_x_center, gap_center_y),
                            ha='center', va='center',
                            fontsize=9.5, fontweight='bold', color='black')

                horiz_left = reserved_x_center - reserved_width / 2
                horiz_right = reserved_x_center + reserved_width / 2
                ax.plot([horiz_left, horiz_right],
                        [lower_critical_maf, lower_critical_maf],
                        color='black', linewidth=1.0, alpha=0.75, linestyle='--')

            if show_reserved_connector:
                ax.bar(x_pos[i] - main_width/2 + 0.02, total_reserved_maf, width=0.04,
                       bottom=main_bar_maf - total_reserved_maf,
                       color='gray', alpha=0.18, edgecolor=None)

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

    # ==================== SPECIAL LEVELS (Improved Triangle) ====================
    for i, r in enumerate(reservoirs):
        special_levels = getattr(r, 'special_levels', [])
        if not special_levels:
            continue

        x = x_pos[i]
        right_x = x + main_width * 0.52 + 0.04   # slight extra spacing for text

        for elev_ft, cap_af, label in special_levels:
            cap_maf = cap_af / 1_000_000

            # Triangle moved slightly inside the bar and made smaller
            ax.plot(x + main_width/2 - 0.035, cap_maf, marker='<', markersize=8.5,
                    color='black', markeredgecolor='black', markerfacecolor='white')

            # Clean two-line annotation (no bubble)
            annot_text = f'{elev_ft:,.0f}\'\n{label}'

            ax.annotate(annot_text,
                        xy=(right_x, cap_maf),
                        ha='left', va='center',
                        fontsize=9.5, fontweight='bold', color='black')

    # Top total MAF and top elevation
    for i in range(len(names)):
        ax.annotate(f'{capacities_maf[i]:.3f}',
                    xy=(x_pos[i], capacities_maf[i]),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10.5, fontweight='bold', color='black')

        if elevations_feet[i]:
            ax.annotate(f'{elevations_feet[i]:,.2f}\'',
                        xy=(x_pos[i] + main_width * 0.52, capacities_maf[i]),
                        ha='left', va='center',
                        fontsize=9.5, color='darkgreen', fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.25", facecolor="lightyellow", alpha=0.9))

    # ==================== LEGENDS ====================
    power_patches = [mpatches.Patch(color=color, label=label) for color, label in power_head_zones]
    leg_power = ax.legend(handles=power_patches, title="Power Head Zones",
                          loc='upper right', bbox_to_anchor=(0.98, 1.0),
                          fontsize=9, title_fontsize=10, framealpha=0.95)

    state_patches = [mpatches.Patch(color=color, label=label) for color, label in reserved_zones]
    leg_ics = ax.legend(handles=state_patches, title="ICS 2024 EoY",
                        loc='upper right', bbox_to_anchor=(0.79, 1.0),
                        fontsize=9, title_fontsize=10, framealpha=0.95)

    aquifer_patches = [
        mpatches.Patch(color=lb.TUCSON_COLOR, label='Tucson AMA'),
        mpatches.Patch(color=lb.PINAL_COLOR, label='Pinal AMA'),
        mpatches.Patch(color=lb.PHX_COLOR, label='Phoenix AMA')
    ]
    leg_aquifer = ax.legend(handles=aquifer_patches, title="Aquifer Storage 2023 EOY (LTSC)",
                            loc='upper left', bbox_to_anchor=(0.02, 1.0),
                            fontsize=9, title_fontsize=10, framealpha=0.95)

    ax.add_artist(leg_power)
    ax.add_artist(leg_ics)

    # Labels and layout
    ax.set_xlabel('')
    ax.set_ylabel('Volume (Million Acre-Feet)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10.5)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    fig.tight_layout(pad=1.2)
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.12, top=0.89)

    return fig

def create_inflow_outflow_chart(reservoirs, title="Reservoir Inflow vs Outflow"):
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    names = [r.name for r in reservoirs]
    x_pos = np.arange(len(names))
    bar_width = 0.33

    fig = Figure(figsize=(14.2, 5.4), dpi=100)
    ax = fig.add_subplot(111)

    # ==================== OUTFLOW + EVAP STACKED (Left) ====================
    for i, r in enumerate(reservoirs):
        bottom = 0.0
        outflow_only_total = 0.0

        for label, amount, color in getattr(r, 'outflow_parts', []):
            if amount > 0:
                maf = amount / 1_000_000
                bar = ax.bar(x_pos[i] - 0.18, amount, width=bar_width,
                             bottom=bottom, color=color, alpha=0.92, edgecolor='darkred')[0]

                if maf >= 0.4:
                    ax.annotate(f'{maf:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, bottom + amount / 2),
                                ha='center', va='center',
                                fontsize=10, fontweight='bold', color='black')
                bottom += amount
                outflow_only_total += amount

        evap_total = 0.0
        for label, amount, color in getattr(r, 'evap_parts', []):
            if amount > 0:
                maf = amount / 1_000_000
                bar = ax.bar(x_pos[i] - 0.18, amount, width=bar_width,
                             bottom=bottom, color=color, alpha=0.92, edgecolor='darkred')[0]

                if maf >= 0.4:
                    ax.annotate(f'{maf:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, bottom + amount / 2),
                                ha='center', va='center',
                                fontsize=10, fontweight='bold', color='black')
                bottom += amount
                evap_total += amount

        total_left = outflow_only_total + evap_total
        if total_left > 0:
            ax.annotate(f'{total_left / 1_000_000:.2f}',
                        xy=(x_pos[i] - 0.18, total_left),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=11.5, fontweight='bold', color='black')

        # === UPDATED: Moved further left (another ~one digit) ===
        if outflow_only_total > 0:
            outflow_maf = outflow_only_total / 1_000_000
            text_x = x_pos[i] - 0.18 - bar_width/2 - 0.02   # further left

            ax.annotate(f'{outflow_maf:.2f}',
                        xy=(text_x, outflow_only_total),
                        ha='right', va='center',
                        fontsize=9.8, fontweight='bold', color='black')

    # ==================== INFLOW (Right) ====================
    for i, r in enumerate(reservoirs):
        bottom = 0.0
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

        total_in = sum(a for _, a, _ in getattr(r, 'inflow_parts', []))
        if total_in > 0:
            ax.annotate(f'{total_in / 1_000_000:.2f}',
                        xy=(x_pos[i] + 0.18, total_in),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=11.5, fontweight='bold', color='black')

    # ==================== DIFFERENCE GAP CONNECTOR ====================
    for i, r in enumerate(reservoirs):
        total_left  = (sum(a for _, a, _ in getattr(r, 'outflow_parts', [])) +
                       sum(a for _, a, _ in getattr(r, 'evap_parts', [])))
        total_right = sum(a for _, a, _ in getattr(r, 'inflow_parts', []))

        if total_left == total_right or total_left == 0 or total_right == 0:
            continue

        if total_left < total_right:
            smaller_total = total_left
            larger_total  = total_right
            smaller_center_x = x_pos[i] - 0.18
            diff_color = 'darkgreen'
        else:
            smaller_total = total_right
            larger_total  = total_left
            smaller_center_x = x_pos[i] + 0.18
            diff_color = 'darkred'

        diff_af = larger_total - smaller_total
        if diff_af <= 0:
            continue

        diff_maf = diff_af / 1_000_000

        top_y = larger_total
        bottom_y = smaller_total

        gap_center_y = (top_y + bottom_y) / 2
        gap_offset = 800

        ax.plot([smaller_center_x, smaller_center_x],
                [bottom_y, gap_center_y - gap_offset],
                color='black', linewidth=1.0, alpha=0.75, linestyle='--')
        ax.plot([smaller_center_x, smaller_center_x],
                [gap_center_y + gap_offset, top_y],
                color='black', linewidth=1.0, alpha=0.75, linestyle='--')

        horiz_left = smaller_center_x - bar_width / 2
        horiz_right = smaller_center_x + bar_width / 2
        ax.plot([horiz_left, horiz_right], [bottom_y, bottom_y],
                color='black', linewidth=1.0, alpha=0.75, linestyle='--')
        ax.plot([horiz_left, horiz_right], [top_y, top_y],
                color='black', linewidth=1.0, alpha=0.75, linestyle='--')

        if diff_maf < 0.6:
            annot_y = top_y
            ax.annotate(f'{diff_maf:.2f}',
                        xy=(smaller_center_x, annot_y),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9.5, fontweight='bold', color=diff_color)
        else:
            ax.annotate(f'{diff_maf:.2f}',
                        xy=(smaller_center_x, gap_center_y),
                        ha='center', va='center',
                        fontsize=9.5, fontweight='bold', color=diff_color)

    # ==================== LEGEND ====================
    handles = [
        mpatches.Patch(color=Reservoir.outflow_actual_color, label='Outflow Actual'),
        mpatches.Patch(color=Reservoir.outflow_projected_color, label='Outflow Projected'),
        mpatches.Patch(color=Reservoir.evap_actual_color, label='Evaporation Actual'),
        mpatches.Patch(color=Reservoir.evap_projected_color, label='Evaporation Projected'),
        mpatches.Patch(color=Reservoir.inflow_actual_color, label='Inflow Actual'),
        mpatches.Patch(color=Reservoir.inflow_projected_color, label='Inflow Projected'),
        mpatches.Patch(color=Reservoir.side_inflow_actual_color, label='Side Inflow Actual'),
        mpatches.Patch(color=Reservoir.side_inflow_projected_color, label='Side Inflow Projected')
    ]
    ax.legend(handles=handles, loc='upper right', fontsize=10,
              title_fontsize=10.5, framealpha=0.95, bbox_to_anchor=(0.98, 1.0))

    ax.set_xlabel('')
    ax.set_ylabel('Volume (Million Acre-Feet)', fontsize=11.5, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10.5)
    ax.grid(axis='y', linestyle='--', alpha=0.65)
    ax.set_axisbelow(True)

    fig.tight_layout(pad=1.0)
    fig.subplots_adjust(left=0.07, right=0.96, bottom=0.15, top=0.89)

    return fig

def datetime64_to_str(dt64) -> str:
    """Convert pandas datetime64 to 'Mar 28, 2026' format"""
    if pd.isna(dt64):
        return ""
    dt = pd.to_datetime(dt64)
    return dt.strftime("%b %d, %Y")


class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoirs, date_time, title="Reservoir Analysis Dashboard"):
        super().__init__(None, title=title, size=wx.Size(1580, 1020))

        self.reservoirs = reservoirs

        # Main panel and notebook
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self.panel)

        # ==================== CAPACITY TAB ====================
        self.cap_panel = wx.Panel(self.notebook)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)

        date_str = datetime64_to_str(date_time)
        cap_title = f'Reservoir Storage - {date_str} AM - USBR RISE'

        power_zones = [
            (Reservoir.high_power_pool_color, 'Full Power Head'),
            (Reservoir.low_power_pool_color, 'Low Power Head'),
            (Reservoir.non_power_pool_color, 'Limited Access')
        ]

        reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]

        self.capacity_fig = create_capacity_chart(
            reservoirs,
            title=cap_title,
            power_head_zones=power_zones,
            reserved_zones=reserved_zones,
        )

        self.capacity_canvas = FigureCanvas(self.cap_panel, -1, self.capacity_fig)
        cap_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.cap_panel.SetSizer(cap_sizer)

        self.notebook.AddPage(self.cap_panel, "Capacity")

        # ==================== INFLOW / OUTFLOW TAB ====================
        self.in_panel = wx.Panel(self.notebook)
        in_sizer = wx.BoxSizer(wx.VERTICAL)

        self.inflow_fig = create_inflow_outflow_chart(reservoirs)

        self.inflow_canvas = FigureCanvas(self.in_panel, -1, self.inflow_fig)
        in_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.in_panel.SetSizer(in_sizer)

        self.notebook.AddPage(self.in_panel, "Inflow / Outflow")

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_cap_btn = wx.Button(self.panel, label="Save Capacity Chart as PNG")
        save_in_btn = wx.Button(self.panel, label="Save Inflow/Outflow Chart as PNG")

        save_cap_btn.Bind(wx.EVT_BUTTON, self.on_save_capacity)
        save_in_btn.Bind(wx.EVT_BUTTON, self.on_save_inflow)

        btn_sizer.AddStretchSpacer(1)
        btn_sizer.Add(save_cap_btn, 0, wx.ALL, 10)
        btn_sizer.Add(save_in_btn, 0, wx.ALL, 10)
        btn_sizer.AddStretchSpacer(1)

        # Main layout
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=12)

        self.panel.SetSizer(main_sizer)

        self.CreateStatusBar()
        self.SetStatusText(f"Displaying {len(reservoirs)} reservoirs")
        self.SetMinSize(wx.Size(1220, 820))
        self.Centre()

        # Resize handling
        self.panel.Bind(wx.EVT_SIZE, self.on_panel_resize)
        wx.CallAfter(self.force_resize)
        wx.CallLater(100, self.force_resize)

    def force_resize(self):
        """Force canvases to resize properly inside notebook tabs"""
        for canvas, panel in [(self.capacity_canvas, self.cap_panel),
                              (self.inflow_canvas, self.in_panel)]:
            if canvas and panel:
                size = panel.GetClientSize()
                if size[0] > 200 and size[1] > 150:
                    canvas.SetClientSize(size)
                    canvas.draw()
                    canvas.Refresh()

    def on_panel_resize(self, event):
        wx.CallAfter(self.force_resize)
        event.Skip()

    def on_save_capacity(self, event):
        self.save_figure(self.capacity_fig, "Capacity_Chart")

    def on_save_inflow(self, event):
        self.save_figure(self.inflow_fig, "Inflow_Outflow_Chart")

    def save_figure(self, fig, base_name):
        default_name = f"{base_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        wildcard = "PNG files (*.png)|*.png|All files (*.*)|*.*"
        with wx.FileDialog(self, "Save chart as PNG",
                           defaultDir=os.getcwd(), defaultFile=default_name,
                           wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    fig.savefig(dlg.GetPath(), dpi=200, bbox_inches='tight')
                    wx.MessageBox("Chart saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    wx.MessageBox(str(e), "Save Error", wx.OK | wx.ICON_ERROR)


# Keep your existing create_capacity_chart and create_inflow_outflow_chart functions unchanged
# (They are already defined above in your original code)

if __name__ == "__main__":
    # lake_pleasant = LakePleasant()
    lake_powell = LakePowell()

    reservoirs = [
        # lake_pleasant,
        LakeHavasu(),
        LakeMohave(),
        Aquifers(),
        LakeMead(),
        lake_powell,
        FlamingGorge(),
        Navajo(),
        BlueMesa()
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs, lake_powell.date_time)
    frame.Show()
    app.MainLoop()