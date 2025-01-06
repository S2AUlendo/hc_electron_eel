#*******************************************************
# Copyright (C) 2023-2024 Ulendo Technologies, Inc
# This file is part of Ulendo HC Plugin.
# The Ulendo HC Plugin and files contained within the Ulendo HC 
# project folder can not be copied and/or distributed without the 
# express permission of an authorized member of 
# Ulendo Technologies, Inc. 
# For more information contact info@ulendo.io
#*******************************************************

import os
import json
import decimal
import numpy as np
import time
import multiprocessing
from multiprocessing import Process, Value, Array

import requests

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor #is somehow slower than threadpool
from matplotlib.patches import Polygon

from datetime import datetime

import numpy as cpy
import scipy.sparse as sparse
from scipy.sparse import lil_matrix, csr_matrix, spdiags    
from scipy.sparse import spdiags as diags

from scipy.sparse.linalg import eigsh  

TRY_CUDA = False

if (TRY_CUDA == True):
    try:
        # Automatically setup CUPY if it is available
        # 90% reduction when CUDA is enabled running the eigsh method
        # Cupy needs to be installed to use this functionality
        # The version of cupy installed needs to match the CUDA driver
        USE_CUDA = True
        import cupy as cpy                
        # print("Running Ulendo HC with 'cupy' and CUDA")        
        from cupyx.scipy.sparse import csr_matrix as cpy_csr_matrix
        from cupyx.scipy.sparse.linalg import eigsh   

        import cupy_backends.cuda.api._runtime_enum
        import cupy_backends.cuda._softlink
        
    except ModuleNotFoundError:
        USE_CUDA = False
        # print("Running without CUDA")
else:
    USE_CUDA = False


import multiprocessing as mp
CPU_COUNT = mp.cpu_count() - 2
from functools import partial
import logging


# DEBUG_LEVEL = 1 # Save major loop files to numpy
# DEBUG_LEVEL = 2 # Enable major loop print statements
# DEBUG_LEVEL = 3 # Save sub-function files to numpy txt
# DEBUG_LEVEL = 2 # Enable sub function loop print statements
DEBUG_LEVEL = 0

# We need to disable file saves for production
# Set to -1 for release
FILE_LOGGING_LEVEL = -1

# Set to False for Product
# Set this to true to see the output of the Voxelization process
PLOT_LEVEL = False

USE_HATCH_COMPUTE = False
# Setting this variable to True will set the Smart


POINT_RADIUS = 0.5


def set_debug_levels(debug_level:int=5, file_level:int=0, plot_level:bool=False):
    FILE_LOGGING_LEVEL = file_level
    DEBUG_LEVEL = debug_level
    PLOT_LEVEL = plot_level


def debugPrint(context, Level=1):
    # Only print the incoming text if it is a higher priority than 
    if Level < DEBUG_LEVEL:
        print(context)



SERVICE_URL = "https://c85u68p62d.execute-api.us-east-2.amazonaws.com/default/storeexception-staging"
SERVICE_TIMEOUT_THD = 10
ENABLE_SERVER_COMM = True
ENABLE_FILE_SAVE = False


def sortLayers(geometry_matrix, starting_layer, target_layers, unique_z, N_L, N_W, FACTOR):
    """
    This function takes an entire voxelize 3D array and gets the selected number of layers
    starting from the "starting_layer".

    Args:
        geometry_matrix (int):
            3D array containing the stacked voxelized map of each layer.
        starting_layer (int):
            The index of the starting layer.        
        target_layers (int):
            Full path to the STL file to be processed. 
        FACTOR (float):
            slicing resolution.       

    Returns:
        3D array:
            a new array containing the the stacked n number of requested layers
    """

    def f(x):
        return int(float(x)/FACTOR) 

    stackedLayers = np.array([])
    for layer in range(target_layers):
        targetLayer = int(starting_layer + layer)
        
        # Filter out only the values for this layer
        filter = np.asarray([float(unique_z[targetLayer])])
        filtered = geometry_matrix[np.in1d(geometry_matrix[:, 2], filter)]
        
        if DEBUG_LEVEL > 3:  
            print(filtered)

        clean = np.vectorize(f, otypes=[np.ndarray])(filtered)   # apply a function decimal points into whole number positions
        clean = np.array(clean, dtype=int)
        if DEBUG_LEVEL > -1:  
            print (f" Shape of voxeled array: {clean.shape}, {clean.dtype} -- Function sortLayers")

        res = np.zeros((N_L, N_W)) 
        res[clean[:,0], clean[:,1]] = 1     # Create the binary output grid

        if (stackedLayers.size == 0):
            stackedLayers = res
        else :
           stackedLayers = np.dstack((res, stackedLayers))

        if DEBUG_LEVEL > 3:  
            print(f"Stacked Layers: {stackedLayers.shape} -- Function sortLayers")
    
    return stackedLayers


def logErrorData(errorMessage, errorJSON={}):
    """
    Upload the error message to the ulendo server
    """
    if (FILE_LOGGING_LEVEL > 0):
        logErrorData(errorMessage)    



def checkHatchMatrix(hatch_lines = []):
    """
    Generate a matplotlib graph of the hatch data to vizualize the generated solution 
    for the current layer".
    """
    import matplotlib.pyplot as plt
    plt.figure()

    if (len(hatch_lines) == 0):
        hatch_lines = np.loadtxt("output/hatches.txt", delimiter=" ")

    bounding_boxes = np.array([])
    print(hatch_lines.shape)
    # Iterate through the data in hatch_lines    
    for numbers in hatch_lines:                
        x1, y1, x2, y2, layer = numbers
        dx, dy = x2 - x1, y2 - y1
        plt.quiver(x1, y1, dx, dy, angles='xy', scale_units='xy', scale=1, color='b')

    if FILE_LOGGING_LEVEL > 2:
        np.savetxt("staging/bounding.txt", bounding_boxes)

    # Set axis equal for proportions
    plt.axis('equal')

    # Show the plot
    plt.show()


# this code gets a 3D array of a stacked numpy of layers
# That contains the voxlized 2D voxel matrix for N number of layers

def legagySortLayers(geometry_matrix, starting_layer: int = 0, objective_layers_number: int = 2):
    if starting_layer <= objective_layers_number:
        sorted_layers = geometry_matrix[:starting_layer, :, :]
    else:
        sorted_layers = geometry_matrix[starting_layer - objective_layers_number:starting_layer, :, :]
    
    return sorted_layers


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
    
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def check_Authentication(license_key: str = ""):
    URL = "https://hmg3xj3tuc.execute-api.us-east-2.amazonaws.com/staging/license"
    try:
        response = requests.post(URL, 
                json =  json.dumps({"action":"checkLicenseExpired", "license_key":  license_key})
                )

        if ('exception' in response):
            print("An error occurred, check your internet connection and try again")
            print(str(response))
            return False

        __api_server_response = response.json()
        # print(__api_server_response)

        if ('status' in __api_server_response):
            # print(__api_server_response['status'])

            if __api_server_response['status'] == 'success':                

                if ('license_status' in __api_server_response ):
                    if (__api_server_response['license_status'] != 'expired'):
                        return True
                
            return False
        return False
    except Exception as e:
        print("An exception occurred while trying to validate your license")
        return False


def check_key_format(license_key: str = ""):
    attempt_license = str(license_key).replace("-","")    
    if(len(license_key) == 0):
        print("Please provide a valid license before proceeding")

    if (attempt_license.isalnum()):
        return check_Authentication(license_key)
    else:
        print("Ensure that you have provided a valid license. The format of the Key should read XXXX-XXXX-XXXX-XXXX")
        return 0



# Separating out the server component for ease of future modification 
def logErrorData(errorMessage, errorJson):

    print("An errored occured in the HC plugin.. Sending an error log to the server")
    print(errorMessage)
    LOG_TIME = str(datetime.now().strftime('%Y_%m_%d')[:-3])

    functionCall = ""
    if 'location' in errorJson:
        functionCall = errorJson['location']
    
    errordata =  {
            "body": {
            "MACHINEID": "ENGINEERING123",
            "MAKE": "DYNDRITE",
            "MODEL": "LPBFPRO_BETA",
            "CLIENT_ID": "4124sdfafaf",
            "ACCESS_ID": "0123412412",
            "EXCEPTION": str(errorMessage),
            "FUNCTION": functionCall,
            "OPERATION": "STOREERROR",
            "VERSION": "v0.01",
            }
        }
    
    if (ENABLE_FILE_SAVE > 1):
        import os
        directory="C:/Users/Public/Documents/Dyndrite"
        filepath=os.path.join(directory, "log/")
        FILENAME = str(filepath) + "errorlog_"+ str(LOG_TIME) + ".json"
        with open(FILENAME, 'w') as fout: json.dump(errordata, fout, sort_keys=True, indent=4, ensure_ascii=False)

    if ENABLE_SERVER_COMM:
        postreq = requests.post(SERVICE_URL, json=json.dumps(errordata), timeout=SERVICE_TIMEOUT_THD)
        response_body = json.loads(postreq.text)

        if 'exception' in response_body:
            print("An error occurred while processing the error information on the server")
        else:
            print("Error sent to server")


def uploadSequence(sequence):

    print("Sequence successfully generated storing modified sequence on server")
    # print(str(sequence))
    LOG_TIME = str(datetime.now().strftime('%Y_%m_%d')[:-3])
    sequencedata =  {
            "body": {
            "MACHINEID": "ENGINEERING123",
            "MAKE": "DYNDRITE",
            "MODEL": "LPBFPRO_BETA",
            "CLIENT_ID": "4124sdfafaf",
            "ACCESS_ID": "0123412412",
            "EXCEPTION": str(sequence),
            "FUNCTION": "",
            "OPERATION": "STORESEQUENCE",
            "VERSION": "v0.01",
            }
        }
    
    if (ENABLE_FILE_SAVE > 1):
        import os
        directory="C:/Users/Public/Documents/Dyndrite"
        filepath=os.path.join(directory, "log/")
        FILENAME = "log/sequencelog_"+ str(LOG_TIME) + ".json"
        with open(FILENAME, 'w') as fout: json.dump(sequencedata, fout, sort_keys=True, indent=4, ensure_ascii=False)

    if ENABLE_SERVER_COMM:
        postreq = requests.post(SERVICE_URL, json=json.dumps(sequencedata), timeout=SERVICE_TIMEOUT_THD)
        response_body = json.loads(postreq.text)

        if 'exception' in response_body:
            print("An error occurred while processing the error information on the server")
        else:
            print("Error sent to server")




def saveObjects(object, Filename):
    print("saving")
    with open("staging/" + Filename +".json", "w") as outfile:
        json_object = json.dumps(object, cls=DecimalEncoder)
        outfile.write(json_object)

def savePoly(object, Filename):
    print("saving")
    with open("output/" + Filename +".json", "w") as outfile:
        json_object = json.dumps(object, cls=NumpyEncoder)
        outfile.write(json_object)

# Get the dimensions of the bounding box from the dyndrite part object
def getStringfromBB(bounding_box_str):
    """
    Get the bounding box of the STL from the dyndrite string
    """
    import regex as re
    numeric_values = re.findall(r'-?\d+\.\d+', bounding_box_str)

    # Convert the extracted strings to float numbers
    min_x, min_y, min_z, max_x, max_y, max_z = map(float, numeric_values)
    return min_x, min_y, min_z, max_x, max_y, max_z 


def HatchLineWriter(hatch_lines):
    Hatch_Output = open("staging/hatchOutput.txt","w")
    hatch_line_count = 0
    for line in hatch_lines:
        hatch_line_count = hatch_line_count + 1
        for numbers in hatch_lines[line]:
            Hatch_Output.write(str(numbers.tolist()) + "\n")
    Hatch_Output.close()
    print("total hatchlines:", hatch_line_count )

def SequenceWriter(sequence):
    from datetime import datetime

    RUN_TIME = str(datetime.now().strftime('%m_%d_%H_%M')[:-3])
    Hatch_Output = open("output/smartScanSequence" + str(RUN_TIME) + ".txt","w")
    layer_sequence = 0
    for line in sequence:
        layer_sequence = layer_sequence + 1
        for numbers in sequence[line]:
            Hatch_Output.write(str(numbers.tolist()) + ", ")
        Hatch_Output.write("\n")
    Hatch_Output.close()
    print("Layer Sequences: ", layer_sequence )


def PolygonWriter(sequence):
    Hatch_Output = open("staging/polygon.txt","w")
    layer_sequence = 0
    for line in sequence:
        layer_sequence = layer_sequence + 1
        for numbers in sequence[line]:
            Hatch_Output.write(str(numbers) + ", ")
        Hatch_Output.write("\n")
    Hatch_Output.close()
    print("Layer Sequences: ", layer_sequence )


# Append to continuous json file when being called statelessly    
def polygonJSON(DATA_FILENAME, Sequence):
    """
    This file provides support for writing the log data to a json file
    Because the smartscan code is being called statelessly from the 
    dyndrite code, we need to store some data in files.

    Args:
        DATA_FILENAME (String):
            The data to save the file
        Sequence (ndarray):
           a dictionary containing the polygons for a particular layer.

    """
    if FILE_LOGGING_LEVEL > -1:

        try:
            RUN_TIME = str(datetime.now().strftime('%m_%d_%H')[:-3])
            
            DATA_FILENAME = "log/" + str(RUN_TIME) + "_" + DATA_FILENAME
            if not os.path.isfile(DATA_FILENAME):
                with open(DATA_FILENAME, mode='w') as f:
                    f.write(json.dumps(Sequence, indent=1, cls=NumpyEncoder))
            else:
                with open(DATA_FILENAME) as feedsjson:
                    data = json.load(feedsjson)

                data[len(data)] = Sequence
                with open(DATA_FILENAME, mode='w') as f:
                    f.write(json.dumps(data, indent=1, cls=NumpyEncoder))
        except:
            print("Does not have permission to perform file operations")



# Append to continuous json file when being called statelessly    
def appendJSON(DATA_FILENAME, Sequence):
    """
    This file provides support for writing the log data to a json file
    Because the smartscan code is being called statelessly from the 
    dyndrite code, we need to store some data in files.

    Args:
        DATA_FILENAME (String):
            The data to save the file
        Sequence (ndarray):
            a 1D array containing sequence generated by smartScan.

    """
    if FILE_LOGGING_LEVEL > -1:

        try:
            RUN_TIME = str(datetime.now().strftime('%m_%d_%H')[:-3])
            
            DATA_FILENAME = "log/" + str(RUN_TIME) + "_" + DATA_FILENAME
            # entry is numpy array
            entry = str(Sequence.tolist())
            a = []
            if not os.path.isfile(DATA_FILENAME):
                a.append(entry)
                with open(DATA_FILENAME, mode='w') as f:
                    f.write(json.dumps(a, indent=2))
            else:
                with open(DATA_FILENAME) as feedsjson:
                    data = json.load(feedsjson)

                data.append(entry)
                with open(DATA_FILENAME, mode='w') as f:
                    f.write(json.dumps(data, indent=2))

        except:
            print("Does not have permission to perform file operations")




# Simple helper file to reorder the Plylines and hatches within a layer
# In case they are generated out of order as in version 1.4.0 of the Dyndrite software

def reorder_lines(input_text):
    # Split the input text into lines
    lines = input_text.split('\n')

    # Initialize variables
    output_lines = []
    current_layer_lines = []
    hatches_lines = []

    polyline_lines = []

    for line in lines:
        if line.startswith('$$LAYER') or line.startswith('$$GEOMETRYEND'):
            output_lines.extend(hatches_lines)
            output_lines.extend(polyline_lines)
            polyline_lines = []
            hatches_lines = []
            output_lines.append(line)     

        # Process the previous layer (if any)
        elif line.startswith('$$HATCHES'):
            hatches_lines.append(line)
        elif line.startswith('$$POLYLINE'):
            polyline_lines.append(line)
            # Reorder and combine
        else:
            # Lines that don't start with $$HATCHES or $$POLYLINE
            output_lines.append(line)

    # Combine the modified lines back into the final output
    output_text = '\n'.join(output_lines)
    return output_text



# Create a custom delete function because this is not available 
# in the current version of CUDA
# if USE_CUDA == True:
#     import cupy
#     from cupy import _core

#     def delete(arr, indices, axis=None):
#         """
#         Delete values from an array along the specified axis.

#         Args:
#             arr (cupy.ndarray):
#                 Values are deleted from a copy of this array.
#             indices (slice, int or array of ints):
#                 These indices correspond to values that will be deleted from the
#                 copy of `arr`.
#                 Boolean indices are treated as a mask of elements to remove.
#             axis (int or None):
#                 The axis along which `indices` correspond to values that will be
#                 deleted. If `axis` is not given, `arr` will be flattened.

#         Returns:
#             cupy.ndarray:
#                 A copy of `arr` with values specified by `indices` deleted along
#                 `axis`.

#         .. warning:: This function may synchronize the device.

#         .. seealso:: :func:`numpy.delete`.
#         """

#         if axis is None:

#             arr = arr.ravel()

#             if isinstance(indices, cupy.ndarray) and indices.dtype == cupy.bool_:
#                 return arr[~indices]

#             mask = cupy.ones(arr.size, dtype=bool)
#             mask[indices] = False
#             return arr[mask]

#         else:

#             if isinstance(indices, cupy.ndarray) and indices.dtype == cupy.bool_:
#                 return cupy.compress(~indices, arr, axis=axis)

#             mask = cupy.ones(arr.shape[axis], dtype=bool)
#             mask[indices] = False
#             return cupy.compress(mask, arr, axis=axis)


#TODO: Use in new version
# Old implementation threw an error, implementing a slimmer version
def checkConsecutiveArr(data,  stepsize=1):    
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)


