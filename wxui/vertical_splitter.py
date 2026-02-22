import wx

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Progressive Bottom-Split Splitter", size=(1000, 700))

        # Main vertical splitter: left (static) | right (dynamic)
        self.main_splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.main_splitter.SetMinimumPaneSize(150)

        # Left panel
        left = wx.Panel(self.main_splitter)
        left.SetBackgroundColour("#e0e8ff")
        wx.StaticText(left, label="Left Panel", pos=(20,20)).SetFont(wx.Font(16, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.AddStretchSpacer()
        left_sizer.Add(wx.StaticText(left, label="Left Panel\n(fixed)"), 0, wx.CENTER)
        left_sizer.AddStretchSpacer()
        left.SetSizer(left_sizer)

        # Right container
        self.right_container = wx.Panel(self.main_splitter)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_container.SetSizer(self.right_sizer)

        self.main_splitter.SplitVertically(left, self.right_container, 300)

        # Toolbar
        tb = self.CreateToolBar()
        add_tool = tb.AddTool(wx.ID_ANY, "Add Panel (split bottom)",
                              wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR, (32,32)),
                              "Split the bottom pane in half")
        tb.Realize()
        self.Bind(wx.EVT_TOOL, self.OnAddPanel, add_tool)

        # Frame sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.main_splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # State
        self.panel_counter = 0
        self.current_splitter = None  # The splitter we will split next (always the bottom one)

        # Create first panel (full height)
        self.OnAddPanel(None)

    def CreatePanel(self, parent):
        self.panel_counter += 1
        color = wx.Colour(200 + self.panel_counter*15, 230, 200 + self.panel_counter*18)
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(color)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(panel, label=f"Panel #{self.panel_counter}",
                                style=wx.ALIGN_CENTER),
                  1, wx.EXPAND | wx.ALL, 20)
        panel.SetSizer(sizer)
        return panel

    def OnAddPanel(self, event):
        new_panel = self.CreatePanel(self.right_container)

        if self.panel_counter == 1:
            # First panel → create main right splitter
            self.current_splitter = wx.SplitterWindow(self.right_container, style=wx.SP_LIVE_UPDATE)
            self.current_splitter.SetMinimumPaneSize(60)
            self.current_splitter.SetSashGravity(0.5)

            new_panel.Reparent(self.current_splitter)
            dummy = wx.Panel(self.current_splitter)  # bottom will be empty for now
            dummy.Hide()  # hide dummy

            self.current_splitter.SplitHorizontally(new_panel, dummy)
            self.right_sizer.Add(self.current_splitter, 1, wx.EXPAND | wx.ALL, 5)

        else:
            # All subsequent panels → split the current bottom pane
            bottom_win = self.current_splitter.GetWindow2()
            if bottom_win.IsShown():
                # Bottom already has a panel → create nested splitter
                nested = wx.SplitterWindow(self.current_splitter, style=wx.SP_LIVE_UPDATE)
                nested.SetMinimumPaneSize(60)
                nested.SetSashGravity(0.5)

                # Move old bottom panel into nested splitter (top)
                old_bottom = bottom_win
                old_bottom.Reparent(nested)

                # New panel goes to bottom of nested
                new_panel.Reparent(nested)

                nested.SplitHorizontally(old_bottom, new_panel)
                nested.SetSashPosition(nested.GetSize().height // 2)

                # Replace the old bottom with the new nested splitter
                self.current_splitter.ReplaceWindow(bottom_win, nested)
                bottom_win.Destroy()

                # Update current splitter to the new nested one
                self.current_splitter = nested

            else:
                # Bottom was dummy → replace it with real panel and split 50/50
                new_panel.Reparent(self.current_splitter)
                self.current_splitter.ReplaceWindow(bottom_win, new_panel)
                bottom_win.Destroy()
                self.current_splitter.SetSashPosition(self.current_splitter.GetSize().height // 2)
                self.current_splitter.GetWindow2().Show()

        if not self.main_splitter.IsSplit():
            self.main_splitter.SplitVertically(
                self.main_splitter.GetWindow1(), self.right_container, 300)

        self.right_sizer.Layout()
        self.Layout()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()