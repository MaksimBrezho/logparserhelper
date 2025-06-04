import tkinter as tk
from gui.app_window import AppWindow

def main():
    root = tk.Tk()
    root.title("LogParserHelper")
    root.geometry("1000x700")

    app = AppWindow(master=root)
    app.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
