# Copyright (C) 2022, Xilinx, Inc.
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

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, List, NamedTuple, Optional, Tuple
from chipscopy.client.axis_ila_core_client import ILATriggerCondition, ILAPort

#
#  IlaMapper -  Mapping match compare values to port match units.
#
#    Look at test_axis_ila_mapper.py, to see data structure json dumps of input data
#    and output data.
#


@dataclass
class Port:
    index: int
    mu_count: int
    width: int
    # 'mu_values' filled out by mapper
    mu_values: [str] = field(default_factory=lambda: [])


@dataclass
class Match:
    name: str
    port_index: int
    # Position of match value LSB, on the port.
    bit_index: int
    op: str
    value: str
    # Un-mapped value is -1.
    mu_index: int = -1
    # 'source' fill out by mapper
    source: str = ""
    # Corresponds to all probes names added to this Match. For debugging.
    _source_names: List[str] = field(default_factory=lambda: [])
    # _source_names: [str] = None
    # Compare value indices in same order as _source_names. For debugging.
    _source_value_indices: List[int] = field(default_factory=lambda: [])
    # _source_value_indices: [int] = None

    @staticmethod
    def get_sort_key():
        return lambda match: (match.port_index << 16) + match.bit_index

    def is_dont_care(self):
        return all(ch == "X" for ch in self.value)

    def ensure_proper_types(self):
        """
        Some old Vivado_lab C++ JSON examples have str values instead of ints, convert to int.
        Ensure values are upper case.
        """
        self.value = self.value.upper()
        if type(self.bit_index) == str:
            self.bit_index = int(self.bit_index)
        if type(self.port_index) == str:
            self.port_index = int(self.port_index)
        if not self._source_names:
            self._source_names = []
        if not self._source_value_indices:
            self._source_value_indices = []

    def update_source(self, force: bool = True) -> None:
        if self.source and not force:
            return
        self.source = " ".join(
            f"{name}<{idx}>" for name, idx in zip(self._source_names, self._source_value_indices)
        )
        # To be compatible with old C++ generated json
        self.source += " "

    def flip_one_bit_neq_to_eq(self) -> None:
        if self.op != "!=" or len(self.value) != 1:
            return
        # Have a "1=" one bit value, which can be flipped.
        self.op = "=="
        self.value = negate_bit_value(self.value)
        # Mark name, for debug printout
        self.name = "~" + self.name

    def merge_shared_ports(self, other_match) -> object:
        """
        if feasible, will merge with 'other' Match, putting merged result into this Match.
        Caller need to remove obsolete 'other'.
        Return merged Match object. None if no merge.
        """
        m1: Match = other_match
        if self.port_index != m1.port_index or self.op != "==" or m1.op != "==":
            return None

        merged_value = self.make_merged_value(self, m1)
        if not merged_value:
            return None

        merged = Match(
            self.name + "&" + m1.name,
            self.port_index,
            min(self.bit_index, m1.bit_index),
            self.op,
            merged_value,
        )

        merged._source_names = self._source_names
        merged._source_names.extend(m1._source_names)
        merged._source_value_indices = self._source_value_indices
        merged._source_value_indices.extend(m1._source_value_indices)
        return merged

    @staticmethod
    def make_merged_value(match0, match1) -> str:
        # Returns empty string, if merge was not possible.

        def merge_ch(ch0: str, ch1: str) -> str:
            if ch0 == ch1 or ch1 == "X":
                return ch0
            elif ch0 == "X":
                return ch1
            else:
                return ""

        m0: Match = match0
        m1: Match = match1
        new_bit_index = min(m0.bit_index, m1.bit_index)
        new_len = max(m0.bit_index + len(m0.value), m1.bit_index + len(m1.value)) - new_bit_index
        # Normalize values to start at the new bit_index and have same length.
        m0_value = Match.resize_value(m0.value, m0.bit_index, new_bit_index, new_len)
        m1_value = Match.resize_value(m1.value, m1.bit_index, new_bit_index, new_len)
        merged_value = [merge_ch(ch0, ch1) for ch0, ch1 in zip(m0_value, m1_value)]
        if all(merged_value):
            return "".join(merged_value)
        else:
            return ""

    @staticmethod
    def resize_value(
        mu_value: str, mu_value_bit_index: int, new_bit_index: int, new_width: int
    ) -> str:
        """
        A value is grown by filling out with don't-care 'X' in the beginning and/or the end.
        Note! In a string value the LSB is at the end of the string.

        Args:
            mu_value (str): Old value to re-sized.
            mu_value_bit_index (int): LSB bit location on port.
            new_bit_index (int): LSB bit of new value.
            new_width (int): Bit width of the new value.

        Returns: Upsized value.

        """
        if (new_bit_index > mu_value_bit_index) or (
            new_bit_index + new_width < mu_value_bit_index + len(mu_value)
        ):
            raise ValueError("Internal Error: Match unit value of the wrong length.")

        value = mu_value + "X" * (mu_value_bit_index - new_bit_index)
        value = "X" * (new_width - len(value)) + value
        return value

    def make_port_match_value(self, port_width: int) -> str:
        value = Match.resize_value(self.value, self.bit_index, 0, port_width)
        if len(value) < port_width:
            raise ValueError("Internal Error: Wrong match value length.")
        return self.op + value


class Condition:
    def __init__(self, op: str, name: str = "", matches: [Match] = None):
        self.name = name
        self.op: str = op
        self.matches: [Match] = matches if matches else []

    def __str__(self):
        return f"\nop: {self.op}\nmatches: {self.matches}"

    def merge_shared_ports(self) -> None:
        # Only allowed to merge match values when 'op' is 'and' or 'nand'.
        if self.op != "and" and self.op != "nand":
            return

        res = []
        work_list = self.matches
        while len(work_list) > 1:
            remaining = []
            match0, work_list = work_list[0], work_list[1:]
            for match2 in work_list:
                # Try merging  match value with the rest of the work list.
                merged = match0.merge_shared_ports(match2)
                if merged:
                    match0 = merged
                else:
                    # Keep match2.
                    remaining.append(match2)

            res.append(match0)
            work_list = remaining

        # work_list may still have an element.
        res.extend(work_list)
        self.matches = res


class IlaMapperEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Match):
            obj.update_source()

        if isinstance(obj, (Port, Match, Condition, IlaMapper)):
            obj_dict = obj.__dict__
            obj_dict.pop("__module__", None)
            obj_dict.pop("__class__", None)
            if isinstance(obj, Match):
                # Get rid of internal data members
                obj_dict.pop("_source_names", None)
                obj_dict.pop("_source_value_indices", None)

            return obj_dict
        return json.JSONEncoder.default(self, obj)


class IlaMapper:
    def __init__(self, ports=None, conditions=None, is_basic_capture=False):
        self.ports: [Port] = ports if ports else []
        self.conditions: [Condition] = conditions if conditions else []
        self._is_basic_capture = is_basic_capture

    def __str__(self):
        return to_json(self)

    def add_ports(self, port_width_with_match_unit_count: [(int, int)]) -> None:
        self.ports = [
            Port(index=index, width=p_width_mu_count[0], mu_count=p_width_mu_count[1])
            for index, p_width_mu_count in enumerate(port_width_with_match_unit_count)
        ]

    def add_condition(self, op: str, name: str = "") -> int:
        """
        Add new condition. Return index of condition.

        Args:
            op (): Lower case operator string, e.g.'and', 'or', 'nor', 'nand'
            name (): Empty string, or ILA core register.

        Returns: Condition index, for added item.

        """
        self.conditions.append(Condition(op, name))
        return len(self.conditions) - 1

    def add_probe_value(
        self,
        condition_index: int,
        probe_name: str,
        port_index: int,
        bit_index: int,
        op: str,
        value: str,
    ) -> None:
        upper_no_underscore_value = "".join(ch if ch != "_" else "" for ch in value.upper())
        match = Match(probe_name, port_index, bit_index, op, upper_no_underscore_value)
        cond: Condition = self.conditions[condition_index]
        cond.matches.append(match)

    def merge_shared_ports(self) -> None:
        for cond in self.conditions:
            cond.merge_shared_ports()

    def flip_one_bit_neq_to_eq(self) -> None:
        for cond in self.conditions:
            for match in cond.matches:
                match.flip_one_bit_neq_to_eq()

    def remove_dont_care_matches(self) -> None:
        for cond in self.conditions:
            cond.matches = [match for match in cond.matches if not match.is_dont_care()]

    def sort_matches(self):
        for cond in self.conditions:
            cond.matches.sort(key=Match.get_sort_key())

    def ensure_proper_types(self) -> None:
        for cond in self.conditions:
            for match in cond.matches:
                match.ensure_proper_types()

    def assign_match_source_info(self) -> None:
        tally = defaultdict(int)
        for cond in self.conditions:
            for match in cond.matches:
                count = tally[match.name]
                match._source_names.append(match.name)
                match._source_value_indices.append(count)

    def map_match_units(self) -> bool:
        """
        Returns True if trigger/capture values fit into port match units.
        """
        result = [self.map_match_unit(mu) for cond in self.conditions for mu in cond.matches]
        return all(result)

    def map_match_unit(self, match: Match) -> bool:
        if match.port_index > len(self.ports):
            raise ValueError(
                f"Internal Error: Match Unit {match.name} refers to non"
                f"-existent port index {match.port_index}"
            )
        port = self.ports[match.port_index]
        value = match.make_port_match_value(port.width)
        if value in port.mu_values:
            # Re-use actual port match unit.
            match.mu_index = port.mu_values.index(value)
        else:
            match.mu_index = len(port.mu_values)
            port.mu_values.append(value)
        # Report if we ran out of port match units.
        return match.mu_index < port.mu_count

    def report_overflow(self) -> [str]:
        def bin_to_hex_if_possible(value: str) -> str:
            if all(ch in ("0", "1") for ch in value):
                return hex(int(value, 2))
            else:
                return value

        def get_compare_values_str(matches: [Match]) -> str:
            compare_values = [
                f"\t{mm.name} {mm.op} {bin_to_hex_if_possible(mm.value)}" for mm in matches
            ]
            return "\n".join(compare_values)

        # Create {port: [match]} map
        port_to_map = defaultdict(list)
        for cond in self.conditions:
            for match in cond.matches:
                port_to_map[match.port_index].append(match)

        overflows = []
        for p_index, port in enumerate(self.ports):
            if port.mu_count < len(port_to_map[p_index]):
                msg = get_compare_values_str(port_to_map[p_index])
                overflows.append(msg)
        return overflows

    __CONDITION_MAPPING_OP = {
        ILATriggerCondition.AND.name.lower(): "==",
        ILATriggerCondition.NAND.name.lower(): "!=",
        ILATriggerCondition.OR.name.lower(): "||",
        # 'nor' -> 'and' after deMorgan
        ILATriggerCondition.NOR.name.lower(): "==",
    }

    @staticmethod
    def get_unused_tc_value(match_unit_count: int) -> str:
        return "==" + ("x" * match_unit_count)

    def create_test_get_mu_index_function(self) -> (int, Callable[[int, int], int]):
        """
        Create function, based on self.ports.
        Intended to be used only in tests.
        Function assumes that match units are paired with Ports in port index order.

        Returns: Tuple( match_unit_count,
                        Function which can be used in test examples when calling "get_mapping()")
        """
        pp_pmu_list = [
            (pp.index, pmu_index) for pp in self.ports for pmu_index in range(pp.mu_count)
        ]
        mu_index_by_port_index_and_mu_index_with_port = {
            pp_pmu: mu_index for mu_index, pp_pmu in enumerate(pp_pmu_list)
        }

        def get_mu_index_fn(port_index: int, mu_index_within_port: int) -> int:
            return mu_index_by_port_index_and_mu_index_with_port.get(
                (port_index, mu_index_within_port), -1
            )

        return len(pp_pmu_list), get_mu_index_fn

    def get_reg_mu_mapping(
        self, mu_count: int, get_mu_index: Callable[[int, int], int]
    ) -> {str: str}:
        """

        Args:
            mu_count: Total ILA match unit count,
            get_mu_index(Callable): A function given (port_index, match_index_within_port)
                returns the ILA match unit index

        Returns: Dict {"reg_name":match value} for Trigger conditions and match units.
        """
        res = {}

        # TCs (trigger conditions)
        for c_index, condition in enumerate(self.conditions):
            mu_used = [False] * mu_count
            for match in condition.matches:
                if match.mu_index >= 0:
                    mu_used[get_mu_index(match.port_index, match.mu_index)] = True
            # LSB should be at end for value.
            mu_used.reverse()
            if condition.op == "nor":
                # Nor handled by deMorgan. Invert inputs using '0'. nor -> and
                cmp_value = ["0" if used else "X" for used in mu_used]
            else:
                cmp_value = ["1" if used else "X" for used in mu_used]
            if condition.name:
                condition_name = condition.name
            else:
                condition_name = "sqc" if self._is_basic_capture else "tc" + str(c_index)
            res[condition_name] = IlaMapper.__CONDITION_MAPPING_OP[condition.op] + "".join(
                cmp_value
            )

        # Match Units
        for p_index, port in enumerate(self.ports):
            for mu_index_for_port, mu_val in enumerate(port.mu_values):
                mu_index = get_mu_index(p_index, mu_index_for_port)
                res["mu" + str(mu_index)] = mu_val

        return res

    def map(self, skip_overflow_messages=True) -> (bool, Optional[str]):
        """
        Map match values onto port match units.

        Args:
            skip_overflow_messages (bool): If True,

        Returns: A tuple - all_mapped_status, None or List of overflow messages.

        """
        self.ensure_proper_types()
        self.assign_match_source_info()
        self.sort_matches()
        self.remove_dont_care_matches()
        self.flip_one_bit_neq_to_eq()
        self.merge_shared_ports()
        all_mapped = self.map_match_units()
        overflow_msg = None
        if not all_mapped and not skip_overflow_messages:
            overflow_msg = self.report_overflow()
        return all_mapped, overflow_msg


def to_json(ila_mapper: IlaMapper, skip_unused_ports=True) -> str:
    if skip_unused_ports:
        ports = [port for port in ila_mapper.ports if port.mu_values]
        ila_mapper1 = IlaMapper(ports, ila_mapper.conditions)
    else:
        ila_mapper1 = ila_mapper
    res = json.dumps(ila_mapper1, cls=IlaMapperEncoder, indent=2)
    return res


def from_json(j_str: str) -> IlaMapper:
    def _decode_condition(cond: dict) -> Condition:
        matches = cond.get("matches", None)
        if matches and type(matches) == list:
            cond["matches"] = [Match(**mm) for mm in matches]
        return Condition(**cond)

    data_tree = json.loads(j_str)
    # Re-creating list of dataclass Port.
    ports = data_tree.get("ports", None)
    if ports and type(ports) == list:
        ports = [Port(index, **pp) for index, pp in enumerate(ports)]
    conditions = data_tree.get("conditions", None)
    # Re-creating 'condition' list.
    if conditions and type(conditions) == list:
        conditions = [_decode_condition(cond) for cond in conditions]
    res = IlaMapper(ports, conditions)
    return res


# Todo: Change MapPortSeq to PortSegment? or PortRange
class MapPortSeq(NamedTuple):
    """A port bit-range."""

    port_idx: int
    high_idx: int
    low_idx: int

    def __str__(self):
        if self.high_idx == self.low_idx:
            return f"port{self.port_idx}[{self.high_idx}]"
        else:
            return f"port{self.port_idx}[{self.high_idx}:{self.low_idx}]"

    @staticmethod
    def to_str(seqs: []) -> str:
        return " ".join(s.__str__() for s in seqs)


_map_re = re.compile(r"(\d+)(\[(\d+)(:(\d+))?\])?")


def port_map_str_to_port_seqs(
    name: str, map_str: str, ports: Optional[List[ILAPort]] = None
) -> [MapPortSeq]:
    """
        If ports is None, some checks are turned off.

    port<int>
    port<int>[<int>]
    port<int>[<int>:<int>]
    """

    def _to_int(s: str):
        return int(s) if s else None

    def _parse_map_item(item: str) -> Tuple[int, int, int]:
        """
        If ports is None, some checks are turned off.
        Return port_idx, high_bit_idx, low_bit_idx.
        """
        if item.startswith("port"):
            s = item[len("port") :]
        elif item.startswith("probe"):
            s = item[len("probe") :]
        else:
            raise ValueError(f'Probe "{name}" map item "{item}" does not start with prefix "port".')

        match = _map_re.match(s)
        if not match:
            raise ValueError(f'Probe "{name}" map item "{item}" has incorrect syntax.')

        port_str, _, left_str, __, right_str = match.groups()
        port_idx, left, right = int(port_str), _to_int(left_str), _to_int(right_str)
        if ports:
            if (port_idx < 0) or (port_idx >= len(ports)):
                raise ValueError(
                    f'Probe "{name}" map item "{item}" has invalid port index "{port_idx}"'
                    f" valid values are 0 to {len(ports)}."
                )
        if right is None:
            # port<int>[<int>] syntax used, if no "right index"
            high, low = left, left
        else:
            high, low = left, right

        port_width = None
        if ports:
            port_width = ports[port_idx]["bit_width"]
            if low is None and high is None:
                # port < int > syntax used. No range specified
                if port_width == 1:
                    high, low = 0, 0
                else:
                    raise ValueError(
                        f'Probe "{name}" map item "{item}" needs explict range '
                        f'"[<high>:<low>]" since port bit width is larger than one.'
                    )

        if low < 0:
            raise ValueError(
                f'Probe "{name}" map item "{item}" has bit range index less than zero.'
            )

        if high < low:
            raise ValueError(
                f'Probe "{name}" map item "{item}" high range index "{high}" '
                f'is less than low bit index "{low}".'
            )

        if port_width is not None and (port_width <= high):
            raise ValueError(
                f'Probe "{name}" map item "{item}" high range index "{high}" '
                f'is invalid. Port has "{port_width}" bit(s).'
            )
        return MapPortSeq(port_idx, high, low)

    items = map_str.lower().split()
    map_seqs = [_parse_map_item(item) for item in items]
    return map_seqs


def negate_bit_value(bit_ch: str) -> str:
    negate_dict = {
        "0": "1",
        "1": "0",
        "X": "X",
        "R": "L",
        "F": "S",
        "T": "N",
        "B": "N",
        "N": "T",
        "L": "R",
        "S": "F",
    }
    return negate_dict.get(bit_ch.upper(), "X")
