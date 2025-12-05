# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2025, Advanced Micro Devices, Inc.
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
import json
import sys
import csv
import zipfile
import re
from chipscopy.api.ila.ila_protocol_processing import Rule, TransactionSpec
from abc import abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, asdict, field
from datetime import datetime
from io import TextIOBase, BytesIO, StringIO
from itertools import islice
from pprint import pformat
from typing import Generator, Dict, List, Union, Optional, Sequence, Any, Tuple, Iterable
from zipfile import ZipFile
from enum import Enum
from chipscopy.api.ila import ILABitRange, ILAProbeRadix
import chipscopy
import os
from chipscopy.shared.ila_util import bin_reversed_to_hex_values
from chipscopy.utils import Enum2StrEncoder


@dataclass
class ILAWaveformProbe:
    """Probe location in a data sample."""

    name: str
    """Name of probe."""
    map: str
    """Location string"""
    map_range: List[ILABitRange]
    """List of bit ranges. See :class:`~chipscopy.api.ila.ILABitRange`"""
    is_bus: bool
    """True for bus probes"""
    bus_left_index: Optional[int] = None
    """ Bus left index. E.g. 5 in probe ``counter[5:0]``"""
    bus_right_index: Optional[int] = None
    """Bus right index. E.g. 0 in probe ``counter[5:0]``"""
    display_radix: ILAProbeRadix = ILAProbeRadix.HEX
    """Display radix, when exporting waveform data. Default is ILAProbeRadix.HEX"""
    enum_def: Optional[enum.EnumMeta] = None
    """Enum class defining {name:int} enum values, for this probe."""

    def length(self) -> int:
        return sum(mr.length for mr in self.map_range)

    def bus_range_str(self) -> str:
        if not self.is_bus:
            res = ""
        elif self.bus_left_index == self.bus_right_index:
            res = f"[{self.bus_left_index}]"
        else:
            res = f"[{self.bus_left_index}:{self.bus_right_index}]"
        return res


@dataclass
class ProbeGroup:
    """Represents a group of related probes in the waveform."""

    name: str
    probes: List[str] = field(default_factory=list)
    description: Optional[str] = None
    is_expanded: bool = True  # For UI state
    color: Optional[str] = None  # For visual grouping
    rules: List["Rule"] = field(default_factory=list)
    rule_results: Dict[str, Dict[str, any]] = field(default_factory=dict)  # Store results
    enum_mappings: Dict[str, int] = None
    channel_name: str = None

    def add_probe(self, probe_name: str) -> None:
        """Add a probe to this group."""
        if probe_name not in self.probes:
            self.probes.append(probe_name)

    def remove_probe(self, probe_name: str) -> None:
        """Remove a probe from this group."""
        if probe_name in self.probes:
            self.probes.remove(probe_name)

    def add_rule(self, rule: "Rule") -> None:
        """Add a rule to this probe group."""
        self.rules.append(rule)

    def write_enum_mappings_to_text_file(
        self, filename: str, enum_mappings: Dict[str, Dict[str, int]]
    ):
        """
        Write enum mappings to a simple text file.

        Args:
            filename: Output filename
            enum_mappings: Dictionary of signal names to their enum mappings
        """
        output_lines = []
        if enum_mappings is None:
            return
        # Sort by value
        sorted_mapping = sorted(enum_mappings.items(), key=lambda x: x[1])

        # Get bit width
        max_value = max(enum_mappings.values()) if enum_mappings else 0
        bit_width = max_value.bit_length() if max_value > 0 else 1

        for label, value in sorted_mapping:
            binary = format(value, f"0{bit_width}b")
            if label == "":
                display_label = "NOEVENTS"
            else:
                display_label = f"{label}"
            output_lines.append(f"{binary} {display_label}")

        with open(filename, "w") as f:
            f.write("\n".join(output_lines))

        print(f"Enum mappings written to {filename}")

    def calculate_values(self, waveform: "ILAWaveform", slot: int = 0) -> None:
        """
        Apply rules specific to this probe group and create interval signals.
        """
        if not self.rules:
            return

        refactor_rules = False
        if waveform.num_slots > 1:
            refactor_rules = True
        all_data = waveform.get_data()

        for rule in self.rules:
            # Create signal mapping only from probes in this group
            signal_mapping = {}

            for signal in rule.signals:
                # Find matching probes within this group's probes
                tsignal = signal
                if refactor_rules:
                    tsignal = f"SLOT_{slot}_AXI/{signal}"
                matching_probes = []
                for probe_name in self.probes:
                    if probe_name.upper() == tsignal.upper():
                        matching_probes.append(probe_name)

                if len(matching_probes) == 1:
                    signal_mapping[signal] = matching_probes[0]
                elif len(matching_probes) > 1:
                    print(
                        f"Warning: Multiple probes in group '{self.name}' match '{signal}': {matching_probes}"
                    )
                    signal_mapping[signal] = matching_probes[0]
                else:
                    print(f"Warning: No probe in group '{self.name}' found for signal '{signal}'")
                    break

            # Skip if we couldn't find all required signals
            if len(signal_mapping) != len(rule.signals):
                continue

            # Get signal data
            signal_data = {
                simple_name: all_data[full_name]
                for simple_name, full_name in signal_mapping.items()
            }

            # Create context with helper methods
            class Context:
                def rising_edge(self, signal, idx):
                    if idx == 0:
                        return False
                    data = signal_data[signal]
                    return data[idx - 1] == 0 and data[idx] == 1

                def both_asserted(self, sig1, sig2, idx):
                    return signal_data[sig1][idx] == 1 and signal_data[sig2][idx] == 1

                def signal(self, signal, idx):
                    return signal_data[signal][idx]

            context = Context()

            # Build hits list
            hits = []
            for idx in range(waveform.sample_count):
                try:
                    hits.append(rule.applies(context, idx))
                except Exception as e:
                    print(
                        f"Error applying rule '{rule.name}' at index {idx} in group '{self.name}': {e}"
                    )
                    hits.append(False)

            # Find intervals
            intervals = []
            start = None
            for idx, fire in enumerate(hits):
                if fire and start is None:
                    start = idx
                elif not fire and start is not None:
                    intervals.append((start, idx - 1))
                    start = None
            if start is not None:
                intervals.append((start, waveform.sample_count - 1))
            # Create manual interval signal for this rule
            # Store results instead of creating signals
            self.rule_results[rule.name] = {
                "hits": hits,  # Boolean array of where rule fires
                "intervals": intervals,  # List of (start, end) tuples
                "signal_mapping": signal_mapping,  # Which signals were used
                "hit_count": sum(hits),  # Total number of hits
                "hit_indices": [i for i, h in enumerate(hits) if h],  # Indices where rule fired
            }

    def get_rule_hits(self, rule_name: str) -> List[bool]:
        """Get the hit array for a specific rule."""
        if rule_name in self.rule_results:
            return self.rule_results[rule_name]["hits"]
        return []

    def get_rule_intervals(self, rule_name: str) -> List["Tuple"]:
        """Get the intervals where a specific rule fired."""
        if rule_name in self.rule_results:
            return self.rule_results[rule_name]["intervals"]
        return []

    def create_interval_signals(
        self, waveform: "ILAWaveform", rule_names: List[str] = None, slot: int = 0
    ):
        """Create a single enum signal for this group combining all rules."""
        """Create a single combined enum signal for all rules in this probe group."""
        # Get rule names from rule_results if not provided
        if rule_names is None:
            rule_names = list(self.rule_results.keys())

        rules_to_process = rule_names

        if not rules_to_process:
            return

        # Build enum mapping: each rule gets a unique bit
        # Example: rule1=0b01, rule2=0b10, both=0b11, neither=0b00
        enum_mapping = {"-": 0}  # Empty string for no rules active
        rule_bit_map = {}

        # Assign each rule a unique bit position
        for i, rule_name in enumerate(rules_to_process):
            if rule_name in self.rule_results:
                bit_value = 1 << i  # 2^i
                rule_bit_map[rule_name] = bit_value
                enum_mapping[rule_name] = bit_value

        # Generate all possible combinations
        num_rules = len(rule_bit_map)
        for combo in range(1, 2**num_rules):  # Skip 0 (empty)
            # Build label for this combination
            active_rules = []
            for rule_name, bit_value in rule_bit_map.items():
                if combo & bit_value:
                    active_rules.append(rule_name)

            if len(active_rules) > 1:
                # Multiple rules active
                label = " & ".join(active_rules)
                enum_mapping[label] = combo

        # Create values array for each sample
        values = [""] * waveform.sample_count
        # Move this to gtkw in export waveform

        # For each sample, determine which rules are active
        for idx in range(waveform.sample_count):
            active_value = 0
            active_rules = []

            for rule_name in rules_to_process:
                if rule_name not in self.rule_results:
                    continue

                # Check if this rule fires at this index
                hits = self.rule_results[rule_name]["hits"]
                if idx < len(hits) and hits[idx]:
                    active_value |= rule_bit_map[rule_name]
                    active_rules.append(rule_name)

            # Set the appropriate label
            if active_value == 0:
                values[idx] = "-"
            elif len(active_rules) == 1:
                values[idx] = active_rules[0]
            else:
                values[idx] = " & ".join(active_rules)

        # Create the combined signal
        if waveform.num_slots > 1:
            signal_name = f"SLOT_{slot}_{self.name}_Events"
        else:
            signal_name = f"{self.name}_Events"
        self.channel_name = signal_name
        self.enum_mappings = enum_mapping
        waveform.append_manual_enum_signal(signal_name, values, enum_mapping)

    def __len__(self) -> int:
        return len(self.probes)


@dataclass
class Transaction:
    kind: str  # "read" | "write"
    id: Optional[int]  # ARID/AWID (0 if not present)
    addr: Optional[int]  # ARADDR/AWADDR (int if available)
    start_idx: int
    probes: Dict[str, Any] = field(default_factory=dict)  # captured open fields
    slot: int = 0
    end_idx: Optional[int] = None
    resp: Optional[int] = None
    channel_name: Optional[str] = None  # e.g. "AXI_ID_2_Write
    enum: Dict[int, str] = field(default_factory=lambda: {0: "-", 1: "ACTIVE"})
    meta: Dict[str, Any] = field(default_factory=defaultdict)


@dataclass
class TopTransactionAssembler:
    specs: List["TransactionSpec"]
    slot_indices: Optional[List[int]] = None
    name_prefix: str = "AXI"

    # per-slot assemblers and results
    assemblers: List["SimpleTransactionAssembler"] = field(default_factory=list)
    transactions_by_slot: Dict[int, List["Transaction"]] = field(default_factory=dict)

    def prepare(self, waveform: "ILAWaveform"):
        # Determine slots from waveform if not provided
        waveform.transactionAssembler = self
        if self.slot_indices is None:
            num_slots = getattr(waveform, "num_slots", 1) or 1
            self.slot_indices = list(range(num_slots))

        # Create per-slot assemblers once
        if not self.assemblers:
            for s in self.slot_indices:
                self.assemblers.append(SimpleTransactionAssembler(self.specs, slot=s))

    def calculate(self, waveform: "ILAWaveform") -> Dict[int, List["Transaction"]]:
        self.prepare(waveform)
        self.transactions_by_slot.clear()

        for asm in self.assemblers:
            txns = asm.calculate_values(waveform)
            self.transactions_by_slot[asm.slot] = txns

        return self.transactions_by_slot

    def append_lanes(self, waveform: "ILAWaveform", separate_by_kind: bool = True):
        # Append per-slot lanes to the waveform
        for asm in self.assemblers:
            # Set a per-slot prefix to avoid name collisions between slots
            prefix = f"{self.name_prefix}_SLOT{asm.slot}"
            asm.append_per_id_binary_lanes(waveform, name_prefix=prefix)

    def write_gtkw_translate(
        self, vcd_path: str, out_dir: str, separate_by_kind: bool = True
    ) -> List[str]:
        """Write per-slot translate tables + .gtkw files, returns list of file paths."""
        written = []
        os.makedirs(out_dir, exist_ok=True)
        for asm in self.assemblers:
            prefix = f"{self.name_prefix}_SLOT{asm.slot}"
            gtkw = asm.write_gtkw_with_translate(
                out_dir=out_dir,
                name_prefix=prefix,
            )
            written.append(gtkw)
        return written

    def all_transactions(self) -> List["Transaction"]:
        # Flatten across slots if needed
        result = []
        for _, lst in sorted(self.transactions_by_slot.items()):
            result.extend(lst)
        return result

    def get_transactions_by_slot(self) -> Dict[int, List["Transaction"]]:
        # Flatten across slots if needed
        return self.transactions_by_slot


class SimpleTransactionAssembler:
    """
    Evaluates each TransactionSpec over the waveform and pairs opens->closes
    using a per-ID FIFO. Ignores counters/overflows for now.
    """

    def __init__(self, specs: List[TransactionSpec], slot: int = 0):
        self.specs = specs
        self.transactions: List[Transaction] = []
        self.slot = slot

    def _bind_sigmap(self, all_data: Dict[str, List], names: List[str]) -> Optional[Dict[str, str]]:
        # Case-insensitive exact-key binding: "ARID" -> actual key in all_data
        sigmap: Dict[str, str] = {}
        for n in names:
            # gather candidates
            cands = [k for k in all_data.keys() if k.upper() == n.upper()]
            if not cands:
                return None
            sigmap[n] = cands[0]
        return sigmap

    @staticmethod
    def _to_int(val) -> Optional[int]:
        if val is None:
            return None
        if isinstance(val, str):
            try:
                return int(val, 16) if val.lower().startswith("0x") else int(val)
            except Exception:
                return None
        try:
            return int(val)
        except Exception:
            return None

    def append_per_id_binary_lanes(
        self,
        waveform: "ILAWaveform",
        name_prefix: str = None,
    ):
        """
        For each ID, create a 0/1 lane indicating transaction activity over time.
        If separate_by_kind=True, create distinct lanes per (ID, kind).
        """
        if not self.transactions:
            return
        n = waveform.sample_count
        base_name = name_prefix or "AXI"

        # Collect IDs (and kinds if requested)
        groups = {}
        for t in self.transactions:
            if t.end_idx is None:
                continue
            key = (t.id or 0, t.kind)
            groups.setdefault(key, []).append(t)  # Enum mapping for binary 0/1

        for (cur_id, cur_kind), txns in groups.items():
            # Sort by start time, then end time for stability
            txns.sort(
                key=lambda x: (x.start_idx, x.end_idx if x.end_idx is not None else x.start_idx)
            )

            # Greedy packing into non-overlapping lanes
            lane_last_end = []  # last end index for each lane
            lanes = []  # list of lists of transactions per lane

            for t in txns:
                placed = False
                for li, last_end in enumerate(lane_last_end):
                    # Place in the first lane that doesn't overlap (strictly after last end)
                    if t.start_idx > last_end:
                        lanes[li].append(t)
                        lane_last_end[li] = t.end_idx
                        placed = True
                        break
                if not placed:
                    lanes.append([t])
                    lane_last_end.append(t.end_idx)

            # Emit one enum lane per lane index
            for li, lane_txns in enumerate(lanes):
                lane_name = f"{base_name}_ID{cur_id}_{cur_kind.capitalize()}_{li}"
                values = ["-"] * n
                enum_map = {"-": 0}
                next_code = 1

                for t in lane_txns:
                    addr_str = f"0x{t.addr:X}" if isinstance(t.addr, int) else "N/A"
                    resp_str = str(t.resp) if t.resp is not None else "N/A"
                    label = f"{t.kind.upper()} ID={t.id} ADDR={addr_str} RESP={resp_str}"

                    if label not in enum_map:
                        enum_map[label] = next_code
                        next_code += 1

                    # Optionally attach mapping and lane name back to the txn
                    t.enum = {code: lab for lab, code in enum_map.items()}
                    t.channel_name = lane_name

                    s = max(0, t.start_idx)
                    e = min(n - 1, t.end_idx)
                    for i in range(s, e + 1):
                        values[i] = label

                waveform.append_manual_enum_signal(lane_name, values, enum_map)

    def calculate_values(self, waveform: "ILAWaveform") -> List[Transaction]:
        from collections import defaultdict, deque

        # if waveform.num_slots >
        #
        # else:
        pgs = (
            waveform.probe_groups[self.slot] if waveform.num_slots > 1 else waveform.probe_groups[0]
        )
        probes = []
        # Iterate through all groups in that slot
        for group_name, probe_group in pgs.items():
            # process each probe_group
            probes.extend(probe_group.probes)

        data = waveform.get_data(probes)
        N = waveform.sample_count
        txns_all: List[Transaction] = []

        def bind(names: list[str]) -> dict[str, str] | None:
            m = {}
            for n in names:
                if waveform.num_slots > 1:
                    pattern = re.compile(rf"(?<=/|_){re.escape(n)}", re.IGNORECASE)
                    ks = [k for k in data if pattern.search(k)]
                else:
                    ks = [k for k in data if k.upper() == n.upper()]
                if not ks:
                    continue
                m[n] = ks[0]
            if len(m) == 0:
                return None
            return m

        def make_ctx(sigmap: dict[str, str]):
            class Ctx:
                def rising_edge(self, s, i):
                    if i == 0:
                        return False
                    if s not in sigmap:
                        return False
                    d = data[sigmap[s]]
                    return d[i - 1] == 0 and d[i] == 1

                def both_asserted(self, a, b, i):
                    if a not in sigmap or b not in sigmap:
                        return False
                    return data[sigmap[a]][i] == 1 and data[sigmap[b]][i] == 1

                def signal(self, s, i):
                    key = sigmap.get(s)
                    if key is None:
                        return None
                    values = data.get(key)
                    if values is None or i < 0 or i >= len(values):
                        return None
                    return values[i]

            return Ctx()

        def to_int(v):
            if v is None:
                return None
            if isinstance(v, str):
                v = v.strip()
                if v.lower().startswith("0x"):
                    try:
                        return int(v, 16)
                    except:
                        return None
            try:
                return int(v)
            except:
                return None

        for spec in self.specs:
            open_cnt_name = "AR_CNT" if spec.txn_type == "read" else "AW_CNT"
            close_cnt_name = "R_CNT" if spec.txn_type == "read" else "B_CNT"
            overflowed = False
            # length
            next_ticket: Dict[int, int] = defaultdict(int)

            pending_by_id_ticket: Dict[int, Dict[int, Transaction]] = defaultdict(dict)

            # Build signal maps for open/close including fields you’ll read

            open_need = list(
                {
                    *spec.open_rule.signals,
                    spec.open_addr_field,
                    *spec.open_fields,
                    open_cnt_name,
                }
            )
            if spec.open_id_field:
                open_need.append(spec.open_id_field)
            # Everything the close rule needs, plus fields we want at close (ID + resp if present)
            close_need = list(
                {
                    *spec.close_rule.signals,
                    spec.close_resp_field,
                    *spec.close_fields,
                    close_cnt_name,
                }
            )
            if spec.close_id_field:
                close_need.append(spec.close_id_field)
            open_map = bind(open_need)
            close_map = bind(close_need)
            if open_map is None or close_map is None:
                continue

            open_ctx = make_ctx(open_map)
            close_ctx = make_ctx(close_map)
            has_open_cnt = open_cnt_name in open_map
            has_close_cnt = close_cnt_name in close_map

            def derive_overflow_thresholds(width: int):
                return (1 << (width - 1)), (1 << width) - 1

            # Per-ID FIFO for this spec

            pending: dict[int, deque[Transaction]] = defaultdict(deque)
            completed: List[Transaction] = []

            for i in range(N):
                # Open: if rule fires, enqueue a Transaction with start_idx and fields
                if spec.open_rule.applies(open_ctx, i):
                    tid = to_int(open_ctx.signal(spec.open_id_field, i)) or 0
                    addr = to_int(open_ctx.signal(spec.open_addr_field, i))
                    resp = (
                        (to_int(close_ctx.signal(spec.close_resp_field, i)) == 0)
                        if spec.close_resp_field
                        else None
                    )
                    ticket = next_ticket[tid]
                    pending_by_id_ticket[tid][ticket] = Transaction(
                        kind=spec.txn_type, id=tid, addr=addr, start_idx=i
                    )
                    next_ticket[tid] += 1
                    pending[tid].append(
                        Transaction(kind=spec.txn_type, id=tid, addr=addr, start_idx=i)
                    )

                # Close: if rule fires, pop from that ID’s queue and finalize
                if spec.close_rule.applies(close_ctx, i):
                    tid = to_int(close_ctx.signal(spec.close_id_field, i)) or 0
                    resp = (
                        (to_int(close_ctx.signal(spec.close_resp_field, i)) == 0)
                        if spec.close_resp_field
                        else None
                    )

                    # I think 00 means good response.
                    t = None
                    if has_close_cnt:
                        cc = to_int(close_ctx.signal(close_cnt_name, i))
                        if cc is not None:
                            # Oldest outstanding ticket (the one completing now)
                            ticket_to_close = next_ticket[tid] - cc
                            t = pending_by_id_ticket[tid].pop(ticket_to_close, None)

                    # Fallback to FIFO if counters not present or lookup failed
                    if t is None:
                        dq = pending[tid]
                        if dq:
                            t = dq.popleft()

                    if t:
                        t.end_idx = i
                        t.resp = resp
                        t.slot = self.slot
                        t.probes = (open_map or {}) | (close_map or {})
                        completed.append(t)
                    else:
                        # Orphan close; ignore or record a violation if desired
                        pass

            txns_all.extend(completed)
        self.transactions = txns_all
        #  self.append_per_id_binary_lanes(waveform, "SLOT_" + str(self.slot) if waveform.num_slots > 1 else "AXI")
        return txns_all

    def write_gtkw_with_translate(
        self,
        out_dir: str = ".",
        name_prefix: str = "AXI",
    ) -> str:
        """
        Write translate tables (.tt) and a .gtkw savefile for GTKWave that
        pipes each lane signal through its translate table.

        Args:
          transactions: list of Transaction; defaults to self.transactions.
          vcd_path: path to the VCD that contains the lane signals.
          out_dir: directory to write .tt files and the .gtkw file.
          name_prefix: lane name prefix (e.g., "AXI4MM" or "AXI4MM_SLOT2").
          separate_by_kind: if True and channel_name missing, synthesize lanes per (ID, kind).
          gtkw_path: optional explicit output path for the .gtkw; defaults to "<out_dir>/<name_prefix>.gtkw".
          hierarchy_prefix: optional VCD hierarchy prefix (e.g., "top/dut/") to prepend to lane names in .gtkw.

        Returns:
          Absolute path to the generated .gtkw file.
        """

        lanes: Dict[str, Dict[int, str]] = {}

        # Helper to merge a single transaction into the lanes dict
        def _merge_txn_lane(t):
            lane_name = getattr(t, "channel_name", None)
            enum_map = getattr(t, "enum", None)  # expected code -> label
            if not lane_name or not enum_map:
                return
            lane_map = lanes.setdefault(lane_name, {})
            # Merge codes; keep first-seen label for determinism
            for code, label in enum_map.items():
                lane_map.setdefault(code, label)

        # 1) Flatten transactions across slots (or fall back to asm.transactions)

        for t in self.transactions:
            _merge_txn_lane(t)

        # 2) Normalize and attach to target_columns once per lane
        if not lanes:
            return []

            # 2) Write one .tt per lane in the desired format
        written_files: List[str] = []

        for lane_name, code_to_label in sorted(lanes.items()):
            # Ensure code 0 exists for idle
            if 0 not in code_to_label:
                code_to_label[0] = "-"

            # Sort by code (value) ascending
            items = sorted(code_to_label.items(), key=lambda kv: kv[0])

            # Compute bit width from the max code
            max_code = items[-1][0] if items else 0
            bit_width = max_code.bit_length() if max_code > 0 else 1

            # Build lines in the requested format
            output_lines: List[str] = []
            for code, label in items:
                binary = format(code, f"0{bit_width}b")
                # Use "'<label>" and map empty to NOEVENTS (or '-' if you prefer strictly '-')
                display_label = f"'{label if label != '' else '-'}"
                output_lines.append(f"{binary} {display_label}")

            # File name per lane (change extension if you prefer .gtkw for a GTKW savefile)
            tt_path = os.path.abspath(os.path.join(out_dir, f"{lane_name}.gtkw"))
            with open(tt_path, "w") as f:
                f.write("\n".join(output_lines))

            written_files.append(tt_path)

        return written_files


@dataclass
class ILAWaveform:
    """Waveform data, with data probe information."""

    width: int
    """Sample bit width."""
    sample_count: int
    """Number of data samples."""
    trigger_position: List[int]
    """Trigger position index, for each data window."""
    window_size: int
    """Number of samples in a window."""

    probes: Dict[str, ILAWaveformProbe]
    """Dict of {probe name, waveform probe}   See :class:`ILAWaveformProbe`"""
    data: bytearray
    """ 
    Waveform data.
    Samples are aligned on byte boundary. 

    This formula can be used to read a bit from the data:
    ::

        bytes_per_sample = len(data) // sample_count

        def get_bit_value(data: bytearray, bytes_per_sample: int,
                          sample_index: int, data_bit_index: int) -> bool:
            byte_value = data[sample_index * bytes_per_sample + data_bit_index // 8]
            mask = 1 << (data_bit_index & 0x7)
            return (byte_value & mask) != 0

    """
    gap_index: Optional[int] = None

    """
    None or 0, if the waveform has no gaps. 
    If the value is >0, one sample bit is reserved to indicate which samples are gaps,
    i.e. the samples with unknown values. 'gap_index' gives the bit location within the sample data.
    """
    probe_groups: List[Dict[str, ProbeGroup]] = field(default_factory=list)
    transactionAssembler: Optional[TopTransactionAssembler] = None
    num_slots: int = 1

    def bytes_per_sample(self) -> int:
        # CR-1244881 - partial window captures are not framed correctly.
        # Changed so that all windows (partial or full) use the full window size
        # when calculating the offset for probes in a buffer. The ILA core
        # uploads an entire buffer regardless of partial of full window, so
        # alignment does not change for the last partial.
        #     old_result = len(self.data) // self.sample_count
        assert len(self.trigger_position) > 0
        assert self.window_size > 0
        result = len(self.data) // (len(self.trigger_position) * self.window_size)
        return result

    def _leaf_name(self, name: str) -> str:
        # Safely extract the last path segment and uppercase it for matching
        return name.split("/")[-1].upper()

    def _match_prefix(self, leaf: str, prefixes: Sequence[str]) -> Optional[str]:
        leaf = leaf.upper()
        for pfx in prefixes:
            if leaf.startswith(pfx.upper()):
                return pfx  # group name == prefix
        return None

    def _extract_slot_id(self, probe_name: str) -> Optional[int]:
        """
        Extract slot ID from probe name of the form:
          SLOT_<n>_.../...
        Returns the integer slot id if found, else None.
        """
        # Example: "SLOT_4_AXI_AWVALID" -> slot 4
        if "cnt" in probe_name.lower():
            m = re.search(r"SLOT_(\d+)", probe_name.upper())
        else:
            m = re.search(r"SLOT_(\d+)", probe_name)
        return int(m.group(1)) if m else None

    def _create_probe_groups(
        self,
        prefixes: Optional[Sequence[str]] = None,
        rules: Optional[List["Rule"]] = None,
        descriptions: Optional[Dict[str, str]] = None,
        create_misc_group: bool = False,
        misc_group_name: str = "MISC",
        slot: int = 0,
    ) -> Dict[str, "ProbeGroup"]:
        """
        Create probe groups based on a list of signal name prefixes for a specific slot.
        Each prefix becomes a group. The first matching prefix (by list order) wins.

        If self.num_slots > 1, only probes whose hierarchical name indicates the
        specified slot (e.g., 'SLOT_<slot>_.../LEAF') are included.

        Args:
            prefixes: List/sequence of prefixes, e.g., ["AW", "W", "B", "AR", "R"].
                      If None, defaults to AXI channels.
            rules: Optional list of Rule objects; assigned by the prefix match of the
                   rule's first signal. Rules are included only if their first signal
                   is from the specified slot.
            descriptions: Optional mapping of group name -> description string.
            create_misc_group: If True, unmatched signals/rules are placed in a MISC group.
            misc_group_name: Name for the MISC group.
            slot: Slot index to build groups for.

        Returns:
            Dictionary of non-empty ProbeGroup objects keyed by group name for the given slot.
        """
        # Default to AXI channel-style prefixes
        if prefixes is None:
            prefixes = ["AW", "W", "B", "AR", "R"]

        # Initialize groups (group name == prefix)
        groups: Dict[str, ProbeGroup] = {}
        for pfx in prefixes:
            desc = (descriptions or {}).get(pfx, f"{pfx} Group")
            groups[pfx] = ProbeGroup(pfx, description=desc)

        # Populate groups with probes for the specified slot
        for probe_name in self.probes.keys():
            # If multiple slots exist, filter probes by the requested slot
            # Use leaf name for prefix matching (e.g., "AWVALID")

            if self.num_slots > 1 and self._extract_slot_id(probe_name) != slot:
                continue

            leaf = self._leaf_name(probe_name)
            if "cnt" in probe_name.lower():
                parts = leaf.split("_")
                leaf = "_".join(parts[-2:])
            else:
                leaf = leaf.rsplit("_", 1)[-1]
            group_key = self._match_prefix(leaf, prefixes)
            # Example: "SLOT_4_AXI_AWVALID" -> slot 4

            if group_key is not None:
                groups[group_key].add_probe(probe_name)

        # Attach rules, if any (only rules whose first signal is in this slot)
        if rules:
            for rule in rules:
                group_key = None
                if getattr(rule, "signals", None):
                    first_signal = rule.signals[0]
                    first_signal_leaf = self._leaf_name(first_signal)
                    group_key = self._match_prefix(first_signal_leaf, prefixes)

                if group_key is not None and group_key in groups:
                    groups[group_key].add_rule(rule)

        # Build result with only non-empty groups
        result: Dict[str, ProbeGroup] = {
            name: group for name, group in groups.items() if len(group) > 0
        }

        # Calculate values for groups that have rules
        for group in result.values():
            if getattr(group, "rules", None) and len(group.rules) > 0:
                group.calculate_values(self, slot=slot)
        # breakpoint()
        return result

    def create_protocol_waveforms(
        self, rules: Dict[str, List[Rule]], probe_prefixes: List[str] = None
    ) -> None:
        if not self.enable_experimental:
            return

        for i in range(self.num_slots):
            self.probe_groups.append(
                self._create_probe_groups(prefixes=probe_prefixes, rules=rules, slot=i)
            )
        for i in range(len(self.probe_groups)):
            for group in self.probe_groups[i].values():
                group.create_interval_signals(self, slot=i)

    def create_transactions(
        self, specs: List["TransactionSpec"], name_prefix: str
    ) -> Dict[int, List["Transaction"]]:
        if self.enable_experimental:
            top = TopTransactionAssembler(specs=specs, name_prefix=name_prefix)

            # Decode all slots
            txns_by_slot = top.calculate(self)
            # Render per-slot lanes
            top.append_lanes(self, separate_by_kind=True)
            return txns_by_slot
        else:
            return []

    def append_manual_enum_signal(
        self, name: str, values: list[str], mapping: dict[str, int]
    ) -> None:
        """
        Append a multi‐bit manual signal to an ILAWaveform, using an Enum display.

        Now supports empty‐string labels by automatically giving them a valid
        enum member name under the hood.
        """
        # sanity checks
        if len(values) != self.sample_count:
            raise ValueError(f"{name}: must supply one value per sample ({self.sample_count})")
        missing = set(values) - set(mapping)
        if missing:
            raise KeyError(f"{name}: no mapping for {missing}")
        # -- step 1: build a "sanitized" mapping that Enum() will accept --
        #    we also keep a reverse‐map so we can show the original strings.
        enum_to_display: dict[str, str] = {}
        sanitized_map: dict[str, int] = {}
        for label, code in mapping.items():
            # pick a valid Python identifier for the enum member
            if label:
                member_name = label
            else:
                # e.g. '' → '_EMPTY', or anything else that isn't a valid name
                member_name = f"VAL_{code}"
            sanitized_map[member_name] = code
            enum_to_display[member_name] = label
        # determine code width
        max_code = max(sanitized_map.values())
        bit_width = max_code.bit_length() or 1

        # assign bit‐range
        old_width = self.width
        bit_index = old_width
        self.width = old_width + bit_width

        # RESIZE THE DATA BUFFER TO ACCOMMODATE NEW BITS
        old_bps = self.bytes_per_sample()
        new_bps = (self.width + 7) // 8  # Calculate new bytes per sample

        if new_bps > old_bps:
            # Need to expand the data buffer
            new_data = bytearray(new_bps * self.sample_count)
            # Copy old data sample by sample
            for i in range(self.sample_count):
                old_start = i * old_bps
                old_end = old_start + old_bps
                new_start = i * new_bps
                new_data[new_start : new_start + old_bps] = self.data[old_start:old_end]
            self.data = new_data

        # create the Enum class with the format expected by decode_waveform_from_json
        enum_name = f"{name}_Enum"
        EnumDef = Enum(enum_name, sanitized_map)

        # Store the enum in the format that can be serialized/deserialized correctly
        # The JSON decoder expects: ["EnumName", {"member1": value1, "member2": value2}]
        enum_def_serializable = [enum_name, sanitized_map]
        # build the probe
        probe = ILAWaveformProbe(
            name=name,
            map="manual",
            map_range=[ILABitRange(bit_index, bit_width)],
            is_bus=True,
            bus_left_index=bit_width - 1,
            bus_right_index=0,
            display_radix=ILAProbeRadix.ENUM,
            enum_def=EnumDef,  # Store the actual Enum class
        )

        # Store serialization info and display map for later use
        probe._enum_def_serializable = enum_def_serializable  # For JSON export
        probe._display_map = enum_to_display  # For showing original labels

        self.probes[name] = probe

        # inject the bits - now use the new bytes_per_sample
        bps = self.bytes_per_sample()  # This will return the NEW bps
        for i, sval in enumerate(values):
            # find the sanitized member name that produced this label
            for member_name, disp in enum_to_display.items():
                if disp == sval:
                    code = sanitized_map[member_name]
                    break
            else:
                # should never happen—sanity check
                raise AssertionError(f"no enum member for {sval!r}")

            base = i * bps
            for bit in range(bit_width):
                byte_off = (bit_index + bit) // 8
                mask = 1 << ((bit_index + bit) % 8)
                idx = base + byte_off
                if (code >> bit) & 1:
                    self.data[idx] |= mask
                else:
                    self.data[idx] &= ~mask

    def get_window_count(self) -> int:
        return len(self.trigger_position)

    def set_sample(self, sample_index: int, sample: bytearray) -> None:
        """Sample may have more bytes than waveform samples have. Erase any gap bit."""
        sample_byte_count = self.bytes_per_sample()
        copy_byte_count = min(sample_byte_count, len(sample))
        start = sample_byte_count * sample_index
        self.data[start : start + copy_byte_count] = sample[0:copy_byte_count]
        if not self.gap_index:
            return
        gap_byte_index, gap_bit_index = divmod(self.width, 8)
        mask = 0xFF ^ (1 << gap_bit_index)
        self.data[start + gap_byte_index] &= mask

    def export_waveform(
        self,
        export_format: str = "CSV",
        fh_or_filepath: Union[TextIOBase, BytesIO, str] = sys.stdout,
        probe_names: Optional[List[str]] = None,
        start_window_idx: int = 0,
        window_count: Optional[int] = None,
        start_sample_idx: int = 0,
        sample_count: Optional[int] = None,
        include_gap: bool = False,
        compression: int = zipfile.ZIP_DEFLATED,
        compresslevel=None,
    ) -> None:
        """
        Export a waveform in CSV, VCD or CITF format, to a file or in-memory buffer.
        By default, all samples for all probes are exported, but it is
        possible to select which probes and window/sample ranges for CSV/VCD formats.

        ================================ ======================== ==============================
        Argument/Parameter               Type                     Supported by Export Format
        ================================ ======================== ==============================
        export_format                    str                      CSV, VCD, CITF
        fh_or_filepath                   TextIOBase               CSV, VCD
        fh_or_filepath                   BytesIO                            CITF
        fh_or_filepath                   str                      CSV, VCD, CITF
        probe_names                      List[str]                CSV, VCD
        start_window                     int                      CSV, VCD
        start_sample_idx                 int                      CSV, VCD
        sample_count                     int                      CSV, VCD
        include_gap                      bool                     CSV, VCD
        include_gap                      bool                     CSV, VCD
        compression                      int                                CITF
        compresslevel                    int                                CITF
        ================================ ======================== ==============================


        Args:
            export_format (str):  Alternatives for output format.

                - 'CSV' - Comma Separated Value Format. Default.
                - 'VCD' - Value Change Dump.
                - 'CITF' - ChipScoPy ILA Trace Format. Export of a whole ILA waveform to a compressed archive.


            fh_or_filepath (TextIOBase, BytesIO, str): File object handle or filepath string. Default is `sys.stdout`.
                If the argument is a file object, closing and opening the file is the responsibility of the caller.
                If argument is a string, the file will be opened and closed by the function.

            probe_names (Optional[List[str]]): List of probe names. Default 'None' means export all probes.
            start_window_idx (int): Starting window index. Default is first window.
            window_count (Optional[int]): Number of windows to export. Default is all windows.
            start_sample_idx (int): Starting sample within window. Default is first sample.
            sample_count (Optional[int]): Number of samples per window. Default is all samples.
            include_gap (bool):  Default is False. Include the pseudo "gap" 1-bit probe in the result.
            compression: Default is zipfile.ZIP_DEFLATED. See zipfile.ZipFile at https://docs.python.org/.
            compresslevel: See zipfile.ZipFile at https://docs.python.org/.

        """

        if export_format.upper() == "CITF":
            export_compressed_waveform(self, fh_or_filepath, compression, compresslevel)
            return

        if export_format.upper() != "VCD" and export_format.upper() != "CSV":
            raise ValueError(
                f'ILAWaveform.export() called with unknown export_format:"{export_format}"'
                "Supported export formats are VCD, CSV and CITF."
            )
        if isinstance(fh_or_filepath, str):
            with open(fh_or_filepath, "w", buffering=16384) as fh:
                export_waveform_to_stream(
                    self,
                    export_format,
                    fh,
                    probe_names,
                    start_window_idx,
                    window_count,
                    start_sample_idx,
                    sample_count,
                    include_gap,
                )
            if export_format.upper() == "CSV" and len(self.probe_groups) > 0:
                self.apply_probe_group_enums_to_csv(fh_or_filepath, strict=True)
            elif export_format.upper() == "VCD" and len(self.probe_groups) > 0:
                for pg in self.probe_groups[
                    0
                ].values():  # This will have to be later updated. Just too clunky to be used rn.
                    pg.write_enum_mappings_to_text_file(f"{pg.name}.gtkw", pg.enum_mappings)
                if self.transactionAssembler:
                    self.transactionAssembler.write_gtkw_translate(
                        vcd_path=fh_or_filepath, out_dir="gtkw_files", separate_by_kind=True
                    )
            return
        else:
            export_waveform_to_stream(
                self,
                export_format,
                fh_or_filepath,
                probe_names,
                start_window_idx,
                window_count,
                start_sample_idx,
                sample_count,
                include_gap,
            )
            if export_format.upper() == "CSV" and len(self.probe_groups) > 0:
                self.apply_probe_group_enums_to_csv(fh_or_filepath, strict=True)
            elif export_format.upper() == "VCD" and len(self.probe_groups) > 0:
                for pg in self.probe_groups[0].values():
                    pg.write_enum_mappings_to_text_file(f"{pg.name}.gtkw", pg.enum_mappings)
                if self.transactionAssembler:
                    self.transactionAssembler.write_gtkw_translate(
                        vcd_path=fh_or_filepath, out_dir="gtkw_files", separate_by_kind=True
                    )

    def apply_probe_group_enums_to_csv(
        self,
        csv_in_path: str,
        strict: bool = False,
    ) -> None:
        """
        Post-process a CSV: replace numeric values in ProbeGroup signal columns with enum labels.

        Args:
            csv_in_path: Path to the input CSV (already exported).
            csv_out_path: Path to write the updated CSV. If None, overwrites csv_in_path.
            probe_groups: Dict of ProbeGroup where each group has:
                - signal_name: str - the column header to target
                - enum_mappings: Dict[str, int] - mapping label -> code
            idle_label: Label used when a mapping resolves to an empty string or missing label.
            strict: If True, raises on missing columns or unparsable numeric values. Otherwise logs and passes through.

        Behavior:
            - Keeps comment lines starting with '#' intact.
            - Finds the header row (first non-comment row) and replaces values only in columns whose header matches
              a group's signal_name.
            - Expected CSV cell values are integers (decimal or 0x-prefixed hex). If a value is already non-numeric,
              it will be left as-is unless strict=True.
        """

        csv_out_path = csv_in_path  # overwrite

        # 1) Read all lines
        with open(csv_in_path, "r", newline="") as fh:
            lines = fh.readlines()
        # 2) Identify header line (first non-comment)
        header_idx = None
        for i, line in enumerate(lines):
            if not line.lstrip().startswith("#"):
                header_idx = i
                break

        if header_idx is None:
            raise ValueError("No header row found (no non-comment lines).")

        # 3) Parse header
        header = next(csv.reader([lines[header_idx]]))
        col_index_by_name = {name: idx for idx, name in enumerate(header)}

        # 4) For each ProbeGroup, find target column and build reverse mapping (code -> label)
        #    Also collect display override if ProbeGroup stores it (optional).
        target_columns: Dict[int, "Tuple"[str, Dict[int, str]]] = {}

        def _find_col_index_by_prefix(header: list[str], signal_name: str) -> Optional[int]:
            # Exact match first
            if signal_name in col_index_by_name:
                return col_index_by_name[signal_name]
            # Case-insensitive startswith fallback
            sig_lower = signal_name.lower()
            matches = [idx for idx, name in enumerate(header) if name.lower().startswith(sig_lower)]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                # If multiple candidates, prefer the shortest name or the one equal ignoring case
                exact_ci = [idx for idx, name in enumerate(header) if name.lower() == sig_lower]
                if exact_ci:
                    return exact_ci[0]
                # Otherwise pick the shortest match deterministically
                shortest = min(matches, key=lambda idx: len(header[idx]))
                return shortest
            return None

        for slot_group in self.probe_groups:
            for group_name, pg in slot_group.items():
                signal_name = getattr(pg, "channel_name", None)
                enum_mapping = getattr(pg, "enum_mappings", None)  # label -> code
                if not signal_name or not enum_mapping:
                    continue
                col_idx = _find_col_index_by_prefix(header, signal_name)

                if col_idx is None:
                    if strict:
                        raise KeyError(f"Signal column '{signal_name}' not found in CSV header.")
                    else:
                        # Skip this group if column not present
                        continue

                # Invert mapping: code -> label
                code_to_label = {code: label for label, code in enum_mapping.items()}
                target_columns[col_idx] = (signal_name, code_to_label)
        lanes: Dict[str, Dict[int, str]] = {}

        if self.transactionAssembler is not None:
            # Aggregate per-lane enum mappings from all transactions (across slots)
            lanes: Dict[str, Dict[int, str]] = {}

            asm = self.transactionAssembler
            txns_by_slot = getattr(asm, "transactions_by_slot", None)

            # Helper to merge a single transaction into the lanes dict
            def _merge_txn_lane(t):
                lane_name = getattr(t, "channel_name", None)
                enum_map = getattr(t, "enum", None)  # expected code -> label
                if not lane_name or not enum_map:
                    return
                lane_map = lanes.setdefault(lane_name, {})
                # Merge codes; keep first-seen label for determinism
                for code, label in enum_map.items():
                    lane_map.setdefault(code, label)

            # 1) Flatten transactions across slots (or fall back to asm.transactions)
            if isinstance(txns_by_slot, dict):
                for slot, txns in txns_by_slot.items():
                    for t in txns:
                        _merge_txn_lane(t)
            else:
                for t in getattr(asm, "transactions", []):
                    _merge_txn_lane(t)

            # 2) Normalize and attach to target_columns once per lane
            for lane_name, code_to_label in lanes.items():
                # Ensure a code 0 mapping exists (choose label convention to match your CSV tools)
                if 0 not in code_to_label:
                    code_to_label[0] = "-"  # or "-" if that’s what your exporter expects

                col_idx = _find_col_index_by_prefix(header, lane_name)
                if col_idx is not None:
                    target_columns[col_idx] = (lane_name, code_to_label)
                elif strict:
                    raise KeyError(
                        f"Transaction lane column '{lane_name}' not found in CSV header."
                    )

        if not target_columns:
            # No work to do; just copy file
            with open(csv_out_path, "w", newline="") as outfh:
                outfh.writelines(lines)
            return

        # 5) Helper: parse numeric value (supports int or hex like 0x..)
        def parse_code(val: str) -> Optional[int]:
            s = val.strip()
            if s == "":
                return None
            try:
                return int(s, 16)
            except ValueError:
                return None

        # 6) Write out modified CSV
        with open(csv_out_path, "w", newline="") as outfh:
            # Copy any leading comment lines unchanged
            for i in range(header_idx):
                outfh.write(lines[i])

            writer = csv.writer(outfh)
            writer.writerow(header)

            # Process rows after header
            for raw_line in lines[header_idx + 1 :]:
                # Keep empty or comment-like lines intact
                if not raw_line.strip():
                    outfh.write(raw_line)
                    continue

                row = next(csv.reader([raw_line]))
                # Ensure row has at least as many columns as header (pad if necessary)
                if len(row) < len(header):
                    row += [""] * (len(header) - len(row))

                # For each target column, map numeric code -> text label
                for col_idx, (signal_name, code_to_label) in target_columns.items():
                    cell = row[col_idx]

                    code = parse_code(cell)
                    # if col_idx == 45 and cell == '0A':
                    #     breakpoint()
                    if code is None:
                        # If non-numeric leave as-is.
                        # if col_idx == 45:
                        #     breakpoint()
                        continue

                    label = code_to_label.get(code, "")
                    if label == "":
                        label = "-"
                    row[col_idx] = label

                writer.writerow(row)

    @staticmethod
    def import_waveform(
        import_format: str,
        filepath_or_buffer: Union[str, BytesIO],
    ):
        """
        Create an ILAWaveform object from a ChipScoPy ILA Trace Format (CITF) compressed archive.
        The archive must contain these two files:

            - waveform.cfg, waveform and probe meta information.
            - waveform.data, binary waveform samples.

        Args:
            import_format (str): Format "CITF" is supported.
            filepath_or_buffer (str, BytesIO): Filepath string or in-memory buffer.

        Returns (ILAWaveform):
            Waveform object.

        """
        if import_format.upper() != "CITF":
            raise (
                f'import_waveform command called with import_format "{import_format}".'
                f' Only "CITF" format is supported.'
            )

        return import_compressed_waveform(filepath_or_buffer)

    def get_data(
        self,
        probe_names: Optional[List[str]] = None,
        start_window_idx: int = 0,
        window_count: Optional[int] = None,
        start_sample_idx: int = 0,
        sample_count: Optional[int] = None,
        include_trigger: bool = False,
        include_sample_info: bool = False,
        include_gap: bool = False,
    ) -> Dict[str, List[int]]:
        """
        Get probe waveform data as a list of int values for each probe.
        By default, all samples for all probes are included in return data,
        but it is possible to select which probes and window/sample ranges.

        Args:
            probe_names (Optional[List[str]]): List of probe names. Default 'None' means export all probes.
            start_window_idx (int): Starting window index. Default is first window.
            window_count (Optional[int]): Number of windows to export. Default is all windows.
            start_sample_idx (int): Starting sample within window. Default is first sample.
            sample_count (Optional[int]): Number of samples per window. Default is all samples.
            include_trigger (bool): Include pseudo probe with name '__TRIGGER' in result. Default is False.
            include_sample_info (bool):  Default is False. Include the following pseudo probes in result:

              - '__SAMPLE_INDEX' - Sample index
              - '__WINDOW_INDEX' - Window index.
              - '__WINDOW_SAMPLE_INDEX' - Sample index within window.

            include_gap (bool):  Default is False. If True, include the pseudo probe '__GAP' in result. \
                                 Value 1 for a gap sample. Value 0 for a regular sample.


        Returns (Dict[str, List[int]]):
            Ordered dict, in order:
              - '__TRIGGER', if argument **include_trigger** is True
              - '__SAMPLE_INDEX', if argument **include_sample_info** is True
              - '__WINDOW_INDEX', if argument **include_sample_info** is True
              - '__WINDOW_SAMPLE_INDEX', if argument **include_sample_info** is True
              - '__GAP', if argument **include_gap** is True
              - probe values in order of argument **probe_names**.

            Dict key: probe name. Dict value is list of int values, for a probe.

        """
        return get_waveform_data_values(
            self,
            probe_names,
            start_window_idx,
            window_count,
            start_sample_idx,
            sample_count,
            include_trigger,
            include_sample_info,
            include_gap,
        )

    def get_probe_data(
        self,
        probe_name: str,
        start_window_idx: int = 0,
        window_count: Optional[int] = None,
        start_sample_idx: int = 0,
        sample_count: Optional[int] = None,
    ) -> List[int]:
        """
        Get waveform data as a list of int values for one probe.
        By default, all samples for the probe are returned,
        It is possible to select window range and sample range.

        Args:
            probe_name (str): probe name.
            start_window_idx (int): Starting window index. Default is first window.
            window_count (Optional[int]): Number of windows to export. Default is all windows.
            start_sample_idx (int): Starting sample within window. Default is first sample.
            sample_count (Optional[int]): Number of samples per window. Default is all samples.

        Returns (List[int]):
            List probe values.

        """
        res_dict = get_waveform_data_values(
            self,
            [probe_name],
            start_window_idx,
            window_count,
            start_sample_idx,
            sample_count,
            include_trigger=False,
            include_sample_info=False,
            include_gap=False,
        )
        return res_dict[probe_name]

    def __str__(self) -> str:
        items = {key: val for key, val in self.__dict__.items() if key != "data"}
        return pformat(items, 2)

    def __repr__(self) -> str:
        data_size = len(self.data) if self.data else 0
        json_dict = {
            "width": self.width,
            "sample_count": self.sample_count,
            "trigger_position": self.trigger_position,
            "window_size": self.window_size,
            "probes": {key: asdict(val) for key, val in self.probes.items()},
            "data size": hex(data_size),
        }
        ret = json.dumps(json_dict, cls=Enum2StrEncoder, indent=4)
        return ret

    def get_txn_data(self, slot: int, kind: str) -> List[Dict[str, Any]]:
        if not self.transactionAssembler:
            return []
        transactions = self.transactionAssembler.get_transactions_by_slot()

        slot_txns = transactions.get(slot, [])
        read_txns = [
            t
            for t in slot_txns
            if getattr(t, "kind", None) == kind and getattr(t, "end_idx", None) is not None
        ]
        if not read_txns:
            raise ValueError("No completed read transactions in slot 0")
        start_sample_idx = min(t.start_idx for t in read_txns)
        latest_end_idx = max(t.end_idx for t in read_txns)
        sample_count = latest_end_idx - start_sample_idx + 1
        if sample_count < 0:
            raise ValueError(
                f"Invalid sample range: start={start_sample_idx}, end={latest_end_idx}"
            )
        unique_probes = []
        seen = set()

        def _add_probe(name: str):
            if name and name not in seen:
                seen.add(name)
                unique_probes.append(name)

        for t in read_txns:
            p = t.probes
            for full in p.values():
                _add_probe(full)

        if not unique_probes:
            raise ValueError("No probe names found on read transactions")

        # Render per-slot lanes
        pdata = self.get_data(
            probe_names=unique_probes, start_sample_idx=start_sample_idx, sample_count=sample_count
        )
        return pdata


def tcf_get_waveform_data(tcf_node) -> {}:
    tcf_props = tcf_node.get_property_group(["data"])
    props = {
        "width": tcf_props["trace_width"],
        "sample_count": tcf_props["trace_sample_count"],
        "trigger_position": tcf_props["trace_trigger_position"],
        "window_size": tcf_props["trace_window_size"],
        "data": tcf_props["trace_data"],
    }
    return props


class WaveformWriter(object):
    def __init__(self, file_handle: Union[TextIOBase, None], probes: [ILAWaveformProbe]):
        self._file_handle = file_handle
        self._probes = probes
        self._probe_count = len(probes)
        self._probe_names = self.make_probe_names()
        self._probe_widths = [p.length() for p in probes]

    def handle(self) -> TextIOBase:
        return self._file_handle

    def write(self, msg: str):
        self._file_handle.write(msg)

    @staticmethod
    def make_values_unknown(in_values: List[str], unknown_ch: str) -> List[str]:
        return [unknown_ch * len(val) for val in in_values]

    @abstractmethod
    def make_probe_names(self) -> [str]:
        return [p.name for p in self._probes]

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def write_sample(
        self,
        sample_position: int,
        window_index: int,
        sample_in_window_index: int,
        is_trigger: bool,
        probe_binary_reversed_values: [str],
        is_last_sample: bool,
        is_gap: bool,
    ) -> None:
        """

        Args:
            sample_position (int):
            window_index (int):
            sample_in_window_index (int):
            is_trigger (bool):
            probe_binary_reversed_values ([str]): binary string values each start lsb at position zero.
            is_last_sample(bool): Last sample in waveform.
            is_gap (bool): True ig no data available for the sample.

        Returns:

        """
        pass


class WaveformWriterCSV(WaveformWriter):
    def __init__(self, file_handle: TextIOBase, probes: [ILAWaveformProbe], include_gap: bool):
        WaveformWriter.__init__(self, file_handle, probes)
        self._include_gap = include_gap

    def init(self):
        self.write("Sample in Buffer,Sample in Window,TRIGGER,")
        if self._include_gap:
            self.write("GAP,")
        self.write(",".join(self._probe_names))
        self.write("\nRadix - UNSIGNED,UNSIGNED,UNSIGNED,")
        # Currently, HEX is the only supported radix
        self.write(",".join(["HEX"] * self._probe_count))
        self.write("\n")

    def make_probe_names(self) -> [str]:
        return [p.name + p.bus_range_str() for p in self._probes]

    def write_sample(
        self,
        sample_position: int,
        window_index: int,
        sample_in_window_index: int,
        is_trigger: bool,
        probe_binary_reversed_values: [str],
        is_last_sample: bool,
        is_gap: bool,
    ) -> None:
        hex_values = bin_reversed_to_hex_values(probe_binary_reversed_values)
        if is_gap:
            hex_values = WaveformWriter.make_values_unknown(hex_values, "X")
        hex_values_str = ",".join(hex_values)
        trig_mark = "1" if is_trigger else "0"
        if self._include_gap:
            gap_value = "1" if is_gap else "0"
            self.write(
                f"{sample_position},{sample_in_window_index},{trig_mark},{gap_value},{hex_values_str}\n"
            )
        else:
            self.write(f"{sample_position},{sample_in_window_index},{trig_mark},{hex_values_str}\n")


class WaveformWriterToDict(WaveformWriter):
    def __init__(
        self,
        probes: [ILAWaveformProbe],
        include_trigger: bool,
        include_sample_info: bool,
        include_gap: bool,
    ):
        WaveformWriter.__init__(self, None, probes)
        self._include_trigger = include_trigger
        self._include_sample_info = include_sample_info
        self._include_gap = include_gap
        self._result = defaultdict(list)

    def init(self):
        return

    def get_result(self) -> Dict[str, List[int]]:
        return self._result

    def write_sample(
        self,
        sample_position: int,
        window_index: int,
        sample_in_window_index: int,
        is_trigger: bool,
        probe_binary_reversed_values: [str],
        is_last_sample: bool,
        is_gap: bool,
    ) -> None:
        if self._include_trigger:
            self._result["__TRIGGER"].append(1 if is_trigger else 0)
        if self._include_sample_info:
            self._result["__SAMPLE_INDEX"].append(sample_position)
            self._result["__WINDOW_INDEX"].append(window_index)
            self._result["__WINDOW_SAMPLE_INDEX"].append(sample_in_window_index)
        if self._include_gap:
            self._result["__GAP"].append(1 if is_gap else 0)

        int_values = [int(r_val[::-1], 2) for r_val in probe_binary_reversed_values]
        for probe_name, val in zip(self._probe_names, int_values):
            self._result[probe_name].append(val)


class WaveformWriterVCD(WaveformWriter):
    """Value Change Dump format. See Wikipedia and IEEE Std 1364-2001."""

    def __init__(self, file_handle: TextIOBase, probes: [ILAWaveformProbe], include_gap: bool):
        WaveformWriter.__init__(self, file_handle, probes)
        self._values = None
        self._vars: List[str] = None
        self._trigger_var = None
        self._window_var = None
        self._gap_var = None
        self._include_gap = include_gap
        self._prev_sample_is_trigger = None
        self._prev_window_index = None
        self._prev_sample_is_gap = None

    @staticmethod
    def _generate_vars() -> Generator[str, None, None]:
        """Supports up to 94 + 94*94 + 94*94*94 = 839,514 probes (or variables)."""
        for x in range(ord("!"), ord("~")):
            yield chr(x)
        for xx in range(ord("!"), ord("~")):
            for yy in range(ord("!"), ord("~")):
                yield chr(xx) + chr(yy)
        for xxx in range(ord("!"), ord("~")):
            for yyy in range(ord("!"), ord("~")):
                for zzz in range(ord("!"), ord("~")):
                    yield chr(xxx) + chr(yyy) + chr(zzz)

    def _write_variable_definitions(self):
        generate_vars = WaveformWriterVCD._generate_vars
        self._values = [None] * self._probe_count
        self._trigger_var, self._window_var, self._gap_var, *self._vars = islice(
            generate_vars(),
            self._probe_count + 3,
        )

        for width, var, probe_name in zip(self._probe_widths, self._vars, self._probe_names):
            self.write(f"$var reg {width} {var} {probe_name} $end\n")
        self.write(
            f"$var reg 1 {self._trigger_var} _TRIGGER $end\n"
            f"$var reg 1 {self._window_var} _WINDOW $end\n"
        )
        if self._include_gap:
            self.write(f"$var reg 1 {self._gap_var} _GAP $end\n")

    def make_probe_names(self) -> [str]:
        return [p.name + " " + p.bus_range_str() for p in self._probes]

    def init(self):
        now = "{:%Y-%m-%d %H:%M:%S}".format(datetime.now())
        # adjust for trigger position
        hdr_1 = f"$date\n        {now}\n$end\n"

        hdr_2 = (
            "$version\n"
            + f"        ChipScoPy Version {chipscopy.__version__}\n"
            + "$end\n"
            + "$timescale\n        1ps\n$end\n"
            + "$scope module dut $end\n"
        )

        hdr_3 = "$upscope $end\n$enddefinitions $end\n"

        self.write(hdr_1 + hdr_2)
        self._write_variable_definitions()
        self.write(hdr_3)

    def write_sample(
        self,
        sample_position: int,
        window_index,
        sample_in_window_index,
        is_trigger,
        probe_binary_reversed_values: [str],
        is_last_sample,
        is_gap: bool,
    ):
        time_written = False

        def write_value(var: str, reversed_value: str) -> None:
            nonlocal time_written
            if not time_written:
                self.write(f"#{sample_position}\n")
                time_written = True

            if len(reversed_value) == 1:
                self.write(f"{reversed_value}{var}\n")
                return

            # Remove leading zeroes
            if is_gap and reversed_value[0] == "x":
                value = reversed_value
            else:
                # Remove leading zeroes
                msb_idx = reversed_value.rfind("1")
                if msb_idx < 0:
                    msb_idx = 0
                value = reversed_value[msb_idx::-1]
            self.write(f"b{value} {var}\n")

        # Write time, for last sample, even if no changes.
        if is_last_sample:
            self.write(f"#{sample_position}\n")
            time_written = True

        # Trigger value
        if is_trigger != self._prev_sample_is_trigger:
            write_value(self._trigger_var, "1" if is_trigger else "0")
            self._prev_sample_is_trigger = is_trigger

        # Window marker.
        if window_index != self._prev_window_index:
            write_value(self._window_var, "1" if window_index % 2 else "0")
            self._prev_window_index = window_index

        # gap value
        if self._include_gap and is_gap != self._prev_sample_is_gap:
            write_value(self._gap_var, "1" if is_gap else "0")
            self._prev_sample_is_gap = is_gap

        # Regular values
        if is_gap:
            probe_binary_reversed_values = WaveformWriter.make_values_unknown(
                probe_binary_reversed_values, "x"
            )
        for idx, new_val in enumerate(probe_binary_reversed_values):
            if new_val == self._values[idx]:
                continue

            self._values[idx] = new_val
            write_value(self._vars[idx], new_val)


def export_waveform_to_stream(
    waveform: ILAWaveform,
    export_format: str,
    stream_handle: TextIOBase,
    probe_names: [str],
    start_window_idx: int,
    window_count: Optional[int],
    start_sample_idx: int,
    sample_count: Optional[int],
    include_gap: bool,
) -> None:
    """Arguments documented in calling API function"""
    if probe_names:
        probes = [waveform.probes.get(p_name, None) for p_name in probe_names]
        if not all(probes):
            bad_names = set(probe_names) - set(waveform.probes.keys())
            raise KeyError(f"export_waveform() called with non-existent probe_name:\n  {bad_names}")
    else:
        probes = waveform.probes.values()
    if export_format.upper() == "CSV":
        waveform_writer = WaveformWriterCSV(stream_handle, probes, include_gap)
    elif export_format.upper() == "VCD":
        waveform_writer = WaveformWriterVCD(stream_handle, probes, include_gap)
    else:
        raise ValueError(
            f'ILAWaveform.export_waveform() called with non-supported format "{export_format}"'
        )
    _export_waveform(
        waveform,
        waveform_writer,
        probes,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
        "export_waveform()",
    )


def get_waveform_data_values(
    waveform: ILAWaveform,
    probe_names: [str],
    start_window_idx: int,
    window_count: Optional[int],
    start_sample_idx: int,
    sample_count: Optional[int],
    include_trigger: bool,
    include_sample_info: bool,
    include_gap: bool,
) -> Dict[str, List[int]]:
    """Arguments documented in calling API function"""
    if probe_names:
        probes = [waveform.probes.get(p_name, None) for p_name in probe_names]
        if not all(probes):
            bad_names = set(probe_names) - set(waveform.probes.keys())
            raise KeyError(
                f"ILAWaveform.get_data() called with non-existent probe name(s):\n  {bad_names}"
            )
    else:
        probes = waveform.probes.values()

    waveform_writer = WaveformWriterToDict(
        probes, include_trigger, include_sample_info, include_gap
    )
    _export_waveform(
        waveform,
        waveform_writer,
        probes,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
        "ILAWaveform.get_data()",
    )

    return waveform_writer.get_result()


def _export_waveform(
    waveform: ILAWaveform,
    writer: WaveformWriter,
    probes: [ILAWaveformProbe],
    start_window_idx: int,
    window_count: Optional[int],
    start_sample_idx: int,
    sample_count: Optional[int],
    calling_function: str,
) -> None:
    # It is at this point where W_events dissapears for whatever reason.
    def get_sample_binary_values(sample_data: memoryview) -> [str]:
        sample_int_value = int.from_bytes(sample_data, byteorder="little", signed=False)
        reversed_bin_value = f"{sample_int_value:0{waveform.width}b}"[::-1]
        values = []
        for probe in probes:
            # Each probe value can be made up of multiple bit range slices.
            slices = [reversed_bin_value[br.index : br.index + br.length] for br in probe.map_range]
            p_val = "".join(slices)
            values.append(p_val)
        return values

    def convert_to_display_values(bin_values: [str], probes: [ILAWaveformProbe]) -> [str]:
        """Convert binary values to display values based on probe settings."""
        display_values = []
        for i, (bin_val, probe) in enumerate(zip(bin_values, probes)):
            if probe.display_radix == ILAProbeRadix.ENUM and probe.enum_def:
                # Convert binary to integer
                int_val = int(bin_val[::-1], 2) if bin_val else 0

                try:
                    # Get enum member
                    enum_member = probe.enum_def(int_val)

                    # Check if probe has display map for custom labels
                    if hasattr(probe, "_display_map"):
                        display_val = probe._display_map.get(enum_member.name, enum_member.name)
                    else:
                        display_val = enum_member.name

                    display_values.append(display_val)
                except ValueError:
                    # Value not in enum, show as hex
                    display_values.append(f"0x{int_val:X}")
            else:
                # Keep binary value for non-enum probes
                display_values.append(bin_val)

        return display_values

    def is_gap(sample_high_byte: int, gap_index: Optional[int]) -> bool:
        if gap_index and sample_high_byte & (1 << (gap_index % 8)):
            return True
        return False

    if not window_count:
        window_count = waveform.get_window_count()
    if not sample_count:
        sample_count = waveform.window_size

    w_size = waveform.window_size
    max_window_count = (waveform.sample_count + w_size - 1) // w_size
    if start_window_idx < 0 or start_window_idx >= max_window_count:
        raise ValueError(
            f'{calling_function} function argument start_window="{start_window_idx}" '
            f"must be in the range [0-{max_window_count - 1}]"
        )
    if start_sample_idx < 0 or start_sample_idx >= w_size:
        raise ValueError(
            f'{calling_function} function argument "start_sample="{start_sample_idx}" '
            f"must be in the range [0-{w_size - 1}]"
        )
    if sample_count < 1 or sample_count > w_size - start_sample_idx:
        raise ValueError(
            f'{calling_function} function argument "sample_count="{sample_count}" '
            f"must be in the range [1-{w_size - start_sample_idx}], "
            f'since start_sample_idx="{start_sample_idx}".'
        )
    if window_count < 1 or window_count > max_window_count - start_window_idx:
        raise ValueError(
            f'{calling_function} function argument "window_count="{window_count}" '
            f"must be in the range [1-{max_window_count - start_window_idx}], "
            f'since start_window_idx="{start_window_idx}".'
        )

    sample_byte_count = waveform.bytes_per_sample()
    raw_samples = memoryview(waveform.data)
    sample_is_gap = False
    writer.init()

    for window_idx in range(start_window_idx, start_window_idx + window_count):
        window_start_sample_idx = window_idx * w_size
        trigger_sample_idx = waveform.trigger_position[window_idx]
        for sample_idx in range(
            window_start_sample_idx + start_sample_idx,
            window_start_sample_idx + start_sample_idx + sample_count,
        ):
            if sample_idx >= waveform.sample_count:
                # last window is not full.
                break
            raw_sample_idx = sample_idx * sample_byte_count
            raw_sample_idx_end = raw_sample_idx + sample_byte_count
            sample_idx_in_window = sample_idx - window_start_sample_idx
            bin_values = get_sample_binary_values(raw_samples[raw_sample_idx:raw_sample_idx_end])
            if waveform.gap_index:
                sample_is_gap = is_gap(raw_samples[raw_sample_idx_end - 1], waveform.gap_index)
            writer.write_sample(
                sample_idx,
                window_idx,
                sample_idx_in_window,
                sample_idx_in_window == trigger_sample_idx,
                bin_values,
                sample_idx + 1 == waveform.sample_count,
                sample_is_gap,
            )


WAVEFORM_ARCHIVE_VERSION = 1


class Waveform2StrEncoder(json.JSONEncoder):
    @staticmethod
    def encode_map_range(obj):
        # Convert ILABitRange tuple to a dict, e.g. [{"index": 0, "length": 2}]
        if isinstance(obj, list):
            return [elem._asdict() if isinstance(elem, ILABitRange) else elem for elem in obj]
        return obj

    def default(self, obj):
        if isinstance(obj, ILAWaveformProbe):
            return {
                key: Waveform2StrEncoder.encode_map_range(val) for key, val in asdict(obj).items()
            }
        if isinstance(obj, ILABitRange):
            return obj._asdict()
        if isinstance(obj, ILAProbeRadix):
            return str(obj.name)
        if isinstance(obj, enum.EnumMeta):
            # Encode as 2-item list: [<name>, <dict of enum value items>]
            items = {item.name: item.value for item in list(obj)}
            return [obj.__name__, items]
        return json.JSONEncoder.default(self, obj)


def export_compressed_waveform(
    waveform: ILAWaveform,
    filepath_or_buffer: Union[str, BytesIO],
    compression: int,
    compresslevel: int,
) -> None:
    waveform_dict = {
        "version": 1,
        "gap_index": waveform.gap_index,
        "probes": waveform.probes,
        "sample_count": waveform.sample_count,
        "trigger_position": waveform.trigger_position,
        "window_size": waveform.window_size,
        "width": waveform.width,
    }

    json_str = json.dumps(waveform_dict, cls=Waveform2StrEncoder, indent=4)

    with ZipFile(
        filepath_or_buffer,
        mode="w",
        allowZip64=True,
        compression=compression,
        compresslevel=compresslevel,
    ) as zf:
        zf.writestr("waveform.cfg", json_str)
        zf.writestr("waveform.data", waveform.data)


def decode_waveform_from_json(json_str: str, in_data: bytearray) -> ILAWaveform:
    def decode_map_range(in_range: List[Dict[str, int]]) -> List[ILABitRange]:
        res = [ILABitRange(**dd) for dd in in_range]
        return res

    def decode_probe(probe_name: str, in_dict: Dict) -> ILAWaveformProbe:
        pd = {}
        for key, value in in_dict.items():
            try:
                if key == "map_range":
                    pd[key] = decode_map_range(value)
                elif key == "display_radix":
                    pd[key] = ILAProbeRadix[value]
                elif key == "enum_def":
                    if isinstance(value, list) and len(value) == 2:
                        pd[key] = enum.Enum(value[0], value[1])
                    else:
                        pd[key] = None
                else:
                    pd[key] = value
            except Exception as ex:
                raise ValueError(f'Error reading ILA waveform probe "{probe_name}"') from ex

        res = ILAWaveformProbe(**pd)
        return res

    def decode_probes(in_probes: Dict) -> Dict[str, ILAWaveformProbe]:
        res = {name: decode_probe(name, probe_dict) for name, probe_dict in in_probes.items()}
        return res

    # Decode waveform json string.
    json_dict = json.load(StringIO(json_str))
    wd = dict()
    wd["data"] = in_data
    wd["probes"] = decode_probes(json_dict.get("probes", dict()))
    for key, value in json_dict.items():
        if key in ["data", "probes"]:
            # data and probes, handled above.
            pass
        elif key == "version":
            if value > WAVEFORM_ARCHIVE_VERSION:
                raise ValueError(
                    f'waveform archive version "{value}" is not supported.'
                    f'Only versions "<={WAVEFORM_ARCHIVE_VERSION}" are supported.'
                )
        else:
            wd[key] = value

    return ILAWaveform(**wd)


def import_compressed_waveform(filepath_or_buffer: Union[str, BytesIO]) -> ILAWaveform:
    with ZipFile(filepath_or_buffer, mode="r") as zf:
        json_str = zf.read("waveform.cfg").decode()
        data = bytearray(zf.read("waveform.data"))

    waveform = decode_waveform_from_json(json_str, data)
    return waveform


class ProbeDataMapper:
    """Wraps ProbeData to map simple signal names to full probe names."""

    def __init__(self, probe_data, signal_mapping):
        self._probe_data = probe_data
        self._mapping = signal_mapping

    def rising_edge(self, signal, idx):
        full_name = self._mapping.get(signal, signal)
        return self._probe_data.rising_edge(full_name, idx)

    def both_asserted(self, sig1, sig2, idx):
        full_sig1 = self._mapping.get(sig1, sig1)
        full_sig2 = self._mapping.get(sig2, sig2)
        return self._probe_data.both_asserted(full_sig1, full_sig2, idx)

    def signal(self, signal, idx):
        full_name = self._mapping.get(signal, signal)
        return self._probe_data.signal(full_name, idx)
