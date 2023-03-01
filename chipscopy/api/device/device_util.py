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
#

"""device_utils.py -

Collection of utility functions

"""
from typing import Optional

from chipscopy.client import ServerInfo
from chipscopy.client.jtagdevice import JtagDevice, JtagRegister
from chipscopy.client.view_info import ViewInfo
from chipscopy.dm import Node


def get_node_hier_name(view: ViewInfo, node: Node) -> str:
    name = node.props["Name"]
    while node.parent_ctx:
        prev_node = node
        node = view.get_node(node.parent_ctx)
        if node == prev_node:
            break
        parent_name = node.props["Name"]
        name = f"{parent_name}/{name}"
    return name


def copy_node_props(node: Node, props: dict) -> dict:
    transformed_props = {}
    for k, v in props.items():
        if type(v) == int or type(v) == str or type(v) == bool:
            transformed_props[str(k)] = v
        elif type(v) == JtagRegister:
            try:
                node.update_regs(reg_names=(f"{k}",), force=True, done=None)
                int_val = int.from_bytes(v.data, byteorder="little", signed=False)
                transformed_props[str(k)] = int_val
            except Exception:  # noqa
                pass
        elif type(v) == dict:
            transformed_props[str(k)] = copy_node_props(node, v)
        elif type(v) == bytearray:
            int_val = int.from_bytes(v, byteorder="little", signed=False)
            transformed_props[str(k)] = int_val
        else:
            transformed_props[str(k)] = str(v)
    return transformed_props


def _create_jtag_node_dict(
    server_name: str,
    view_name: str,
    jtag_cable_ctx: str,
    jtag_index: int,
    view: ViewInfo,
    node: Node,
) -> dict:
    children = list(view.get_children(node))
    jtag_node_dict = {
        "server": server_name,
        "view": view_name,
        "ctx": node.ctx,
        "dna": get_node_dna(node),
        "family": node.props.get("arch_name", None),
        "name": node.props["Name"],
        "hier_name": get_node_hier_name(view, node),
        "jtag_cable_ctx": jtag_cable_ctx,
        "jtag_index": jtag_index,
        "props": copy_node_props(node, node.props),
        "parent_ctx": node["ParentID"],
        "children": {
            child.ctx: _create_jtag_node_dict(
                server_name, view_name, jtag_cable_ctx, jtag_index, view, child
            )
            for child in children
        },
    }
    return jtag_node_dict


def get_jtag_view_dict(hw_server: ServerInfo) -> dict:
    jtag_dict = {}
    server_name = "hw_server"
    view_name = "jtag"
    view = hw_server.get_view(view_name)
    for jtag_cable in view.get_children():
        device_dict = {}
        jtag_cable_ctx = jtag_cable.ctx
        device_nodes_to_process = list(view.get_children(jtag_cable))
        jtag_index = 0
        for node in device_nodes_to_process:
            device_dict[node.ctx] = _create_jtag_node_dict(
                server_name, view_name, jtag_cable_ctx, jtag_index, view, node
            )
        jtag_dict[jtag_cable_ctx] = {
            "name": jtag_cable.props["Name"],
            "ctx": jtag_cable_ctx,
            "devices": device_dict,
            "props": copy_node_props(jtag_cable, jtag_cable.props),
        }
    return jtag_dict


def _create_basic_node_dict(server_name: str, view_name: str, view: ViewInfo, node: Node) -> dict:
    children = list(view.get_children(node))
    debugcore_node_dict = {
        "server": server_name,
        "view": view_name,
        "ctx": node.ctx,
        "dna": get_node_dna(node),
        "name": node.props["Name"],
        "hier_name": get_node_hier_name(view, node),
        "props": copy_node_props(node, node.props),
        "children": {
            child.ctx: _create_basic_node_dict(server_name, view_name, view, child)
            for child in children
        },
    }
    return debugcore_node_dict


def _get_basic_view_dict(server: ServerInfo, server_name, view_name) -> dict:
    device_dict = {}
    view = server.get_view(view_name)
    for node in view.get_children():
        device_dict[node.ctx] = _create_basic_node_dict(server_name, view_name, view, node)
    return device_dict


def get_memory_view_dict(hw_server: ServerInfo) -> dict:
    return _get_basic_view_dict(hw_server, "hw_server", "memory")


def get_debugcore_view_dict(hw_server: ServerInfo) -> dict:
    return _get_basic_view_dict(hw_server, "hw_server", "debugcore")


def get_chipscope_view_dict(cs_server: ServerInfo) -> dict:
    return _get_basic_view_dict(cs_server, "cs_server", "chipscope")


def get_node_dna(node: Node) -> Optional[int]:
    """Returns: 128-bit device dna value if available for the node, None otherwise."""
    dna_128 = None
    if node.props.get("node_cls") is JtagDevice:
        # jtag devices store dna as a bytestream
        if node.props.get("regs", None):
            if node.props["regs"].get("dna", None):
                # Below refreshes the dna data and makes it available
                # node.status('dna')
                try:
                    node.update_regs(reg_names=("dna",), force=True, done=None)
                    jtag_register = node.props["regs"]["dna"]
                    bytearray_data = jtag_register.data
                    dna_128 = int.from_bytes(bytearray_data, byteorder="little", signed=False)
                except Exception:  # noqa
                    dna_128 = None
    else:
        # Other contexts store dna as a 4-tuple of 32-bit ints
        dna_4_tuple = node.props.get("DeviceDNA", None)
        if dna_4_tuple and len(dna_4_tuple) == 4:
            dna_128 = (
                dna_4_tuple[3] << 96 | dna_4_tuple[2] << 64 | dna_4_tuple[1] << 32 | dna_4_tuple[0]
            )
    return dna_128
