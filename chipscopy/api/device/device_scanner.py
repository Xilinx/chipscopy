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

from typing import Optional, List

from chipscopy.api.device.device_spec import (
    DeviceSpec,
)
from chipscopy.api.device.device_util import (
    legacy_scan_all,
    legacy_scan_cable,
    updated_scan_cable,
    updated_scan_all,
)
from chipscopy.client import ServerInfo


class _ScanInterface:
    def scan_cable(
        self, hw_server: ServerInfo, cs_server: ServerInfo, cable_ctx: str
    ) -> List[DeviceSpec]:
        raise NotImplementedError

    def scan_all(self, hw_server: ServerInfo, cs_server: ServerInfo) -> List[DeviceSpec]:
        raise NotImplementedError


class _LegacyDeviceScan(_ScanInterface):
    def __str__(self):
        return "_LegacyDeviceScan"

    def scan_cable(
        self, hw_server: ServerInfo, cs_server: ServerInfo, cable_ctx: str
    ) -> List[DeviceSpec]:
        device_scan_results = []
        for device_tracker_tuple in legacy_scan_cable(hw_server, cs_server, cable_ctx):
            device_tracker = DeviceSpec(device_tracker_tuple)
            device_scan_results.append(device_tracker)
        return device_scan_results

    def scan_all(self, hw_server: ServerInfo, cs_server: ServerInfo) -> List[DeviceSpec]:
        device_scan_results = []
        for device_tracker_tuple in legacy_scan_all(hw_server, cs_server):
            device_tracker = DeviceSpec(device_tracker_tuple)
            device_scan_results.append(device_tracker)
        return device_scan_results


class _UpdatedDeviceScan(_ScanInterface):
    def __str__(self):
        return "_UpdatedDeviceScan"

    def scan_cable(
        self, hw_server: ServerInfo, cs_server: ServerInfo, cable_ctx: str
    ) -> List[DeviceSpec]:
        device_scan_results = []
        for device_tracker_tuple in updated_scan_cable(hw_server, cs_server, cable_ctx):
            device_tracker = DeviceSpec(device_tracker_tuple)
            device_scan_results.append(device_tracker)
        return device_scan_results

    def scan_all(self, hw_server: ServerInfo, cs_server: ServerInfo) -> List[DeviceSpec]:
        device_scan_results = []
        for device_tracker_tuple in updated_scan_all(hw_server, cs_server):
            device_tracker = DeviceSpec(device_tracker_tuple)
            device_scan_results.append(device_tracker)
        return device_scan_results


class DeviceScanner:
    """This is a utility to scan for devices in hardware. It connects the jtag cable nodes to the
    other views using Device DNA.
    """

    def __init__(self, hw_server: ServerInfo, cs_server: ServerInfo, scanner: _ScanInterface):
        """
        Args:
            hw_server: hardware server
            cs_server: chipscope server(optional)
            scanner: algorithm used to scan for devices
        """
        self._hw_server = hw_server
        self._cs_server = cs_server
        self._scanner = scanner

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return f"DeviceScanner: hw_server={self._hw_server}, cs_server={self._cs_server}, scan_algorithm={self._scanner}"

    def to_dict(self):
        raise NotImplementedError

    def to_json(self):
        device_identification_list = self.scan_devices()
        return device_identification_list.__repr__()

    def scan_devices(self, cable_ctx: Optional[str] = None) -> List[DeviceSpec]:
        """Query the hw_server for connected devices. Creates a list of devices found and connects together
        the associated contexts across jtag, memory, debugcore, and chipscope views.
        This is a convenience for finding and organizing nodes that may be living in unexpected places
        like DPC and Versal both living at the top level of a device. We figure it out here so the user
        doesn't have to.

        Upon successful scan completion, self.device_scan_results is populated with the scan results.

        Args:
            cable_ctx: cable context to scan (None=all cables)
        """
        if cable_ctx:
            return self._scanner.scan_cable(self._hw_server, self._cs_server, cable_ctx)
        else:
            return self._scanner.scan_all(self._hw_server, self._cs_server)


def create_device_scanner(
    hw_server: ServerInfo, cs_server: ServerInfo, use_legacy_scanner: bool = False
) -> DeviceScanner:
    if use_legacy_scanner:
        scanner = _LegacyDeviceScan()
    else:
        scanner = _UpdatedDeviceScan()
    return DeviceScanner(hw_server, cs_server, scanner)
