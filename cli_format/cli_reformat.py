# Created by SThompson for Ulendo Technolpoiges inc
# Based on the code developed by Chuan He
# Convert the CLI+ format output by the Dyndrite LPBF Pro software
# and reformat it into the same format that is expected by Smart Scan

import os
import json

from datetime import datetime
from ulendohc_core.smartScanCore import *
from ulendohc_core.util import *
import eel

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

def display_status(status_message):
    eel.displayStatus(status_message)
    print(status_message)
    
def convertDYNCliFile(filecontent, filename, outputname, filelocation, progress, selected_material):
    Sorted_layers = np.array([])
    v0_evInit = None
    
    display_status("Retrieving file information...")
    data = filecontent.splitlines()
    # with open(filename, 'r') as f:
    #     data = f.readlines()
        
    # fileFound = os.path.isfile(filename)
    # print(f" File status: {fileFound}")
    # print(f" Total rows: {len(data)}")
    
    units, version, date, dimension, layers, label = parse_cli_header(data)
    print(f"Units: {units}, Version: {version}, Date: {date}, Dimension: {dimension}, Layers: {layers}, Label: {label}")
    
    # Assuming 'data' is a list or array containing strings
    # Find indices where strings start with '$$LAYER/'
    layer_indices = np.where(np.char.startswith(data, "$$LAYER/"))[0]    

    # Find indices where strings start with '$$HATCHES/'
    hatch_indices = np.where(np.char.startswith(data, "$$HATCHES/"))[0]
    print(f"Hatch Indicies {len(hatch_indices)}")

    polyline_indices = np.where(np.char.startswith(data, "$$POLYLINE/"))[0]
    print(f"Polyline Indicies {len(polyline_indices)}")
    
    # Combine layer and hatch indices
    layer_indices = np.array(layer_indices)
    hatch_indices = np.array(hatch_indices)
    layer_indices = np.append(layer_indices, hatch_indices[-1]+ 1)
    print(f"Layer Indicies {len(layer_indices)}")    

    # Initialize an empty dictionary for hatch lines
    hatch_lines = {}

    # Initialize empty lists for x and y min/max values
    x_min_value = []
    x_max_value = []
    y_min_value = []
    y_max_value = []

    totaltracker = 0
    
    output_dir = filelocation
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Then use os.path.join for file path
    display_status("Creating output file...")
    output_file = os.path.join(output_dir, outputname)
    
    with open(output_file, "a+") as outfile:
        # Iterate over layers
        for layer_num in range(len(layer_indices)-1):
            display_status(f"Processing layer {layer_num}/{len(layer_indices) - 1}")
            # Find feature indices within the current layer
            hatch_data = {}
            hatch_feature_indices = [i for i in hatch_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
            polyline_feautre_indices = [i for i in polyline_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
            
            # print(feature_indices)
            if layer_num == 0: 
                outfile.write(f"$$HEADERSTART\n")
                outfile.write(f"$$ASCII\n$$UNITS/{units}\n$$VERSION/{version}\n$$DATE/{date}\n$$DIMENSION/{dimension}\n$$LAYERS/{layers}\n$$LABEL/{label}\n")
                outfile.write(f"$$HEADEREND\n")
            
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
                
                # print(f"X Max: {x_max}, X Min: {x_min}, Y Max: {y_max}, Y Min: {y_min}")
                numbers = np.array([])
                
                if (numbers.size == 0):
                    numbers = np.array([x_max, y_max, x_min, y_min, kk])
                    # print(numbers.shape)
                else:                     
                    numbers = np.vstack((numbers, np.array([x_max, y_max, x_min, y_min, kk])))

                # Prevent a 1D a array from getting past this point and causing an error
                if (len(numbers.shape) == 1):
                    numbers = np.reshape(numbers, (-1, 5))
                
                # Initialize hatch_lines if not already done
                if layer_num not in hatch_lines:
                    # hatch_lines[layer_num] = numbers
                    hatch_lines[layer_num] = numbers
                else:
                    # Append numbers to hatch_lines
                    hatch_lines[layer_num] = np.vstack((hatch_lines[layer_num], numbers))

            if (layer_num in hatch_lines):
                totaltracker = int(hatch_lines[layer_num].shape[0]) + totaltracker
                # print(hatch_lines[layer_num].shape , "total : ", totaltracker)
                                    
                new_layer, x_size, y_size = convert_hatch_to_voxel(hatch_lines[layer_num], 67, 1, 1)   
                Objective_layers = 2     
                
                # Create super-features
                print(f"Total Hatch Lines {hatch_lines[layer_num].shape}, at layer {layer_num}")

                Sorted_layers = stack_layers(new_layer, Sorted_layers, Objective_layers)
                print(f"Matrix shape {Sorted_layers.shape}, at layer {layer_num}")
                
                tic = time.perf_counter()
                optimized_Sequence, v0_evInit, R_opt, R_ori = smartScanCore(numbers_set=hatch_lines[layer_num], 
                                                                            Sorted_layers=Sorted_layers, 
                                                                            dx=dx, dy=dy, 
                                                                            reduced_order=50, 
                                                                            kt=float(selected_material['kt']),
                                                                            rho=float(selected_material['rho']),
                                                                            cp=float(selected_material['cp']),
                                                                            vs=float(selected_material['vs']),
                                                                            h=float(selected_material['h']),
                                                                            P=float(selected_material['P']),
                                                                            v0_ev=v0_evInit, 
                                                                            )  
                
                outfile.write(f"$$LAYER/{layer_num:.3f}\n")
                outfile.write(f"//R_VALUES/{R_opt:.3f}, {R_ori:.3f}//\n")
                for polyline in polyline_feautre_indices:
                    outfile.write(f"{data[polyline]}\n")
                    
                for opt_seq in optimized_Sequence:
                    outfile.write(f"{hatch_data[opt_seq]}\n")
                    
                progress[filename] = (layer_num + 1) / len(layer_indices)
                
        display_status("Finishing...")
        outfile.write("$$GEOMETRYEND\n")
        

    # Calculate dimensions
    dimension_x = np.max(x_max_value) - np.min(x_min_value)
    dimension_y = np.max(y_max_value) - np.min(y_min_value)

    minumum_x = np.min(x_min_value)
    minumum_y = np.min(x_min_value)
    # print("minimum x: ", minumum_x, "minimum y : ", minumum_y)

    
    # print(f"Layer Lines {len(hatch_lines)} layer num {layer_num}")
    # print(f"Hatch Data {hatch_data} ")

    # Iterate over layers
    for ii in range(len(layer_indices)-1):
        if ii in hatch_lines:
            # Update x coordinates
            hatch_lines[ii][:, [0, 2]] = hatch_lines[ii][:, [0, 2]] - minumum_x
            # Update y coordinates
            hatch_lines[ii][:, [1, 3]] = hatch_lines[ii][:, [1, 3]] - minumum_y
    
    return hatch_lines, dimension_x, dimension_y