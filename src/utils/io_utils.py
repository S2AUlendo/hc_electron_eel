import os
import sys

def persistent_path(rel_path):
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.getcwd()
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
