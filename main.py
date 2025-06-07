import tkinter as tk
from gui.app_window import AppWindow
import os

def main():
    root = tk.Tk()
    root.title("LogParserHelper")
    root.geometry("1000x700")

    icon_path = os.path.join(os.path.dirname(__file__), "icon", "ALLtoCEF.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    app = AppWindow(master=root)
    app.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
