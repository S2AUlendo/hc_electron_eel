import sys
from src.screens.errorWindow import ErrorWindow

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