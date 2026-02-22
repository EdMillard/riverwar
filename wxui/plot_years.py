import wx
import wx.lib.agw.aui as aui   # optional, just for nicer layout
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

# ----------------------------------------------------------------------
class DatePlotPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        # ---- 1. Build the data ------------------------------------------------
        start = np.datetime64('2023-11-01')
        end   = np.datetime64('2024-10-31')
        self.dates = np.arange(start, end + np.timedelta64(1, 'D'),
                               dtype='datetime64[D]')

        np.random.seed(0)
        self.values = (20 +
                       10 * np.sin(np.arange(len(self.dates)) *
                                   2 * np.pi / 365) +
                       np.random.randn(len(self.dates)) * 2)

        # ---- 2. Matplotlib figure --------------------------------------------
        self.fig = plt.Figure(figsize=(10, 4), dpi=100)
        self.ax  = self.fig.add_subplot(111)

        self.canvas = FigureCanvas(self, -1, self.fig)

        # ---- 3. Layout --------------------------------------------------------
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # ---- 4. Draw the plot -------------------------------------------------
        self.draw_plot()

    # ------------------------------------------------------------------
    def draw_plot(self):
        ax = self.ax
        ax.clear()
        ax.plot(self.dates, self.values, linewidth=1.2, color='#1f77b4')

        # --- 1. Set exact axis limits ---
        ax.set_xlim(self.dates[0], self.dates[-1])

        # --- 2. Grid lines: every 1st of the month ---
        grid_locator = mdates.MonthLocator(bymonthday=1)
        ax.xaxis.set_major_locator(grid_locator)
        ax.xaxis.set_major_formatter(plt.NullFormatter())  # No labels on grid

        # --- 3. Labels: centered in each month (15th) ---
        first_label_date = np.datetime64('2023-11-15')  # Change to '2023-12-15' if you want to skip Nov
        last_label_date = np.datetime64('2024-10-15')

        label_dates = []
        current = first_label_date
        while current <= last_label_date:
            label_dates.append(current)
            # Add one month
            dt_obj = current.astype(object)
            year, month = dt_obj.year, dt_obj.month + 1
            if month > 12:
                month = 1
                year += 1
            current = np.datetime64(f'{year}-{month:02d}-15')

        # CRITICAL: Convert datetime64 → float (Matplotlib internal format)
        label_nums = mdates.date2num([d.astype('datetime64[D]') for d in label_dates])

        # Now safe to set ticks
        ax.set_xticks(label_nums)
        ax.set_xticklabels([mdates.num2date(num).strftime('%b') for num in label_nums],
                           ha='center', va='top')

        # --- 4. Grid ---
        ax.grid(True, which='major', axis='x', linestyle='-', linewidth=1.0, alpha=0.7)
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
        ax.grid(True, which='minor', axis='x', linestyle=':', alpha=0.3)

        # --- 5. Layout ---
        self.fig.autofmt_xdate(bottom=0.18, rotation=0, ha='center')
        self.fig.tight_layout(pad=1.0)
        self.canvas.draw()

# ----------------------------------------------------------------------
class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Monthly-grid datetime64 plot (wxPython)",
                         size=(900, 500))

        panel = DatePlotPanel(self)
        self.Centre()
        self.Show()

# ----------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(False)
    MainFrame()
    app.MainLoop()