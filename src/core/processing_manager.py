import json
import eel
import traceback
from datetime import datetime
from multiprocessing import Pool, Manager
from src.utils.io_utils import persistent_path
from src.cli_format.cli_reformat import *

class ProcessingManager:
    def __init__(self, config_manager, data_manager):
        self.config_manager = config_manager
        self.data_manager = data_manager
        self._manager = Manager()
        self._pool = Pool()
        self.futures = {}
        self.progress = {}
        
        # Initialize shared resources
        self.data_output_dict = self.load_data_output_dict()

    def load_data_output_dict(self):
        data_output_dict_path = persistent_path("dictionary.json")
        try:
            with open(data_output_dict_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data_output_dict(self):
        with open(persistent_path("dictionary.json"), "w") as file:
            json.dump(self.data_output_dict, file)

    def convert_cli_file(self, filecontent, filename, selected_material, selected_material_category, selected_machine):
        try:
            # Deserialize if needed
            if isinstance(selected_material, str):
                selected_material = json.loads(selected_material)
            if isinstance(selected_machine, str):
                selected_machine = json.loads(selected_machine)

            # Material handling
            material_key = "_".join(selected_material["name"].strip().split())
            if material_key not in self.data_manager.materials[selected_material_category]:
                self.data_manager.store_custom_material(
                    selected_material_category,
                    material_key,
                    selected_material
                )

            # Machine handling
            machine_key = "_".join(selected_machine["name"].strip().split())
            if machine_key not in self.data_manager.machines:
                self.data_manager.store_custom_machine(machine_key, selected_machine)

            # File naming
            timestamp = datetime.now().strftime('%m-%d-%Y_%H-%M-%S')
            ori_name = f"{filename[:-4].strip()}-{timestamp}.cli"
            output_name = f"{filename[:-4].strip()}-hc-{timestamp}.cli"
            
            # Update tracking dictionary
            self.data_output_dict[output_name] = ori_name
            self.save_data_output_dict()

            # Initialize progress tracking
            self.progress[filename] = self._manager.dict()
            self.progress[filename].update({
                'value': 0,
                'msg': "",
                'error': ""
            })

            # Submit task
            async_result = self._pool.apply_async(
                convertDYNCliFile,
                args=(
                    filecontent,
                    ori_name,
                    output_name,
                    self.config_manager.output_dir,
                    self.progress[filename],
                    selected_material,
                    selected_machine,
                    self.config_manager.features[self.config_manager.active_feature]
                )
            )
            self.futures[filename] = async_result
            return {"status": "started", "message": "Task started successfully"}

        except Exception as e:
            error_msg = f"Error starting task: {str(e)}"
            tb = traceback.format_exc()
            eel.displayError(tb, "Processing Error")

    def get_task_status(self, filename):
        if filename not in self.futures:
            return {"status": "not_found"}

        future = self.futures[filename]
        if not future.ready():
            progress_data = dict(self.progress[filename])
            if progress_data['msg']:
                eel.displayStatus(progress_data['msg'])
            return {
                "status": "running",
                "progress": progress_data['value'],
                "message": progress_data['msg']
            }

        try:
            result = future.get()
            progress_data = dict(self.progress[filename])
            if progress_data['error']:
                eel.displayError(progress_data['error'], "Processing Error")
            return {"status": "completed", "result": result}
            
        except Exception as e:
            tb = traceback.format_exc()
            eel.displayError(tb, "Processing Error")
            return {"status": "error", "message": str(e)}