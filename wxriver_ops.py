"""
Reservoir Dashboard - Stacked bar annotations restored + compact heights
"""

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import datetime
import os


def create_capacity_chart(reservoirs, title="Reservoir Active Capacity"):
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    names = [r.name for r in reservoirs]
    capacities = [r.active_capacity for r in reservoirs]
    elevations = [r.elevation for r in reservoirs]

    fig = Figure(figsize=(14.5, 5.0), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    reserved_width = 0.26
    main_width = 0.55

    # RESERVED BARS (unchanged)
    for i, r in enumerate(reservoirs):
        reserved_parts = getattr(r, 'reserved_parts', [])
        if reserved_parts:
            total_reserved = sum(amount for _, amount, _ in reserved_parts)
            current_bottom = capacities[i] - total_reserved
            for owner, amount, color in reserved_parts:
                if amount > 0:
                    reserved_x = x_pos[i] - (main_width / 2) - (reserved_width / 2)
                    bar = ax.bar(reserved_x, amount, width=reserved_width,
                                 bottom=current_bottom, color=color, alpha=0.92,
                                 edgecolor='darkgoldenrod')[0]
                    if amount >= 450_000:
                        ax.annotate(owner[:8],
                                    xy=(bar.get_x() + bar.get_width() / 2, current_bottom + amount / 2),
                                    ha='center', va='center',
                                    fontsize=8.2, fontweight='bold', color='black')
                    current_bottom += amount

    # MAIN STACKED CAPACITY BARS + ANNOTATIONS
    for i, r in enumerate(reservoirs):
        crit_points = getattr(r, 'critical_points', [])
        segments = []
        prev = 0
        for name, elev_ft, cap_af, color in crit_points:
            if cap_af > prev:
                segments.append((cap_af - prev, color, name, cap_af))
                prev = cap_af
        if capacities[i] > prev:
            segments.append((capacities[i] - prev, 'royalblue', 'Above Highest Critical', capacities[i]))

        current_bottom = 0
        for height, color, label, total_cap in segments:
            bar = ax.bar(x_pos[i], height, width=main_width,
                         bottom=current_bottom, color=color, alpha=0.85, edgecolor='navy')[0]

            # Annotation: capacity value centered in the segment
            if height >= 300_000:   # only show if segment is tall enough
                mid_y = current_bottom + height / 2
                ax.annotate(f'{total_cap:,.0f}',
                            xy=(bar.get_x() + bar.get_width() / 2, mid_y),
                            ha='center', va='center',
                            fontsize=9.5, fontweight='bold', color='black')

            current_bottom += height

    # MAF labels on top of entire bar
    for i in range(len(names)):
        maf = capacities[i] / 1_000_000
        ax.annotate(f'{maf:.2f} MAF', xy=(x_pos[i], capacities[i]), xytext=(0, 8),
                    textcoords="offset points", ha='center', va='bottom',
                    fontsize=10.5, fontweight='bold', color='black')

    # Elevation labels
    for i in range(len(names)):
        ax.annotate(f'{elevations[i]:,.1f} ft',
                    xy=(x_pos[i] + main_width * 0.52, capacities[i] * 0.96),
                    ha='left', va='center', fontsize=9.8, color='darkgreen', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.35", facecolor="lightyellow", alpha=0.92))

    ax.set_xlabel('Reservoirs', fontsize=11, fontweight='bold')
    ax.set_ylabel('Volume (Acre-Feet)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=22)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=0, ha='center', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper right', fontsize=9)

    fig.tight_layout(pad=5.0)
    fig.subplots_adjust(bottom=0.28, top=0.90)
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
        super().__init__(None, title=title, size=(1580, 1020))

        self.reservoirs = reservoirs
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Capacity
        self.cap_panel = wx.Panel(self.panel)
        cap_sizer = wx.BoxSizer(wx.VERTICAL)
        self.capacity_fig = create_capacity_chart(reservoirs)
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
        self.SetMinSize((1220, 820))
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
                        canvas.resize(size[0], size[1])
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
    class Reservoir:
        def __init__(self, name, elevation, active_capacity,
                     reserved_parts=None, critical_points=None,
                     inflow_parts=None, outflow_parts=None):
            self.name = name
            self.elevation = elevation
            self.active_capacity = active_capacity
            self.reserved_parts = reserved_parts or []
            self.critical_points = critical_points or []
            self.inflow_parts = inflow_parts or []
            self.outflow_parts = outflow_parts or []

    reservoirs = [
        Reservoir("Lake Mead", 1075.5, 9500000,
                  reserved_parts=[("SNWA", 1200000, '#1f77b4'),
                                 ("Metropolitan", 1100000, '#ff7f0e'),
                                 ("IID", 1000000, '#2ca02c')],
                  critical_points=[("Lower Turbine", 950, 2005585, 'red'),
                                 ("Upper Turbine", 1035, 6637508, 'darkred')],
                  inflow_parts=[("Actual so far", 8500, '#2ca02c'),
                              ("Projected Apr", 4500, '#98fb98')],
                  outflow_parts=[("Actual so far", 7200, '#d62728'),
                               ("Projected Apr", 3800, '#ff9896')]),

        Reservoir("Lake Powell", 1120.3, 7200000,
                  reserved_parts=[("Upper Basin", 800000, '#1f77b4')],
                  critical_points=[("Dead Pool", 895, 1500000, 'red')],
                  inflow_parts=[("Actual", 6200, '#2ca02c')],
                  outflow_parts=[("Actual", 9400, '#d62728')])
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs)
    frame.Show()
    app.MainLoop()