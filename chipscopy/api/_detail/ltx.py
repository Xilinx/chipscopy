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
import sys
from pprint import pformat
from collections import defaultdict
from dataclasses import dataclass
from typing import Union, Dict, List, Optional, Tuple

from chipscopy.api import CoreType


@dataclass(frozen=True)
class LtxProbe:
    """Represents a single probe in the LTX file"""

    name: str
    direction: str
    probe_type: str
    is_bus: bool
    port_index: int
    msb_index: int
    lsb_index: int


@dataclass(frozen=True)
class LtxCore:
    core_type: CoreType
    cell_name: str
    uuid: str
    debug_hub_address: int
    probes: [LtxProbe]
    upstream_cell_names: [str]

    def __repr__(self) -> str:
        return pformat(self.__dict__)


@dataclass(frozen=True)
class LtxStreamRef:
    cell_name: str
    uuid: int
    stream_index: int


class Ltx:
    __LTX_IP_NAME_TO_CORE_TYPE = {
        "axi_dbg_hub": CoreType.AXI_DEBUG_HUB,
        "axis_ila": CoreType.AXIS_ILA,
        "axis_vio": CoreType.AXIS_VIO,
        "trace": CoreType.AXIS_TRACE,
    }

    __NULL_UUID = "0" * 32

    def __init__(self):
        self._debug_hub_addresses: [int] = []
        self._cores: {CoreType, [LtxCore]} = defaultdict(list)
        # key: upstream_cell_name. value: LtxStreamRef list
        self._downstream_refs: {str, List[LtxStreamRef]} = defaultdict(list)

    def get_debug_hub_addresses(self) -> [int]:
        return self._debug_hub_addresses

    def get_core(self, core_type: CoreType, uuid: str = "") -> Optional[LtxCore]:
        """ Return first matching core, or None."""
        cores = [core for core in self._cores[core_type] if core.uuid.upper() == uuid.upper()]
        return cores[0] if cores else None

    def get_downstream_refs(self, upstream_core_name: str) -> List[LtxStreamRef]:
        """Return list of LtxStreamRef"""
        return self._downstream_refs.get(upstream_core_name, [])

    def get_cores(self, core_type: CoreType) -> [LtxCore]:
        return self._cores[core_type]

    def parse_file(self, probes_file: str) -> None:
        with open(probes_file, "r") as json_file:
            json_data = json.load(json_file)

        ltx_root = json_data.get("ltx_root", None)
        ltx_data = ltx_root.get("ltx_data", []) if ltx_root else []
        # Always expect one item in 'ltx_data' list.
        ltx_data_item = ltx_data[0] if ltx_data else None
        debug_cores = ltx_data_item.get("debug_cores", None) if ltx_data_item else None
        if not debug_cores:
            return

        for debug_core in debug_cores:
            core = Ltx._read_core(debug_core)
            if not core:
                continue

            self._cores[core.core_type].append(core)
            for idx, up_stream_cell_names in enumerate(core.upstream_cell_names):
                self._downstream_refs[up_stream_cell_names].append(
                    LtxStreamRef(core.cell_name, core.uuid, idx)
                )

        self._debug_hub_addresses = [
            int(core.debug_hub_address, 16) for core in self._cores[CoreType.AXI_DEBUG_HUB]
        ]

    def verify_port_width_by_type(
        self, core_type: CoreType, uuid: str, width_by_type: Dict[str, List[int]]
    ) -> None:
        mismatch_msg = "Mismatch between LTX file(s) and device debug core.\n"
        core = self.get_core(core_type, uuid)
        if not core:
            raise Exception(
                mismatch_msg
                + f"Device {core_type.value} core with UUID {uuid} is not found in the LTX file."
            )

        for probe in core.probes:
            port_widths = width_by_type.get(probe.probe_type, [])
            port_width = port_widths[probe.port_index] if len(port_widths) > probe.port_index else 0
            if port_width == 0:
                raise Exception(
                    mismatch_msg
                    + f'LTX core "{core.cell_name}" probe "{probe.name}" of type {probe.probe_type} '
                    f'refers to core port index "{probe.port_index}", '
                    f"which does not exist in the debug core for probe type {probe.probe_type}."
                )
            if port_width <= probe.msb_index:
                raise Exception(
                    mismatch_msg
                    + f'LTX core "{core.cell_name}" probe "{probe.name}" of type {probe.probe_type} '
                    f"has invalid msb index:{probe.msb_index}.\n The port width is {port_width}"
                )

    @staticmethod
    def _read_core(in_core: {}) -> Union[LtxCore, None]:
        pins = in_core.get("pins", [])
        probes = [Ltx._read_pin(pin) for pin in pins]
        probes = [probe for probe in probes if probe]
        ip_name = in_core.get("ipName", "")
        if ip_name == "axi_dbg_hub" and "address_info" in in_core:
            addr = in_core["address_info"].get("offset", "")
        else:
            addr = ""

        core_type = Ltx.__LTX_IP_NAME_TO_CORE_TYPE.get(ip_name, "")
        cell_name = in_core.get("name", "")
        uuid = in_core.get("uuid", Ltx.__NULL_UUID).upper()
        upstream = in_core.get("master", "")
        upstream_cell_names = upstream.split(":") if upstream else []

        # todo error checks?
        if not core_type:
            return None
        return LtxCore(core_type, cell_name, uuid, addr, probes, upstream_cell_names)

    @staticmethod
    def _read_pin(pin: {}) -> LtxProbe:
        nets = pin.get("nets", [])
        name = nets[0].get("name", "") if nets else ""

        probe_type = pin.get("type", "")
        is_bus = pin.get("isVector", False)
        port_index = pin.get("portIndex", 0)
        # LTX file has right/left switched.
        msb_index = pin.get("rightIndex", 0)
        lsb_index = pin.get("leftIndex", 0)
        direction = pin.get("direction", "")

        # todo error check?
        return LtxProbe(name, direction, probe_type, is_bus, port_index, msb_index, lsb_index)

    def __str__(self) -> str:
        dump = "\ndebug_hub_addresses :" + ",".join(
            [hex(addr) for addr in self._debug_hub_addresses]
        )
        for core_type, cores in self._cores.items():
            underline = "=" * (len(core_type.__str__()) + 4)
            for idx, core in enumerate(cores):
                dump += f"\n\n{core_type}:{idx:3}\n{underline}\n"
                dump += core.__str__() + "\n"

        return dump
