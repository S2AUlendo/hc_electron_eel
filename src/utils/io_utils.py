import os
import sys
from src.screens.errorWindow import ErrorWindow

def persistent_path(rel_path):
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, rel_path)

def resource_path(rel_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

def get_data_dir():
    data_dir = persistent_path("data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def get_persistent_output_dir():
    output_dir = persistent_path("output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def create_mutex():
    """Create a Windows mutex to ensure single instance"""
    import win32event
    import win32api
    import winerror
    
    mutex_name = "Global\\UlendoHCAppMutex"  # Choose a unique name
    try:
        handle = win32event.CreateMutex(None, 1, mutex_name)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            error_screen = ErrorWindow(
                "Another instance is already running",
                "Please close the existing Heat Compensation application before starting a new one."
            )
            sys.exit(1)
        return handle
    except Exception as e:
        raise e