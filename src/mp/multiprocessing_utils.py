# multiprocessing_utils.py
from multiprocessing import Manager

_initialized = False
_manager = None
_pool = None

def initialize_multiprocessing():
    global _initialized, _manager, _pool
    if not _initialized:
        _manager = Manager()
        _pool = NestablePool(processes=4)
        _initialized = True
    return _manager, _pool

def get_pool():
    return _pool

def get_manager():
    return _manager

import multiprocessing.pool

class NoDaemonProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class NoDaemonContext(type(multiprocessing.get_context())):
    Process = NoDaemonProcess

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class NestablePool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(NestablePool, self).__init__(*args, **kwargs)