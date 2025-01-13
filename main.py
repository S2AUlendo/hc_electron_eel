import eel
import os
from os import listdir
import subprocess
import sys
import json
import tkinter as tk
from tkinter import filedialog

from output_capture.output_capture import *
from cli_format.cli_visualizer import *
from cli_format.cli_reformat import *
from splash_screen.splashScreen import *

opti_visualizer = None
data_visualizer = None

executor = ThreadPoolExecutor(max_workers=2)

futures = {}
progress = {}
materials = {}
machines = {}

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
    
def get_data_dir():
    data_dir = persistent_path("data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def get_data_output_dict():
    data_output_dict_path = persistent_path("dictionary.json")
    data_output_dict = {}
    if not os.path.exists(data_output_dict_path):
        with open(data_output_dict_path, "w") as file:
            json.dump(data_output_dict, file)  # Write an empty dictionary to the file
    else:
        with open(data_output_dict_path, 'r') as f:
            try:
                data_output_dict = json.load(f)
            except json.JSONDecodeError:
                data_output_dict = {}
                with open(data_output_dict_path, "w") as file:
                    json.dump(data_output_dict, file)  # Write an empty dictionary to the file
    return data_output_dict

DATA_OUTPUT_DICT = get_data_output_dict()
DEFAULT_DATA_DIR = get_data_dir()
DEFAULT_OUTPUT_DIR = get_persistent_output_dir()

output_dir = ""
data_dir = ""
config = ""

materials_path = ""
machines_path = ""
app_config_path = ""

terminal_output = []

config_defaults = {
    "default": {
        "data": DEFAULT_DATA_DIR,
        "output": DEFAULT_OUTPUT_DIR,
        "active": True
    }
}

material_defaults = {
    "titanium_alloy": {
        "name": "Titanium Alloy",
        "kt": 7.0,
        "rho": 4420,
        "cp": 560,
        "h": 20
    },
    "aluminum_alloy": {
        "name": "Aluminum Alloy",
        "kt": 120.0,
        "rho": 2700,
        "cp": 900,
        "h": 20
    },
    "nickel_alloy": {
        "name": "Nickel Alloy",
        "kt": 12.0,
        "rho": 8190,
        "cp": 435,
        "h": 20
    },
    "stainless_steel": {
        "name": "Stainless Steel",
        "kt": 22.5,
        "rho": 7990,
        "cp": 500,
        "h": 50
    },
    "cobalt_chromium": {
        "name": "Cobalt Chromium",
        "kt": 14.0,
        "rho": 8300,
        "cp": 420,
        "h": 20
    }
}

machine_defaults = {
    "default": {
        "name": "Default",
        "vs": 300,
        "P": 100
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
    
    
def store_custom_machine(machine_key, custom_properties):
    try:
        global machines_path
        # Validate input
        if not isinstance(custom_properties, dict) or "name" not in custom_properties:
            raise ValueError("Invalid custom machine format")
        machines[machine_key] = custom_properties
        
        with open(machines_path, 'w') as f:
            f.write(json.dumps(machines))
            
        return True

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error saving custom material: {e}")
        return False

def get_configs():
    global config, app_config_path, data_dir, output_dir
    app_config_path = persistent_path('config.json')
    
    try:
        # Load existing config
        with open(app_config_path, 'r') as f:
            config = json.load(f)
            
        # Find active config and set directories
        active_config = None
        for key, item in config.items():
            if item.get("active", False):
                active_config = item
                break
                
        if active_config:
            data_dir = active_config.get("data", DEFAULT_DATA_DIR)
            output_dir = active_config.get("output", DEFAULT_OUTPUT_DIR)
        else:
            # No active config found, use defaults
            config = config_defaults.copy()
            data_dir = DEFAULT_DATA_DIR
            output_dir = DEFAULT_OUTPUT_DIR
            
            # Save default config
            with open(app_config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
    except (FileNotFoundError, json.JSONDecodeError):
        # Create new config file with defaults
        config = config_defaults.copy()
        data_dir = DEFAULT_DATA_DIR
        output_dir = DEFAULT_OUTPUT_DIR
        
        with open(app_config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    return config

@eel.expose
def change_output_dir(new_path):
    global config, output_dir
    if new_path:
        output_dir = new_path
        config["default"]["active"] = False
        
        # Initialize custom config if not exists
        if "custom" not in config:
            config["custom"] = {
                "data": DEFAULT_DATA_DIR,
                "output": new_path,
                "active": True
            }
        else:
            config["custom"]["output"] = new_path
            config["custom"]["active"] = True
        
        try:
            with open(app_config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
            return output_dir
            
    return output_dir

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
            f.write(json.dumps(material_defaults))
        return get_materials()

@eel.expose
def get_machines():
    global machines
    global machines_path
    machines_path = persistent_path('machines.json')
    try:
        with open(machines_path, 'r') as f:
            machines = json.load(f)
        return machines
    except FileNotFoundError:
        with open(machines_path, 'w') as f:
            f.write(json.dumps(machine_defaults))
        return get_machines()
        
@eel.expose
def convert_cli_file(filecontent, filename, selected_material, selected_machine):
    display_status("Starting...")
    global output_dir
    global data_dir
    global DATA_OUTPUT_DICT
    if type(selected_material) == str:
        selected_material = json.loads(selected_material)
    if type(selected_machine) == str:
        selected_machine = json.loads(selected_machine)
    
    material_key = "_".join(selected_material["name"].lower().strip().split(" "))
    machine_key = "_".join(selected_machine["name"].lower().strip().split(" "))
    if (material_key not in materials):
        display_status("Saving Custom Material...")
        store_custom_material(material_key, selected_material)
    if (machine_key not in machines):
        display_status("Saving Custom Machine...")
        store_custom_machine(machine_key, selected_machine)
    
    # store original file
    data_file = os.path.join(data_dir, filename)
    with open(data_file, "w", newline='') as f:
        f.write(filecontent)
    
    outputname = f"{filename[:-4].strip()}-{datetime.now().strftime('%m-%d-%Y_%H-%M-%S')}.cli"
    DATA_OUTPUT_DICT[outputname] = filename
    
    with open(persistent_path("dictionary.json"), "w") as file:
        json.dump(DATA_OUTPUT_DICT, file)
        
    future = executor.submit(convertDYNCliFile, filecontent, filename, outputname, output_dir, progress, selected_material, selected_machine)
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
        global output_dir
        
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
        global output_dir
        
        file_path = os.path.join(output_dir, filename)
        subprocess.Popen(f'explorer /select,"{file_path}"')
        
    except Exception as e:
        print(f"Error opening file location: {e}")
        return []

@eel.expose
def read_cli(filecontent):
    global data_visualizer  # Add global keyword
    data_visualizer = CLIVisualizer()
    data_visualizer.read_cli(filecontent)
    
    return

@eel.expose
def compare_cli(filename):
    global data_visualizer
    global opti_visualizer  # Add global keyword
    global data_dir
    global output_dir
    global DATA_OUTPUT_DICT
    
    original_file = DATA_OUTPUT_DICT[filename]
    data_visualizer = CLIVisualizer(original_file)
    opti_visualizer = CLIVisualizer(filename)
    
    data_visualizer.read_cli_file(data_dir)
    opti_visualizer.read_cli_file(output_dir, opti=True)
    return
            
@eel.expose
def retrieve_opti_layers():
    global opti_visualizer
    if opti_visualizer is None:
        return []
    return opti_visualizer.layers

@eel.expose
def retrieve_data_layers():
    global data_visualizer
    if data_visualizer is None:
        return []
    return data_visualizer.layers

@eel.expose
def get_num_layers_data():
    global data_visualizer
    if data_visualizer is None:
        return 0
    return data_visualizer.get_num_layers()

@eel.expose
def get_num_layers_opti():
    global opti_visualizer
    if opti_visualizer is None:
        return 0
    return opti_visualizer.get_num_layers()

@eel.expose
def get_num_hatches_data():
    global data_visualizer
    if data_visualizer is None:
        return 0
    return data_visualizer.get_num_hatches()

@eel.expose
def get_num_hatches_opti():
    global opti_visualizer
    if opti_visualizer is None:
        return 0
    return opti_visualizer.get_num_hatches()

@eel.expose
def get_r_from_opti_layer():
    global opti_visualizer
    if opti_visualizer is None:
        return []
    return opti_visualizer.get_r_from_layer()

@eel.expose
def get_r_from_data_layer():
    global data_visualizer
    if data_visualizer is None:
        return []
    return data_visualizer.get_r_from_layer()

@eel.expose
def set_current_opti_layer(layer_num):
    global opti_visualizer
    if opti_visualizer is not None:
        opti_visualizer.set_current_layer(layer_num)
        
@eel.expose
def set_current_data_layer(layer_num):
    global data_visualizer
    if data_visualizer is not None:
        data_visualizer.set_current_layer(layer_num)

@eel.expose
def set_current_opti_hatch(hatch_num):
    global opti_visualizer
    if opti_visualizer is not None:
        opti_visualizer.set_current_hatch(hatch_num)
        
@eel.expose
def set_current_data_hatch(hatch_num):
    global data_visualizer
    if data_visualizer is not None:
        data_visualizer.set_current_hatch(hatch_num)
    
@eel.expose
def retrieve_bounding_box_from_opti_layer():
    global opti_visualizer
    if opti_visualizer is None:
        return {'x': [], 'y': []}
    bounding_boxes = opti_visualizer.get_bounding_boxes_from_layer()
    return {'bounding_boxes': bounding_boxes, 'x_min': opti_visualizer.x_min, 'x_max': opti_visualizer.x_max, 'y_min': opti_visualizer.y_min, 'y_max': opti_visualizer.y_max}

@eel.expose
def retrieve_coords_from_opti_cur():
    global opti_visualizer
    if opti_visualizer is None:
        return []
    coords = opti_visualizer.retrieve_hatch_lines_from_layer()
    return {'x': coords[0], 'y': coords[1], 'x_min': opti_visualizer.x_min, 'x_max': opti_visualizer.x_max, 'y_min': opti_visualizer.y_min, 'y_max': opti_visualizer.y_max}

@eel.expose
def retrieve_bounding_box_from_data_layer():
    global data_visualizer
    if data_visualizer is None:
        return {'x': [], 'y': []}
    bounding_boxes = data_visualizer.get_bounding_boxes_from_layer()
    return {'bounding_boxes': bounding_boxes, 'x_min': data_visualizer.x_min, 'x_max': data_visualizer.x_max, 'y_min': data_visualizer.y_min, 'y_max': data_visualizer.y_max}

@eel.expose
def retrieve_coords_from_data_cur():
    global data_visualizer
    if data_visualizer is None:
        return []
    coords = data_visualizer.retrieve_hatch_lines_from_layer()
    return {'x': coords[0], 'y': coords[1], 'x_min': data_visualizer.x_min, 'x_max': data_visualizer.x_max, 'y_min': data_visualizer.y_min, 'y_max': data_visualizer.y_max}

if __name__ == '__main__':
    splash = SplashScreen()
    for i in range(5):
        splash.update_progress(i * 20)
        time.sleep(0.5)  # Simulate loading
    splash.destroy()
    
    output_capture = OutputCapture()
    output_capture.start_capture()
    
    get_configs()
    eel.start('templates/app.html', mode="electron")
