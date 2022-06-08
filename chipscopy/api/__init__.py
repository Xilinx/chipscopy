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

from dataclasses import dataclass
from enum import Enum, unique
from pprint import pformat
from typing import Optional

from chipscopy import dm
from chipscopy.api._detail import dataclass_fields, filter_props


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
