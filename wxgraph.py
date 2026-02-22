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
import wx.dataview as dv
import json
import pandas as pd
from pathlib import Path
import plyvel
from wxui.graphic_panel import GraphicPanel

class YearSelectorPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        # FIXME - dependence on WaterYear is undesirable
        # db_path = Path(WaterYear.global_file_names['dolores_all_data_db'])
        db_path = Path('cache/Dolores/Amended/dolores_all_data_db')
        try:
            self.db = plyvel.DB(str(db_path), create_if_missing=False)
        except plyvel.IOError as e:
            print(f"Error opening database: {db_path} {e}")
        except Exception as e:
            print(f"Unexpected database error: {db_path} {e}")

        self.sources = {}
        self.variables = {}
        self.years = []
        self.load_all_years()
        # self.load_year('1986')
        splitter = wx.SplitterWindow(self)

        # ===================== LEFT PANEL =====================
        left = wx.Panel(splitter)
        sizer = wx.BoxSizer(wx.VERTICAL)

        info = wx.StaticText(left, label="Years")
        info.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD))
        sizer.Add(info, 0, wx.ALL, 10)

        self.dlc = dv.DataViewListCtrl(left,
            style=dv.DV_ROW_LINES | dv.DV_VERT_RULES | dv.DV_MULTIPLE)

        self.dlc.AppendTextColumn("Year",  mode=dv.DATAVIEW_CELL_ACTIVATABLE, width=280)

        self.dlc.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        sizer.Add(self.dlc, 1, wx.EXPAND | wx.ALL, 10)
        left.SetSizer(sizer)

        # ===================== POPULATE =====================
        for year in self.years:
            self.dlc.AppendItem([year])

        # ===================== RIGHT PANEL =====================
        right = wx.Panel(splitter)
        # left = wx.Panel(splitter)

        right_sizer = wx.BoxSizer(wx.VERTICAL)
        units = ''
        self.graphic_panel = GraphicPanel(right, self.sources, units, None)

        right_sizer.Add(self.graphic_panel, 1, wx.EXPAND | wx.ALL, 10)
        right.SetSizer(right_sizer)

        splitter.SplitVertically(left, right, 100)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        self.dlc.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectionChanged)

        self.ShowSelected()

    def __del__(self):
        if self.db:
            self.db.close()

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        current_row = self.dlc.GetSelectedRow()
        row_count = self.dlc.GetItemCount()

        if keycode == wx.WXK_UP:  # Up arrow
            if current_row > 0:
                new_row = current_row - 1
            else:
                new_row = row_count - 1  # wrap to bottom (optional)
            self.select_row(new_row)
        elif keycode == wx.WXK_DOWN:  # Down arrow
            if current_row < row_count - 1:
                new_row = current_row + 1
            else:
                new_row = 0  # wrap to top (optional)
            self.select_row(new_row)
        else:
            # Let other keys (Enter, letters, etc.) be handled normally
            event.Skip()

    def select_row(self, row):
        self.dlc.UnselectAll()
        self.dlc.SelectRow(row)
        self.dlc.SetFocus()  # keep keyboard focus
        # Optional: scroll the row into view
        self.dlc.EnsureVisible(self.dlc.RowToItem(row))

        # Do whatever you need with the selected row here
        year = self.dlc.GetTextValue(row, 0)
        print(f"Selected: {year}")
        self.graphic_panel.source_change(year, set_source_control=True)

    def OnSelectionChanged(self, event):
        self.ShowSelected()
        if event:
            event.Skip()

    def ShowSelected(self):
        selections = self.dlc.GetSelections()
        text = ''
        if len(selections) == 1:
            year = self.dlc.GetModel().GetValue(selections[0], 0)
            self.graphic_panel.source_change(year, set_source_control=True)
            # self.select_row(row)
        else:
            years = []
            for selection in selections:
                year = self.dlc.GetModel().GetValue(selection, 0)
                years.append(year)
            self.graphic_panel.sources_change(years, set_source_control=True)

    def load_year(self, year):
        values = self.db.get(year.encode('utf-8'))
        print(f'Loading {year}')
        self.years.append(year)
        json_str = values.decode('utf-8')
        variables = json.loads(json_str)
        dates = variables.get('DATE')
        if dates:
            date_times = []
            for date_str in dates:
                dt = pd.to_datetime(date_str)
                date_times.append(dt)
            variables['DATE'] = date_times

        self.variables[year] = variables
        self.sources[year] = self.variables[year]

    def load_all_years(self):
        self.sources = {}
        self.variables = {}
        self.years = []
        for key in self.db.iterator(reverse=True, include_value=False):
            year = key.decode('utf-8')
            self.load_year(year)

    @staticmethod
    def get_all_keys(db):
            keys = []
            for key in db.iterator(reverse=True, include_value=False):
                # Keys and values are bytes, decode if they're UTF-8 text
                try:
                    key_str = key.decode('utf-8')
                except UnicodeDecodeError:
                    key_str = key.hex()  # fallback to hex if not valid UTF-8
                keys.append(key_str)
            return keys

if __name__ == "__main__":
    app = wx.App(False)
    w, h = wx.GetClientDisplayRect().GetSize()
    h = int(h / 2)
    frame = wx.Frame(None, title="Dolores Project", pos=wx.Point(10, 64), size=wx.Size(w-20, h))
    YearSelectorPanel(frame)
    frame.Show()
    app.MainLoop()