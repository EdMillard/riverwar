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
import wx.stc as stc
import keyword  # For Python keywords

class StyledTextView(stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent, style=wx.BORDER_NONE|wx.HSCROLL)

        # Example: Style 10 = clickable green string
        # self.StyleSetSpec(6, "fore:#7FCE7F")  # blue underlined
        # self.SetMarginType(0, 0)  # no margins needed

        # Bind click (single or double — double is more intentional)
        # self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)          # single click
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnClick)     # or double click
        self.clickable_style = stc.STC_P_CHARACTER

    def OnClick(self, event):
        x, y = event.GetX(), event.GetY()
        pos = self.PositionFromPointClose(x, y)
        if pos == wx.NOT_FOUND:
            event.Skip()
            return

        style_at_click = self.GetStyleAt(pos)
        if style_at_click != self.clickable_style:
            event.Skip()
            return

        # Expand to full styled range (forward and backward)
        start = pos
        end = pos + 1

        # Go backward until style changes or beginning
        while start > 0 and self.GetStyleAt(start - 1) == self.clickable_style:
            start -= 1

        # Go forward until style changes or end
        total_len = self.GetLength()
        while end < total_len and self.GetStyleAt(end) == self.clickable_style:
            end += 1

        clicked_text = self.GetTextRange(start, end)
        text = clicked_text.strip()
        text = clicked_text.strip('\'"')

        # Find full line
        line_num = self.LineFromPosition(pos)
        line_start = self.PositionFromLine(line_num)
        line_end = self.GetLineEndPosition(line_num)
        line_text = self.GetTextRange(line_start, line_end)

        parent = self.GetParent()
        self.on_styled_text_clicked(text, start, end, line_text, parent=parent)

        # event.Skip()

    def on_styled_text_clicked(self, text:str, start_pos:int, end_pos:int, line_text:str, parent=None):
        """Override or bind to this"""
        print(f"Clicked on styled value: '{text}' at positions {start_pos}–{end_pos}")
        # wx.CallAfter(wx.MessageBox, f"You clicked: {text}", "Clickable Value")

class PythonTextView(wx.Panel):
    """A simple demo of wx.stc.StyledTextCtrl with Python syntax highlighting in dark mode (no line numbers)."""

    def __init__(self, parent):
        super().__init__(parent)

        # Create the StyledTextCtrl (Scintilla-based editor)
        #self.editor = stc.StyledTextCtrl(self)
        self.editor = StyledTextView(self)
        self.editor.on_styled_text_clicked = self.handle_click

        # Setup basic Python syntax highlighting in dark mode
        self.setup_python_highlighting()

        self.editor.SetText('')

        # Make it read-only for demo (remove for editing)1
        self.editor.SetReadOnly(False)  # Set to True for view-only

        # Turn off line number column (set width to 0)
        self.editor.SetMarginWidth(0, 0)  # Previously set to 50 for line numbers

        # Enable word wrap (optional)
        self.editor.SetWrapMode(stc.STC_WRAP_NONE)
        # self.editor.SetWrapMode(stc.STC_WRAP_WORD)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.editor, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Show()

    def handle_click(self, text:str, start:int, end:int, line_text:str, parent=None):
        wx.MessageBox(f'You clicked:\n{text} {start}-{end}\n{line_text}')

    def update_text(self, text):
        self.editor.SetText(text)
        self.editor.Colourise(0, -1)  # Re-apply syntax highlighting
        self.editor.ShowPosition(0)
        # Method 1 – The official, always-works way
        self.editor.SetScrollWidth(1)  # temporarily shrink
        self.editor.SetScrollWidth(-1)  # -1 = auto-track the longest line

        # Method 2 – Even shorter (my favorite)
        self.editor.SetScrollWidthTracking(True)


    def append_text(self, text):
        self.editor.AppendText(text)
        self.editor.Colourise(0, -1)  # Re-apply syntax highlighting
        self.editor.ShowPosition(0)
        self.editor.ShowPosition(self.editor.GetLastPosition())
        # Method 1 – The official, always-works way
        self.editor.SetScrollWidth(1)  # temporarily shrink
        self.editor.SetScrollWidth(-1)  # -1 = auto-track the longest line

        # Method 2 – Even shorter (my favorite)
        self.editor.SetScrollWidthTracking(True)

    def setup_python_highlighting(self):
        # mono_font = 'DejaVu Sans Mono'
        mono_font = 'Courier New'

        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                         faceName=mono_font)
        if not font.IsOk():
            print(f'styled text view mono font is not OK: {mono_font}')

        self.editor.StyleSetFont(stc.STC_STYLE_DEFAULT, font)
        self.editor.StyleClearAll()
        self.editor.StyleSetFont(stc.STC_P_WORD, font)

        """Configure styles for Python syntax in dark mode."""
        # Dark mode colors (high contrast, easy on eyes)
        faces = {
            'font': mono_font,
            'size': 11,
            'default': '#D4D4D4',  # Light gray text
            'background': '#1E1E1E',  # Dark background (Visual Studio-like)
            'comment': '#6A9955',  # Greenish comments
            'keyword': '#569CD6',  # Blue keywords
            'string': '#7FCE7F',  # Light green strings
            'number': '#CE9178',  # Orange-red numbers
            'operator': '#D4D4D4',  # Same as default
            'selection_bg': '#264F78',  # Selection background
            'caret': '#FFFFFF',  # White caret
            'margin_bg': '#252526',  # Margin background (still used for folding if enabled)
        }

        # Clear and set default style (background and foreground)
        # self.editor.StyleClearAll()
        self.editor.StyleSetSpec(stc.STC_STYLE_DEFAULT,
                                 f"face:{faces['font']},size:{faces['size']},fore:{faces['default']},back:{faces['background']}")
        self.editor.StyleSetBackground(stc.STC_STYLE_DEFAULT, faces['background'])
        self.editor.StyleSetForeground(stc.STC_STYLE_DEFAULT, faces['default'])

        # Apply to all styles
        self.editor.StyleSetBackground(stc.STC_STYLE_DEFAULT, faces['background'])

        # Python-specific styles (using STC_P_ constants)
        self.editor.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{faces['default']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_COMMENTLINE, f"fore:{faces['comment']},italic,back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_COMMENTBLOCK, f"fore:{faces['comment']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_NUMBER, f"fore:{faces['number']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_STRING, f"fore:{faces['string']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_CHARACTER, f"fore:{faces['string']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_WORD, f"fore:{faces['keyword']},bold,back:{faces['background']}")  # Keywords
        self.editor.StyleSetSpec(stc.STC_P_TRIPLE, f"fore:{faces['string']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, f"fore:{faces['string']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_CLASSNAME, f"fore:{faces['keyword']},bold,back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_DEFNAME, f"fore:{faces['keyword']},bold,back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_OPERATOR, f"fore:{faces['operator']},bold,back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_IDENTIFIER, f"fore:{faces['default']},back:{faces['background']}")
        self.editor.StyleSetSpec(stc.STC_P_DECORATOR, f"fore:#FF8000,back:{faces['background']}")  # Orange decorators

        # Line number margin styling (still configured but width=0 hides it)
        self.editor.StyleSetBackground(stc.STC_STYLE_LINENUMBER, faces['margin_bg'])
        self.editor.StyleSetForeground(stc.STC_STYLE_LINENUMBER, '#858585')

        # Selection and caret
        self.editor.SetSelBackground(True, faces['selection_bg'])
        self.editor.SetCaretForeground(faces['caret'])

        # Set lexer to Python
        self.editor.SetLexer(stc.STC_LEX_PYTHON)

        # Define Python keywords
        python_keywords = " ".join(keyword.kwlist) + " print exec"
        self.editor.SetKeyWords(0, python_keywords)

        # Enable code folding with dark symbols (kept, but margin 1 still visible if needed)
        self.editor.SetProperty("fold", "1")
        self.editor.SetMarginType(1, stc.STC_MARGIN_SYMBOL)
        self.editor.SetMarginMask(1, stc.STC_MASK_FOLDERS)
        self.editor.SetMarginSensitive(1, True)
        self.editor.SetMarginWidth(1, 20)
        self.editor.StyleSetBackground(1, faces['margin_bg'])  # Folding margin bg

        # Folding symbols (inverted colors for dark mode)
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_MINUS, faces['background'], "#007ACC")
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_PLUS, faces['background'], "#007ACC")
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_EMPTY, faces['background'], "#007ACC")
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_EMPTY, faces['background'], "#007ACC")
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_PLUS, faces['background'], "#007ACC")
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_MINUS, faces['background'], "#007ACC")
        self.editor.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY, faces['background'], "#007ACC")


if __name__ == "__main__":
    app = wx.App(False)
    demo = SyntaxHighlightDemo()
    app.MainLoop()