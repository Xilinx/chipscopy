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
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Optional, Union, Dict, List
from struct import pack, unpack

from chipscopy.api._detail.ltx import Ltx
from chipscopy.api._detail.trace import Trace
from chipscopy.api.containers import QueryList
from chipscopy.api.ddr.ddr import DDR
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
from chipscopy.client.jtagdevice import JtagDevice, JtagCable, JtagRegister
from chipscopy.client.noc_perfmon_core_client import NoCPerfMonCoreClient
from chipscopy.client.sysmon_core_client import SysMonCoreClient
from chipscopy.dm import chipscope, request, Node
from chipscopy.utils.printer import printer, PercentProgressBar
from chipscopy.api.device.device_spec import DeviceSpec
from chipscopy.api.device.device_scanner import create_device_scanner
from chipscopy.api.device.device_util import copy_node_props


class FeatureNotAvailableError(Exception):
    def __init__(self):
        super().__init__("Feature not available on this architecture")


class Device(ABC):
    """The Device class represents a single device. It is the base class for other
    Xilinx or Generic devices.
    Depending on the device type, some features may be available or unavailable.

    Device has the kitchen sink of properties functions to make documentation and type hints easy.
    Child classes raise FeatureNotAvailable for functions they do not support.
    """

    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_spec: DeviceSpec,
        device_node: Node,
    ):
        self.hw_server = hw_server
        self.cs_server = cs_server
        self._device_spec = device_spec
        self.device_node = device_node
        # The following filter_by becomes a dictionary with architecture, jtag_index, context, etc.
        # This is used when asking for a device by filter from the device list like:
        #    report_devices(session.devices.get(dna=".*1234"))
        # Needs improvement because QueryList filtering does not work with hierarchy
        self.filter_by = self.to_dict()

    def __str__(self) -> str:
        return str(self._device_spec)

    def __repr__(self) -> str:
        return self.to_json()

    def __getitem__(self, item):
        raw_json = repr(self._device_spec)
        parsed_json = json.loads(raw_json)
        return parsed_json[item]

    def to_dict(self) -> Dict:
        """Returns a dictionary representation of the device data"""
        d = {}
        d.update(self._device_spec.to_dict())
        try:
            jtag_node = self._device_spec.find_jtag_node(self.hw_server)
        except ValueError:
            jtag_node = None
        except AttributeError:
            jtag_node = None
        if jtag_node:
            d["jtag"] = copy_node_props(jtag_node, jtag_node.props)
        d["is_valid"] = self.is_valid
        d["context"] = self.context
        return dict(sorted(d.items()))  # noqa

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
        return self.device_node.ctx if self.device_node else None

    @property
    def is_programmed(self) -> bool:
        """Returns True if this Device is programmed, False otherwise."""
        raise NotImplementedError

    @property
    def is_valid(self) -> bool:
        """Returns True if this Node is valid, False otherwise."""
        return self.device_node and self.device_node.is_valid

    @property
    def jtag_cable_node(self) -> Optional[JtagCable]:
        """Low level TCF node access - For advanced use"""
        jtag_view = self.hw_server.get_view("jtag")
        return jtag_view.get_node(self.jtag_node.parent_ctx)

    @property
    def jtag_node(self) -> Optional[JtagDevice]:
        """Low level TCF node access - For advanced use"""
        return self._device_spec.find_jtag_node(self.hw_server)

    @property
    def debugcore_node(self) -> Optional[Node]:
        """Low level TCF node access - For advanced use"""
        return self._device_spec.find_debugcore_node(self.hw_server)

    @property
    def chipscope_node(self) -> Optional[CoreParent]:
        """Low level TCF node access - For advanced use"""
        if self.cs_server:
            return self._device_spec.find_chipscope_node(self.cs_server)
        else:
            return None

    # DEBUG CORES

    @property
    @abstractmethod
    def ibert_cores(self) -> QueryList[IBERT]:
        """Returns:
        list of detected IBERT cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def vio_cores(self) -> QueryList[VIO]:
        """Returns:
        list of detected VIO cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def ila_cores(self) -> QueryList[ILA]:
        """Returns:
        list of detected ILA cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def trace_cores(self) -> QueryList[Trace]:
        """Returns:
        list of detected Trace cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def pcie_cores(self) -> QueryList[PCIe]:
        """Returns:
        list of detected PCIe cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def noc_core(self) -> QueryList[NocPerfmon]:
        """Returns:
        List with NOC roots for the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def ddrs(self) -> QueryList[DDR]:
        """Returns:
        list of detected DDRMC cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def hbms(self) -> QueryList[HBM]:
        """Returns:
        list of detected HBM cores in the device"""
        raise NotImplementedError

    @property
    @abstractmethod
    def sysmon_root(self) -> QueryList[Sysmon]:
        """Returns:
        List with one SysMon core for the device"""
        raise NotImplementedError

    @abstractmethod
    def discover_and_setup_cores(
        self, *, hub_address_list: Optional[List[int]] = None, ltx_file: str = None, **kwargs
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
        raise NotImplementedError

    # MEMORY

    @property
    @abstractmethod
    def memory_target_names(self):
        """Returns:
        list of supported memory targets"""
        raise NotImplementedError

    @property
    @abstractmethod
    def memory(self) -> QueryList[Memory]:
        """Returns:
        the memory access for the device"""
        raise NotImplementedError

    @abstractmethod
    def memory_read(self, address: int, num: int = 1, *, size, target=None) -> List[int]:
        """Read num values from given memory address.  This method is slow because it locates the memory context
        in the target tree every time. If you want to execute a large number of memory operations, grab a memory
        context and do all the operations in batch.
        Note: This method should not be used in inner loops. It is not the fastest because it looks up the memory
        target every time. Inner loops should just call the find_memory_target once.
        """
        raise NotImplementedError

    @abstractmethod
    def memory_write(self, address: int, values: List[int], *, size, target=None):
        """Write list of values to given memory address. This method is slow because it locates the memory context
        in the target tree every time. If you want to execute a large number of memory operations, grab a memory
        context and do the operations in batch.
        Note: This method should not be used in inner loops. It is not the fastest because it looks up the memory
        target every time. Inner loops should just call the find_memory_target once.
        """
        raise NotImplementedError

    @abstractmethod
    def _dpc_read_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        raise NotImplementedError

    @abstractmethod
    def _dpc_write_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        raise NotImplementedError

    # PROGRAMMING

    @abstractmethod
    def get_program_log(self, memory_target=None) -> str:
        """
        Returns: Programming log read from hardware (None=Use default transport)

        Args:
            memory_target: Optional name of memory target such as APU, RPU, DPC
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        """Reset the device to a non-programmed state."""
        raise NotImplementedError

    @abstractmethod
    def program(
        self,
        programming_file: Union[str, Path],
        *,
        skip_reset: bool = False,
        show_progress_bar: bool = True,
        done: request.DoneFutureCallback = None,
    ):
        """Program the device with a given programming file (bit or pdi).

        Args:
            programming_file: PDI file path
            skip_reset: False = Do not reset device prior to program
            show_progress_bar: False if the progress bar doesn't need to be shown
            done: Optional async future callback
        """
        raise NotImplementedError


class GenericDevice(Device):
    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_spec: DeviceSpec,
        device_node: Node,
    ):
        super().__init__(
            hw_server=hw_server,
            cs_server=cs_server,
            device_spec=device_spec,
            device_node=device_node,
        )

    @property
    def is_programmed(self) -> bool:
        raise FeatureNotAvailableError

    def memory_read(self, address: int, num: int = 1, *, size, target=None) -> List[int]:
        raise FeatureNotAvailableError

    def memory_write(self, address: int, values: List[int], *, size, target=None):
        raise FeatureNotAvailableError

    def _dpc_read_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        raise FeatureNotAvailableError

    def _dpc_write_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        raise FeatureNotAvailableError

    @property
    def ibert_cores(self) -> QueryList[IBERT]:
        raise FeatureNotAvailableError

    @property
    def vio_cores(self) -> QueryList[VIO]:
        raise FeatureNotAvailableError

    @property
    def ila_cores(self) -> QueryList[ILA]:
        raise FeatureNotAvailableError

    @property
    def trace_cores(self) -> QueryList[Trace]:
        raise FeatureNotAvailableError

    @property
    def pcie_cores(self) -> QueryList[PCIe]:
        raise FeatureNotAvailableError

    @property
    def noc_core(self) -> QueryList[NocPerfmon]:
        raise FeatureNotAvailableError

    @property
    def ddrs(self) -> QueryList[DDR]:
        raise FeatureNotAvailableError

    @property
    def hbms(self) -> QueryList[HBM]:
        raise FeatureNotAvailableError

    @property
    def sysmon_root(self) -> QueryList[Sysmon]:
        raise FeatureNotAvailableError

    def discover_and_setup_cores(
        self, *, hub_address_list: Optional[List[int]] = None, ltx_file: str = None, **kwargs
    ):
        raise FeatureNotAvailableError

    @property
    def memory_target_names(self):
        raise FeatureNotAvailableError

    @property
    def memory(self) -> QueryList[Memory]:
        raise FeatureNotAvailableError

    def get_program_log(self, memory_target=None) -> str:
        raise FeatureNotAvailableError

    def reset(self):
        raise FeatureNotAvailableError

    def program(
        self,
        programming_file: Union[str, Path],
        *,
        skip_reset: bool = False,
        show_progress_bar: bool = True,
        done: request.DoneFutureCallback = None,
    ):
        raise FeatureNotAvailableError


class FpgaDevice(Device, ABC):
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
        "hbm": HBMClient,
    }

    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_spec: DeviceSpec,
        disable_core_scan: bool,
        device_node: Node,
    ):
        self.disable_core_scan = disable_core_scan
        self.cores_to_scan = {}  # set during discover_and_setup_cores
        self.ltx = None
        self.programming_error: Optional[str] = None
        self.programming_done: bool = False
        super().__init__(
            hw_server=hw_server,
            cs_server=cs_server,
            device_spec=device_spec,
            device_node=device_node,
        )

    @property
    def is_programmed(self) -> bool:
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
    def ibert_cores(self) -> QueryList[IBERT]:
        raise FeatureNotAvailableError

    @property
    def vio_cores(self) -> QueryList[VIO]:
        return self._get_debug_core_wrappers(AxisVIOCoreClient)

    @property
    def ila_cores(self) -> QueryList[ILA]:
        return self._get_debug_core_wrappers(AxisIlaCoreClient)

    @property
    def trace_cores(self) -> QueryList[Trace]:
        raise FeatureNotAvailableError

    @property
    def pcie_cores(self) -> QueryList[PCIe]:
        raise FeatureNotAvailableError

    @property
    def noc_core(self) -> QueryList[NocPerfmon]:
        raise FeatureNotAvailableError

    @property
    def ddrs(self) -> QueryList[DDR]:
        raise FeatureNotAvailableError

    @property
    def hbms(self) -> QueryList[HBM]:
        raise FeatureNotAvailableError

    @property
    def sysmon_root(self) -> QueryList[Sysmon]:
        raise FeatureNotAvailableError

    @property
    def memory_target_names(self):
        raise FeatureNotAvailableError

    @property
    def memory(self) -> QueryList[Memory]:
        raise FeatureNotAvailableError

    def to_dict(self) -> Dict:
        d = super().to_dict()
        d["is_programmed"] = self.is_programmed
        return d

    def memory_read(self, address: int, num: int = 1, *, size, target=None) -> List[int]:
        raise FeatureNotAvailableError

    def memory_write(self, address: int, values: List[int], *, size, target=None):
        raise FeatureNotAvailableError

    def _dpc_read_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        raise FeatureNotAvailableError

    def _dpc_write_bytes(
        self,
        address: int,
        data: bytearray,
        *,
        offset: int = 0,
        byte_size: int = None,
        show_progress_bar: bool = True,
    ):
        raise FeatureNotAvailableError

    def get_program_log(self, memory_target=None) -> str:
        raise FeatureNotAvailableError

    def reset(self):
        jtag_programming_node = self._device_spec.find_jtag_node(self.hw_server)
        assert jtag_programming_node is not None
        jtag_programming_node.future().reset()
        time.sleep(0.5)

    def program(
        self,
        programming_file: Union[str, Path],
        *,
        skip_reset: bool = False,
        show_progress_bar: bool = True,
        done: request.DoneFutureCallback = None,
    ):
        program_future = request.CsFutureSync(done)

        if isinstance(programming_file, str):
            programming_file = Path(programming_file)

        if not programming_file.exists():
            raise FileNotFoundError(
                f"Programming file: {str(programming_file.resolve())} doesn't exists!"
            )

        printer(f"Programming device with: {str(programming_file.resolve())}\n", level="info")

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

        jtag_programming_node = self._device_spec.find_jtag_node(self.hw_server)
        assert jtag_programming_node is not None
        if not skip_reset:
            jtag_programming_node.future().reset()

        jtag_programming_node.future(
            progress=progress_update, done=done_programming, final=finalize_program
        ).config(str(programming_file.resolve()))

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
        self, *, hub_address_list: Optional[List[int]] = None, ltx_file: str = None, **kwargs
    ):
        # Selectively disable scanning of cores depending on what comes in
        # This is second priority to the disable_core_scan in __init__.
        self.cores_to_scan = {}
        if self.disable_core_scan:
            for core_name in FpgaDevice.CORE_TYPE_TO_CLASS_MAP.keys():
                self.cores_to_scan[core_name] = False
        else:
            self.cores_to_scan = {
                "ila": kwargs.get("ila_scan", True),
                "vio": kwargs.get("vio_scan", True),
                "npi_nir": kwargs.get("noc_scan", False),
                "ddrmc_main": kwargs.get("ddr_scan", True),
                "hbm": kwargs.get("hbm_scan", True),
                "pcie": kwargs.get("pcie_scan", True),
                "ibert": kwargs.get("ibert_scan", False),
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
            if not self.chipscope_node:
                raise RuntimeError("No chipscope server connection. Could not get chipscope view")
            self.chipscope_node.setup_cores(debug_hub_addrs=hub_address_list)

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
        #
        cs_view = self.cs_server.get_view(chipscope)
        found_cores = defaultdict(list)
        # Using the self.chipscope_node restricts nodes to this device only
        for cs_node in cs_view.get_children(self.chipscope_node):
            if cs_node.type == "debug_hub":
                debug_hub_children = cs_view.get_children(cs_node)
                for child in debug_hub_children:
                    if self.cores_to_scan.get(child.type, True):
                        core_class_type = FpgaDevice.CORE_TYPE_TO_CLASS_MAP.get(child.type, None)
                        if core_class_type and core_class_type.is_compatible(child):
                            upgraded_node = cs_view.get_node(child.ctx, core_class_type)
                            found_cores[core_class_type].append(upgraded_node)
            else:
                if self.cores_to_scan.get(cs_node.type, True):
                    core_class_type = FpgaDevice.CORE_TYPE_TO_CLASS_MAP.get(cs_node.type, None)
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
            debug_core_wrapper = FpgaDevice._get_client_wrapper(node)
            if debug_core_wrapper is None:
                # Lazy debugcore initialization here.
                # Initialization happens the first time we access the debug core.
                debug_core_wrapper = self._create_debugcore_wrapper(node)
            self._set_client_wrapper(node, debug_core_wrapper)
            # Now the node should have a proper debug_core_wrapper attached.
            if FpgaDevice._get_client_wrapper(node):
                found_cores.append(FpgaDevice._get_client_wrapper(node))
        return found_cores


class UltrascaleDevice(FpgaDevice):
    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_spec: DeviceSpec,
        disable_core_scan: bool,
        device_node: Node,
    ):
        super().__init__(
            hw_server=hw_server,
            cs_server=cs_server,
            device_spec=device_spec,
            disable_core_scan=disable_core_scan,
            device_node=device_node,
        )


class VersalDevice(FpgaDevice):
    def __init__(
        self,
        *,
        hw_server: ServerInfo,
        cs_server: Optional[ServerInfo],
        device_spec: DeviceSpec,
        disable_core_scan: bool,
        device_node: Node,
    ):
        super().__init__(
            hw_server=hw_server,
            cs_server=cs_server,
            device_spec=device_spec,
            disable_core_scan=disable_core_scan,
            device_node=device_node,
        )

    @property
    def ibert_cores(self) -> QueryList[IBERT]:
        return self._get_debug_core_wrappers(IBERTCoreClient)

    @property
    def vio_cores(self) -> QueryList[VIO]:
        return self._get_debug_core_wrappers(AxisVIOCoreClient)

    @property
    def ila_cores(self) -> QueryList[ILA]:
        return self._get_debug_core_wrappers(AxisIlaCoreClient)

    @property
    def trace_cores(self) -> QueryList[Trace]:
        return self._get_debug_core_wrappers(AxisTraceClient)

    @property
    def pcie_cores(self) -> QueryList[PCIe]:
        return self._get_debug_core_wrappers(AxisPCIeCoreClient)

    @property
    def noc_core(self) -> QueryList[NocPerfmon]:
        return self._get_debug_core_wrappers(NoCPerfMonCoreClient)

    @property
    def ddrs(self):
        return self._get_debug_core_wrappers(DDRMCClient)

    @property
    def hbms(self):
        return self._get_debug_core_wrappers(HBMClient)

    @property
    def sysmon_root(self) -> QueryList[Sysmon]:
        return self._get_debug_core_wrappers(SysMonCoreClient)

    @property
    def memory_target_names(self):
        valid_memory_targets = (
            r"(Versal .*)|(DPC)|(APU)|(RPU)|(PPU)|(PSM)|(Cortex.*)|(MicroBlaze.*)"
        )
        memory_target_names = list()
        memory_node_list = self._device_spec.get_memory_target_nodes(self.hw_server)
        for memory_node in memory_node_list:
            memory_target_name = memory_node.props.get("Name")
            if len(memory_target_name) > 0 and re.search(valid_memory_targets, memory_target_name):
                memory_target_names.append(memory_target_name)
        return memory_target_names

    @property
    def memory(self) -> QueryList[Memory]:
        target_nodes = self._device_spec.get_memory_target_nodes(self.hw_server)
        memory_node_list = QueryList()
        for node in target_nodes:
            if Memory.is_compatible(node):
                memory_node_list.append(node)
        return memory_node_list

    def memory_write(self, address: int, values: List[int], *, size="w", target=None):
        node = self._device_spec.find_memory_target(self.hw_server, target)
        node.memory_write(address=address, values=values, size=size)

    def memory_read(self, address: int, num: int = 1, *, size="w", target=None) -> List[int]:
        node = self._device_spec.find_memory_target(self.hw_server, target)
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
        plm_log_bytearray = VersalDevice._plm2bytearray(plm_data)

        if plm_wrapped_addr:
            plm_data = mem.memory_read(address=plm_wrapped_addr, num=plm_wrapped_len, size="w")
            plm_log_bytearray += VersalDevice._plm2bytearray(plm_data)

        plm_log_str = plm_log_bytearray.decode("utf-8")
        return plm_log_str

    def get_program_log(self, memory_target="APU") -> str:
        try:
            mem = self.memory.get(name=memory_target)
        except ValueError:
            raise ValueError(f"Memory target {memory_target} not available")
        return VersalDevice._read_plm_log(mem)


def discover_devices(
    hw_server: ServerInfo,
    cs_server: ServerInfo,
    disable_core_scan: bool,
    cable_ctx: Optional[str] = None,
    use_legacy_scaner: bool = True,
) -> QueryList[Device]:
    devices: QueryList[Device] = QueryList()
    device_scanner = create_device_scanner(hw_server, cs_server, use_legacy_scaner)
    for device_spec in device_scanner.scan_devices(cable_ctx=cable_ctx):
        device_node = device_spec.find_top_level_device_node(hw_server)
        if cable_ctx:
            assert device_node.parent_ctx == cable_ctx

        if device_node.device_wrapper is None:
            family = device_spec.to_dict().get("family")
            if use_legacy_scaner or family == "versal" or family == "xvc_defined_family":
                device_node.device_wrapper = VersalDevice(
                    hw_server=hw_server,
                    cs_server=cs_server,
                    device_spec=device_spec,
                    disable_core_scan=disable_core_scan,
                    device_node=device_node,
                )
            elif family is not None:
                device_node.device_wrapper = UltrascaleDevice(
                    hw_server=hw_server,
                    cs_server=cs_server,
                    device_spec=device_spec,
                    disable_core_scan=disable_core_scan,
                    device_node=device_node,
                )
            else:
                device_node.device_wrapper = GenericDevice(
                    hw_server=hw_server,
                    cs_server=cs_server,
                    device_spec=device_spec,
                    device_node=device_node,
                )

        devices.append(device_node.device_wrapper)
    return devices
