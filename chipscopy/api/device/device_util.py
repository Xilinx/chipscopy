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
from collections import namedtuple, defaultdict
from typing import Optional, Dict, List

from chipscopy.client import ServerInfo
from chipscopy.client.jtagdevice import JtagCable, JtagDevice, JtagRegister
from chipscopy.client.view_info import ViewInfo
from chipscopy.dm import Node


# Tuples are created during DeviceScanner scan - used to create the DeviceSpec
_DeviceIdentificationTuple = namedtuple(
    "DeviceTracker",
    [
        "part",
        "family",
        "node_identification",
        "dna",
        "cable_context",
        "cable_name",
        "jtag_index",
        "jtag_context",
    ],
)
_DeviceNodeIdentificationTuple = namedtuple(
    "NodeTracker", ["server_type", "view_name", "name", "context", "hier_name"]
)


def _get_jtag_device_for_dna(hw_server: ServerInfo, dna_128: int) -> Optional[namedtuple]:
    # TODO: Inefficient - optimize later to reduce the number of jtag node traversals
    JtagDeviceInfo = namedtuple(
        "JtagDeviceInfo", "cable_ctx cable_name chain_index node_ctx family part ctx"
    )
    view = hw_server.get_view("jtag")
    for node in view.get_children():
        # Jtag cables live right under the jtag view.
        jtag_cable_node = view.get_node(node.ctx, JtagCable)
        if jtag_cable_node:
            jtag_index = 0
            for child in view.get_children(parent=jtag_cable_node.ctx):
                jtag_device_node = view.get_node(child.ctx, JtagDevice)
                # I assume the node order is the same order as the physical jtag chain.
                if jtag_device_node:
                    dna_128_ = get_node_dna(jtag_device_node)
                    if dna_128_ == dna_128:
                        part = jtag_device_node.props.get("Name", None)
                        family = jtag_device_node.props.get("arch_name", None)
                        jtag_cable_name = jtag_cable_node.ctx
                        jtag_cable_desc = jtag_cable_node.props.get("Description", None)
                        jtag_cable_serial = jtag_cable_node.props.get("Serial", None)
                        if jtag_cable_desc:
                            jtag_cable_name = jtag_cable_desc
                            if jtag_cable_serial:
                                jtag_cable_name += " " + jtag_cable_serial
                        return JtagDeviceInfo(
                            jtag_cable_node.ctx,
                            jtag_cable_name,
                            jtag_index,
                            jtag_device_node.ctx,
                            family,
                            part,
                            jtag_device_node.ctx,
                        )
                    jtag_index += 1
    return None


def _get_node_hier_name(view: ViewInfo, node: Node) -> str:
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
            node.update_regs(reg_names=(f"{k}",), force=True, done=None)
            int_val = int.from_bytes(v.data, byteorder="little", signed=False)
            transformed_props[str(k)] = int_val
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
        "hier_name": _get_node_hier_name(view, node),
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
        "hier_name": _get_node_hier_name(view, node),
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


def _get_children(
    server_type, view_name, view, node_hier_name, node
) -> List[_DeviceIdentificationTuple]:
    retval = list()
    for child in view.get_children(node):
        name_with_hierarchy = node_hier_name + "/" + child.props.get("Name")
        child_node_id = _DeviceNodeIdentificationTuple(
            server_type, view_name, child.props.get("Name"), child.ctx, name_with_hierarchy
        )
        retval.append(child_node_id)
        children = _get_children(server_type, view_name, view, name_with_hierarchy, child)
        if children:
            retval.extend(children)
    return retval


def get_node_dna(node: Node) -> Optional[int]:
    """Returns: 128-bit device dna value if available for the node, None otherwise."""
    dna_128 = None
    if node.props.get("node_cls") is JtagDevice:
        # jtag devices store dna as a bytestream
        if node.props.get("regs", None):
            if node.props["regs"].get("dna", None):
                # Below refreshes the dna data and makes it available
                # node.status('dna')
                node.update_regs(reg_names=("dna",), force=True, done=None)
                jtag_register = node.props["regs"]["dna"]
                bytearray_data = jtag_register.data
                dna_128 = int.from_bytes(bytearray_data, byteorder="little", signed=False)
    else:
        # Other contexts store dna as a 4-tuple of 32-bit ints
        dna_4_tuple = node.props.get("DeviceDNA", None)
        if dna_4_tuple and len(dna_4_tuple) == 4:
            dna_128 = (
                dna_4_tuple[3] << 96 | dna_4_tuple[2] << 64 | dna_4_tuple[1] << 32 | dna_4_tuple[0]
            )
    return dna_128


def _create_node_cache(hw_server: ServerInfo, cs_server: ServerInfo) -> Dict:
    node_cache_by_dna = defaultdict(list)
    for server, view_name in [
        (hw_server, "memory"),
        (hw_server, "debugcore"),
        (cs_server, "chipscope"),
    ]:
        if server:
            view = server.get_view(view_name)
            for node in view.get_all():
                if not node.props.get("Name"):
                    continue
                dna_128 = get_node_dna(node)
                if dna_128:
                    node_cache_by_dna[dna_128].append((server, view, node))
    return node_cache_by_dna


def legacy_scan_cable(
    hw_server: ServerInfo, cs_server: ServerInfo, cable_ctx: str
) -> List[_DeviceIdentificationTuple]:
    all_devices = legacy_scan_all(hw_server, cs_server)
    cable_devices = []
    for device_id in all_devices:
        if device_id.cable_context == cable_ctx:
            cable_devices.append(device_id)
    return cable_devices


def legacy_scan_all(
    hw_server: ServerInfo, cs_server: ServerInfo
) -> List[_DeviceIdentificationTuple]:
    dna_values_already_found = {}
    # Use the debug core view to figure out how many devices we have
    devices_found = []
    views_to_add = list()
    views_to_add.append(("hw_server", "jtag", hw_server.get_view("jtag")))
    views_to_add.append(("hw_server", "memory", hw_server.get_view("memory")))
    views_to_add.append(("hw_server", "debugcore", hw_server.get_view("debugcore")))
    if cs_server:
        views_to_add.append(("cs_server", "chipscope", cs_server.get_view("chipscope")))
    for (server_type, view_name, view) in views_to_add:
        # Versal debugcore will currently have 2 top level targets for a single device -
        #    "Versal" and "DPC". This is bad - but both have a common DNA value, so we can connect things together
        #    based on dna
        for node in view.get_all():
            if not node.props.get("Name"):
                continue
            dna_128 = get_node_dna(node)
            node_hier_name = f"{view_name}/{node.props.get('Name')}"
            node_id = _DeviceNodeIdentificationTuple(
                server_type=server_type,
                view_name=view_name,
                name=node.props.get("Name"),
                context=node.ctx,
                hier_name=node_hier_name,
            )
            node_id_list = [node_id]
            children = _get_children(server_type, view_name, view, node_hier_name, node)
            node_id_list.extend(children)
            if dna_128:
                # Found device dna - If this is a versal device, make sure
                # we associate the DPC and Versal top targets together
                if dna_values_already_found.get(dna_128) is None:
                    jtag_device_info = _get_jtag_device_for_dna(hw_server, dna_128)
                    if jtag_device_info:
                        # NOTE: it is possible that a single cs_server has multiple hw_server connections.
                        # In that case, jtag_device_info is None for the other hw_server nodes.
                        # We only add cs_server nodes for the correct hw_server.
                        device_id = _DeviceIdentificationTuple(
                            part=jtag_device_info.part,
                            family=jtag_device_info.family,
                            node_identification=node_id_list,
                            dna=dna_128,
                            cable_context=jtag_device_info.cable_ctx,
                            cable_name=jtag_device_info.cable_name,
                            jtag_index=jtag_device_info.chain_index,
                            jtag_context=jtag_device_info.ctx,
                        )
                        dna_values_already_found[dna_128] = device_id
                        devices_found.append(device_id)
                else:
                    # Duplicate entry - just add the name we found to the list. Happens for Versal and DPC
                    dna_values_already_found[dna_128].node_identification.extend(node_id_list)
            else:
                # No device dna on a node. Lots of reasons but this is not a node to worry about now.
                # In the future we probably need to consider how to associate nodes with no dna.
                #
                name = node.props.get("Name")
                if name.startswith("XVC:"):
                    # This is an XVC cable. Node name is in the format: "XVC:<host>:port"
                    # Use node name as a key instead of DNA for XVC cables to group things together
                    if dna_values_already_found.get(name) is None:
                        device_id = _DeviceIdentificationTuple(
                            part="xvc_defined_part",
                            family="xvc_defined_family",
                            node_identification=node_id_list,
                            dna=None,
                            cable_context=None,
                            cable_name=name,
                            jtag_index=None,
                            jtag_context=None,
                        )
                        dna_values_already_found[name] = device_id
                        devices_found.append(device_id)
                    else:
                        # Duplicate entry - just add the name we found to the list. Happens for Versal and DPC
                        dna_values_already_found[name].node_identification.extend(node_id_list)
                else:
                    # print(f"*** IGNORING NODE: {node.props.get('Name')} - {node}")
                    pass

    # Keep in a somewhat consistent sorted order by jtag cable then jtag index if possible
    devices_found.sort(key=lambda x: [x.cable_name, x.jtag_index])
    return devices_found


def updated_scan_cable(
    hw_server: ServerInfo, cs_server: ServerInfo, cable_ctx: str
) -> List[_DeviceIdentificationTuple]:
    all_devices = updated_scan_all(hw_server, cs_server)
    cable_devices = []
    for device_id in all_devices:
        if device_id.cable_context == cable_ctx:
            cable_devices.append(device_id)
    return cable_devices


def updated_scan_all(
    hw_server: ServerInfo, cs_server: ServerInfo
) -> List[_DeviceIdentificationTuple]:
    dna_values_already_found = {}
    # Use the debug core view to figure out how many devices we have
    devices_found = []
    views_to_add = list()
    views_to_add.append(("hw_server", "jtag", hw_server.get_view("jtag")))
    views_to_add.append(("hw_server", "memory", hw_server.get_view("memory")))
    views_to_add.append(("hw_server", "debugcore", hw_server.get_view("debugcore")))
    if cs_server:
        views_to_add.append(("cs_server", "chipscope", cs_server.get_view("chipscope")))
    for (server_type, view_name, view) in views_to_add:
        # Versal debugcore will currently have 2 top level targets for a single device -
        #    "Versal" and "DPC". This is bad - but both have a common DNA value, so we can connect things together
        #    based on dna
        chain_index = 0
        if view_name == "jtag":
            # In jtag view, we just want the cable and top level JtagDevice nodes - not their children.
            # This prevents the bscan-switch, axi nodes, etc from becoming devices
            # Need to order this as cable, device..., cable, device...
            nodes_to_traverse = []
            jtag_cables = view.get_children()
            for jtag_cable in jtag_cables:
                nodes_to_traverse.append(jtag_cable)
                for jtag_device in view.get_children(jtag_cable):
                    nodes_to_traverse.append(jtag_device)
        else:
            # In other views like memory, we do want all nodes recursively to be checked and added
            nodes_to_traverse = view.get_all()
        for node in nodes_to_traverse:
            if not node.props.get("Name"):
                continue
            dna_128 = get_node_dna(node)
            node_hier_name = f"{view_name}/{node.props.get('Name')}"
            node_id = _DeviceNodeIdentificationTuple(
                server_type=server_type,
                view_name=view_name,
                name=node.props.get("Name"),
                context=node.ctx,
                hier_name=node_hier_name,
            )
            node_id_list = [node_id]
            children = _get_children(server_type, view_name, view, node_hier_name, node)
            node_id_list.extend(children)
            if dna_128:
                # Found device dna - If this is a versal device, make sure
                # we associate the DPC and Versal top targets together
                if dna_values_already_found.get(dna_128) is None:
                    jtag_device_info = _get_jtag_device_for_dna(hw_server, dna_128)
                    if jtag_device_info:
                        # NOTE: it is possible that a single cs_server has multiple hw_server connections.
                        # In that case, jtag_device_info is None for the other hw_server nodes.
                        # We only add cs_server nodes for the correct hw_server.
                        device_id = _DeviceIdentificationTuple(
                            part=jtag_device_info.part,
                            family=jtag_device_info.family,
                            node_identification=node_id_list,
                            dna=dna_128,
                            cable_context=jtag_device_info.cable_ctx,
                            cable_name=jtag_device_info.cable_name,
                            jtag_index=jtag_device_info.chain_index,
                            jtag_context=jtag_device_info.ctx,
                        )
                        dna_values_already_found[dna_128] = device_id
                        devices_found.append(device_id)
                        chain_index += 1
                else:
                    # Duplicate entry - just add the name we found to the list. Happens for Versal and DPC
                    dna_values_already_found[dna_128].node_identification.extend(node_id_list)
            else:
                # No device dna on a node. Lots of reasons but this is not a node to worry about now.
                # In the future we probably need to consider how to associate nodes with no dna.
                #
                name = node.props.get("Name")
                if name.startswith("XVC:"):
                    # This is an XVC cable. Node name is in the format: "XVC:<host>:port"
                    # Use node name as a key instead of DNA for XVC cables to group things together
                    if dna_values_already_found.get(name) is None:
                        device_id = _DeviceIdentificationTuple(
                            part="xvc_defined_part",
                            family="xvc_defined_family",
                            node_identification=node_id_list,
                            dna=None,
                            cable_context=None,
                            cable_name=name,
                            jtag_index=None,
                            jtag_context=None,
                        )
                        dna_values_already_found[name] = device_id
                        devices_found.append(device_id)
                    else:
                        # Duplicate entry - just add the name we found to the list. Happens for Versal and DPC
                        dna_values_already_found[name].node_identification.extend(node_id_list)
                elif node.props.get("node_cls") is JtagCable:
                    chain_index = 0
                elif node.props.get("node_cls") is JtagDevice:
                    # This is a DNA-less jtag device - just add it as-is
                    cable_node = view.get_node(node.parent_ctx)
                    cable_name = (
                        cable_node.props.get("Description")
                        or cable_node.props.get("Name")
                        or cable_node.ctx("Name")
                    )
                    device_id = _DeviceIdentificationTuple(
                        part=node.props.get("Name"),
                        family=node.props.get("arch_name"),
                        node_identification=node_id_list,
                        dna=None,
                        cable_context=node.parent_ctx,
                        cable_name=cable_name,
                        jtag_index=chain_index,
                        jtag_context=node.ctx,
                    )
                    devices_found.append(device_id)
                    chain_index += 1
                else:
                    # print(f"*** IGNORING NODE: {node.props.get('Name')} - {node}")
                    pass

    # Keep in a somewhat consistent sorted order by jtag cable then jtag index if possible
    devices_found.sort(key=lambda x: [x.cable_context, x.jtag_index])
    return devices_found
