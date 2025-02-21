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
            required_fields = {"name", "kt", "rho", "cp", "h"}
            if not (isinstance(custom_material, dict) and 
                    required_fields.issubset(custom_material.keys())):
                raise ValueError("Invalid material format")
            
            self.materials[material_category][material_key] = custom_material
            
            with open(self.materials_path, 'w') as f:
                f.write(json.dumps(self.materials))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error saving custom material: {e}")
            return False
    
    def edit_material(self, material_category, material_key, new_properties):
        try:
            # Validate input
            if not isinstance(new_properties, dict):
                raise ValueError("Invalid material properties format")
            
            if material_category not in self.materials:
                self.materials[material_category] = {}
                
            if material_key not in self.materials[material_category]:
                self.store_custom_material(material_category, material_key, new_properties)
            else:
                self.materials[material_category][material_key] = new_properties
            
            with open(self.materials_path, 'w') as f:
                f.write(json.dumps(self.materials))
            
            print("Material edited")
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error editing material: {e}")
            return False
        
    def delete_material(self, material_category, material_key):
        try:
            del self.materials[material_category][material_key]
            
            with open(self.materials_path, 'w') as f:
                f.write(json.dumps(self.materials))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error deleting material: {e}")
            return False
        
    def store_custom_machine(self, machine_key, custom_properties):
        try:
            required_fields = {"name", "vs", "P"}
            if not (isinstance(custom_properties, dict) and 
                    required_fields.issubset(custom_properties.keys())):
                raise ValueError("Invalid material format")
            
            self.machines[machine_key] = custom_properties
            with open(self.machines_path, 'w') as f:
                f.write(json.dumps(self.machines))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error saving custom material: {e}")
            return False

    def edit_machine(self, machine_key, new_properties):
        try:
            # Validate input
            if not isinstance(new_properties, dict):
                raise ValueError("Invalid machine properties format")
            
            if machine_key not in self.machines:
                self.store_custom_machine(machine_key, new_properties)
            else:
                self.machines[machine_key] = new_properties
            
            with open(self.machines_path, 'w') as f:
                f.write(json.dumps(self.machines))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error editing machine: {e}")
            return False
        
    def delete_machine(self, machine_key):
        try:
            del self.machines[machine_key]
            
            with open(self.machines_path, 'w') as f:
                f.write(json.dumps(self.machines))
                
            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error deleting material: {e}")
            return False
            