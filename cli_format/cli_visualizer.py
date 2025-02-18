import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.patches import Rectangle
import os
import re

def extract_array_from_line(line):
    """
    Extracts a numerical array from a string line formatted as `//PREFIX/[values]//`.
    Example: Converts `//R_ORI/[1.04, 2.49, ...]//` to a NumPy array.
    """
    # Use regex to find content between [ and ]
    match = re.search(r'\[(.*?)\]', line)
    if not match:
        return np.array([])
    
    # Split matched string into numerical values
    array_str = match.group(1)
    return np.array([float(x) for x in array_str.split(', ')])
    
class CLIVisualizer:
    def __init__(self, filename=""):
        self.filename = filename
        self.layers = []  # Change to list instead of numpy array
        self.magnitude = 0.1
        self.origin = [0, 0]
        self.fig = None
        self.ax = None
        self.r = []
        self.layer_slider = None
        self.hatch_slider = None
        self.current_layer = 0
        self.current_hatch = 0
        self.x_min = 0
        self.x_max = 0
        self.y_min = 0
        self.y_max = 0

    def read_cli(self, filecontent):
        
        try:
            data = filecontent.splitlines()
            layer_indices = np.where(np.char.startswith(data, "$$LAYER/"))[0]
            hatch_indices = np.where(np.char.startswith(data, "$$HATCHES/"))[0]
            polyline_indices = np.where(np.char.startswith(data, "$$POLYLINE/"))[0]
            
            # Combine layer and hatch indices
            layer_indices = np.array(layer_indices)
            hatch_indices = np.array(hatch_indices)
            layer_indices = np.append(layer_indices, hatch_indices[-1]+ 1)
            
            for layer_num in range(len(layer_indices)-1):
                # Find feature indices within the current layer
                hatch_feature_indices = [i for i in hatch_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
                polyline_feautre_indices = [i for i in polyline_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
                
                layer_hatches = [] 
                
                for kk in range(len(hatch_feature_indices)):
                    hatches = data[hatch_feature_indices[kk]]
                    strCell = hatches.split(',')
                    hatch_coords = list(map(float, strCell[2:]))
                    layer_hatches.append(hatch_coords) 
                
                if layer_hatches:  # Only append if we have data
                    self.layers.append(layer_hatches)  # Store as numpy array
                    
        except Exception as e:
            raise e
                    
    def read_cli_file(self, dir, has_r=False, data=None):
        try:
            if data is None:
                file_path = os.path.join(dir, self.filename)
                with open(file_path, 'r') as f:
                    data = f.readlines()
                    
            layer_indices = np.where(np.char.startswith(data, "$$LAYER/"))[0]
            r_indices = np.where(np.char.startswith(data, "//R/"))[0]
            hatch_indices = np.where(np.char.startswith(data, "$$HATCHES/"))[0]
            polyline_indices = np.where(np.char.startswith(data, "$$POLYLINE/"))[0]
            
            # Combine layer and hatch indices
            layer_indices = np.array(layer_indices)
            hatch_indices = np.array(hatch_indices)
            layer_indices = np.append(layer_indices, hatch_indices[-1]+ 1)
            
            for layer_num in range(len(layer_indices)-1):
                # Find feature indices within the current layer
                hatch_feature_indices = [i for i in hatch_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
                polyline_feautre_indices = [i for i in polyline_indices if layer_indices[layer_num] < i < layer_indices[layer_num+1]]
                
                layer_hatches = [] 
                
                for kk in range(len(hatch_feature_indices)):
                    hatches = data[hatch_feature_indices[kk]]
                    strCell = hatches.split(',')
                    hatch_coords = list(map(float, strCell[2:]))
                    layer_hatches.append(hatch_coords) 
                
                if layer_hatches:  # Only append if we have data
                    self.layers.append(layer_hatches)  # Store as numpy array
                    if has_r:
                        if len(r_indices) > 0:
                            r_str = data[r_indices[0]]  # Take the first match
                            r_array = extract_array_from_line(r_str)
                            self.r.append(r_array)
                                    
        except Exception as e:
            raise e

    def get_num_layers(self):
        return len(self.layers) - 1
    
    def get_num_hatches(self):
        if 0 <= self.current_layer < len(self.layers):
            return len(self.layers[self.current_layer])
        return 0
    
    def get_r_from_layer(self):
        if 0 <= self.current_layer < len(self.r):
            return self.r[self.current_layer]
        return []
    
    def set_current_layer(self, layer_num):
        self.current_layer = layer_num
    
    def set_current_hatch(self, hatch_num):
        self.current_hatch = hatch_num
        
    def retrieve_hatch_lines_from_layer(self):
        if 0 <= self.current_layer < len(self.layers):
            layer = self.layers[self.current_layer]
            coords = layer[:self.current_hatch]
            x_coords = []
            y_coords = []
            
            for i in range(len(coords)):
                for j in range(0, len(coords[i]), 4):
                    x_coords.extend([coords[i][j], coords[i][j+2]])
                    y_coords.extend([coords[i][j+1], coords[i][j+3]])
            
            if len(coords) > 0:
                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)
                
                if x_min > self.x_min:
                    self.x_min = x_min
                if x_max < self.x_max:
                    self.x_max = x_max
                if y_min > self.y_min:
                    self.y_min = y_min
                if y_max < self.y_max:
                    self.y_max = y_max
            
            return x_coords, y_coords
        
        return None, None
    
    def get_bounding_boxes_from_layer(self):
        if 0 <= self.current_layer < len(self.layers):
            layer = self.layers[self.current_layer]
            coords = layer[:self.current_hatch]
            bounding_boxes = []
            
            for i in range(len(coords)):
                x_coords = np.concatenate([coords[i][::4], coords[i][2::4]])
                # print(x_coords)
                y_coords = np.concatenate([coords[i][1::4], coords[i][3::4]])
                
                if len(coords) > 0:
                    x_min = np.min(x_coords)
                    x_max = np.max(x_coords)
                    y_min = np.min(y_coords)
                    y_max = np.max(y_coords)
                    
                    if x_min > self.x_min:
                        self.x_min = x_min
                    if x_max < self.x_max:
                        self.x_max = x_max
                    if y_min > self.y_min:
                        self.y_min = y_min
                    if y_max < self.y_max:
                        self.y_max = y_max
                        
                    bounding_boxes.append([[x_min, x_max, x_max, x_min, x_min], [y_min, y_min, y_max, y_max, y_min]])
                    
            return bounding_boxes
        
        return None
    
    def get_full_bounding_boxes_from_layer(self):
        if 0 <= self.current_layer < len(self.layers):
            layer = self.layers[self.current_layer]
            coords = layer
            bounding_boxes = []
            
            for i in range(len(coords)):
                x_coords = np.concatenate([coords[i][::4], coords[i][2::4]])
                # print(x_coords)
                y_coords = np.concatenate([coords[i][1::4], coords[i][3::4]])
                
                if len(coords) > 0:
                    x_min = np.min(x_coords)
                    x_max = np.max(x_coords)
                    y_min = np.min(y_coords)
                    y_max = np.max(y_coords)
                    
                    if x_min > self.x_min:
                        self.x_min = x_min
                    if x_max < self.x_max:
                        self.x_max = x_max
                    if y_min > self.y_min:
                        self.y_min = y_min
                    if y_max < self.y_max:
                        self.y_max = y_max
                        
                    bounding_boxes.append([[x_min, x_max, x_max, x_min, x_min], [y_min, y_min, y_max, y_max, y_min]])
                    
            return bounding_boxes
        
        return None
                
    def plot_with_slider(self):
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        
        plt.subplots_adjust(bottom=0.2)
        
        layer_slider_ax = plt.axes([0.2, 0.1, 0.6, 0.03])
        hatch_slider_ax = plt.axes([0.05, 0.2, 0.03, 0.6])
        
        self.layer_slider = Slider(
            ax=layer_slider_ax,
            label='Layer',
            valmin=0,
            valmax=len(self.layers) - 1,
            valinit=0,
            valstep=1
        )
                    
        self.hatch_slider = Slider(
            ax=hatch_slider_ax,
            label='Hatches',
            valmin=0,
            valmax=len(self.layers[self.current_layer]) - 1,
            valinit=len(self.layers[self.current_layer]) - 1,
            valstep=1,
            orientation='vertical'  # Make vertical
        )
        
        self.current_layer = 0
        self.current_hatch = len(self.layers[self.current_layer]) - 1
        
        self.layer_slider.on_changed(self.update_layer)
        self.hatch_slider.on_changed(self.update_hatches)
        
        # Plot initial layer
        self._plot_layer_and_hatches()
        
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.set_xlabel('X Coordinate')
        self.ax.set_ylabel('Y Coordinate')
        
        plt.show()

    # Update function for the slider
    def update_layer(self, val):
        self.current_layer = int(val)
        max_hatches = len(self.layers[self.current_layer]) - 1
        
        # Update hatch slider range and value
        self.hatch_slider.valmax = max_hatches
        self.hatch_slider.ax.set_ylim(0, max_hatches)  # Update y-axis limits for vertical slider
        self.hatch_slider.set_val(max_hatches)  # Set to max hatches
        
        # Update current hatch and redraw
        self.current_hatch = max_hatches
        self.ax.clear()
        self._plot_layer_and_hatches()
        self.fig.canvas.draw_idle()
        
    def update_hatches(self, val):
        self.current_hatch = int(val)
        self.ax.clear()
        self._plot_layer_and_hatches()
        self.fig.canvas.draw_idle()
        
    def _plot_layer_and_hatches(self):
        if 0 <= self.current_layer < len(self.layers):
            layer = self.layers[self.current_layer]
            coordinates = layer.reshape(-1, 4)  # Reshape into groups of 4 (x1,y1,x2,y2)
            coords = coordinates[:self.current_hatch]
    
            # Create arrays for x and y coordinates
            x_coords = np.array([[coord[0], coord[2]] for coord in coords]).T
            y_coords = np.array([[coord[1], coord[3]] for coord in coords]).T
            
            # Single plot call for all lines
            self.ax.plot(x_coords, y_coords, 'b-', linewidth=0.5)
            
            self.ax.set_title(f'CLI Visualization - Layer {self.current_layer + 1}/{len(self.layers)}')
            
            x_coords = coordinates[:, [0, 2]].flatten()
            y_coords = coordinates[:, [1, 3]].flatten()
            # Adjust view to show all data points
            if len(coordinates) > 0:
                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)
                
                padding = 0.1 * max(x_max - x_min, y_max - y_min)
                self.ax.set_xlim(x_min - padding, x_max + padding)
                self.ax.set_ylim(y_min - padding, y_max + padding)


# visualizer = CLIVisualizer("staging\hatches.cli")
# visualizer.read_cli_file()
# visualizer.plot_with_slider()