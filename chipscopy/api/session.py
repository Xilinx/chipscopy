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
import sys
import threading
import traceback
import socket
import time
from typing import Optional, Dict, Any, List, Union, Callable, Set, Tuple

from chipscopy.api import DMNodeListener
from chipscopy.client.jtagdevice import JtagDevice, JtagCable
from chipscopy.dm import chipscope, Node
from chipscopy.utils.logger import get_logger, enable_domain, disable_domain, change_log_level
from chipscopy.utils.version import version_consistency_check
from chipscopy.client import stimgen
from chipscopy.client import connect as client_connect
from chipscopy.client import disconnect as client_disconnect
from chipscopy.client.util import connect_hw, process_param_str, parse_params
from chipscopy.client.view_info import ViewInfo
from chipscopy.client.server_info import ServerInfo
from chipscopy.api.containers import QueryList
from chipscopy.api.device.device import Device, FeatureNotAvailableError, DeviceState, DeviceFamily
from chipscopy.api.device.device_util import get_jtag_view_dict
from chipscopy.api.memory import Memory
from chipscopy.api.cable import Cable, discover_devices, wait_for_all_cables_ready, discover_cables

logger = get_logger("client")


class PostProgramReacquireError(RuntimeError):
    """Raised when a programmed device never reacquires a stable chipscope root."""


class Session:
    """Top level object that tracks a connection to a hardware server and optionally, chipscope
    server. To create and destroy a session, use the factory function
    create_session() and delete_session().
    """

    _session_lock = threading.RLock()

    # Global session tracking here. We keep a list of who is connected at any time.
    # Format:
    #    dict[hex(id(session))] = (hw_server, cs_server, session)
    _connected_session_dict: Dict[str, Tuple[ServerInfo, ServerInfo, "Session"]] = {}

    # cs_server channel reference counting.
    # cs_server instances are shared for the same host/port.
    # Format:
    #    dict[(normalized_host,port)] = (count, cs_server)
    _cs_server_channel_ref_count: Dict[Tuple[str, int], Tuple[int, ServerInfo]] = {}

    def __init__(
        self,
        *,
        hw_server_url: str,
        cs_server_url: Optional[str] = None,
        xvc_mm_server_url: Optional[str] = None,
        disable_core_scan: bool,
        bypass_version_check: bool,
        cable_timeout: int,
        disable_cache: bool,
        initial_device_scan: bool,
        pre_device_scan_delay: int,
        cs_server_sharing: bool,
        enable_experimental_protocol_decode: bool = False,
    ):
        self._cs_server_sharing: bool = cs_server_sharing
        self._disable_core_scan: bool = disable_core_scan
        self._bypass_version_check: bool = bypass_version_check
        self._hw_server_url: str = hw_server_url
        self._cs_server_url: str = cs_server_url
        self._xvc_mm_server_url: str = xvc_mm_server_url
        self._cable_timeout = cable_timeout
        self._cables_are_initialized = False
        self._disable_cache = disable_cache
        self._register_node_listeners = not self._disable_cache
        self._initial_device_scan = initial_device_scan
        self._pre_device_scan_delay = pre_device_scan_delay
        self.enable_experimental_protocol_decode = enable_experimental_protocol_decode
        self.hw_server: Optional[ServerInfo] = None
        self.cs_server: Optional[ServerInfo] = None

        self._need_to_scan_devices = True
        self._devices: QueryList[Device] = QueryList()
        self._device_lock = threading.Lock()

        self._dm_node_listener = DMNodeListener(self.node_callback)

    def __str__(self):
        return f"{self.handle}"

    def __repr__(self):
        return self.to_json()

    def __getitem__(self, item):
        props = self.to_dict()
        if item in props:
            return props[item]
        else:
            raise AttributeError(f"No property {str(item)}")

    def to_json(self):
        json_dict = json.dumps(self.to_dict(), indent=4)
        return json_dict

    def to_dict(self):
        ret_dict = {
            "name": self.handle,
            "hw_server_url": self._hw_server_url,
            "cs_server_url": self._cs_server_url,
            "xvc_mm_server_url": self._xvc_mm_server_url,
            "bypass_version_check": self._bypass_version_check,
            "disable_core_scan": self._disable_core_scan,
            "cable_timeout": self._cable_timeout,
            "handle": self.handle,
        }
        return ret_dict

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            traceback.print_exception(exc_type, exc_val, exc_tb)
        delete_session(self)

    def node_callback(self, action: DMNodeListener.NodeAction, node: Node, props: Optional[Set]):
        # This callback is called when nodes are added, changed, or removed.
        if node:
            valid_device_list = QueryList()
            devices = self._get_devices_with_lock()
            for device in devices:
                # Propagate node events to devices, so they can decide what to do with the event
                device.node_callback(action, node, props)
                if device.state == DeviceState.INVALID:
                    # Not typical - could be a board power off situation
                    # Anything that causes a device to be INVALID means we need to re-scan the
                    # devices and get that one removed from the list.
                    self._need_to_scan_devices = True
                else:
                    valid_device_list.append(device)

            self._set_device_with_lock(valid_device_list)

    @classmethod
    def _add_connection(
        cls, hw_server: ServerInfo, cs_server: Optional[ServerInfo], session: "Session"
    ):
        with cls._session_lock:
            cls._connected_session_dict[hex(id(session))] = (hw_server, cs_server, session)

    @classmethod
    def _remove_connection(cls, session: "Session"):
        with cls._session_lock:
            del cls._connected_session_dict[hex(id(session))]

    @classmethod
    def _get_all_sessions(cls) -> List["Session"]:
        sessions = []
        with cls._session_lock:
            for id_key, (_, _, session) in cls._connected_session_dict.items():
                sessions.append(session)
        return sessions

    @staticmethod
    def _make_device_rescan_callback(device: Device, callback: Callable):
        def request_rescan(hw_server: ServerInfo):
            callback(hw_server, device)

        return request_rescan

    @staticmethod
    def _device_needs_post_program_wait(device: Device) -> bool:
        return bool(device.cs_server) and device.device_family == DeviceFamily.UPLUS

    @staticmethod
    def _get_stable_chipscope_node(device: Device) -> Optional[Node]:
        chipscope_node = device.chipscope_node
        if not chipscope_node:
            return None

        cs_server = getattr(device, "cs_server", None)
        if not cs_server:
            return chipscope_node

        node_ctx = getattr(chipscope_node, "ctx", "")
        if not node_ctx:
            return None

        try:
            chipscope_view = cs_server.get_view(chipscope)
        except Exception:
            return None

        raw_node = None
        for _ in range(2):
            chipscope_view.run_events()
            raw_node = chipscope_view.cs_manager.get_node(node_ctx)
            if raw_node is None:
                return None

        return raw_node

    @staticmethod
    def _matches_reacquired_device(original_device: Device, scanned_device: Device) -> bool:
        if scanned_device is original_device:
            return True
        if scanned_device.context == original_device.context:
            return True
        return (
            getattr(scanned_device, "dna", None) is not None
            and scanned_device.dna == getattr(original_device, "dna", None)
            and scanned_device.jtag_index == getattr(original_device, "jtag_index", None)
            and scanned_device.part_name == getattr(original_device, "part_name", None)
        )

    def _adopt_reacquired_device(
        self, original_device: Device, reacquired_device: Optional[Device]
    ) -> Device:
        if reacquired_device is None or reacquired_device is original_device:
            return original_device

        original_device._rebind_device_spec(reacquired_device._device_spec)
        original_device.hw_server = reacquired_device.hw_server
        original_device.cs_server = reacquired_device.cs_server

        device_node = original_device._device_spec.get_device_node()
        if device_node:
            device_node.device_wrapper = original_device

        rebound_devices = QueryList()
        replaced = False
        for scanned_device in self._get_devices_with_lock():
            if scanned_device is reacquired_device:
                rebound_devices.append(original_device)
                replaced = True
            elif scanned_device is not original_device:
                rebound_devices.append(scanned_device)

        if replaced:
            self._set_device_with_lock(rebound_devices)

        return original_device

    def _rescan_after_program(
        self, device: Device, timeout: float = 5.0, poll_interval: float = 0.1
    ) -> None:
        deadline = time.monotonic() + timeout
        current_device = device
        last_error: Optional[Exception] = None

        while True:
            rescan_cancelled = getattr(current_device, "_rescan_cancelled", None)
            if rescan_cancelled is not None and rescan_cancelled.is_set():
                return

            try:
                scanned_devices = self.scan_devices()
                reacquired_device = None
                for scanned_device in scanned_devices:
                    if self._matches_reacquired_device(device, scanned_device):
                        reacquired_device = scanned_device
                        break

                current_device = self._adopt_reacquired_device(device, reacquired_device)
                if not self._device_needs_post_program_wait(current_device):
                    return

                if self._get_stable_chipscope_node(current_device):
                    return

                # Device found but chipscope node not yet stable. For UPLUS
                # devices the chipscope context is established by
                # discover_and_setup_cores() which runs after program() returns.
                # Accept the device as reacquired once it is visible in the
                # JTAG chain; the debug infrastructure will be set up later.
                if reacquired_device is not None:
                    return

                last_error = None
            except Exception as exc:
                last_error = exc

            if time.monotonic() >= deadline:
                message = (
                    f"Timed out waiting for device reacquire after programming " f"{current_device}"
                )
                if last_error is not None:
                    raise PostProgramReacquireError(message) from last_error
                raise PostProgramReacquireError(message)

            if self.cs_server:
                self.cs_server.get_view("chipscope").run_events()
            time.sleep(poll_interval)

    def _on_device_rescan_needed(self, hw_server: ServerInfo, device: Device = None):
        """Callback invoked when a device requests device list rescan.

        This is called after device programming to ensure newly created debug paths
        are discovered and added to session.devices.

        Args:
            hw_server: The hw_server connection whose devices need rescanning
            device: The device object that triggered the rescan request
        """
        # Capture reference to avoid TOCTOU (time-of-check-time-of-use) race
        # where disconnect could set hw_server to None between check and use
        current_hw_server = self.hw_server
        if current_hw_server and current_hw_server == hw_server:
            self._need_to_scan_devices = True
            if device:
                self._rescan_after_program(device)

    @classmethod
    def disconnect_all_sessions(cls):
        sessions_to_disconnect = []
        with cls._session_lock:
            for id_key, (_, _, session) in cls._connected_session_dict.items():
                sessions_to_disconnect.append(session)
            for session in sessions_to_disconnect:
                try:
                    session.disconnect()
                except Exception:  # pragma: no cover
                    # TODO: Look into root cause later - happens intermittently in pytest infra causing tests to fail
                    pass
            cls._connected_session_dict = {}
            cls._cs_server_channel_ref_count = {}

    @staticmethod
    def _parse_url(url: str) -> Tuple[str, int]:
        param_str = process_param_str(url)
        host_port_dict = parse_params(param_str)
        host = host_port_dict.get("Host")
        port = int(host_port_dict.get("Port"))
        return host, port

    @staticmethod
    def _normalize_sync_result(result: Any) -> Any:
        while isinstance(result, list) and len(result) == 1:
            result = result[0]
        return result

    @staticmethod
    def _resolve_host(host: str) -> str:
        try:
            return socket.gethostbyname(host)
        except OSError:
            return host

    @classmethod
    def _remote_channel_matches_hw_server(cls, remote_channel_id: str, hw_server_url: str) -> bool:
        target_url = hw_server_url if hw_server_url.startswith("TCP:") else f"TCP:{hw_server_url}"
        try:
            target_host, target_port = cls._parse_url(target_url)
            remote_host, remote_port = cls._parse_url(remote_channel_id)
        except (TypeError, ValueError):
            return False

        if remote_port != target_port:
            return False

        target_hosts = {target_host, cls._resolve_host(target_host)}
        remote_hosts = {remote_host, cls._resolve_host(remote_host)}
        return bool(target_hosts & remote_hosts)

    @classmethod
    def _get_remote_disconnect_candidates(cls, server: ServerInfo, hw_server_url: str) -> List[str]:
        candidates: List[str] = []
        if not hw_server_url:
            return candidates

        try:
            locator = server.get_sync_service("Locator")
            remote_channels = cls._normalize_sync_result(locator.get_remote_channels().get())
            if isinstance(remote_channels, str):
                remote_channels = [remote_channels]
            if isinstance(remote_channels, list):
                for remote_channel_id in remote_channels:
                    if not isinstance(remote_channel_id, str):
                        continue
                    if cls._remote_channel_matches_hw_server(remote_channel_id, hw_server_url):
                        candidates.append(remote_channel_id)
        except Exception:
            pass

        fallback_url = hw_server_url if hw_server_url.startswith("TCP:") else f"TCP:{hw_server_url}"
        candidates.append(fallback_url)

        try:
            fallback_host, fallback_port = cls._parse_url(fallback_url)
            candidates.append(f"TCP:{cls._resolve_host(fallback_host)}:{fallback_port}")
        except (TypeError, ValueError):
            pass

        deduped_candidates: List[str] = []
        for candidate in candidates:
            if candidate and candidate not in deduped_candidates:
                deduped_candidates.append(candidate)
        return deduped_candidates

    @classmethod
    def _disconnect_remote_hw_server(cls, server: ServerInfo, hw_server_url: str) -> None:
        last_error: Optional[Exception] = None
        for remote_peer_id in cls._get_remote_disconnect_candidates(server, hw_server_url):
            try:
                result = server.disconnect_remote(remote_peer_id)
            except Exception as exc:
                last_error = exc
                continue

            if cls._normalize_sync_result(result):
                return

        if last_error is not None:
            raise last_error

    def connect_hw_server(self):
        if not self._hw_server_url:
            # A hw_server is always required when creating a session
            raise ValueError("hw_server_url must point to a valid hw_server")
        if self.hw_server:
            raise RuntimeError("hw_server already connected")
        server = Session._connect_server("hw_server", self._hw_server_url, connect_hw)
        self.hw_server = server

    def disconnect_hw_server(self):
        if not self.hw_server:
            # silently ignore disconnect calls if no server was ever connected - no harm
            return
        client_disconnect(self.hw_server)
        self.hw_server = None

    def connect_cs_server(self):
        if not self._cs_server_url:
            # A cs_server is OPTIONAL required when creating a session - so no error
            return
        if self.cs_server:
            raise RuntimeError("cs_server already connected")

        # Due to a client limitation, we can not connect multiple times to the
        # server from the same process. This causes errors due to the manager being
        # removed on second connect.
        #
        # WORKAROUND:
        # Reference count to safely share the cs_server connection
        #
        host, port = Session._parse_url(self._cs_server_url)
        ip = socket.gethostbyname(host)

        # entry = Tuple(ref_count, cs_server)
        entry = Session._cs_server_channel_ref_count.get((ip, port))
        if entry is None or not self._cs_server_sharing:
            # This is the first session - create ref_cnt entry and server
            server = Session._connect_server("cs_server", self._cs_server_url, client_connect)
            entry = (0, server)

        # Increment reference count for every session connection to same cs_server
        server = entry[1]
        entry = (entry[0] + 1, server)
        Session._cs_server_channel_ref_count[(ip, port)] = entry

        server.connect_remote(self.hw_server.url)
        if self._xvc_mm_server_url and server:
            server.connect_xvc(self._xvc_mm_server_url, self._hw_server_url)
        self.cs_server = server

    def disconnect_cs_server(self):
        if not self.cs_server:
            # silently ignore disconnect calls if no server was ever connected - no harm
            return
        host, port = Session._parse_url(self._cs_server_url)
        ip = socket.gethostbyname(host)

        # entry = Tuple(ref_count, cs_server)
        entry: Tuple[int, ServerInfo] = Session._cs_server_channel_ref_count.get((ip, port))
        if not entry:
            # This should not be possible - no entry indicates something unbalanced happened.
            raise RuntimeError("Error during disconnect - no ref_cnt for session.cs_server")

        ref_cnt, server = entry
        ref_cnt -= 1

        hw_server_url = self.hw_server.url if self.hw_server else self._hw_server_url
        self._disconnect_remote_hw_server(server, hw_server_url)
        self.cs_server = None

        if ref_cnt == 0 or not self._cs_server_sharing:
            # This is the last session - delete the ref count tracking entry from dict
            del Session._cs_server_channel_ref_count[(ip, port)]
            client_disconnect(server)
        else:
            # This is not the last session - just decrement the ref count
            Session._cs_server_channel_ref_count[(ip, port)] = (ref_cnt, server)

    def connect(self):
        self.connect_hw_server()

        with Session._session_lock:
            # cs_server changes are locked because they use a reference counted
            # shared cs_server - this is delicate
            self.connect_cs_server()

        Session._add_connection(self.hw_server, self.cs_server, self)

        try:
            # Quick sanity check - throws RuntimeError on version mismatch
            version_consistency_check(self.hw_server, self.cs_server, self._bypass_version_check)

            # Add event listeners
            if self._register_node_listeners:
                if self.hw_server:
                    for view_name in ["memory", "jtag", "debugcore"]:
                        self.hw_server.get_view(view_name).add_node_listener(self._dm_node_listener)
                if self.cs_server:
                    self.cs_server.get_view("chipscope").add_node_listener(self._dm_node_listener)
            if self._pre_device_scan_delay:
                time.sleep(self._pre_device_scan_delay / 1000.0)

            if self._initial_device_scan:
                # Ensures we have a set of pre-scanned devices ready to go for first use.
                # Downside is this does take up-front time, so it is optional.
                # If not done at session creation, it will be done when devices are first accessed with session.devices
                self.scan_devices()

        except RuntimeError:
            self.disconnect()
            t, v, tb = sys.exc_info()
            raise t(v).with_traceback(tb)

    def disconnect(self):
        # Cancel any running rescan futures before disconnect
        for device in self._get_devices_with_lock():
            if hasattr(device, "_cancel_rescan_future"):
                device._cancel_rescan_future()

        # Cleanup registered event listeners
        if self._register_node_listeners:
            if self.hw_server:
                for view_name in ["memory", "jtag", "debugcore"]:
                    self.hw_server.get_view(view_name).remove_node_listener(self._dm_node_listener)
            if self.cs_server:
                self.cs_server.get_view("chipscope").remove_node_listener(self._dm_node_listener)

        with Session._session_lock:
            # cs_server changes are locked because they use a reference counted
            # shared cs_server - this is delicate
            self.disconnect_cs_server()
        self.disconnect_hw_server()
        Session._remove_connection(self)

    def set_param(self, params: Dict[str, Any]):
        """Generic parameter get and set for low level chipscope server params"""
        if not isinstance(params, dict):
            message = "Please provide the params to set as a dictionary!"
            logger.error(message)
            raise TypeError(message)
        cs_service = self.cs_server.get_sync_service("ChipScope")
        cs_service.set_css_param(params)

    def get_param(self, params: Union[str, List[str]]) -> Dict[str, str]:
        """Generic parameter get and set for low level chipscope server params"""
        if isinstance(params, str):
            params = [params]
        cs_service = self.cs_server.get_sync_service("ChipScope")
        return cs_service.get_css_param(params).get()

    @property
    def handle(self) -> str:
        if self.cs_server and self.hw_server:
            handle_str = f"{self.cs_server.url}<->{self.hw_server.url}"
        elif self.hw_server:
            handle_str = f"{self.hw_server.url}"
        else:
            handle_str = "no_hw_server<->no_cs_server"
        return handle_str

    @property
    def chipscope_view(self) -> ViewInfo:
        view = None
        if self.cs_server:
            view = self.cs_server.get_view(chipscope)
        return view

    @property
    def jtag_devices(self) -> QueryList[JtagDevice]:
        def matcher(node, key, value):
            if getattr(node, key, None) == value:
                return True
            elif node.props.get(key) == value:
                return True
            return False

        devices: QueryList[JtagDevice] = QueryList()
        devices.set_custom_match_function(matcher)
        jtag_view_dict = get_jtag_view_dict(self.hw_server)
        view = self.hw_server.get_view("jtag")
        for cable_values in jtag_view_dict.values():
            devices_dict = cable_values.get("devices", {})
            jtag_index = 0
            for device_ctx in devices_dict.keys():
                jtag_device = view.get_node(ctx=device_ctx, cls=JtagDevice)
                # TODO: Check the correct way to get the jtag_index. I couldn't find in the props so I just add 1 each
                #       time we find a device on the cable...
                jtag_device.cable_serial = cable_values["props"].get("Serial")
                jtag_device.jtag_index = jtag_index
                jtag_index += 1
                devices.append(jtag_device)
        return devices

    @property
    def jtag_cables(self) -> QueryList[JtagCable]:
        # TODO: Transition jtag_cables -> target_cables.
        #       target_cables will return a higher level wrapper that can represent a virtual cable with virtual
        #       devices in the future. jtag_cables here only support the JtagCable node.
        def matcher(node, key, value):
            if getattr(node, key, None) == value:
                return True
            elif node.props.get(key) == value:
                return True
            return False

        jtag_cables: QueryList[JtagCable] = QueryList()
        jtag_cables.set_custom_match_function(matcher)
        jtag_view_dict = get_jtag_view_dict(self.hw_server)
        view = self.hw_server.get_view("jtag")
        for jtag_cable_ctx, cable_values in jtag_view_dict.items():
            jtag_cable = view.get_node(ctx=jtag_cable_ctx, cls=JtagCable)
            jtag_cables.append(jtag_cable)
        return jtag_cables

    @property
    def cables(self) -> QueryList[Cable]:
        """Returns a list of all cables connected to the hw_server.
        Similar to vivado get_hw_targets command. target_cables may be jtag or virtual.
        """
        retval = discover_cables(
            hw_server=self.hw_server,
            cs_server=self.cs_server,
            disable_core_scan=self._disable_core_scan,
            timeout=self._cable_timeout,
        )
        return retval

    def scan_devices(self) -> QueryList[Device]:
        if not self._cables_are_initialized:
            wait_for_all_cables_ready(self.hw_server, self._cable_timeout)
            self._cables_are_initialized = True
        devices = discover_devices(
            hw_server=self.hw_server,
            cs_server=self.cs_server,
            disable_core_scan=self._disable_core_scan,
            cable_ctx=None,
            disable_cache=self._disable_cache,
            enable_experimental_protocol_decode=self.enable_experimental_protocol_decode,
        )  # Gating logic goes Here

        # Register rescan callback on all discovered devices
        # This enables devices to notify the session when they need a rescan (e.g., after programming)
        for device in devices:
            if device.rescan_callback is None:
                device.rescan_callback = self._make_device_rescan_callback(
                    device, self._on_device_rescan_needed
                )
        self._set_device_with_lock(devices)
        return QueryList(self._devices)

    def _get_devices_with_lock(self) -> QueryList[Device]:
        with self._device_lock:
            return QueryList(self._devices)

    def _set_device_with_lock(self, devices: QueryList) -> None:
        with self._device_lock:
            self._devices = QueryList(devices)
            self._need_to_scan_devices = False

    @property
    def devices(self) -> QueryList[Device]:
        """Returns a list of devices connected to this hw_server and cable.
        Devices may span multiple jtag chains. No ordering is guaranteed.
        Devices are cached after scanning until an event changes state and
        requires a re-scan if caching is enabled.
        """
        if self._disable_cache or self._need_to_scan_devices:
            # Force scan from hardware (slow)
            devices = self.scan_devices()
        else:
            # Use the cached device list (fast)
            devices = self._get_devices_with_lock()
        return devices

    @property
    def memory(self) -> QueryList[Memory]:
        memory_node_list = QueryList()
        # This is not fast - improve it later. We don't need to query each
        # device - but it's clear and simple now.
        for device in self.devices:
            try:
                memory_nodes = device.memory
                for node in memory_nodes:
                    memory_node_list.append(node)
            except FeatureNotAvailableError:
                pass
        return memory_node_list

    @staticmethod
    def set_log_level(level: str = None):
        """
        Set the logging level for the ChipScoPy client. This applies to all sessions.
        Default is "NONE"

        Args:
            level: The minimum level to use for the logger. Valid levels are
                "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"

        """

        if level is None or level.upper() == "NONE":
            disable_domain("client")
            return

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level = level.upper()
        if level not in valid_levels:
            raise ValueError(
                f"Invalid log level '{level}'. Valid levels: {', '.join(valid_levels)}, NONE"
            )
        change_log_level(level)
        enable_domain("client")

    @staticmethod
    def _connect_server(server_name: str, server_url: str, connect_func: Callable) -> ServerInfo:
        try:
            return connect_func(server_url)
        except ConnectionRefusedError:
            # Shorten stack dump, by creating new exception.
            raise ConnectionRefusedError(
                f"Connection could not be opened to {server_name} @ {server_url}.\n"
                f"  Please make sure that {server_name} is running at the URL provided, "
                f"and firewall is not blocking."
            )
        except ConnectionError:
            # Shorten stack dump, by creating new exception.
            raise ConnectionRefusedError(
                f"Connection could not be opened to {server_name} @ {server_url}.\n"
                f"  Please make sure that {server_name} is running at the URL provided, "
                f"and firewall is not blocking."
            )
        except Exception as ex:
            # Chain exceptions.
            raise Exception(
                f"Connection could not be opened to {server_name} @ {server_url}."
            ) from ex

    def setup_stimgen(self, params: dict = None) -> stimgen.StimgenClient:
        """
        Sets up StimGen support on the cs_server
        :param params: Dict of arguments used for setting up StimGen support.
        +-------------------+----------------------+------------------------------------------+
        | Name              | Type                 | Description                              |
        +===================+======================+==========================================+
        | sg4db             |  str                 | Path to .sg4db file to use               |
        +-------------------+----------------------+------------------------------------------+
        :returns: StimgenClient instance
        """
        if params is None:
            params = {}
        return stimgen.setup(self.cs_server, self.hw_server, params)


###############################################################################
# Factory methods below
###############################################################################


def create_session(*, hw_server_url: str, cs_server_url: Optional[str] = None, **kwargs) -> Session:
    """
    Create a new session. Connect to the specified hw_server, and optionally
    the cs_server.

    - hw_server is used for programming and Versal Memory read/write operations
    - cs_server is used for higher level debug core communication

    Example 1: Default session create ::

        my_session = create_session(hw_server_url="TCP:localhost:3121",
                                    cs_server_url="TCP:localhost:3042")

    Example 2: Disable core scanning and server version checking ::

        my_session = create_session(hw_server_url="TCP:localhost:3121",
                                    cs_server_url="TCP:localhost:3042",
                                    disable_core_scan=True,
                                    bypass_version_check=True)

    Args:
        hw_server_url: Hardware server URL. Format ``TCP:<hostname>:<port>``
        cs_server_url: ChipScope server URL. Format ``TCP:<hostname>:<port>``

    Keyword Arguments:
        disable_core_scan: Set True to completely disable core scanning during discover_and_setup_debug_cores
        bypass_version_check: Set True to change hw_server and cs_server version mismatch to warning instead of error
        xvc_mm_server_url: Url for the testing xvc memory map server - For special debug core testing use cases
        cable_timeout: Seconds before timing out when detecting devices on a jtag cable
        initial_device_scan: Do an initial device scan when opening session (lazy initialization otherwise)
        pre_device_scan_delay: Time (in milliseconds) to wait after creating connections to hw_server before scanning for device
        disable_cache: Control client caching (experimental)
        auto_connect: Automatically connect to server(s) when session is created
        cs_server_sharing: Enable reference count to share cs_server connections

    Returns:
        New session object.

    """
    disable_core_scan = kwargs.get("disable_core_scan", False)
    bypass_version_check = kwargs.get("bypass_version_check", True)
    xvc_mm_server_url = kwargs.get("xvc_mm_server_url", None)
    cable_timeout = kwargs.get("cable_timeout", 4)
    initial_device_scan = kwargs.get("initial_device_scan", True)
    pre_device_scan_delay = kwargs.get("pre_device_scan_delay", 0)
    disable_cache = kwargs.get("disable_cache", False)
    auto_connect = kwargs.get("auto_connect", True)
    cs_server_sharing = kwargs.get("cs_server_sharing", False)
    enable_experimental_protocol_decode = kwargs.get("enable_experimental_protocol_decode", False)
    # Create session even if there already exists a session with the same cs_server and hw_server
    # It *should* be safe.
    session = Session(
        cs_server_url=cs_server_url,
        hw_server_url=hw_server_url,
        xvc_mm_server_url=xvc_mm_server_url,
        disable_core_scan=disable_core_scan,
        bypass_version_check=bypass_version_check,
        cable_timeout=cable_timeout,
        disable_cache=disable_cache,
        initial_device_scan=initial_device_scan,
        pre_device_scan_delay=pre_device_scan_delay,
        cs_server_sharing=cs_server_sharing,
        enable_experimental_protocol_decode=enable_experimental_protocol_decode,
    )
    if auto_connect:
        session.connect()
    return session


def delete_session(session: Session):
    """
    Delete a session. Shuts down any open server connections.

    Args:
        session: The session object to delete
    """
    session.disconnect()
