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
import wx
import wx.adv
import matplotlib
from source.water_year_info import WaterYearInfo
from api.times_series import TimeSeries
matplotlib.use('WxAgg')
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from enum import Enum
import numpy as np
import pandas as pd
from wxui.python_text_view import PythonTextView
from typing_extensions import LiteralString
from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU

# ------------------------------------------------------------------
# 1. Data
# ------------------------------------------------------------------
VARIABLES = [
    {"label": "", "options": []},
    {"label": "", "options": []},
    {"label": "", "options": []},
    {"label": "", "options": []},
]

color_names = X11_COLOR_NAMES = [
    'firebrick', "blue", "purple", # First 3 are important defaults
    "aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque",
    "black", "blanchedalmond",  "blueviolet", "brown", "burlywood", "cadetblue",
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
    "red", "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown",
    "seagreen", "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray",
    "slategrey", "snow", "springgreen", "steelblue", "tan", "teal", "thistle",
    "tomato", "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow",
    "yellowgreen"
]


class PlotType(Enum):
    NONE = 0
    LINE = 1
    STACKED = 2
    MARKER = 3
    BAR = 4
    BAR_HORIZONTAL = 5
    STACKED_BAR = 6
    FILL_BETWEEN = 7

    def __str__(self):
        names = {
            self.NONE: "None",
            self.LINE: "Line",
            self.STACKED: "Stacked",
            self.MARKER: "Marker",
            self.BAR: "Bar",
            self.BAR_HORIZONTAL: "Bar Horizontal",
            self.STACKED_BAR: "Stacked Bar",
            self.FILL_BETWEEN: "Fill Between",
        }
        return names[self]


class Plot:
    def __init__(self, source_name : str, variable_name : str, color:tuple=None, plot_type:PlotType=PlotType.LINE):
        self.source_name:str = source_name
        self.variable_name:str = variable_name
        self.color:tuple = color
        self.plot_type:PlotType = plot_type
        self.marker_type:str = 'x'
        self.width:int = 1
        self.x = None
        self.y = None
        self.year = None

    def __str__(self):
        return f'{self.source_name}, {self.variable_name}, {self.color}. {self.plot_type}'


class GraphicPanel(wx.Panel):
    INSERT_POS = 9

    def __init__(self, parent, sources:dict, units:str, text:str=None):
        super().__init__(parent)
        self.sources:dict = sources
        self.units:str = units
        self._current_marker_artists:list = []
        self.python_text_view:PythonTextView|None = None

        # For doc report generation on verify error panels
        self.variable_name:str|None = None

        self.figure = Figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.ax = self.figure.add_subplot(111)

        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()

        self.colours: list[tuple[str, tuple[int, int, int]]] = [
            ("", GraphicPanel.color_as_rgb(wx.RED)),
            ("", GraphicPanel.color_as_rgb(wx.BLUE)),
            ("", GraphicPanel.color_as_rgb(wx.GREEN)),
            ("", GraphicPanel.color_as_rgb(wx.CYAN)),
            ("", (172, 0, 172)),
            ("", (172, 172, 0)),
            ("", (0, 172, 172)),
            ("", GraphicPanel.color_as_rgb(wx.BLACK)),
        ]
        self.colours.clear()
        self.valid_colors = {}

        db = wx.ColourDatabase()
        for name in color_names:
            color = db.Find(name)  # Returns wx.Colour
            if color:
                rgb = (color.Red(), color.Green(), color.Blue())
                self.valid_colors[name] = rgb
        for valid_color, rgb in self.valid_colors.items():
            v = ('', rgb)
            # v = (valid_color, rgb) # If you want color names in menu
            self.colours.append(v)

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
            self.python_text_view.editor.on_styled_text_clicked = self.handle_click

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

    @staticmethod
    def find_date_and_index(dates: list, month_day: str):
        """
        Find the first date in the list that matches the given 'month_day' format (e.g., 'Dec-10')
        and return the date object along with its index.

        Handles lists containing pd.Timestamp, np.datetime64, or a mix of compatible date types.
        """
        if month_day:
            print(f'find_date_and_index {month_day}')
            for idx, ts in enumerate(dates):
                # Convert to pandas Timestamp for uniform formatting
                if not isinstance(ts, pd.Timestamp):
                    ts = pd.Timestamp(ts)
                if ts.strftime('%b-%d') == month_day:
                    return ts, idx
            raise ValueError(f"No date matching {month_day} found in the list")
        else:
            print(f'find_date_and_index no date string')


    @staticmethod
    def find_date_and_index2(dates: list[pd.Timestamp], month_day: str):
        print(f'find_date_and_index {month_day}')
        return next((ts, idx) for idx, ts in enumerate(dates) if ts.strftime('%b-%d') == month_day)

    def handle_click(self, selected_string: str, start: int, end: int, line_text: str, parent=None):
        # If this is a known variable name we aren't handling this click, we are looking for month days i.e. 'Jun-1'
        for source_name, source in self.sources.items():
            if selected_string in source:
                print(f'GraphicPanel doesn\'t handle variable names {selected_string}')
                return

        dates = self.get_dates('')
        if dates is None:
            print(f'GraphicPanel handle click no dates {selected_string}')
            return

        dt, idx = GraphicPanel.find_date_and_index(dates, selected_string)
        y_left = y_right = 0
        for i, ctrl in enumerate(self.var_controls):
            source_name = ctrl["source"].GetStringSelection()
            source = self.sources.get(source_name)
            if source is not None:
                variable_name = ctrl["var"].GetStringSelection()
                variables = source[variable_name]
                if i == 0:
                    y_left = variables[idx]
                elif i == 1:
                    y_right = variables[idx]
                    break

        left_text = f'{y_left:9.3f}'
        right_text = f'{y_right:9.3f}'
        self.add_vertical_marker(
            time=dt,
            time_str=selected_string,
            y_left=y_left,
            y_right=y_right,
            left_text=left_text,
            right_text=right_text,
            line_color='red',
            line_width=2,
            text_color='darkred',
            fontsize=10,
            fontweight='bold'
        )

    def preprocess_plot(self):
        plots = []
        prev_source_name = ''
        multiple_sources = False
        dates = None
        for i, ctrl in enumerate(self.var_controls):
            source_name = ctrl["source"].GetStringSelection()
            source = self.sources.get(source_name)
            if source is not None:
                variable_name = ctrl["var"].GetStringSelection()
                if variable_name:
                    sel = ctrl["color"].GetSelection()
                    bmp = ctrl["color"].GetItemBitmap(sel)
                    rgb = GraphicPanel.first_pixel_rgb(bmp)
                    if source_name == 'custom':
                        plot_type = PlotType.MARKER
                    else:
                        plot_type = PlotType.LINE
                    plot = Plot(source_name, variable_name, rgb, plot_type=plot_type)
                    if source_name != prev_source_name:
                        multiple_sources = True
                    prev_source_name = source_name

                    y = source.get(variable_name)
                    if isinstance(y, np.ndarray) and len(y.dtype) == 2:
                        plot.x = dates = y['dt']
                        plot.y = y['val']
                    else:
                        plot.x = dates = self.get_dates(source_name)
                        plot.y = y
                    if plot.x is None:
                        print(f'plot.x is None: {source_name} {plot.variable_name}')
                    if plot.y is None:
                        print(f'plot.y is None: {source_name} {plot.variable_name}')

                    if len(plot.x):
                        water_year_info_first = WaterYearInfo.get_water_year(plot.x[0])
                        water_year_info_last = WaterYearInfo.get_water_year(plot.x[-1])
                        if water_year_info_first.year == water_year_info_last.year:
                            plot.year = water_year_info_first.year
                        else:
                            print(f'Plot multiyear data {water_year_info_first.year}-{water_year_info_last.year} {plot.source_name} {plot.variable_name}')

                    plots.append(plot)

        prev_length = 0
        prev_year = 0
        multiple_years = False
        multiple_lengths = False
        for plot in plots:
            if dates is None:
                dates = plot.x

            if plot.y is not None:
                if prev_length and len(plot.y) != prev_length:
                    multiple_lengths = True

                if plot.year is not None:
                    if prev_year and prev_year != plot.year:
                        multiple_years = True
                        print(f'multiple years True {prev_year} {plot.year}')
                    prev_year = plot.year

                    prev_length = len(plot.y)
            else:
                print(f'Plot y invalid {plot.source_name} {plot.variable_name}')

        if multiple_years:
            first_plot_actual_feb29_indices = GraphicPanel.actual_feb29_indices(plots[0].x)
            first_plot_potential_feb29_indices = GraphicPanel.index_of_feb29_from_timestamps(plots[0].x)
            dates = plots[0].x
            for n, plot in enumerate(plots):
                if n > 0:
                    actual_feb29_indices = GraphicPanel.actual_feb29_indices(plot.x)
                    if len(first_plot_actual_feb29_indices) != len(actual_feb29_indices):
                        potential_feb29_indices = GraphicPanel.index_of_feb29_from_timestamps(plot.x)
                        if len(first_plot_actual_feb29_indices) > len(actual_feb29_indices):
                            if first_plot_actual_feb29_indices[0] == 120 and potential_feb29_indices[1] == 119:
                                plot.y = GraphicPanel.duplicate_at_index(plot.y, potential_feb29_indices[1])
                            else:
                                print(f'Unexpected leap year indices {first_plot_actual_feb29_indices} {potential_feb29_indices}')
                        else:
                            if first_plot_potential_feb29_indices[1] == 119 and actual_feb29_indices[0] == 120:
                                plot.y = GraphicPanel.remove_at_index(plot.y, actual_feb29_indices[0])
                            else:
                                print(f'Unexpected leap year indices {first_plot_potential_feb29_indices} {actual_feb29_indices}')
                    plot.x = plots[0].x

                print(f'plot {n} {len(plot.x)} {len(plot.y)}')

        if multiple_lengths:
            for plot in plots:
                if len(plot.y) != len(dates):
                    if len(dates) == 366:
                        if len(plot.y) != 366:
                            pass
                        pass
                    elif len(dates) == 365:
                        if len(plot.y) != 365:
                            pass
                        pass
                    else:
                        print('FIXME partial year')

        return plots, dates, multiple_years

    def remove_at_index(data, idx):
        """
        Removes the element at index `idx` from a list or numpy array.

        Parameters:
        -----------
        data : list or np.ndarray
            Input sequence (1D list or numpy array)
        idx  : int
            Index of the element to remove (0 <= idx < len(data))

        Returns:
        --------
        Same type as input, but with the element at `idx` removed.

        Examples:
            remove_at_index([10, 20, 30, 40], 1)   → [10, 30, 40]
            remove_at_index(np.array([119, 200, 300]), 0) → array([200, 300])
        """
        if isinstance(data, np.ndarray):
            return np.delete(data, idx)

        elif isinstance(data, list):
            # Create new list without the element at idx
            return data[:idx] + data[idx + 1:]

        else:
            raise TypeError("Input must be a list or numpy.ndarray")

    @staticmethod
    def duplicate_at_index(data, idx):
        """
        Duplicates the element at index `idx` and inserts the duplicate
        immediately after it (at position idx+1).

        Works with:
        - numpy.ndarray  → returns new np.ndarray
        - list           → returns new list

        Parameters:
        -----------
        data : np.ndarray or list
            Input sequence (1D array or list)
        idx  : int
            Index of the element to duplicate (0 <= idx < len(data))

        Returns:
        --------
        Same type as input, with one extra element (the duplicate inserted)

        Examples:
            duplicate_at_index([10, 20, 30], 1)          → [10, 20, 20, 30]
            duplicate_at_index(np.array([119, 200]), 0) → array([119, 119, 200])
        """
        if isinstance(data, np.ndarray):
            return np.insert(data, idx + 1, data[idx])

        elif isinstance(data, list):
            # For lists: create a new list with slice + insert
            return data[:idx + 1] + [data[idx]] + data[idx + 1:]

        else:
            raise TypeError("Input must be a numpy.ndarray or a list")

    def get_dates(self, source_name:str):
        if source_name:
            source = self.sources.get(source_name)
            if source is not None:
                if 'DATE' in source:
                    return source['DATE']
        for source_name, source in self.sources.items():
            if 'DATE' in source:
                return source['DATE']
        return None

    def update_plot(self):
        self.ax.clear()

        plots, x, multiple_years = self.preprocess_plot()
        dates = x
        units = ''
        did_plot = False
        stacked:list[Plot] = []
        stacked_labels:list[str] = []
        for plot in plots:
            if plot.plot_type == PlotType.STACKED:
                stacked.append(plot)

        if len(stacked) == 1:
            self.ax.stackplot(stacked[0].x, stacked[0].y, labels=stacked_labels)
        if len(stacked) == 2:
            self.ax.stackplot(stacked[0].x, stacked[0].y, stacked[1].y, labels=stacked_labels)
        elif len(stacked) == 3:
            self.ax.stackplot(stacked[0].x, stacked[0].y, stacked[1].y, stacked[2].y, labels=stacked_labels)
        elif len(stacked) == 4:
            self.ax.stackplot(stacked[0].x, stacked[0].y, stacked[1].y, stacked[2].y, stacked[3].y, labels=stacked_labels)

        for plot in plots:
            y = plot.y
            if self.units is not None and plot.variable_name in self.units:
                mext_units = self.units[plot.variable_name]
                if units and mext_units != units:
                    print(f'Units mismatch {plot.variable_name} {mext_units} {units}')
                else:
                    units = mext_units
            else:
                units = ''

            x = plot.x
            if x is not None and y is not None:
                # self.ax.fill_between(dates, 0, y1, color='skyblue', label='Variable 1', alpha=0.8)
                # self.ax.bar(x_pos, var1, width=bar_width, label='Variable 1', color='skyblue', edgecolor='black', linewidth=0.5)
                # bars1 = self.ax.bar(x_pos - bar_width, var1, bar_width,
                #                             label='Variable 1', color='#4e79a7', edgecolor='black', linewidth=0.6)
                #         bars2 = self.ax.bar(x_pos,            var2, bar_width,
                #                             label='Variable 2', color='#f28e2b', edgecolor='black', linewidth=0.6)
                #         bars3 = self.ax.bar(x_pos + bar_width, var3, bar_width,
                #                             label='Variable 3', color='#76b7b2', edgecolor='black', linewidth=0.6)
                # ax.barh(months, values, height=0.7, color='coral')            # horizontal
                # ax.stackplot(dates, v1, v2, v3, labels=['A','B','C'])        # stacked area
                # ax.step(dates, values, where='mid', linewidth=2, color='purple')
                # ax.stem(dates, values, linefmt='C2-', markerfmt='C2D')
                # ax.violinplot([jan, feb, mar], positions=[0,1,2])
                if plot.plot_type == PlotType.MARKER:
                    self.ax.plot(x, y, 'x', color=plot.color, label=f'Custom {plot.variable_name} ({plot.source_name})',
                                 markersize=10)
                elif plot.plot_type == PlotType.BAR:
                    self.ax.bar(x, y, color=plot.color,  label=f'{plot.variable_name} ({plot.source_name}',
                                width=plot.width, edgecolor='black', linewidth=0.5)
                elif plot.plot_type == PlotType.STACKED:
                    pass
                elif plot.plot_type == PlotType.LINE:
                    self.ax.plot(x, y, color=plot.color, label=f"{plot.variable_name} ({plot.source_name})")
                else:
                    print(f'Plot type not implemented {plot.plot_type}')
                did_plot = True
            else:
                print(f'Plot failed {plot.variable_name}')

        if did_plot:
            self.ax.legend()
        self.ax.set_title("Dolores")
        # self.ax.set_xlabel("Month")
        if dates is not None:
            success = self.format_grid(dates)
            if not success:
                return
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

    def set_time_series(self, time_series:list[TimeSeries]):
        for n, ts in enumerate(time_series):
            ctrl = self.var_controls[n]
            self.source_changed(ctrl, ts.source_name, ts.variable_name)

        wx.CallAfter(self.update_plot)

    def set_variables(self, variables):
        for variable in variables:
            if len(variable) == 4:
                index, source, variable_name, pass_fail = variable
            else:
                index, source, variable_name = variable

            ctrl = self.var_controls[index]
            self.source_changed(ctrl, source, variable_name)

        wx.CallAfter(self.update_plot)

    def source_changed(self, ctrl, source, variable_name):
        source_ctrl = ctrl.get('source')
        source_selected = source_ctrl.GetStringSelection()
        if source_selected != source:
            self.source_change(source, control=source_ctrl, set_source_control=True)
            # source_ctrl.SetStringSelection(source)
        wx.GetApp().Yield()
        var_ctrl = ctrl.get('var')
        var_ctrl.SetStringSelection(variable_name)
        wx.GetApp().Yield()

    def source_select(self):
        for ctrl in self.var_controls:
            source_choice = ctrl['source']
            if source_choice:
                # FIXME, selection call back isn't being called
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
        self.source_change(source, control=control)

    def sources_change(self, sources, control=None, set_source_control=False):
        first_variable_name = ''
        for n, source in enumerate(sources):
            if n < len(self.var_controls):
                # self.source_change(source, control=self.var_controls[n], set_source_control=set_source_control)
                ctrl = self.var_controls[n]
                variable_names = self.variable_names_for_source(source)
                var_choice = ctrl["var"]
                current_variable_name = var_choice.GetStringSelection()
                if current_variable_name and not first_variable_name:
                    first_variable_name = current_variable_name
                if set_source_control:
                    ctrl['source'].SetStringSelection(source)
                var_choice.Clear()
                for variable_name in variable_names:
                    var_choice.Append(variable_name)
                if current_variable_name:
                    var_choice.SetStringSelection(current_variable_name)
                elif first_variable_name:
                    var_choice.SetStringSelection(first_variable_name)
        self.Layout()
        self.update_plot()

    def source_change(self, source, control=None, set_source_control=False):
        variable_names = self.variable_names_for_source(source)
        for i, ctrl in enumerate(self.var_controls):
            if control is None or control == ctrl['source']:
                var_choice = ctrl["var"]
                current_variable_name = var_choice.GetStringSelection()
                if set_source_control:
                    ctrl['source'].SetStringSelection(source)
                var_choice.Clear()
                for variable_name in variable_names:
                    var_choice.Append(variable_name)
                if current_variable_name is not None:
                    var_choice.SetStringSelection(current_variable_name)
        self.Layout()
        self.update_plot()

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

    def create_color_choice(self, parent, colors):
        combo = wx.adv.BitmapComboBox(parent, style=wx.CB_READONLY)

        # keep references so the bitmaps are not garbage-collected
        _bitmaps = []

        for name, rgb in self.colours:
            bmp = GraphicPanel.make_bitmap(rgb, size=(24, 24))
            _bitmaps.append(bmp)
            combo.Append(name, bmp)  # text + bitmap
        return combo

    def insert_tool_block(self, i, var_info, start_pos):
        pos = start_pos

        # Color selector – Choice with COLORED hex strings
        col_choice = self.create_color_choice(self.toolbar, self.colours)
        col_choice.SetSelection(i)
        self.toolbar.InsertControl(pos, col_choice)
        col_choice.Bind(wx.EVT_COMBOBOX, self.on_change)
        pos += 1

        # Data Source Choice
        if self.sources is not None:
            source_names = list(self.sources.keys())
        else:
            source_names = []
        # if len(source_names) > 1:
        source_choice = wx.Choice(self.toolbar, choices=source_names)
        source_choice.Bind(wx.EVT_CHOICE, self.on_source_change)
        default_source = 0
        if source_names:
            variable_names = self.variable_names_for_source(source_names[default_source])
            source_choice.SetSelection(default_source)
        else:
            variable_names = []
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
        if dates is not None and len(dates):
            ax.set_xlim(dates[0], dates[-1])
        else:
            print('plot dates empty')
            return False

        # --- 2. Grid lines: every 1st of the month ---
        grid_locator = mdates.MonthLocator(bymonthday=1)
        ax.xaxis.set_major_locator(grid_locator)
        ax.xaxis.set_major_formatter(plt.NullFormatter())  # No labels on grid

        # --- 3. Labels: centered in each month (15th) ---
        first_label_date = np.datetime64(dates[0])  # Change to '2023-12-15' if you want to skip Nov
        last_label_date = np.datetime64(dates[-1])

        label_dates = []
        current = first_label_date
        if first_label_date >= last_label_date:
            print(f'Invalid date range {first_label_date} {last_label_date}')
            return False
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

        return True

    @staticmethod
    def first_pixel_rgb(bitmap):
        img = bitmap.ConvertToImage()
        r = img.GetRed(0, 0) / 255.0  # normalize 0–255 to 0.0–1.0
        g = img.GetGreen(0, 0) / 255.0
        b = img.GetBlue(0, 0) / 255.0
        return r, g, b


    @staticmethod
    def actual_feb29_indices(ts_list):
        """
        Given a list of pandas.Timestamp objects (daily frequency),
        return a NumPy array of indices where February 29 actually occurs.

        Returns:
            np.ndarray: indices of real Feb 29 dates (e.g. 2024-02-29, 2020-02-29, etc.)
            Empty array if no leap-year Feb 29 is present.
        """
        # Convert to numpy datetime64[ns] array (preserves leap days)
        dates = pd.to_datetime(ts_list).values

        # Use pandas accessors for safe month/day extraction
        # This works on datetime64[ns] arrays and handles leap days correctly
        is_feb29 = (pd.DatetimeIndex(dates).month == 2) & (pd.DatetimeIndex(dates).day == 29)

        # Get indices where condition is True
        indices = np.where(is_feb29)[0]

        return indices

    @staticmethod
    def index_of_feb29_from_timestamps(ts_list):
        """
        Given a list of pandas.Timestamp objects (daily frequency),
        return the index where February 29 is or would be inserted.

        Fixed: Uses pandas for safe year addition to avoid NumPy ufunc casting errors.
        """
        # Convert list[Timestamp] → sorted numpy datetime64 array
        dates = pd.to_datetime(ts_list).values

        # Get unique years from the data
        years = pd.DatetimeIndex(dates).year.unique()

        # Build Feb 29 targets for each year using pandas (safe arithmetic)
        feb29_targets = []
        for year in years:
            try:
                feb29 = pd.Timestamp(year=year, month=2, day=29)  # Raises ValueError if not leap year, but we don't care
            except ValueError:
                feb29 = pd.Timestamp(year=year, month=3, day=1) - pd.Timedelta(days=1)  # Feb 28
            feb29_targets.append(feb29.to_numpy())

        feb29_targets = np.array(feb29_targets)

        # Find insertion points (or exact positions if exists)
        indices = np.searchsorted(dates, feb29_targets, side='left')

        # Return single int if one year, else array
        return indices[0] if len(indices) == 1 else indices.astype(int)

    # time_num = ax.convert_xaxis_units(event_time)  # works
    # or
    # time_num = ax.transData.transform((mdates.date2num(event_time), 0))[0]
    def add_vertical_marker(self, time, time_str, y_left, y_right,
                            left_text=None, right_text=None,
                            line_color='red', text_color='darkred', **kwargs):
        ax = self.ax

        # === 1. Remove previous marker (line + texts) ===
        for artist in self._current_marker_artists:
            artist.remove()
        self._current_marker_artists.clear()

        # === 2. Convert time ===
        if not isinstance(time, pd.Timestamp):
            time = pd.to_datetime(time)

        # === 3. Draw new vertical line ===
        vline = ax.axvline(time, color=line_color, linestyle='--', linewidth=2, zorder=5)
        self._current_marker_artists.append(vline)

        # === 4. Add text labels ===
        default_left_bbox = dict(boxstyle="round,pad=0.4", facecolor="yellow", alpha=0.8, edgecolor="orange")
        default_right_bbox = dict(boxstyle="round,pad=0.4", facecolor="lightgreen", alpha=0.8, edgecolor="green")
        time_bbox = dict(boxstyle="round,pad=0.4", facecolor="lightgreen", alpha=0.8, edgecolor="blue")

        y_min, y_max = ax.get_ylim()

        texts = []
        if left_text:
            offset = pd.Timedelta(days=2)  # or hours=6, etc.
            time_offset = time - offset
            txt = ax.text(time_offset, y_left, f"  {left_text}",
                          color=text_color, fontsize=10, fontweight='bold',
                          va='center', ha='right',
                          bbox=kwargs.get('left_bbox', default_left_bbox),
                          zorder=6)
            texts.append(txt)

        if right_text:
            offset = pd.Timedelta(days=2)  # or hours=6, etc.
            time_offset = time + offset
            txt = ax.text(time_offset, y_right, f"  {right_text}",
                          color=text_color, fontsize=10, fontweight='bold',
                          va='center', ha='left',
                          bbox=kwargs.get('right_bbox', default_right_bbox),
                          zorder=6)
            texts.append(txt)

        # Use this to get consistent offset on time axis
        # txt = ax.annotate(
        #     f" {left_text}",
        #     xy=(time, y_left),                  # Anchor at original time
        #     xycoords='data',
        #     xytext=(10, 0),                     # Shift right by 10 points (adjust value)
        #     textcoords='offset points',         # Offset in screen points
        #     color=text_color,
        #     fontsize=10,
        #     fontweight='bold',
        #     va='center',
        #     ha='left',                          # Change to 'left' since offset pushes it right
        #     bbox=kwargs.get('left_bbox', default_left_bbox),
        #     zorder=6
        # )

        if time_str:
            txt = ax.text(time, y_min, f"  {time_str}",
                          color=text_color, fontsize=10, fontweight='bold',
                          va='center', ha='center',
                          bbox=kwargs.get('left_bbox', time_bbox),
                          zorder=6)
            texts.append(txt)

        # Store all new artists
        self._current_marker_artists.extend(texts)

        # === 5. Redraw ===
        self.canvas.draw()

import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

class DraggableTimeCursor:
    """
    One single vertical line across ALL subplots.
    Draggable only horizontally (time axis).
    Your callback receives the current Timestamp and returns
    one dict per subplot with y-value and optional text.
    """
    def __init__(self, fig, canvas, axes_list, callback):
        """
        fig        : matplotlib Figure
        canvas     : FigureCanvasWxAgg
        axes_list  : list[Axes] in top-to-bottom order (all must sharex=True)
        callback   : def callback(ts: pd.Timestamp) -> list[dict]
                     Each dict: {'y': float, 'text': str, 'side': 'left'|'right'}
        """
        self.fig = fig
        self.canvas = canvas
        self.axes_list = axes_list
        self.callback = callback

        self.current_time = None
        self.artists = []           # vlines + text objects
        self.dragging = False

        # Start in the middle
        xlim = axes_list[0].get_xlim()
        middle = pd.to_datetime((xlim[0] + xlim[1]) / 2, unit='D')
        self._update_marker(middle)

        # Mouse events
        self.cid_press   = canvas.mpl_connect('button_press_event',   self.on_press)
        self.cid_release = canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion  = canvas.mpl_connect('motion_notify_event',  self.on_motion)

    def _update_marker(self, timestamp):
        if not isinstance(timestamp, pd.Timestamp):
            timestamp = pd.to_datetime(timestamp)

        if timestamp == self.current_time:
            return
        self.current_time = timestamp

        # Remove old artists
        for art in self.artists:
            art.remove()
        self.artists.clear()

        # Get your dynamic data
        try:
            labels = self.callback(timestamp)
        except Exception:
            labels = [{} for _ in self.axes_list]

        line_color = 'red'
        for ax, label in zip(self.axes_list, labels):
            y = label.get('y')
            text = label.get('text', '')
            side = label.get('side', 'left')

            # One vertical line per subplot (spans the whole subplot height)
            vline = ax.axvline(timestamp, color=line_color, linewidth=2, alpha=0.9, zorder=10)
            self.artists.append(vline)

            if y is not None and text:
                ha = 'right' if side == 'left' else 'left'
                bbox_color = 'red' if side == 'left' else 'green'
                txt = ax.text(timestamp, y, f"  {text}",
                              color='white', fontsize=9, fontweight='bold',
                              va='center', ha=ha,
                              bbox=dict(boxstyle="round,pad=0.3", facecolor=bbox_color, alpha=0.9),
                              zorder=11)
                self.artists.append(txt)

        self.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes in self.axes_list and event.button == 1:
            self.dragging = True
            self._move_to_event(event)

    def on_release(self, event):
        self.dragging = False

    def on_motion(self, event):
        if self.dragging and event.inaxes in self.axes_list:
            self._move_to_event(event)

    def _move_to_event(self, event):
        # event.xdata is already a matplotlib date number → convert to Timestamp
        new_time = pd.to_datetime(event.xdata, unit='D')
        self._update_marker(new_time)

    def remove(self):
        for art in self.artists:
            art.remove()
        self.canvas.mpl_disconnect(self.cid_press)
        self.canvas.mpl_disconnect(self.cid_release)
        self.canvas.mpl_disconnect(self.cid_motion)
        self.canvas.draw_idle()

class MyPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.fig, self.axes = plt.subplots(5, 1, sharex=True, figsize=(12, 8))
        self.canvas = FigureCanvas(self, -1, self.fig)

        dates = pd.date_range("2024-11-01", periods=365, freq="D")
        np.random.seed(0)
        for i, ax in enumerate(self.axes):
            y = 100 + np.cumsum(np.random.randn(len(dates)))
            ax.plot(dates, y, label=f"Asset {i+1}")
            ax.legend(loc='upper left')
            ax.grid(alpha=0.3)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # ←←← This is all you need
        self.cursor = DraggableTimeCursor(
            fig=self.fig,
            canvas=self.canvas,
            axes_list=self.axes,
            callback=self.get_labels_at_time
        )

    def get_labels_at_time(self, ts: pd.Timestamp):
        """Called every time the cursor moves"""
        labels = []
        for ax in self.axes:
            line = ax.lines[0]
            xdata = pd.to_datetime(line.get_xdata())
            ydata = line.get_ydata()
            idx = (xdata - ts).abs().argmin()
            price = ydata[idx]
            labels.append({
                'y': price,
                'text': f"{price:.2f}",
                'side': 'left'          # or 'right' if you prefer
            })
        return labels