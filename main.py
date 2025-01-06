import eel
import os
from os import listdir
import subprocess
import sys
  
from cli_format.cli_visualizer import *
from cli_format.cli_reformat import *

visualizer = None

executor = ThreadPoolExecutor(max_workers=2)
futures = {}
progress = {}
materials = {}
terminal_output = []

# class StreamToList:
#     def __init__(self, output_list):
#         self.output_list = output_list
        
#     def write(self, message):
#         if message.strip():
#             self.output_list.append(message)
    
#     def flush(self):
#         pass
    
# sys.stdout = StreamToList(terminal_output)
# sys.stderr = StreamToList(terminal_output)

def get_persistent_output_dir():
    if hasattr(sys, '_MEIPASS'):
        # Running as bundled EXE - store beside the EXE
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'output')
    else:
        # Running in development
        project_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(project_dir, 'output')
    
def store_custom_material(material_key, custom_material):
    try:
        # Validate input
        if not isinstance(custom_material, dict) or "name" not in custom_material:
            raise ValueError("Invalid custom material format")
        materials[material_key] = custom_material
        
        project_path = os.getcwd()
        file_path = os.path.join(project_path, 'materials.json')
        
        with open(file_path, 'w') as f:
            json.dump(materials, f, indent=4)
            
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
    with open('materials.json', 'r') as f:
        materials = json.load(f)
    return materials

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

def get_json_path():
    if hasattr(sys, '_MEIPASS'):
        # Running as bundled exe
        base_path = sys._MEIPASS
    else:
        # Running in development
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, 'materials.json')

get_json_path()
eel.init('web')
eel.start('templates/main.html', mode="electron")