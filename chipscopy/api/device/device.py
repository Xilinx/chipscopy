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
import json
import re
import time
from collections import defaultdict, deque
from enum import Enum
from pathlib import Path
from typing import Optional, Union, Dict, List, Set, Any, NewType, Literal
from struct import pack, unpack

from chipscopy.api import DMNodeListener
from chipscopy.api._detail.ltx import parse_ltx_files
from chipscopy.api._detail.trace import Trace
from chipscopy.api.containers import QueryList
from chipscopy.api.ddr.ddr import DDR
from chipscopy.api.device.device_spec import DeviceSpec
from chipscopy.api.hbm.hbm import HBM
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
from chipscopy.client.hbm_client import HBMClient
from chipscopy.client.ibert_core_client import IBERTCoreClient
from chipscopy.client.jtagdevice import JtagCable, JtagDevice
from chipscopy.client.mem import MemoryNode
from chipscopy.client.noc_perfmon_core_client import NoCPerfMonCoreClient
from chipscopy.client.sysmon_core_client import SysMonCoreClient
from chipscopy.dm import chipscope, request, Node
from chipscopy.utils.printer import printer, PercentProgressBar
from chipscopy.api.device.device_scanner import (
    scan_all_views,
)
from chipscopy.api.device.device_util import copy_node_props
from chipscopy.utils.logger import log


class FeatureNotAvailableError(Exception):
    def __init__(self):
        super().__init__("Feature not available on this architecture")


class DeviceFamily(Enum):
    GENERIC = "generic"
    UPLUS = "ultrascaleplus"
    VERSAL = "versal"
    XVC = "xvc"

    @staticmethod
    def get_family_for_name(family_name: str) -> "DeviceFamily":
        if family_name == "versal":
            return DeviceFamily.VERSAL
        elif family_name.startswith("xvc"):
            return DeviceFamily.XVC
        elif family_name.endswith("uplus"):
            return DeviceFamily.UPLUS
        else:
            return DeviceFamily.GENERIC


class Device:
    """The Device class represents a single device. It is the base class for other
    Xilinx or Generic devices. Depending on the device type, some features may be available or unavailable.

    Device has the kitchen sink of properties functions to make documentation and type hints easy.
    Child classes raise FeatureNotAvailable for functions they do not support.
    """

    _CORE_TYPE_TO_CLASS_MAP = {
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
        "hbm": HBMClient,
    }

    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_spec: DeviceSpec,
        disable_core_scan: bool,
        disable_cache: bool,
    ):
        self.hw_server = hw_server
        self.cs_server = cs_server

        self._device_spec = device_spec
        self.default_target: Literal["DPC", "DAP"] = "DPC"

        self.family_name = self._device_spec.get_arch_name()
        self.device_family = DeviceFamily.get_family_for_name(self.family_name)
        self.part_name = self._device_spec.get_part_name()
        self.dna = self._device_spec.get_dna()
        self.jtag_index = self._device_spec.jtag_index

        self.disable_core_scan = disable_core_scan
        self._disable_cache = disable_cache

        self.ltx = None
        self.ltx_sources = []
        self.cores_to_scan = {}  # set during discover_and_setup_cores
        self.programming_error: Optional[str] = None  # Keep error for query after programming
        self.programming_done: bool = False

        # The following filter_by becomes a dictionary with architecture, jtag_index, context, etc.
        # This is used when asking for a device by filter from the device list like:
        #    report_devices(session.devices.get(dna=".*1234"))
        # Needs improvement because QueryList filtering does not work with hierarchy
        # Should always be the last part of __init__ because of to_dict() call...
        self.filter_by = self.to_dict()

    def __str__(self) -> str:
        return f"{self.part_name}:{self.dna}:{self.context}"

    def __repr__(self) -> str:
        return self.to_json()

    def __getitem__(self, item):
        props = self.to_dict()
        if item in props:
            return props[item]
        else:
            raise AttributeError(f"No property {str(item)}")

    def node_callback(self, action: DMNodeListener.NodeAction, node: Node, props: Optional[Set]):
        def owns_context(self, node_ctx: str):
            """Returns true if the node_ctx is managed by this device"""
            if node_ctx in [self.jtag_node, self.device_node]:
                return True
            else:
                return False

        pass
        # TODO: Implement for dynamic node tracking
        # if action in [
        #     DMNodeListener.NodeAction.NODE_CHANGED,
        #     DMNodeListener.NodeAction.NODE_REMOVED,
        # ]:
        #     # Device properties are cached until an event indicates something
        #     # changed that needs properties to be reread from hardware.
        #     cache_clear_contexts = set()
        #     if self.device_node:
        #         cache_clear_contexts.add(self.device_node.ctx)
        #     if self.jtag_node:
        #         cache_clear_contexts.add(self.jtag_node.ctx)
        #     if self.debugcore_node:
        #         cache_clear_contexts.add(self.debugcore_node.ctx)
        #     if self.chipscope_node:
        #         cache_clear_contexts.add(self.chipscope_node.ctx)
        #     if node.ctx in cache_clear_contexts:
        #         # Mark the properties as invalid if any hardware node changed that could affect the values.
        #         # This will force a re-read next time the properties are accessed through to_dict() for instance.
        #         # self._props_are_valid = False
        #         # print("****** node_callback:", action, node, node.ctx)
        #         pass
        # elif action == DMNodeListener.NodeAction.NODE_ADDED:
        #     # print("****** node_callback:", action, node, node.ctx)
        #     pass

    def scan_props(self) -> Dict[str, Any]:
        props = {}
        if self.hw_server and self.jtag_node:
            node = self.jtag_node
            props["jtag"] = copy_node_props(node, node.props)
        props["is_valid"] = self.is_valid
        props["context"] = self.context
        props["is_programmed"] = self.is_programmed
        props["is_programmable"] = self.is_programmable
        props["part"] = self.part_name
        props["family"] = self.family_name
        props["dna"] = self.dna
        props["jtag_index"] = self.jtag_index
        props["cable_context"] = self._device_spec.jtag_cable_ctx
        props["jtag_context"] = self._device_spec.jtag_device_ctx
        props["cable_name"] = self._device_spec.get_jtag_cable_name()
        props = dict(sorted(props.items()))  # noqa
        return props

    def to_dict(self) -> Dict:
        """Returns a dictionary representation of the device data"""
        # TODO: Cache results to make this faster
        props = self.scan_props()
        return props

    def to_json(self) -> str:
        """Returns a json representation of the device data"""
        raw_json = json.dumps(self.to_dict(), indent=4, default=lambda o: str(o))
        return raw_json

    # NODE / LOW LEVEL

    @property
    def context(self) -> str:
        """Returns the unique context for this device. Normally this is the
        jtag node context. If this device is not on a jtag chain, the top
        level device context will be a non-jtag node.
        """
        return self._device_spec.device_ctx

    @property
    def is_programmed(self) -> bool:
        """Returns True if this Device is programmed, False otherwise."""
        # TODO: Queries hardware for jtag program status. This could be slow -
        # is there a way to collect this once, then track by subsequent events pushed from
        # the hw_server if we detect DONE went low?
        is_programmed_ = False
        try:
            node = self.jtag_node
            is_programmable = node.props.get("is_programmable")
            if is_programmable:
                regs = node.props.get("regs")
                if regs:
                    jtag_status = node.props.get("regs").get("jtag_status")
                    config_status = node.props.get("regs").get("config_status")
                    if jtag_status:
                        node.update_regs(reg_names=("jtag_status",), force=True, done=None)
                        done_reg = jtag_status.fields["DONE"]
                        is_programmed_ = done_reg["value"] == 1
                    elif config_status:
                        node.update_regs(reg_names=("config_status",), force=True, done=None)
                        done_reg = config_status.fields["DONE_PIN"]
                        is_programmed_ = done_reg["value"] == 1
        except Exception:  # noqa
            is_programmed_ = False
        return is_programmed_

    @property
    def is_programmable(self) -> bool:
        """Returns True if this Device is programmable, False otherwise"""
        is_programmable_ = False
        node = self.jtag_node
        if node:
            return node.props.get("is_programmable", False)

    @property
    def is_valid(self) -> bool:
        """Returns True if this Node is valid, False otherwise."""
        return self._device_spec.is_valid

    @property
    def jtag_cable_node(self) -> Optional[JtagCable]:
        """Low level TCF node access - For advanced use"""
        return self._device_spec.get_jtag_cable_node()

    @property
    def jtag_node(self) -> Optional[JtagDevice]:
        """Low level TCF node access - For advanced use"""
        return self._device_spec.get_jtag_node()

    @property
    def debugcore_node(self) -> Optional[CoreParent]:
        """Low level TCF node access - For advanced use"""
        return self._device_spec.get_debugcore_node(target=None, default_target=self.default_target)

    @property
    def chipscope_node(self) -> Optional[CoreParent]:
        """Low level TCF node access - For advanced use"""
        return self._device_spec.get_chipscope_node(target=None, default_target=self.default_target)

    # DEBUG CORES

    @property
    def ibert_cores(self) -> QueryList[IBERT]:
        """Returns:
        list of detected IBERT cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(IBERTCoreClient)

    @property
    def vio_cores(self) -> QueryList[VIO]:
        """Returns:
        list of detected VIO cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL, DeviceFamily.UPLUS)
        return self._get_debug_core_wrappers(AxisVIOCoreClient)

    @property
    def ila_cores(self) -> QueryList[ILA]:
        """Returns:
        list of detected ILA cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL, DeviceFamily.UPLUS)
        return self._get_debug_core_wrappers(AxisIlaCoreClient)

    @property
    def trace_cores(self) -> QueryList[Trace]:
        """Returns:
        list of detected Trace cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(AxisTraceClient)

    @property
    def pcie_cores(self) -> QueryList[PCIe]:
        """Returns:
        list of detected PCIe cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(AxisPCIeCoreClient)

    @property
    def noc_core(self) -> QueryList[NocPerfmon]:
        """Returns:
        List with NOC roots for the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(NoCPerfMonCoreClient)

    @property
    def ddrs(self) -> QueryList[DDR]:
        """Returns:
        list of detected DDRMC cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(DDRMCClient)

    @property
    def hbms(self) -> QueryList[HBM]:
        """Returns:
        list of detected HBM cores in the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(HBMClient)

    @property
    def sysmon_root(self) -> QueryList[Sysmon]:
        """Returns:
        List with one SysMon core for the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        return self._get_debug_core_wrappers(SysMonCoreClient)

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
        elif node.type == "hbm":
            debug_core_wrapper = HBM(node)
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

        cs_view = self.cs_server.get_view(chipscope)
        found_cores = defaultdict(list)

        def check_and_upgrade_node(node):
            if self.cores_to_scan.get(cs_node.type, True):
                core_class_type = Device._CORE_TYPE_TO_CLASS_MAP.get(node.type, None)
                if core_class_type and core_class_type.is_compatible(node):
                    upgraded_node = cs_view.get_node(node.ctx, core_class_type)
                    found_cores[core_class_type].append(upgraded_node)

        # Using the self.chipscope_node restricts nodes to this device only
        for cs_node in cs_view.get_children(self.chipscope_node):
            if cs_node.type == "debug_hub":
                debug_hub_children = cs_view.get_children(cs_node)
                for child in debug_hub_children:
                    check_and_upgrade_node(child)
            else:
                check_and_upgrade_node(cs_node)
        return found_cores

    def _get_debug_core_wrappers(self, core_type) -> QueryList:
        # Returns a QueryList of the debug_core_wrappers matching the given core_type
        #   core_type is a class from CORE_TYPE_TO_CLASS_MAP
        #   returned wrapper_type is ILA, VIO, etc. wrapping the node
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
            self._set_client_wrapper(node, debug_core_wrapper)
            # Now the node should have a proper debug_core_wrapper attached.
            if Device._get_client_wrapper(node):
                found_cores.append(Device._get_client_wrapper(node))
        return found_cores

    def discover_and_setup_cores(
        self,
        *,
        hub_address_list: Optional[List[int]] = None,
        ltx_file: Union[Path, str] = None,
        **kwargs,
    ):
        """Scan device for debug cores. This may take some time depending on
        what gets scanned.

        Args:
            hub_address_list: List of debug hub addresses to scan
            ltx_file: LTX file (which contains debug hub addresses)

        Keyword Arguments:
            ila_scan: True=Scan Device for ILAs
            vio_scan: True=Scan Device for VIOs
            ibert_scan: True=Scan Device for IBERTs
            pcie_scan: True=Scan Device for PCIEs
            noc_scan: True=Scan Device for NOC
            ddr_scan: True=Scan Device for DDRs
            hbm_scan: True=Scan Device for HBMs
            sysmon_scan: True=Scan Device for System Monitor
        """
        # Selectively disable scanning of cores depending on what comes in
        # This is second priority to the disable_core_scan in __init__.
        self._raise_if_family_not(DeviceFamily.VERSAL, DeviceFamily.UPLUS)
        self.cores_to_scan = {}
        if self.disable_core_scan:
            for core_name in Device._CORE_TYPE_TO_CLASS_MAP.keys():
                self.cores_to_scan[core_name] = False
        else:
            self.cores_to_scan = {
                "ila": kwargs.get("ila_scan", True),
                "vio": kwargs.get("vio_scan", True),
                "npi_nir": kwargs.get("noc_scan", False),
                "ddrmc_main": kwargs.get("ddr_scan", True),
                "hbm": kwargs.get("hbm_scan", True),
                "pcie": kwargs.get("pcie_scan", True),
                "ibert": kwargs.get("ibert_scan", True),
                "sysmon": kwargs.get("sysmon_scan", False),
            }
        if not self.cs_server:
            raise RuntimeError("cs_server is not connected")

        self.ltx = None

        # Make sure debug_hub_addrs is a list of hub addresses.
        # It may come as an int or a list or None
        if isinstance(hub_address_list, int):
            hub_address_list = [hub_address_list]
        if not hub_address_list:
            hub_address_list = []

        if ltx_file:
            self.ltx, self.ltx_sources, _ = parse_ltx_files(ltx_file)  # noqa
            hub_address_list.extend(self.ltx.get_debug_hub_addresses())
            # Remove any duplicate hub addresses in list, in case same one
            # was passed to function as well as in ltx
            # Below is a quick python trick to uniquify a list.
            hub_address_list = list(dict.fromkeys(hub_address_list))

        # Set up all debug cores in hw_server for the given hub addresses
        # Do this by default unless the user has explicitly told us not to with
        # "disable_core_scan" as an argument.
        if not self.disable_core_scan:
            if not self.cs_server:
                raise RuntimeError("No chipscope server connection. Could not get chipscope view")
            self.chipscope_node.setup_cores(debug_hub_addrs=hub_address_list)

    # MEMORY

    @property
    def memory_target_names(self) -> List[str]:
        """Returns:
        list of supported memory targets"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        valid_memory_targets = (
            r"(Versal .*)|(DPC)|(APU)|(RPU)|(PPU)|(PSM)|(Cortex.*)|(MicroBlaze.*)"
        )
        memory_view = self.hw_server.get_view("memory")
        memory_node_list = []
        mem_dpc_node = self._device_spec.get_memory_node(target="DPC")
        if mem_dpc_node:
            memory_node_list.append(mem_dpc_node)
        mem_dap_node = self._device_spec.get_memory_node(target="DAP")
        if mem_dap_node:
            memory_node_list.append(mem_dap_node)

        nodes_to_travel = deque(memory_node_list)
        memory_node_list = []
        while nodes_to_travel:
            node = nodes_to_travel.popleft()
            if MemoryNode.is_compatible(node):
                memory_node = memory_view.get_node(node.ctx, MemoryNode)
                memory_node_list.append(memory_node)
                nodes_to_travel.extendleft(memory_view.get_children(memory_node))

        # Now the memory_node_list has all memory nodes.
        # Make the list of what we found and return it
        memory_target_names = []
        for node in memory_node_list:
            memory_target_name = node.props.get("Name")
            if memory_target_name and re.search(valid_memory_targets, memory_target_name):
                memory_target_names.append(memory_target_name)
        return memory_target_names

    @property
    def memory(self) -> QueryList[Memory]:
        """Returns:
        the memory access for the device"""
        self._raise_if_family_not(DeviceFamily.VERSAL)
        target_nodes = self._device_spec.get_all_memory_nodes()
        node_list = QueryList()
        for node in target_nodes:
            node_list.append(node)
        return node_list

    def memory_read(self, address: int, num: int = 1, *, size="w", target=None) -> List[int]:
        """Read num values from given memory address.  This method is slow because it locates the memory context
        in the target tree every time. If you want to execute a large number of memory operations, grab a memory
        context and do all the operations in batch.
        Note: This method should not be used in inner loops. It is not the fastest because it looks up the memory
        target every time. Inner loops should just call the find_memory_target once.
        """
        self._raise_if_family_not(DeviceFamily.VERSAL)
        node = self._device_spec.search_memory_node_deep(target, default_target=self.default_target)
        if not node:
            raise (ValueError(f"Could not find memory node for target {target}"))
        retval = node.memory_read(address=address, num=num, size=size)
        return retval

    def memory_write(self, address: int, values: List[int], *, size="w", target=None):
        """Write list of values to given memory address. This method is slow because it locates the memory context
        in the target tree every time. If you want to execute a large number of memory operations, grab a memory
        context and do the operations in batch.
        Note: This method should not be used in inner loops. It is not the fastest because it looks up the memory
        target every time. Inner loops should just call the find_memory_target once.
        """
        self._raise_if_family_not(DeviceFamily.VERSAL)
        node = self._device_spec.search_memory_node_deep(target, default_target=self.default_target)
        if not node:
            raise (ValueError(f"Could not find memory node for target {target}"))
        node.memory_write(address=address, values=values, size=size)

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

    # PROGRAMMING

    @staticmethod
    def _plm2bytearray(raw_plm_data: List[int]) -> bytearray:
        # Memory returns a list of 32-bit ints - convert them to a linear byte array for easier string manipulation
        plm_log_bytearray = bytearray()
        plm_data_tuples = [unpack("cccc", pack("I", w)) for w in raw_plm_data]
        for tup in plm_data_tuples:
            try:
                for c in tup:
                    plm_log_bytearray.append(ord(c.decode("utf-8")))
            except UnicodeDecodeError:
                # bytearray index out of range happens at end of useful log data
                break
        return plm_log_bytearray

    @staticmethod
    def _read_plm_log(mem: Memory) -> str:
        # Given a memory target, read the PLM log data and return as a big string
        rtca_data = mem.memory_read(address=0xF2014000, num=0x20, size="w")
        header = rtca_data[0]
        plm_wrapped_addr = 0
        plm_wrapped_len = 0

        if header == 0x41435452:
            # use_rtca = True
            use_defaults = False
            plm_addr = rtca_data[4] | (rtca_data[5] << 32)  # 64-bit address
            if (
                rtca_data[4] == 0xDEADBEEF
                or rtca_data[5] == 0xDEADBEEF
                or rtca_data[7] == 0xDEADBEEF
            ):
                use_defaults = True

            plm_offset = rtca_data[7]
            plm_len = (plm_offset & 0x7FFFFFFF) - 1
            if plm_offset & 0x80000000:
                plm_wrapped_addr = plm_addr
                plm_wrapped_len = plm_len - 1
                plm_addr = plm_addr + plm_len + 1
                plm_size = rtca_data[6]
                plm_len = plm_size - plm_len - 1
        else:
            # use_rtca = False
            use_defaults = True
            plm_addr = 0
            plm_len = 0

        if use_defaults:
            plm_addr = 0xF2019000
            plm_len = 1024

        # plm_log_bytearray = bytearray(b'@' * (plm_len + plm_wrapped_len))
        plm_data = mem.memory_read(address=plm_addr, num=plm_len, size="w")
        plm_log_bytearray = Device._plm2bytearray(plm_data)

        if plm_wrapped_addr:
            plm_data = mem.memory_read(address=plm_wrapped_addr, num=plm_wrapped_len, size="w")
            plm_log_bytearray += Device._plm2bytearray(plm_data)

        plm_log_str = plm_log_bytearray.decode("utf-8")
        return plm_log_str

    def get_program_log(self, memory_target="APU") -> str:
        """
        Returns: Programming log read from hardware (None=Use default transport)

        Args:
            memory_target: Optional name of memory target such as APU, RPU, DPC
        """
        self._raise_if_family_not(DeviceFamily.VERSAL)
        try:
            mem = self.memory.get(name=memory_target)
        except ValueError:
            raise ValueError(f"Memory target {memory_target} not available")
        return Device._read_plm_log(mem)

    def reset(self):
        """Reset the device to a non-programmed state."""
        self._raise_if_family_not(DeviceFamily.VERSAL, DeviceFamily.UPLUS)
        jtag_programming_node = self.jtag_node
        assert jtag_programming_node is not None
        jtag_programming_node.future().reset()
        time.sleep(0.5)

    def program(
        self,
        programming_file: Union[str, Path],
        *,
        skip_reset: bool = False,
        delay_after_program: int = 0,
        show_progress_bar: bool = True,
        progress: request.ProgressFutureCallback = None,
        done: request.DoneFutureCallback = None,
    ):
        """Program the device with a given programming file (bit or pdi).

        Args:
            programming_file: PDI file path
            skip_reset: False = Do not reset device prior to program
            delay_after_program: Seconds to delay at end of programming (default=0)
            show_progress_bar: False if the progress bar doesn't need to be shown
            progress: Optional progress callback
            done: Optional async future callback
        """
        self._raise_if_family_not(DeviceFamily.VERSAL, DeviceFamily.UPLUS)
        program_future = request.CsFutureSync(done=done, progress=progress)

        if isinstance(programming_file, str):
            programming_file = Path(programming_file)

        if not programming_file.exists():
            raise FileNotFoundError(
                f"Programming file: {str(programming_file.resolve())} doesn't exists!"
            )

        printer(f"Programming device with: {str(programming_file.resolve())}\n", level="info")

        if show_progress_bar:
            progress_ = PercentProgressBar()
            progress_.add_task(
                description="Device program progress",
                status=PercentProgressBar.Status.STARTING,
                visible=show_progress_bar,
            )

        def progress_update(future):
            if program_future:
                program_future.set_progress(future.progress)

            if show_progress_bar:
                progress_.update(
                    completed=future.progress * 100, status=PercentProgressBar.Status.IN_PROGRESS
                )

        def done_programming(future):
            if show_progress_bar:
                if future.error is not None:
                    progress_.update(status=PercentProgressBar.Status.ABORTED)
                else:
                    for i in range(delay_after_program):
                        # This pushes end-of-config node events to the listeners
                        # They seem to happen within about 2-3 seconds - need a more
                        # reliable way to wait for them to finish.
                        # If we don't wait, the DPC node may not be ready for use.
                        time.sleep(0.5)
                        if self.cs_server:
                            self.cs_server.get_view("chipscope").run_events()
                        time.sleep(0.5)

                    progress_.update(completed=100, status=PercentProgressBar.Status.DONE)

            self.programming_error = future.error
            self.programming_done = True
            if future.error:
                program_future.set_exception(future.error)
            else:
                program_future.set_result(None)

        def finalize_program():
            if self.programming_error is not None:
                raise RuntimeError(self.programming_error)

        jtag_programming_node = self.jtag_node
        assert jtag_programming_node is not None
        if not skip_reset:
            jtag_programming_node.future().reset()

        jtag_programming_node.future(
            progress=progress_update, done=done_programming, final=finalize_program
        ).config(str(programming_file.resolve()))

        return program_future if done else program_future.result

    def _raise_if_family_not(self, *args):
        if self.device_family == DeviceFamily.XVC:
            # special partial setup case for xvc sw testing - always ok
            return
        if self.device_family not in args:
            raise FeatureNotAvailableError()


# Legacy support - to not break old code that may have referenced the classes
# that were removed (and now all implemented by Device)

VersalDevice = NewType("VersalDevice", Device)
UltrascaleDevice = NewType("UltrascaleDevice", Device)
GenericDevice = NewType("GenericDevice", Device)


def discover_devices(
    hw_server: ServerInfo,
    cs_server: ServerInfo = None,
    disable_core_scan: bool = False,
    cable_ctx: Optional[str] = None,
    disable_cache: bool = True,
) -> QueryList[Device]:

    log.client.debug(
        f"discover_devices: hw_server={hw_server}, cs_server={cs_server}, disable_core_scan={disable_core_scan}, cable_ctx={cable_ctx}",
        disable_cache={disable_cache},
    )
    include_dna = True
    devices: QueryList[Device] = QueryList()
    idx = 0
    for key, device_record_list in scan_all_views(hw_server, cs_server, include_dna).items():
        device_spec = DeviceSpec.create_from_device_records(
            hw_server, cs_server, device_record_list
        )
        if cable_ctx is None or device_spec.jtag_cable_ctx == cable_ctx:
            device_node = device_spec.get_device_node()
            if device_node.device_wrapper is None:
                device_node.device_wrapper = Device(
                    hw_server=hw_server,
                    cs_server=cs_server,
                    device_spec=device_spec,
                    disable_core_scan=disable_core_scan,
                    disable_cache=disable_cache,
                )
                log.client.debug(
                    f"discover_devices: created new device: {device_node.device_wrapper}"
                )
            else:
                log.client.debug(
                    f"discover_devices: reusing device wrapper: {device_node.device_wrapper}"
                )
            devices.append(device_node.device_wrapper)
            log.client.info(f"discover_devices: {idx}: {device_node.device_wrapper}")
            idx += 1
    return devices
