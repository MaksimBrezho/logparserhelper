
import tkinter as tk
from utils.window_utils import set_window_icon


class ToolTip:
    def __init__(self, widget, delay=500):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.delay = delay

    def showtip(self, text, x, y):
        if self.tipwindow or not text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        set_window_icon(tw)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x+10}+{y+10}")
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None

    def schedule(self, text, x, y):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip, text, x, y)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
        self.hidetip()
