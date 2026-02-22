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
from pathlib import Path
import re
import json
import wx
import wx.adv
import wx.lib.agw.aui as aui
from api.pool import FillRun, DrainRun, EvapRun
from dwcd.water_year import TimeSeries
from dwcd.water_year import WaterYear
from dwcd.dolores_year import DoloresYear
from source.water_year_info import WaterYearInfo
from report.doc import Report
from wxui.graphic_panel import GraphicPanel
from wxui.file_chooser import FileChooser
from wxui.progress_bar import ProgressBar
from wxui.python_text_view import PythonTextView
import sys
import threading

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
        super().__init__(None, title="Dolores Project", pos=wx.Point(512, 0), size=MainFrame.size_report)

        self.global_config:dict = {}
        self.global_config_path = Path('cache/Dolores/config.json')
        self.batch = False
        self.progress = None
        self.water_year:WaterYear|None = None
        self.verify_error_graphs = []

        self.notebook = aui.AuiNotebook(self)
        custom_art = CustomTabArt()
        self.notebook.SetArtProvider(custom_art)

        self.ui_abstraction = WxAbstraction(self, self.notebook)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def Run(self, excel_paths, batch=False):
        self.batch = batch
        if not batch and excel_paths and excel_paths[0] is None:
            try:
                with self.global_config_path.open("r") as file:
                    self.global_config = json.load(file)
                    current_file = self.global_config.get('current_file', '')
                    if current_file:
                        excel_paths = [current_file]
            except FileNotFoundError:
                pass
        if len(excel_paths) > 1:
            title = f'Batch loading {len(excel_paths)} files'
            MainFrame.graph_verification_errors = False
        else:
            excel_path = excel_paths[0]
            if excel_path:
                file_name = Path(excel_path)
            else:
                file_name = Path('Amended/River2024-Amended.xlsx')
                # file_name = Path('Daily/River2025-Provisional (27-OCT-2025).xlsx')
            excel_paths = [file_name]
            title = file_name.stem

        w, h = wx.GetClientDisplayRect().GetSize()
        pb_frame = wx.Frame(None, title=title, pos=wx.Point(0,0), size=wx.Size(600, h-72))
        self.progress = ProgressBar(pb_frame)
        self.progress.log.editor.on_styled_text_clicked = self.handle_click

        self.ui_abstraction.set_progress_bar(self.progress)
        pb_frame.Show()

        thread = threading.Thread(
            target=self.background_task,
            args=(excel_paths, ),
            daemon=True
        )
        thread.start()

    def background_task(self, excel_paths):
        for excel_path in excel_paths:
            self.background_load(excel_path)
        if len(excel_paths) > 1:
            self.progress.log_message('Variable name archaeology')
            WaterYear.variable_name_archaeology_all_years(Path(WaterYear.global_file_names['variable_names_db']),
                                                          Path(WaterYear.global_file_names['variable_names_history_log']))
            WaterYear.variable_name_archaeology_all_years(Path(WaterYear.global_file_names['variable_names_raw_db']),
                                                          Path(WaterYear.global_file_names['variable_names_raw_history_log']))
            wx.CallAfter(self.progress.set_progress, 100, "Batch processing complete")

    def background_load(self, file_name):
        self.water_year = DoloresYear(self.ui_abstraction)
        wx.CallAfter(self.progress.set_progress, 20, f"Loading {file_name.name}")
        if not self.water_year.load(file_name, force_reload=True):
            return

        wx.CallAfter(self.progress.set_progress, 40, "Running Dolores Water Accounting")
        self.water_year.run()

        report = None
        if self.generate_report:
            self.progress.set_progress(72, "Create Report Doc")

            report = Report()
            report.create_title_page(self.water_year.water_year_info.year, 'Ed Millard')
            report.page_break()
            # This may only work in Word on Windows, Libreoffice you create TOC manually
            #DoloresApp.report.table_of_contents()
            report.page_setup()

        # Does verification mostly, generates excel
        self.water_year.post_process()

        done = threading.Event()
        wx.CallAfter(self.post_process_task, report, file_name, done)
        done.wait()
        pass

    @staticmethod
    def clear_after_last(s, last_char):
        index = s.rfind(last_char)
        if index == -1:
            return s
        return s[:index]

    @staticmethod
    def extract_quoted_strings(line: str):
        pattern = r"'([^']*)'"
        results = []
        for match in re.finditer(pattern, line):
            content = match.group(1)
            start = match.start(1)  # Start of content inside quotes
            end = match.end(1) - 1  # End of content inside quotes (inclusive)
            is_date = bool(re.match(r'^[A-Za-z]{3}-\d{2}$', content))
            results.append({
                'string': content,
                'start': start,
                'end': end,
                'is_date': is_date
            })
        return results

    def handle_click(self, clicked_str:str, start:int, end:int, line_text:str, parent=None):
        # Log file
        #
        if '.log' in clicked_str or '.json' in clicked_str:
            self.show_file(clicked_str)
            return

        variable_name = ''
        date_str = ''
        strings_info = MainFrame.extract_quoted_strings(line_text)
        for string_info in strings_info:
            if clicked_str == string_info['string']:
                if string_info['is_date']:
                    date_str = clicked_str
                else:
                    variable_name = clicked_str

        # Parameter name with verification details
        #
        if variable_name and 'PASS' in line_text or 'FAIL' in line_text:
            if  self.verification_graph(variable_name):
                return

        # Date from pool run
        #
        if 'Fill' in line_text or 'Drain' in line_text or 'Evap' in line_text:
            if self.graph_run(date_str, line_text, strings_info):
               return

        # USGS, CDSS and USBR data
        #
        if variable_name and self.graph_api_data(variable_name, line_text):
            return

        # Parameter name, nothing special
        #
        if self.graph_variable(variable_name):
            return

        # Return to graphic panel to handle, Month-day string for annotation marker probably
        #
        if date_str and parent is not None:
            grand_parent = parent.GetParent()
            if grand_parent is not None and isinstance(grand_parent, GraphicPanel):
                # Date
                grand_parent.handle_click(date_str, start, end, line_text, parent=None)
                return

            # if grand_parent is not None and isinstance(grand_parent, aui.AuiNotebook):
                # page_index = grand_parent.GetSelection()
                # name = grand_parent.GetPageText(page_index)

        print(f'Click not handled: {variable_name} {line_text}')

    @staticmethod
    def select_tab_by_title(notebook: aui.AuiNotebook, search_title: str, case_sensitive: bool = False) -> bool:
        """
        Searches the titles of all tabs in the notebook for the given string.
        If a match is found, selects that tab and returns True.
        Returns False if no match.

        Args:
            notebook: The wx.Notebook instance.
            search_title: The string to search for in tab titles.
            case_sensitive: If False (default), search is case-insensitive.

        Returns:
            bool: True if a matching tab was found and selected, False otherwise.
        """
        if not case_sensitive:
            search_title = search_title.lower()

        for index in range(notebook.GetPageCount()):
            tab_title = notebook.GetPageText(index)
            if not case_sensitive:
                tab_title = tab_title.lower()

            if search_title in tab_title:  # Partial match
                # if tab_title == search_title:       # Use this line for exact match
                notebook.SetSelection(index)  # Makes the tab visible/selected
                return True

        return False

    def show_file(self, file_name:str):
        path = self.water_year.cache_base_path.joinpath(file_name)
        try:
            text = path.read_text(encoding="utf-8")
            python_text_view = PythonTextView(self.notebook)
            name = MainFrame.clear_after_last(file_name, '_')
            name = name.replace('_', '')
            name = name.capitalize()
            if not MainFrame.select_tab_by_title(self.notebook, name):
                self.notebook.AddPage(python_text_view, name)
                self.notebook.SetSelection(self.notebook.GetPageCount() - 1)
                python_text_view.update_text(text)
                python_text_view.editor.on_styled_text_clicked = self.handle_click
        except FileNotFoundError:
            print(f'Log file not found {path}')

    def graph_variable(self, variable_name:str):
        time_series: list[TimeSeries] = []
        n = 0
        for source_name, source in self.water_year.sources.items():
            if variable_name in source:
                if 'DATE' in source:
                    dt = None
                else:
                    dt = self.water_year.y['DATE']
                ts = TimeSeries(variable_name, source_name, source, alt_date_time=dt)
                time_series.append(ts)
                n += 1

        text = ''
        if len(time_series) > 1:
            diffs, text = WaterYear.flexible_diff(time_series)

        if len(time_series):
            graphic_panel = self.ui_abstraction.plot_time_series(self.water_year.sources, time_series, text=text)
            if graphic_panel.python_text_view is not None:
                graphic_panel.python_text_view.editor.on_styled_text_clicked = self.handle_click
            return True
        return False

    def graph_run(self, date_str:str, line_text:str, string_info:list[dict]):
        if 'Fill' in line_text:
            if self.water_year.fill_queue:
                run: FillRun
                for run in self.water_year.fill_queue:
                    if run.start_date() == date_str or run.end_date_for_print() == date_str:
                        break
        elif 'Drain' in line_text:
            if self.water_year.drain_queue:
                run: DrainRun
                for run in self.water_year.drain_queue:
                    if run.start_date() == date_str or run.end_date_for_print() == date_str:
                        break
        elif 'Evap' in line_text:
            if self.water_year.evap_queue:
                run: EvapRun
                for run in self.water_year.evap_queue:
                    if run.start_date() == date_str or run.end_date_for_print() == date_str:
                        break

    def graph_api_data(self, variable_name:str, line_text:str):
        for source_name in self.water_year.source_names_api:
            source = None
            if source_name in line_text:
                if source_name == 'cdss':
                    source = self.water_year.inputs_cdss
                elif source_name == 'usgs':
                    source = self.water_year.inputs_usgs
                elif source_name == 'usbr':
                    source = self.water_year.inputs_usbr
                if source is not None:
                    ts = TimeSeries(variable_name, source_name, source)
                    x, y = ts.get_data()
                    text = ''
                    if x is not None and y is not None:
                        fmt = WaterYearInfo.format_float
                        for day, x in enumerate(x):
                            dt = WaterYearInfo.format_to_month_day(x)
                            text += f'\'{dt}\' {y[day]:{fmt}}\n'
                    graphic_panel = self.ui_abstraction.plot_time_series(self.water_year.sources, [ts], text=text)
                    if graphic_panel.python_text_view is not None:
                        graphic_panel.python_text_view.editor.on_styled_text_clicked = self.handle_click
                    return True
        return False

    def custom_data_as_text(self, variable_name:str)->str:
        text = ''
        custom_data = self.water_year.custom_data[variable_name]
        equations = self.water_year.equations[variable_name]
        dates = self.water_year.calc['DATE']
        fmt = WaterYearInfo.format_float
        for day, value in enumerate(custom_data):
            if value is not None:
                text += f"'{WaterYearInfo.format_to_month_day(dates[day])}' {value:{fmt}}\n"
                equation = equations[day]
                if equation is not None:
                    text += f'\t{equation}'
                text += f'\n'
        return text

    def verification_graph(self, graph_variable_name)->bool:
        for verification_error in self.water_year.verification_errors:
            variables = verification_error[0]
            if graph_variable_name is None or graph_variable_name == variables[0][2]:
                variable_name = variables[0][2]
                if MainFrame.select_tab_by_title(self.notebook, variable_name):
                    return True
                else:
                    text = verification_error[1]
                    if not text and variable_name in self.water_year.custom_data:
                        # Passed but with custom data
                        text = self.custom_data_as_text(variable_name)
                    if MainFrame.graph_verification_errors:
                        graphic_panel = self.ui_abstraction.plot_variable_from_source(variable_name, self.water_year.sources,
                                                                            self.water_year.units, variables, text)
                        if graphic_panel.python_text_view is not None:
                            graphic_panel.python_text_view.editor.on_styled_text_clicked = self.handle_click

                        wx.GetApp().Yield()
                        return True
        return False

    def post_process_task(self, report, file_name, done):
        if not self.batch:
            # dt = self.water_year.y['DATE']
            panel = wx.Panel(self.notebook)
            plot = GraphicPanel(panel, self.water_year.sources, self.water_year.units)
            self.notebook.AddPage(plot, "Graph")
            self.Show()
            wx.MilliSleep(10)
            wx.GetApp().Yield()

        # Uncomment if you want all failed verification tests to be graphed automatically
        # self.verification_graph(None)

        if report:
            self.build_report(report)
        self.progress.log_message(f'Accounting complete {file_name.name}')
        self.save_message_log()
        done.set()

        if not self.batch:
            self.global_config['current_file'] = str(file_name)
            with self.global_config_path.open("w") as file:
                json.dump(self.global_config, file, indent=4)

    def build_report(self, report):
        if report:
            for verify_error_graph  in self.verify_error_graphs:
                verify_error_graph.save_plot_to_image(report, f'sample_plot.png',
                                                      verify_error_graph.variable_name, verify_error_graph.text)
                self.progress.set_progress(72, f"  Verify failed {verify_error_graph.variable_name}")
                wx.GetApp().Yield()
            year_string = str(self.water_year.water_year_info.year)
            path = self.water_year.file_names['excel_error_log']
            path = Path(str(path).replace('YEAR', year_string))
            WaterYear.report_excel_row_index_errors(report, path)
            file_path = Path(self.water_year.file_names['report_doc'])
            report.save_doc(file_path)
            Report.open_docx_in_app(file_path)

    def save_message_log(self):
        path = self.water_year.file_names['message_log']
        year_string = str(self.water_year.water_year_info.year)
        path = Path(str(path).replace('YEAR', year_string))
        self.ui_abstraction.progress_bar.save(path)


class DoloresApp(wx.App):
    def __init__(self):
        super().__init__()
        self.frame = None

    @staticmethod
    def batch_loader(path):
        excel_files = WaterYear.get_file_list(path, '*.xlsx')
        paths = []
        for excel_file in excel_files:
            file_path = Path(excel_file[3])
            print(f'batch_loader_task', file_path)
            file_path = file_path.relative_to('data/Dolores')
            paths.append(Path(file_path))
        frame = MainFrame()
        frame.Run(paths, batch=True)

    def OnInit(self):
        batch = '--batch' in sys.argv or '-b' in sys.argv
        WaterYear.load_usbr_data = '--load_usbr' in sys.argv or '-lusbr' in sys.argv
        WaterYear.load_usgs_data = '--load_usgs' in sys.argv or '-lusgs' in sys.argv
        WaterYear.load_cdss_data = '--load_cdss' in sys.argv or '-lcdss' in sys.argv

        if batch:
            DoloresApp.batch_loader(Path('data/Dolores/Amended'))
        else:
            self.frame = MainFrame()
            file_chooser = FileChooser()
            path = file_chooser.show(self.frame, 'Excel files (*.xlsx)|*.xlsx', Path('data/Dolores/Amended'))
            wx.CallAfter(self.frame.Run, [path])
        return True  # Must return True to continue

    def OnExit(self):
        return super().OnExit()

if __name__ == "__main__":
    app = DoloresApp()
    app.MainLoop()
