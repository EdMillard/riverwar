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
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FsROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import wx
import wx.adv
import matplotlib
matplotlib.use('WxAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from wxui.python_text_view import PythonTextView
from typing_extensions import LiteralString
from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU
from typing import Tuple


# ------------------------------------------------------------------
# 1. Data
# ------------------------------------------------------------------
WATER_YEARS = [str(y) for y in range(2024, 2025)]

VARIABLES = [
    {"label": "", "options": []},
    {"label": "", "options": []},
    {"label": "", "options": []},
]

color_names = X11_COLOR_NAMES = [
    'firebrick', "royalblue", "purple", # First 3 are important defaults
    "aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque",
    "black", "blanchedalmond", "blue", "blueviolet", "brown", "burlywood", "cadetblue",
    "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan",
    "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkgrey",
    "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred",
    "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkslategrey",
    "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dimgrey",
    "dodgerblue", "floralwhite", "forestgreen", "fuchsia", "gainsboro",
    "ghostwhite", "gold", "goldenrod", "gray", "green", "greenyellow", "grey",
    "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender",
    "lavenderblush", "lawngreen", "lemonchiffon", "lightblue", "lightcoral",
    "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgreen", "lightgrey",
    "lightpink", "lightsalmon", "lightseagreen", "lightskyblue", "lightslategray",
    "lightslategrey", "lightsteelblue", "lightyellow", "lime", "limegreen", "linen",
    "magenta", "maroon", "mediumaquamarine", "mediumblue", "mediumorchid",
    "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen",
    "mediumturquoise", "mediumvioletred", "midnightblue", "mintcream", "mistyrose",
    "moccasin", "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orange",
    "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise",
    "palevioletred", "papayawhip", "peachpuff", "peru", "pink", "plum", "powderblue",
    "red", "rosybrown", "saddlebrown", "salmon", "sandybrown",
    "seagreen", "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray",
    "slategrey", "snow", "springgreen", "steelblue", "tan", "teal", "thistle",
    "tomato", "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow",
    "yellowgreen"
]

class GraphicPanel(wx.Panel):
    INSERT_POS = 9
    valid_colors = {}

    def __init__(self, parent, sources, dates, units, text=None):
        super().__init__(parent)
        self.sources = sources
        self.dates = dates
        self.units = units
        self.text = text
        self.python_text_view = None

        # For doc report generation on verify error panels
        self.variable_name = None
        self.text = None

        self.figure = Figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.ax = self.figure.add_subplot(111)

        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()

        self.colors: list[tuple[str, tuple[int, int, int]]] = []

        if not GraphicPanel.valid_colors:
            db = wx.ColourDatabase()
            for name in color_names:
                color = db.Find(name)  # Returns wx.Colour
                if color:
                    rgb = (color.Red(), color.Green(), color.Blue())
                    GraphicPanel.valid_colors[name] = rgb
            for valid_color, rgb in GraphicPanel.valid_colors.items():
                v = ('', rgb)
                self.colors.append(v)

        self.var_controls = []
        pos = self.INSERT_POS
        for i, var in enumerate(VARIABLES):
            var["options"] = ''
            pos = self.insert_tool_block(i, var, pos)
            if i < len(VARIABLES) - 1:
                self.toolbar.InsertSeparator(pos)
                pos += 1

        if text is not None and text:
            self.python_text_view = PythonTextView(self)
            self.python_text_view.update_text(text)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        if self.python_text_view:
            sizer.Add(self.python_text_view, 0, wx.EXPAND)
            self.python_text_view.SetMinSize(wx.Size(-1, 200))
        self.SetSizer(sizer)

        # FIXME Doesnt work
        # wx.CallAfter(self.source_select)
        # self.update_plot()

    def update_plot(self):
        self.ax.clear()

        dates = None
        units = ''
        did_plot = False
        for i, ctrl in enumerate(self.var_controls):
            sel = ctrl["color"].GetSelection()
            bmp = ctrl["color"].GetItemBitmap(sel)  # <-- the key method
            rgb = GraphicPanel.first_pixel_rgb(bmp)

            source_string = ctrl["source"].GetStringSelection()
            source = self.sources.get(source_string)
            if source is not None:
                # year = ctrl["year"].GetStringSelection()
                year = ''
                variable_name = ctrl["var"].GetStringSelection()
                print(f'\tupdate_plot: {i} {source_string} {variable_name}')
                if variable_name:
                    y = source.get(variable_name)
                    mext_units = self.units[variable_name]
                    if units and mext_units != units:
                        print(f'Units mismatch {variable_name} {mext_units} {units}')
                    else:
                        units = mext_units

                    expected = [('dt', '<M8[D]'), ('val', '<f8')]
                    if GraphicPanel.is_expected_structured_dtype(y, expected):
                        x = dates = y['dt']
                        v = y['val']
                        self.ax.plot(x, v, color=rgb, label=f"{variable_name} ({year})")
                        did_plot = True
                    else:
                        # FIXME this wont work for multiple years
                        x = dates = self.dates
                        if x is not None and y is not None:
                            self.ax.plot(x, y, color=rgb, label=f"{variable_name} ({year})")
                            did_plot = True
                        else:
                            print(f'Plot failed {variable_name}')

        if did_plot:
            self.ax.legend()
        self.ax.set_title("Dolores")
        # self.ax.set_xlabel("Month")
        if dates is not None:
            self.format_grid(dates)
        self.ax.set_ylabel(units)
        self.ax.grid(True)
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.1, hspace=0.1)
        self.canvas.draw()

    def save_plot_to_image(self, report, file_name, variable_name, text):
        self.update_plot()

        dpi = self.figure.get_dpi()
        display_dpi = wx.GetDisplayPPI()[0]
        canvas_pixel_width, canvas_pixel_height = self.canvas.GetSize()  # Get wxWidgets canvas size in pixels
        # print(f'\tPlot canvas size {canvas_pixel_width}x{canvas_pixel_height}')
        width_in_inches = canvas_pixel_width / display_dpi
        height_in_inches = canvas_pixel_height / display_dpi
        self.figure.set_size_inches(width_in_inches, height_in_inches)

        # plt.tight_layout()
        plot_filename = file_name
        wx.MilliSleep(10)
        wx.GetApp().Yield()
        wx.MilliSleep(10)
        wx.GetApp().Yield()
        self.figure.savefig(plot_filename, dpi=dpi, bbox_inches='tight')

        report.page_break()

        header = variable_name + ' - Unset Priority'
        report.header(header, header_level=2)
        report.plot(plot_filename, inches=9)
        report.paragraph_with_header('Description', '')
        report.paragraph_with_header('Suggested Fix', '', font='Courier New', size=10)
        report.paragraph_with_header('Errors', text, font='Courier New', size=10)

        plt.close(self.figure)

    def set_variables(self, variables):
        for variable in variables:
            index, source, variable_name = variable
            ctrl = self.var_controls[index]
            GraphicPanel.source_changed(ctrl, source, variable_name)

        wx.CallAfter(self.update_plot)

    @staticmethod
    def source_changed(ctrl, source, variable_name):
        source_ctrl = ctrl.get('source')
        source_selected = source_ctrl.GetStringSelection()
        if source_selected != source:
            source_ctrl.SetStringSelection(source)
        var_ctrl = ctrl.get('var')
        var_ctrl.SetStringSelection(variable_name)

    def source_select(self):
        for ctrl in self.var_controls:
            source_choice = ctrl['source']
            if source_choice:
                # FIXME, selection call back isnt being called
                source_choice.SetSelection(1)

    def on_select_color(self, event):
        self.update_plot()

    def on_change(self, event):
        self.update_plot()

    def variable_names_for_source(self, source):
        variables = self.sources[source]
        variable_names = list(variables.keys())
        if "DATE" in variable_names:
            variable_names.remove("DATE")
        variable_names.sort()
        return variable_names

    def on_source_change(self, event):
        control = event.GetEventObject()
        source = control.GetStringSelection()
        self.source_change(control, source)

    def source_change(self, control, source):
        for i, ctrl in enumerate(self.var_controls):
            if control == ctrl['source']:
                variable_names = self.variable_names_for_source(source)
                var_choice = ctrl["var"]
                var_choice.Clear()  # remove all old items
                for s in variable_names:
                    var_choice.Append(s)
                # GraphicPanel.resize_choice_to_longest_string(var_choice)
                self.Layout()
                break

    @staticmethod
    def resize_choice_to_longest_string(choice):
        # FIXME Doesnt work at least on Linux
        """Resize choice to fit the longest string (sizer-independent)."""
        if not choice.GetItems():
            return

        # Measure text using the control's font
        dc = wx.ClientDC(choice)
        dc.SetFont(choice.GetFont())

        # Get width of each string
        widths = [dc.GetTextExtent(item)[0] for item in choice.GetItems()]
        max_width = max(widths)

        # Add padding for dropdown arrow + margins
        padding = 30
        new_width = max_width + padding

        # Set minimum size (only width)
        current = choice.GetSize()
        choice.SetMinSize((new_width, current.height))

        # ---- FORCE LAYOUT (works even if GetContainingSizer() is None) ----
        choice.GetParent().Layout()  # This is the key!

    @staticmethod
    def color_as_rgb(color):
        return color.Red(), color.Green(), color.Blue()

    @staticmethod
    def make_bitmap(rgb, size=(24, 24)):
        """Return a solid-colour wx.Bitmap."""
        img = wx.Image(*size)

        # ---- correct way to fill the whole image ----
        # 1. rect version (wx.Rect)
        img.SetRGB(wx.Rect(0, 0, size[0], size[1]), *rgb)

        # 2. alternative: per-pixel version (slower but works everywhere)
        # for x in range(size[0]):
        #     for y in range(size[1]):
        #         img.SetRGB(x, y, *rgb)

        return wx.Bitmap(img)

    @staticmethod
    def create_color_choice(parent, colors):
        combo = wx.adv.BitmapComboBox(parent, style=wx.CB_READONLY)

        # keep references so the bitmaps are not garbage-collected
        _bitmaps = []

        for name, rgb in colors:
            bmp = GraphicPanel.make_bitmap(rgb, size=(24, 24))
            _bitmaps.append(bmp)
            combo.Append(name, bmp)  # text + bitmap
        return combo

    def insert_tool_block(self, i, var_info, start_pos):
        pos = start_pos

        # Color selector – Choice with COLORED hex strings
        col_choice = GraphicPanel.create_color_choice(self.toolbar, self.colors)
        col_choice.SetSelection(i)
        self.toolbar.InsertControl(pos, col_choice)
        col_choice.Bind(wx.EVT_COMBOBOX, self.on_change)
        pos += 1

        # Data Source Choice
        source_names = list(self.sources.keys())
        # if len(source_names) > 1:
        source_choice = wx.Choice(self.toolbar, choices=source_names)
        source_choice.Bind(wx.EVT_CHOICE, self.on_source_change)
        default_source = 0
        variable_names = self.variable_names_for_source(source_names[default_source])
        source_choice.SetSelection(default_source)
        self.toolbar.InsertControl(pos, source_choice)
        pos += 1

        # Water-year Choice
        # year_choice = wx.Choice(self.toolbar, choices=WATER_YEARS)
        # year_choice.SetSelection(0)
        # self.toolbar.InsertControl(pos, year_choice)
        # year_choice.Bind(wx.EVT_CHOICE, self.on_change)
        # pos += 1

        # Variable selector
        var_choice = wx.Choice(self.toolbar, choices=variable_names)
        # var_choice.SetSelection(0)
        self.toolbar.InsertControl(pos, var_choice)
        var_choice.Bind(wx.EVT_CHOICE, self.on_change)
        pos += 1

        # Store
        self.var_controls.append({
            "color": col_choice,
            "source": source_choice,
        #    "year": year_choice,
            "var": var_choice,
            "info": var_info,
        })
        self.toolbar.Realize()
        return pos

    @staticmethod
    def is_expected_structured_dtype(arr, expected):
        if not isinstance(arr, np.ndarray):
            return False
        if arr.dtype.names is None:
            return False  # Not structured

        expected_names = [name for name, _ in expected]
        expected_formats = [fmt for _, fmt in expected]

        # Check field names
        if arr.dtype.names != tuple(expected_names):
            return False

        # Check field formats
        # lname = LiteralString[name]
        # actual_formats = [arr.dtype.fields[name][0].str for name in arr.dtype.names]
        actual_formats: list[LiteralString] = [
            arr.dtype.fields[name][0].str  # type: ignore[assignment]
            for name in arr.dtype.names
        ]
        return actual_formats == expected_formats

    @staticmethod
    def _wd(wd):
        _WEEKDAY_MAP = {MO: 0, TU: 1, WE: 2, TH: 3, FR: 4, SA: 5, SU: 6}
        return _WEEKDAY_MAP[wd]

    def format_grid(self, dates):
        ax = self.ax

        # --- 1. Set exact axis limits ---
        ax.set_xlim(dates[0], dates[-1])

        # --- 2. Grid lines: every 1st of the month ---
        grid_locator = mdates.MonthLocator(bymonthday=1)
        ax.xaxis.set_major_locator(grid_locator)
        ax.xaxis.set_major_formatter(plt.NullFormatter())  # No labels on grid

        # --- 3. Labels: centered in each month (15th) ---
        first_label_date = np.datetime64(dates[0])  # Change to '2023-12-15' if you want to skip Nov
        last_label_date = np.datetime64(dates[-1])

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
            current = np.datetime64(f'{year}-{month:02d}-01')

        # CRITICAL: Convert datetime64 → float (Matplotlib internal format)
        label_nums = mdates.date2num([d.astype('datetime64[D]') for d in label_dates])

        # Now safe to set ticks
        ax.set_xticks(label_nums)
        ax.set_xticklabels([mdates.num2date(num).strftime('%b') for num in label_nums],
                           ha='center', va='top')

        # --- 4. Grid ---
        ax.grid(True, which='major', axis='x', linestyle='-', linewidth=1.0, alpha=0.7)
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=GraphicPanel._wd(mdates.MO)))
        ax.grid(True, which='minor', axis='x', linestyle=':', alpha=0.3)

        # --- 5. Layout ---
        self.figure.autofmt_xdate(bottom=0.18, rotation=0, ha='center')
        self.figure.tight_layout(pad=1.0)

    @staticmethod
    def first_pixel_rgb(bitmap):
        img = bitmap.ConvertToImage()
        r = img.GetRed(0, 0) / 255.0  # normalize 0–255 to 0.0–1.0
        g = img.GetGreen(0, 0) / 255.0
        b = img.GetBlue(0, 0) / 255.0
        return r, g, b
