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
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional, DefaultDict, Union, Dict, List

from chipscopy import CoreType
from chipscopy.api._detail.ltx import Ltx
from chipscopy.api._detail.trace import Trace
from chipscopy.api.containers import QueryList
from chipscopy.api.ddr import DDR
from chipscopy.api.ibert import IBERT
from chipscopy.api.ila import ILA
from chipscopy.api.memory import Memory
from chipscopy.api.noc.noc import NocPerfmon
from chipscopy.api.pcie import PCIe
from chipscopy.api.sysmon import Sysmon
from chipscopy.api.vio import VIO
from chipscopy.client import ServerInfo
from chipscopy.client.axis_ila_core_client import AxisIlaCoreClient
from chipscopy.client.axis_pcie_core_client import AxisPCIeCoreClient
from chipscopy.client.axis_trace_core_client import AxisTraceClient
from chipscopy.client.axis_vio_core_client import AxisVIOCoreClient
from chipscopy.client.core import CoreParent
from chipscopy.client.ddrmc_client import DDRMCClient
from chipscopy.client.ibert_core_client import IBERTCoreClient
from chipscopy.client.jtagdevice import JtagDevice
from chipscopy.client.noc_perfmon_core_client import NoCPerfMonCoreClient
from chipscopy.client.sysmon_core_client import SysMonCoreClient
from chipscopy.dm import chipscope, request, Node
from chipscopy.utils.printer import printer, PercentProgressBar
from chipscopy.api.device.device_identification import DeviceIdentification


class Device:
    """The Device class represents a single Xilinx Versal device.
    Device has methods for programming, memory access, and contains the detected
    collection of debug cores. The collection of detected devices is held in
    the session - see session.devices.
    """

    # This dict maps a core.type string to the correct node class type.
    CORE_TYPE_TO_CLASS_MAP = {
        "vio": AxisVIOCoreClient,
        "ila": AxisIlaCoreClient,
        "trace": AxisTraceClient,
        # todo: remove after hw_server is updated.
        "Core": AxisTraceClient,
        "pcie": AxisPCIeCoreClient,
        "npi_nir": NoCPerfMonCoreClient,
        "ibert": IBERTCoreClient,
        "sysmon": SysMonCoreClient,
        "ddrmc_main": DDRMCClient,
    }

    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_identification: DeviceIdentification,
        disable_core_scan: bool,
    ):
        self.disable_core_scan = disable_core_scan
        self.cores_to_scan = {}  # set during discover_and_setup_cores

        self.hw_server = hw_server
        self.cs_server = cs_server
        self.device_identification = device_identification
        self.ltx = None

        self.debug_core_dict: DefaultDict[
            CoreType, QueryList[Union[VIO, ILA, PCIe, DDR, IBERT, NocPerfmon]]
        ] = defaultdict(QueryList)

        self.programming_done: bool = False
        self.programming_error: Optional[str] = None

        # The following filter_by becomes a dictionary with architecture, jtag_index, context, etc.
        # This is used when asking for a device by filter from the device list like:
        #    report_devices(session.devices.get(dna=".*1234"))
        # There is a problem with the new node identification as a list - need to flatten or something.
        # I don't think that the current filtering system will consider  list items in the dict.
        # TODO: address node_identification member of filter_by - maybe something other than loads below.
        self.filter_by = json.loads(repr(self.device_identification))

    def __str__(self):
        return str(self.device_identification)

    def __repr__(self):
        return repr(self.device_identification)

    def __getitem__(self, item):
        raw_json = repr(self.device_identification)
        parsed_json = json.loads(raw_json)
        return parsed_json[item]

    def _create_debugcore_wrapper(self, node):
        # Factory to build debug_core_wrappers
        # Instantiate debug core wrappers for a known core type. The wrapper gets attached to a
        # node for safe keeping. Any time we need to grab a debug core wrapper (like ILA)
        # it is available on the node using
        #     wrapper = self._get_client_wrapper(node)
        if node.type == "ila":
            debug_core_wrapper = ILA(node, self, ltx=self.ltx)
        elif node.type == "vio":
            debug_core_wrapper = VIO(node, ltx=self.ltx)
        elif node.type == "trace":
            debug_core_wrapper = Trace(node)
        # todo: remove after hw_server is updated.
        elif node.type == "Core":
            debug_core_wrapper = Trace(node)
        elif node.type == "pcie":
            debug_core_wrapper = PCIe(node)
        elif node.type == "npi_nir":
            debug_core_wrapper = NocPerfmon(node)
        elif node.type == "ibert":
            debug_core_wrapper = IBERT(node)
        elif node.type == "sysmon":
            debug_core_wrapper = Sysmon(node)
        elif node.type == "ddrmc_main":
            debug_core_wrapper = DDR(node)
        else:
            # TODO: extend this factory to other core types with a plugin model for additional types
            debug_core_wrapper = None
        return debug_core_wrapper

    def _find_all_debugcore_nodes(self) -> Dict:
        # Traverse the chipscope view for debug cores in this device.
        # Returns a dict mapping core_types to a list of found nodes.
        # Notes are returned in upgraded form.
        #   Example return:
        #         {
        #           AxisIlaCoreClient: [ila_node_1, ila_node_2, ...],
        #           AxisVIOCoreClient: [vio_node_1, vio_node_2, ...],
        #           ...
        #         }
        # The first time calling this function is slow because nodes have
        # not been upgraded yet. Slow is around 1 second. Subsequent calls are
        # faster, around 1 ms.
        #
        # Best to avoid calling this function in an inner loop.
        #
        cs_view = self.cs_server.get_view(chipscope)
        found_cores = defaultdict(list)
        # Using the self.chipscope_node restricts nodes to this device only
        for cs_node in cs_view.get_children(self.chipscope_node):
            if cs_node.type == "debug_hub":
                debug_hub_children = cs_view.get_children(cs_node)
                for child in debug_hub_children:
                    if self.cores_to_scan.get(child.type, True):
                        core_class_type = Device.CORE_TYPE_TO_CLASS_MAP.get(child.type, None)
                        if core_class_type and core_class_type.is_compatible(child):
                            upgraded_node = cs_view.get_node(child.ctx, core_class_type)
                            found_cores[core_class_type].append(upgraded_node)
            else:
                if self.cores_to_scan.get(cs_node.type, True):
                    core_class_type = Device.CORE_TYPE_TO_CLASS_MAP.get(cs_node.type, None)
                    if core_class_type and core_class_type.is_compatible(cs_node):
                        upgraded_node = cs_view.get_node(cs_node.ctx, core_class_type)
                        found_cores[core_class_type].append(upgraded_node)
        return found_cores

    def _get_debug_core_wrappers(self, core_type) -> QueryList:
        # Returns a QueryList of the debug_core_wrappers matching the given core_type
        #   core_type is a class from CORE_TYPE_TO_CLASS_MAP
        #   returned wrapper_type is ILA, VIO, etc wrapping the node
        #
        # debug_core_wrappers are initialized if they don't yet exist for the
        # node. After initialization, they are hung on the node for future reference.
        # This is convenient because their lifecycle is tied to the node.
        found_cores = QueryList()
        all_debug_core_nodes = self._find_all_debugcore_nodes()
        for node in all_debug_core_nodes.get(core_type, []):
            debug_core_wrapper = Device._get_client_wrapper(node)
            if debug_core_wrapper is None:
                # Lazy debugcore initialization here.
                # Initialization happens the first time we access the debug core.
                debug_core_wrapper = self._create_debugcore_wrapper(node)
            if debug_core_wrapper:
                self._set_client_wrapper(node, debug_core_wrapper)
            else:
                # TODO: Hasn't happened yet - is this an error, warning, or something else?
                pass
            # Now the node should have a proper debug_core_wrapper attached.
            if Device._get_client_wrapper(node):
                found_cores.append(Device._get_client_wrapper(node))
        return found_cores

    @property
    def jtag_node(self) -> JtagDevice:
        # Low level hw_server jtag node access
        if self.hw_server:
            discovery_node = self.device_identification.find_jtag_node(self.hw_server)
        else:
            raise RuntimeError("No hw_server server connection. Could not get jtag view")
        return discovery_node

    @property
    def debugcore_node(self) -> Node:
        # Low level hw_server debugcore access
        if self.hw_server:
            discovery_node = self.device_identification.find_debugcore_node(self.hw_server)
        else:
            raise RuntimeError("No hw_server server connection. Could not get debugcore view")
        return discovery_node

    @property
    def chipscope_node(self) -> CoreParent:
        # Low level cs_server chipscope access
        if self.cs_server:
            discovery_node = self.device_identification.find_chipscope_node(self.cs_server)
        else:
            raise RuntimeError("No chipscope server connection. Could not get chipscope view")
        return discovery_node

    @property
    def ibert_cores(self) -> QueryList[IBERT]:
        """Returns:
        list of detected IBERT cores in the device"""
        return self._get_debug_core_wrappers(IBERTCoreClient)

    @property
    def vio_cores(self) -> QueryList[VIO]:
        """Returns:
        list of detected VIO cores in the device"""
        return self._get_debug_core_wrappers(AxisVIOCoreClient)

    @property
    def ila_cores(self) -> QueryList[ILA]:
        """Returns:
        list of detected ILA cores in the device"""
        return self._get_debug_core_wrappers(AxisIlaCoreClient)

    @property
    def trace_cores(self) -> QueryList[Trace]:
        """Returns:
        list of detected Trace cores in the device"""
        return self._get_debug_core_wrappers(AxisTraceClient)

    @property
    def pcie_cores(self) -> QueryList[PCIe]:
        """Returns:
        list of detected PCIe cores in the device"""
        return self._get_debug_core_wrappers(AxisPCIeCoreClient)

    @property
    def noc_core(self) -> QueryList[NocPerfmon]:
        """Returns:
        List with one NOC core for the device"""
        return self._get_debug_core_wrappers(NoCPerfMonCoreClient)

    @property
    def ddrs(self):
        """Returns:
        list of detected DDRMC cores in the device"""
        return self._get_debug_core_wrappers(DDRMCClient)

    @property
    def sysmon_root(self) -> QueryList[Sysmon]:
        """Returns:
        List with one SysMon core for the device"""
        return self._get_debug_core_wrappers(SysMonCoreClient)

    @property
    # TODO: @chipscopy_deprecated("Use alternative session.mem.all() instead.")
    def memory_target_names(self):
        """Returns:
        list of supported memory targets"""
        valid_memory_targets = (
            r"(Versal .*)|(DPC)|(APU)|(RPU)|(PPU)|(PSM)|(Cortex.*)|(MicroBlaze.*)"
        )
        memory_target_names = list()
        memory_node_list = self.device_identification.get_memory_target_nodes(self.hw_server)
        for memory_node in memory_node_list:
            memory_target_name = memory_node.props.get("Name")
            if len(memory_target_name) > 0 and re.search(valid_memory_targets, memory_target_name):
                memory_target_names.append(memory_target_name)
        return memory_target_names

    @property
    def memory(self) -> QueryList[Memory]:
        """Returns:
        the memory access for the device"""
        target_nodes = self.device_identification.get_memory_target_nodes(self.hw_server)
        memory_node_list = QueryList()
        for node in target_nodes:
            if Memory.is_compatible(node):
                memory_node_list.append(node)
        return memory_node_list

    # ----------------------------------------------------------------------------------------------
    def reset(self):
        jtag_programming_node = self.device_identification.find_jtag_node(self.hw_server)
        assert jtag_programming_node is not None
        jtag_programming_node.future().reset()
        # Wait an additional 500ms just to be safe. I believe hw_server has a 200ms delay - had a couple of issues
        # so added some extra time.
        time.sleep(0.5)

    def program(
        self,
        pdi_file_path: Union[str, Path],
        *,
        show_progress_bar: bool = True,
        done: request.DoneFutureCallback = None,
    ):
        """
        Program the device with a given PDI file.

        Args:
            pdi_file_path: PDI file path
            show_progress_bar: False if the progress bar doesn't need to be shown
            done: Optional async future callback
        """
        program_future = request.CsFutureSync(done)

        if isinstance(pdi_file_path, str):
            pdi_file_path = Path(pdi_file_path)

        if not pdi_file_path.exists():
            raise FileNotFoundError(f"PDI file at {str(pdi_file_path.resolve())} doesn't exists!")

        printer(f"Programming PDI file {str(pdi_file_path.resolve())}\n", level="info")

        progress = PercentProgressBar()
        progress.add_task(
            description="Device program progress",
            status=PercentProgressBar.Status.STARTING,
            visible=show_progress_bar,
        )

        def progress_update(future):
            progress.update(
                completed=future.progress * 100, status=PercentProgressBar.Status.IN_PROGRESS
            )

        def done_programming(future):
            if future.error is not None:
                progress.update(status=PercentProgressBar.Status.ABORTED)
            else:
                progress.update(completed=100, status=PercentProgressBar.Status.DONE)

            self.programming_error = future.error
            self.programming_done = True
            if future.error:
                program_future.set_exception(future.error)
            else:
                program_future.set_result(None)

        def finalize_program():
            if self.programming_error is not None:
                raise RuntimeError(self.programming_error)

        # Go through list of possible jtag configurable devices - when we find our matching context,
        # program it. This is versal specific. It will need work when we add ultrascale.
        # One problem at a time...
        jtag_programming_node = self.device_identification.find_jtag_node(self.hw_server)
        assert jtag_programming_node is not None
        # TODO: Log the jtag node information to a log or something that we are about to program
        jtag_programming_node.future().reset()
        jtag_programming_node.future(
            progress=progress_update, done=done_programming, final=finalize_program
        ).config(str(pdi_file_path.resolve()))

        return program_future if done else program_future.result

    @staticmethod
    def _set_client_wrapper(node, api_client_wrapper):
        # Tacks a wrapper onto a node for tracking. Always call this
        # instead of setting directly on node - in case we change the
        # client wrapper tracking process.
        node.api_client_wrapper = api_client_wrapper

    @staticmethod
    def _get_client_wrapper(node):
        # Gets the tacked on wrapper from a node.
        return node.api_client_wrapper

    def discover_and_setup_cores(
        self,
        *,
        hub_address_list: Optional[List[int]] = None,
        ltx_file: str = None,
        ila_scan: bool = True,
        vio_scan: bool = True,
        noc_scan: bool = False,
        ddr_scan: bool = True,
        pcie_scan: bool = True,
        ibert_scan: bool = False,
        sysmon_scan: bool = False,
    ):
        """Scan device for debug cores. This may take some time depending on
        what gets scanned.

        Args:

            hub_address_list: List of debug hub addresses to scan
            ltx_file: LTX file (which contains debug hub addresses)
            ila_scan: True=Scan Device for ILAs
            vio_scan: True=Scan Device for VIOs
            ibert_scan: True=Scan Device for IBERTs
            pcie_scan: True=Scan Device for PCIEs
            noc_scan: True=Scan Device for NOC
            ddr_scan: True=Scan Device for DDRs
            sysmon_scan: True=Scan Device for System Monitor
        """

        # TODO: Cleanup: Could we pass the <core>_scan optional args as a dict or something?

        # Selectively disable scanning of cores depending on what comes in
        # This is second priority to the disable_core_scan in __init__.
        self.cores_to_scan = {}
        if self.disable_core_scan:
            for core_name in Device.CORE_TYPE_TO_CLASS_MAP.keys():
                self.cores_to_scan[core_name] = False
        else:
            self.cores_to_scan = {
                "ila": ila_scan,
                "vio": vio_scan,
                "npi_nir": noc_scan,
                "ddrmc_main": ddr_scan,
                "pcie": pcie_scan,
                "ibert": ibert_scan,
                "sysmon": sysmon_scan,
            }

        if not self.cs_server:
            raise RuntimeError("cs_server is not connected")

        self.ltx = None
        # Erase any old cores lingering from a previously detected run
        self.debug_core_dict.clear()

        # Make sure debug_hub_addrs is a list of hub addresses.
        # It may come as an int or a list or None
        if isinstance(hub_address_list, int):
            hub_address_list = [hub_address_list]
        if not hub_address_list:
            hub_address_list = []

        if ltx_file:
            self.ltx = Ltx()
            self.ltx.parse_file(ltx_file)
            hub_address_list.extend(self.ltx.get_debug_hub_addresses())
            # Remove any duplicate hub addresses in list, in case same one
            # was passed to function as well as in ltx
            # Below is a quick python trick to uniquify a list.
            hub_address_list = list(dict.fromkeys(hub_address_list))

        # Set up all debug cores in hw_server for the given hub addresses
        # Do this by default unless the user has explicitly told us not to with
        # "disable_core_scan" as an argument.
        if not self.disable_core_scan:
            # setup_debug_cores can take a while...
            self.chipscope_node.setup_cores(debug_hub_addrs=hub_address_list)

    def memory_write(self, address: int, values: List[int], *, size="w", target=None):
        """Write list of values to given memory address. This method is slow because it locates the memory context
        in the target tree every time. If you want to execute a large number of memory operations, grab a memory
        context and do the operations in batch.

        Note: This method should not be used in inner loops. It is not the fastest because it looks up
              the memory target every time. Inner loops should just call the find_memory_target once.
        """
        node = self.device_identification.find_memory_target(self.hw_server, target)
        node.memory_write(address=address, values=values, size=size)

    def memory_read(self, address: int, num: int = 1, *, size="w", target=None) -> List[int]:
        """Read num values from given memory address.  This method is slow because it locates the memory context
        in the target tree every time. If you want to execute a large number of memory operations, grab a memory
        context and do all the operations in batch.

        Note: This method should not be used in inner loops. It is not the fastest because it looks up
              the memory target every time. Inner loops should just call the find_memory_target once.
        """
        node = self.device_identification.find_memory_target(self.hw_server, target)
        retval = node.memory_read(address=address, num=num, size=size)
        return retval

    def _dpc_read_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        """
        Reads byte data from memory, using the DPC.

        Args:
            address (int): Start address
            data (bytearray): result buffer which gets filled with read data.
            offset (int): start index in *data* to start write to.
            byte_size (int): Number of bytes to read. Default is the size of the *data* buffer.
            show_progress_bar (bool): Show if True.
        """
        node = self.debugcore_node
        if not show_progress_bar:
            node.read_bytes(address, data, offset, byte_size)
            return

        # With progress bar
        transfer_byte_count = byte_size if byte_size else len(data)
        desc = (
            f"Transferring {transfer_byte_count/(1024 * 1024):0.1f} MB "
            f"[bold](Read {hex(address)})[/]"
        )

        bar = PercentProgressBar()
        bar.add_task(description=desc, status=PercentProgressBar.Status.STARTING)

        try:
            node.read_bytes(
                address,
                data,
                offset,
                byte_size,
                progress=lambda progress: bar.update(
                    completed=int(progress * 100), status=PercentProgressBar.Status.IN_PROGRESS
                ),
            )
        except Exception as ex:
            bar.update(status=PercentProgressBar.Status.ABORTED)
            raise ex

        bar.update(status=PercentProgressBar.Status.DONE)

    def _dpc_write_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        """
        Write byte data from memory, using the DPC.

        Args:
            address (int): Start address
            data (bytearray): data to write.
            offset (int): start index in *data* to start write from.
            byte_size (int): Number of bytes to write. Default is the size of the *data* buffer.
            show_progress_bar (bool): Show if True.
        """
        node = self.debugcore_node
        if not show_progress_bar:
            node.write_bytes(address, data, offset, byte_size)
            return

        # With progress bar
        transfer_byte_count = byte_size if byte_size else len(data)
        desc = (
            f"Transferring {transfer_byte_count/(1024 * 1024):0.1f} MB "
            f"[bold](Write {hex(address)})[/]"
        )

        bar = PercentProgressBar()
        bar.add_task(description=desc, status=PercentProgressBar.Status.STARTING)

        try:
            node.write_bytes(
                address,
                data,
                offset,
                byte_size,
                progress=lambda progress: bar.update(
                    completed=int(progress * 100), status=PercentProgressBar.Status.IN_PROGRESS
                ),
            )
        except Exception as ex:
            bar.update(status=PercentProgressBar.Status.ABORTED)
            raise ex

        bar.update(status=PercentProgressBar.Status.DONE)
