import json
from src.utils.io_utils import persistent_path
from src.utils.constants import material_defaults, machine_defaults

class DataManager:
    def __init__(self):
        self.materials = {}
        self.machines = {}
        self.materials_path = persistent_path('materials.json')
        self.machines_path = persistent_path('machines.json')
        self.load_materials()
        self.load_machines()

    def load_materials(self):
        try:
            with open(self.materials_path, 'r') as f:
                self.materials = json.load(f)
        except FileNotFoundError:
            self.initialize_default_materials()

    def initialize_default_materials(self):
        self.materials = material_defaults
        with open(self.materials_path, 'w') as f:
            json.dump(self.materials, f)

    def load_machines(self):
        try:
            with open(self.machines_path, 'r') as f:
                self.machines = json.load(f)
        except FileNotFoundError:
            self.initialize_default_machines()

    def initialize_default_machines(self):
        self.machines = machine_defaults
        with open(self.machines_path, 'w') as f:
            json.dump(self.machines, f)

    def store_custom_material(self, material_category, material_key, custom_material):
        try:
            # Validate input
            if not isinstance(custom_material, dict) or "name" not in custom_material:
                raise ValueError("Invalid custom material format")
            self.materials[material_category][material_key] = custom_material
            
            with open(self.materials_path, 'w') as f:
                f.write(json.dumps(self.materials))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error saving custom material: {e}")
            return False
        
        
    def store_custom_machine(self, machine_key, custom_properties):
        try:
            # Validate input
            if not isinstance(custom_properties, dict) or "name" not in custom_properties:
                raise ValueError("Invalid custom machine format")
            self.machines[machine_key] = custom_properties
            
            with open(self.machines_path, 'w') as f:
                f.write(json.dumps(self.machines))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error saving custom material: {e}")
            return False
