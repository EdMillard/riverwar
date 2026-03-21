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
from wxui.progress_bar import ProgressBar
import wx
import wx.adv
import wx.lib.agw.aui as aui
from api.times_series import TimeSeries
from wxui.graphic_panel import GraphicPanel
import colorado.river
from sheet.sheet import Sheet, sheets

class WxAbstraction(object):
    def __init__(self, main_frame, ui_object):
        super().__init__()
        self.main_frame = main_frame
        self.notebook = ui_object
        self.progress_bar = None

    def plot_time_series(self, sources, time_series:list[TimeSeries], text='')->GraphicPanel:
        date_times = {}
        variable_name = ''
        units = ''
        for ts in time_series:
            variable_name = ts.variable_name
            x, y = ts.get_data()
            date_times[ts.source_name] = x
            if ts.units and not units:
                units = ts.units
        graphic_panel = GraphicPanel(self.notebook, sources, units, text=text)
        self.main_frame.verify_error_graphs.append(graphic_panel)
        graphic_panel.set_time_series(time_series)
        graphic_panel.variable_name = variable_name
        graphic_panel.text = ''
        self.notebook.AddPage(graphic_panel, variable_name)
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)
        graphic_panel.Show()
        return graphic_panel

    def plot_variable_from_source(self, variable_name, sources, units, variables, text)->GraphicPanel:
        graphic_panel = GraphicPanel(self.notebook, sources, units, text=text)
        self.main_frame.verify_error_graphs.append(graphic_panel)
        graphic_panel.set_variables(variables)
        graphic_panel.variable_name = variable_name
        graphic_panel.text = text
        self.notebook.AddPage(graphic_panel, variable_name)
        self.notebook.SetSelection(self.notebook.GetPageCount() - 1)
        graphic_panel.Show()
        return graphic_panel

    def log_message_cb(self, message):
        if self.progress_bar is not None:
            self.progress_bar.log_message(message)

    def log_message(self, message):
        if self.progress_bar:
            wx.CallAfter(self.log_message_cb, message)
        else:
            print(message)

    def set_progress_bar(self, progress_bar):
        self.progress_bar = progress_bar

class CustomTabArt(aui.AuiSimpleTabArt):
    def __init__(self):
        super().__init__()
        self._selected_bkbrush = wx.Brush(wx.Colour(150, 0, 0))
        self._selected_bkpen = wx.Pen(wx.WHITE_PEN)

class MainFrame(wx.Frame):
    size_gui = wx.Size(2048, 1024)
    size_report = wx.Size(2048, 1024)
    generate_report = False
    graph_verification_errors = True

    def __init__(self):
        super().__init__(None, title="Colorado Crisis", pos=wx.Point(512, 0), size=MainFrame.size_report)

        self.global_config:dict = {}
        self.global_config_path = Path('cache/Colorado/config.json')
        self.batch = False
        self.progress = None
        # self.water_year:WaterYear|None = None
        self.verify_error_graphs = []

        self.column_num = 1

        self.notebook = aui.AuiNotebook(self)
        custom_art = CustomTabArt()
        self.notebook.SetArtProvider(custom_art)

        self.ui_abstraction = WxAbstraction(self, self.notebook)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Show()

        colorado.river.run()


    def handle_click(self, clicked_str:str, start:int, end:int, line_text:str, line_num:int,
                     parent=None):
        sheet:Sheet | None = None
        for s in sheets:
            if s.start_parameters <= line_num <= s.end_parameters:
                sheet = s
                break
        if sheet:
            df = sheet.df

            # Create minimal wx app to demonstrate
           # frame = wx.Frame(None, title="Grouped Bar Chart Example", size=wx.Size(900, 600))

           # panel = wx.Panel(frame)
           # sizer = wx.BoxSizer(wx.VERTICAL)

            graphic_panel = GraphicPanel(self.notebook, None, None, text='')
            # self.main_frame.verify_error_graphs.append(graphic_panel)
            # graphic_panel.set_time_series(time_series)
            # graphic_panel.variable_name = variable_name
            graphic_panel.text = ''
            self.notebook.AddPage(graphic_panel, clicked_str)
            self.notebook.SetSelection(self.notebook.GetPageCount() - 1)
            graphic_panel.Show()

            # Create the plot
            graphic_panel.plot_grouped_bar_chart(
                df=df,
                param_columns=[clicked_str],
                title="Compact Math",
                bar_width=0.25,
                legend_loc="upper left"
            )

            # sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 10)

            # panel.SetSizer(sizer)
            # frame.Show()

    def Run(self, excel_paths, batch=False):
        w, h = wx.GetClientDisplayRect().GetSize()
        title = 'Colorado River'
        pb_frame = wx.Frame(None, title=title, pos=wx.Point(0, 0), size=wx.Size(600, h - 72))
        self.progress = ProgressBar(pb_frame)
        self.progress.log.editor.on_styled_text_clicked = self.handle_click

        self.ui_abstraction.set_progress_bar(self.progress)
        pb_frame.Show()

        line_num = 0
        for sheet in sheets:
            self.ui_abstraction.log_message(f"{sheet.name}")
            line_num += 1
            sheet.start_parameters = line_num
            for parameter in sheet.headers:
                self.ui_abstraction.log_message(f"\t\'{parameter}\'")
                line_num += 1
            sheet.end_parameters = line_num


class ColoradoApp(wx.App):
    def __init__(self):
        super().__init__()
        self.frame = None

    def OnInit(self):
        # batch = '--batch' in sys.argv or '-b' in sys.argv
        self.frame = MainFrame()
        wx.CallAfter(self.frame.Run, '')

        return True  # Must return True to continue

    def OnExit(self):
        return super().OnExit()

if __name__ == "__main__":
    app = ColoradoApp()
    app.MainLoop()