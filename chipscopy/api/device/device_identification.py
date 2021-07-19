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

import json
import re
from collections import namedtuple, defaultdict, deque
from typing import List

from chipscopy.api.memory import Memory
from chipscopy.client.core import CoreParent
from chipscopy.client.debug_core_client import DebugCoreClientNode
from chipscopy.client.jtagdevice import JtagDevice
from chipscopy.client.mem import MemoryNode
from chipscopy.client.view_info import ViewInfo

# Tuple with the raw data for tracking scanned device information for a device
# Used during DeviceScanner scan
# TODO: Add an incrementing device number for easy path reporting (not jtag_index)
# Tuple with the raw data for tracking scanned device information for nodes associated with the device
# Used during DeviceScanner scan

_DeviceIdentificationTuple = namedtuple(
    "DeviceTracker",
    ["family", "node_identification", "dna", "cable_context", "cable_name", "jtag_index"],
)
_DeviceNodeIdentificationTuple = namedtuple(
    "NodeTracker", ["server_type", "view_name", "name", "context", "hier_name"]
)


class DeviceIdentification:
    """DeviceIdentification is a wrapper around the _DeviceIdentificationTuple object providing some additional
    services given the raw device identification data.

    All devices are expected to carry some form of identification. DNA is the most reliable, but we take what we can
    get for a likely match. Jtag cable and jtag position will work if DNA is unavailable for non-Versal devices.
    This identification helps us match up nodes targets across different views, especially ones that don't make
    hierarchical sense like DPC and Versal top level targets on the same device.

    TODO: Get rid of the _DeviceIdentificationTuple - just use this class for everything. That should be simpler.
    """

    def __init__(self, device_tracker: _DeviceIdentificationTuple):
        self.device_tracker = device_tracker

    def __getitem__(self, key):
        return getattr(self.device_tracker, key)

    def __repr__(self):
        # Make a nice nested dictionary representation of the nested named tuples.
        # This necessary because namedtuple._asdict() doesn't work well with nesting tuples.
        # I want the inner node_identification to be a list of dicts, not a list of tuples
        outer_dict = defaultdict(list)
        for field, value in zip(self.device_tracker._fields, self.device_tracker):
            if isinstance(value, list):
                for device_node_id_tuple in value:
                    # Nested list of tuples
                    inner_dict = {}
                    for field2, value2 in zip(device_node_id_tuple._fields, device_node_id_tuple):
                        inner_dict[field2] = value2
                    outer_dict[field].append(inner_dict)
            else:
                outer_dict[field] = value
        raw_json = json.dumps(outer_dict, indent=4)
        return raw_json

    def __str__(self):
        json_obj = self.__repr__()
        d = json.loads(json_obj)
        family = d.get("family", "unknown_family")
        dna = hex(d.get("dna", "0x0"))
        return f"{family}:{dna}"

    def find_top_level_device_node(self, hw_server):
        """
        Returns the device node we will use as a top level to identify
        this device. This node is where we also hang additional device services
        (wrappers). This forces the additional device services lifecycle
        to match the device node. Helps keep everything in sync.
        It really doesn't matter which device node is picked, as long as it
        is consistent everytime we call.
        """
        try:
            node = self.find_jtag_node(hw_server)
        except ValueError:
            # Jtag node finder didn't work - happens in case like XVC with
            # no jtag. Fall back to debugcore instead in that case.
            node = None

        if node is None:
            try:
                node = self.find_debugcore_node(hw_server)
            except ValueError:
                # Could not find the node - this is not good.
                node = None

        if node is None:
            raise ValueError("Failed to lookup top level device node")
        return node

    def get_target_tuples(self) -> List[_DeviceNodeIdentificationTuple]:
        """
        Returns: Tuple with all the accessible targets for this device including a hierarchical style path.
        """
        return self.device_tracker.node_identification

    def _find_node(self, view_name, server, node_class_type):
        """Finds the top level node for a view given the name and server.
        device_node_ctx_finder() return defaults to DPC. This is only
        for the chipscope and debugcore views. Use the find_jtag_node
        for jtag because the required process is slightly different.
        """
        assert view_name == "chipscope" or view_name == "debugcore"
        view = server.get_view(view_name)
        discovery_node_ctx = self.device_node_ctx_finder(view_name)
        discovery_node = view.get_node(discovery_node_ctx, node_class_type)
        return discovery_node

    def find_debugcore_node(self, server) -> DebugCoreClientNode:
        return self._find_node("debugcore", server, DebugCoreClientNode)

    def find_chipscope_node(self, server) -> CoreParent:
        return self._find_node("chipscope", server, CoreParent)

    def find_jtag_node(self, hw_server) -> JtagDevice:
        """Finds the node we use for programming the device.
        Returns: jtag programming node for the device
        """
        # Go through list of possible jtag configurable devices - when we find our matching context,
        # program it. This is versal specific. It will need work when we add ultrascale.
        # One problem at a time...
        jtag_view = hw_server.get_view("jtag")
        jtag_node = None
        # Grab the jtag node context stored for this device jtag view.
        discovery_node_ctx = self.device_node_ctx_finder("jtag", ".*")
        for node in jtag_view.get_all():
            if JtagDevice.is_compatible(node):
                jtag_node = jtag_view.get_node(node.ctx, JtagDevice)
                if jtag_node.ctx == discovery_node_ctx:
                    break
        return jtag_node

    def find_dpc_memory_node(self, hw_server):
        memory_view: ViewInfo = hw_server.get_view("memory")
        top_memory_node_ctx = self.device_node_ctx_finder("memory", "^DPC")
        node = memory_view.get_node(top_memory_node_ctx, MemoryNode)
        upgraded_node = Memory.check_and_upgrade(memory_view, node)
        return upgraded_node

    def find_versal_node(self, hw_server):
        memory_view: ViewInfo = hw_server.get_view("memory")
        top_memory_node_ctx = self.device_node_ctx_finder("memory", "^Versal")
        node = memory_view.get_node(top_memory_node_ctx, MemoryNode)
        return node

    def get_memory_target_nodes(self, hw_server):
        # Return the memory target nodes for this device
        view_name = "memory"
        node_ctx_list = list()
        access_priority_list = [r"^DPC", r"^Versal", r"^XVC"]
        for access_type in access_priority_list:
            for node_tracker in self.device_tracker.node_identification:
                if (
                    re.search(access_type, node_tracker.name)
                    and node_tracker.view_name == view_name
                ):
                    # The top level debug core discovery node
                    node_ctx_list.append(node_tracker.context)

        memory_view: ViewInfo = hw_server.get_view(view_name)
        memory_node_list = list()
        for node_ctx in node_ctx_list:
            node = memory_view.get_node(node_ctx)
            if MemoryNode.is_compatible(node):
                memory_node = memory_view.get_node(node.ctx, MemoryNode)
                if memory_node and len(memory_node.props.get("Name")) > 0:
                    memory_node_list.append(memory_node)

        # Add child nodes
        nodes_to_travel = deque(memory_node_list)
        memory_node_list = list()
        while nodes_to_travel:
            node = nodes_to_travel.popleft()
            if MemoryNode.is_compatible(node):
                memory_node = memory_view.get_node(node.ctx, MemoryNode)
                memory_node_list.append(memory_node)
                nodes_to_travel.extendleft(memory_view.get_children(memory_node))
        # Upgrade all
        upgraded_memory_node_list = [
            Memory.check_and_upgrade(memory_view, node) for node in memory_node_list
        ]
        return upgraded_memory_node_list

    def find_memory_target(self, hw_server, target: str):
        if target is None:
            dpc_or_versal_target = None
            target = "DPC"
        elif target == "DPC":
            # Use the DPC (Default if None is specified)
            dpc_or_versal_target = "^DPC"
        else:
            # Use the DAP
            dpc_or_versal_target = "^Versal"

        memory_view: ViewInfo = hw_server.get_view("memory")
        top_memory_node_ctx = self.device_node_ctx_finder("memory", dpc_or_versal_target)
        top_memory_node = memory_view.get_node(top_memory_node_ctx, MemoryNode)
        assert top_memory_node is not None

        # Now we have a top memory node for this device - either Versal or DPC. Do a search through all children
        # and stop when we find a matching target.
        target_node = None
        nodes_to_travel = deque([top_memory_node])
        while nodes_to_travel:
            node = nodes_to_travel.popleft()
            if MemoryNode.is_compatible(node):
                memory_node = memory_view.get_node(node.ctx, MemoryNode)
                if memory_node:
                    name = memory_node.props.get("Name")
                    if name and re.search(target, name):
                        target_node = memory_node
                        break
                    nodes_to_travel.extendleft(memory_view.get_children(memory_node))
        if not target_node:
            raise KeyError(f"Could not find target key {target} in memory targets")
        target_node = Memory.check_and_upgrade(memory_view, target_node)
        return target_node

    def device_node_ctx_finder(self, view_name: str, target_name_regex: str = None):
        """This is a function that returns the correct top level CoreParent context used for debug core scanning.
        It should return the correct context for a device given the view and target name.
        The returned node will be used when calling setup_debug_cores and device programming.

        Args:
            view_name: view to search (jtag, memory, debugcore, chipscope)
            target_name_regex: regex to override default target prioritized search

        Returns: top level node for this device (or ValueError exception if none found)
        """
        if target_name_regex:
            access_priority_list = [target_name_regex]
        else:
            access_priority_list = [r"^DPC", r"^Versal", r"^XVC", r"^Ultra"]
        for access_type in access_priority_list:
            for node_tracker in self.device_tracker.node_identification:
                if (
                    re.search(access_type, node_tracker.name)
                    and node_tracker.view_name == view_name
                ):
                    # The top level debug core discovery node
                    return node_tracker.context
        # Should not happen.
        raise (
            ValueError(
                f"Could not find matching node - view:{view_name}, target:{target_name_regex}"
            )
        )
