# --------------------------------------------------------------
#  Matplotlib toolbar – 3 controls per variable, fully working
# --------------------------------------------------------------
import wx
import matplotlib
matplotlib.use('WxAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import numpy as np

# ------------------------------------------------------------------
# 1. Data
# ------------------------------------------------------------------
PLOT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5", "#c49c94",
]

WATER_YEARS = [str(y) for y in range(2024, 2031)]

# Each entry now contains a *list* of possible variables for that block
VARIABLES = [
    {"label": "Flow",       "options": ["Streamflow", "Discharge"]},
    {"label": "Rain",       "options": ["Precipitation", "Rainfall"]},
    {"label": "Temp",       "options": ["Temperature", "AirTemp"]},
]

# ------------------------------------------------------------------
# 2. Helper: 16x16 coloured bitmap
# ------------------------------------------------------------------
def _color_bitmap(hex_color, size=16):
    bmp = wx.Bitmap(size, size)
    dc = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(hex_color))
    dc.Clear()
    dc.SelectObject(wx.NullBitmap)
    return bmp

# ------------------------------------------------------------------
# 3. Colour button – shows colour + down-arrow, opens popup
# ------------------------------------------------------------------
class ColorButton(wx.BitmapButton):
    def __init__(self, parent, colors):
        self.colors = colors
        self.idx = 0
        # combine colour square + tiny down-arrow
        bmp = self._make_bitmap()
        super().__init__(parent,
                         bitmap=bmp,
                         size=(28, 22),          # a little wider for the arrow
                         style=wx.BORDER_NONE)
        self.Bind(wx.EVT_BUTTON, self._on_click)

    # --------------------------------------------------------------
    def _make_bitmap(self):
        """Colour square + small down-triangle on the right."""
        w, h = 16, 16
        bmp = wx.Bitmap(28, 22)
        dc = wx.MemoryDC(bmp)
        dc.SetBackground(wx.Brush(self.colors[self.idx]))
        dc.Clear()
        # draw the down-arrow (simple triangle)
        dc.SetBrush(wx.Brush(wx.BLACK))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawPolygon([(20, 8), (24, 8), (22, 12)])
        dc.SelectObject(wx.NullBitmap)
        return bmp

    # --------------------------------------------------------------
    def _on_click(self, event):
        menu = wx.Menu()
        for i, col in enumerate(self.colors):
            item = wx.MenuItem(menu, wx.ID_ANY, col.upper())
            item.SetBitmap(_color_bitmap(col))
            menu.Bind(wx.EVT_MENU, lambda e, idx=i: self._set(idx), id=item.GetId())
            menu.Append(item)
        self.PopupMenu(menu)

    # --------------------------------------------------------------
    def _set(self, idx):
        self.idx = idx
        self.SetBitmap(self._make_bitmap())
        # fire a change event so the plot updates
        wx.PostEvent(self.GetTopLevelParent(),
                     wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.GetId()))

    # --------------------------------------------------------------
    def GetCurrentColor(self):
        return self.colors[self.idx]

# ------------------------------------------------------------------
# 4. Main frame – all blocks start at position 9
# ------------------------------------------------------------------
class PlotFrame(wx.Frame):
    INSERT_POS = 9

    def __init__(self):
        super().__init__(None, title="Fully Working Toolbar", size=(950, 650))

        # ---- Matplotlib ------------------------------------------------
        self.figure = Figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.ax = self.figure.add_subplot(111)

        # ---- Toolbar ---------------------------------------------------
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()

        # ---- Insert variable blocks ------------------------------------
        self.var_controls = []
        pos = self.INSERT_POS
        for i, var in enumerate(VARIABLES):
            pos = self._insert_block(var, pos)
            if i < len(VARIABLES) - 1:
                self.toolbar.InsertSeparator(pos)
                pos += 1

        # ---- Layout ----------------------------------------------------
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self._update_plot()

    # ------------------------------------------------------------------
    def _insert_block(self, var_info, start_pos):
        pos = start_pos

        # 1. Colour button (with down-arrow)
        col_btn = ColorButton(self.toolbar, PLOT_COLORS)
        self.toolbar.InsertControl(pos, col_btn)
        pos += 1

        # 2. Water-year Choice
        year_choice = wx.Choice(self.toolbar, choices=WATER_YEARS)
        year_choice.SetSelection(0)
        self.toolbar.InsertControl(pos, year_choice)
        pos += 1

        # 3. Variable selector – **enabled** Choice with all options
        var_choice = wx.Choice(self.toolbar, choices=var_info["options"])
        var_choice.SetSelection(0)
        self.toolbar.InsertControl(pos, var_choice)
        pos += 1

        # Store
        self.var_controls.append({
            "color": col_btn,
            "year":  year_choice,
            "var":   var_choice,
            "info":  var_info,
        })

        # Bind events
        col_btn.Bind(wx.EVT_BUTTON, lambda e: self.on_change(e))
        year_choice.Bind(wx.EVT_CHOICE, self.on_change)
        var_choice.Bind(wx.EVT_CHOICE, self.on_change)

        self.toolbar.Realize()
        return pos

    # ------------------------------------------------------------------
    def on_change(self, event):
        self._update_plot()

    # ------------------------------------------------------------------
    def _update_plot(self):
        self.ax.clear()
        x = np.linspace(0, 12, 100)

        for ctrl in self.var_controls:
            color = ctrl["color"].GetCurrentColor()
            year  = ctrl["year"].GetStringSelection()
            var   = ctrl["var"].GetStringSelection()   # <-- now user-selectable

            # ---- Dummy data – replace with your real source ----------------
            if "Streamflow" in var or "Discharge" in var:
                y = 50 + 30*np.sin(x) + np.random.normal(0, 3, len(x))
            elif "Precipitation" in var or "Rainfall" in var:
                y = 20 + 15*np.abs(np.sin(x*1.3)) + np.random.normal(0, 2, len(x))
            elif "Temperature" in var or "AirTemp" in var:
                y = 15 + 8*np.cos(x*0.8) + np.random.normal(0, 1, len(x))
            else:
                y = np.zeros_like(x)

            self.ax.plot(x, y, color=color, label=f"{var} ({year})")

        self.ax.legend()
        self.ax.set_title("All controls work")
        self.ax.set_xlabel("Month")
        self.ax.set_ylabel("Value")
        self.canvas.draw()

# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)
    frame = PlotFrame()
    frame.Show()
    app.MainLoop()