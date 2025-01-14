import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import os
import sys

def resource_path(rel_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size and position
        width = 420
        height = 300
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        
        # Configure window
        self.root.configure(bg='white')
        self.root.attributes('-topmost', True)
        
        # Add logo/image
        try:
            img_path = resource_path("web/public/ulendo_full_logo_no_bg.png")
            img = Image.open(img_path)
            img = img.resize((280, 80))
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(self.root, image=photo, bg='white')
            label.image = photo
            label.pack(pady=20)
        except:
            pass
        
        # Add title
        title = tk.Label(self.root, text="Heat Compensation", font=("Helvetica", 16), bg='white')
        title.pack(pady=10)
        
        # Add progress bar
        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=20)
        
    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update()
        
    def destroy(self):
        self.root.destroy()