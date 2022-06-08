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

import enum
from dataclasses import dataclass
from typing import NamedTuple, Any, Optional

from chipscopy.api import CoreType, dataclass_fields, filter_props
from chipscopy.api._detail.ltx import Ltx, LtxCore, LtxProbe
from chipscopy.client.axis_ila_core_client import (
    AxisIlaCoreClient as TCF_AxisIlaCoreClient,
    ILAPortType as TCF_ILAPortType,
)
from chipscopy.shared.ila_util import is_hex_str


class ILAMatchUnitType(enum.Enum):
    """
    Probe comparator types. Only LARGE is supported.

    ===========  =====================================================================
    Enum Value   Description
    ===========  =====================================================================
    SMALL        Not supported.
    MEDIUM       Not supported.
    LARGE        Supports operators: ['==', '!=', '>', '<', '>=', '<=', '||']
                  and bit values: '01xXrRfFnNbBtTlLsS\_'
    ===========  =====================================================================

    """

    SMALL = 0
    MEDIUM = 1
    LARGE = 2


class ILAProbeRadix(enum.Enum):
    """
    Display radix for probe data values.

    =====================  ================================
    Enum Value             Description
    =====================  ================================
    BIN                    Not Supported.
    ENUM                   Enumeration
    HEX                    Default.
    SIGNED                 Not supported.
    UNSIGNED               Not supported.
    =====================  ================================

    """

    BIN = 0
    ENUM = 1
    HEX = 2
    SIGNED = 3
    UNSIGNED = 4


@dataclass(frozen=True)
class ILAPort:
    """Probe Port on the ILA Core"""

    bit_width: int
    """Number of port bits."""
    data_bit_index: int
    """Start bit index in waveform data."""
    index: int
    """Port index"""
    is_trigger: bool
    """Port is used for triggering."""
    is_data: bool
    """Port is used for capturing data."""
    match_unit_count: int
    """Number of compare match units, available to the port."""
    match_unit_type: ILAMatchUnitType
    """Type of match unit."""


ILA_PORT_MEMBERS = dataclass_fields(ILAPort)


@dataclass(frozen=True)
class ILAProbe:
    """Logical probe. Probes may share the same probe port."""

    name: str
    """Name of probe."""
    bit_width: int
    """Number of probe bits."""
    is_data: bool
    """Probe is used to capture waveform data."""
    is_trigger: bool
    """Probe can be used in trigger settings."""
    map: str
    """How probe is mapped to ports."""
    mu_count: int
    """Max number of compare match units, available to the probe."""
    is_bus: bool = False
    """True for bus probes"""
    bus_left_index: Optional[int] = None
    """Bus left index. E.g. 5 in probe ``counter[5:0]``"""
    bus_right_index: Optional[int] = None
    """Bus right index. E.g. 0 in probe ``counter[5:0]``"""


ILA_PROBE_MEMBERS = dataclass_fields(ILAProbe)


ILA_MATCH_OPERATORS = ["==", "!=", ">", "<", ">=", "<=", "||"]
"""
Operators for probe compare values.

========= =================================================================
Operator  Description
========= =================================================================
==        Equal
!=        Not equal
<         Less than
<=        Equal or less than
>         Greater than
>=        Equal or Greater than
||        Reduction OR
========= =================================================================

"""


ILA_MATCH_BIT_VALUES = "01xXrRfFnNbBtTlLsS_"
"""
Binary bit values for probe compare values.

========= =================================================================
Bit Value Description
========= =================================================================
_         Underscore separator for readability.
X         Don't care bit matches any bit-value.
0         Zero
1         One
F         Falling. Transition 1 -> 0
R         Rising. Transition 0 -> 1
L         Laying. Opposite to R.
S         Staying. Opposite to F.
B         Either Falling or Rising.
N         No change. Opposite to B.
========= =================================================================

"""


@dataclass
class ILAProbeValues:
    """
    A compare value consists of a pair: <operator> and <value>
    <value> may be of type int or binary/hex string of the correct bit_width.

    Hex values start with a '0x' prefix.
    Note! String values for 3-bit probes are always interpreted as binary values,
    e.g. "0x0", "0x1", "0xx", "011".

    An empty list is a don't-care value.




        Example: Test for LSB is '0' on a 4-bit probe.
           ['==',   'XXX0']

        Example: Range check, assuming the global Trigger Condition is ILATriggerCondition.AND:
           ['>=',   '0x3',   '<=',   '0x10']

        Example: Range check, assuming the global Trigger Condition is ILATriggerCondition.AND:
           ['>=',   3,   '<=',   10]

        Example: Test equal to any of 3 numbers, assuming the global Trigger Condition is ILATriggerCondition.OR:
           ['==',   '0011',   '==',   '0111',   '==',   '1111']

        Example: 4-bit dont-care value.
           ['==',   'XXXX']

        Example: Dont-care value, written as an empty list.
           []

    """

    bit_width: int
    """Number of probe bits."""
    trigger_value: []
    """Trigger compare values, in a list."""
    capture_value: []
    """Basic capture compare value. A two item list with [<operator>, <value>]"""
    display_radix: ILAProbeRadix = ILAProbeRadix.HEX
    """Display radix, when exporting waveform data. Default is ILAProbeRadix.HEX"""
    enum_def: Optional[enum.EnumMeta] = None
    """Enum class defining {name:int} enum values, for this probe."""

    def default_value(self):
        return ["==", "x" * self.bit_width]


class ILABitRange(NamedTuple):
    index: int
    """Bit index."""
    length: int
    """Bit length."""


#
# ports functions
#
def verify_ports(ltx: Ltx, uuid: str, ports: [ILAPort]) -> None:
    def get_width(port: ILAPort, trigger: bool, data: bool) -> int:
        return port.bit_width if port.is_trigger == trigger and port.is_data == data else 0

    widths_by_type = {
        "DATA": [get_width(port, trigger=False, data=True) for port in ports],
        "DATA_TRIGGER": [get_width(port, trigger=True, data=True) for port in ports],
        "TRIGGER": [get_width(port, trigger=True, data=False) for port in ports],
    }
    ltx.verify_port_width_by_type(CoreType.AXIS_ILA, uuid, widths_by_type)


def ports_from_tcf_props(props) -> [ILAPort]:
    ports = []
    for p_index, p in enumerate(props["ports"]):
        port_info = filter_props(p, ILA_PORT_MEMBERS)
        port_info["index"] = p_index
        port_info["match_unit_count"] = len(p["mus"])
        port_type = p["port_type"]
        port_info["is_data"] = port_type & TCF_ILAPortType.IS_DATA != 0
        port_info["is_trigger"] = port_type & TCF_ILAPortType.IS_TRIGGER != 0
        if port_type & TCF_ILAPortType.MU_EDGE_EQ_REL:
            port_info["match_unit_type"] = ILAMatchUnitType.LARGE
        elif port_type & TCF_ILAPortType.MU_EDGE_EQ_EDGE:
            port_info["match_unit_type"] = ILAMatchUnitType.MEDIUM
        else:
            port_info["match_unit_type"] = ILAMatchUnitType.SMALL
        ports.append(ILAPort(**port_info))

    return ports


#
# probes functions
#
def verify_probe_value(value_list: [], is_trigger: bool, probe: ILAProbe, enum_def=None):
    """
    int values, enums, binary string and hex strings are supported for now.
    More verification is done by the cs_server.

    Args:
        enum_def ():
    """

    def is_valid_enum_str(number) -> bool:
        try:
            enum = enum_def[number]
        except KeyError:
            return False
        verify_enum_value(enum)
        return True

    def get_hex_char_bit_len(ch: str) -> int:
        if ch in "x01":
            return 1
        elif ch in "23":
            return 2
        elif ch in "4567":
            return 3
        else:
            return 4

    def verify_int_bit_length(number):
        val_len = int.bit_length(number)
        if val_len > probe.bit_width:
            raise ValueError(
                f'Probe "{probe.name}" has bit width:{probe.bit_width} and cannot be assigned'
                f' value "{number}" which has bit width:{val_len}.'
            )

    def verify_enum_value(enum: enum.Enum):
        if not isinstance(enum, enum_def):
            raise TypeError(f'Probe "{probe.name}" cannot be assigned enum value {enum}.')
        verify_int_bit_length(enum.value)

    def verify_one_hex_value(op: str, hex_number: str):
        valid_hex_chars = "x0123456789abcdef_"
        value_no_underscore = "".join([ch for ch in hex_number[2:].lower() if ch != "_"])
        hex_val_len = len(value_no_underscore)
        if hex_val_len == 0:
            raise ValueError(
                f'Probe "{probe.name}" has cannot be assigned invalid value "{hex_number}".'
            )
        if not all([ch in valid_hex_chars for ch in value_no_underscore]):
            raise ValueError(
                f'Probe "{probe.name}" value "{hex_number}" has invalid character(s).'
                f' Valid characters are {valid_hex_chars}".'
            )
        required_hex_ch_len = (probe.bit_width + 3) // 4
        if hex_val_len != required_hex_ch_len:
            raise ValueError(
                f'Probe "{probe.name}" has bit width:{probe.bit_width} requiring {required_hex_ch_len} hex character(s)'
                f' but value "{hex_number}" has only {hex_val_len} hex character(s).'
            )
        bin_val_len = (hex_val_len - 1) * 4 + get_hex_char_bit_len(value_no_underscore[0])
        if bin_val_len > probe.bit_width:
            # Too many bits in first hex char.
            raise ValueError(
                f'Probe "{probe.name}" has bit width:{probe.bit_width} and cannot be assigned'
                f' value "{hex_number}" which has bit width:{bin_val_len}.'
            )
        if (op not in ["==", "!="]) and ("x" in value_no_underscore):
            raise ValueError(
                f'Probe "{probe.name}" is assigned value "{op} {hex_number}". '
                f"""The operator cannot be used when the value has a don't care "x"."""
            )

    def verify_value_pair(op: str, number):
        if op not in ILA_MATCH_OPERATORS:
            raise ValueError(
                f'Probe "{probe.name}" operator "{op}" is not one of the allowed operators: '
                f"{ILA_MATCH_OPERATORS}."
            )

        if isinstance(number, int):
            verify_int_bit_length(number)
        elif enum_def and isinstance(number, enum.Enum):
            verify_enum_value(number)
        elif is_hex_str(number, probe.bit_width):
            verify_one_hex_value(op, number)
        elif enum_def and is_valid_enum_str(number):
            # is_valid_enum_str() will did the checking if it is an enum string for this probe.
            pass
        elif isinstance(number, str):
            # binary value
            if not all([ch in ILA_MATCH_BIT_VALUES for ch in number]):
                raise TypeError(
                    f'Probe "{probe.name}" value "{number}" has invalid character(s).'
                    f' Valid characters are "{ILA_MATCH_BIT_VALUES}".'
                )

            val_len = len(number) - number.count("_")
            if val_len != probe.bit_width:
                raise ValueError(
                    f'Probe "{probe.name}" has bit width:{probe.bit_width} and cannot be assigned'
                    f' value "{number}" which has bit width:{val_len}.'
                )
            if (op not in ["==", "!="]) and not all([ch in "01_" for ch in number]):
                raise TypeError(
                    f'Probe "{probe.name}" is assigned value "{op} {number}". '
                    f'The operator "{op}" can only be used with "0" and "1" bit values.'
                )

    # Empty list are allowed. Used for DONT_CARE values.
    if not isinstance(value_list, list):
        raise TypeError(
            f'Probe "{probe.name}" trigger/capture set value {value_list} is required to be a list.'
        )
    if len(value_list) > 2 and not is_trigger:
        raise ValueError(
            f'Probe "{probe.name}" capture set value {value_list} list length cannot be more than 2.'
        )
    if len(value_list) % 2 != 0:
        raise TypeError(
            f'Probe "{probe.name}" trigger/capture set value {value_list} is required to be a list'
            " with even number of items. Odd items are operators and even items are numbers."
        )
    for idx in range(0, len(value_list), 2):
        verify_value_pair(value_list[idx], value_list[idx + 1])


def create_probes_from_ports_and_ltx(
    tcf_ila: TCF_AxisIlaCoreClient, ports: [ILAPort], ltx: Ltx, uuid: str
) -> ({}, {}, str, {}):
    """ Returns:  probes, map_to_port_seqs, cell_name, probe enum defs"""

    def process_one_tcf_probe(attrs: {str, Any}) -> {}:
        res = {
            key: value
            for key, value in attrs.items()
            if key in {"bit_width", "mu_count", "map", "name"}
        }
        port_type = TCF_ILAPortType(attrs.get("port_type", 0))
        res["is_data"] = TCF_ILAPortType.IS_DATA in port_type
        res["is_trigger"] = TCF_ILAPortType.IS_TRIGGER in port_type
        return res

    def process_one_tcf_probe_mapping(attrs: {str, Any}) -> [ILABitRange]:
        def create_bit_range(map_seq: ()) -> ILABitRange:
            port_idx, high_idx, low_idx = map_seq
            start = ports[port_idx].data_bit_index + low_idx
            length = abs(high_idx - low_idx) + 1
            return ILABitRange(start, length)

        tcf_mapping = attrs.get("__map_seqs", [])
        mapping = [create_bit_range(map_seq) for map_seq in tcf_mapping]
        return mapping

    def ltx_probes_to_tcf_pdefs(ltx: LtxCore) -> [{str, str}]:
        return [
            {
                "name": probe.name,
                "net_name": probe.name,
                "map": f"port{probe.port_index}[{probe.port_msb_index}:{probe.port_lsb_index}]",
            }
            for probe in ltx.probes
            if probe.probe_type != "DATA"
        ]

    def add_probe_bus_info(p_dicts: {}, ltx_probes: [LtxProbe]) -> None:
        for ltx_p in ltx_probes:
            if ltx_p.is_bus and ltx_p.name in p_dicts:
                p_dicts[ltx_p.name].update(
                    {
                        "is_bus": ltx_p.is_bus,
                        "bus_left_index": ltx_p.bus_left_index,
                        "bus_right_index": ltx_p.bus_right_index,
                    }
                )

    def get_probe_enum_defs(p_dicts: {}, ltx_probes: [LtxProbe]) -> {}:
        res = {}
        for ltx_p in ltx_probes:
            if ltx_p.enum_def and ltx_p.name in p_dicts:
                res[ltx_p.name] = ltx_p.enum_def
        return res

    cell_name = ""
    tcf_ila.undefine_probe([])
    ltx_core = ltx.get_core(CoreType.AXIS_ILA, uuid) if ltx else None
    if ltx and not ltx_core:
        raise IndexError(f"Unable to find ILA core with uuid:{uuid} in LTX file.")
    if ltx_core:
        cell_name = ltx_core.cell_name
        probe_defs = ltx_probes_to_tcf_pdefs(ltx_core)
        tcf_ila.define_probe(probe_defs)
    else:
        tcf_ila.define_port_probes({"force": True})

    probe_attrs = ["name", "bit_width", "mu_count", "port_type", "map", "__map_seqs"]
    tcf_probes = tcf_ila.get_probe([], probe_attrs)
    probe_dicts = {p_name: process_one_tcf_probe(attrs) for p_name, attrs in tcf_probes.items()}
    # Add bus information
    add_probe_bus_info(probe_dicts, ltx_core.probes)
    enum_defs = get_probe_enum_defs(probe_dicts, ltx_core.probes)
    map_to_port_seqs = {
        attrs["map"]: process_one_tcf_probe_mapping(attrs) for p_name, attrs in tcf_probes.items()
    }
    probes = {p_name: ILAProbe(**probe) for p_name, probe in probe_dicts.items()}
    return probes, map_to_port_seqs, cell_name, enum_defs


def verify_probe_enum_def(probe: ILAProbe, enum_def: enum.EnumMeta):
    if not isinstance(enum_def, enum.EnumMeta):
        raise TypeError(
            f"enum definition need to be an Enum class. Type '{type(enum_def)}' was passed in."
        )
    for ei in enum_def:
        if type(ei.value) is not int:
            raise TypeError(f'enum {ei} value must be of type "int" for probe "{probe.name}".')
        if ei.value.bit_length() > probe.bit_width:
            raise ValueError(
                f"Enum value {ei} has bit length:{ei.value.bit_length()}, "
                f'which is more than probe "{probe.name}" bit length:{probe.bit_width}.'
            )
