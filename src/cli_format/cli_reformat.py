# Created by SThompson for Ulendo Technolpoiges inc
# Based on the code developed by Chuan He
# Convert the CLI+ format output by the Dyndrite LPBF Pro software
# and reformat it into the same format that is expected by Smart Scan

import os
import traceback
import sys
import io
from src.output_capture.mp_output import CustomMPOutput
from datetime import datetime
from src.ulendohc_core.smartScanCore import *
from src.ulendohc_core.util import *
from src.exceptions.exceptions import OverLimitException

class CLIReformat:
    def __init__(self, data, output_location, original_name, output_name, progress, selected_material, selected_machine, feature=2000, mp_output_queue=None):
        # Configuration parameters
        self.FACTOR = 1
        self.LAYER_GROUP = 10
        self.dx = self.FACTOR  # mm
        self.dy = self.FACTOR  # mm
        self.feature = feature
        
        self.data = data.splitlines()
        self.filelocation = output_location
        self.ori_filename = original_name
        self.opt_filename = output_name
        
        # File processing state
        self.units = 0
        self.version = 0
        self.date = ""
        self.dimension = ""
        self.layers = 0
        self.label = ""
        self.dimension_x = 0
        self.dimension_y = 0
        self.build_area = 0
        
        # Geometry self.data
        self.layer_indices = []
        self.hatch_indices = []
        self.polyline_indices = []
        self.hatch_lines = {}
        self.layer_data = {}
        self.x_max_values = []
        self.x_min_values = []
        self.y_max_values = []
        self.y_min_values = []
        
        # External interfaces
        self.mp_output_queue = mp_output_queue
        self.progress = progress
        self.selected_material = selected_material
        self.selected_machine = selected_machine
        
        self.parse_cli_header()
        self.retrieve_indices()
    
    def retrieve_indices(self):
        
        self.layer_indices = np.where(np.char.startswith(self.data, "$$LAYER/"))[0]    
        self.hatch_indices = np.where(np.char.startswith(self.data, "$$HATCHES/"))[0]
        self.display_message(f"Hatch Indicies {len(self.hatch_indices)}")

        self.polyline_indices = np.where(np.char.startswith(self.data, "$$POLYLINE/"))[0]
        self.display_message(f"Polyline Indicies {len(self.polyline_indices)}")
        
        self.layer_indices = np.array(self.layer_indices)
        self.hatch_indices = np.array(self.hatch_indices)
        self.layer_indices = np.append(self.layer_indices, self.hatch_indices[-1] + 1)
        self.display_message(f"Layer Indicies {len(self.layer_indices)}") 
           
    def parse_cli_header(self):
        """Parse CLI file header section"""
        def extract_value(prefix: str) -> str:
            for line in self.data:
                if line.startswith(prefix):
                    return line.split('/')[1].strip()
            raise ValueError(f"Missing {prefix} in CLI header")

        # Extract and convert values
        self.units = float(extract_value("$$UNITS"))
        self.version = int(extract_value("$$VERSION"))
        self.date = extract_value("$$DATE")
        self.dimension = extract_value("$$DIMENSION")
        self.layers = int(extract_value("$$LAYERS"))
        self.label = extract_value("$$LABEL")
        
    def retrieve_file_data(self):
        for layer_num in range(len(self.layer_indices) - 1):
            hatch_data = {}
            hatch_feature_indices = [
                i for i in self.hatch_indices 
                if self.layer_indices[layer_num] < i < self.layer_indices[layer_num + 1]
            ]
            polyline_feature_indices = [
                i for i in self.polyline_indices 
                if self.layer_indices[layer_num] < i < self.layer_indices[layer_num + 1]
            ]

            for kk, hatch_idx in enumerate(hatch_feature_indices):
                hatches = self.data[hatch_idx]
                hatch_data[kk] = hatches
                str_cell = hatches.split(',')
                hatches = list(map(float, str_cell[2:]))

                x_max = np.max(hatches[::4])
                x_min = np.min(hatches[2::4])
                y_max = np.max(hatches[1::4])
                y_min = np.min(hatches[3::4])

                self.x_min_values.append(x_min)
                self.x_max_values.append(x_max)
                self.y_min_values.append(y_min)
                self.y_max_values.append(y_max)

                numbers = np.array([x_max, y_max, x_min, y_min, kk])

                if layer_num not in self.hatch_lines:
                    self.hatch_lines[layer_num] = numbers
                else:
                    self.hatch_lines[layer_num] = np.vstack((self.hatch_lines[layer_num], numbers))

            self.layer_data[layer_num] = {
                'hatch_data': hatch_data,
                'hatch_feature_indices': hatch_feature_indices,
                'polyline_feature_indices': polyline_feature_indices
            }

    def optimize_and_write(self):
        Sorted_layers = np.array([])
        v0_evInit = None
        totaltracker = 0
        output_dir = self.filelocation

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.progress['msg'] = f"Creating output file..."
        ori_path = os.path.join("data", self.ori_filename)
        output_file = os.path.join(output_dir, self.opt_filename)
        
        try:
            with open(ori_path, "+a") as ori_file ,open(output_file, "+a") as opt_file:
                for layer_num in range(len(self.layer_indices)-1):
                    self.progress['msg'] = f"Processing layer {layer_num}/{len(self.layer_indices) - 1}"
                    if layer_num == 0: 
                        ori_file.write(f"$$HEADERSTART\n")
                        ori_file.write(f"$$ASCII\n$$UNITS/{self.units}\n$$VERSION/{self.version}\n$$DATE/{self.date}\n$$DIMENSION/{self.dimension}\n$$LAYERS/{self.layers}\n$$LABEL/{self.label}\n")
                        ori_file.write(f"$$HEADEREND\n")
                        
                        opt_file.write(f"$$HEADERSTART\n")
                        opt_file.write(f"$$ASCII\n$$UNITS/{self.units}\n$$VERSION/{self.version}\n$$DATE/{self.date}\n$$DIMENSION/{self.dimension}\n$$LAYERS/{self.layers}\n$$LABEL/{self.label}\n")
                        opt_file.write(f"$$HEADEREND\n")
                        
                    if (layer_num in self.hatch_lines):
                        
                        if self.hatch_lines[layer_num].shape[0] < 3:
                            optimized_Sequence = self.hatch_lines[layer_num][:, -1]
                            R_opt = 0
                            R_ori = 0
                            
                        else:
                            totaltracker = int(self.hatch_lines[layer_num].shape[0]) + totaltracker
                                                
                            new_layer, x_size, y_size = convert_hatch_to_voxel(self.hatch_lines[layer_num], 67, 1, 1)   
                            Objective_layers = 2     
                            
                            self.display_message(f"Total Hatch Lines {self.hatch_lines[layer_num].shape}, at layer {layer_num}")

                            Sorted_layers = stack_layers(new_layer, Sorted_layers, Objective_layers)
                            self.display_message(f"Matrix shape {Sorted_layers.shape}, at layer {layer_num}")

                            try:
                                optimized_Sequence, v0_evInit, R_opt, R_ori = smartScanCore(numbers_set=self.hatch_lines[layer_num], 
                                                                                            Sorted_layers=Sorted_layers, 
                                                                                            dx=self.dx, dy=self.dy, 
                                                                                            reduced_order=50, 
                                                                                            kt=float(self.selected_material['kt']),
                                                                                            rho=float(self.selected_material['rho']),
                                                                                            cp=float(self.selected_material['cp']),
                                                                                            vs=float(self.selected_machine['vs']),
                                                                                            h=float(self.selected_material['h']),
                                                                                            P=float(self.selected_machine['P']),
                                                                                            v0_ev=v0_evInit
                                                                                            )  
                            except Exception as e:
                                # if unable to find solution just original sequence
                                optimized_Sequence = self.hatch_lines[layer_num][:, -1]
                                R_opt = 0
                                R_ori = 0
                        
                        ori_file.write(f"$$LAYER/{layer_num:.3f}\n")
                        opt_file.write(f"$$LAYER/{layer_num:.3f}\n")
                        
                        R_ori_str = str(R_ori)
                        R_opt_str = str(R_opt)
                        
                        ori_file.write(f"//R/{R_ori_str}//\n")
                        opt_file.write(f"//R/{R_opt_str}//\n")
                        
                        # Access stored per-layer self.data
                        layer_info = self.layer_data[layer_num]
                        
                        for ori_seq in self.hatch_lines[layer_num][:, -1]:
                            ori_file.write(f"{layer_info['hatch_data'][ori_seq]}\n")
                            
                        for opt_seq in optimized_Sequence:
                            opt_file.write(f"{layer_info['hatch_data'][opt_seq]}\n")
                            
                        for polyline in layer_info['polyline_feature_indices']:
                            opt_file.write(f"{self.data[polyline]}\n")
                        
                        self.progress['value'] = (layer_num + 1) / len(self.layer_indices)
            
                self.display_message("Finishing...")
                ori_file.write("$$GEOMETRYEND\n")
                opt_file.write("$$GEOMETRYEND\n")
        
        except Exception as e:
            self.display_message(traceback.format_exc())
            self.display_message(f"Error: {e}")
            raise e
    
    def get_and_check_dimensions(self):
        self.dimension_x = np.max(self.x_max_values) - np.min(self.x_min_values)
        self.dimension_y = np.max(self.y_max_values) - np.min(self.y_min_values)
        self.build_area = self.dimension_x * self.dimension_y
        
        if self.build_area < 0:
            self.progress["error"] = "Error: Build area is less than 0"
            return False
        
        if self.build_area > self.feature:
            self.progress["error"] = f"Error: Build area is more than {self.feature}!\nPlease navigate to the help menu to upgrade your current license to support a bigger build volume."
            return False
        
        return True
    
    def display_message(self, message):
        print(message)
        
    def convert_dync_cli_file(self):
        try:
            sys.stdout = CustomMPOutput(self.mp_output_queue)
            
            self.progress["msg"] = "Retrieving file information..."

            # Retrieve file self.data
            self.retrieve_file_data()
            
            # Calculate dimensions
            is_valid = self.get_and_check_dimensions()
            
            if not is_valid:
                raise OverLimitException("Build dimensions exceed allowed limits. Please upgrade your license key to increase the build volume limit.")
            
            # Optimize and write output file
            self.optimize_and_write()
            
            minimum_x = np.min(self.x_min_values)
            minimum_y = np.min(self.y_min_values)

            # Iterate over layers
            for ii in range(len(self.layer_indices)-1):
                if ii in self.hatch_lines:
                    self.hatch_lines[ii][:, [0, 2]] = self.hatch_lines[ii][:, [0, 2]] - minimum_x
                    self.hatch_lines[ii][:, [1, 3]] = self.hatch_lines[ii][:, [1, 3]] - minimum_y
                    
            self.progress["msg"] = "Completed"

        except OverLimitException as e:
            return {
                "status": "error",
                "error_type": "OverLimitException",
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "GenericException",
                "message": str(e)
            }
        