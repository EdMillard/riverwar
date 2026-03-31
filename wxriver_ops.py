"""
Reservoir Dashboard - Stacked bar annotations restored + compact heights
"""

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import datetime
import colorado.lb as lb
import os
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
        power_head_zones = [
            ('lightblue', 'Power Head'),
            ('#FF746C', 'Lower Power Head'),
            ('#FFEE8C', 'Non Power Head')
        ]

    if reserved_zones is None:
        reserved_zones = [('darkgoldenrod', 'Reserved')]

    names = [r.name for r in reservoirs]
    capacities_maf = [r.active_capacity_af / 1_000_000 for r in reservoirs]
    elevations_feet = [r.elevation_feet for r in reservoirs]

    max_maf = max(capacities_maf) if capacities_maf else 10

    fig = Figure(figsize=(14.8, 6.5), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    reserved_width = 0.26
    main_width = 0.55

    # RESERVED BARS
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

            # Total reserved MAF just above the top of the reserved bar (restored)
            ax.annotate(f'{total_reserved_maf:.3f}',
                        xy=(reserved_x_center, main_bar_maf),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10.5, fontweight='bold', color='black')

            # Gap below reserved bar
            gap_center_y = (main_bar_maf - total_reserved_maf) / 2
            gap_offset = 0.18

            ax.plot([reserved_x_center, reserved_x_center],
                    [main_bar_maf - total_reserved_maf, gap_center_y + gap_offset],
                    color='black', linewidth=1.0, alpha=0.75, linestyle='--')

            ax.plot([reserved_x_center, reserved_x_center],
                    [gap_center_y - gap_offset, 0],
                    color='black', linewidth=1.0, alpha=0.75, linestyle='--')

            ax.annotate(f'{main_bar_maf - total_reserved_maf:.3f}',
                        xy=(reserved_x_center, gap_center_y),
                        ha='center', va='center',
                        fontsize=9.5, fontweight='bold', color='black')

            if show_reserved_connector:
                ax.bar(x_pos[i] - main_width/2 + 0.02, total_reserved_maf, width=0.04,
                       bottom=main_bar_maf - total_reserved_maf,
                       color='gray', alpha=0.18, edgecolor=None)

    # MAIN STACKED BARS
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
            if elevations_feet[i] > 0:
                segments.append((segment_height_maf, Reservoir.high_power_pool_color, 'Above Highest Critical', capacities_maf[i], elevations_feet[i]))
            else:
                segments.append((segment_height_maf, Reservoir.non_power_pool_color, 'Above Highest Critical', capacities_maf[i], elevations_feet[i]))

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
                ax.annotate(f'{elev_ft:,.0f} ft',
                            xy=(x_pos[i] + main_width * 0.52, current_bottom + height_maf),
                            ha='left', va='center',
                            fontsize=9, fontweight='bold', color='darkblue',
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))

            current_bottom += height_maf

    # Top total MAF for main bar
    for i in range(len(names)):
        ax.annotate(f'{capacities_maf[i]:.3f}',
                    xy=(x_pos[i], capacities_maf[i]),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10.5, fontweight='bold', color='black')

    # Elevation annotations centered at top
    for i in range(len(names)):
        if elevations_feet[i]:
            ax.annotate(f'{elevations_feet[i]:,.2f}',
                        xy=(x_pos[i] + main_width * 0.52, capacities_maf[i]),
                        ha='left', va='center',
                        fontsize=9.5, color='darkgreen', fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.25", facecolor="lightyellow", alpha=0.9))

    # ==================== TWO LEGENDS IN UPPER RIGHT ====================
    # Power Head Zones Legend (slightly left so it doesn't go off edge)
    power_patches = [mpatches.Patch(color=color, label=label) for color, label in power_head_zones]
    leg1 = ax.legend(handles=power_patches,
                     title="Power Head Zones",
                     loc='upper right',
                     bbox_to_anchor=(0.98, 1.0),   # moved slightly left
                     fontsize=9,
                     title_fontsize=10,
                     framealpha=0.95)

    # Reserved Legend - placed further right, closer to the Power Head legend
    reserved_patches = [mpatches.Patch(color=color, label=label) for color, label in reserved_zones]
    ax.legend(handles=reserved_patches,
              title="ICS 2024 EoY",
              loc='upper right',
              bbox_to_anchor=(0.79, 1.0),   # moved further right, next to first legend
              fontsize=9,
              title_fontsize=10,
              framealpha=0.95)

    ax.add_artist(leg1)

    # Labels
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
    bar_width = 0.30

    fig = Figure(figsize=(13.8, 4.3), dpi=100)
    ax = fig.add_subplot(111)

    # === INFLOW BARS WITH ANNOTATIONS ===
    for i, r in enumerate(reservoirs):
        current_bottom = 0
        for label, amount, color in getattr(r, 'inflow_parts', []):
            if amount > 0:
                bar = ax.bar(x_pos[i] - bar_width, amount, width=bar_width,
                             bottom=current_bottom, color=color, alpha=0.90, edgecolor='darkgreen')[0]

                # Annotation centered in each inflow segment
                if amount >= 800:
                    mid_y = current_bottom + amount / 2
                    ax.annotate(f'{amount:,.0f}',
                                xy=(bar.get_x() + bar.get_width() / 2, mid_y),
                                ha='center', va='center',
                                fontsize=9.5, fontweight='bold', color='black')

                current_bottom += amount

    # === OUTFLOW BARS WITH ANNOTATIONS ===
    for i, r in enumerate(reservoirs):
        current_bottom = 0
        for label, amount, color in getattr(r, 'outflow_parts', []):
            if amount > 0:
                bar = ax.bar(x_pos[i], amount, width=bar_width,
                             bottom=current_bottom, color=color, alpha=0.90, edgecolor='darkred')[0]

                # Annotation centered in each outflow segment
                if amount >= 800:
                    mid_y = current_bottom + amount / 2
                    ax.annotate(f'{amount:,.0f}',
                                xy=(bar.get_x() + bar.get_width() / 2, mid_y),
                                ha='center', va='center',
                                fontsize=9.5, fontweight='bold', color='black')

                current_bottom += amount

    # Total In:/Out: labels on top (kept for clarity)
    for i, r in enumerate(reservoirs):
        inflow_total = sum(a for _, a, _ in getattr(r, 'inflow_parts', []))
        outflow_total = sum(a for _, a, _ in getattr(r, 'outflow_parts', []))

        if inflow_total > 0:
            ax.annotate(f'In: {inflow_total:,.0f}',
                        xy=(x_pos[i] - bar_width, inflow_total), xytext=(0, 8),
                        textcoords="offset points", ha='center', va='bottom',
                        fontsize=10, fontweight='bold', color='darkgreen')

        if outflow_total > 0:
            ax.annotate(f'Out: {outflow_total:,.0f}',
                        xy=(x_pos[i], outflow_total), xytext=(0, 8),
                        textcoords="offset points", ha='center', va='bottom',
                        fontsize=10, fontweight='bold', color='darkred')

    ax.set_xlabel('Reservoirs', fontsize=11, fontweight='bold')
    ax.set_ylabel('Flow Volume', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    fig.tight_layout(pad=5.0)
    fig.subplots_adjust(bottom=0.32)
    return fig


class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoirs, title="Reservoir Analysis Dashboard"):
        super().__init__(None, title=title, size=wx.Size(1580, 1020))

        self.reservoirs = reservoirs
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Capacity
        power_zones = [
            (Reservoir.high_power_pool_color, 'Full Power Head'),
            (Reservoir.low_power_pool_color, 'Low Power Head'),
            (Reservoir.non_power_pool_color, 'No Power')
        ]
        reserved_zones = [
            (lb.AZ_COLOR, 'AZ'),
            (lb.NV_COLOR, 'NV'),
            (lb.CA_COLOR, 'CA')
        ]
        self.cap_panel = wx.Panel(self.panel)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)
        title = 'Reservoir Capacities - Mar 28, 2026 AM - USBR RISE'
        self.capacity_fig = create_capacity_chart(reservoirs, title=title,
                                                  power_head_zones=power_zones, reserved_zones=reserved_zones)
        self.capacity_canvas = FigureCanvas(self.cap_panel, -1, self.capacity_fig)
        cap_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.cap_panel.SetSizer(cap_sizer)

        # Inflow/Outflow
        self.in_panel = wx.Panel(self.panel)
        in_sizer = wx.BoxSizer(wx.VERTICAL)
        self.inflow_fig = create_inflow_outflow_chart(reservoirs)
        self.inflow_canvas = FigureCanvas(self.in_panel, -1, self.inflow_fig)
        in_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, border=8)
        self.in_panel.SetSizer(in_sizer)

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

        main_sizer.Add(self.cap_panel, 1, wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, border=15)
        main_sizer.Add(self.in_panel, 1, wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=12)

        self.panel.SetSizer(main_sizer)

        self.CreateStatusBar()
        self.SetStatusText(f"Displaying {len(reservoirs)} reservoirs")
        self.SetMinSize(wx.Size(1220, 820))
        self.Centre()

        self.panel.Bind(wx.EVT_SIZE, self.on_panel_resize)

        self.Layout()
        wx.CallAfter(self.force_resize)
        wx.CallLater(100, self.force_resize)
        wx.CallLater(300, self.force_resize)

        self.Bind(wx.EVT_SIZE, lambda e: e.Skip())

    def force_resize(self):
        for canvas, p in [(self.capacity_canvas, self.cap_panel),
                          (self.inflow_canvas, self.in_panel)]:
            if canvas and p:
                size = p.GetClientSize()
                if size[0] > 200 and size[1] > 150:
                    canvas.SetClientSize(size)
                    try:
                        canvas.SetSize(wx.Size(size[0], size[1]))
                    except Exception:
                        pass
                    canvas.draw()
                    canvas.Refresh()

        self.panel.Layout()
        self.SendSizeEvent()

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


if __name__ == "__main__":
    '''
    class Reservoir:
        def __init__(self, name, elevation_feet, active_capacity_af
,
                     reserved_parts=None, critical_elevations_feet=None,
                     inflow_parts=None, outflow_parts=None):
            self.name = name
            self.elevation_feet = elevation_feet
            self.intake_elevation_feet = 0
            self.active_capacity_af = active_capacity_af
            self.reserved_parts = reserved_parts or []
            self.critical_elevations_feet = critical_elevations_feet or []
            self.inflow_parts = inflow_parts or []
            self.outflow_parts = outflow_parts or []

        
        Reservoir("Lake Test", 1075.5, 9500000,
                  reserved_parts=[("SNWA", 1200000, '#1f77b4'),
                                 ("Metropolitan", 1100000, '#ff7f0e'),
                                 ("IID", 1000000, '#2ca02c')],
                  critical_elevations_feet=[("Lower Turbine", 950, 2005585, 'red'),
                                 ("Upper Turbine", 1035, 6637508, 'darkred')],
                  inflow_parts=[("Actual so far", 8500, '#2ca02c'),
                              ("Projected Apr", 4500, '#98fb98')],
                  outflow_parts=[("Actual so far", 7200, '#d62728'),
                               ("Projected Apr", 3800, '#ff9896')]),
        '''
    lake_pleasant = LakePleasant()
    reservoirs = [
        lake_pleasant,
        LakeHavasu(),
        LakeMohave(),
        Aquifers(),
        LakeMead(),
        LakePowell(),
        FlamingGorge(),
        Navajo(),
        BlueMesa()
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs)
    frame.Show()
    app.MainLoop()