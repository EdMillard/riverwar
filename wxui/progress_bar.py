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
from wxui.python_text_view import PythonTextView
import wx

class ProgressBar(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.show_time = False
        self.messages = []

        # --- Widgets ---
        self.gauge = wx.Gauge(self, range=100, size=wx.Size(300, 25))
        self.log = PythonTextView(self)
        # self.log = wx.TextCtrl(
        #    self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
        #    size=wx.Size(300, 150)
        #)

        # --- Layout ---
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.gauge, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(sizer)

        # Start at 0
        self.gauge.SetValue(0)
        self.Show()

    # --- Public Methods ---
    def set_progress(self, value: int, message: str = ""):
        """
        Update progress bar (0–100) and optionally log a message.
        """
        if not (0 <= value <= 100):
            raise ValueError("Progress value must be between 0 and 100")
        self.gauge.SetValue(value)
        if message:
            self.log_message(message)

    def log_message(self, message: str):
        """
        Append a message to the log with timestamp.
        """
        import time
        self.messages.append(message)
        if self.show_time:
            timestamp = time.strftime("%H:%M:%S")
            self.log.append_text( f"[{timestamp}] {message}\n")
        else:
            self.log.append_text( f"{message}\n")

    def reset(self):
        self.gauge.SetValue(0)
        # self.log.Clear()
        self.messages.clear()

    def save(self, path):
        with open(path, "w") as file:
            for message in self.messages:
                file.write(f'{message}\n')
        self.messages.clear()

