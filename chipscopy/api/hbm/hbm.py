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
from typing import Dict, List, TYPE_CHECKING
from dataclasses import dataclass
from collections import OrderedDict
from rich.tree import Tree

from chipscopy.dm import request
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy.api.report import report_hierarchy
from chipscopy.api.hbm.hbmmc import HBMMC
from chipscopy.client.hbm_mc_client import HBMMCClient

if TYPE_CHECKING:
    from chipscopy.client.hbm_client import HBMClient


def listify(item):
    return item if isinstance(item, list) or isinstance(item, tuple) else [item]


@dataclass
class HBM(DebugCore["HBMClient"]):
    """
    This class contains the top level API functions to interact with the
    integrated HBM Stack level debug core(s) on Versal devices.

    """

    def __init__(self, hbm_node):
        super(HBM, self).__init__(CoreType.HBM, hbm_node)
        self.node_name = hbm_node.props["Name"]
        self.stack_index = self.node_name[-1]
        self.name = "hbm_stack" + self.stack_index
        self.hbm_node = self.core_tcf_node
        self.is_enabled = self.is_user_enabled()
        self.init_status = self.get_init_status()
        self.hbm_mcs: List[HBMMC] = []
        self._populate_mcs()

    def get_init_status(self):
        """
        Get the overall Middle Stack init status of HBM Stack

        Args:

        Returns:
            status in string

        """

        status = self.hbm_node.get_init_status()

        return status

    def get_overtemp_status(self):
        """
        Get the Over Temperature detection status of HBM Stack

        Args:

        Returns:
            status in string

        """
        key = "ms.reg_isr.cattrip"
        ot_status = None

        if self.is_enabled:
            results = self.hbm_node.refresh_property(key)
            status = results[key]

            if status:
                ot_status = "ERROR"
            else:
                ot_status = "OK"

        return ot_status

    def refresh_temperature(self, done: DoneHWCommand = None):
        """
        Refresh the temperature status of HBM Stack

        Args:
            done: Optional command callback that will be invoked when the response is received

        Returns:

        """

        # self.hbm_node.refresh_cal_status(done)

    def get_enabled_mcs_list(self):
        """
        Get a list of integers representing the enabled MC index under the HBM Stack

        Args:

        Returns:
            A list of integers representing the enabled MC index under the HBM Stack

        """
        en_list = []

        en_mask_tup = self.hbm_node.get_enabled_mcs_mask()
        en_mask = en_mask_tup[0]

        for mc_index in range(0, len(self.hbm_mcs)):
            if en_mask & 1:
                en_list.append(mc_index)
            en_mask = en_mask >> 1

        return en_list

    def display_status_tree(self):
        """
        Display the current status of HBM stack and the enabled HBMMCs under it

        Args:

        Returns:
            Printer outputs in the format of tree hierarchy

        """

        report_hierarchy(self)

    def get_temperature(self):
        """
        Refresh and get the current temperature of the HBM Stack

        Args:

        Returns:
            Current temperature value in integer of HBM Stack in Celcius

        """
        self.hbm_node.refresh_temp_status()

        key = "temp_value"
        result = self.hbm_node.get_property(key)

        return result[key]

    def get_mc(self, mc_index: int):
        """
        Get an HBM_MC object with a given MC index under the HBM Stack

        Args:

        Returns:
            HBM_MC object with a given MC index under the HBM Stack

        """
        mc_count = len(self.hbm_mcs)

        if (mc_index < 0) or (mc_index + 1 > mc_count):
            raise Exception("Invalid HBM MC index given.")

        return self.hbm_mcs[mc_index]

    def is_user_enabled(self):
        """
        Find out whether the HBM Stack core is user enabled or not after
        Versal device configuration

        Args:

        Returns:
            Status value in Bool

        """

        key = "en_status"
        result = self.hbm_node.get_property(key)

        if not result[key]:
            return False
        else:
            return True

    def _populate_mcs(self):
        if self.is_enabled:
            for node in self.hbm_node.manager.get_children(self.hbm_node):
                if HBMMCClient.is_compatible(node):
                    upgraded_node = self.hbm_node.manager.get_node(node.ctx, HBMMCClient)
                    HBM_MC = HBMMC(self, upgraded_node)
                    upgraded_node.api_client_wrapper = HBM_MC
                    self.hbm_mcs.append(HBM_MC)

    def save_properties(self, file_name=None, mc_index=-1, group: [str] = None):
        """
        Refresh, get, and save registers and properties data from the intended Stack or
        HBMMC to a file in CSV format

        Args:

            file_name: the file name or full path for the data file to be saved.
                       A default file name will be given if none is supplied.

            mc_index:  the target HBMMC index under the HBM Stack to point to
                       When this argument is not supplied, it defaults to just data in the Stack

            group:  Specific group names(s) that the users want to see within a block, can be a
                         single or a list of string values.
                         When this argument is not supplied, ALL groups within the block will be processed.

        Returns:

        """
        out_file = None

        if not file_name:
            # Provide a default for file
            file_name = "hbm2e_property_stack"
            file_name += self.stack_index

        headers = []
        headers.append("Name")
        headers.append("Value")
        data = {}
        groups = []
        if group:
            group = listify(group)
            groups.extend(group)

        if mc_index >= 0:
            # Users intend to fetch properties from HBMMC
            mc = self.get_mc(mc_index)
            data = mc.mc_node.refresh_property_group(groups)
            file_name += "_mc" + str(mc_index)
        else:
            # Intend for HBM Stack and MS
            self.hbm_node.refresh_temp_status()
            data = self.hbm_node.refresh_property_group(groups)

        file_name = os.path.splitext(file_name)[0] + ".csv"

        with open(file_name, "w", newline="") as out_file:
            data_writer = csv.DictWriter(out_file, headers)
            data_writer.writeheader()
            writer = csv.writer(out_file)
            for key, val in sorted(data.items()):
                if isinstance(val, int):
                    value = hex(val)
                    writer.writerow([key, value])
            print("\nInfo: Properties data are being formatted and saved to:", out_file.name)

    def get_property(self, property_names=None, done: DoneHWCommand = None):
        """
        Get the property value mapped to HBM Stack core

        Args:
            property_names: single string or list of string of property names
                (if None specified, all properties available will be queried and returned)

            done: Optional command callback that will be invoked when the response is received

        Returns:
            A dictionary, where
                Key = property name
                Val = property value

        """

        results = self.hbm_node.get_property(property_names, done)

        return results

    def __rich_tree__(self):
        root_display = self.name + " -- Status: "
        root_display += self.init_status
        root = Tree(root_display)

        for mc in self.hbm_mcs:
            if mc.is_enabled:
                display_name = mc.name + "("
                display_name += mc.mc_location + ") -- Status: "
                display_name += mc.cal_status
                root.add(display_name)

        return root

    def __str__(self):
        return self.name
