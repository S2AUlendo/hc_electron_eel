import eel
import os
from os import listdir
import subprocess
import sys
import json
import traceback

from output_capture.output_capture import *
from cli_format.cli_visualizer import *
from cli_format.cli_reformat import *
from screens.errorWindow import *
from screens.splashScreen import *
from screens.activationScreen import *
from license.license import *

from mp.multiprocessing_utils import initialize_multiprocessing

from queue import Queue
VERSION = "0.1.1"

_manager, _pool = None, None
futures = {}  # Tracks AsyncResult objects
progress = {}  # Progress tracking
license = LicenseKey()

activation_splash = None
opti_visualizer = None
data_visualizer = None

futures = {}
progress = {}
materials = {}
machines = {}
active_config = None

def persistent_path(rel_path):
    if getattr(sys, 'frozen', False):
        # The application is frozen (PyInstaller)
        exe_dir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, rel_path)

def get_persistent_output_dir():
    global output_dir
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

data_output_dict = None
default_data_dir = None
default_output_dir = None

output_dir = ""
data_dir = ""
config = ""

materials_path = ""
machines_path = ""
app_config_path = ""

terminal_output = []
is_activated = False

config_defaults = {
    "default": {
        "data": default_data_dir,
        "output": default_output_dir,
        "license_key": "",
        "feature": 0,
        "active": True
    }
}

material_defaults = {
    "Aluminum": {
        "AlSi10Mg": {
            "name": "AlSi10Mg",
            "kt": 150,
            "rho": 2670,
            "cp": 900,
            "h": 10
        },
        "Al6061": {
            "name": "Al6061",
            "kt": 167,
            "rho": 2700,
            "cp": 895,
            "h": 10
        },
        "AlSi12": {
            "name": "AlSi12",
            "kt": 155,
            "rho": 2680,
            "cp": 890,
            "h": 10
        }
    },
    "Titanium": {
        "Ti6Al4V": {
            "name": "Ti6Al4V",
            "kt": 6.7,
            "rho": 4420,
            "cp": 560,
            "h": 15
        },
        "Pure Titanium": {
            "name": "Pure Titanium",
            "kt": 16.4,
            "rho": 4506,
            "cp": 520,
            "h": 15
        },
        "Ti-6Al-4V (Grade 5)": {
            "name": "Ti-6Al-4V (Grade 5)",
            "kt": 6.7,
            "rho": 4420,
            "cp": 560,
            "h": 15
        },
        "Ti-6Al-2Sn-4Zr-2Mo": {
            "name": "Ti-6Al-2Sn-4Zr-2Mo",
            "kt": 6.3,
            "rho": 4540,
            "cp": 570,
            "h": 15
        }
    },
    "Steel": {
        "316L Stainless Steel": {
            "name": "316L Stainless Steel",
            "kt": 14,
            "rho": 8000,
            "cp": 500,
            "h": 20
        },
        "304 Stainless Steel": {
            "name": "304 Stainless Steel",
            "kt": 14,
            "rho": 8000,
            "cp": 500,
            "h": 20
        },
        "Maraging Steel (18Ni300)": {
            "name": "Maraging Steel (18Ni300)",
            "kt": 14,
            "rho": 8000,
            "cp": 500,
            "h": 20
        }
    },
    "Nickel": {
        "Inconel 718": {
            "name": "Inconel 718",
            "kt": 11.4,
            "rho": 8190,
            "cp": 435,
            "h": 25
        },
        "Inconel 625": {
            "name": "Inconel 625",
            "kt": 9.8,
            "rho": 8440,
            "cp": 427,
            "h": 25
        }
    },
    "Copper": {
        "CuCrZr": {
            "name": "CuCrZr",
            "kt": 330,
            "rho": 8900,
            "cp": 385,
            "h": 35
        },
        "Pure Copper": {
            "name": "Pure Copper",
            "kt": 398,
            "rho": 8960,
            "cp": 385,
            "h": 35
        }
    },
    "Cobalt": {
        "CoCr": {
            "name": "CoCr",
            "kt": 14,
            "rho": 8500,
            "cp": 450,
            "h": 20
        }
    },
    "Nickel-Based Superalloys": {
        "Hastelloy X": {
            "name": "Hastelloy X",
            "kt": 11,
            "rho": 8220,
            "cp": 460,
            "h": 25
        }
    },
    "Stainless Steels": {
        "17-4 PH": {
            "name": "17-4 PH",
            "kt": 16,
            "rho": 7800,
            "cp": 500,
            "h": 20
        }
    },
    "Cobalt-Chromium Alloys": {
        "CoCrMo": {
            "name": "CoCrMo",
            "kt": 14,
            "rho": 8300,
            "cp": 460,
            "h": 22
        },
        "CoCrFeNiMn (High Entropy Alloys)": {
            "name": "CoCrFeNiMn (High Entropy Alloys)",
            "kt": 12.5,
            "rho": 7800,
            "cp": 480,
            "h": 22
        }
    },
    "Maraging Steels": {
        "18Ni-300": {
            "name": "18Ni-300",
            "kt": 14.5,
            "rho": 8000,
            "cp": 500,
            "h": 20
        }
    },
    "Tool Steels": {
        "H13 Tool Steel": {
            "name": "H13 Tool Steel",
            "kt": 28,
            "rho": 7750,
            "cp": 460,
            "h": 30
        }
    },
    "Refractory Metals": {
        "Tungsten (W)": {
            "name": "Tungsten (W)",
            "kt": 174,
            "rho": 19250,
            "cp": 134,
            "h": 50
        },
        "Tantalum (Ta)": {
            "name": "Tantalum (Ta)",
            "kt": 57.5,
            "rho": 16650,
            "cp": 140,
            "h": 45
        }
    },
    "Precious Metals": {
        "Gold Alloys": {
            "name": "Gold Alloys",
            "kt": 315,
            "rho": 19300,
            "cp": 129,
            "h": 35
        },
        "Platinum Alloys": {
            "name": "Platinum Alloys",
            "kt": 71.6,
            "rho": 21450,
            "cp": 133,
            "h": 38
        }
    },
    "Custom": {}
}

machine_defaults = {
    "Default": {
        "name": "Default",
        "vs": 300,
        "P": 100
    }
}

features = {
    "0": 2000,
    "1": 20000,
    "2": 200000,
    "3": 1000000,
    "4": np.inf
}

def resource_path(rel_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# eel.browsers.set_path('electron', resource_path('electron\electron.exe'))
# eel.init('web', allowed_extensions=['.js', '.html'])

def store_custom_material(material_category, material_key, custom_material):
    try:
        global materials_path
        # Validate input
        if not isinstance(custom_material, dict) or "name" not in custom_material:
            raise ValueError("Invalid custom material format")
        materials[material_category][material_key] = custom_material
        
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
    global config, app_config_path, data_dir, output_dir, active_config, data_output_dict
    default_data_dir = get_data_dir()
    data_output_dict = get_data_output_dict()
    default_output_dir = get_persistent_output_dir()
    app_config_path = persistent_path('config.json')
    
    try:
        # Load existing config
        with open(app_config_path, 'r') as f:
            config = json.load(f)
            
        # Find active config and set directories
        for key, item in config.items():
            if item.get("active", False):
                active_config = item
                break
        
        if active_config:
            data_dir = active_config.get("data", default_data_dir)
            output_dir = active_config.get("output", default_output_dir)
        else:
            # No active config found, use defaults
            config = config_defaults.copy()
            data_dir = default_data_dir
            output_dir = default_output_dir
            active_config = config["default"]
            
            # Save default config
            with open(app_config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
    except (FileNotFoundError, json.JSONDecodeError):
        # Create new config file with defaults
        config = config_defaults.copy()
        data_dir = default_data_dir
        output_dir = default_output_dir
        active_config = config["default"]
        
        with open(app_config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    return config

def set_size_limit(feature):
    if feature == active_config["feature"]:
        return
    active_config["feature"] = feature
    
    # save new config with new feature
    with open(app_config_path, "w") as f:
        json.dump(config, f, indent=4)
    
@eel.expose
def change_output_dir(new_path):
    global config, output_dir
    if new_path:
        output_dir = new_path
        config["default"]["active"] = False
        
        # Initialize custom config if not exists
        if "custom" not in config:
            config["custom"] = {
                "data": default_data_dir,
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
            eel.displayError(traceback.format_exc(), "Error")
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
    
def display_status(status_message):
    eel.displayStatus(status_message)
    print(status_message)
    
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
def convert_cli_file(filecontent, filename, selected_material, selected_material_category, selected_machine):
    global _manager, _pool
    
    if _manager is None or _pool is None:
        _manager, _pool = initialize_multiprocessing()
    
    display_status("Starting...")
    global output_dir
    global data_dir
    global data_output_dict
    try:
        if type(selected_material) == str:
            selected_material = json.loads(selected_material)
        if type(selected_machine) == str:
            selected_machine = json.loads(selected_machine)
        
        material_key = "_".join(selected_material["name"].strip().split(" "))
        machine_key = "_".join(selected_machine["name"].strip().split(" "))
        if (material_key not in materials[selected_material_category]):
            display_status("Saving Custom Material...")
            store_custom_material(selected_material_category, material_key, selected_material)
        if (machine_key not in machines):
            display_status("Saving Custom Machine...")
            store_custom_machine(machine_key, selected_machine)
        
        # store original file
        data_file = os.path.join(data_dir, filename)
        with open(data_file, "w", newline='') as f:
            f.write(filecontent)
        
        outputname = f"{filename[:-4].strip()}-hc-{datetime.now().strftime('%m-%d-%Y_%H-%M-%S')}.cli"
        data_output_dict[outputname] = filename
        
        with open(persistent_path("dictionary.json"), "w") as file:
            json.dump(data_output_dict, file)
            
        progress[filename] = _manager.dict()
        progress[filename]['value'] = 0
        progress[filename]['msg'] = ""
        progress[filename]['error'] = ""
        
        # Submit task to pool
        async_result = _pool.apply_async(
            convertDYNCliFile,
            args=(
                filecontent,
                filename,
                outputname,
                output_dir,
                progress[filename],  # Pass the shared dict item
                selected_material,
                selected_machine,
                features[active_config["feature"]]
            )
        )
        futures[filename] = async_result
        return "Task started"
    
    except Exception as e:
        eel.displayError(traceback.format_exc(), "Error")
        print(f"Error starting task: {e}")
        return "Error starting task"

@eel.expose 
def get_task_status(filename):
    if filename in futures:
        async_result = futures[filename]
        if async_result.ready():
            try:
                async_result.get()
                if progress[filename]['error'] != "":
                    eel.displayError(progress[filename]["error"], "Error")
                return {"status": "completed"}
            except Exception as e:
                print(traceback.format_exc())
                return {"status": "error", "error": str(e)}
        else:
            if progress[filename]['msg'] != "":
                display_status(progress[filename]['msg'])
                
            return {"status": "running", "progress": progress[filename]['value']}
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
        eel.displayError(traceback.format_exc(), "Error")
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
        eel.displayError(traceback.format_exc(), "Error")
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
    global data_output_dict
    
    try:
        original_file = data_output_dict[filename]
        data_visualizer = CLIVisualizer(original_file)
        opti_visualizer = CLIVisualizer(filename)
        
        data_visualizer.read_cli_file(data_dir)
        opti_visualizer.read_cli_file(output_dir, opti=True)
        return
    except Exception as e:
        eel.displayError(traceback.format_exc(), "Error")
        print(f"Error comparing files: {e}")
            
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
def retrieve_full_bounding_box_opti():
    global opti_visualizer
    if opti_visualizer is None:
        return {'x': [], 'y': []}
    bounding_boxes = opti_visualizer.get_full_bounding_boxes_from_layer()
    return {'bounding_boxes': bounding_boxes, 'x_min': opti_visualizer.x_min, 'x_max': opti_visualizer.x_max, 'y_min': opti_visualizer.y_min, 'y_max': opti_visualizer.y_max}
    
@eel.expose
def retrieve_full_bounding_box_data():
    global data_visualizer
    if data_visualizer is None:
        return {'x': [], 'y': []}
    bounding_boxes = data_visualizer.get_full_bounding_boxes_from_layer()
    return {'bounding_boxes': bounding_boxes, 'x_min': data_visualizer.x_min, 'x_max': data_visualizer.x_max, 'y_min': data_visualizer.y_min, 'y_max': data_visualizer.y_max}
    
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

@eel.expose
def show_activate_screen():
    global license
    activation_splash = ActivationScreen(license, preload=False)
    activation_splash.run()
    
@eel.expose
def get_app_info():
    global license
    
    license.get_license_day_remaining()
    return {
        "version": VERSION,
        "activated": license.activated,
        "feature": license.feature,
        "license_key": license.license_key,
        "days_remaining": license.days_remaining
    }

def create_mutex():
    """Create a Windows mutex to ensure single instance"""
    import win32event
    import win32api
    import winerror
    
    mutex_name = "Global\\UlendoHCAppMutex"  # Choose a unique name
    try:
        handle = win32event.CreateMutex(None, 1, mutex_name)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            error_screen = ErrorWindow(
                "Another instance is already running",
                "Please close the existing Heat Compensation application before starting a new one."
            )
            sys.exit(1)
        return handle
    except Exception as e:
        raise e

if __name__ == '__main__':
    try:
        from multiprocessing import freeze_support
        freeze_support()
        
        # Initialize multiprocessing FIRST
        initialize_multiprocessing()
        
        # Check for instance then create splash screen first
        mutex = create_mutex()
        
        activation_splash = ActivationScreen(license)
        activation_splash.run()
        splash = SplashScreen()
        
        get_configs()
        
        # Set the feature size limit
        if not license.activated:
            sys.exit()
        set_size_limit(license.feature)
        
        # Create communication queue and event flag
        init_queue = Queue()
        init_complete = threading.Event()

        # Thread worker function
        def initialize_eel():
            try:
                eel.init('web', allowed_extensions=['.js', '.html'])
                eel.browsers.set_path('electron', resource_path('electron\electron.exe'))
                init_queue.put(("success", None))
            except Exception as e:
                init_queue.put(("error", e))
            finally:
                init_complete.set()

        # Start initialization thread
        init_thread = threading.Thread(target=initialize_eel)
        init_thread.start()

        while not init_complete.is_set():
            # Update splash with indeterminate progress pattern
            splash.update_progress("Warming up static files...")
            time.sleep(0.1)  # Faster updates for responsiveness

            # Check for initialization results
            if not init_queue.empty():
                status, payload = init_queue.get()
                if status == "error":
                    raise payload

        # Clean up splash
        splash.destroy()

        # Handle post-init
        output_capture = OutputCapture()
        output_capture.start_capture()
        
        # start the app
        eel.start('templates/app.html', mode="electron")
        
    except Exception as e:
        error_screen = ErrorWindow(str(e), traceback.format_exc())
        sys.exit(1)