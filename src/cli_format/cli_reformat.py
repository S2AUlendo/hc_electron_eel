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
import multiprocessing


class CLIReformat:
    def __init__(self, filepath, output_location, original_name, output_name, progress, selected_material, selected_machine, data=None, feature=2000, mp_output_queue=None):
        # Configuration parameters
        self.FACTOR = 1
        self.LAYER_GROUP = 10
        self.dx = self.FACTOR  # mm
        self.dy = self.FACTOR  # mm
        self.feature = feature

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
        self.end_file_indice = 0
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
        # self.mp_progress = multiprocessing.Value('i', 0)

        if filepath:
            with open(filepath, "r") as file:
                self.data = file.readlines()
        else:
            self.data = data.splitlines()

        self.parse_cli_header()
        self.retrieve_indices()

    def retrieve_indices(self):

        self.layer_indices = np.where(
            np.char.startswith(self.data, "$$LAYER/"))[0]
        self.hatch_indices = np.where(
            np.char.startswith(self.data, "$$HATCHES/"))[0]
        self.display_message(f"Hatch Indicies {len(self.hatch_indices)}")

        self.polyline_indices = np.where(
            np.char.startswith(self.data, "$$POLYLINE/"))[0]
        self.display_message(f"Polyline Indicies {len(self.polyline_indices)}")

        self.hatch_indices = np.array(self.hatch_indices)

        self.end_file_indices = np.where(
            np.char.startswith(self.data, "$$GEOMETRYEND"))[0]

        self.display_message(f"Layer Indicies {len(self.layer_indices)}")
        self.layer_indices = np.array(self.layer_indices)
        # Add the last index of file as a dummy layer
        self.layer_indices = np.append(
            self.layer_indices, self.end_file_indices)

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
                    self.hatch_lines[layer_num] = np.vstack(
                        (self.hatch_lines[layer_num], numbers))

            self.layer_data[layer_num] = {
                'hatch_data': hatch_data,
                'hatch_feature_indices': hatch_feature_indices,
                'polyline_feature_indices': polyline_feature_indices
            }

    def optimize_and_write(self):
        output_dir = self.filelocation

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.progress['msg'] = f"Creating output file..."
        ori_path = os.path.join("data", self.ori_filename)
        output_file = os.path.join(output_dir, self.opt_filename)

        layer_data = []
        for layer_num in range(len(self.layer_indices)-1):
            layer_data.append((
                layer_num,
                self.hatch_lines.get(layer_num, np.empty(0)),
                self.layer_data[layer_num]
            ))

        # Create parallel processing pool
        self.progress['msg'] = f"Starting pool..."
        with Pool(processes=cpu_count() - 2) as pool:
            results = pool.starmap(self.process_layer, layer_data)

        results.sort(key=lambda x: x[0])

        try:
            with open(ori_path, "w") as ori_file, open(output_file, "w") as opt_file:
                header = (
                    "$$HEADERSTART\n"
                    f"$$ASCII\n$$UNITS/{self.units}\n"
                    f"$$VERSION/{self.version}\n$$DATE/{self.date}\n"
                    f"$$DIMENSION/{self.dimension}\n"
                    f"$$LAYERS/{self.layers}\n$$LABEL/{self.label}\n"
                    "$$HEADEREND\n"
                )
                ori_file.write(header)
                opt_file.write(header)

                for layer_num, ori_lines, opt_lines in results:

                    ori_file.write(f"$$LAYER/{layer_num:.3f}\n")
                    opt_file.write(f"$$LAYER/{layer_num:.3f}\n")

                    ori_file.writelines(ori_lines)
                    opt_file.writelines(opt_lines)

                # Write footers
                ori_file.write("$$GEOMETRYEND\n")
                opt_file.write("$$GEOMETRYEND\n")

        except Exception as e:
            self.display_message(traceback.format_exc())
            self.display_message(f"Error: {e}")
            raise Exception(traceback.format_exc()) from e

    def process_layer(self, layer_num, hatch_lines, layer_info):
        try:
            sorted_layers = np.array([])
            v0_evInit = None
            # Initialize empty results
            ori_lines, opt_lines = [], []

            if hatch_lines.ndim == 1 or hatch_lines.shape[0] < 3:
                # Simple case handling
                optimized_sequence = hatch_lines[:, -
                                                 1] if hatch_lines.ndim > 1 else hatch_lines
                r_opt, r_ori = [], []
            else:
                # Full processing
                new_layer, *_ = cvs_hatch_to_voxel(hatch_lines, 67, 1, 1)
                sorted_layers = stack_layers(new_layer, np.empty(0), 2)

                try:
                    optimized_sequence, v0_evInit, r_opt, r_ori = smartScanCore(numbers_set=self.hatch_lines[layer_num],
                                                                                Sorted_layers=sorted_layers,
                                                                                dx=self.dx, dy=self.dy,
                                                                                reduced_order=50,
                                                                                kt=float(
                                                                                    self.selected_material['kt']),
                                                                                rho=float(
                                                                                    self.selected_material['rho']),
                                                                                cp=float(
                                                                                    self.selected_material['cp']),
                                                                                vs=float(
                                                                                    self.selected_machine['vs']),
                                                                                h=float(
                                                                                    self.selected_material['h']),
                                                                                P=float(
                                                                                    self.selected_machine['P']),
                                                                                v0_ev=v0_evInit
                                                                                )
                except Exception:
                    optimized_sequence = hatch_lines[:, -1]
                    r_opt, r_ori = 0, 0

            # Build output lines
            ori_lines.append(f"//R/{r_ori}//\n")
            opt_lines.append(f"//R/{r_opt}//\n")

            if hatch_lines.ndim == 1:
                ori_lines.append(f"{layer_info['hatch_data'][0]}\n")
                opt_lines.append(f"{layer_info['hatch_data'][0]}\n")
            else:
                for seq in optimized_sequence:
                    opt_lines.append(f"{layer_info['hatch_data'][seq]}\n")
                for seq in hatch_lines[:, -1]:
                    ori_lines.append(f"{layer_info['hatch_data'][seq]}\n")

            # Add polylines
            for polyline in layer_info['polyline_feature_indices']:
                line = f"{polyline}\n"  # Adjust based on actual data format
                ori_lines.append(line)
                opt_lines.append(line)

            # with self.mp_progress.get_lock():
            #     self.mp_progress.value += 1
            #     self.progress['value'] = self.mp_progress.value

            return (layer_num, ori_lines, opt_lines)

        except Exception as e:
            print(f"Error processing layer {layer_num}: {str(e)}")
            return (layer_num, ["ERROR\n"], ["ERROR\n"])

    def get_and_check_dimensions(self):
        self.dimension_x = np.max(self.x_max_values) - \
            np.min(self.x_min_values)
        self.dimension_y = np.max(self.y_max_values) - \
            np.min(self.y_min_values)
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
                raise OverLimitException(
                    "Build dimensions exceed allowed limits. Please upgrade your license key to increase the build volume limit.")

            # Optimize and write output file
            self.optimize_and_write()

            minimum_x = np.min(self.x_min_values)
            minimum_y = np.min(self.y_min_values)

            # Iterate over layers
            for ii in range(len(self.layer_indices)-1):
                if ii in self.hatch_lines:
                    if self.hatch_lines[ii].ndim == 1:
                        self.hatch_lines[ii][[
                            0, 2]] = self.hatch_lines[ii][[0, 2]] - minimum_x
                        self.hatch_lines[ii][[
                            1, 3]] = self.hatch_lines[ii][[1, 3]] - minimum_y
                    else:
                        self.hatch_lines[ii][:, [
                            0, 2]] = self.hatch_lines[ii][:, [0, 2]] - minimum_x
                        self.hatch_lines[ii][:, [
                            1, 3]] = self.hatch_lines[ii][:, [1, 3]] - minimum_y

            self.progress["msg"] = "Completed"

            return {
                "status": "success",
                "output": self.opt_filename
            }

        except OverLimitException as e:
            self.display_message(traceback.format_exc())
            return {
                "status": "error",
                "error_type": "OverLimitException",
                "message": str(e)
            }
        except Exception as e:
            self.display_message(traceback.format_exc())
            return {
                "status": "error",
                "error_type": "GeneralError",
                "message": str(e)
            }
