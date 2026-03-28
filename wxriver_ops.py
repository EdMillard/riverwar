"""
Copyright (c) 2026 Ed Millard

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
import colorado.lb as lb
import colorado.ub as ub
import colorado.allb as all_b
from openpyxl import Workbook
import pandas as pd
from report.doc import Report
from sheet import sheet
from sheet.sheet import Sheet
from colorado.lake_powell import LakePowell

import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class Reservoir:
    def __init__(self, name, elevation, active_capacity,
                 inflow, outflow,
                 reserved=0,           # e.g. 3.3 * 1_000_000 for 3.3 MAF ICS
                 critical_capacity=None):   # acre-feet remaining at power head critical
        self.name = name
        self.elevation = elevation
        self.active_capacity = active_capacity
        self.inflow = inflow
        self.outflow = outflow
        self.reserved = reserved
        self.critical_capacity = critical_capacity   # capacity (AF) at critical elevation

def create_capacity_chart(reservoirs, title="Reservoir Active Capacity"):
    """
    Creates the top chart with optional stacked bars.

    Reservoir objects should have:
        - name
        - elevation (current elevation in feet)
        - active_capacity (in acre-feet)
        - reserved (optional, in acre-feet, e.g. ICS) — if 0 or None, no stacking
        - critical_capacity (optional, in acre-feet at power head critical level)
          The annotation will show the corresponding elevation in feet.
    """
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    names = [r.name for r in reservoirs]
    capacities = [r.active_capacity for r in reservoirs]
    elevations = [r.elevation for r in reservoirs]

    # Reserved (e.g. ICS) - use 0 if not present
    reserved = []
    for r in reservoirs:
        res = getattr(r, 'reserved', 0) or 0
        reserved.append(res)

    # Critical capacity -> we'll annotate elevation (you provide capacity at critical, we show feet)
    critical_elevs = []
    for r in reservoirs:
        crit_cap = getattr(r, 'critical_capacity', None)
        if crit_cap is not None and r.active_capacity > 0:
            # Simple linear approximation: scale the critical capacity to elevation
            # (Better accuracy would require full elevation-capacity curve, but this is a reasonable start)
            ratio = crit_cap / r.active_capacity
            estimated_crit_elev = r.elevation * ratio  # rough; improve if you have better mapping
            critical_elevs.append(estimated_crit_elev)
        else:
            critical_elevs.append(None)

    fig = Figure(figsize=(10, 5.2), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    bar_width = 0.35

    # Stacked bars
    # Bottom: Active Capacity
    bars_active = ax.bar(x_pos, capacities, width=bar_width,
                         color='royalblue', alpha=0.85, edgecolor='navy',
                         label='Active Capacity')

    # Top: Reserved (stacked on top when > 0)
    bars_reserved = ax.bar(x_pos, reserved, width=bar_width,
                           bottom=capacities,
                           color='gold', alpha=0.9, edgecolor='darkgoldenrod',
                           label='Reserved (e.g. ICS)')

    ax.set_xlabel('Reservoirs', fontsize=11, fontweight='bold')
    ax.set_ylabel('Volume (Acre-Feet)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9)

    # Total height for positioning
    totals = [cap + res for cap, res in zip(capacities, reserved)]

    # Capacity value on top of active portion
    for bar in bars_active:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9.5, fontweight='bold', color='navy')

    # Reserved value on top of reserved portion (if any)
    for i, (bar, res_val) in enumerate(zip(bars_reserved, reserved)):
        if res_val > 0:
            bottom = capacities[i]
            ax.annotate(f'+{res_val:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, bottom + res_val),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9, fontweight='bold', color='darkgoldenrod')

    # Elevation on LEFT side (near top of whole bar)
    for i, (bar, elev) in enumerate(zip(bars_active, elevations)):
        bar_left = bar.get_x()
        total_height = totals[i]
        y_pos = total_height * 0.96

        ax.annotate(f'Elev: {elev:,.1f} ft',
                    xy=(bar_left, y_pos),
                    xytext=(-10, 0),
                    textcoords="offset points",
                    ha='right', va='center',
                    fontsize=9.5, color='darkgreen', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.4",
                              facecolor="lightyellow", edgecolor='darkgreen', alpha=0.9))

    # Power Head Critical Elevation annotation (horizontal line + label)
    for i, crit_elev in enumerate(critical_elevs):
        if crit_elev is not None:
            # Draw a dashed red line across the bar at the critical level
            # Approximate y-position using linear scaling (active_capacity corresponds to current elevation)
            if capacities[i] > 0:
                y_crit = (crit_elev / elevations[i]) * capacities[i]  # rough scaling
                ax.axhline(y=y_crit, xmin=x_pos[i] - bar_width / 2.2, xmax=x_pos[i] + bar_width / 2.2,
                           color='red', linestyle='--', linewidth=1.5, alpha=0.8)

                ax.annotate(f'Power Head Critical\n{crit_elev:,.1f} ft',
                            xy=(x_pos[i] + bar_width / 2 + 0.05, y_crit),
                            xytext=(12, 0),
                            textcoords="offset points",
                            ha='left', va='center',
                            fontsize=8.5, color='darkred', fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="mistyrose", alpha=0.95))

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper right')
    fig.tight_layout()
    return fig

def create_inflow_outflow_chart(reservoirs, title="Reservoir Inflow vs Outflow"):
    """Bottom chart: Grouped bars - Inflow and Outflow side by side"""
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    names = [r.name for r in reservoirs]
    inflows = [r.inflow for r in reservoirs]      # Assuming these attributes exist
    outflows = [r.outflow for r in reservoirs]

    fig = Figure(figsize=(10, 5), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    bar_width = 0.35
    gap = 0.05

    # Inflow bars (left of group)
    inflow_bars = ax.bar(x_pos - bar_width/2 - gap/2, inflows, width=bar_width,
                         color='seagreen', alpha=0.85, edgecolor='darkgreen',
                         label='Inflow')

    # Outflow bars (right of group)
    outflow_bars = ax.bar(x_pos + bar_width/2 + gap/2, outflows, width=bar_width,
                          color='orangered', alpha=0.85, edgecolor='darkred',
                          label='Outflow')

    ax.set_xlabel('Reservoirs', fontsize=11, fontweight='bold')
    ax.set_ylabel('Flow Rate', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9)

    # Value labels on top of bars
    for bar in inflow_bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9, color='darkgreen', fontweight='bold')

    for bar in outflow_bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9, color='darkred', fontweight='bold')

    ax.legend(loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    fig.tight_layout()
    return fig


# ====================== WXWIDGETS FRAME ======================
class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoirs, title="Reservoir Analysis Dashboard"):
        super().__init__(None, title=title, size=(1020, 980))

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top chart - Capacity (with stacking and critical elevation)
        capacity_fig = create_capacity_chart(reservoirs, "Reservoir Active Capacity & Reserved Water")
        self.capacity_canvas = FigureCanvas(panel, -1, capacity_fig)

        # Separator
        separator = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)

        # Bottom chart - Inflow vs Outflow
        inflow_fig = create_inflow_outflow_chart(reservoirs, "Reservoir Inflow vs Outflow")
        self.inflow_canvas = FigureCanvas(panel, -1, inflow_fig)

        main_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        main_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

        self.CreateStatusBar()
        self.SetStatusText(f"Displaying {len(reservoirs)} reservoirs")


class Colorado_River_Ops(Sheet):
    def __init__(self):
        headers = [lb.MEAD_ELEVATION, ub.POWELL_ELEVATION, '1', lb.MEAD, ub.POWELL, ub.FLAMING_GORGE, ub.BLUE_MESA]
        super().__init__(headers, start_year=2026, end_year=2026)


    def load_df(self, df_compact : pd.DataFrame) -> None:
        df_len = len(self.df) + 2
        usbr_lake_mead_elevation_ft = 6123
        mead_elevation = sheet.usbr_get_last_value(usbr_lake_mead_elevation_ft, self.start_year)

        usbr_lake_mead_storage_af = 6124
        mead_storage = sheet.usbr_get_last_value(usbr_lake_mead_storage_af, self.start_year)

        usbr_lake_powell_elevation_af = 508
        powell_elevation = sheet.usbr_get_last_value(usbr_lake_powell_elevation_af, self.start_year)

        usbr_lake_powell_storage_af = 509
        powell_storage = sheet.usbr_get_last_value(usbr_lake_powell_storage_af, self.start_year)

        usbr_flaming_gorge_storage_af = 337
        flaming_gorge_storage = sheet.usbr_get_last_value(usbr_flaming_gorge_storage_af, self.start_year)

        usbr_blue_mesa_storage_af = 76
        blue_mesa_storage = sheet.usbr_get_last_value(usbr_blue_mesa_storage_af, self.start_year)

        pass

    def build_sheet(self)-> None:
        # self.set_bg(lb.MX_TREATY, ub.GLEN_CANYON_RELEASE, color=all_b.USBR_AR_FLOW)

        self.format_header()

        self.set_column_width(lb.MEAD_ELEVATION, 5, to=ub.POWELL_ELEVATION)
        self.set_column_width(lb.MEAD, 7, to=ub.BLUE_MESA)


def run():
    # Elevation_ft_NAVD88,Elevation_ft_NGVD29,Area_acres,Capacity_acrefeet

    river_ops = Colorado_River_Ops()
    file_path = Path('excel/Colorado_River_Ops.xlsx')
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        river_ops.export(writer, all_b.OPERATIONS, None, number_format='#,##0;-#,##0')

        wb: Workbook = writer.book
        wb.calcMode = "auto"  # ensure automatic calculation

    Report.open_docx_in_app(file_path)

# if __name__ == "__main__":
#    run()

import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


def create_capacity_chart(reservoirs, title="Reservoir Active Capacity"):
    """Stacked bars (2 or 3 segments) with elevations tightly on the right side"""
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    names = [r.name for r in reservoirs]
    capacities = [r.active_capacity for r in reservoirs]
    elevations = [r.elevation for r in reservoirs]
    reserved_list = [getattr(r, 'reserved', 0) or 0 for r in reservoirs]

    # Critical remaining capacity (top red segment)
    critical_remaining = []
    critical_elevs = []  # <-- Fixed: explicitly defined here
    for r in reservoirs:
        crit_cap = getattr(r, 'critical_capacity', None)
        if crit_cap is not None and crit_cap > 0:
            critical_remaining.append(crit_cap)
            # Approximate critical elevation (linear scaling)
            ratio = crit_cap / r.active_capacity
            est_crit_elev = r.elevation * ratio
            critical_elevs.append(est_crit_elev)
        else:
            critical_remaining.append(0)
            critical_elevs.append(None)

    fig = Figure(figsize=(11, 5.8), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    bar_width = 0.45

    # 1. Active Capacity (bottom - blue)
    bars_active = ax.bar(x_pos, capacities, width=bar_width,
                         color='royalblue', alpha=0.85, edgecolor='navy',
                         label='Active Capacity')

    # 2. Reserved (middle - gold) when present
    for i, res in enumerate(reserved_list):
        if res > 0:
            ax.bar(x_pos[i], res, width=bar_width,
                   bottom=capacities[i],
                   color='gold', alpha=0.9, edgecolor='darkgoldenrod',
                   label='Reserved (ICS)' if i == 0 else "")

    # 3. Critical remaining (top - light red) when present
    for i, crit_rem in enumerate(critical_remaining):
        if crit_rem > 0:
            bottom = capacities[i] + reserved_list[i]
            ax.bar(x_pos[i], crit_rem, width=bar_width,
                   bottom=bottom,
                   color='lightcoral', alpha=0.85, edgecolor='darkred',
                   label='Power Head Critical Remaining' if i == 0 else "")

    ax.set_xlabel('Reservoirs', fontsize=11, fontweight='bold')
    ax.set_ylabel('Volume (Acre-Feet)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9.5)

    totals = [cap + res + crit for cap, res, crit in zip(capacities, reserved_list, critical_remaining)]

    # Value labels on segments
    for bar in bars_active:
        h = bar.get_height()
        ax.annotate(f'{h:,.0f}', xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='navy')

    for i, res in enumerate(reserved_list):
        if res > 0:
            ax.annotate(f'+{res:,.0f}',
                        xy=(x_pos[i] + bar_width / 2, capacities[i] + res),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold', color='darkgoldenrod')

    for i, crit in enumerate(critical_remaining):
        if crit > 0:
            bottom = capacities[i] + reserved_list[i]
            ax.annotate(f'+{crit:,.0f}',
                        xy=(x_pos[i] + bar_width / 2, bottom + crit),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold', color='darkred')

    # ====================== ELEVATIONS TIGHT ON RIGHT SIDE ======================
    right_offset = bar_width * 0.55  # Close to the right edge

    for i in range(len(names)):
        bar_right = x_pos[i] + right_offset
        total_height = totals[i]

        # 1. Current elevation (top of whole bar)
        ax.annotate(f'{elevations[i]:,.1f}',
                    xy=(bar_right, total_height * 0.96),
                    ha='left', va='center',
                    fontsize=9.8, color='darkgreen', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.35", facecolor="lightyellow", alpha=0.92))

        # 2. Elevation at start of critical segment (if critical exists)
        if critical_remaining[i] > 0:
            y_interface = capacities[i] + reserved_list[i]
            if total_height > 0:
                elev_interface = elevations[i] * (y_interface / total_height)
                ax.annotate(f'{elev_interface:,.1f}',
                            xy=(bar_right, y_interface),
                            ha='left', va='center',
                            fontsize=9.5, color='darkgreen', fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.35", facecolor="lightyellow", alpha=0.85))

        # 3. Power Head Critical elevation (at interface of critical segment)
        if critical_remaining[i] > 0 and critical_elevs[i] is not None:
            y_crit = capacities[i] + reserved_list[i]
            ax.annotate(f'{critical_elevs[i]:,.1f}',
                        xy=(bar_right, y_crit),
                        ha='left', va='center',
                        fontsize=9.5, color='darkred', fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.35", facecolor="mistyrose", alpha=0.92))

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper right', fontsize=9)
    fig.tight_layout(pad=2.8)
    return fig


def create_inflow_outflow_chart(reservoirs, title="Reservoir Inflow vs Outflow"):
    if not reservoirs:
        raise ValueError("Reservoir list cannot be empty")

    names = [r.name for r in reservoirs]
    inflows = [r.inflow for r in reservoirs]
    outflows = [r.outflow for r in reservoirs]

    fig = Figure(figsize=(11, 5.3), dpi=100)
    ax = fig.add_subplot(111)

    x_pos = np.arange(len(names))
    bar_width = 0.35

    ax.bar(x_pos - bar_width / 2 - 0.03, inflows, width=bar_width,
           color='seagreen', alpha=0.85, edgecolor='darkgreen', label='Inflow')
    ax.bar(x_pos + bar_width / 2 + 0.03, outflows, width=bar_width,
           color='orangered', alpha=0.85, edgecolor='darkred', label='Outflow')

    ax.set_xlabel('Reservoirs', fontsize=11, fontweight='bold')
    ax.set_ylabel('Flow Rate', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9.5)

    ax.legend(loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    fig.tight_layout()
    return fig


class ReservoirChartFrame(wx.Frame):
    def __init__(self, reservoirs, title="Reservoir Analysis Dashboard"):
        super().__init__(None, title=title, size=(1100, 1020))

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        capacity_fig = create_capacity_chart(reservoirs, "Reservoir Active Capacity")
        self.capacity_canvas = FigureCanvas(panel, -1, capacity_fig)

        separator = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)

        inflow_fig = create_inflow_outflow_chart(reservoirs, "Reservoir Inflow vs Outflow")
        self.inflow_canvas = FigureCanvas(panel, -1, inflow_fig)

        main_sizer.Add(self.capacity_canvas, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        main_sizer.Add(self.inflow_canvas, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

        self.CreateStatusBar()
        self.SetStatusText(f"Displaying {len(reservoirs)} reservoirs")


# ====================== MAIN USAGE EXAMPLE ======================
if __name__ == "__main__":
    class Reservoir:
        def __init__(self, name, elevation, active_capacity, inflow, outflow,
                     reserved=0, critical_capacity=None):
            self.name = name
            self.elevation = elevation
            self.active_capacity = active_capacity
            self.inflow = inflow
            self.outflow = outflow
            self.reserved = reserved
            self.critical_capacity = critical_capacity   # remaining AF when power head is critical

    reservoirs = [
        Reservoir("Lake Mead",     1075.5, 9500000, 12500, 9800, 3300000, 2800000),
        Reservoir("Lake Powell",   1120.3, 8700000, 9800,  11200, 0,       1500000),
        Reservoir("Lake Shasta",   1067.0, 4550000, 6500,  4200,  800000,  1200000),
        Reservoir("Oroville",      900.2,  3500000, 7800,  5100,  0,       900000),
    ]

    app = wx.App(False)
    frame = ReservoirChartFrame(reservoirs)
    frame.Show()
    app.MainLoop()