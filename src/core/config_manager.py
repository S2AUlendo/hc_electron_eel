import json
import os
from src.utils.io_utils import persistent_path, get_data_dir, get_persistent_output_dir
from src.utils.constants import config_defaults

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.active_config = None
        self.app_config_path = persistent_path('config.json')
        self.version = ""
        self.load_config()

    def load_config(self):
        try:
            with open(self.app_config_path, 'r') as f:
                self.config = json.load(f)
            
            for key, item in self.config.items():
                if item.get("active", False):
                    self.active_config = item
                    break
            
            if not self.active_config:
                self.initialize_default_config()
                
        except (FileNotFoundError, json.JSONDecodeError):
            self.initialize_default_config()

    def initialize_default_config(self):
        self.config = {
            "default": {
                "data": get_data_dir(),
                "output": get_persistent_output_dir(),
                "license_key": "",
                "feature": 0,
                "active": True
            }
        }
        self.active_config = self.config["default"]
        self.save_config()

    def save_config(self):
        with open(self.app_config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def set_size_limit(self, feature):
        if feature != self.active_config["feature"]:
            self.active_config["feature"] = feature
            self.save_config()

    def change_output_dir(self, new_path):
        if new_path:
            self.output_dir = new_path
            self.config["default"]["active"] = False
            
            if "custom" not in self.config:
                self.config["custom"] = {
                    "data": get_data_dir(),
                    "output": new_path,
                    "active": True
                }
            else:
                self.config["custom"]["output"] = new_path
                self.config["custom"]["active"] = True
            
            self.save_config()
        return self.output_dir