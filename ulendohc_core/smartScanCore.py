#*******************************************************
# Copyright (C) 2023-2024 Ulendo Technologies, Inc
# This file is part of Ulendo HC Plugin.
# The Ulendo HC Plugin and files contained within the Ulendo HC 
# project folder can not be copied and/or distributed without the 
# express permission of an authorized member of 
# Ulendo Technologies, Inc. 
# For more information contact info@ulendo.io
#*******************************************************


from ulendohc_core.util import *
import ulendohc_core.stateMatrixConstruction as SMC
from numba import jit

class smartscanServer():
    # Class does not provide an extra benefit aside from auth
    # function is called REST-like with no saved state

    def __init__(self ):
        self.__counter = 1  # C
        self.__valid_license = True


def stack_layers(newLayer=np.array([]), PreviousLayers =np.array([]), n_layers:int = 2):
        """
        Stack, N number of previous layers for smartScan

        Args:
            newLayers (ndarray):
                The sequence that is returned by SmartScan Core (Un-offset hatches)
            n_layers (int):
                the number of layers that should be used in the optimization  

        Returns:
            numpy.ndarray:
                A 3D array of the sorted Voxelized layers in the order that SS Core expects
        """

        if (PreviousLayers.size == 0 or (newLayer.shape[0] != PreviousLayers.shape[0]) or (newLayer.shape[1] != PreviousLayers.shape[1])):
            # Initialize an empty 3D layer when the program is started
            # If the size of the new layer is different from the previous layer then 
            # we need to re-initialize the history so that the code still runs as expected
            PreviousLayers = np.zeros((newLayer.shape[0], newLayer.shape[1], n_layers))
        
        debugPrint(f"stackLayers - New Layers Shape {newLayer.shape} Previous Layers Shape {PreviousLayers.shape}", 0)
        # Get the first layer of the newly generated grid, and get N-1 of the grid for the previous layers
        PreviousLayers = np.dstack((newLayer[:,:,0:1], PreviousLayers[:,:,0:n_layers-1]))
        
        return PreviousLayers


def calculate_1D_offset(row, column, COLUMNS_PER_ROW):
    return row * COLUMNS_PER_ROW + column


def process_points(hatch_point, coord):
    point_Radius = POINT_RADIUS
    x, y = coord
    
    # Iterate all of the points in the list
    for point in hatch_point:
        i, j, r = point
        # The points are sorted in order, if we reach a value that is greater than the 
        # X,Y coord we need to check, we can assume all of the points after this 
        # will return false
        if(i > x+point_Radius):
            # return x, y, False
            if(j > y+point_Radius):
                return x, y, False
        if (x-point_Radius < i < x+point_Radius) and (y-point_Radius < j < y+point_Radius):
            return x, y, True
    return x, y, False


# TODO: Time whether it is faster to convert the hatches or the polygons
def convert_points_to_voxel(exposure_points = np.array([]), bbox= np.array([]), x_resolution:float = 1, y_resolution:float = 1):

    """
    This function converts the hatches supplied in the bounding box format
    directly to a voxelized map

    Args:
        hatch_lines (ndarry):
            an ndarray that contains an order list of hatches
        rotation (float):
            The rotation used to slice the hatches, in degrees
        x_resolution (float):
            Width of the slice thickness
        y_resolution (string):
            Path to the STL that needs to be processed

    Returns:
        numpy.ndarray:
            A binary grid containing the 1,0s, where a 1 represents an area of the area where 
            there is material present, i.e. is occupied by the STL

    """
    # print(bbox)
    # Get the bounding boxes form the hatch data
    x_Min = bbox[0]
    x_Max = bbox[3]
    y_Min = bbox[1]
    y_Max = bbox[4]

    # if the part is offset from 0,0 adjust the offset of the part to create the smallest
    # possible a-matrix
    x_offset = - x_Min
    y_offset = - y_Min

    x_upscale = int(1/x_resolution)
    y_upscale = int(1/y_resolution)


    # if part of part crosses -0, -0 adjust the part so that all of the offsets are positive
    if x_Min < 0:
        x_offset = 0 - x_Min
    if y_Min < 0:
        y_offset = 0 - y_Min
    
    ax_Max = (x_Max + x_offset + 1) *  x_upscale
    ay_Max = (y_Max + y_offset + 1) *  y_upscale
    ax_Min = (x_Min + x_offset) *  x_upscale
    ay_Min = (y_Min + y_offset)*  y_upscale

    grid_x = int(np.ceil(ax_Max))
    grid_y = int(np.ceil(ay_Max))
    grid = np.zeros((grid_x, grid_y)) 
    grid_zero = np.zeros((grid_x, grid_y))
    
    debugPrint(f"True min {x_Min}, {x_Max}, {y_Min}, {y_Max}", 0)
    debugPrint(f"Adjusted min {ax_Min}, {ax_Max}, {ay_Min}, {ay_Max}", 0)
    y_int = np.arange(ay_Min, ay_Max)
    x_int = np.arange(ax_Min, ax_Max)
    g = np.meshgrid(x_int, y_int)
    coords = list(zip(*(c.flat for c in g)))

    ellipsepoints = np.array([0,0])
   
    tic = time.perf_counter()    
    counter = 0
    hatch_coords = []
    for row in exposure_points:
        x, y, r = row
        hatch_coords.append((x, y, counter))
        counter = counter + 1
    
    def process_offsets(row):
        x, y, r = row
        x = (x + x_offset) *  x_upscale
        y = (y + y_offset) *  y_upscale
        return x, y, int(r)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        for row, solution in zip(hatch_coords, executor.map(process_offsets, hatch_coords)):            
            x, y, r = solution    
            hatch_coords[r] = (x, y, r)

    # Sort the items first
    hatch_coords = sorted(hatch_coords, key=lambda tup: (tup[0], tup[1]))

    debugPrint(f"hatch coords {len(hatch_coords)}", 0)

    def log_result(result):
        # This is called whenever foo_pool(i) returns a result.
        # result_list is modified only by the main process, not the pool workers.
        for x, y, is_contained in result:    
            if (is_contained == True):
                grid[int(x), int(y)] = 1

    with mp.Pool() as pool:
        worker = partial(process_points, hatch_coords)  # Set y to 2
        result = pool.map_async (worker, coords, callback=log_result, chunksize=5000)
        result.wait()
            
               

    toc = time.perf_counter()    
    debugPrint(f"Points to voxel time {toc - tic:0.4f} seconds", -1) 
    debugPrint(f"Grid Shape {grid.shape} seconds", -1) 

    if PLOT_LEVEL == True:
        import matplotlib.pyplot as plt    
        plt.matshow(grid)
        plt.show()

        
    if FILE_LOGGING_LEVEL > 1:
        np.savetxt("staging/grid.txt", grid)
    grid = np.dstack((grid, grid_zero))
    return grid

# TODO: Time whether it is faster to convert the hatches or the polygons
def convert_hatch_to_voxel(hatch_lines, rotation=0, x_resolution=1, y_resolution=1):
    """
    Converts hatch lines supplied in bounding box format directly to a voxelized map.

    Args:
        hatch_lines (ndarray): Ordered list of hatches as an ndarray.
        rotation (float): Rotation angle (currently unused in this function).
        x_resolution (float): Width of the slice thickness.
        y_resolution (float): Height of the slice thickness.

    Returns:
        np.ndarray: A binary grid where 1 represents material presence.
    """
    # Precompute scaling factors
    x_upscale = 1 / x_resolution
    y_upscale = 1 / y_resolution

    x_min, y_min = np.min(hatch_lines[:, [0, 1]], axis=0)
    x_max, y_max = np.max(hatch_lines[:, [2, 3]], axis=0)

    x_offset = -x_min if x_min < 0 else 0
    y_offset = -y_min if y_min < 0 else 0

    # Adjust the bounding box coordinates to ensure positive values
    hatch_lines[:, [0, 2]] += x_offset
    hatch_lines[:, [1, 3]] += y_offset

    # Scale hatch lines to match voxel resolution
    hatch_lines[:, [0, 2]] *= x_upscale
    hatch_lines[:, [1, 3]] *= y_upscale

    # Compute grid dimensions
    grid_x = int(np.ceil((x_max + x_offset) * x_upscale)) + 1
    grid_y = int(np.ceil((y_max + y_offset) * y_upscale)) + 1
    grid = np.zeros((grid_x, grid_y), dtype=np.uint8)

    x_coords = np.arange(grid_x)
    y_coords = np.arange(grid_y)
    x_grid, y_grid = np.meshgrid(x_coords, y_coords, indexing='ij')
    voxel_coords = np.stack([x_grid.ravel(), y_grid.ravel()], axis=1)

    # Vectorized check for bounding box overlap
    tic = time.perf_counter()
    for bbox in hatch_lines:
        x_min, y_min, x_max, y_max, _ = bbox

        # Determine overlapping voxels
        x_mask = (voxel_coords[:, 0] >= x_min) & (voxel_coords[:, 0] <= x_max)
        y_mask = (voxel_coords[:, 1] >= y_min) & (voxel_coords[:, 1] <= y_max)
        overlap_mask = x_mask & y_mask

        # Set grid values to 1 for overlapping voxels
        grid_x_indices = voxel_coords[overlap_mask, 0].astype(int)
        grid_y_indices = voxel_coords[overlap_mask, 1].astype(int)
        grid[grid_x_indices, grid_y_indices] = 1
        
    toc = time.perf_counter()

    # print(f"Vectorized hatch to voxel time: {toc - tic:0.4f} seconds")

    # Stack grid with an empty zero layer
    grid_zero = np.zeros_like(grid)
    grid = np.dstack((grid, grid_zero))

    return grid, int(np.ceil(x_max) + np.floor(x_min)), int(np.ceil(y_max) + np.floor(y_min))

# We can take the perimeter of the bounding boxes from the dyndrite software
# so that we avoid having to re-voxelize an STL file, and the potential errors
# that might arise from hatching not being contained within the externally voxelized map 
# Function takes a diction that contains all of the polygons for a layer
# The definition of the polygons may vary, however, we do not need the hatch angle
# We can take the perimeter of the bounding boxes from the dyndrite software
# so that we avoid having to re-voxelize an STL file, and the potential errors
# that might arise from hatching not being contained within the externally voxelized map 
# Function takes a diction that contains all of the polygons for a layer
# The definition of the polygons may vary, however, we do not need the hatch angle
def convert_polygon_to_vector(fragment_data = {}, originalSequenceIDs=[], x_resolution=1, y_resolution=1):
    
    """
    This function converts part fragments supplied in n-polygon format
    directly to a voxelized map

    Args:
        fragment_data (dict.ndarry):
            an ndarray that contains an order list of hatches
        x_resolution (float):
            Width of the slice thickness
        y_resolution (string):
            Path to the STL that needs to be processed

    Returns:
        numpy.ndarray:
            A binary grid containing the 1,0s, where a 1 represents an area of the area where 
            there is material present, i.e. is occupied by the STL

    """    
    if (len(fragment_data) == 0):
        raise Exception("No fragments provided for this layer.") 
    

    # Get the bounding boxes form the fragment data    
    x_Min = 2000
    x_Max = -2000
    y_Min = 2000
    y_Max = -2000

    # TODO: See if this can be multi-threaded
    for key in fragment_data: 
        # print(fragment_data[key])
        if not isinstance(fragment_data[key], dict):
            numbers = fragment_data[key]
            numbers = np.array(numbers, dtype=float)            
            # Get the bounding boxes form the fragment data
            x_MaxT = np.max(numbers[:,0])
            x_MinT = np.min(numbers[:,0])
            y_MinT = np.min(numbers[:,1])        
            y_MaxT = np.max(numbers[:,1])        
            if (x_Min > x_MinT): x_Min = x_MinT
            if (x_Max < x_MaxT): x_Max = x_MaxT
            if (y_Min > y_MinT): y_Min = y_MinT
            if (y_Max < y_MaxT): y_Max = y_MaxT
        
    # scale the axes based on the resolution of the slicing data
    # the incoming data is provided in mm, but size of the output 
    # array must match the number of hatched elements

    # if the part is offset from 0,0 adjust the offset of the part to create the smallest
    # possible a-matrix
    x_offset = - x_Min
    y_offset = - y_Min

    x_upscale = int(1/x_resolution)
    y_upscale = int(1/y_resolution)

    # if part of part crosses -0, -0 adjust the part so that all of the offsets are positive
    if x_Min < 0:
        x_offset = 0 - x_Min
    if y_Min < 0:
        y_offset = 0 - y_Min
    
    ax_Max = (x_Max + x_offset + 1) *  x_upscale
    ay_Max = (y_Max + y_offset + 1) *  y_upscale
    ax_Min = (x_Min + x_offset) *  x_upscale
    ay_Min = (y_Min + y_offset) *  y_upscale

    grid_x = int(np.ceil(ax_Max))
    grid_y = int(np.ceil(ay_Max))
    grid = np.zeros((grid_x, grid_y)) 
    grid_zero = np.zeros((grid_x, grid_y))

    debugPrint(f"True min {x_Min}, {x_Max}, {y_Min}, {y_Max}, offset {x_offset}, {y_offset} {x_upscale}", 0)
    debugPrint(f"Adjusted min {ax_Min}, {ax_Max}, {ay_Min}, {ay_Max}", 0)

    mutlithread_fragment_data = {}
    for row in fragment_data:  
        # print(row)
        row_int = int(row)  
        try:
            mutlithread_fragment_data[row_int] = np.array(fragment_data[row], dtype=float).flatten()
        except:
            pass

    # Get the bounding box for each of the polygons multi-threaded
    mutlithread_bbox = []

    def __process_segments_to_BBOX (row, seqID):
        row_int = int(row)
        dynpoly = np.array(mutlithread_fragment_data[row_int], dtype=float)  

        polyArray = np.reshape(dynpoly, (-1,2))
        
        polyArray[:, 0] = (polyArray[:, 0] + x_offset) 
        polyArray[:, 1] = (polyArray[:, 1] + y_offset) 
        polygon = Polygon(polyArray)

        # Get the bounding box of the polygon to use in the SmartScan Algorithm
        fragment_bbox = np.array(polygon.get_path().get_extents().get_points()).flatten().tolist()   
        fragment_bbox.append(seqID)
        mutlithread_bbox.append(fragment_bbox)
        
        # Broadcast comomparison operations
        x_mins = [fragment_bbox][:,0]
        x_maxs = [fragment_bbox][:,2]
        y_mins = [fragment_bbox][:,1]
        y_maxs = [fragment_bbox][:,3]
        
        x_coords, y_coords = np.meshgrid(np.arange(grid_x), np.arange(grid_y), indexing='ij')
        grid_coords = np.stack((x_coords.ravel(), y_coords.ravel()), axis=-1)
        
        x = grid_coords[:, 0][:, None]  
        y = grid_coords[:, 1][:, None]  
        
        overlaps = (
            (x + POINT_RADIUS >= x_mins) &
            (x - POINT_RADIUS <= x_maxs) &
            (y + POINT_RADIUS >= y_mins) &
            (y - POINT_RADIUS <= y_maxs)
        )

        # If any bounding box overlaps a grid point, set the value to 1
        contained = np.any(overlaps, axis=1)

        # Reshape the result back into a 2D grid
        grid = contained.reshape(grid_x, grid_y)

        return grid
        
    with ThreadPoolExecutor(max_workers=CPU_COUNT) as executor:
        executor.map(__process_segments_to_BBOX, mutlithread_fragment_data, originalSequenceIDs)

    x_int = np.arange(ax_Min, ax_Max)
    y_int = np.arange(ay_Min, ay_Max)    
    g = np.meshgrid(x_int, y_int)
    coords = list(zip(*(c.flat for c in g)))

    # for i in range(grid_x):
    #     for j in range(grid_y):
    #         x, y, is_contained = process_hatches(mutlithread_bbox,(i,j))
    #         if (is_contained == True):                
    #             grid[i, j] = 1

    # def log_result(result):
    #     # This is called whenever foo_pool(i) returns a result.
    #     # result_list is modified only by the main process, not the pool workers.
    #     for x, y, is_contained in result:    
    #         if (is_contained == True):
    #             grid[int(x), int(y)] = 1


    # limit_chunksize  = int(len(mutlithread_bbox) / CPU_COUNT)    
    # # Parallelize the processing of hatch lines
    # with mp.Pool(CPU_COUNT) as pool:
    #     worker = partial(process_hatches, mutlithread_bbox)  # Set y to 2
    #     result = pool.map_async (worker, coords, callback=log_result, chunksize=100)
    #     result.wait()

    if PLOT_LEVEL == True:
        import matplotlib.pyplot as plt    
        plt.matshow(grid)
        plt.show()
    
    grid = np.dstack((grid, grid_zero))    
    return grid, np.array(mutlithread_bbox)


def smartScanCore (numbers_set=np.array([]), Sorted_layers=np.array([]), dx:float = 1, dy:float = 1, reduced_order:int=20, 
                    kt:float = 22.5, rho:float = 7990,  cp:float = 500, vs:float = 0.6,  h:float = 50,  P:float = 100, v0_ev=None, logging_function=None ):
    try:
        lambda_val = 0.37
        Rb = 0.075 / 2

        T_a = 293
        T_init = 293

        N_x, N_y, N_z = Sorted_layers.shape    

        __ssbounds = N_x * N_y * N_z    
        debugPrint(f"smartScanCore - numbers_set shape: {numbers_set.shape}   Sorted_layers.shape: {Sorted_layers.shape}", -1) 

        tic = time.perf_counter()    
        StateMatrix, F_z, H, G = SMC.constructStateMatrix(N_x, N_y, N_z, dx * 10**-3, dy * 10**-3, h, kt, rho, cp, vs, P)
        StateMatrix = csr_matrix(StateMatrix, (__ssbounds, __ssbounds))
        
        Sorted_layers_T = np.zeros((N_x, N_y, N_z))
        for k in range(N_z):
            Sorted_layers_T[:, :, N_z - k - 1] = Sorted_layers[:, :, k]

        Z = diags(np.reshape(Sorted_layers_T, -1), [0], __ssbounds, __ssbounds)           
        
        # debugPrint(f"smartScanCore - Generated State Matrix Z:{Z.shape} StateMatrix:{StateMatrix.shape} {__ssbounds} {toc - tic:0.4f} seconds", 0)

        Sorted_layers_T = np.array(Sorted_layers_T)

        A1 = Z.dot(StateMatrix)
        A2 = Z.dot(A1)
        ones_diag = np.ones((StateMatrix.shape[0], 1))
        sum_A2 = csr_matrix.sum(A2, axis=1)  
        
        A3 = diags(cpy.reshape(ones_diag-sum_A2, -1), [0], __ssbounds, __ssbounds)
            
        Correct_A = np.add(A2.tocsr(), A3.tocsr())
        debugPrint(f"Correct_A: {Correct_A.shape}", 0)

        toc = time.perf_counter()    
        # debugPrint(f"smartScanCore - Generated State Matrix {toc - tic:0.4f} seconds", -1)  
        
        tic = time.perf_counter()
        Final_A = SMC.addBoundaryConditions(Correct_A, N_x, N_y, N_z, H, 0)    
        toc = time.perf_counter()    
        # debugPrint(f"smartScanCore - Added boundary conditions {toc - tic:0.4f} seconds", -1)   
            
        diag_elements = Correct_A.diagonal()
        diag = np.where(diag_elements == 1)
        #TODO: Reimplement delete of diagonal
        # Final_A = delete(Correct_A, diag, axis = 0)
        # Final_A = delete(Final_A, diag, axis = 1)    
        debugPrint(f"smartScanCore - Final_A: {Final_A.shape}", -1)        

        tic = time.perf_counter()    
        try:
            debugPrint(f"smartScanCore - Reduced order A: {reduced_order}", 0)
            # Catch a condition where we might try to reduce the order smaller than the existing matrix
            # Calculating the eigenvalues and eigenvectors            
            reduced_order = int (reduced_order)
            custom_ncv = int(max(2*reduced_order + 1, __ssbounds/4))
            if USE_CUDA == True:
                CPY_Final_A = cpy_csr_matrix(Final_A)
                temp1, eigen_vectors = eigsh(a=CPY_Final_A, k=reduced_order, which='LA', maxiter=200) 
                eigen_vectors = eigen_vectors.get()
            else:
                temp1, eigen_vectors = eigsh(Final_A, reduced_order, which='SA', v0=v0_ev, maxiter=100, return_eigenvectors=True)        
                v0_ev = eigen_vectors[:,-1]
        except Exception as e:
            # The eigsh method without CUPY takes a high number of iterations to find a solution
            # Instead we increase the order to a high number and cap it at the half of the size of geometry        
            debugPrint(f"smartScanCore - Could not resize to - Final_A: {reduced_order} attempt to use {int (min(50, __ssbounds/2))}", -1) 
            reduced_order = int (min(50, __ssbounds/2))        
            
            custom_ncv = int(max(2*reduced_order + 1, __ssbounds/4))
            
            # We were not able to find any solutions with the previous initialization vector, start at random
            v0_ev = None 

            if USE_CUDA == True:
                CPY_Final_A = cpy_csr_matrix(Final_A)
                temp1, eigen_vectors = eigsh(a=CPY_Final_A, k=reduced_order, which='SA', maxiter=1000) 
                eigen_vectors = eigen_vectors.get()
            else:
                temp1, eigen_vectors = eigsh(Final_A, reduced_order, ncv=custom_ncv, which='LA', v0=v0_ev, maxiter=300, return_eigenvectors=True)   
                v0_ev = eigen_vectors[:,-1]                            
            
        toc = time.perf_counter()    
        debugPrint(f"smartScanCore - Order time {toc - tic:0.4f} seconds  eigen_vectors: {eigen_vectors.shape}", -1)     

        # Final_A
        eigen_vectors = np.array(eigen_vectors)
        
        tempAMatrix = np.dot(eigen_vectors.T, Final_A.A)        
        Final_A = np.dot(tempAMatrix, eigen_vectors)              

        # Create arrays M and N
        M = np.repeat(np.arange(1, N_x + 1)[:, np.newaxis], N_y, axis=1)  # row information
        N = np.repeat(np.arange(1, N_y + 1)[np.newaxis, :], N_x, axis=0)  # col information

        # Combine M and N along the third dimension
        MN = np.dstack((M, N))

        # Adjust MN values (subtract 1 and multiply by 0.2)
        MN = (MN - 1) * 0.2 

        # Sort the rows of numbers_set based on the fifth column (index 4)
        numbers_set = numbers_set[np.argsort(numbers_set[:, 4])]

        # Get the value from the last row and last column
        feature_n = numbers_set.shape[0]    
        debugPrint(f"smartScanCore - Total features: {feature_n}", 0)

        # Initialize feature_start to 0
        feature_start = 0
        total_features = int(feature_n)

        # Initialize an empty list for Ab_set
        Ab_set = dict.fromkeys((range(total_features)))

        # initialize matrices
        B = np.zeros((MN.shape[0], MN.shape[1]))
        x, y = [], []
        Nt = 0
        
        # Create a zeros array for Beq
        Beq = np.zeros((int(Final_A.shape[0]), int(feature_n)))    
        # debugPrint(f"smartScanCoreCUDA - {Beq.shape} Beq Array Initialized", 2)      

        # PRE_COMPUTE
        MN_SLICE_0 = MN[:, :, 0]
        MN_SLICE_1 = MN[:, :, 1]
        q_factor_3 = np.exp(Rb)
        q_factor_4 = np.exp(np.pi * Rb)
        q_factor_1 = (2 * lambda_val * P)
        nt_pre = 1 / vs / (dx / vs)

        Q = 0

        Ab = np.eye(Final_A.shape[0])    

        tic = time.perf_counter()
        
        for feature_current in range(total_features):
            numbers = numbers_set[feature_current, :]            

            if feature_current != feature_start:
                Ab = np.eye(Final_A.shape[0])
                Bb = np.zeros((Final_A.shape[0], 1))
                x, y = [], []
                Nt = 0
                B = np.zeros((MN.shape[0], MN.shape[1]))
                A = Final_A
                feature_start = feature_start + 1  

            startPoint = numbers[:2]
            endPoint = numbers[2:4]  

            sqDiff = np.power((endPoint - startPoint), 2)
            distance = np.sqrt(np.sum(sqDiff))

            # nt = distance / vs / (dx / vs)
            nt = distance * nt_pre
            Nt += int(np.floor(nt))

            # Create linearly spaced arrays for x and y
            x.extend(np.linspace(startPoint[0], endPoint[0], int(nt)))
            y.extend(np.linspace(startPoint[1], endPoint[1], int(nt)))        
            debugPrint(f"smartScanCore - X: {x} Y: {y}", 2)

            # Energy input at each time step                          
            for i in range(Nt - int(nt), Nt):                    
            # def go_fast(i):
                Posi = np.array([x[i], y[i]])
                # rb = np.power((MN[:, :, 0] - Posi[0]), 2) + np.power((MN[:, :, 1] - Posi[1]), 2)
                rb = np.power((MN_SLICE_0 - Posi[0]), 2) + np.power((MN_SLICE_1 - Posi[1]), 2)
                rb = np.sqrt(rb)
                q_factor_2 = np.exp(-2 * rb)             
                Q = q_factor_1 * (q_factor_2 / q_factor_3)  / q_factor_4
                # Q = Q / np.sum(Q)
                # Q = np.array(Q)            
                # B = np.add(B, Q)
                Q /= np.sum(Q)
                B += Q

            debugPrint(f"smartScanCore - Current Features: {feature_current}", 2)
            
            # Ab = np.eye(Final_A.shape[0])        
            debugPrint(f"smartScanCore - Ab : {Ab.shape}", 2)
            
            Bb = np.zeros((Final_A.shape[0], 1))        
            debugPrint(f"smartScanCore - Bb : {Bb.shape}", 2)

            # Ab = Ab ** Nt
            Ab = np.power(Ab, Nt)

            # Ab_1 = Ab @ eigen_vectors.T
            Ab_1 = np.matmul(Ab, eigen_vectors.T)            
            debugPrint(f"smartScanCore - Ab_1 : {Ab_1.shape}", 2)

            B_current = np.reshape(B,  [N_x*N_y, -1])
            debugPrint(f"smartScanCore - B_current : {B_current.shape}", 2)

            diag = np.array(diag)
            debugPrint(f"smartScanCore - diag : {diag.shape}", 2)
            
            B_current = B_current[diag[diag < N_x*N_y ]]
            # debugPrint(f"smartScanCoreCUDA - B_current : {B_current.shape}", 2)

            Ab_1 = np.multiply(G, Ab_1)
            Ab1_temp = np.concatenate((B_current, np.zeros((Ab_1.shape[1] - B_current.shape[0], 1))))
            Ab_1 = np.dot(Ab_1, Ab1_temp)
            Bb = np.add(Bb, Ab_1)
            
            Beq[:, feature_current] = Bb[0]
            Ab_set[feature_current] = Ab
        

        
        # # Initialize Cb matrix    
        Cb_ones = np.ones((reduced_order, reduced_order))/reduced_order
        Cb = np.eye(reduced_order) - Cb_ones
        
        # Calculate lambda_0
        lambda_0 = np.diag(np.matmul(Beq.T,  np.matmul(Cb, Beq)))
        
        # if DEBUG_LEVEL > 2:
        #     np.savetxt("staging/lambda_0.txt", lambda_0)

        # Initialize lambda_1 (empty list)
        lambda_1 = np.zeros((int(feature_n), Final_A.shape[0]))

        def __calculateLambda_1 (feature):
            lambda_1[feature] = (2 * np.matmul(Beq[:, feature].T, np.matmul(Cb, Ab_set[feature])))
        
        with ThreadPoolExecutor(max_workers=CPU_COUNT) as executor:
            executor.map(__calculateLambda_1, range(1, int(feature_n)))    

        T_opt = np.concatenate((T_init * np.ones(Final_A.shape[0] - 2), [T_a, T_a]))     

        # set_opt contains the smart scan sequence - save the output
        set_opt = np.array([])
        debugPrint(f"smartScanCore -lambda_0 {lambda_0.shape} lambda_1: {lambda_1.shape} T_opt: {T_opt.shape}", 2)

        toc = time.perf_counter()    
        debugPrint(f"smartScanCore - Loop time {toc - tic:0.4f} seconds", -1)
        
        T_opt = np.array(T_opt)
        T_ori = np.array(T_opt)

        tic = time.perf_counter()
        # debugPrint(f"Generating Sequence ", 0)
        for i in range(total_features):
            c = lambda_0 + np.dot(lambda_1, T_opt)
            sorted_indices = np.argsort(c)
            indices = sorted_indices[~np.isin(sorted_indices, set_opt)]
            I = int(indices[0])
            T_opt_temp = np.dot(Ab_set[I], T_opt)
            T_opt = np.add(T_opt_temp, Beq[:, I])
            T_ori = np.add(T_opt_temp, Beq[:, i])
            set_opt = np.append(set_opt, I)


            if FILE_LOGGING_LEVEL > 2:    
                np.savetxt("staging/T_opt.txt", T_opt)
        
        if FILE_LOGGING_LEVEL > 2:    
            np.savetxt("staging/setopt.txt", set_opt)
        
        toc = time.perf_counter()  
        R_opt = np.std(T_opt)
        debugPrint(f"R_opt: {R_opt}", -1)
        R_ori = np.std(T_ori)
        debugPrint(f"R_ori: {R_ori}", -1)  
        # debugPrint(f"smartScanCore - End sort time {toc - tic:0.4f} seconds", -1)


        return set_opt.astype(int), v0_ev, R_opt, R_ori
    
    except Exception as e:
        logging_function(f"Error in smartScanCore {e}")
        raise e