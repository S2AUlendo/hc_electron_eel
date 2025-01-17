import tkinter as tk
from tkinter import ttk
import sys
import os

def resource_path(rel_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
class SingleInstanceScreen:
    def __init__(self):
        self.root = tk.Tk()
        
        # Set the window title and dimensions
        self.root.title("App Already Running")
        self.root.iconbitmap(resource_path("web/public/icon.ico"))
        
        width = 300
        height = 250
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

        # Configure window
        self.root.configure(bg='white')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for the message
        top_frame = tk.Frame(main_frame, bg='white')
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title label
        title_label = tk.Label(
            top_frame,
            text="An instance of the app is already running.",
            font=("Roboto", 12),
            bg='white',
            wraplength=250,
            justify="center"
        )
        title_label.pack(pady=10)
        
        # Bottom frame for the button
        bottom_frame = tk.Frame(main_frame, bg='white')
        bottom_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # OK button
        ok_button = ttk.Button(
            bottom_frame,
            text="OK",
            command=self.destroy  # Call the destroy method to close the window
        )
        ok_button.pack(pady=10)
        
    def destroy(self):
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()