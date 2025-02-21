import eel
import threading
import subprocess
import traceback
import os
import sys
import time
import json
from os import listdir
from queue import Queue
from src.core.config_manager import ConfigManager
from src.core.data_manager import DataManager
from src.core.processing_manager import ProcessingManager
from src.cli_format.cli_visualizer import CLIVisualizer
from src.utils.io_utils import persistent_path, resource_path
from src.output_capture.output_capture import OutputCapture
from src.license.license import LicenseKey
from src.screens.activationScreen import ActivationScreen
from src.screens.errorWindow import ErrorWindow
from src.screens.splashScreen import SplashScreen

class HeatCompensationApp:
    def __init__(self):
        self.output_capture = OutputCapture()
        self.config = ConfigManager()
        self.data_manager = DataManager()
        self.processing = ProcessingManager(self.config, self.data_manager, self.output_capture.mp_output_queue)
        self.license = LicenseKey()
        self.init_queue = Queue()
        self.init_complete = threading.Event()
        self.init_thread = threading.Thread(target=self.initialize_eel)
        self.activation_splash = None
        self.loading_splash = None
        self.opti_visualizer = None
        self.data_visualizer = None
        
        self.setup_exposed_functions()
        
    def __del__(self):
        # self.output_capture.restore()
        self.opti_visualizer = None
        self.data_visualizer = None
        print("App closed.")

    def initialize_eel(self):
        try:
            eel.init('web', allowed_extensions=['.js', '.html'])
            eel.browsers.set_path('electron', resource_path('electron\electron.exe'))
            self.init_queue.put(("success", None))
        except Exception as e:
            self.init_queue.put(("error", e))
        finally:
            self.init_complete.set()

    def setup_exposed_functions(self):
        # Expose all necessary methods to Eel
        eel.expose(self.get_terminal_output)
        eel.expose(self.view_processed_files)
        eel.expose(self.get_r_from_opti_layer)
        eel.expose(self.get_r_from_data_layer)
        eel.expose(self.convert_cli_file)
        eel.expose(self.get_task_status)
        eel.expose(self.open_file_location)
        eel.expose(self.get_materials)
        eel.expose(self.get_machines)
        eel.expose(self.read_cli)
        eel.expose(self.compare_cli)
        eel.expose(self.set_current_opti_layer)
        eel.expose(self.set_current_data_layer)
        eel.expose(self.set_current_opti_hatch)
        eel.expose(self.set_current_data_hatch)
        eel.expose(self.retrieve_coords_from_opti_cur)
        eel.expose(self.retrieve_coords_from_data_cur)
        eel.expose(self.get_app_info)
        eel.expose(self.show_upgrade_screen)
        eel.expose(self.display_status)
        eel.expose(self.retrieve_opti_layers)
        eel.expose(self.retrieve_data_layers)
        eel.expose(self.get_num_layers_data)
        eel.expose(self.get_num_layers_opti)
        eel.expose(self.get_num_hatches_data)
        eel.expose(self.get_num_hatches_opti)
        eel.expose(self.retrieve_full_bounding_box_opti)
        eel.expose(self.retrieve_full_bounding_box_data)
        eel.expose(self.retrieve_bounding_box_from_opti_layer)
        eel.expose(self.retrieve_bounding_box_from_data_layer)
        eel.expose(self.edit_material)
        eel.expose(self.delete_material)
        eel.expose(self.edit_machine)
        eel.expose(self.delete_machine)

    def start(self):
        try:
            self.show_activate_screen()
            self.show_loading_screen()
            self.init_thread.start()
            self.update_loading_screen()
            self.output_capture.start_capture()
            
            eel.start('templates/app.html', mode="electron")
        except Exception as e:
            print(e)
            print(str(e))
            self.handle_error(e)

    def show_activate_screen(self):
        self.activation_splash = ActivationScreen(self.license)
        self.activation_splash.run()
        
        # set the feature of the license
        self.config.set_size_limit(self.license.feature)
    
    def show_upgrade_screen(self):
        self.activation_splash = ActivationScreen(self.license, False)
        self.activation_splash.run()
        
        # set the feature of the license
        self.config.set_size_limit(self.license.feature)

    def show_loading_screen(self):
        self.loading_splash = SplashScreen()

    def update_loading_screen(self):
        while not self.init_complete.is_set():
            # Update splash with indeterminate progress pattern
            self.loading_splash.update_progress("Warming up static files...")
            time.sleep(0.1)  # Faster updates for responsiveness

            # Check for initialization results
            if not self.init_queue.empty():
                status, payload = self.init_queue.get()
                if status == "error":
                    raise payload
                
        self.loading_splash.destroy()

    def handle_error(self, error):
        print(str(error))
        error_screen = ErrorWindow(str(error), traceback.format_exc())
        sys.exit(1)

    # File operations
    def convert_cli_file(self, filecontent, filename, material, material_category, machine):
        return self.processing.convert_cli_file(filecontent, filename, material, material_category, machine)

    def get_task_status(self, filename):
        return self.processing.get_task_status(filename)

    def open_file_location(self, filename):
        try:
            file_path = os.path.join(self.config.active_config["output"], filename)
            if sys.platform == 'win32':
                subprocess.Popen(f'explorer /select,"{file_path}"')
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-R', file_path])
            else:
                subprocess.Popen(['xdg-open', os.path.dirname(file_path)])
            return True
        except Exception as e:
            eel.displayError(traceback.format_exc(), "Error")
            return False

    # def get_terminal_output():
    #     return terminal_output
    def edit_material(self, material_category, material_properties):
        selected_material = material_properties
        if isinstance(material_properties, str):
            selected_material = json.loads(selected_material)
        material_key = selected_material["name"].strip()
        
        return self.data_manager.edit_material(material_category, material_key, material_properties)
    
    def delete_material(self, material_category, material_properties):
        selected_material = material_properties
        if isinstance(material_properties, str):
            selected_material = json.loads(material_properties)
        material_key = selected_material["name"].strip()
        
        return self.data_manager.delete_material(material_category, material_key)
    
    def edit_machine(self, machine_properties):
        selected_machine = machine_properties
        if isinstance(machine_properties, str):
            selected_machine = json.loads(machine_properties)
        machine_key = selected_machine["name"].strip()
            
        return self.data_manager.edit_machine(machine_key, machine_properties)
    
    def delete_machine(self, machine_properties):
        selected_machine = machine_properties
        if isinstance(machine_properties, str):
            selected_machine = json.loads(machine_properties)
        machine_key = selected_machine["name"].strip()
        
        return self.data_manager.delete_machine(machine_key)
    
    def get_materials(self):
        return self.data_manager.materials
        
    def display_status(status_message):
        eel.displayStatus(status_message)
        print(status_message)
        
    def get_machines(self):
        return self.data_manager.machines
    
    # Visualization methods
    def read_cli(self, filecontent):
        try:
            self.data_visualizer = CLIVisualizer()
            self.data_visualizer.read_cli(filecontent)
            return True
        except Exception as e:
            eel.displayError(traceback.format_exc(), "Error")
            return False

    def compare_cli(self, filename):
        try:
            original_file = self.processing.data_output_dict[filename]
            self.data_visualizer = CLIVisualizer(original_file)
            self.opti_visualizer = CLIVisualizer(filename)
            
            self.data_visualizer.read_cli_file(self.config.active_config["data"], has_r=True)
            self.opti_visualizer.read_cli_file(self.config.active_config["output"], has_r=True)
            return True
        except Exception as e:
            eel.displayError(traceback.format_exc(), "Error")
            return False 
        
    def retrieve_opti_layers(self):
        if self.opti_visualizer is None:
            return []
        return self.opti_visualizer.layers

    def retrieve_data_layers(self):
        if self.data_visualizer is None:
            return []
        return self.data_visualizer.layers

    def get_num_layers_data(self):
        if self.data_visualizer is None:
            return 0
        return self.data_visualizer.get_num_layers()

    def get_num_layers_opti(self):
        if self.opti_visualizer is None:
            return 0
        return self.opti_visualizer.get_num_layers()
    
    def get_num_hatches_data(self):
        if self.data_visualizer is None:
            return 0
        return self.data_visualizer.get_num_hatches()

    def get_num_hatches_opti(self):
        if self.opti_visualizer is None:
            return 0
        return self.opti_visualizer.get_num_hatches()

    def get_r_from_opti_layer(self):
        if self.opti_visualizer:
            return self.opti_visualizer.get_r_from_layer().tolist()
        return []

    def get_r_from_data_layer(self):
        if self.data_visualizer:
            return self.data_visualizer.get_r_from_layer().tolist()
        return []

    # Layer/hatch control methods
    def set_current_opti_layer(self, layer_num):
        if self.opti_visualizer:
            self.opti_visualizer.set_current_layer(layer_num)
        
    def set_current_data_layer(self, layer_num):
        if self.data_visualizer:
            self.data_visualizer.set_current_layer(layer_num)

    def set_current_opti_hatch(self, hatch_num):
        if self.opti_visualizer:
            self.opti_visualizer.set_current_hatch(hatch_num)
        
    def set_current_data_hatch(self, hatch_num):
        if self.data_visualizer:
            self.data_visualizer.set_current_hatch(hatch_num)

    def retrieve_full_bounding_box_opti(self):
        if self.opti_visualizer is None:
            return {'x': [], 'y': []}
        bounding_boxes = self.opti_visualizer.get_full_bounding_boxes_from_layer()
        return {'bounding_boxes': bounding_boxes, 'x_min': self.opti_visualizer.x_min, 'x_max': self.opti_visualizer.x_max, 'y_min': self.opti_visualizer.y_min, 'y_max': self.opti_visualizer.y_max}
        
    def retrieve_full_bounding_box_data(self):
        if self.data_visualizer is None:
            return {'x': [], 'y': []}
        bounding_boxes = self.data_visualizer.get_full_bounding_boxes_from_layer()
        return {'bounding_boxes': bounding_boxes, 'x_min': self.data_visualizer.x_min, 'x_max': self.data_visualizer.x_max, 'y_min': self.data_visualizer.y_min, 'y_max': self.data_visualizer.y_max}
        
    def retrieve_bounding_box_from_opti_layer(self):
        if self.opti_visualizer is None:
            return {'x': [], 'y': []}
        bounding_boxes = self.opti_visualizer.get_bounding_boxes_from_layer()
        return {'bounding_boxes': bounding_boxes, 'x_min': self.opti_visualizer.x_min, 'x_max': self.opti_visualizer.x_max, 'y_min': self.opti_visualizer.y_min, 'y_max': self.opti_visualizer.y_max}

    def retrieve_bounding_box_from_data_layer(self):
        if self.data_visualizer is None:
            return {'x': [], 'y': []}
        bounding_boxes = self.data_visualizer.get_bounding_boxes_from_layer()
        return {'bounding_boxes': bounding_boxes, 'x_min': self.data_visualizer.x_min, 'x_max': self.data_visualizer.x_max, 'y_min': self.data_visualizer.y_min, 'y_max': self.data_visualizer.y_max}
    
    # Coordinate retrieval methods
    def retrieve_coords_from_opti_cur(self):
        if self.opti_visualizer:
            coords = self.opti_visualizer.retrieve_hatch_lines_from_layer()
            return {
                'x': coords[0],
                'y': coords[1],
                'bounds': {
                    'x_min': self.opti_visualizer.x_min,
                    'x_max': self.opti_visualizer.x_max,
                    'y_min': self.opti_visualizer.y_min,
                    'y_max': self.opti_visualizer.y_max
                }
            }
        return {}

    def retrieve_coords_from_data_cur(self):
        if self.data_visualizer:
            coords = self.data_visualizer.retrieve_hatch_lines_from_layer()
            return {
                'x': coords[0],
                'y': coords[1],
                'bounds': {
                    'x_min': self.data_visualizer.x_min,
                    'x_max': self.data_visualizer.x_max,
                    'y_min': self.data_visualizer.y_min,
                    'y_max': self.data_visualizer.y_max
                }
            }
        return {}

    # Application info
    def get_app_info(self):
        self.license.get_license_day_remaining()
        return {
            "version": self.config.version,
            "activated": self.license.activated,
            "feature": self.license.feature,
            "license_key": self.license.license_key,
            "days_remaining": self.license.days_remaining
        }

    def get_terminal_output(self):
        return self.output_capture.get_output()

    def view_processed_files(self):
        try:
            output_dir = self.config.active_config["output"]
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            files = [f for f in listdir(output_dir) if f.endswith('.cli') and f in self.processing.data_output_dict]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
            return files
        except Exception as e:
            eel.displayError(traceback.format_exc(), "Error")
            return []
        