import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys
import traceback
import webbrowser
import eel
from src.utils.io_utils import resource_path

class ActivationScreen:
    def __init__    (self, license, preload=True):
        self.license = license
        
        if preload and self.preload_license():
            self.root = None
            return
        
        self.root = tk.Tk()
        self.setup_ui()
        
    def setup_ui(self):
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.iconbitmap(resource_path("web/public/icon.ico"))
        # Configure the main window
        self.root.title("Ulendo HC (Heat Compensation) License Activation")
        self.root.configure(bg='#f0f0f0')
        self.center_window(450, 400)
        
        # Create main container with padding
        self.main_frame = tk.Frame(self.root, bg='#f0f0f0', padx=25, pady=25)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add logo section
        self.setup_logo()
        
        # Add title
        self.setup_title()
        
        # Add input section
        self.setup_input_section()
        
        # Add buttons
        self.setup_buttons()
        
        # Add window drag functionality
        self.setup_window_drag()
        
        self.root.focus_force() 
        
    def setup_window_drag(self):
        def start_move(event):
            self.root.x = event.x
            self.root.y = event.y

        def stop_move(event):
            self.root.x = None
            self.root.y = None

        def do_move(event):
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        self.main_frame.bind('<Button-1>', start_move)
        self.main_frame.bind('<ButtonRelease-1>', stop_move)
        self.main_frame.bind('<B1-Motion>', do_move)

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

    def setup_logo(self):
        logo_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        logo_frame.pack(fill=tk.X, pady=(0, 20))
        
        try:
            img_path = resource_path("web/public/ulendo_full_logo_no_bg.png")
            img = Image.open(img_path)
            # Calculate aspect ratio to maintain proportions
            aspect_ratio = img.width / img.height
            new_width = 280
            new_height = int(new_width / aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            label = tk.Label(logo_frame, image=self.photo, bg='#f0f0f0')
            label.pack()
        except Exception as e:
            print(f"Error loading logo: {e}")
            label = tk.Label(logo_frame, text="Ulendo", font=("Robotica", 24, "bold"), bg='#f0f0f0')
            label.pack()

    def setup_title(self):
        title_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame,
            text="License Activation",
            font=("Robotica", 16),
            bg='#f0f0f0'
        )
        title_label.pack()

    def setup_input_section(self):
        input_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # License key label
        key_label = tk.Label(
            input_frame,
            text="Enter your license key:",
            font=("Robotica", 10),
            bg='#f0f0f0'
        )
        key_label.pack(anchor='w', pady=(0, 5))
        
        # Custom styled text input
        self.input_text = tk.Text(
            input_frame,
            height=2,
            width=40,
            font=("Robotica", 10),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.input_text.pack(fill=tk.X, pady=(0, 5))
        
        # Error label
        self.error_label = tk.Label(
            input_frame,
            text="",
            fg="#d32f2f",
            bg='#f0f0f0',
            font=("Robotica", 10)
        )
        self.error_label.pack(fill=tk.X)

    def setup_buttons(self):
        button_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Activate button style
        activate_button = tk.Button(
            button_frame,
            text="Activate License",
            command=self.activate_app,
            bg='#2196f3',
            fg='white',
            font=("Robotica", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        activate_button.pack(side=tk.LEFT)
        
        # Get trial button style
        activate_button = tk.Button(
            button_frame,
            text="Request Trial",
            command=lambda: webbrowser.open("https://www.ulendo.io/hc-desktop-trial"),
            bg='#f0f0f0',
            fg='#0078D4',  # Changed to blue color
            font=("Robotica", 10, "underline"),  # Added underline
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            activeforeground='#005A9E'  # Darker blue when hovered
        )
        activate_button.pack(side=tk.LEFT)
        
        # Close button style
        close_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            bg='#f0f0f0',
            fg='#666666',
            font=("Robotica", 10),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        close_button.pack(side=tk.RIGHT)

    def preload_license(self):
        if not self.license:
            return False
        try:
            self.license.check_license_from_cloud()
            if self.license.activated:
                return self.license.activated
            return False
        except Exception as e:
            raise e
        
    def activate_app(self):
        self.error_label.config(text="")
        input_key = self.input_text.get("1.0", tk.END).strip()
        
        if len(input_key) < 10:
            self.error_label.config(text="Please enter a valid license key (minimum 10 characters)")
            return
        
        # Add loading state
        self.root.config(cursor="wait")
        self.root.update()
        
        self.license.set_license_key(input_key)
        
        try:
            self.license.activate_license_from_cloud()
            
            if self.license.activated:
                self.root.config(cursor="")
                self.destroy()
            else:
                self.error_label.config(text="Invalid license key. Please try again.")
                
        except Exception as e:
            self.error_label.config(text="An error occurred. Please try again.")
            raise e

    def run(self):
        if self.root:
            self.root.mainloop()

    def destroy(self):
        if self.root:
            self.root.update()
            self.root.destroy()
        
    def stop_app(self):
        sys.exit()