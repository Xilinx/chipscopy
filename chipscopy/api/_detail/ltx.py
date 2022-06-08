# Copyright 2022 Xilinx, Inc.
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
from enum import Enum, EnumMeta
from io import TextIOBase
from pprint import pformat
from collections import defaultdict
from dataclasses import dataclass, asdict
from re import compile as re_compile
from typing import Union, Dict, List, Optional, Tuple, NewType

from chipscopy.api import CoreType
from chipscopy.utils import Enum2StrEncoder


@dataclass(frozen=True)
class LtxProbe:
    """Represents a single probe in the LTX file"""

    name: str
    direction: str
    probe_type: str
    port_index: int
    port_msb_index: int
    port_lsb_index: int
    is_bus: bool
    bus_left_index: int
    bus_right_index: int
    enum_def: Optional[EnumMeta]


@dataclass(frozen=True)
class LtxCore:
    core_type: CoreType
    cell_name: str
    uuid: str
    debug_hub_address: int
    probes: [LtxProbe]
    upstream_cell_names: [str]
    """ E.g. A VIO debug core would list the connected debug_hub, as an upstream core."""

    def __str__(self) -> str:
        return pformat(self.__dict__)


@dataclass(frozen=True)
class LtxStreamRef:
    """
    Reference to a debug core stream interface.
    A debug core has one or more control/data streams which connect to other debug cores.
    E.g. A debug hub may have multiple downstream connections, one for each connected VIO and ILA debug cores.
    """

    cell_name: str
    uuid: int
    stream_index: int


ParentEnums = NewType("ParentEnums", Dict[int, Dict[str, str]])


class Ltx:
    __LTX_IP_NAME_TO_CORE_TYPE = {
        "axi_dbg_hub": CoreType.AXI_DEBUG_HUB,
        "axis_ila": CoreType.AXIS_ILA,
        "axis_vio": CoreType.AXIS_VIO,
        "trace": CoreType.AXIS_TRACE,
        "hw_trace": CoreType.AXIS_TRACE,
    }

    __NULL_UUID = "0" * 32
    __net_bus_index_re = None
    __subnet_bus_index_re = None

    def __init__(self):
        self._debug_hub_addresses: [int] = []
        self._cores: {CoreType, [LtxCore]} = defaultdict(list)
        # key: upstream_cell_name. value: list of downstream LtxStreamRef
        # E.g. an entry for a debug_hub core, would list other debug cores connected to it.
        self._downstream_refs: {str: List[LtxStreamRef]} = defaultdict(list)
        self._parent_id_to_enum: ParentEnums = {}

    def get_debug_hub_addresses(self) -> [int]:
        return self._debug_hub_addresses

    def get_core(self, core_type: CoreType, uuid: str = "") -> Optional[LtxCore]:
        """ Return first matching core, or None."""
        cores = [core for core in self._cores[core_type] if core.uuid.upper() == uuid.upper()]
        return cores[0] if cores else None

    def get_downstream_refs(self, upstream_core_name: str) -> List[LtxStreamRef]:
        """
        Returns list of LtxStreamRef, which lists which debug cores the upstream core is connected to.
        The list is not ordered.
        E.g. given a debug_hub cell_name, the function returns a list of connected debug cores.
        """
        return self._downstream_refs.get(upstream_core_name, [])

    def get_cores(self, core_type: CoreType) -> [LtxCore]:
        return self._cores[core_type]

    def parse_file(self, probes_file: str) -> None:
        with open(probes_file, "r") as json_file:
            self.parse_ltx(json_file)

    def parse_ltx(self, fh: TextIOBase) -> None:
        json_data = json.load(fh)

        ltx_root = json_data.get("ltx_root", None)
        ltx_data = ltx_root.get("ltx_data", []) if ltx_root else []
        # Always expect one item in 'ltx_data' list.
        ltx_data_item = ltx_data[0] if ltx_data else None
        debug_cores = ltx_data_item.get("debug_cores", None) if ltx_data_item else None
        if not debug_cores:
            return
        if "parent_nets" in ltx_data_item:
            self._parent_id_to_enum = self._read_parent_net_enums(ltx_data_item["parent_nets"])
        for debug_core in debug_cores:
            core = Ltx._read_core(debug_core, self._parent_id_to_enum)
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
            raise KeyError(
                mismatch_msg
                + f"Device {core_type.value} core with UUID {uuid} is not found in the LTX file."
            )

        for probe in core.probes:
            port_widths = width_by_type.get(probe.probe_type, [])
            port_width = port_widths[probe.port_index] if len(port_widths) > probe.port_index else 0
            if port_width == 0:
                raise KeyError(
                    mismatch_msg
                    + f'LTX core "{core.cell_name}" probe "{probe.name}" of type {probe.probe_type} '
                    f'refers to core port index "{probe.port_index}", '
                    f"which does not exist in the debug core for probe type {probe.probe_type}."
                )
            if port_width <= probe.port_msb_index:
                raise ValueError(
                    mismatch_msg
                    + f'LTX core "{core.cell_name}" probe "{probe.name}" of type {probe.probe_type} '
                    f"has invalid msb index:{probe.port_msb_index}.\n The port width is {port_width}"
                )

    @staticmethod
    def _read_parent_net_enums(parent_nets: []) -> ParentEnums:
        """State values are returned as binary strings, so the bit_width is obvious.
        Return type: {parent_id: {state_name, state_binary_str_value}}
        """
        pid_to_enums = {}
        for pnet in parent_nets:
            pid_states = {}
            for sr in pnet.get("state_reg", []):
                pid_states.update((state["name"], state["val"]) for state in sr.get("states", []))
            if pid_states:
                pid_to_enums[pnet["id"]] = pid_states
        return pid_to_enums

    @staticmethod
    def _get_enum_def(
        probe_name: str, parent_ids: [int], parent_enums: ParentEnums, probe_width: int
    ) -> Optional[Enum]:
        if not parent_ids:
            return None
        p_enum = parent_enums.get(parent_ids[0], None)
        if not all([len(val) == probe_width for val in p_enum.values()]):
            # Old LTX files have bad enums, for non-important probes. Skip enum.
            return None
        enum_vals = {state: int(val, 2) for state, val in p_enum.items()}
        return Enum(probe_name, enum_vals)

    @staticmethod
    def _read_core(in_core: {}, parent_enums: ParentEnums) -> Union[LtxCore, None]:
        pins = in_core.get("pins", [])
        probes = [Ltx._read_pin(pin, parent_enums) for pin in pins]
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

        # todo syntax/semantic checks?
        if not core_type:
            return None
        return LtxCore(core_type, cell_name, uuid, addr, probes, upstream_cell_names)

    @staticmethod
    def read_nets(nets: []) -> Tuple[bool, int, int, List[int]]:
        """
        Returns (name, left index, right index, [parent_ids])
        """
        if not nets:
            return False, 0, 0, []

        parent_ids = [net.get("parentNetId", None) for net in nets]
        parent_ids = [p_id for p_id in parent_ids if p_id is not None]

        left_name = nets[0].get("name", "")
        right_name = nets[-1].get("name", "")

        if not Ltx.__net_bus_index_re:
            Ltx.__net_bus_index_re = re_compile(r"(.+)\[(-?\d+)]$")
        left_m = Ltx.__net_bus_index_re.match(left_name)
        right_m = Ltx.__net_bus_index_re.match(right_name)
        if not left_m or not right_m:
            return False, 0, 0, parent_ids
        return left_m.group(1), int(left_m.group(2)), int(right_m.group(2)), parent_ids

    @staticmethod
    def read_subnets(subnets: []) -> Tuple[int, int, List[int]]:
        """
        If a bus returns (left index, right index, [parent_ids])
        """
        if not subnets:
            return 0, 0, []

        parent_ids = [subnet.get("parentNetId", None) for subnet in subnets]
        parent_ids = [p_id for p_id in parent_ids if p_id is not None]

        left_name = subnets[0].get("name", "")
        right_name = subnets[-1].get("name", "")

        if not Ltx.__subnet_bus_index_re:
            Ltx.__subnet_bus_index_re = re_compile(r".+\[(-?\d+)]$")
        left_m = Ltx.__subnet_bus_index_re.match(left_name)
        right_m = Ltx.__subnet_bus_index_re.match(right_name)
        if not left_m or not right_m:
            return 0, 0, parent_ids
        return int(left_m.group(1)), int(right_m.group(1)), parent_ids

    @staticmethod
    def _read_pin(pin: {}, parent_enums: ParentEnums) -> LtxProbe:
        nets = pin.get("nets", [])
        if len(nets) == 1:
            name = nets[0].get("name", "") if nets else ""
            subnets = nets[0].get("subnets", [])
            bus_left_index, bus_right_index, parent_ids = Ltx.read_subnets(subnets)
        else:
            # Some state machine registers are split up in multiple nets.
            name, bus_left_index, bus_right_index, parent_ids = Ltx.read_nets(nets)

        probe_type = pin.get("type", "")
        is_bus = pin.get("isVector", False)
        port_index = pin.get("portIndex", 0)
        # The LTX file has port right/left switched.
        port_msb_index = pin.get("rightIndex", 0)
        port_lsb_index = pin.get("leftIndex", 0)
        direction = pin.get("direction", "")
        probe_def = Ltx._get_enum_def(
            name, parent_ids, parent_enums, abs(bus_left_index - bus_right_index) + 1
        )
        return LtxProbe(
            name,
            direction,
            probe_type,
            port_index,
            port_msb_index,
            port_lsb_index,
            is_bus,
            bus_left_index,
            bus_right_index,
            probe_def,
        )

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

    def __repr__(self) -> str:
        cores = defaultdict(list)
        for core_type, core_list in self._cores.items():
            for core in core_list:
                cores[str(core_type)].append(asdict(core))
        downstream_refs = defaultdict(list)
        for up, down_list in self._downstream_refs.items():
            for down in down_list:
                downstream_refs[up].append(asdict(down))

        ret_dict = {
            "debug_hub_addresses": [f"0x{addr:x}" for addr in self._debug_hub_addresses],
            "downstream_refs": downstream_refs,
            "parent_id_to_enum": self._parent_id_to_enum,
            "cores": cores,
        }
        json_dict = json.dumps(ret_dict, cls=Enum2StrEncoder, indent=4)
        return json_dict
