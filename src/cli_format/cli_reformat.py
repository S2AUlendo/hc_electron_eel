# Created by SThompson for Ulendo Technolpoiges inc
# Based on the code developed by Chuan He
# Convert the CLI+ format output by the Dyndrite LPBF Pro software
# and reformat it into the same format that is expected by Smart Scan

import os
import traceback
import sys

from datetime import datetime
from src.ulendohc_core.smartScanCore import *
from src.ulendohc_core.util import *

FACTOR = 1 
LAYER_GROUP = 10

dx = FACTOR # mm
dy = FACTOR # mm
        
def parse_cli_header(data):
    """Parse CLI file header section"""
    def extract_value(prefix: str) -> str:
        for line in data:
            if line.startswith(prefix):
                return line.split('/')[1].strip()
        raise ValueError(f"Missing {prefix} in CLI header")

    # Extract and convert values
    units = float(extract_value("$$UNITS"))
    version = int(extract_value("$$VERSION"))
    date = extract_value("$$DATE")
    dimensions = extract_value("$$DIMENSION")
    layers = int(extract_value("$$LAYERS"))
    label = extract_value("$$LABEL")
    return [units, version, date, dimensions, layers, label]

def retrieve_file_data(layer_indices, hatch_indices, polyline_indices, data):
    hatch_lines= {}
    layer_data = {}
    
    x_min_value = []
    x_max_value = []
    y_min_value = []
    y_max_value = []
    
    for layer_num in range(len(layer_indices)-1):
        hatch_data = {}
        hatch_feature_indices = [i for i in hatch_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
        polyline_feautre_indices = [i for i in polyline_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
        
        # Process each feature index
        for kk in range(len(hatch_feature_indices)):
            hatches = data[hatch_feature_indices[kk]]
            hatch_data[kk] = hatches
            strCell = hatches.split(',')
            hatches = list(map(float, strCell[2:]))
            
            x_max = np.max(hatches[::4])
            x_min = np.min(hatches[2::4])
            y_max = np.max(hatches[1::4])
            y_min = np.min(hatches[3::4])
            x_min_value.append(x_min)
            x_max_value.append(x_max)
            y_min_value.append(y_min)
            y_max_value.append(y_max)
            
            numbers = np.array([])
            
            if (numbers.size == 0):
                numbers = np.array([x_max, y_max, x_min, y_min, kk])
            else:                     
                numbers = np.vstack((numbers, np.array([x_max, y_max, x_min, y_min, kk])))

            if (len(numbers.shape) == 1):
                numbers = np.reshape(numbers, (-1, 5))
            
            if layer_num not in hatch_lines:
                hatch_lines[layer_num] = numbers
            else:
                hatch_lines[layer_num] = np.vstack((hatch_lines[layer_num], numbers))
        
        # Store per-layer data
        layer_data[layer_num] = {
            'hatch_data': hatch_data,
            'hatch_feature_indices': hatch_feature_indices,
            'polyline_feautre_indices': polyline_feautre_indices
        }
        
    return x_max_value, x_min_value, y_max_value, y_min_value, layer_data, hatch_lines

def optimize_and_write(ori_filename, opt_filename, filelocation, progress, layer_data, data, selected_material, selected_machine, layer_indices, hatch_lines):
    Sorted_layers = np.array([])
    v0_evInit = None
    totaltracker = 0
    output_dir = filelocation
    
    units, version, date, dimension, layers, label = parse_cli_header(data)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    progress['msg'] = f"Creating output file..."
    ori_path = os.path.join("data", ori_filename)
    output_file = os.path.join(output_dir, opt_filename)
    
    try:
        with open(ori_path, "+a") as ori_file ,open(output_file, "+a") as opt_file:
            for layer_num in range(len(layer_indices)-1):
                progress['msg'] = f"Processing layer {layer_num}/{len(layer_indices) - 1}"
                if layer_num == 0: 
                    ori_file.write(f"$$HEADERSTART\n")
                    ori_file.write(f"$$ASCII\n$$UNITS/{units}\n$$VERSION/{version}\n$$DATE/{date}\n$$DIMENSION/{dimension}\n$$LAYERS/{layers}\n$$LABEL/{label}\n")
                    ori_file.write(f"$$HEADEREND\n")
                    
                    opt_file.write(f"$$HEADERSTART\n")
                    opt_file.write(f"$$ASCII\n$$UNITS/{units}\n$$VERSION/{version}\n$$DATE/{date}\n$$DIMENSION/{dimension}\n$$LAYERS/{layers}\n$$LABEL/{label}\n")
                    opt_file.write(f"$$HEADEREND\n")
                    
                if (layer_num in hatch_lines):
                    
                    if hatch_lines[layer_num].shape[0] < 3:
                        optimized_Sequence = hatch_lines[layer_num][:, -1]
                        R_opt = 0
                        R_ori = 0
                        
                    else:
                        totaltracker = int(hatch_lines[layer_num].shape[0]) + totaltracker
                                            
                        new_layer, x_size, y_size = convert_hatch_to_voxel(hatch_lines[layer_num], 67, 1, 1)   
                        Objective_layers = 2     
                        
                        print(f"Total Hatch Lines {hatch_lines[layer_num].shape}, at layer {layer_num}")

                        Sorted_layers = stack_layers(new_layer, Sorted_layers, Objective_layers)
                        print(f"Matrix shape {Sorted_layers.shape}, at layer {layer_num}")

                        try:
                            optimized_Sequence, v0_evInit, R_opt, R_ori = smartScanCore(numbers_set=hatch_lines[layer_num], 
                                                                                        Sorted_layers=Sorted_layers, 
                                                                                        dx=dx, dy=dy, 
                                                                                        reduced_order=50, 
                                                                                        kt=float(selected_material['kt']),
                                                                                        rho=float(selected_material['rho']),
                                                                                        cp=float(selected_material['cp']),
                                                                                        vs=float(selected_machine['vs']),
                                                                                        h=float(selected_material['h']),
                                                                                        P=float(selected_machine['P']),
                                                                                        v0_ev=v0_evInit
                                                                                        )  
                        except Exception as e:
                            # if unable to find solution just original sequence
                            optimized_Sequence = hatch_lines[layer_num][:, -1]
                            R_opt = 0
                            R_ori = 0
                    
                    ori_file.write(f"$$LAYER/{layer_num:.3f}\n")
                    opt_file.write(f"$$LAYER/{layer_num:.3f}\n")
                    
                    R_ori_str = str(R_ori)
                    R_opt_str = str(R_opt)
                    
                    ori_file.write(f"//R/{R_ori_str}//\n")
                    opt_file.write(f"//R/{R_opt_str}//\n")
                    
                    # Access stored per-layer data
                    layer_info = layer_data[layer_num]
                    
                    for ori_seq in hatch_lines[layer_num][:, -1]:
                        ori_file.write(f"{layer_info['hatch_data'][ori_seq]}\n")
                        
                    for opt_seq in optimized_Sequence:
                        opt_file.write(f"{layer_info['hatch_data'][opt_seq]}\n")
                        
                    for polyline in layer_info['polyline_feautre_indices']:
                        opt_file.write(f"{data[polyline]}\n")
                    
                    progress['value'] = (layer_num + 1) / len(layer_indices)
        
            progress['msg'] = "Finishing..."
            ori_file.write("$$GEOMETRYEND\n")
            opt_file.write("$$GEOMETRYEND\n")
    
    except Exception as e:
        print(traceback.format_exc())
        print(f"Error: {e}")
        raise e
    
def convertDYNCliFile(filecontent, inputname, outputname, filelocation, progress, selected_material, selected_machine, max_size=1250):
    
    progress["msg"] = "Retrieving file information..."
    data = filecontent.splitlines()
    
    layer_indices = np.where(np.char.startswith(data, "$$LAYER/"))[0]    
    hatch_indices = np.where(np.char.startswith(data, "$$HATCHES/"))[0]
    print(f"Hatch Indicies {len(hatch_indices)}")

    polyline_indices = np.where(np.char.startswith(data, "$$POLYLINE/"))[0]
    print(f"Polyline Indicies {len(polyline_indices)}")
    
    layer_indices = np.array(layer_indices)
    hatch_indices = np.array(hatch_indices)
    layer_indices = np.append(layer_indices, hatch_indices[-1] + 1)
    print(f"Layer Indicies {len(layer_indices)}")    

    # Retrieve file data
    x_max_value, x_min_value, y_max_value, y_min_value, layer_data, hatch_lines = retrieve_file_data(layer_indices, hatch_indices, polyline_indices, data)
    
    # Calculate dimensions
    dimension_x = np.max(x_max_value) - np.min(x_min_value)
    dimension_y = np.max(y_max_value) - np.min(y_min_value)
    build_area = dimension_x * dimension_y
    
    if build_area < 0:
        progress["error"] = "Error: Build area is less than 0"
        return
    
    if build_area > max_size:
        progress["error"] = f"Error: Build area is more than {max_size}!\nPlease navigate to the help menu to upgrade your current license to support a bigger build volume."
        return
    
    # Optimize and write output file
    optimize_and_write(inputname, outputname, filelocation, progress, layer_data, data, selected_material, selected_machine, layer_indices, hatch_lines)
    
    minimum_x = np.min(x_min_value)
    minimum_y = np.min(y_min_value)

    # Iterate over layers
    for ii in range(len(layer_indices)-1):
        if ii in hatch_lines:
            hatch_lines[ii][:, [0, 2]] = hatch_lines[ii][:, [0, 2]] - minimum_x
            hatch_lines[ii][:, [1, 3]] = hatch_lines[ii][:, [1, 3]] - minimum_y
            
    progress["msg"] = "Completed"
    return hatch_lines, dimension_x, dimension_y
    