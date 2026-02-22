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
import re
import os

class FileChooser():
    def __init__(self):
        pass

    def show(self, parent, file_filter, dir):
        if file_filter is None or not file_filter:
            file_filter = "All files (*.*)|*.*|Text files (*.txt)|*.txt"
        with wx.FileDialog(
                parent,
                "Open file",
                defaultDir=str(dir),
                wildcard=file_filter,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return None

            path = file_dialog.GetPath()
            print(f"Selected file: {path}")
            # wx.MessageBox(f"You selected:\n{path}", "File Chosen", wx.OK | wx.ICON_INFORMATION)

            return path

class CustomFileDialog(wx.Dialog):
    def __init__(self, parent, message, defaultDir="", defaultFile="", wildcard="*"):
        super().__init__(parent, title=message, size=wx.Size(768, 768))

        self.selected_path = ""
        self.file_paths = []  # To map index -> full path

        self.wildcard = wildcard
        self.wildcard_regex = self._compile_wildcard_regex(wildcard)

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Path display
        self.path_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        sizer.Add(self.path_text, 0, wx.EXPAND | wx.ALL, 5)

        # List control
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "Name", width=350)
        self.list_ctrl.InsertColumn(1, "Size", width=100)
        self.list_ctrl.InsertColumn(2, "Modified", width=240)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Open")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        panel.SetSizer(sizer)

        # Bindings
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate)
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_btn)

        # Load files
        self.current_dir = defaultDir or os.getcwd()
        self.wildcard = wildcard
        self.load_directory(self.current_dir)

    def load_directory(self, path):
        self.current_dir = path
        self.path_text.SetValue(path)
        self.list_ctrl.DeleteAllItems()
        self.file_paths = []

        try:
            entries = os.listdir(path)
            files = []
            for entry in entries:
                full_path = os.path.join(path, entry)
                if os.path.isfile(full_path):
                    # Wildcard filtering
                    # if self.wildcard == "*" or any(entry.lower().endswith(ext.strip().lower().lstrip("*."))
                    #                               for ext in self.wildcard.split(";") if ext.strip()):
                    if self.wildcard_regex and not self.wildcard_regex.search(entry):
                        continue
                    size = os.path.getsize(full_path)
                    mtime = os.path.getmtime(full_path)
                    dt = wx.DateTime.FromTimeT(int(mtime))  # Fixed line
                    modified = dt.Format("%Y-%m-%d %H:%M")
                    files.append((entry, size, modified, full_path))

            # Sort reverse alphabetical (case-insensitive)
            files.sort(key=lambda x: x[0].lower(), reverse=True)

            for i, (name, size, modified, full_path) in enumerate(files):
                idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), name)
                self.list_ctrl.SetItem(idx, 1, f"{size:,} B")
                self.list_ctrl.SetItem(idx, 2, modified)
                self.list_ctrl.SetItemData(idx, i)
                self.file_paths.append(full_path)

        except Exception as e:
            wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def on_select(self, event):
        idx = event.GetIndex()
        data_idx = self.list_ctrl.GetItemData(idx)
        if 0 <= data_idx < len(self.file_paths):
            self.selected_path = self.file_paths[data_idx]

    def on_activate(self, event):
        self.on_select(event)
        if self.selected_path:
            self.EndModal(wx.ID_OK)

    def on_ok(self, event):
        if self.selected_path:
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("Please select a file.", "No selection", wx.OK | wx.ICON_WARNING)

    def GetPath(self):
        return self.selected_path

    def _compile_wildcard_regex(self, wildcard):
        """
        Convert "*.xls;*.xlsx" → regex that matches any of those extensions (case-insensitive)
        Returns compiled regex or None if wildcard == "*"
        """
        if not wildcard or wildcard.strip() == "*":
            return None  # match all

        patterns = []
        for part in wildcard.split(";"):
            part = part.strip()
            if not part:
                continue
            # Convert *.ext → \.ext$  (literal dot, end of string)
            esc = re.escape(part.replace("*", ""))  # escape . in case of weird chars
            esc = esc.replace(r"\.", ".")  # unescape the dot
            pattern = esc + "$"  # must end with extension
            patterns.append(pattern)

        if not patterns:
            return None

        combined = "|".join(patterns)
        return re.compile(combined, re.IGNORECASE)

def main():
    app = wx.App()
    dlg = CustomFileDialog(None, "Choose a file", wildcard="*.xlsx;*.xls", defaultDir="/opt/dev/riverwar/data/Dolores")
    if dlg.ShowModal() == wx.ID_OK:
        print("Selected:", dlg.GetPath())
    dlg.Destroy()
    app.MainLoop()

if __name__ == "__main__":
    main()