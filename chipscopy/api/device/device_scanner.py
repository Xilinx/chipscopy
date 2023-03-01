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
"""device_scanner.py -

Scans hw_server and cs_server and organize nodes into the devices.

There is a relationship between nodes across views. The device scanner identifies
the available devices, and help to connect associated nodes in the views together
for any given device.

::

    ----------------------------------------------------------------------------
    -- Versal Node Tree Example
    ----------------------------------------------------------------------------
    jtag (ViewInfo)
    └── whole scan chain (JtagCable)                  jsn-VCK190 FT4232H-80500501b019A
        ├── arm_dap (JtagDevice)                      jsn-VCK190 FT4232H-80500501b019A-6ba00477-0
        └── xcvc1902 (JtagDevice)                     jsn-VCK190 FT4232H-80500501b019A-14ca8093-0

    memory (ViewInfo)
    ├── Versal xcvc1902 (MemoryNode)                  JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0
    │   ├── RPU (MemoryNode)                          JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0R
        ...
    │   ├── APU (MemoryNode)                          JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0A
        ...
    │   ├── PPU (MemoryNode)                          JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0P1
        ...
    │   ├── PSM (MemoryNode)                          JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0M
        ...
    │   ├── PMC (Node)                                JTAG-jsn-VCK190 FT4232H-80500501b019A-14ca8093-0
    │   └── PL (Node)                                 JTAG-jsn-VCK190 FT4232H-80500501b019A-14ca8093-0PL
    └── DPC (MemoryNode)                              DPC-dpc-jsn-VCK190 FT4232H-80500501b019A-14ca8093-0-70b435d3-0

    debugcore (ViewInfo)
    ├── Versal xcvc1902 (Node)                        JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0
    └── DPC xcvc1902 (DebugCoreClientNode)            dpc-jsn-VCK190 FT4232H-80500501b019A-14ca8093-0-70b435d3-0

    chipscope (ViewInfo)
    ├── Versal xcvc1902 (Node)                        [TCP:localhost:3121.debugcore]-JTAG-jsn-VCK190 FT4232H-80500501b019A-6ba00477-0
    └── DPC xcvc1902 (CoreParent)                     [TCP:localhost:3121.debugcore]-dpc-jsn-VCK190 FT4232H-80500501b019A-14ca8093-0-70b435d3-0

    ----------------------------------------------------------------------------
    -- US+ Node Tree Example
    ----------------------------------------------------------------------------

    jtag (ViewInfo)
    └── whole scan chain (JtagCable)                  jsn-JTAG-SMT2NC-210308958001
        └── xcku040 (JtagDevice)                      jsn-JTAG-SMT2NC-210308958001-13822093-0
            └── bscan-switch (JtagDevice)             jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1
                ├── axi (JtagDevice)                  jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS1
                └── axi (JtagDevice)                  jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS2

    memory (ViewInfo)
    └── xcku040 (Node)                                JTAG-jsn-JTAG-SMT2NC-210308958001-13822093-0
        ├── axi (Node)                                JTAG-jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS1
        └── axi (Node)                                JTAG-jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS2

    debugcore (ViewInfo)
    └── Ultrascale xcku040 (DebugCoreClientNode)      jsn-JTAG-SMT2NC-210308958001-13822093-0
        ├── DebugHub (Node)                           jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS1
        │   ├── VIO_0 (Node)                          jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS1-DBGCORE02-00000000
        ...
        └── DebugHub (Node)                           jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS2
            ├── Core_0 (Node)                         jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS2-DBGCOREDEE3-00000000
            ...

    chipscope (ViewInfo)
    └── Ultrascale xcku040 (CoreParent)               [TCP:localhost:3120.debugcore]-jsn-JTAG-SMT2NC-210308958001-13822093-0
        ├── DebugHub (Node)                           [TCP:localhost:3120.debugcore]-jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS1
        │   ├── VIO_0 (Node)                          [TCP:localhost:3120.debugcore]-jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS1-DBGCORE02-00000000
        ...
        └── DebugHub (Node)                           [TCP:localhost:3120.debugcore]-jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS2
            ├── Core_0 (Node)                         [TCP:localhost:3120.debugcore]-jsn-JTAG-SMT2NC-210308958001-13822093-0-BS-1-BS2-DBGCOREDEE3-00000000
            ...
"""
import dataclasses
from collections import defaultdict
from typing import Optional, List, Iterator, Dict, TypeVar

from chipscopy.api.device.device_util import get_node_dna
from chipscopy.client import ServerInfo


@dataclasses.dataclass
class JtagRecord:
    server: str
    view: str
    ctx: str
    name: str
    hier_name: str
    part: str
    arch_name: str
    is_arm_dap: bool
    jtag_index: int
    jtag_cable_ctx: str
    dap_ctx: str = ""
    dna: Optional[int] = None


@dataclasses.dataclass
class MemoryRecord:
    server: str
    view: str
    ctx: str
    name: str
    hier_name: str
    jtag_node_id: str = None
    jtag_node_group: str = None
    is_dap: bool = False
    is_dpc: bool = False
    dna: Optional[int] = None


@dataclasses.dataclass
class DebugcoreRecord:
    server: str
    view: str
    ctx: str
    name: str
    hier_name: str
    is_dap: bool = False
    is_dpc: bool = False
    dna: Optional[int] = None


@dataclasses.dataclass
class ChipscopeRecord:
    server: str
    view: str
    ctx: str
    name: str
    hier_name: str
    is_dap: bool = False
    is_dpc: bool = False
    dna: Optional[int] = None


ViewRecordType = TypeVar(
    "ViewRecordType", JtagRecord, MemoryRecord, DebugcoreRecord, ChipscopeRecord
)


def scan_jtag_view(
    hw_server: ServerInfo, include_dna=True, include_arm_dap=False
) -> Iterator[JtagRecord]:
    """
    Scans the jtag chains of a hw_server, returning a dict record for
    devices in order for each cable. Arm-dap devices are collapsed into the
    device they are associated with (by default).

    Args:
        hw_server: Hardware server
        include_dna: True to include dna (default True)
        include_arm_dap: True to return arm-dap devices (default False)

    Returns:
        Iterator of devices in jtag chain

    """
    previous_jtag_device_record: Optional[JtagRecord] = None
    view = hw_server.get_view("jtag")
    for jtag_cable in view.get_children():
        jtag_index = 0
        for jtag_device in view.get_children(jtag_cable):
            jtag_record = JtagRecord(
                server="hw_server",
                view="jtag",
                ctx=jtag_device.ctx,
                name=jtag_device.props.get("Name"),
                hier_name=f"jtag/{jtag_device.props.get('Name')}",
                part=jtag_device.props.get("Name"),
                arch_name=jtag_device.props.get("arch_name"),
                is_arm_dap=jtag_device.props.get("Name") == "arm_dap",
                jtag_index=jtag_index,
                jtag_cable_ctx=jtag_cable.ctx,
            )

            if jtag_record.is_arm_dap is False:
                if previous_jtag_device_record and previous_jtag_device_record.is_arm_dap:
                    # Versal and Zynq
                    jtag_record.dap_ctx = previous_jtag_device_record.ctx
                    if include_dna:
                        jtag_record.dna = get_node_dna(jtag_device)
                elif jtag_record.arch_name in ["kintexuplus", "virtexuplus"]:
                    # Virtex, Kintex US+, no arm-dap
                    jtag_record.dap_ctx = ""
                    if include_dna:
                        jtag_record.dna = get_node_dna(jtag_device)
                yield jtag_record
            else:
                if include_arm_dap:
                    yield jtag_record

            jtag_index += 1
            previous_jtag_device_record = jtag_record


def scan_memory_view(hw_server: ServerInfo, include_dna=True) -> Iterator[MemoryRecord]:
    """
    Scan and return the top level memory nodes

    Args:
        hw_server:
        include_dna:

    Returns:

    """
    view = hw_server.get_view("memory")
    for memory_node in view.get_children():
        name = memory_node.props.get("Name", "")
        is_dpc = name.startswith("DPC")
        memory_record = MemoryRecord(
            server="hw_server",
            view="memory",
            ctx=memory_node.ctx,
            name=name,
            hier_name=f"memory/{memory_node.props.get('Name')}",
            jtag_node_id=memory_node.props.get("JtagNodeID"),
            jtag_node_group=memory_node.props.get("JtagGroup"),
            is_dap=not is_dpc,
            is_dpc=is_dpc,
        )
        if include_dna:
            memory_record.dna = get_node_dna(memory_node)
        yield memory_record


def scan_debugcore_view(hw_server: ServerInfo, include_dna=True) -> Iterator[DebugcoreRecord]:
    """
    Args:
        hw_server:
        include_dna:

    Returns:
    """
    view = hw_server.get_view("debugcore")
    for debugcore_node in view.get_children():
        name = debugcore_node.props.get("Name", "")
        is_dpc = name.startswith("DPC")
        debugcore_record = DebugcoreRecord(
            server="hw_server",
            view="debugcore",
            ctx=debugcore_node.ctx,
            name=name,
            hier_name=f"debugcore/{debugcore_node.props.get('Name')}",
            is_dap=not is_dpc,
            is_dpc=is_dpc,
        )
        if include_dna:
            debugcore_record.dna = get_node_dna(debugcore_node)
        yield debugcore_record


def scan_chipscope_view(cs_server: ServerInfo, include_dna=True) -> Iterator[ChipscopeRecord]:
    """
    Args:
        cs_server:
        include_dna:

    Returns:
    """
    view = cs_server.get_view("chipscope")
    for chipscope_node in view.get_children():
        name = chipscope_node.props.get("Name", "")
        is_dpc = name.startswith("DPC")
        chipscope_record = ChipscopeRecord(
            server="cs_server",
            view="chipscope",
            ctx=chipscope_node.ctx,
            name=name,
            hier_name=f"chipscope/{chipscope_node.props.get('Name')}",
            is_dap=not is_dpc,
            is_dpc=is_dpc,
        )
        if include_dna:
            chipscope_record.dna = get_node_dna(chipscope_node)
        yield chipscope_record


def scan_all_views(
    hw_server: ServerInfo, cs_server: ServerInfo, include_dna=True
) -> Dict[str, List[ViewRecordType]]:
    def populate_dna_or_context_dicts(rec_itr, all_view_dict_, view_dict_):
        # Helper to reduce duplication - just add nodes to the correct dict if dna may exist
        for rec in rec_itr:
            if rec.dna:
                all_view_dict_[str(rec.dna)].append(rec)
            else:
                view_dict_[rec.ctx] = rec

    def populate_context_dicts(all_view_dict_, view_dict_, jtag_ctx_, dap_ctx_):
        # Helper to reduce duplication - add nodes to correct dict without help of dna
        for ctx in list(view_dict_.keys()):
            rec = view_dict_[ctx]
            if jtag_ctx_ in ctx:
                all_view_dict_[jtag_ctx].append(rec)
                del view_dict_[ctx]
            elif dap_ctx_ and dap_ctx_ in ctx:
                all_view_dict_[jtag_ctx_].append(rec)
                del view_dict_[ctx]

    # Tracking dictionaries. As we detect nodes attached to specific devices,
    # they move from the <view>_view_ctx_dicts into the all_view_dict.
    jtag_view_ctx_dict = {}
    memory_view_ctx_dict = {}
    chipscope_view_ctx_dict = {}
    debugcore_view_ctx_dict = {}
    all_view_dict: Dict = defaultdict(list)

    # Populate the all_view_dna_dict with any nodes tha that have dna
    # values. Maintain context dictionaries for fallback matching.
    if hw_server:
        populate_dna_or_context_dicts(
            scan_jtag_view(hw_server, include_dna=include_dna), all_view_dict, jtag_view_ctx_dict
        )
        populate_dna_or_context_dicts(
            scan_memory_view(hw_server, include_dna=include_dna),
            all_view_dict,
            memory_view_ctx_dict,
        )
        populate_dna_or_context_dicts(
            scan_debugcore_view(hw_server, include_dna=include_dna),
            all_view_dict,
            debugcore_view_ctx_dict,
        )
    if cs_server:
        populate_dna_or_context_dicts(
            scan_chipscope_view(cs_server, include_dna=include_dna),
            all_view_dict,
            chipscope_view_ctx_dict,
        )

    # Remaining non-dna nodes need to be matched based on their context names.
    # First match any JTAG devices and pull them out of the mix.
    # Jtag nodes give us an easy context to match other nodes with and remove
    # some from the list.

    for jtag_ctx in list(jtag_view_ctx_dict.keys()):
        jtag_rec = jtag_view_ctx_dict[jtag_ctx]
        all_view_dict[jtag_ctx].append(jtag_rec)
        del jtag_view_ctx_dict[jtag_ctx]
        populate_context_dicts(all_view_dict, memory_view_ctx_dict, jtag_ctx, jtag_rec.dap_ctx)
        populate_context_dicts(all_view_dict, debugcore_view_ctx_dict, jtag_ctx, jtag_rec.dap_ctx)
        populate_context_dicts(all_view_dict, chipscope_view_ctx_dict, jtag_ctx, jtag_rec.dap_ctx)

    # What remains are nodes not attached to a jtag node and has no dna...
    # Here we glue the remaining nodes together based on debugcore contexts.
    # Not much verification with this... If we get here, the
    # device list may end up with duplicate devices for DAP and DPC
    # because the context matching is not perfect and there is no dna key.
    # This likely happens for XVC MM testing or emulation flows where the
    # device is not fully configured in hw_server like real hardware.

    for dc_ctx in list(debugcore_view_ctx_dict.keys()):
        dc_rec = debugcore_view_ctx_dict[dc_ctx]
        all_view_dict[dc_ctx].append(dc_rec)
        del debugcore_view_ctx_dict[dc_ctx]
        for mem_ctx in list(memory_view_ctx_dict.keys()):
            if dc_ctx in mem_ctx:
                mem_rec = memory_view_ctx_dict[mem_ctx]
                all_view_dict[dc_ctx].append(mem_rec)
                del memory_view_ctx_dict[mem_ctx]
        for cs_ctx in list(chipscope_view_ctx_dict.keys()):
            if dc_ctx in cs_ctx:
                cs_rec = chipscope_view_ctx_dict[cs_ctx]
                all_view_dict[dc_ctx].append(cs_rec)
                del chipscope_view_ctx_dict[cs_ctx]
    return all_view_dict
