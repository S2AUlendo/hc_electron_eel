import sys
import traceback
from src.core.heat_compensation_app import HeatCompensationApp
from src.screens.errorWindow import ErrorWindow
from src.utils.mutex import create_mutex  # Implement create_mutex in io_utils.py

if __name__ == '__main__':
    try:
        from multiprocessing import freeze_support
        freeze_support()
        
        create_mutex()  # Windows mutex check
        app = HeatCompensationApp()
        print("Starting app")
        app.start()
    except Exception as e:
        ErrorWindow(str(e), traceback.format_exc())
        sys.exit(1)