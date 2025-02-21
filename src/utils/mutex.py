# src/utils/mutex.py
import sys
import win32event
import win32api
import winerror
from src.screens.errorWindow import ErrorWindow

_mutex_handle = None  # Global in the module

def create_mutex():
    global _mutex_handle  # Critical: Retain handle in the module's scope
    
    mutex_name = "Global\\UlendoHCAppMutex"
    try:
        # Use bInitialOwner=False for reliable error checking
        _mutex_handle = win32event.CreateMutex(None, False, mutex_name)
        last_error = win32api.GetLastError()
        
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            error_dialog = ErrorWindow(
                "Another instance is running",
                "Close the existing instance first."
            )
            sys.exit(1)  # Terminate here to prevent app initialization
        return _mutex_handle
    except Exception as e:
        raise e