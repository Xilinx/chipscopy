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
import sys
from typing import Optional, Dict, Any, List, Union, Callable

from chipscopy.dm import chipscope
from chipscopy.utils.logger import log
from chipscopy.utils.version import version_consistency_check
from chipscopy.client import connect, disconnect
from chipscopy.client.util import connect_hw
from chipscopy.client.view_info import TargetFilter, ViewInfo
from chipscopy.client.server_info import ServerInfo
from chipscopy.api.containers import QueryList
from chipscopy.api.device.device import Device
from chipscopy.api.device.device_scanner import DeviceScanner
from chipscopy.api.memory import Memory

DOMAIN_NAME = "client"

# Global session tracking here. We keep a list of who is connected at any time.
# Format:
#    dict[hex(id(session))] = (hw_server, cs_server, session)
_connected_session_dict: dict = {}


class Session:
    """Top level object that tracks a connection to a hardware server and optionally, chipscope
    server. To create and destroy a session, use the factory function
    create_session() and delete_session().
    """

    _hw_server_url: str = None
    _cs_server_url: str = None
    _xvc_server_url: str = None
    _hw_server: Optional[ServerInfo] = None
    _cs_server: Optional[ServerInfo] = None

    def __init__(
        self,
        *,
        hw_server_url: str,
        cs_server_url: Optional[str] = None,
        xvc_server_url: Optional[str] = None,
        disable_core_scan: bool,
        bypass_version_check: bool,
    ):
        self._disable_core_scan = disable_core_scan
        self._bypass_version_check = bypass_version_check
        self._hw_server_url = hw_server_url
        self._cs_server_url = cs_server_url
        self._xvc_server_url = xvc_server_url
        self.connect()

    def __str__(self):
        return f"{self.handle}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        delete_session(self)

    @classmethod
    def _add_connection(
        cls, hw_server: ServerInfo, cs_server: Optional[ServerInfo], session: "Session"
    ):
        _connected_session_dict[hex(id(session))] = (hw_server, cs_server, session)

    @classmethod
    def _remove_connection(cls, session: "Session"):
        del _connected_session_dict[hex(id(session))]

    @classmethod
    def disconnect_all_sessions(cls):
        sessions_to_disconnect = []
        for id_key, (_, _, session) in _connected_session_dict.items():
            sessions_to_disconnect.append(session)
        for session in sessions_to_disconnect:
            session.disconnect()

    def connect(self):
        if not self._hw_server_url:
            raise ValueError("hw_server_url must point to a valid hw_server")
        self._hw_server = Session._connect_hw_server(self._hw_server_url)
        if self._cs_server_url:
            self._cs_server = Session._connect_cs_server(self._cs_server_url)
            self._cs_server.connect_remote(self._hw_server.url)
            if self._xvc_server_url:
                self._cs_server.connect_xvc(self._xvc_server_url, self._hw_server_url)
        Session._add_connection(self._hw_server, self._cs_server, self)
        try:
            # Quick sanity check - throws RuntimeError on version mismatch
            self._version_check()
        except RuntimeError:
            self.disconnect()
            t, v, tb = sys.exc_info()
            raise t(v).with_traceback(tb)

    def disconnect(self):
        Session._remove_connection(self)
        if self._cs_server:
            self._cs_server.disconnect_remote(f"TCP:{self._hw_server.url}")
            disconnect(self._cs_server)
            self._cs_server = None
        disconnect(self._hw_server)
        self._hw_server = None

    def set_param(self, params: Dict[str, Any]):
        """Generic parameter get and set for low level chipscope server params"""
        if not isinstance(params, dict):
            message = "Please provide the params to set as a dictionary!"
            log[DOMAIN_NAME].error(message)
            raise TypeError(message)
        cs_service = self._cs_server.get_sync_service("ChipScope")
        cs_service.set_css_param(params)

    def get_param(self, params: Union[str, List[str]]) -> Dict[str, str]:
        """Generic parameter get and set for low level chipscope server params"""
        if isinstance(params, str):
            params = [params]
        cs_service = self._cs_server.get_sync_service("ChipScope")
        return cs_service.get_css_param(params).get()

    @property
    def hw_server(self) -> ServerInfo:
        return self._hw_server

    @property
    def cs_server(self) -> ServerInfo:
        return self._cs_server

    @property
    def handle(self) -> str:
        if self._cs_server and self._hw_server:
            handle_str = f"{self._cs_server.url}<->{self._hw_server.url}"
        elif self._hw_server:
            handle_str = f"{self._hw_server.url}"
        else:
            handle_str = "no_hw_server<->no_cs_server"
        return handle_str

    @property
    def chipscope_view(self) -> ViewInfo:
        view = None
        if self._cs_server:
            view = self._cs_server.get_view(chipscope)
        return view

    @property
    def devices(self) -> QueryList[Device]:
        """Returns a list of devices connected to this hw_server. Devices may
        contain several chains so don't always assume a single jtag chain
        in-order is returned"""
        devices: QueryList[Device] = QueryList()
        device_scanner = DeviceScanner(self._hw_server, self._cs_server)
        device_scanner.scan_devices()
        for device_identification in device_scanner.get_scan_results():
            device_node = device_identification.find_top_level_device_node(self._hw_server)
            if device_node.device_wrapper is None:
                device_node.device_wrapper = Device(
                    hw_server=self._hw_server,
                    cs_server=self._cs_server,
                    device_identification=device_identification,
                    disable_core_scan=self._disable_core_scan,
                )
            devices.append(device_node.device_wrapper)
        return devices

    @property
    def memory(self) -> QueryList[Memory]:
        memory_node_list = QueryList()
        # This is not fast - improve it later. We don't need to query each
        # device - but it's clear and simple now.
        for device in self.devices:
            memory_nodes = device.memory
            for node in memory_nodes:
                memory_node_list.append(node)
        return memory_node_list

    @staticmethod
    def set_log_level(level: str = None):
        """
        Set the logging level for the ChipScoPy client. This applies to all sessions.
        Default is "NONE"

        Args:
            level: The minimum level to use for the logger. Valid levels are
                "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL", "NONE"

        """

        if level is None:
            log.disable_domain(DOMAIN_NAME)

        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL", "NONE"]
        level = level.upper()
        assert level in valid_levels
        log.change_log_level(level)
        log.enable_domain(DOMAIN_NAME)

    @staticmethod
    def _connect_hw_server(hw_server_url: str) -> ServerInfo:
        return Session._connect_server("hw_server", hw_server_url, connect_hw)

    @staticmethod
    def _connect_cs_server(cs_server_url: str) -> ServerInfo:
        return Session._connect_server("cs_server", cs_server_url, connect)

    @staticmethod
    def _connect_server(server_name: str, server_url: str, connect_func: Callable) -> ServerInfo:
        connection_refused_msg = None
        try:
            server: ServerInfo = connect_func(server_url)
        except ConnectionRefusedError:
            # Shorten stack dump, by creating new exception.
            connection_refused_msg = (
                f"Connection could not be opened to {server_name} @ {server_url}.\n"
                f"  Please make sure that {server_name} is running at the URL provided, and firewall is not blocking."
            )
        except Exception as ex:
            # Chain exceptions.
            raise Exception(
                f"Connection could not be opened to {server_name} @ {server_url}."
            ) from ex

        if connection_refused_msg:
            raise ConnectionRefusedError(connection_refused_msg)
        return server

    def _version_check(self):
        version_consistency_check(self._hw_server, self._cs_server, self._bypass_version_check)


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

    Returns:
        New session object.

    """
    # Optional arguments in kwargs -
    #    disable_core_scan - This determines how devices setup the debug cores.
    #         It is possible to disable the setup_debug_cores detection
    #         if it is likely to interfere with an existing hw_server
    disable_core_scan = kwargs.get("disable_core_scan", False)
    bypass_version_check = kwargs.get("bypass_version_check", False)
    xvc_server_url = kwargs.get("xvc_server_url", None)

    # Create session even if there already exists a session with the same cs_server and hw_server
    # It *should* be safe.
    return Session(
        cs_server_url=cs_server_url,
        hw_server_url=hw_server_url,
        xvc_server_url=xvc_server_url,
        disable_core_scan=disable_core_scan,
        bypass_version_check=bypass_version_check,
    )


def delete_session(session: Session):
    """
    Delete a session. Shuts down any open server connections.

    Args:
        session: The session object to delete
    """
    session.disconnect()
