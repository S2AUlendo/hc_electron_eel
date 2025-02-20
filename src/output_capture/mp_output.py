class CustomMPOutput:
        def __init__(self, queue):
            self.queue = queue

        def write(self, text):
            self.queue.put(text)

        def flush(self):
            pass

        # Add these to satisfy TextIOWrapper requirements
        def readable(self):
            return False

        def writable(self):
            return True

        def seekable(self):
            return False