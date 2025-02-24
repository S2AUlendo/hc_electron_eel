# multiprocessing_utils.py
from multiprocessing import Pool, Manager
import os

_initialized = False
_manager = None
_pool = None

def initialize_multiprocessing():
    global _initialized, _manager, _pool
    if not _initialized:
        _manager = Manager()
        _pool = Pool(processes=4)
        _initialized = True
    return _manager, _pool

def get_pool():
    return _pool

def get_manager():
    return _manager