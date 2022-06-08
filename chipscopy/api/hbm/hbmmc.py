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
from typing import Dict, List, TYPE_CHECKING
from dataclasses import dataclass
from collections import OrderedDict

from chipscopy.dm import request
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore

if TYPE_CHECKING:
    from chipscopy.client.hbm_mc_client import HBMMCClient


@dataclass
class HBMMC(DebugCore["HBMMCClient"]):
    """
    This class contains the top level API functions to interact with the
    integrated HBMMC debug core(s) under a HBM Stack on Versal devices.

    """

    def __init__(self, hbm_parent_stack, hbmmc_node):
        from chipscopy.api.hbm.hbm import HBM

        super(HBMMC, self).__init__("HBMMC", hbmmc_node)
        self.node_name = hbmmc_node.props["Name"]
        self.mc_index = hbmmc_node.props.get("mc_index")
        self.mc_location = hbmmc_node.props.get("mc_loc")
        self.name = "hbm_mc" + str(self.mc_index)
        self.mc_node = self.core_tcf_node
        self.is_enabled = self.is_user_enabled()
        self.cal_status = self.get_cal_status()
        self.hbm_stack: HBM = hbm_parent_stack

    def get_cal_status(self):
        """
        Get the overall calibration status of HBMMC under a Stack

        Args:

        Returns:
            status in string

        """

        key = "cal_status"
        result = self.mc_node.get_property(key)
        cal_status = result[key]

        return cal_status

    def is_user_enabled(self):
        """
        Find out whether the HBMMC core under a HBM Stack is user enabled or not
        after Versal device configuration

        Args:

        Returns:
            Status value in Bool

        """

        key = "mc_enabled"
        result = self.mc_node.get_property(key)

        if (key in result) and result[key]:
            return True
        else:
            return False

    def get_power_mode(self):
        """
        Get the current power mode status of HBMMC under a Stack

        Args:

        Returns:
            mode status in string

        """

        key = "mc.mc_stat"
        power_mode = None

        if self.is_enabled:
            results = self.mc_node.refresh_property_group(key)
            self_refresh = results["hbmmc_mc_stat.self_refresh"]
            pow_down = results["hbmmc_mc_stat.power_down"]
            active = results["hbmmc_mc_stat.active"]

            if self_refresh:
                power_mode = "Self Refresh"
            elif pow_down:
                power_mode = "Powered Down"
            elif active:
                power_mode = "Active"
            else:
                power_mode = "ERROR"

        return power_mode

    def get_property(self, property_names=None, done: DoneHWCommand = None):
        """
        Get the property value mapped to HBMMC core

        Args:
            property_names: single string or list of string of property names
                (if None specified, all properties available will be queried and returned)

            done: Optional command callback that will be invoked when the response is received

        Returns:
            A dictionary, where
                Key = property name
                Val = property value

        """

        results = self.mc_node.get_property(property_names, done)

        return results

    def __str__(self):
        return self.name
