import os
import tkinter as tk


def get_icon_path() -> str:
    """Return the absolute path to the application icon."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon", "ALLtoCEF.ico")


def set_window_icon(window: tk.Misc) -> None:
    """Apply the application icon to the given Tkinter window."""
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        try:
            window.iconbitmap(icon_path)
        except Exception:
            pass
