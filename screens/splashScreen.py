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
        self.root.overrideredirect(True)
        # self.root.attributes('-alpha', 0.95)  # Slight transparency
        
        # Window dimensions
        width = 400
        height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        
        # Configure window
        self.root.configure(bg='white')
        
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for logo and title
        top_frame = tk.Frame(main_frame, bg='white')
        top_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Load and display logo
        try:
            img_path = resource_path("web/public/ulendo_full_logo_no_bg.png")
            img = Image.open(img_path)
            img = img.resize((310, 90))
            self.photo = ImageTk.PhotoImage(img)
            label = tk.Label(top_frame, image=self.photo, bg='white')
            label.pack(pady=(20,10))
        except Exception as e:
            print(f"Error loading splash image: {e}")
            
        # Add title
        title = tk.Label(top_frame, text="Heat Compensation", 
                        font=("Helvetica", 16, "bold"), bg='white')
        title.pack()
        
        # Style for progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Custom.Horizontal.TProgressbar",
                       thickness=10,
                       troughcolor='#E0E0E0',
                       background='#4CAF50',
                       borderwidth=0,
                       lightcolor='#4CAF50',
                       darkcolor='#4CAF50')
        
        # Bottom frame for progress bar
        bottom_frame = tk.Frame(main_frame, bg='white')
        bottom_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # Progress bar
        self.progress = tk.Label(bottom_frame, text="Starting up...", 
                        font=("Helvetica", 8), bg='white')
        self.progress.pack()
        
        self.root.focus_force() 
        
    def update_progress(self, value):
        self.progress['text'] = value
        self.root.update()
        
    def destroy(self):
        self.root.destroy()