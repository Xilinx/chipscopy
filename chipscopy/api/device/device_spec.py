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
#
import dataclasses
import json
from collections import deque
from typing import Optional, Literal, List

from chipscopy.api.device.device_scanner import (
    ViewRecordType,
    JtagRecord,
    MemoryRecord,
    DebugcoreRecord,
    ChipscopeRecord,
)
from chipscopy.api.device.device_util import get_node_dna
from chipscopy.api.memory import Memory
from chipscopy.client import ServerInfo
from chipscopy.client.core import CoreParent
from chipscopy.client.debug_core_client import DebugCoreClientNode
from chipscopy.client.jtagdevice import JtagDevice, JtagCable
from chipscopy.client.mem import MemoryNode
from chipscopy.client.view_info import ViewInfo
from chipscopy.dm import Node


@dataclasses.dataclass
class DeviceSpec:
    """
    This support class keeps track of the low level TCF nodes for a device.
    Nodes can change - this class also tracks node events and marks invalid
    nodes as they change (ex: power cycle or program).

    What are we keeping track of? See below.

    ::

        jtag (ViewInfo)
        └── whole scan chain (JtagCable)          -> jtag_cable
            ├── arm_dap (JtagDevice)              -> jtag_dap
            └── xcvc1902 (JtagDevice)             -> jtag_device **

        memory (ViewInfo)
        ├── Versal xcvc1902 (MemoryNode)          -> memory_dap
               ...
        └── DPC (MemoryNode)                      -> memory_dpc

        debugcore (ViewInfo)
        ├── Versal xcvc1902 (Node)                -> debugcore_dap
        └── DPC xcvc1902 (DebugCoreClientNode)    -> debugcore_dpc

        chipscope (ViewInfo)
        ├── Versal xcvc1902 (Node)                -> chipscope_dap
        └── DPC xcvc1902 (CoreParent)             -> chipscope_dpc

    ** jtag_device is the default ctx that identifies the device when available
           (see get_device_ctx)
    """

    TargetType = Optional[Literal["DPC", "DAP"]]

    hw_server: ServerInfo
    cs_server: Optional[ServerInfo]
    jtag_cable_ctx: str = ""
    jtag_dap_ctx: str = ""
    jtag_device_ctx: str = ""
    jtag_index: Optional[int] = None
    memory_dap_ctx: str = ""
    memory_dpc_ctx: str = ""
    debugcore_dap_ctx: str = ""
    debugcore_dpc_ctx: str = ""
    chipscope_dpc_ctx: str = ""
    chipscope_dap_ctx: str = ""
    is_valid: bool = False
    device_ctx: str = ""
    device_view: str = ""

    @staticmethod
    def create_from_device_records(
        hw_server, cs_server, device_record_list: List[ViewRecordType]
    ) -> "DeviceSpec":
        """
        Factory to create a _DeviceNodes object correctly given the records list.
        """
        d = DeviceSpec(hw_server, cs_server)
        for rec in device_record_list:
            if type(rec) is JtagRecord:
                d.jtag_device_ctx = rec.ctx
                d.jtag_dap_ctx = rec.dap_ctx
                d.jtag_cable_ctx = rec.jtag_cable_ctx
                d.jtag_index = rec.jtag_index
            elif type(rec) is MemoryRecord:
                if rec.is_dap:
                    d.memory_dap_ctx = rec.ctx
                elif rec.is_dpc:
                    d.memory_dpc_ctx = rec.ctx
            elif type(rec) is DebugcoreRecord:
                if rec.is_dap:
                    d.debugcore_dap_ctx = rec.ctx
                elif rec.is_dpc:
                    d.debugcore_dpc_ctx = rec.ctx
            elif type(rec) is ChipscopeRecord:
                if rec.is_dap:
                    d.chipscope_dap_ctx = rec.ctx
                elif rec.is_dpc:
                    d.chipscope_dpc_ctx = rec.ctx

        d._pick_best_device_ctx()
        if d.device_ctx:
            d.is_valid = True
        return d

    def to_dict(self):
        fields = [field.name for field in dataclasses.fields(self)]
        retval = {}
        for f in fields:
            if f == "hw_server" or f == "cs_server":
                server = getattr(self, f)
                retval[f] = server.props.get("url", "")
            else:
                retval[f] = getattr(self, f)
        return retval

    def get_dna(self) -> Optional[int]:
        node = self.get_jtag_node()
        if node:
            return get_node_dna(node)
        else:
            node = self.get_debugcore_node(target=None, default_target="DAP")
            if node:
                return get_node_dna(node)

    def get_arch_name(self) -> str:
        node = self.get_jtag_node()
        arch_name = ""
        if node:
            arch_name = node.props.get("arch_name", "")
        else:
            node = self.get_debugcore_node(target=None, default_target="DAP")
            if node:
                try:
                    # In case of XVC cable, the jtag node does not exist. The
                    # dpc_driver_name is something we can use to identify xvc
                    dpc_driver_name = node.props.get("DpcDriverName", "")
                    if dpc_driver_name:
                        arch_name = "xvc"
                    else:
                        arch_name, _ = node.props.get("Name", "").split()
                except ValueError:
                    if node.props.get("Name", "").startswith("XVC"):
                        arch_name = "xvc"
                arch_name = arch_name.lower()
                if arch_name == "ultrascale":
                    arch_name = "uplus"
        return arch_name

    def get_part_name(self) -> str:
        node = self.get_jtag_node()
        part_name = ""
        if node:
            part_name = node.props.get("Name", "")
        else:
            node = self.get_debugcore_node(target=None, default_target="DAP")
            if node:
                try:
                    _, part_name = node.props.get("Name", "").split()
                except ValueError:
                    part_name = ""
        return part_name

    def to_json(self) -> str:
        raw_json = json.dumps(self.to_dict(), indent=4, default=lambda o: str(o))
        return raw_json

    def handle_node_update(self):
        # Check if device context changed - if so, mark the device invalid
        ...

    def get_device_node(self) -> Optional[Node]:
        if self.device_ctx:
            return self.get_node(self.device_view, self.device_ctx)
        else:
            return None

    def get_jtag_ctx(self) -> Optional[str]:
        return self.jtag_device_ctx

    def get_jtag_node(self) -> Optional[Node]:
        return self.get_node("jtag", self.jtag_device_ctx, JtagDevice)

    def get_jtag_cable_node(self) -> Optional[Node]:
        return self.get_node("jtag", self.jtag_cable_ctx, JtagCable)

    def get_jtag_cable_name(self) -> Optional[str]:
        node = self.get_jtag_cable_node()
        name = ""
        if node:
            name = node.props.get("Name", "")
        return name

    def get_memory_ctx(
        self, target: TargetType = None, default_target: TargetType = "DPC"
    ) -> Optional[str]:
        return self._pick_best_ctx(
            "memory", self.memory_dap_ctx, self.memory_dpc_ctx, target, default_target
        )

    def get_memory_node(
        self, target: TargetType = None, default_target: TargetType = "DPC"
    ) -> Optional[Memory]:
        ctx = self.get_memory_ctx(target=target, default_target=default_target)
        node = self.get_node("memory", ctx, MemoryNode)
        memory_view = self.hw_server.get_view("memory")
        try:
            memory = Memory.check_and_upgrade(memory_view, node)  # noqa
        except Exception:  # noqa
            memory = None
        return memory

    def get_all_memory_nodes(self) -> List[Memory]:
        all_nodes = []
        if self.memory_dpc_ctx:
            all_nodes.append(self.get_memory_node(target="DPC"))
        if self.memory_dap_ctx:
            memory_view = self.hw_server.get_view("memory")
            top = self.get_memory_node(target="DAP")
            dap_nodes = []
            nodes_to_travel = deque([top])
            while nodes_to_travel:
                node = nodes_to_travel.popleft()
                if MemoryNode.is_compatible(node):
                    memory_node = memory_view.get_node(node.ctx, MemoryNode)
                    memory_node = Memory.check_and_upgrade(memory_view, memory_node)
                    dap_nodes.append(memory_node)
                    nodes_to_travel.extendleft(memory_view.get_children(memory_node))
            all_nodes.extend(dap_nodes)
        return all_nodes

    def search_memory_node_deep(
        self, any_target: str = None, default_target: TargetType = "DPC"
    ) -> Optional[Memory]:
        # Go dumpster diving searching for the first match to the requested node
        # Note: here the any_target is the node name (not just DPC or DAP)...
        # This is an inefficient matching algorithm meant to maintain backward
        # compatibility with the previous memory search algorithm
        memory_view = self.hw_server.get_view("memory")
        if any_target == "DPC" or any_target == "DAP" or any_target is None:
            return self.get_memory_node(target=any_target, default_target=default_target)
        else:
            # TODO: Make a more efficient way to do this
            found_node = None
            top = self.get_memory_node(target="DAP", default_target=default_target)
            if top:
                nodes_to_travel = deque([top])
                memory_node_list = []
                while nodes_to_travel:
                    node = nodes_to_travel.popleft()
                    if node.props.get("Name") == any_target:
                        found_node = self.get_node("memory", node.ctx, MemoryNode)  # upgrade
                        break
                    if MemoryNode.is_compatible(node):
                        memory_node = memory_view.get_node(node.ctx, MemoryNode)
                        memory_node_list.append(memory_node)
                        nodes_to_travel.extendleft(memory_view.get_children(memory_node))
        if found_node:
            found_node = Memory.check_and_upgrade(memory_view, found_node)  # noqa
        return found_node

    def get_debugcore_ctx(
        self, target: TargetType = None, default_target: TargetType = "DPC"
    ) -> Optional[str]:
        return self._pick_best_ctx(
            "debugcore", self.debugcore_dap_ctx, self.debugcore_dpc_ctx, target, default_target
        )

    def get_debugcore_node(
        self, target: TargetType = None, default_target: TargetType = "DPC"
    ) -> Optional[Node]:
        ctx = self.get_debugcore_ctx(target=target, default_target=default_target)
        return self.get_node("debugcore", ctx, DebugCoreClientNode)

    def get_chipscope_ctx(
        self, target: TargetType = None, default_target: TargetType = "DPC"
    ) -> Optional[str]:
        return self._pick_best_ctx(
            "chipscope", self.chipscope_dap_ctx, self.chipscope_dpc_ctx, target, default_target
        )

    def get_chipscope_node(
        self, target: TargetType = None, default_target: TargetType = "DPC"
    ) -> Optional[Node]:
        ctx = self.get_chipscope_ctx(target=target, default_target=default_target)
        node = self.get_node("chipscope", ctx, CoreParent)
        return node

    def get_node(self, view_name: str, node_ctx: str, upgrade_cls=None) -> Optional[Node]:
        """Returns the node for a given context"""
        node = None
        try:
            view = self._get_view(view_name)
            if view:
                if upgrade_cls:
                    node = view.get_node(node_ctx, upgrade_cls)
                else:
                    node = view.get_node(node_ctx)
        except Exception:  # noqa
            node = None
        return node

    def _get_view(self, view_name: str) -> Optional[ViewInfo]:
        """reduce repetitive typing for getting the server/view"""
        if self.cs_server and view_name == "chipscope":
            return self.cs_server.get_view("chipscope")
        elif self.hw_server and view_name == "jtag":
            return self.hw_server.get_view("jtag")
        elif self.hw_server and view_name == "memory":
            return self.hw_server.get_view("memory")
        elif self.hw_server and view_name == "debugcore":
            return self.hw_server.get_view("debugcore")
        else:
            return None

    def _pick_best_device_ctx(self):
        """A device is associated with many contexts. We need to consistently
        choose one to represent the device. It should be the one least likely
        to be removed.

        If the device context changes due to some event, it invalidates the
        whole device.

        Set the best context to use
        """
        if self.jtag_device_ctx:
            self.device_ctx = self.jtag_device_ctx
            self.device_view = "jtag"
        elif self.debugcore_dpc_ctx:
            self.device_ctx = self.debugcore_dpc_ctx
            self.device_view = "debugcore"
        elif self.debugcore_dap_ctx:
            self.device_ctx = self.debugcore_dap_ctx
            self.device_view = "debugcore"

    def _pick_best_ctx(
        self,
        view_name: str,
        dap_ctx: str,
        dpc_ctx: str,
        target: TargetType,
        default_target: TargetType,
    ) -> str:
        """Helper - given a dap and dpc ctx and target, pick the best we have"""
        # TODO: determine if node invalid - don't assume context valid!!
        if target == "DAP":
            return dap_ctx  # explicitly specified
        elif target == "DPC":
            return dpc_ctx  # explicitly specified
        elif target is None:
            # Best guess based on availability and known default
            if view_name == "chipscope":
                view = self.cs_server.get_view(view_name)
            else:
                view = self.hw_server.get_view(view_name)
            try:
                is_dpc_valid = view.get_node(dpc_ctx) is not None
            except Exception:  # noqa
                is_dpc_valid = False
            try:
                is_dap_valid = view.get_node(dap_ctx) is not None
            except Exception:  # noqa
                is_dap_valid = False

            if default_target == "DPC" and is_dpc_valid:
                return dpc_ctx
            elif default_target == "DAP" and is_dap_valid:
                return dap_ctx
            else:
                # default target not available - return the best thing we have
                if is_dpc_valid:
                    return dpc_ctx
                elif is_dap_valid:
                    return dap_ctx
        return ""
