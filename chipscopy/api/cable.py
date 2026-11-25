# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
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
from typing import Any, Dict, Optional

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

    def __getitem__(self, item):
        props = self.to_dict()
        if item in props:
            return props[item]
        else:
            raise AttributeError(f"No property {str(item)}")

    # Properties excluded from filter_by. node_cls is a Python class object injected by
    # ViewInfo.add_sync_node - it is not a meaningful filter key for users.
    _FILTER_EXCLUDED_KEYS = frozenset({"node_cls"})

    @property
    def filter_by(self) -> Dict[str, Any]:
        """Specifies the dict used for filtering cables in the session.

        Filters the QueryList returned by ``Session.cables``. Both the raw hw_server
        property names (``Description``, ``Serial``) and lowercase aliases
        (``description``, ``serial``) are accepted. ``name`` is always the cable's
        human readable description, matching :attr:`Cable.name`.

        Match values are compared by equality, not by regular expression, so pass the
        property's native type.

        Returns:
            dict[str, value]
        """
        props = {
            k: v for k, v in self.to_dict().items() if k not in type(self)._FILTER_EXCLUDED_KEYS
        }
        # Lowercase aliases first, then the original keys win, so 'Name' keeps the raw
        # hw_server value. 'name' is overridden last so it agrees with Cable.name.
        filters = {**{k.lower(): v for k, v in props.items()}, **props}
        filters["name"] = self.name
        return filters

    @staticmethod
    def check_for_filter_match(filters_dict, filter_name, match_value) -> bool:
        """Matches ``filter_by()`` values by equality rather than by regular expression.

        Cable serial numbers and descriptions routinely contain regular-expression
        metacharacters, and this operation retunes hardware shared with every other
        client, so an accidental wildcard match is unacceptable here.

        Returns:
            True if ``filter_name`` is present in ``filters_dict`` and equal to
            ``match_value``.
        """
        if filter_name not in filters_dict:
            return False
        return filters_dict[filter_name] == match_value

    def get_option(self, key: str) -> Any:
        """Reads a cable option value from the hw_server.

        Option values are read live from the hw_server on every call. They are not cached
        in the api layer. Supported keys are cable dependent. ``frequency`` (in Hz),
        ``frequency_list``, ``skew`` and ``timing_class`` are common.

        Cable options are hw_server state shared by every client, and they persist for the
        life of the hw_server process. Restore anything you change.

        Examples: ::

            cable = session.cables.get(Serial="252502174339A")
            original = cable.get_option("frequency")
            try:
                cable.set_option("frequency", 3_000_000)
                ...
            finally:
                cable.set_option("frequency", original)

        Args:
            key: Name of the option, for example ``"frequency"``.

        Returns:
            The current option value.

        Raises:
            NotImplementedError: If this cable type does not support options.
            Exception: If the hw_server rejects the request.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support cable options")

    def set_option(self, key: str, value: Any) -> Any:
        """Sets a cable option in the hw_server and returns the value actually applied.

        The hw_server is free to apply a value different from the one requested. JTAG TCK
        frequency in particular is quantized to what the cable hardware can generate. On
        the FT4232H cables this was verified against, an out-of-range value was snapped
        down to an achievable one rather than rejected, but that is cable-dependent and
        another cable may reject the request instead. This method sets the option, reads
        it back, and returns the read-back value. It does not raise when the applied value
        differs from the requested value, so the caller must compare.

        The returned value is a best-effort read-back. The set and the read are two
        independent unlocked requests, so another client may have intervened.

        A ``frequency`` of ``0`` is reserved. On some cables it requests auto-negotiation
        rather than setting a rate, and on others it does nothing. Read the value back.

        Args:
            key: Name of the option, for example ``"frequency"``.
            value: New value for the option. Only ``int`` values are supported today.

        Returns:
            The option value as read back from the hw_server after the set.

        Raises:
            NotImplementedError: If this cable type does not support options.
            TypeError: If ``value`` is not an ``int``.
            Exception: If the hw_server rejects the set or the read back.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support cable options")

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        """Returns True if the underlying cable node is still valid."""
        raise NotImplementedError

    @property
    @abstractmethod
    def devices(self) -> QueryList[Device]:
        """Returns the devices discovered on this cable."""
        raise NotImplementedError

    @abstractmethod
    def to_json(self) -> str:
        """Returns a JSON string representation of this cable's properties."""
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> Dict:
        """Returns a dict of this cable's properties."""
        raise NotImplementedError

    @property
    @abstractmethod
    def context(self) -> str:
        """Returns the TCF context id of this cable."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the human readable description of this cable."""
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
        timeout: int,
    ):
        super().__init__()
        self._tcf_node = tcf_node
        self._hw_server = hw_server
        self._cs_server = cs_server
        self._disable_core_scan = disable_core_scan
        self._timeout = timeout
        self._should_wait_for_ready = True
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

    def get_option(self, key: str) -> Any:
        """Reads a cable option value from the hw_server."""
        return self._tcf_node.get_option(key)

    def set_option(self, key: str, value: Any) -> Any:
        """Sets a cable option and returns the value the hw_server actually applied."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(
                f"Cable option {key!r} value must be an int, "
                f"got {type(value).__name__}. Only int option values are supported."
            )
        self._tcf_node.set_option(key, value)
        return self._tcf_node.get_option(key)


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
    timeout: int,
) -> QueryList[Cable]:
    """Given a hw_server and cs_server, scan for cables in hardware and return the list.

    Args:
        hw_server: hardware server connection
        cs_server: chipscope server connection (or None if no connection)
        disable_core_scan: Disable scanning debug cores in all devices (global to cable)
        timeout: cable device detection timeout in seconds

    Returns:
        New QueryList of cables
    """
    cables: QueryList[Cable] = QueryList()
    view = hw_server.get_view("jtag")
    for node in view.get_children():
        cables.append(_JtagCable(node, hw_server, cs_server, disable_core_scan, timeout))
    return cables
