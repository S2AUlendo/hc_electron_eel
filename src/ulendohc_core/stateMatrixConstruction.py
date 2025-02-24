#*******************************************************
# Copyright (C) 2023-2024 Ulendo Technologies, Inc
# This file is part of Ulendo HC Plugin.
# The Ulendo HC Plugin and files contained within the Ulendo HC 
# project folder can not be copied and/or distributed without the 
# express permission of an authorized member of 
# Ulendo Technologies, Inc. 
# For more information contact info@ulendo.io
#*******************************************************

from src.ulendohc_core.util import *

# Chuan He
# Generate the state matrix, A, without boundary conditions considered
# Inputs: L - length
#         W - width
#         H - height
#         dx - x grid size
#         dx - y grid size (Assume it is same as dx)
#         dz - z grid size
#         kt - conductivity
#         rho - density
#         cp - heat capacity
#         vs - scanning speed
# Output: State matrix without boundary conditions

# Number of elements on the x-axis
# Number of elements on the y-axis
# Number of elements on the z-axis (Must be one more than one layer)
def constructStateMatrix(N_x, N_y, N_z, dx, dz, h, kt, rho, cp, vs, P):
    alpha = kt / rho / cp  # Diffusivity [m^2/s]
    dt = dx / vs / 1 # Sampling time [s] (Assume laser spot is tracing one grid per time step)

    # Assuming you have defined the necessary variables (replace with your actual values)
    F_x = alpha * dt / dx / dx
    F_z = alpha * dt / dz / dz
    H = alpha * h * dt / kt / dz
    
    __stmbounds = N_x * N_y * N_z
    A = lil_matrix((__stmbounds, __stmbounds)) # Initialize sparse matrix
    G = alpha * P * dt / kt / dx / dx / dx

    # Corners.
    A[0, 0] = 1 - 2 * F_x - F_z
    A[0, 1] = F_x
    A[0, N_x] = F_x
    A[0, N_x * N_y] = F_z

    A[N_x - 1, N_x - 1] = 1 - 2 * F_x - F_z
    A[N_x - 1, N_x - 2] = F_x
    A[N_x - 1, N_x + N_x] = F_x
    A[N_x - 1, N_x + N_x * N_y] = F_z

    A[N_x * (N_y - 1), N_x * (N_y - 1)] = 1 - 2 * F_x - F_z
    A[N_x * (N_y - 1), N_x * (N_y - 1) + 1] = F_x
    A[N_x * (N_y - 1), N_x * (N_y - 1) - N_x] = F_x
    A[N_x * (N_y - 1), N_x * (N_y - 1) + N_x * N_y] = F_z

    
    fill = [1, N_x, N_x * (N_y - 1) + 1, N_x * N_y, (N_z - 1) * N_x * N_y + 1, (N_z - 1) * N_x * N_y + N_x, (N_z - 1) * N_x * N_y + N_x * (N_y - 1) + 1, (N_z - 1) * N_x * N_y + N_x * N_y]

    #Sides.
    for i in range(2, N_x):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - 1] = F_x
        A[i, i + 1] = F_x
        A[i, i + N_x] = F_x
        A[i, i + N_x * N_y] = F_z
        fill.append(i)
    
    for i in range(N_x * (N_y - 1) + 2, N_x * (N_y - 1) + N_x):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - 1] = F_x
        A[i, i + 1] = F_x
        A[i, i - N_x] = F_x
        A[i, i + N_x * N_y] = F_z
        fill.append(i)

    # Assuming you have defined N_x, N_y, F_x, F_z, and A (replace with your actual values)
    for i in range(1 + N_x, N_x * (N_y - 2) + 1, N_x):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - N_x] = F_x
        A[i, i + N_x] = F_x
        A[i, i + 1] = F_x
        A[i, i + N_x * N_y] = F_z
        fill.append(i)

    
    # Assuming you have defined N_x, N_y, N_z, F_x, F_z, and A (replace with your actual values)
    for i in range(N_x + N_x, N_x * (N_y - 2) + N_x, N_x):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - N_x] = F_x
        A[i, i + N_x] = F_x
        A[i, i - 1] = F_x
        A[i, i + N_x * N_y] = F_z
        fill.append(i)

    for i in range((N_z - 1) * N_x * N_y + 2, (N_z - 1) * N_x * N_y + N_x - 1):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - 1] = F_x
        A[i, i + 1] = F_x
        A[i, i + N_x] = F_x
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    for i in range((N_z - 1) * N_x * N_y + N_x * (N_y - 1) + 2, (N_z - 1) * N_x * N_y + N_x * (N_y - 1) + N_x - 1):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - 1] = F_x
        A[i, i + 1] = F_x
        A[i, i - N_x] = F_x
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    
    # Assuming you have defined N_x, N_y, N_z, F_x, F_z, and A (replace with your actual values)
    for i in range((N_z - 1) * N_x * N_y + 1 + N_x, (N_z - 1) * N_x * N_y + N_x * (N_y - 2) + 1, N_x):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - N_x] = F_x
        A[i, i + N_x] = F_x
        A[i, i + 1] = F_x
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    for i in range((N_z - 1) * N_x * N_y + N_x + N_x, (N_z - 1) * N_x * N_y + N_x * (N_y - 2) + N_x, N_x):
        A[i, i] = 1 - 3 * F_x - F_z
        A[i, i - N_x] = F_x
        A[i, i + N_x] = F_x
        A[i, i - 1] = F_x
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    for i in range(1 + N_x * N_y, N_x * N_y, (N_z - 2) * N_x * N_y + 1):
        A[i, i] = 1 - 2 * F_x - 2 * F_z
        A[i, i + 1] = F_x
        A[i, i + N_x] = F_x
        A[i, i + N_x * N_y] = F_z
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    # Assuming you have defined N_x, N_y, N_z, F_x, F_z, and A (replace with your actual values)
    for i in range(N_x + N_x * N_y, N_x * N_y, (N_z - 2) * N_x * N_y + N_x):
        A[i, i] = 1 - 2 * F_x - 2 * F_z
        A[i, i - 1] = F_x
        A[i, i + N_x] = F_x
        A[i, i + N_x * N_y] = F_z
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    for i in range(N_x * (N_y - 1) + 1 + N_x * N_y, N_x * N_y, (N_z - 2) * N_x * N_y + 1):
        A[i, i] = 1 - 2 * F_x - 2 * F_z
        A[i, i + 1] = F_x
        A[i, i - N_x] = F_x
        A[i, i + N_x * N_y] = F_z
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    for i in range(N_x * N_y + N_x * N_y, N_x * N_y, (N_z - 2) * N_x * N_y + N_x * N_y):
        A[i, i] = 1 - 2 * F_x - 2 * F_z
        A[i, i - 1] = F_x
        A[i, i - N_x] = F_x
        A[i, i + N_x * N_y] = F_z
        A[i, i - N_x * N_y] = F_z
        fill.append(i)

    #Surfaces.
    fill_top = np.arange(1, N_x * N_y + 1)
    indices_to_remove = np.concatenate([
        np.arange(1, N_x + 1),
        np.arange(N_x + 1, N_x * (N_y - 1) + 2, N_x),
        np.arange(N_x + N_x, N_x * (N_y - 1) + N_x + 1, N_x),
        np.arange(N_x * (N_y - 1) + 2, N_x * (N_y - 1) + N_x)
    ])

    fill_top[indices_to_remove - 1] = 0  # Set the specified indices to 0

    # Fill A matrix based on fill_top indices
    for k in range(len(fill_top)):
        i = fill_top[k] - 1
        A[i, i] = 1 - 4 * F_x - F_z
        A[i, i - N_x] = F_x
        A[i, i + N_x] = F_x
        A[i, i + 1] = F_x
        A[i, i - 1] = F_x
        A[i, i + N_x * N_y] = F_z

    # Assuming you have defined N_x, N_y, N_z, F_x, and F_z
    fill_bot = np.arange((N_z - 1) * N_x * N_y + 1, (N_z - 1) * N_x * N_y + N_x * N_y + 1)
    indices_to_remove = np.concatenate([
        np.arange(1, N_x + 1),
        np.arange(N_x + 1, N_x * (N_y - 1) + 2, N_x),
        np.arange(N_x + N_x, N_x * (N_y - 1) + N_x + 1, N_x),
        np.arange(N_x * (N_y - 1) + 2, N_x * (N_y - 1) + N_x)
    ])
    fill_bot[indices_to_remove - 1] = 0  # Set the specified indices to 0

    # Fill A matrix based on fill_bot indices
    for k in range(len(fill_bot)):
        i = fill_bot[k] - 1
        A[i, i] = 1 - 4 * F_x - F_z
        A[i, i - N_x] = F_x
        A[i, i + N_x] = F_x
        A[i, i + 1] = F_x
        A[i, i - 1] = F_x
        A[i, i - N_x * N_y] = F_z

    top_set = np.arange(2, N_x)

    # Loop over k values
    for k in range(1, N_z - 1):
        for j in range(len(top_set)):
            i = k * N_x * N_y + top_set[j]
            A[i, i] = 1 - 3 * F_x - 2 * F_z
            A[i, i - 1] = F_x
            A[i, i + 1] = F_x
            A[i, i + N_x] = F_x
            A[i, i + N_x * N_y] = F_z
            A[i, i - N_x * N_y] = F_z
            fill.append(i)

    top_set = np.arange(N_x * (N_y - 1) + 2, N_x * (N_y - 1) + N_x)

    for k in range(1, N_z - 2):
        for j in range(len(top_set)):
            i = k * N_x * N_y + top_set[j]
            A[i, i] = 1 - 3 * F_x - 2 * F_z
            A[i, i - 1] = F_x
            A[i, i + 1] = F_x
            A[i, i - N_x] = F_x
            A[i, i + N_x * N_y] = F_z
            A[i, i - N_x * N_y] = F_z
            fill.append(i)

    top_set = range(1 + N_x, N_x * (N_y - 2) + 1, N_x)

    for k in range(1, N_z - 2):
        for j in range(len(top_set)):
            i = k * N_x * N_y + top_set[j]
            A[i, i] = 1 - 3 * F_x - 2 * F_z
            A[i, i - N_x] = F_x
            A[i, i + N_x] = F_x
            A[i, i + 1] = F_x
            A[i, i + N_x * N_y] = F_z
            A[i, i - N_x * N_y] = F_z
            fill.append(i)

    top_set = np.arange(N_x + N_x, N_x * (N_y - 2) + N_x, N_x)

    for k in range(1, N_z - 2):
        for j in range(len(top_set)):
            i = k * N_x * N_y + top_set[j]
            A[i, i] = 1 - 3 * F_x - 2 * F_z
            A[i, i - N_x] = F_x
            A[i, i + N_x] = F_x
            A[i, i - 1] = F_x
            A[i, i + N_x * N_y] = F_z
            A[i, i - N_x * N_y] = F_z
            fill.append(i)

    # Create an array for fill_set
    fill_set = np.arange(1, (N_z * N_x * N_y)+1)    

    # subtract 1 from all the values in fill.
    fill = np.array(fill)
    fill -= 1

    # Remove the elements specified by 'fill'    
    fill_set = np.delete(fill_set, fill)
    
    if DEBUG_LEVEL > 3:  
        print((fill_set.shape))
    if DEBUG_LEVEL > 4:  
        if USE_CUDA == True:
            cpy.savetxt("staging/fill.txt", fill)
        else:
            np.savetxt("staging/fill.txt", fill)

    # Loop over k values
    # for k in range(len(fill_set)):
    for k in range(1, N_z - 2):
        for j in range(len(top_set)):
            i = fill_set[k]
            A[i, i] = 1 - 4 * F_x - 2 * F_z
            A[i, i - N_x] = F_x
            A[i, i + N_x] = F_x
            A[i, i + 1] = F_x
            A[i, i - 1] = F_x
            A[i, i + N_x * N_y] = F_z
            A[i, i - N_x * N_y] = F_z

    return A, F_z, H, G   # StateMatrix 

    
def addBoundaryConditions(Correct_A, N_x, N_y, N_z, H, F):

    __stmbounds = N_x * N_y * N_z
    
    tic = time.perf_counter()
    
    Final_A = lil_matrix(Correct_A)
    Final_A.resize((__stmbounds, __stmbounds))
        
    toc = time.perf_counter()    
    # debugPrint(f"smartScanCore - Added boundary conditions {toc - tic:0.4f} seconds", -1)  

    for i in range(N_x * N_y):
        Final_A[i, i] = Final_A[i, i] - H

    for i in range(N_x * N_y * (N_z - 1), N_x * N_y * N_z):
        Final_A[i, i] = Final_A[i, i] - F
    
    Final_A[:N_x * N_y, N_x * N_y] = H
    Final_A[N_x * N_y * (N_z - 1):N_x * N_y * N_z, N_x * N_y + 1] = F

    # Final_A[num_elements, num_elements] = 1
    # Final_A[num_elements + 1, num_elements + 1] = 1
    
    # return csr_matrix(Final_A)
    return Final_A


def returnOtherParams(vs, rho, cp, h, P, kt, dx, dz):
    alpha = kt/rho/cp;    
    dt = dx/vs/1;         
    F_z = alpha*dt/(dz**2)
    H = alpha * h * dt / (kt * dz)
    G = alpha * P * dt / (kt * (dx**3))
    return F_z, H, G #Convection term, Input terms 