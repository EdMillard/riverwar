import wx

class SplitterFrame(wx.Frame):
    def __init__(self, panel_factory_list):
        """
        panel_factory_list: list of 3 callables that return a panel when called with (parent)
                            e.g. [lambda p: MyPanel(p, "Top"), ...]
        """
        super().__init__(None, title="25% | 25% | 50% Vertical Splitter", size=(800, 600))

        # Main splitter (left 50% vs right 50%)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)

        # === LEFT SIDE (50% total): contains two 25% panels ===
        self.left_container = wx.Panel(self.splitter)

        # Nested splitter inside left_container
        self.nested_splitter = wx.SplitterWindow(self.left_container, style=wx.SP_LIVE_UPDATE)

        # Create the three panels with proper parents
        self.panel_top    = panel_factory_list[0](self.nested_splitter)  # 25%
        self.panel_middle = panel_factory_list[1](self.nested_splitter)  # 25%
        self.panel_right  = panel_factory_list[2](self.splitter)         # 50%

        # --- Layout nested splitter (25% / 25%) ---
        self.nested_splitter.SplitHorizontally(self.panel_top, self.panel_middle)

        # Layout left_container to hold nested splitter
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.nested_splitter, 1, wx.EXPAND)
        self.left_container.SetSizer(left_sizer)

        # --- Main splitter: left (50%) vs right (50%) ---
        self.splitter.SplitVertically(self.left_container, self.panel_right)

        # --- Set sash positions after layout ---
        wx.CallAfter(self._set_sash_positions)

        # Main frame sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

    def _set_sash_positions(self):
        # Main splitter: 50% width
        width = self.splitter.GetSize().width
        self.splitter.SetSashPosition(width // 2)

        # Nested splitter: 50% of its height → 25% of total
        height = self.nested_splitter.GetSize().height
        self.nested_splitter.SetSashPosition(height // 2)


# ----------------------------------------------------------------------
# Example: Define your three panels as functions that take a parent
# ----------------------------------------------------------------------
def create_panel1(parent):
    panel = wx.Panel(parent)
    panel.SetBackgroundColour(wx.Colour(255, 200, 200))
    wx.StaticText(panel, label="Panel 1 (25%)", pos=(10, 10))
    return panel

def create_panel2(parent):
    panel = wx.Panel(parent)
    panel.SetBackgroundColour(wx.Colour(200, 255, 200))
    wx.StaticText(panel, label="Panel 2 (25%)", pos=(10, 10))
    return panel

def create_panel3(parent):
    panel = wx.Panel(parent)
    panel.SetBackgroundColour(wx.Colour(200, 200, 255))
    wx.StaticText(panel, label="Panel 3 (50%)", pos=(10, 10))
    return panel


# ----------------------------------------------------------------------
# Run the app
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)

    # Pass a list of factory functions
    frame = SplitterFrame([create_panel1, create_panel2, create_panel3])
    frame.Show()

    app.MainLoop()

    app.MainLoop()