# --------------------------------------------------------------
#  Matplotlib toolbar – 3 controls per variable, colour = Choice
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

# Each block has its own list of possible variables
VARIABLES = [
    {"label": "Flow",       "options": ["Streamflow", "Discharge"]},
    {"label": "Rain",       "options": ["Precipitation", "Rainfall"]},
    {"label": "Temp",       "options": ["Temperature", "AirTemp"]},
]

# ------------------------------------------------------------------
# 2. Main frame – colour is a simple Choice
# ------------------------------------------------------------------
class PlotFrame(wx.Frame):
    INSERT_POS = 9                     # you confirmed this works

    def __init__(self):
        super().__init__(None, title="Colour = Hex Choice", size=(950, 650))

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

        # 1. Colour selector – plain Choice with hex strings
        col_choice = wx.Choice(self.toolbar, choices=PLOT_COLORS)
        col_choice.SetSelection(0)                     # default colour
        self.toolbar.InsertControl(pos, col_choice)
        pos += 1

        # 2. Water-year Choice
        year_choice = wx.Choice(self.toolbar, choices=WATER_YEARS)
        year_choice.SetSelection(0)
        self.toolbar.InsertControl(pos, year_choice)
        pos += 1

        # 3. Variable selector – enabled Choice
        var_choice = wx.Choice(self.toolbar, choices=var_info["options"])
        var_choice.SetSelection(0)
        self.toolbar.InsertControl(pos, var_choice)
        pos += 1

        # Store references
        self.var_controls.append({
            "color": col_choice,
            "year":  year_choice,
            "var":   var_choice,
            "info":  var_info,
        })

        # Bind events
        col_choice.Bind(wx.EVT_CHOICE, self.on_change)
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
            hex_col = ctrl["color"].GetStringSelection()   # <-- hex string
            year    = ctrl["year"].GetStringSelection()
            var     = ctrl["var"].GetStringSelection()

            # ---- Dummy data – replace with your real source ----------------
            if "Streamflow" in var or "Discharge" in var:
                y = 50 + 30*np.sin(x) + np.random.normal(0, 3, len(x))
            elif "Precipitation" in var or "Rainfall" in var:
                y = 20 + 15*np.abs(np.sin(x*1.3)) + np.random.normal(0, 2, len(x))
            elif "Temperature" in var or "AirTemp" in var:
                y = 15 + 8*np.cos(x*0.8) + np.random.normal(0, 1, len(x))
            else:
                y = np.zeros_like(x)

            self.ax.plot(x, y, color=hex_col, label=f"{var} ({year})")

        self.ax.legend()
        self.ax.set_title("All controls work")
        self.ax.set_xlabel("Month")
        self.ax.set_ylabel("Value")
        self.canvas.draw()

'''
# create a Choice that shows a coloured square + hex
col_choice = wx.Choice(self.toolbar, choices=PLOT_COLORS)
# add bitmaps
il = wx.ImageList(12, 12)
for col in PLOT_COLORS:
    bmp = wx.Bitmap(12, 12)
    dc = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(col))
    dc.Clear()
    dc.SelectObject(wx.NullBitmap)
    il.Add(bmp)
col_choice.AssignImageList(il, wx.IMAGE_LIST_SMALL)
for i in range(len(PLOT_COLORS)):
    col_choice.SetItemBitmap(i, il.GetBitmap(i))
'''
# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)
    frame = PlotFrame()
    frame.Show()
    app.MainLoop()