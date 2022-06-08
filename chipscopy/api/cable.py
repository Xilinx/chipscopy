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

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

from chipscopy.client.view_info import ViewInfo
from chipscopy.dm import Node
from chipscopy.client.jtagdevice import JtagCable
from chipscopy.client import ServerInfo
from chipscopy.api.device.device import Device, discover_devices
from chipscopy.api.containers import QueryList

DOMAIN_NAME = "client"


class Cable(ABC):
    """A Cable represents a cable connection. This may be a physical jtag cable, or a virtual cable.
    Zero or more devices may be associated with the cable, and each device has a position.
    Roughly equivalent to a vivado hw_target.
    """

    def __init__(self):
        pass

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return self.to_json()

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def devices(self) -> QueryList[Device]:
        raise NotImplementedError

    @abstractmethod
    def to_json(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> Dict:
        raise NotImplementedError

    @property
    @abstractmethod
    def context(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class _VirtualCable(Cable):
    # TODO: Placeholder - Implement when needed
    pass


class _JtagCable(Cable):
    def __init__(
        self,
        tcf_node: Node,
        hw_server: ServerInfo,
        cs_server: ServerInfo,
        disable_core_scan: bool,
        use_legacy_scanner: bool,
        timeout: int,
    ):
        super().__init__()
        self._tcf_node = tcf_node
        self._hw_server = hw_server
        self._cs_server = cs_server
        self._disable_core_scan = disable_core_scan
        self._timeout = timeout
        self._should_wait_for_ready = True
        self._use_legacy_scanner = use_legacy_scanner
        assert tcf_node.props.get("node_cls") == JtagCable
        assert tcf_node.is_valid is True

    @property
    def is_valid(self) -> bool:
        return self._tcf_node.is_valid

    @property
    def devices(self) -> QueryList[Device]:
        if self._should_wait_for_ready:
            # Only wait first time
            self._should_wait_for_ready = False
            self.wait_for_cable_ready(self._timeout)
        devices = discover_devices(
            hw_server=self._hw_server,
            cs_server=self._cs_server,
            disable_core_scan=self._disable_core_scan,
            cable_ctx=self._tcf_node.ctx,
            use_legacy_scaner=self._use_legacy_scanner,
        )
        return devices

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4, default=lambda o: str(o))

    def to_dict(self):
        d = {}
        d.update(self._tcf_node.props)
        d.update({"context": self._tcf_node.ctx})
        return d

    @property
    def context(self) -> str:
        return self._tcf_node.ctx

    @property
    def name(self) -> str:
        return self._tcf_node.props.get("Description")

    def wait_for_cable_ready(self, cable_timeout: int):
        """Waits for a cable to be ready up to cable_timeout seconds.

        Args:
            cable_timeout: Max seconds to wait
        """
        if cable_timeout > 0:
            view = self._hw_server.get_view("jtag")
            for ctx, cable in _get_cable_contexts(view).items():
                if ctx == self.context:
                    # Wait for cable to become ready
                    start = time.time()
                    while time.time() - start < cable_timeout:
                        device_nodes = list(view.get_children(cable))
                        if len(device_nodes) > 0:
                            break
                        time.sleep(0.25)


def _get_cable_contexts(view: ViewInfo) -> Dict[str, Node]:
    """Returns a dict of all cable contexts mapped to cable nodes attached to the hw_server"""
    cables = view.get_children()
    cable_ctx_dict = {}
    for cable in cables:
        cable_ctx_dict[cable.ctx] = cable
    return cable_ctx_dict


def wait_for_all_cables_ready(hw_server: ServerInfo, cable_timeout: int):
    """Wait for all jtag cables to be ready. Simple method - iterate over all the cables. If any
    have 0 devices, wait until devices appear. If we get a timeout, there are assumed to be
    no devices on the cable.

    Some cables take a second or two to come up. Don't have a good way to ask the
    cable if it is ready, so we just inspect the device nodes and see if they exist.

    Args:
        cable_timeout: max timeout in seconds to initialize a cable
        hw_server: hardware server
    """
    if cable_timeout > 0:
        view = hw_server.get_view("jtag")
        start = time.time()
        keep_trying = True
        cables = _get_cable_contexts(view)
        while keep_trying and time.time() - start < cable_timeout:
            keep_trying = False
            for ctx, cable in cables.items():
                # Wait for cable to become ready
                device_nodes = list(view.get_children(cable))
                if len(device_nodes) == 0:
                    keep_trying = True
                    time.sleep(0.25)
                    break


def discover_cables(
    hw_server: ServerInfo,
    cs_server: Optional[ServerInfo],
    disable_core_scan: bool,
    use_legacy_scanner: bool,
    timeout: int,
) -> QueryList[Cable]:
    """Given a hw_server and cs_server, scan for cables in hardware and return the list.

    Args:
        hw_server: hardware server connection
        cs_server: chipscope server connection (or None if no connection)
        disable_core_scan: Disable scanning debug cores in all devices (global to cable)
        use_legacy_scanner: Use legacy device scan algorithm
        timeout: cable device detection timeout in seconds

    Returns:
        New QueryList of cables
    """
    cables: QueryList[Cable] = QueryList()
    view = hw_server.get_view("jtag")
    for node in view.get_children():
        cables.append(
            _JtagCable(node, hw_server, cs_server, disable_core_scan, use_legacy_scanner, timeout)
        )
    return cables
