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
from typing import Optional, List

from chipscopy.client.jtagdevice import JtagCable, JtagDevice
from chipscopy.api.device.device_identification import (
    _DeviceIdentificationTuple,
    _DeviceNodeIdentificationTuple,
    DeviceIdentification,
)
from chipscopy.api.device.device import Device


class DeviceScanner:
    """This is a utility to scan for live devices in hardware. It is used by the Session when creating the
    initial list of devices or rescanning hardware.

    scan_devices() generates a convenient list of DeviceIdentification named tuples based on the hw_server and
        cs_server connections.
    """

    def __init__(self, hw_server, cs_server):
        """
        Args:
            hw_server: hardware server
            cs_server: chipscope server(optional)
        """
        self.hw_server = hw_server
        self.cs_server = cs_server
        self.device_scan_results: Optional[List[DeviceIdentification]] = None

    def __repr__(self):
        device_identification_list = self.get_scan_results()
        return device_identification_list.__repr__()

    def __str__(self):
        raw_json = self.__repr__()
        parsed = json.loads(raw_json)
        retval = json.dumps(parsed, indent=4, sort_keys=True)
        return retval

    def __iter__(self):
        return self.device_scan_results.__iter__()

    def get_scan_results(self):
        if not self.device_scan_results:
            self.scan_devices()
        return self.device_scan_results

    @staticmethod
    def _get_children(server_type, view_name, view, node_hier_name, node):
        retval = list()
        for child in view.get_children(node):
            name_with_hierarchy = node_hier_name + "/" + child.props.get("Name")
            child_node_id = _DeviceNodeIdentificationTuple(
                server_type, view_name, child.props.get("Name"), child.ctx, name_with_hierarchy
            )
            retval.append(child_node_id)
            children = DeviceScanner._get_children(
                server_type, view_name, view, name_with_hierarchy, child
            )
            if children:
                retval.extend(children)
        return retval

    def scan_devices(self):
        """Query the hw_server for connected devices. Creates a list of devices found and connects together
        the associated contexts across jtag, memory, debugcore, and chipscope views.
        This is a convenience for finding and organizing nodes that may be living in unexpected places
        like DPC and Versal both living at the top level of a device. We figure it out here so the user
        doesn't have to.

        Upon successful scan completion, self.device_scan_results is populated with the scan results.

        TODO: Non versal device scanning
        """
        dna_values_already_found = {}
        # Use the debug core view to figure out how many devices we have
        devices_found = []
        views_to_add = list()
        views_to_add.append(("hw_server", "jtag", self.hw_server.get_view("jtag")))
        views_to_add.append(("hw_server", "memory", self.hw_server.get_view("memory")))
        views_to_add.append(("hw_server", "debugcore", self.hw_server.get_view("debugcore")))
        if self.cs_server:
            views_to_add.append(("cs_server", "chipscope", self.cs_server.get_view("chipscope")))
        for (server_type, view_name, view) in views_to_add:
            # Versal debugcore will currently have 2 top level targets in the chipscope and debugcore and memory views
            # Versal and DPC. Both will have the same DNA value so we can connect things together based on dna
            for node in view.get_all():
                if not node.props.get("Name"):
                    continue
                dna_128 = DeviceScanner.get_device_dna(node)
                node_hier_name = f"{view_name}/{node.props.get('Name')}"
                node_id = _DeviceNodeIdentificationTuple(
                    server_type=server_type,
                    view_name=view_name,
                    name=node.props.get("Name"),
                    context=node.ctx,
                    hier_name=node_hier_name,
                )
                node_id_list = [node_id]
                children = DeviceScanner._get_children(
                    server_type, view_name, view, node_hier_name, node
                )
                node_id_list.extend(children)
                if dna_128:
                    # Found device dna - this is a versal device. Using the dna, make sure we associate the DPC and
                    # Versal together to know we are operating on the same device
                    if dna_values_already_found.get(dna_128) is None:
                        try:
                            (
                                jtag_cable_context,
                                jtag_cable_name,
                                jtag_index,
                            ) = DeviceScanner.get_jtag_index_for_dna(self.hw_server, dna_128)
                        except LookupError:
                            jtag_cable_context = None
                            jtag_cable_name = None
                            jtag_index = -1
                        device_id = _DeviceIdentificationTuple(
                            architecture="versal",
                            node_identification=node_id_list,
                            dna=dna_128,
                            cable_context=jtag_cable_context,
                            cable_name=jtag_cable_name,
                            jtag_index=jtag_index,
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
                        # TODO: STill more work here - this is hardcoded for versal right now.
                        if dna_values_already_found.get(name) is None:
                            device_id = _DeviceIdentificationTuple(
                                architecture="versal",
                                node_identification=node_id_list,
                                dna=None,
                                cable_context=None,
                                cable_name=name,
                                jtag_index=None,
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
        self.device_scan_results = list()
        for device_tracker_tuple in devices_found:
            device_tracker = DeviceIdentification(device_tracker_tuple)
            self.device_scan_results.append(device_tracker)

    @staticmethod
    def get_jtag_index_for_dna(hw_server, dna_128: int):
        """Returns the jtag cable context and device index in the chain given the 128-bit device dna"""
        view = hw_server.get_view("jtag")
        for node in view.get_children():
            # Jtag cables live right under the jtag view.
            jtag_cable_node = view.get_node(node.ctx, JtagCable)
            if jtag_cable_node:
                jtag_index = 0
                for child in view.get_children(parent=jtag_cable_node.ctx):
                    jtag_device_node = view.get_node(child.ctx, JtagDevice)
                    # Here I assume the node order is the same order as the physical jtag chain.
                    # TODO: Verify chain ordering assumption is the same as child nodes returned from get_children()
                    if jtag_device_node:
                        dna_128_ = DeviceScanner.get_device_dna(jtag_device_node)
                        if dna_128_ == dna_128:
                            jtag_cable_name = jtag_cable_node.ctx
                            jtag_cable_desc = jtag_cable_node.props.get("Description", None)
                            jtag_cable_serial = jtag_cable_node.props.get("Serial", None)
                            if jtag_cable_desc:
                                jtag_cable_name = jtag_cable_desc
                                if jtag_cable_serial:
                                    jtag_cable_name += " " + jtag_cable_serial
                            return jtag_cable_node.ctx, jtag_cable_name, jtag_index
                        jtag_index += 1
        raise LookupError(f"dna value {dna_128} did not match any jtag device")

    @staticmethod
    def get_device_dna(node):
        """
        Returns: 128-bit device dna value if available for the node, None otherwise.
        """
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
                    dna_4_tuple[3] << 96
                    | dna_4_tuple[2] << 64
                    | dna_4_tuple[1] << 32
                    | dna_4_tuple[0]
                )
        return dna_128
