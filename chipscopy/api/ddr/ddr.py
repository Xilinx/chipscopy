# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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
        self.is_gen5 = False
        arch_type = ddr_node.props.get("arch")
        if arch_type:
            if arch_type == "gen5":
                self.is_gen5 = True
                self.crypto_en = False
                self.crypto_type = "N/A"
                self.__get_crypto_status()
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

    def __get_crypto_status(self):
        # Only care if it is Gen5 and User enabled
        if not self.is_enabled:
            return

        props = ["crypto_en", "crypto_status"]
        results = self.ddr_node.get_property(props)

        if results["crypto_en"]:
            self.crypto_en = True

        self.crypto_type = results["crypto_status"]

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
        elif val == 4:
            configs["Memory Interface"] = "DDR5"
        elif val == 5:
            configs["Memory Interface"] = "LPDDR5"
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
        results = self.ddr_node.get_property("dual_freq_en")
        dual_freq = results["dual_freq_en"]
        if self.is_gen5:
            f0_ck_name = "f0_ck_period"
            f1_ck_name = "f1_ck_period"
        else:
            f0_ck_name = "f0_period"
            f1_ck_name = "f1_period"
        results = self.ddr_node.get_property(f0_ck_name)
        period = results[f0_ck_name]
        if (period != "0") and (period != ""):
            freq0 = int(1000000 / float(period) + 0.5)
            freq_zero = str(freq0) + " MHz"
        configs["Memory Frequency 0"] = freq_zero
        if int(dual_freq) > 0:
            results = self.ddr_node.get_property(f1_ck_name)
            period = results[f1_ck_name]
            if (period != "0") and (period != ""):
                freq1 = int(1000000 / float(period) + 0.5)
                freq_one = str(freq1) + " MHz"
            configs["Memory Frequency 1"] = freq_one

        return configs

    def __get_cal_margins(
        self, mode_base: str, left_margs: Dict, right_margs: Dict, centers: Dict, prbs: bool = False
    ):
        group_name = mode_base + "_left"
        results = self.ddr_node.get_property_group([group_name])
        left_margs.clear()
        left_margs.update(results)
        group_name = mode_base + "_right"
        results = self.ddr_node.get_property_group([group_name])
        right_margs.clear()
        right_margs.update(results)
        centers.clear()
        if not prbs:
            group_name = mode_base + "_center"
            results = self.ddr_node.get_property_group([group_name])
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

    def __output_gen5_margins(
        self,
        is_dq: bool,
        bytes: int,
        bits_byte: int,
        left_margs: Dict,
        right_margs: Dict,
        centers: Dict,
    ):
        left_marg_vals = sorted(left_margs.items())
        right_marg_vals = sorted(right_margs.items())
        center_vals = {}
        if not centers:
            for idx in range(len(left_margs)):
                center_vals[idx] = (0, 0)
        else:
            center_vals = sorted(centers.items())

        if is_dq:
            for byte in range(bytes):
                for bit in range(bits_byte):
                    left_marg = left_marg_vals[byte * bits_byte + bit][1]
                    center = center_vals[byte * bits_byte + bit][1]
                    right_marg = right_marg_vals[byte * bits_byte + bit][1]
                    printer(
                        "Byte ",
                        str(byte),
                        " Bit ",
                        str(bit),
                        " - Left Margin: ",
                        str(left_marg[1]),
                        "(",
                        str(left_marg[0]),
                        ") Center Point: ",
                        str(center[1]),
                        "(",
                        str(center[0]),
                        ") Right Margin: ",
                        str(right_marg[1]),
                        "(",
                        str(right_marg[0]),
                        ")",
                    )
        else:
            # DBI for LP5 Read
            # DM for Write
            for byte in range(bytes):
                left_marg = left_marg_vals[byte][1]
                center = center_vals[byte][1]
                right_marg = right_marg_vals[byte][1]
                printer(
                    "Byte ",
                    str(byte),
                    " - Left Margin: ",
                    str(left_marg[1]),
                    "(",
                    str(left_marg[0]),
                    ") Center Point: ",
                    str(center[1]),
                    "(",
                    str(center[0]),
                    ") Right Margin: ",
                    str(right_marg[1]),
                    "(",
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

        # User enabled status check
        if not self.is_enabled:
            printer(self.name, "is not enabled.", "\n")
            if out_file:
                sys.stdout = orig_out
                out_file.close()
            return

        self.refresh_cal_status()
        self.refresh_health_status()
        printer("Calibration Status:  ", self.get_cal_status(), "\n")
        results = self.ddr_node.get_property("health_status")
        printer("Overall Health:  ", results["health_status"], "\n")
        if self.is_gen5:
            printer("Crypto Status:  ", self.crypto_type, "\n")
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
            cal_margin_modes = self.get_cal_margin_mode()
            num_byte = int(configs["Bytes"])
            if not self.is_gen5:
                is_by_8 = True
                num_nibble = int(configs["Nibbles"])
                self.refresh_cal_margin()
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
                            is_by_8,
                            num_byte,
                            num_nibble,
                            left_margins,
                            right_margins,
                            center_points,
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
                            is_by_8,
                            num_byte,
                            num_nibble,
                            left_margins,
                            right_margins,
                            center_points,
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
                            is_by_8,
                            num_byte,
                            num_nibble,
                            left_margins,
                            right_margins,
                            center_points,
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
                            is_by_8,
                            num_byte,
                            num_nibble,
                            left_margins,
                            right_margins,
                            center_points,
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
            # Is Gen5
            else:
                dual_freqs = configs.get("Memory Frequency 1")
                if dual_freqs:
                    num_freqs = 2
                else:
                    num_freqs = 1
                num_ranks = int(configs["Ranks"])
                num_bits_byte = int(configs["Bits per Byte"])
                prbs_ctps_rise = {}
                prbs_ctps_fall = {}
                prbs_ctps = {}

                # Main loop to go through dual frequencies
                for freq in range(num_freqs):
                    base = "Freq " + str(freq) + " Rank "
                    for rank in range(num_ranks):
                        # Read DQ Simp
                        key = "f" + str(freq) + "_rd_dq_simp"
                        if cal_margin_modes[key]:
                            # Rising Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dq_simp_rise"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DQ Margin - Simple Pattern - Rising Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_rise = center_points.copy()

                            # Falling Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dq_simp_fall"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DQ Margin - Simple Pattern - Falling Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_fall = center_points.copy()

                        # Read DQ Comp
                        key = "f" + str(freq) + "_rd_dq_comp"
                        if cal_margin_modes[key]:
                            # Rising Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dq_comp_rise"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DQ Margin - Complex Pattern - Rising Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_rise = center_points.copy()

                            # Falling Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dq_comp_fall"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DQ Margin - Complex Pattern - Falling Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_fall = center_points.copy()

                        # Read DQ PRBS
                        key = "f" + str(freq) + "_rd_dq_prbs"
                        if cal_margin_modes[key]:
                            # Rising Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dq_prbs_rise"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points, True
                            )
                            if prbs_ctps_rise:
                                center_points = prbs_ctps_rise.copy()
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DQ Margin - PRBS Pattern - Rising Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_rise.clear()

                            # Falling Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dq_prbs_fall"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points, True
                            )
                            if prbs_ctps_fall:
                                center_points = prbs_ctps_fall.copy()
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DQ Margin - PRBS Pattern - Falling Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_fall.clear()

                        # Read DBI Simp
                        key = "f" + str(freq) + "_rd_dbi_simp"
                        if cal_margin_modes[key]:
                            # Rising Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dbi_simp_rise"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DBI Margin - Simple Pattern - Rising Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_rise = center_points.copy()

                            # Falling Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dbi_simp_fall"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DBI Margin - Simple Pattern - Falling Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_fall = center_points.copy()

                        # Read DBI Comp
                        key = "f" + str(freq) + "_rd_dbi_comp"
                        if cal_margin_modes[key]:
                            # Rising Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dbi_comp_rise"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DBI Margin - Complex Pattern - Rising Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_rise = center_points.copy()

                            # Falling Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dbi_comp_fall"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DBI Margin - Complex Pattern - Falling Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_fall = center_points.copy()

                        # Read DBI PRBS
                        key = "f" + str(freq) + "_rd_dbi_prbs"
                        if cal_margin_modes[key]:
                            # Rising Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dbi_prbs_rise"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points, True
                            )
                            if prbs_ctps_rise:
                                center_points = prbs_ctps_rise.copy()
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DBI Margin - PRBS Pattern - Rising Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_rise.clear()

                            # Falling Edge
                            group_name_base = (
                                "f" + str(freq) + "_rank" + str(rank) + "_rd_dbi_prbs_fall"
                            )
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points, True
                            )
                            if prbs_ctps_fall:
                                center_points = prbs_ctps_fall.copy()
                            printer(
                                "\n",
                                base + str(rank),
                                " - Read DBI Margin - PRBS Pattern - Falling Edge Clock in pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps_fall.clear()

                        # Write DQ Simp
                        key = "f" + str(freq) + "_wr_dq_simp"
                        if cal_margin_modes[key]:
                            group_name_base = "f" + str(freq) + "_rank" + str(rank) + "_wr_dq_simp"
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Write DQ Margin - Simple Pattern - In pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps = center_points.copy()

                        # Write DQ Comp
                        key = "f" + str(freq) + "_wr_dq_comp"
                        if cal_margin_modes[key]:
                            group_name_base = "f" + str(freq) + "_rank" + str(rank) + "_wr_dq_comp"
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Write DQ Margin - Complex Pattern - In pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps = center_points.copy()

                        # Write DQ PRBS
                        key = "f" + str(freq) + "_wr_dq_prbs"
                        if cal_margin_modes[key]:
                            group_name_base = "f" + str(freq) + "_rank" + str(rank) + "_wr_dq_prbs"
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points, True
                            )
                            if prbs_ctps:
                                center_points = prbs_ctps.copy()
                            printer(
                                "\n",
                                base + str(rank),
                                " - Write DQ Margin - PRBS Pattern - In pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                True,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps.clear()

                        # Write DM Simp
                        key = "f" + str(freq) + "_wr_dm_simp"
                        if cal_margin_modes[key]:
                            group_name_base = "f" + str(freq) + "_rank" + str(rank) + "_wr_dm_simp"
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Write DM Margin - Simple Pattern - In pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps = center_points.copy()

                        # Write DM Comp
                        key = "f" + str(freq) + "_wr_dm_comp"
                        if cal_margin_modes[key]:
                            group_name_base = "f" + str(freq) + "_rank" + str(rank) + "_wr_dm_comp"
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points
                            )
                            printer(
                                "\n",
                                base + str(rank),
                                " - Write DM Margin - Complex Pattern - In pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
                            )
                            prbs_ctps = center_points.copy()

                        # Write DM PRBS
                        key = "f" + str(freq) + "_wr_dm_prbs"
                        if cal_margin_modes[key]:
                            group_name_base = "f" + str(freq) + "_rank" + str(rank) + "_wr_dm_prbs"
                            self.__get_cal_margins(
                                group_name_base, left_margins, right_margins, center_points, True
                            )
                            if prbs_ctps:
                                center_points = prbs_ctps.copy()
                            printer(
                                "\n",
                                base + str(rank),
                                " - Write DM Margin - PRBS Pattern - In pS and (delay taps):\n",
                            )
                            self.__output_gen5_margins(
                                False,
                                num_byte,
                                num_bits_byte,
                                left_margins,
                                right_margins,
                                center_points,
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

    def select_eye_scan_prbs_pattern(self, choice: int):
        """
        Select 2D eye scan traffic pattern to specific PRBS modes.

        Args:

            choice:
                Choice number valid between 0 and 2 only and corrosponding to following pattern:
                    0) PRBS 23
                    1) PRBS 10
                    2) PRBS 7

        Returns:

        """
        if isinstance(choice, str):
            printer("ERROR: Please enter an integer value from 0 to 2 for PRBS pattern selection.")
            return
        elif choice > 2:
            printer("ERROR: Cannot enter a choice number larger than 2.")
            return

        decoded_pattern_choice = choice + 2
        self.ddr_node.set_property({"mgchk_pattern_mode": decoded_pattern_choice})
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

    def get_eye_scan_default_read_vref(self) -> int:
        """
        A helper function for Gen5 DDRMC designs for querying default Read VRef value used
        during Calibration, in encoded format for control registers (not in percentage format).

        Args:

        Returns:

            A calculated value of default Read VRef done during Calibration

        """
        results = self.ddr_node.get_property(
            ["mgchk_def_rd_vref_h1p_lsb", "mgchk_def_rd_vref_h1p_msb"]
        )
        vref_lower = results["mgchk_def_rd_vref_h1p_lsb"]
        vref_upper = results["mgchk_def_rd_vref_h1p_msb"]
        vref_value = vref_lower

        if vref_upper > 0:
            vref_value += 512

        return vref_value

    def get_eye_scan_default_write_vref(self) -> int:
        """
        A helper function for Gen5 DDRMC designs for querying default Write VRef value used
        during Calibration, in encoded format for control registers (not in percentage format).

        Args:

        Returns:

            A calculated value of default Write VRef done during Calibration

        """
        results = self.ddr_node.get_property(["mgchk_def_wr_vref"])
        vref_value = results["mgchk_def_wr_vref"]

        return vref_value

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
        lp5_base = 10.0
        lp5_incr_size = 0.5
        read_incr_size = 0.0976563
        prop_list = []
        # Gen5 Write Vref
        vref_threshold = 128

        prop_list.append("mgchk_rw_mode")
        prop_list.append("mem_type")
        if not self.is_gen5:
            prop_list.append("mgchk_def_wr_vref_range")
            vref_threshold = 50

        results = self.ddr_node.get_property(prop_list)
        rw_mode = results["mgchk_rw_mode"]
        mem_type = results["mem_type"]
        if not self.is_gen5:
            write_vref_range = results["mgchk_def_wr_vref_range"]

        if rw_mode:
            if vref > vref_threshold:
                printer(
                    "ERROR: Cannot enter Vref values larger than ",
                    vref_threshold,
                    " for Write Margin mode",
                )
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
            elif mem_type == 5:
                base_value = lp5_base
                incr_size = lp5_incr_size
            elif mem_type == 4:
                # This needs to be finalized later
                pass
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
        elif rw_mode:
            if not self.is_gen5 and (steps > 51):
                printer("ERROR: Cannot enter Vref step sizes larger than 51 for Write Margin mode")
                return
            elif self.is_gen5 and (steps > 129):
                printer("ERROR: Cannot enter Vref step sizes larger than 129 for Write Margin mode")
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

        if "Read" in scan_mode:
            old_key_base = "rdmargin_"
            new_key_base = "read_"
            for data in engine_data:
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
            for data in engine_data:
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

    def __update_gen5_eye_scan_data(self):
        edges = ["left", "right"]
        clocks = ["nqtr", "pqtr"]
        clock_defs = {
            "nqtr": "fall_",
            "pqtr": "rise_",
        }
        data_list = []

        engine_data = self.ddr_node.get_eye_scan_data()
        data_length = len(engine_data)

        # If initial vref scan went wrong after enabled, needless to process data further
        if not data_length > 1:
            return

        scan_mode = engine_data[0]["config.mode"]
        bit_count = engine_data[0]["config.bits"]
        byte_count = engine_data[0]["config.bytes"]

        if "Read" in scan_mode:
            old_key_base = "rdmargin_"
            new_key_base = "read_"
            for data in engine_data:
                for bit in range(int(bit_count)):
                    for clock in clocks:
                        for edge in edges:
                            old_key = (
                                old_key_base + clock + "_" + edge + "_bit" + "{:02d}".format(bit)
                            )
                            reformat_name = new_key_base + clock_defs[clock] + "{:02d}".format(bit)
                            new_key = reformat_name + "_" + edge
                            tap_value = data[old_key]
                            data[new_key] = tap_value
                            del data[old_key]
                temp_data = {key: val for key, val in data.items() if "wrmargin" not in key}
                new_data = OrderedDict(sorted(temp_data.items()))
                data_list.append(new_data)
        else:
            for data in engine_data:
                temp_data = {key: val for key, val in data.items() if "rdmargin" not in key}
                new_data = OrderedDict(sorted(temp_data.items()))
                data_list.append(new_data)

        self.eye_scan_data = data_list
        self.ddr_node.set_property({"es_data_need_update": 0})

    def __draw_eye_scan_graph(
        self,
        margin_data: List,
        base_name: str,
        margin_title: str,
        def_vref: float,
        cur_max: List,
        unit_string: str = "",
        margin_only: bool = False,
    ):
        vrefs = []
        left_margs = []
        right_margs = []
        total_margs = []
        left_ps = []
        right_ps = []
        def_window_found = False
        min_found = False
        max_found = False
        def_margin = 0
        vref_swing = 0.0
        x_min = 0
        x_max = 0
        y_min = 0.0
        y_max = 0.0

        if not self.is_gen5:
            for data in margin_data:
                cur_vref = float(data["config.vrefp"])
                vrefs.append(cur_vref)
                key_name = base_name + "_left"
                left_marg = int(data[key_name])
                left_margs.append(left_marg)
                key_name += "_ps"
                left_ps.append(int(data[key_name]))
                key_name = base_name + "_right"
                right_marg = int(data[key_name])
                right_margs.append(right_marg)
                key_name += "_ps"
                right_ps.append(int(data[key_name]))
                total_margin = left_marg + right_marg
                total_margs.append(total_margin)
                if not def_window_found:
                    if cur_vref == def_vref:
                        def_margin = total_margin
                        def_window_found = True
                if cur_vref < def_vref:
                    if total_margin == 0:
                        if min_found:
                            min_found = False
                if not min_found:
                    if total_margin > 0:
                        y_min = cur_vref
                        y_max = cur_vref
                        min_found = True
                elif not max_found:
                    if total_margin == 0:
                        max_found = True
                    else:
                        y_max = cur_vref
        else:
            ps_factors = self.ddr_node.get_margin_ps_factors()
            ps_factor = ps_factors[0]

            if "wrmargin" in base_name:
                for data in margin_data:
                    cur_vref = float(data["config.vrefp"])
                    vrefs.append(cur_vref)
                    key_name = base_name + "left_lsb_" + unit_string
                    tap_val = int(data[key_name])
                    key_name = base_name + "left_msb_" + unit_string
                    msb_val = int(data[key_name])
                    left_marg = (msb_val * (2**9)) + tap_val
                    left_margs.append(left_marg)
                    ps_val = int(round(left_marg * ps_factor))
                    left_ps.append(ps_val)
                    key_name = base_name + "right_lsb_" + unit_string
                    tap_val = int(data[key_name])
                    key_name = base_name + "right_msb_" + unit_string
                    msb_val = int(data[key_name])
                    right_marg = (msb_val * (2**9)) + tap_val
                    right_margs.append(right_marg)
                    ps_val = int(round(right_marg * ps_factor))
                    right_ps.append(ps_val)
                    total_margin = left_marg + right_marg
                    total_margs.append(total_margin)
                    if not def_window_found:
                        if cur_vref == def_vref:
                            def_margin = total_margin
                            def_window_found = True
                    if cur_vref < def_vref:
                        if total_margin == 0:
                            if min_found:
                                min_found = False
                    if not min_found:
                        if total_margin > 0:
                            y_min = cur_vref
                            y_max = cur_vref
                            min_found = True
                    elif not max_found:
                        if total_margin == 0:
                            max_found = True
                        else:
                            y_max = cur_vref
            else:
                for data in margin_data:
                    cur_vref = float(data["config.vrefp"])
                    vrefs.append(cur_vref)
                    key_name = base_name + "_left"
                    left_marg = int(data[key_name])
                    left_margs.append(left_marg)
                    ps_val = int(round(left_marg * ps_factor))
                    left_ps.append(ps_val)
                    key_name = base_name + "_right"
                    right_marg = int(data[key_name])
                    right_margs.append(right_marg)
                    ps_val = int(round(right_marg * ps_factor))
                    right_ps.append(ps_val)
                    total_margin = left_marg + right_marg
                    total_margs.append(total_margin)
                    if not def_window_found:
                        if cur_vref == def_vref:
                            def_margin = total_margin
                            def_window_found = True
                    if cur_vref < def_vref:
                        if total_margin == 0:
                            if min_found:
                                min_found = False
                    if not min_found:
                        if total_margin > 0:
                            y_min = cur_vref
                            y_max = cur_vref
                            min_found = True
                    elif not max_found:
                        if total_margin == 0:
                            max_found = True
                        else:
                            y_max = cur_vref

        x_min = max(left_ps)
        x_max = max(right_ps)
        max_marg = max(total_margs)
        max_marg_idx = total_margs.index(max_marg)
        max_marg_vref = vrefs[max_marg_idx]
        if not def_window_found:
            def_window = []
            init_list = []
            scan_data = self.eye_scan_data
            init_list.append(scan_data[0])
            self.__draw_eye_scan_graph(
                init_list, base_name, "", def_vref, def_window, unit_string, margin_only=True
            )
            def_margin = def_window[0][0]
        vref_swing = round((y_max - y_min), 3)
        cur_max.append((max_marg, max_marg_vref, def_margin, def_vref, vref_swing, y_min, y_max))

        if margin_only:
            return

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
        if self.is_gen5:
            self.__update_gen5_eye_scan_data()
        else:
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
            check_eye_scan_window()
            check_eye_scan_height()

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
            if self.is_gen5:
                vref_threshold = 128
            else:
                vref_threshold = 50

            if (vref_min > vref_threshold) or (vref_max > vref_threshold):
                printer(
                    "ERROR: Cannot set Vref values larger than ",
                    vref_threshold,
                    " under Write margin mode.",
                )
                return False
            if vref_steps > vref_threshold + 1:
                printer(
                    "ERROR: Cannot set Vref step sizes larger than ",
                    vref_threshold + 1,
                    " for Write Margin mode",
                )
                return False

        if vref_min > vref_max:
            printer("ERROR: Cannot set minimum Vref value larger than maximum Vref value.")
            return False

        percent_min = self.get_eye_scan_vref_percentage(vref_min)
        percent_max = self.get_eye_scan_vref_percentage(vref_max)
        printer("Min VRef is set at:", percent_min, "%, encoded value", vref_min)
        printer("Max VRef is set at:", percent_max, "%, encoded value", vref_max)
        printer("Number of VRef steps is set at:", vref_steps)

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
        self,
        unit_index: int = 0,
        return_as_list: bool = False,
        display_type: str = "dynamic",
        get_margin_only: bool = False,
    ):
        """
        Assemble and display 2D eye scan drawing in chart format. By default, it tries to process and
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

            get_margin_only: Optional argument, default to False. If set to True, this API call
                will process scan data only, per the specified unit_index, find its widest margin
                windows and return the values and along with their VRef points as a list of tuples.
                No graphing results will be given.

        Returns:
            A list of Figure objects from Plotly, if return_as_list is specified as True,
            None is return otherwise by default, but graphs will be displayed in a browser.

            If optional argument get_margin_only is set to True. A list, which contains tuples as
            (int, float) representing the widest window margin found and along with their VRef points
            after a scan is returned.

            For Read Margin, two data results are displayed or returned. (First data for Rising
            Clock edge, and the second for Falling Clock edge) For Write Margin, only one data
            result will be displayed or returned.

        """
        if (not get_margin_only) and (not _plotting_pkgs_available):
            raise ImportError(
                f"Plotting packages not installed! Please run ",
                "'pip install chipscopy[plotly,pandas]'",
            )

        result = self.ddr_node.get_property(["es_data_need_update"])
        data_need_update = result["es_data_need_update"]

        if data_need_update:
            self.eye_scan_data.clear()
            if self.is_gen5:
                self.__update_gen5_eye_scan_data()
            else:
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
        mc_id = data_list[0]["config.mc_id"]
        scan_mode = data_list[0]["config.mode"]
        unit_mode = data_list[0]["config.unit"]
        rank_num = data_list[0]["config.rank"]
        mem_type = data_list[0]["config.mem_type"]
        df_vref = data_list[0]["config.df_vrefp"]
        df_vref = float(df_vref)
        if not self.is_gen5:
            nibble_count = data_list[0]["config.nibbles"]
        else:
            bit_count = data_list[0]["config.bits"]
        byte_count = data_list[0]["config.bytes"]
        unit_val = "{:02d}".format(unit_index)
        data_list = data_list[1:]
        unit_str = ""
        max_window = []  # list of tuple (int, float)
        window_results = []  # list of tuple (int, float)

        # Some logical data check first on user inputs
        if unit_mode == "bit":
            if (unit_index < 0) or (unit_index >= int(bit_count)):
                max_unit = int(bit_count) - 1
                err_msg = (
                    "ERROR: unit_index given for "
                    + unit_mode
                    + " mode needs to be between 0 and "
                    + str(max_unit)
                )
                err_msg += ", based on current memory configuration."
                printer(err_msg)
                return
            unit_str = unit_mode + unit_val
        elif unit_mode == "nibble":
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
            unit_str = unit_mode + str(unit_index)

        mc_name = mc_id

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
                margin_mode += mc_name + " - "
                margin_mode += mem_type + " - Rank" + str(rank_num)
                if not get_margin_only:
                    fig = self.__draw_eye_scan_graph(
                        data_list, name_base, margin_mode, df_vref, max_window
                    )
                    figure_list.append(fig)
                    printer(
                        "Margin window found:",
                        clock_defs[clock],
                        max_window[0][0],
                        "fine taps at VRef %:",
                        max_window[0][1],
                    )
                else:
                    self.__draw_eye_scan_graph(
                        data_list, name_base, margin_mode, df_vref, max_window, margin_only=True
                    )
                    window_results.append(max_window[0])
                max_window.clear()

        else:
            margin_mode = scan_mode + " - " + unit_mode.capitalize() + str(unit_index) + "<br>"
            margin_mode += mc_name + " - "
            margin_mode += mem_type + " - Rank" + str(rank_num)
            if not self.is_gen5:
                name_base = "write_" + unit_val
                if not get_margin_only:
                    fig = self.__draw_eye_scan_graph(
                        data_list, name_base, margin_mode, df_vref, max_window
                    )
                    printer(
                        "Margin window found:",
                        max_window[0][0],
                        "fine taps at VRef %:",
                        max_window[0][1],
                    )
                    figure_list.append(fig)
                else:
                    self.__draw_eye_scan_graph(
                        data_list, name_base, margin_mode, df_vref, max_window, margin_only=True
                    )
                    window_results.append(max_window[0])
            else:
                name_base = "wrmargin_"
                if not get_margin_only:
                    fig = self.__draw_eye_scan_graph(
                        data_list, name_base, margin_mode, df_vref, max_window, unit_str
                    )
                    printer(
                        "Margin window found:",
                        max_window[0][0],
                        "fine taps at VRef %:",
                        max_window[0][1],
                    )
                    figure_list.append(fig)
                else:
                    self.__draw_eye_scan_graph(
                        data_list,
                        name_base,
                        margin_mode,
                        df_vref,
                        max_window,
                        unit_str,
                        margin_only=True,
                    )
                    window_results.append(max_window[0])

        if get_margin_only:
            return window_results

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

    def check_eye_scan_height(self, unit_index: int = 0):
        """
        Calculate and obtain the VRef swing/height found from a margin scan by a specified unit index.
        The height is defined by having the lowest point of VRef that a non-zero margin window starts, and ends
        with the highest VRef point found in the same fashion. By default, it tries to process from the scan
        data found in the most recent 2D eye scan run. Users have the option to load scan data first prior to
        using this function, in order to process specific set of scan data, see load_eye_scan_data().

        Args:
            unit_index: Specify the index from a set of scan data users intend to display, based on
                unit mode found in the scan settings (bit, nibble, byte)

        Returns:
            A list, which contains lists of floating point values representing the VRef percentage values
            in the following item order: [VRef swing, minimum VRef, maximum VRef]
            For Read Margin, two sets of data list are being returned. (First item from the list is for Rising
            Clock edge, and the second is for Falling Clock edge) For Write Margin, only one set of data list
            will be returned.
        """
        vref_results = []  # List of list [float, float, float]

        window_results = self.display_eye_scan(unit_index, get_margin_only=True)

        for window in window_results:
            vref_results.append([window[4], window[5], window[6]])

        return vref_results

    def check_eye_scan_window(self, unit_index: int = 0, default_vref: bool = False):
        """
        Calculate and obtain the widest 2D eye scan margin window by a specified unit index. This function
        also checks the margin window found at default VRef setting determined by the memory controller.
        By default, it tries to process from the scan data found in the most recent 2D eye scan run. Users
        have the option to load scan data first prior to using this function, in order to process specific
        set of scan data, see load_eye_scan_data().

        Args:
            unit_index: Specify the index from a set of scan data users intend to display, based on
                unit mode found in the scan settings (bit, nibble, byte)

            default_vref: Optional argument, default to False, which means the function will check and report
                the widest margin window found and along with its corrosponding vref value at the earliest point.
                If set to True, the function will report margin window found at its default VRef point instead.

        Returns:
            A list, which contains tuples of (int, float) will be returned. The first integer item from the
            tuples represents the window margin found after a scan, and the second item indicates the VRef
            setting value in floating point.

            For Read Margin, two data results are being returned. (First tuple of data is for Rising
            Clock edge, and the second is for Falling Clock edge) For Write Margin, only one tuple
            result will be returned.

        """
        checked_results = []  # List of tuples (int, float)
        return_idx0 = 0
        return_idx1 = 1

        window_results = self.display_eye_scan(unit_index, get_margin_only=True)

        if default_vref:
            return_idx0 += 2
            return_idx1 += 2

        # Read Modes
        if len(window_results) > 1:
            for window in window_results:
                checked_results.append((window[return_idx0], window[return_idx1]))
        else:
            # Write Modes
            window = window_results[0]
            checked_results.append((window[return_idx0], window[return_idx1]))

        return checked_results

    def __str__(self):
        return self.name
