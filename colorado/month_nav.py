"""
Copyright (c) 2025 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in

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
from datetime import date
import wx.lib.buttons as buttons
from colorado.chart import Chart

arrow_fg = wx.Colour(150, 150, 150)

class MonthYearNavigator(wx.Panel):
    """Reusable single month/year navigator with smaller raised buttons"""
    def __init__(self, parent:wx.Panel, current_date:date, on_changed=None, name:str=""):
        super().__init__(parent, style=wx.BORDER_NONE)

        self.name = name
        self.current_date = current_date
        self.on_changed = on_changed

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)

        self.btn_left = buttons.GenButton(self, label="◀", size=wx.Size(34, 32))
        self.btn_left.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_left.SetForegroundColour(arrow_fg)
        self.btn_left.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.btn_left.SetBezelWidth(3)
        self.btn_left.SetUseFocusIndicator(False)
        self.btn_left.Bind(wx.EVT_BUTTON, self._on_left)
        sizer.Add(self.btn_left, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)

        self.date_text = wx.StaticText(self, label="")
        self.date_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.date_text.SetForegroundColour(wx.Colour(230, 230, 230))
        sizer.Add(self.date_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=12)

        self.btn_right = buttons.GenButton(self, label="▶", size=wx.Size(34, 32))
        self.btn_right.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.btn_right.SetForegroundColour(arrow_fg)
        self.btn_right.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.btn_right.SetBezelWidth(3)
        self.btn_right.SetUseFocusIndicator(False)
        self.btn_right.Bind(wx.EVT_BUTTON, self._on_right)
        sizer.Add(self.btn_right, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=6)

        self.SetSizer(sizer)
        self.SetBackgroundColour(bg)
        self._update_display()

    def _update_display(self):
        self.date_text.SetLabel(Chart.date_to_string(self.current_date))

    def _on_left(self, event):
        month = self.current_date.month - 1
        year = self.current_date.year
        if month < 1:
            month = 12
            year -= 1
        self.current_date = date(year, month, 1)
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_date)

    def _on_right(self, event):
        month = self.current_date.month + 1
        year = self.current_date.year
        if month > 12:
            month = 1
            year += 1
        self.current_date = date(year, month, 1)
        self._update_display()
        if self.on_changed:
            self.on_changed(self.name, self.current_date)

