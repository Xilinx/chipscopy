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

from dataclasses import dataclass
from enum import Enum, unique
from pprint import pformat
from typing import Optional, Callable, List, Set

from chipscopy import dm
from chipscopy.api._detail import dataclass_fields, filter_props
from chipscopy.dm import NodeListener


@unique
class CoreType(Enum):
    IBERT = "IBERT"
    NOC_ROOT = "NOC CORE"
    DDR = "DDRMC"
    HBM = "HBM"
    AXIS_ILA = "AXIS ILA"
    AXIS_VIO = "AXIS VIO"
    AXIS_PCIE = "AXIS PCIE"
    AXIS_TRACE = "AXIS TRACE"
    AXI_DEBUG_HUB = "AXI_DEBUG HUB"
    SYSMON = "SYSMON"


@dataclass(frozen=True)
class CoreInfo:
    """Debug Fabric Core version information."""

    core_type: int
    """Core type number."""
    drv_ver: int
    """SW/IP interface version."""
    core_major_ver: int
    """Core IP major version."""
    core_minor_ver: int
    """Core IP minor version."""
    tool_major_ver: int
    """Major version of the design tool, which created the core."""
    tool_minor_ver: int
    """Minor version of the design tool, which created the core."""
    uuid: str
    """Core UUID. UUID is unique among debug cores in the design."""

    def __str__(self) -> str:
        return pformat(self.__dict__, 2)


CORE_INFO_MEMBERS = dataclass_fields(CoreInfo)


def get_core_info(tcf_node: dm.Node) -> Optional[CoreInfo]:
    if set(CORE_INFO_MEMBERS).issubset(tcf_node.props):
        # Only fabric cores have core info information.
        return CoreInfo(**filter_props(tcf_node.props, CORE_INFO_MEMBERS))

    return None


class DMNodeListener(NodeListener):
    """
    The Session hooks into the hw_server and cs_server with a DMNodeListener to
    listen to events that happen when hardware changes occur.
    This enables the session to keep track of asynchronous events to the device
    and adjust cached values as needed to remain consistent with the hardware
    state.

    When an events happen on a tracked node, the registered callback is called
    with node event details.

    Usage:

    ::

        def _node_callback(self, action: DMNodeListener.NodeAction, node: Node, props: Optional[Set]):
            ... handle callback ...


        # register for callbacks
        self.hw_server.get_view("memory").add_node_listener(DMNodeListener(self._node_callback))

        ...


    """

    @unique
    class NodeAction(Enum):
        NODE_ADDED = "NODE_ADDED"
        NODE_REMOVED = "NODE_REMOVED"
        NODE_CHANGED = "NODE_CHANGED"

    def __init__(self, callback: Callable[[NodeAction, dm.Node, Optional[Set]], None]):
        super().__init__()
        self._callback = callback

    def nodes_added(self, nodes: List[dm.Node]):
        if self._callback:
            for node in nodes:
                self._callback(DMNodeListener.NodeAction.NODE_ADDED, node, None)

    def node_changed(self, node: dm.Node, updated_keys: Set[str]):
        if self._callback:
            self._callback(DMNodeListener.NodeAction.NODE_CHANGED, node, updated_keys)

    def nodes_removed(self, nodes: List[dm.Node]):
        if self._callback:
            for node in nodes:
                self._callback(DMNodeListener.NodeAction.NODE_REMOVED, node, None)
