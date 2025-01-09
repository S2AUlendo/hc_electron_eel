import eel
import os
from os import listdir
import subprocess
import sys
import json

from output_capture.output_capture import *
from cli_format.cli_visualizer import *
from cli_format.cli_reformat import *

visualizer = None

executor = ThreadPoolExecutor(max_workers=2)

futures = {}
progress = {}
materials = {}
materials_path = ""
terminal_output = []
default_materials = {
    "titanium_alloy": {
        "name": "Titanium Alloy",
        "kt": 7.0,
        "rho": 4420,
        "cp": 560,
        "vs": 0.6,
        "h": 20,
        "P": 150
    },
    "aluminum_alloy": {
        "name": "Aluminum Alloy",
        "kt": 120.0,
        "rho": 2700,
        "cp": 900,
        "vs": 1.0,
        "h": 20,
        "P": 250
    },
    "nickel_alloy": {
        "name": "Nickel Alloy",
        "kt": 12.0,
        "rho": 8190,
        "cp": 435,
        "vs": 0.8,
        "h": 20,
        "P": 300
    },
    "stainless_steel": {
        "name": "Stainless Steel",
        "kt": 22.5,
        "rho": 7990,
        "cp": 500,
        "vs": 0.6,
        "h": 50,
        "P": 100
    },
    "cobalt_chromium": {
        "name": "Cobalt Chromium",
        "kt": 14.0,
        "rho": 8300,
        "cp": 420,
        "vs": 0.7,
        "h": 20,
        "P": 200
    }
}


def resource_path(rel_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# eel.browsers.set_path('electron', resource_path('electron\electron.exe'))
eel.init('web', allowed_extensions=['.js', '.html'])
   
def persistent_path(rel_path):
    if getattr(sys, 'frozen', False):
        # The application is frozen (PyInstaller)
        exe_dir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, rel_path)

def get_persistent_output_dir():
    output_dir = persistent_path("output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir
    
def store_custom_material(material_key, custom_material):
    try:
        global materials_path
        # Validate input
        if not isinstance(custom_material, dict) or "name" not in custom_material:
            raise ValueError("Invalid custom material format")
        materials[material_key] = custom_material
        
        with open(materials_path, 'w') as f:
            f.write(json.dumps(materials))
            
        return True

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error saving custom material: {e}")
        return False

@eel.expose
def get_terminal_output():
    return terminal_output

@eel.expose
def get_materials():
    global materials
    global materials_path
    materials_path = persistent_path('materials.json')
    try:
        with open(materials_path, 'r') as f:
            materials = json.load(f)
        return materials
    except FileNotFoundError:
        with open(materials_path, 'w') as f:
            f.write(json.dumps(default_materials))
        return get_materials()
        
@eel.expose
def convert_cli_file(filecontent, filename, selected_material):
    if type(selected_material) == str:
        selected_material = json.loads(selected_material)
    material_key = "_".join(selected_material["name"].lower().strip().split(" "))
    if (material_key not in materials):
        store_custom_material(material_key, selected_material)
    
    output_dir = get_persistent_output_dir()
    
    future = executor.submit(convertDYNCliFile, filecontent, filename, output_dir, progress, selected_material)
    futures[filename] = future
    progress[filename] = 0
    return "Task started"

@eel.expose
def get_task_status(filename):
    if filename in futures:
        future = futures[filename]
        if future.done():
            try:
                result = future.result()
                return {"status": "completed", "result": result}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return {"status": "in_progress", "progress": progress[filename]}
    else:
        return {"status": "not_found"}
    
@eel.expose
def view_processed_files():
    try:
        output_dir = get_persistent_output_dir()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        files = [f for f in listdir(output_dir) if f.endswith('.cli')]
        
        files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
        
        return files
    except Exception as e:
        print(f"Error listing processed files: {e}")
        return []

@eel.expose
def plot_with_slider():
    return plot_with_slider()

@eel.expose
def open_file_location(filename):
    try:
        base_path = get_persistent_output_dir()
        
        file_path = os.path.join(base_path, filename)
        subprocess.Popen(f'explorer /select,"{file_path}"')
        
    except Exception as e:
        print(f"Error opening file location: {e}")
        return []

@eel.expose
def read_cli(filename):
    global visualizer  # Add global keyword
    visualizer = CLIVisualizer(filename)
    
    output_dir = get_persistent_output_dir()
    
    visualizer.read_cli_file(output_dir)
    return
            
@eel.expose
def retrieve_layers():
    global visualizer
    if visualizer is None:
        return []
    return visualizer.layers

@eel.expose
def get_num_layers():
    global visualizer
    if visualizer is None:
        return 0
    return visualizer.get_num_layers()

@eel.expose
def get_num_hatches():
    global visualizer
    if visualizer is None:
        return 0
    return visualizer.get_num_hatches()

@eel.expose
def get_r_from_layer():
    global visualizer
    if visualizer is None:
        return []
    return visualizer.get_r_from_layer()

@eel.expose
def set_current_layer(layer_num):
    global visualizer
    if visualizer is not None:
        visualizer.set_current_layer(layer_num)

@eel.expose
def set_current_hatch(hatch_num):
    global visualizer
    if visualizer is not None:
        visualizer.set_current_hatch(hatch_num)
    
@eel.expose
def retrieve_bounding_box_from_layer():
    global visualizer
    if visualizer is None:
        return {'x': [], 'y': []}
    bounding_boxes = visualizer.get_bounding_boxes_from_layer()
    return {'bounding_boxes': bounding_boxes, 'x_min': visualizer.x_min, 'x_max': visualizer.x_max, 'y_min': visualizer.y_min, 'y_max': visualizer.y_max}

@eel.expose
def retrieve_coords_from_cur():
    global visualizer
    if visualizer is None:
        return []
    coords = visualizer.retrieve_hatch_lines_from_layer()
    return {'x': coords[0], 'y': coords[1], 'x_min': visualizer.x_min, 'x_max': visualizer.x_max, 'y_min': visualizer.y_min, 'y_max': visualizer.y_max}

output_capture = OutputCapture()
output_capture.start_capture()
eel.start('templates/app.html', mode="electron")
