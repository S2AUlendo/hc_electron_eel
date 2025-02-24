import tkinter as tk
from tkinter import ttk
from src.utils.io_utils import resource_path
        
class ErrorWindow:
    def __init__(self, error_message, traceback_info):
        self.error_window = tk.Tk()
        self.error_message = error_message
        self.traceback_info = traceback_info
        self.setup_error_window()
        
    def setup_error_window(self):
        self.error_window.iconbitmap(resource_path("web/public/icon.ico"))
        self.error_window.title("Error")
        self.error_window.geometry("600x400")
        self.error_window.configure(bg='white')
        self.error_window.attributes('-topmost', True)
        self.error_window.bind('<Escape>', lambda e: self.error_window.destroy())
        
        # Center window
        screen_width = self.error_window.winfo_screenwidth()
        screen_height = self.error_window.winfo_screenheight()
        x = (screen_width / 2) - (600 / 2)
        y = (screen_height / 2) - (400 / 2)
        self.error_window.geometry(f'+{int(x)}+{int(y)}')
        
        # Error icon and message
        frame = tk.Frame(self.error_window, bg='white', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        header = tk.Label(
            frame, 
            text="An error has occurred", 
            font=("Helvetica", 16, "bold"),
            bg='white'
        )
        header.pack(pady=(0,10))
        
        message = tk.Label(
            frame,
            text=str(self.error_message),
            font=("Helvetica", 10),
            bg='white',
            wraplength=550
        )
        message.pack(pady=(0,20))
        
        # Traceback in scrolled text with scrollbar
        trace_frame = tk.Frame(frame, bg='white')
        trace_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(trace_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        trace_text = tk.Text(
            trace_frame,
            height=10,
            font=("Courier", 8),
            bg='#f0f0f0',
            yscrollcommand=scrollbar.set
        )
        trace_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=trace_text.yview)
        
        trace_text.insert(tk.END, self.traceback_info)
        trace_text.config(state='disabled')  # Make read-only
        
        close_button = tk.Button(
            frame,
            text="Close",
            command=self.error_window.destroy,
            bg='#d32f2f',
            fg='white',
            font=("Helvetica", 10),
            padx=20,
            pady=5
        )
        close_button.pack(pady=(20,0))
        
        self.error_window.focus_force()  # Force focus
        self.error_window.mainloop()