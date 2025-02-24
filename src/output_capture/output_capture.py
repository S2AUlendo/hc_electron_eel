
import sys
import threading
import io
import queue
import time
import eel
import logging
from multiprocessing import Manager, Event
import atexit

class OutputCapture:
    def __init__(self):
        self.output_queue = queue.Queue()
        self._manager = Manager()
        self.mp_output_queue = self._manager.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self._monitor_running = threading.Event()
        self.shutdown_event = Event()
        atexit.register(self.cleanup)
    
    def start_capture(self):
        # Create custom stdout that both prints and captures
        class CustomOutput(io.StringIO):
            def __init__(self, queue, original_stdout):
                super().__init__()
                self.queue = queue
                self.original_stdout = original_stdout
            
            def write(self, text):
                if self.original_stdout:
                    self.original_stdout.write(text)
                self.queue.put(text)
                
            def flush(self):
                if self.original_stdout:
                    self.original_stdout.flush()
                
            def fileno(self):
                if hasattr(self.original_stdout, 'fileno'):
                    return self.original_stdout.fileno()
                # TODO: this is a bypass, please fix in the future
                return 1
        
        # Replace sys.stdout with our custom output
        sys.stdout = CustomOutput(self.output_queue, self.original_stdout)
        sys.stderr = CustomOutput(self.output_queue, self.original_stderr)
        
        self._monitor_running.set()  # <-- Start monitoring
        threading.Thread(target=self._monitor_output, daemon=True).start()
        
    def _monitor_output(self):
        while True and not self.shutdown_event.is_set():
            try:
                # Process all messages from the multiprocessing queue first
                while not self.mp_output_queue.empty():
                    output_mp = self.mp_output_queue.get_nowait()
                    if output_mp:
                        eel.update_terminal_output(output_mp)

                # Process all messages from the standard output queue
                while not self.output_queue.empty():
                    output_std = self.output_queue.get_nowait()
                    if output_std:
                        eel.update_terminal_output(output_std)

                # Short sleep to prevent busy-waiting
                time.sleep(0.1)

            except Exception as e:
                print(f"Error in output monitoring: {e}")
    
    def restore(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def cleanup(self):
        print("Cleaning up output capture...")
        self.shutdown_event.set()

        self.restore()
        self._monitor_running.clear()