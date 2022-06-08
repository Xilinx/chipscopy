# Copyright 2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import csv
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING
from dataclasses import dataclass
from collections import OrderedDict

try:
    import pandas as pd
    import plotly.graph_objects as go

    _plotting_pkgs_available = True
except ImportError:
    _plotting_pkgs_available = False

try:
    from IPython import get_ipython
    from IPython.display import Image, display

    _jupyter_available = True
except ImportError:
    get_ipython = None
    Image = None
    display = None
    _jupyter_available = False

from chipscopy.dm import request
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy.utils.printer import PercentProgressBar, printer

if TYPE_CHECKING:
    from chipscopy.client.ddrmc_client import DDRMCClient


@dataclass
class DDR(DebugCore["DDRMCClient"]):
    """
    This class contains the top level API functions to interact with the
    integrated DDR memory controller debug core(s) on Versal devices.

    """

    def __init__(self, ddr_node):
        super(DDR, self).__init__(CoreType.DDR, ddr_node)
        self.node_name = ddr_node.props["Name"]
        self.mc_index = ddr_node.props["mc_index"]
        self.mc_loc = ddr_node.props["mc_loc"]
        self.name = "ddr_" + self.mc_index
        self.ddr_node = self.core_tcf_node
        self.is_enabled = self.is_user_enabled()
        self.eye_scan_data = []
        self.filter_by = {"name": self.name, "mc_index": self.mc_index, "mc_loc": self.mc_loc}

    def get_cal_status(self):
        """
        Get the main calibration status of DDRMC

        Args:

        Returns:
            status in string

        """

        status = self.ddr_node.get_cal_status()

        return status

    def refresh_cal_status(self, done: DoneHWCommand = None):
        """
        Refresh the main calibration status of DDRMC

        Args:
            done: Optional command callback that will be invoked when the response is received

        Returns:

        """

        self.ddr_node.refresh_cal_status(done)

    def get_cal_stages(self):
        """
        Get the decoded calibration stages results happened from a
        calibration run

        Args:

        Returns:
            A dictionary where
                Key = calibration stage name
                Val = stage calibration result

        """
        results = {}
        results = self.ddr_node.get_property_group(["stages"])

        return results

    def refresh_cal_margin(self, done: DoneHWCommand = None):
        """
        Refresh the calibration windows margin analysis of DDRMC

        Args:
            done: Optional command callback that will be invoked when the response is received

        Returns:

        """

        self.ddr_node.refresh_cal_margin(done)

    def refresh_health_status(self, done: DoneHWCommand = None):
        """
        Refresh the overall health status analysis of DDRMC

        Args:
            done: Optional command callback that will be invoked when the response is received

        Returns:

        """

        self.ddr_node.refresh_health_status(done)

    def get_cal_margin_mode(self):
        """
        Get the availability of windows margin mode generated from a
        calibration run

        Args:

        Returns:
            A dictionary where
                Key = name of margin mode
                Val = True or False value indicating the availability

        """
        results = {}

        results = self.ddr_node.get_cal_margin_mode()

        return results

    def is_user_enabled(self):
        """
        Find out whether the DDRMC core is user enabled or not after
        Versal device configuration

        Args:

        Returns:
            Status value in Bool

        """
        # if not being powered by NoC clock, it is automatically disabled
        clock_off = self.ddr_node.is_clock_gated()

        if clock_off:
            return False
        else:
            result = {}
            key = "pcsr_control_ub_init"
            result = self.ddr_node.get_property(key)

            if not result[key]:
                return False
            else:
                return True

    def get_property(self, property_names=None, done: DoneHWCommand = None):
        """
        Get the property value mapped to DDRMC core

        Args:
            property_names: single string or list of string of property names
                (if None specified, all properties available will be queried and returned)

            done: Optional command callback that will be invoked when the response is received

        Returns:
            A dictionary, where
                Key = property name
                Val = property value

        """
        results = {}

        results = self.ddr_node.get_property(property_names, done)

        return results

    def __get_configuration(self) -> OrderedDict:
        configs = OrderedDict()
        is_lrdimm = False

        configs["DDRMC Core Name"] = self.name

        results = self.ddr_node.get_property("mem_type")
        val = results["mem_type"]
        if val == 1:
            configs["Memory Interface"] = "DDR4"
        elif val == 2:
            configs["Memory Interface"] = "LPDDR4"
        else:
            configs["Memory Interface"] = "Unknown"

        results = self.ddr_node.get_property("dimm_type")
        val = results["dimm_type"]
        if val == 0:
            configs["Device Type"] = "Component"
        elif val == 1:
            configs["Device Type"] = "UDIMM"
        elif val == 2:
            configs["Device Type"] = "RDIMM"
        elif val == 3:
            configs["Device Type"] = "LRDIMM"
            is_lrdimm = True
        else:
            configs["Device Type"] = "Unknown"

        configs["MC Location"] = self.mc_loc

        results = self.ddr_node.get_property("slots")
        slots = results["slots"]
        results = self.ddr_node.get_property("phy_ranks")
        phy_ranks = results["phy_ranks"]
        results = self.ddr_node.get_property("mem_ranks")
        mem_ranks = results["mem_ranks"]

        if is_lrdimm:
            configs["Slots"] = str(phy_ranks)
            configs["Ranks"] = str(mem_ranks)
        else:
            configs["Slots"] = str(slots)
            configs["Ranks"] = str(phy_ranks)

        results = self.ddr_node.get_property("bytes")
        bytes = results["bytes"]
        results = self.ddr_node.get_property("nibbles")
        nibbles = results["nibbles"]
        results = self.ddr_node.get_property("bits_per_byte")
        bits = results["bits_per_byte"]
        data_width = bytes * bits
        configs["Data Width"] = str(data_width)
        configs["Bytes"] = str(bytes)
        configs["Nibbles"] = str(nibbles)
        configs["Bits per Byte"] = str(bits)

        freq_zero = "Unknown"
        freq_one = "Unknown"
        results = self.ddr_node.get_property("f0_period")
        period = results["f0_period"]
        if (period != "0") and (period != ""):
            freq0 = int(1000000 / float(period) + 0.5)
            freq_zero = str(freq0) + " MHz"
        results = self.ddr_node.get_property("f1_period")
        period = results["f1_period"]
        if (period != "0") and (period != ""):
            freq1 = int(1000000 / float(period) + 0.5)
            freq_one = str(freq1) + " MHz"
        results = self.ddr_node.get_property("dual_freq_en")
        dual_freq = results["dual_freq_en"]
        configs["Memory Frequency 0"] = freq_zero
        if int(dual_freq) > 0:
            configs["Memory Frequency 1"] = freq_one

        return configs

    def __get_cal_margins(self, mode_base: str, left_margs: Dict, right_margs: Dict, centers: Dict):
        group_name = mode_base + "_left"
        results = self.ddr_node.get_property_group([group_name])
        left_margs.clear()
        left_margs.update(results)
        group_name = mode_base + "_right"
        results = self.ddr_node.get_property_group([group_name])
        right_margs.clear()
        right_margs.update(results)
        group_name = mode_base + "_center"
        results = self.ddr_node.get_property_group([group_name])
        centers.clear()
        centers.update(results)

    def __output_read_margins(
        self,
        by_8_mode,
        bytes: int,
        nibbles: int,
        left_margs: Dict,
        right_margs: Dict,
        centers: Dict,
    ):
        left_marg_vals = sorted(left_margs.items())
        center_vals = sorted(centers.items())
        right_marg_vals = sorted(right_margs.items())

        if by_8_mode:
            for byte in range(bytes):
                left_marg = left_marg_vals[byte * 2][1]
                center = center_vals[byte * 2][1]
                right_marg = right_marg_vals[byte * 2][1]
                printer(
                    "Byte ",
                    str(byte),
                    " Nibble 0  -",
                    "  Left Margin:  ",
                    str(left_marg[1]),
                    " (",
                    str(left_marg[0]),
                    ")  Center Point:  ",
                    str(center[1]),
                    " (",
                    str(center[0]),
                    ")  Right Margin:  ",
                    str(right_marg[1]),
                    " (",
                    str(right_marg[0]),
                    ")",
                )

                left_marg = left_marg_vals[byte * 2 + 1][1]
                center = center_vals[byte * 2 + 1][1]
                right_marg = right_marg_vals[byte * 2 + 1][1]
                printer(
                    "Byte ",
                    str(byte),
                    " Nibble 1  -",
                    "  Left Margin:  ",
                    str(left_marg[1]),
                    " (",
                    str(left_marg[0]),
                    ")  Center Point:  ",
                    str(center[1]),
                    " (",
                    str(center[0]),
                    ")  Right Margin:  ",
                    str(right_marg[1]),
                    " (",
                    str(right_marg[0]),
                    ")",
                )
        else:
            for nibble in range(nibbles):
                left_marg = left_marg_vals[nibble][1]
                center = center_vals[nibble][1]
                right_marg = right_marg_vals[nibble][1]
                printer(
                    "Nibble ",
                    str(nibble),
                    "  -" "  Left Margin:  ",
                    str(left_marg[1]),
                    " (",
                    str(left_marg[0]),
                    ")  Center Point:  ",
                    str(center[1]),
                    " (",
                    str(center[0]),
                    ")  Right Margin:  ",
                    str(right_marg[1]),
                    " (",
                    str(right_marg[0]),
                    ")",
                )

    def __output_write_margins(
        self, bytes: int, left_margs: Dict, right_margs: Dict, centers: Dict
    ):
        left_marg_vals = sorted(left_margs.items())
        center_vals = sorted(centers.items())
        right_marg_vals = sorted(right_margs.items())

        for byte in range(bytes):
            left_marg = left_marg_vals[byte][1]
            center = center_vals[byte][1]
            right_marg = right_marg_vals[byte][1]
            printer(
                "Byte ",
                str(byte),
                "  -" "  Left Margin:  ",
                str(left_marg[1]),
                " (",
                str(left_marg[0]),
                ")  Center Point:  ",
                str(center[1]),
                " (",
                str(center[0]),
                ")  Right Margin:  ",
                str(right_marg[1]),
                " (",
                str(right_marg[0]),
                ")",
            )

    def report(self, to_file=False, file_name=None):
        """
        Run a report on the current statuses and analytical data of the DDRMC

        Args:
            to_file: specify True to have the report saved to a file

            file_name: the file name or full path for the report file to be saved

        Returns:

        """
        out_file = None
        orig_out = None

        if to_file:
            if not file_name:
                printer("\nNOTE: Need to specify a file name for the report output.")
            else:
                out_file = open(file_name, "w")
                printer("\nNOTE: The report is being generated and saved as:", file_name)
                orig_out = sys.stdout
                sys.stdout = out_file

        # DDRMC Status & Message
        printer("-------------------\n")
        printer(" DDRMC Status \n")
        printer("-------------------\n")
        self.refresh_cal_status()
        self.refresh_health_status()
        printer("Calibration Status:  ", self.get_cal_status(), "\n")
        results = self.ddr_node.get_property("health_status")
        printer("Overall Health:  ", results["health_status"], "\n")
        results = self.ddr_node.get_property("cal_message")
        printer("Message:  ", results["cal_message"], "\n")

        # Check if there is error condition to report
        results = self.ddr_node.get_property("cal_error_msg")
        if results["cal_error_msg"] != "None":
            printer("Error:  ", results["cal_error_msg"], "\n")

        # DDRMC ISR Registers
        printer("\n-------------------\n")
        printer(" Status Registers\n")
        printer("-------------------\n")

        printer("DDRMC ISR Table\n")
        results = self.ddr_node.get_property_group(["ddrmc_isr_e", "ddrmc_isr_w"])
        for key, val in sorted(results.items()):
            printer("  ", key, ":  ", str(val))

        printer("\nUB ISR Table\n")
        results = self.ddr_node.get_property_group(["ub_isr_e", "ub_isr_w"])
        for key, val in sorted(results.items()):
            printer("  ", key, ":  ", str(val))

        # Memory configuration info
        printer("\n----------------------------------\n")
        printer(" Memory Configuration \n")
        printer("----------------------------------\n")
        configs = self.__get_configuration()
        for key, val in configs.items():
            printer(key, ":  ", val)

        # Memory calibration stages info
        printer("\n-----------------------------------\n")
        printer(" Calibration Stages Information \n")
        printer("-----------------------------------\n")
        # Do not do calibration stages if a system error is detected
        sys_error = False
        if self.get_cal_status() == "SYSTEM ERROR":
            sys_error = True
        if not sys_error:
            results = self.get_cal_stages()
            for key, val in sorted(results.items()):
                printer(key, ":  ", val)
        else:
            printer(
                "\nNote: DDRMC system error is detected. Calibration stages decoding will not be provided for ",
                self.name,
                "\n",
            )

        # Cal Margin Analysis
        printer("\n---------------------------------------\n")
        printer(" Calibration Window Margin Analysis \n")
        printer("---------------------------------------\n")

        if not sys_error:
            cal_margin_modes = {}
            left_margins = {}
            right_margins = {}
            center_points = {}
            is_by_8 = True
            num_byte = int(configs["Bytes"])
            num_nibble = int(configs["Nibbles"])
            self.refresh_cal_margin()
            cal_margin_modes = self.get_cal_margin_mode()
            if int(configs["Bits per Byte"]) == 4:
                is_by_8 = False

            # Main loop to go through dual frequencies
            for freq in range(2):
                base = "Frequency " + str(freq)
                # Read Simple
                key = "f" + str(freq) + "_rd_simp"
                if cal_margin_modes[key]:
                    # Rising Edge
                    self.__get_cal_margins(
                        key + "_rise", left_margins, right_margins, center_points
                    )
                    printer(
                        "\n",
                        base,
                        " - Read Margin - Simple Pattern - Rising Edge Clock in pS and (delay taps):\n",
                    )
                    self.__output_read_margins(
                        is_by_8, num_byte, num_nibble, left_margins, right_margins, center_points
                    )
                    # Falling Edge
                    self.__get_cal_margins(
                        key + "_fall", left_margins, right_margins, center_points
                    )
                    printer(
                        "\n",
                        base,
                        " - Read Margin - Simple Pattern - Falling Edge Clock in pS and (delay taps):\n",
                    )
                    self.__output_read_margins(
                        is_by_8, num_byte, num_nibble, left_margins, right_margins, center_points
                    )
                # Read Complex
                key = "f" + str(freq) + "_rd_comp"
                if cal_margin_modes[key]:
                    # Rising Edge
                    self.__get_cal_margins(
                        key + "_rise", left_margins, right_margins, center_points
                    )
                    printer(
                        "\n",
                        base,
                        " - Read Margin - Complex Pattern - Rising Edge Clock in pS and (delay taps):\n",
                    )
                    self.__output_read_margins(
                        is_by_8, num_byte, num_nibble, left_margins, right_margins, center_points
                    )
                    # Falling Edge
                    self.__get_cal_margins(
                        key + "_fall", left_margins, right_margins, center_points
                    )
                    printer(
                        "\n",
                        base,
                        " - Read Margin - Complex Pattern - Falling Edge Clock in pS and (delay taps):\n",
                    )
                    self.__output_read_margins(
                        is_by_8, num_byte, num_nibble, left_margins, right_margins, center_points
                    )
                # Write Simple
                key = "f" + str(freq) + "_wr_simp"
                if cal_margin_modes[key]:
                    self.__get_cal_margins(key, left_margins, right_margins, center_points)
                    printer(
                        "\n",
                        base,
                        " - Write Margin - Simple Pattern - Calibration Window in pS and (delay taps):\n",
                    )
                    self.__output_write_margins(
                        num_byte, left_margins, right_margins, center_points
                    )
                # Write Complex
                key = "f" + str(freq) + "_wr_comp"
                if cal_margin_modes[key]:
                    self.__get_cal_margins(key, left_margins, right_margins, center_points)
                    printer(
                        "\n",
                        base,
                        " - Write Margin - Complex Pattern - Calibration Window in pS and (delay taps):\n",
                    )
                    self.__output_write_margins(
                        num_byte, left_margins, right_margins, center_points
                    )
        else:
            printer(
                "\nNote: DDRMC system error is detected. Margin Analysis will not be provided for ",
                self.name,
                "\n",
            )

        if out_file:
            sys.stdout = orig_out
            out_file.close()

        return

    def set_eye_scan_read_mode(self):
        """
        Set 2D eye scan to read mode

        Args:

        Returns:

        """
        self.ddr_node.set_property({"mgchk_rw_mode": 0})
        self.ddr_node.commit_property_group([])

        return

    def set_eye_scan_write_mode(self):
        """
        Set 2D eye scan to write mode

        Args:

        Returns:

        """
        self.ddr_node.set_property({"mgchk_rw_mode": 1})
        self.ddr_node.commit_property_group([])

        return

    def set_eye_scan_simple_pattern(self):
        """
        Set 2D eye scan traffic pattern to simple mode

        Args:

        Returns:

        """
        self.ddr_node.set_property({"mgchk_pattern_mode": 0})
        self.ddr_node.commit_property_group([])

        return

    def set_eye_scan_complex_pattern(self):
        """
        Set 2D eye scan traffic pattern to complex mode

        Args:

        Returns:

        """
        self.ddr_node.set_property({"mgchk_pattern_mode": 1})
        self.ddr_node.commit_property_group([])

        return

    def set_eye_scan_rank(self, rank_num: int):
        """
        Set the target rank number on the DDR for 2D eye scan to run on.
        There will be 4 total possible rank selections. For single slot designs, there will be quad ranks.
        For dual slot designs, there will be dual ranks per slot.
        2D Margin Scan can only be performed on one rank at a time, and not in parallel.

        Args:

            rank_num:
                Rank number valid between 0 and 3 on the DDR for 2D Margin to be run on.

        Returns:

        """
        if isinstance(rank_num, str):
            printer("ERROR: Please enter an integer value from 0 to 3 for Slot/Rank selection.")
            return
        elif rank_num > 3:
            printer("ERROR: Cannot enter a rank_num value larger than 3.")
            return

        self.ddr_node.set_property({"mgchk_rank": rank_num})
        self.ddr_node.commit_property_group([])

        return

    def get_eye_scan_vref_percentage(self, vref: int) -> float:
        """
        A user helper function that takes in an encoding vref value intended for the margin scan,
        and converts it into a percentage value based on the current scan mode
        and memory configuration detected from the current hardware.

        Args:

            vref:
                For Read mode, valid integer range between 0 to 1023
                For Write mode, valid integer range between 0 to 50

        Returns:

            A translated percentage number in floating point

        """
        if isinstance(vref, str):
            printer("ERROR: Please re-enter an integer value for Vref.")
            return
        elif vref > 1023:
            printer("ERROR: Cannot enter VRef values larger than 1023")
            return

        base_value = 0
        incr_size = 0
        ddr4_range_one = 60
        ddr4_range_two = 45
        lp4_range_one = 10
        lp4_range_two = 20.4
        ddr4_incr_size = 0.65
        lp4_incr_size = 0.4
        read_incr_size = 0.0976563
        prop_list = []

        prop_list.append("mgchk_rw_mode")
        prop_list.append("mem_type")
        prop_list.append("mgchk_def_wr_vref_range")

        results = self.ddr_node.get_property(prop_list)
        rw_mode = results["mgchk_rw_mode"]
        mem_type = results["mem_type"]
        write_vref_range = results["mgchk_def_wr_vref_range"]

        if rw_mode:
            if vref > 50:
                printer("ERROR: Cannot enter Vref values larger than 50 for Write Margin mode")
                return
            if mem_type == 1:
                if write_vref_range == 0:
                    base_value = ddr4_range_one
                else:
                    base_value = ddr4_range_two
                incr_size = ddr4_incr_size
            elif mem_type == 2:
                if write_vref_range == 0:
                    base_value = lp4_range_one
                else:
                    base_value = lp4_range_two
                incr_size = lp4_incr_size
        else:
            incr_size = read_incr_size

        offset_value = vref * incr_size
        output_vref = base_value + offset_value

        if not rw_mode:
            output_vref = "%.3f" % output_vref
        else:
            output_vref = "%.2f" % output_vref

        return float(output_vref)

    def set_eye_scan_vref_min(self, vref: int) -> float:
        """
        Set 2D eye scan desired minimum vref value to scan

        Args:

            vref:
                For Read mode, valid integer range between 0 to 1023
                For Write mode, valid integer range between 0 to 50

        Returns:

            A translated percentage number in floating point if
            the input VRef is set successfully

        """
        percent_vref = self.get_eye_scan_vref_percentage(vref)

        if percent_vref is not None:
            vref = int(vref)
            self.ddr_node.set_property({"es_vref_min": vref})
            return percent_vref

    def set_eye_scan_vref_max(self, vref: int) -> float:
        """
        Set 2D eye scan desired maximum vref value to scan

        Args:

            vref:
                For Read mode, valid integer range between 0 to 1023
                For Write mode, valid integer range between 0 to 50

        Returns:

            A translated percentage number in floating point if
            the input VRef is set successfully

        """
        percent_vref = self.get_eye_scan_vref_percentage(vref)

        if percent_vref is not None:
            vref = int(vref)
            self.ddr_node.set_property({"es_vref_max": vref})
            return percent_vref

    def set_eye_scan_vref_steps(self, steps: int):
        """
        Set 2D eye scan desired number of vref steps to scan vertically

        Args:

            steps:
                Valid integer range between 1 to 1024 for Read mode.
                Valid integer range between 1 to 51 for Write mode.

        Returns:

        """
        results = self.ddr_node.get_property(["mgchk_rw_mode"])
        rw_mode = results["mgchk_rw_mode"]

        if isinstance(steps, str):
            printer("ERROR: Please re-enter an integer value for Vref steps.")
            return
        elif rw_mode and (steps > 51):
            printer("ERROR: Cannot enter Vref step sizes larger than 51 for Write Margin mode")
            return
        elif steps > 1024:
            printer("ERROR: Cannot enter Vref step sizes larger than 1024 for Read Margin mode")
            return

        steps = int(steps)
        self.ddr_node.set_property({"es_vref_steps": steps})

        return

    def __update_eye_scan_data(self):
        edges = ["left", "right"]
        clocks = ["nqtr", "pqtr"]
        clock_defs = {
            "nqtr": "fall_",
            "pqtr": "rise_",
        }
        data_list = []

        engine_data = self.ddr_node.get_eye_scan_data()
        ps_factors = self.ddr_node.get_margin_ps_factors()
        data_length = len(engine_data)

        # If initial vref scan went wrong after enabled, needless to process data further
        if not data_length > 1:
            return

        scan_mode = engine_data[0]["config.mode"]
        nibble_count = engine_data[0]["config.nibbles"]
        byte_count = engine_data[0]["config.bytes"]
        data_list.append(engine_data[0])

        if "Read" in scan_mode:
            old_key_base = "rdmargin_"
            new_key_base = "read_"
            for data in engine_data[1:]:
                for nibble in range(int(nibble_count)):
                    for clock in clocks:
                        for edge in edges:
                            old_key = (
                                old_key_base
                                + clock
                                + "_"
                                + edge
                                + "_nibble"
                                + "{:02d}".format(nibble)
                            )
                            ps_name = new_key_base + clock_defs[clock] + "{:02d}".format(nibble)
                            new_key = ps_name + "_" + edge
                            new_key_ps = new_key + "_ps"
                            ps_factor = ps_factors[ps_name]
                            tap_value = data[old_key]
                            ps_value = int(round(tap_value * ps_factor))
                            data[new_key] = tap_value
                            data[new_key_ps] = ps_value
                            del data[old_key]
                temp_data = {key: val for key, val in data.items() if "wrmargin" not in key}
                new_data = OrderedDict(sorted(temp_data.items()))
                data_list.append(new_data)
        else:
            old_key_base = "wrmargin_"
            new_key_base = "write_"
            for data in engine_data[1:]:
                for byte in range(int(byte_count)):
                    for edge in edges:
                        old_key = old_key_base + edge + "_byte" + str(byte)
                        ps_name = new_key_base + "{:02d}".format(byte)
                        new_key = ps_name + "_" + edge
                        new_key_ps = new_key + "_ps"
                        ps_factor = ps_factors[ps_name]
                        tap_value = data[old_key]
                        ps_value = int(round(tap_value * ps_factor))
                        data[new_key] = tap_value
                        data[new_key_ps] = ps_value
                        del data[old_key]
                temp_data = {key: val for key, val in data.items() if "rdmargin" not in key}
                new_data = OrderedDict(sorted(temp_data.items()))
                data_list.append(new_data)

        self.eye_scan_data = data_list
        self.ddr_node.set_property({"es_data_need_update": 0})

    def __draw_eye_scan_graph(
        self, margin_data: List, base_name: str, margin_title: str, def_vref: float
    ):
        vrefs = []
        left_margs = []
        right_margs = []
        left_ps = []
        right_ps = []
        x_min = 0
        x_max = 0

        for data in margin_data:
            vrefs.append(float(data["config.vrefp"]))
            key_name = base_name + "_left"
            left_margs.append(int(data[key_name]))
            key_name += "_ps"
            left_ps.append(int(data[key_name]))
            key_name = base_name + "_right"
            right_margs.append(int(data[key_name]))
            key_name += "_ps"
            right_ps.append(int(data[key_name]))

        x_min = max(left_ps)
        x_max = max(right_ps)

        data_defs = {
            "VRef": vrefs,
            "Left_Margin": left_margs,
            "Right_Margin": right_margs,
            "Left_PS": left_ps,
            "Right_PS": right_ps,
        }

        df = pd.DataFrame(data_defs)
        fig = go.Figure()

        for col in df.columns[1:2]:
            df_left = df[col]
            ps_left = df[df.columns[3]]
            data_left = list(zip(df_left, ps_left))
            fig.add_trace(
                go.Bar(
                    x=-ps_left.values,
                    y=df[df.columns[0]],
                    orientation="h",
                    name=col,
                    customdata=data_left,
                    marker_color="#75ad0a",
                    hovertemplate="Taps: %{customdata[0]} <br>pS: %{customdata[1]} <br>VRef: %{y}",
                )
            )

        for col in df.columns[2:3]:
            df_right = df[col]
            ps_right = df[df.columns[4]]
            data_right = list(zip(df_right, ps_right))
            fig.add_trace(
                go.Bar(
                    x=ps_right,
                    y=df[df.columns[0]],
                    orientation="h",
                    name=col,
                    customdata=data_right,
                    marker_color="#0073e6",
                    hovertemplate="Taps: %{customdata[0]} <br>pS: %{customdata[1]} <br>VRef: %{y}",
                )
            )

        fig.add_trace(
            go.Scatter(
                x=[-x_min, x_max],
                y=[def_vref, def_vref],
                mode="lines",
                line=dict(
                    color="#92b1a9",
                    width=4,
                    dash="dot",
                ),
                name="DDRMC VRef: " + str(def_vref),
                customdata=[x_min, x_max],
                hovertemplate="%{customdata}",
            )
        )

        fig.update_layout(
            barmode="relative",
            height=600,
            width=900,
            bargap=0.01,
            plot_bgcolor="#0f263e",
            title=margin_title,
            xaxis=dict(title="Delay in pS"),
            yaxis=dict(title="VRef Percentage"),
            legend_orientation="v",
            legend_x=1.0,
            legend_y=0.0,
        )

        return fig

    def save_eye_scan_data(self, file_name=None):
        """
        Save the eye scan 2D margin data from the most recent run to a file in CSV format

        Args:

            file_name: the file name or full path for the data file to be saved.
                       A default file name will be given if none is supplied.

        Returns:

        """
        out_file = None

        if not file_name:
            # Gives a default for users
            file_name = "eye_scan_data"

        file_name = os.path.splitext(file_name)[0] + ".csv"
        self.__update_eye_scan_data()

        if not self.eye_scan_data:
            printer("ERROR: No scan data is found. Please re-run 2D eye scan.")
            return

        data_list = self.eye_scan_data
        keys = list(data_list[0].keys())
        more_keys = list(data_list[1].keys())
        keys.extend(more_keys)

        with open(file_name, "w", newline="") as out_file:
            data_writer = csv.DictWriter(out_file, keys)
            data_writer.writeheader()
            data_writer.writerows(data_list)
            printer("\nInfo: Data are being formatted and saved to:", out_file.name)

    def load_eye_scan_data(self, file_name):
        """
        Load the eye scan 2D margin data from a data file

        Args:

            file_name: the file name or full path for the data file to be read and load

        Returns:

        """
        file_path = Path(file_name)
        data_list = []

        with file_path.open(mode="r") as data_file:
            reader = csv.DictReader(data_file)
            data_reader = list(reader)
            for data in data_reader:
                data_list.append(data)
            file_name = data_file.name

        self.eye_scan_data = data_list
        self.ddr_node.set_property({"es_data_need_update": 0})
        printer("\nInfo: Scan data are being loaded successfully from:", file_name)

    def run_eye_scan(self, done: request.DoneFutureCallback = None) -> bool or request.CsFuture:
        """
        Kick off a run on 2D margin analysis and prepare scan data which is needed to draw an
        eye scan graph. The default scan settings will be used if users have not configured with
        new settings. See the following related commands for more info:

            save_eye_scan_data()
            load_eye_scan_data()
            display_eye_scan()

        Args:
            done: Optional command callback that will be invoked when the scan is finished

        Returns:
            Boolean value indicating success of the 2D margin scan

        """

        # Perform some logical data check on user settings
        prop_list = []
        prop_list.append("mgchk_rw_mode")
        prop_list.append("es_vref_min")
        prop_list.append("es_vref_max")
        prop_list.append("es_vref_steps")

        results = self.ddr_node.get_property(prop_list)
        rw_mode = results["mgchk_rw_mode"]
        vref_min = results["es_vref_min"]
        vref_max = results["es_vref_max"]
        vref_steps = results["es_vref_steps"]

        if rw_mode:
            if (vref_min > 50) or (vref_max > 50):
                printer("ERROR: Cannot set Vref values larger than 50 under Write margin mode.")
                return False
            if vref_steps > 51:
                printer("ERROR: Cannot set Vref step sizes larger than 51 for Write Margin mode")
                return False

        if vref_min > vref_max:
            printer("ERROR: Cannot set minimum Vref value larger than maximum Vref value.")
            return False

        percent_min = self.get_eye_scan_vref_percentage(vref_min)
        percent_max = self.get_eye_scan_vref_percentage(vref_max)
        printer("Min VRef is set at: ", percent_min, "%, value ", vref_min)
        printer("Max VRef is set at: ", percent_max, "%, value ", vref_max)
        printer("Number of VRef steps is set at: ", vref_steps)

        vref_incr_size = int((vref_max - vref_min) / (vref_steps - 1))
        max_step_size = vref_max - vref_min + 1

        if vref_incr_size < 1:
            printer(
                "ERROR: For the selected VRef Min and VRef Max, the maximum step size is: ",
                str(max_step_size),
            )
            printer(
                "Please either reduce the VRef steps or increase the VRef range by adjusting Min/Max."
            )
            return False

        scan_future = request.CsFutureSync(done)

        # Institute a Progress Bar
        progress_bar = PercentProgressBar()
        in_progress = "[bold dodger_blue2]In Progress[/]"
        progress_bar.add_task(
            description="2D Margin Scan Progress",
            status=PercentProgressBar.Status.STARTING,
            visible=True,
        )

        def progress_update(future):
            progress_bar.update(completed=future.progress * 100, status=in_progress)

        def done_scan(future):
            if future.error is not None:
                progress_bar.update(status=PercentProgressBar.Status.ABORTED)
            else:
                progress_bar.update(completed=100, status=PercentProgressBar.Status.DONE)

            if future.error:
                scan_future.set_exception(future.error)
            else:
                scan_future.set_result(None)

        def finalize(future):
            # Call on main thread for any final processing desired
            result_list = future._result
            if result_list[0]:
                # Can think about if want to provide auto-draw or
                # auto-save log for the users
                status = "COMPLETED"
            else:
                status = "ERROR"

            printer("2D margin scan run status is: ", status)

        self.ddr_node.future(
            progress=progress_update, done=done_scan, final=finalize
        ).run_eye_scan_async(data_checked=True)
        printer("Info: Margin Scans in progress...")

        return scan_future if done else scan_future.result

    def display_eye_scan(
        self, unit_index: int = 0, return_as_list: bool = False, display_type: str = "dynamic"
    ):
        """
        Assemble and display 2D eye scan drawing in chart format. By default it tries to process and
        draw from the scan data found in the most recent 2D eye scan run. Users have the option to
        load scan data first prior to using this function in order to display specific set of scan
        data, see load_eye_scan_data().

        By default, if no unit_index is specified, unit zero from the scan data will be displayed.
        For read margins, both rising and falling edge clock scan data will be processed and displayed.

        Args:
            unit_index: Specify the index from a set of scan data users intend to display, based on
                unit mode found in the scan settings (bit, nibble, byte)

            return_as_list: Optional argument, default to False. If set to True, the function will
                not display graphs by default. Instead, it returns a list of the grapghing objects
                back to the caller.

            display_type: Optional argument, default to dynamic. If set to static, a static image
                will be returned. If set to dynamic, a dynamic, interactive javascript view will be
                returned.

        Returns:
            A list of Figure object from Plotly, if return_as_list is specified as True,
            None is return otherwise by default.

        """
        if not _plotting_pkgs_available:
            raise ImportError(
                f"Plotting packages not installed! Please run ",
                "'pip install chipscopy[plotly,pandas]'",
            )

        result = self.ddr_node.get_property(["es_data_need_update"])
        data_need_update = result["es_data_need_update"]

        if data_need_update:
            self.eye_scan_data.clear()
            self.__update_eye_scan_data()

        if not self.eye_scan_data:
            printer(
                "ERROR: No scan data is found. Please re-run 2D eye scan, "
                "or load scan data first from a data file."
            )
            return

        if isinstance(unit_index, str):
            printer("ERROR: Please re-enter an integer value for unit_index.")
            return

        figure_list = []
        data_list = self.eye_scan_data
        scan_mode = data_list[0]["config.mode"]
        unit_mode = data_list[0]["config.unit"]
        rank_num = data_list[0]["config.rank"]
        mem_type = data_list[0]["config.mem_type"]
        df_vref = data_list[0]["config.df_vrefp"]
        df_vref = float(df_vref)
        nibble_count = data_list[0]["config.nibbles"]
        byte_count = data_list[0]["config.bytes"]
        unit_val = "{:02d}".format(unit_index)
        data_list = data_list[1:]

        # Some logical data check first on user inputs
        if unit_mode == "nibble":
            if (unit_index < 0) or (unit_index >= int(nibble_count)):
                max_unit = int(nibble_count) - 1
                err_msg = (
                    "ERROR: unit_index given for "
                    + unit_mode
                    + " mode needs to be between 0 and "
                    + str(max_unit)
                )
                err_msg += ", based on current memory configuration."
                printer(err_msg)
                return
        elif unit_mode == "byte":
            if (unit_index < 0) or (unit_index >= int(byte_count)):
                max_unit = int(byte_count) - 1
                err_msg = (
                    "ERROR: unit_index given for "
                    + unit_mode
                    + " mode needs to be between 0 and "
                    + str(max_unit)
                )
                err_msg += ", based on current memory configuration."
                printer(err_msg)
                return

        if "Read" in scan_mode:
            clocks = ["rise_", "fall_"]
            clock_defs = {
                "rise_": " - Rising Edge Clock - ",
                "fall_": " - Falling Edge Clock - ",
            }

            for clock in clocks:
                name_base = "read_" + clock + unit_val
                margin_mode = (
                    scan_mode
                    + clock_defs[clock]
                    + unit_mode.capitalize()
                    + str(unit_index)
                    + "<br>"
                )
                margin_mode += mem_type + " - Rank" + str(rank_num)
                fig = self.__draw_eye_scan_graph(data_list, name_base, margin_mode, df_vref)
                figure_list.append(fig)
        else:
            name_base = "write_" + unit_val
            margin_mode = scan_mode + " - " + unit_mode.capitalize() + str(unit_index) + "<br>"
            margin_mode += mem_type + " - Rank" + str(rank_num)
            fig = self.__draw_eye_scan_graph(data_list, name_base, margin_mode, df_vref)
            figure_list.append(fig)

        if not return_as_list:
            for fig in figure_list:
                if display_type == "dynamic":
                    fig.show()
                elif display_type == "static":
                    if not _jupyter_available:
                        raise ImportError(
                            f"Jupyter packages not installed! Please run 'pip install chipscopy[jupyter]'"
                        )
                    image_bytes = fig.to_image(format="png")
                    ipython_image = Image(image_bytes)
                    display(ipython_image)
                else:
                    raise ValueError("display_type argument must be static or dynamic")
        else:
            return figure_list

    def __str__(self):
        return self.name
