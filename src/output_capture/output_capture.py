
import sys
import threading
import io
import queue
import eel

class OutputCapture:
    def __init__(self):
        self.output_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
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
        
        # Start output monitoring thread
        threading.Thread(target=self._monitor_output, daemon=True).start()
    
    def _monitor_output(self):
        while True:
            try:
                output = self.output_queue.get()
                # Send captured output to frontend
                if output:
                    eel.update_terminal_output(output)
            except Exception as e:
                print(f"Error in output monitoring: {e}")
    
    def restore(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
