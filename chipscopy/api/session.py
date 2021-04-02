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

from typing import Optional, Dict, Any, List, Union

from chipscopy.api.device.device_identification import DeviceIdentification
from chipscopy.dm import chipscope
from chipscopy.utils.logger import log
from chipscopy.utils.version import version_consistency_check
from chipscopy.client import connect, disconnect
from chipscopy.client.util import connect_hw
from chipscopy.client.view_info import ViewInfo, TargetFilter
from chipscopy.client.server_info import ServerInfo
from chipscopy.api.containers import QueryList
from chipscopy.api.device.device import Device
from chipscopy.api.device.device_scanner import DeviceScanner
from chipscopy.api.memory import MemoryDevice

DOMAIN_NAME = "client"


class Session:
    """Top level object that tracks a connection to a hardware server and optionally, chipscope
    server. To create and destroy a session, use the factory function
    :py:func:`~chipscopy.create_session` and :py:func:`~chipscopy.delete_session`
    respectively.
    """

    def __init__(
        self,
        *,
        hw_server_url: str,
        cs_server_url: Optional[str] = None,
        xvc_server_url: Optional[str] = None,
        disable_core_scan: bool,
        bypass_version_check: bool,
    ):
        if not hw_server_url:
            raise ValueError("hw_server_url must point to a valid hw_server")

        self.disable_core_scan = disable_core_scan

        self.hw_server: ServerInfo = Session._connect_hw_server(hw_server_url)
        self.cs_server: Optional[ServerInfo] = None
        if cs_server_url:
            self.cs_server = Session._connect_cs_server(cs_server_url)
            self.cs_server.connect_remote(self.hw_server.url)
            if xvc_server_url:
                self.cs_server.connect_xvc(xvc_server_url, hw_server_url)
            self.handle = f"{self.cs_server.url}<->{self.hw_server.url}"
        else:
            self.handle: str = f"{self.hw_server.url}"

        version_consistency_check(self.hw_server, self.cs_server, bypass_version_check)

        # TODO: Stop using chipscope_view in noc_perfmon.py, sptg_example.py and make member private
        self.chipscope_view: Optional[ViewInfo] = None
        if self.cs_server:
            self.chipscope_view = self.cs_server.get_view(chipscope)

    def __str__(self):
        return f"Session properties - (Handle, {self.handle})"

    def set_param(self, params: Dict[str, Any]):
        """Generic parameter get and set for low level chipscope server params"""
        if not isinstance(params, dict):
            message = "Please provide the params to set as a dictionary!"
            log[DOMAIN_NAME].error(message)
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
    def devices(self):
        """Returns a list of devices connected to this hw_server. Devices may
        contain several chains so don't always assume a single jtag chain
        in-order is returned"""
        devices: QueryList[Device] = QueryList()
        device_scanner = DeviceScanner(self.hw_server, self.cs_server)
        for device_identification in device_scanner.get_scan_results():
            device_node = device_identification.find_top_level_device_node(self.hw_server)
            if device_node.device_wrapper is None:
                device_node.device_wrapper = Device(
                    hw_server=self.hw_server,
                    cs_server=self.cs_server,
                    device_identification=device_identification,
                    disable_core_scan=self.disable_core_scan,
                )
            devices.append(device_node.device_wrapper)
        return devices

    @property
    def mem(self):
        view_info = self.hw_server.get_view("memory")
        return TargetFilter(view_info, node_cls=MemoryDevice)

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
        try:
            hw_server: ServerInfo = connect_hw(hw_server_url)
        except ConnectionRefusedError as ex:
            # TODO - Include this message in the exception.
            # print_msg(
            #     f"Connection could not be opened to hw_server @ {hw_server_url}. "
            #     f"Please make sure that hw_server is running at the URL provided",
            #     msg_level="error",
            # )
            raise ex
        except Exception as ex:
            ex.args = (
                f"Connection could not be opened to hw_server @ {hw_server_url}. "
                f"Following error occurred - {str(ex)}",
            )
            raise ex
        return hw_server

    @staticmethod
    def _connect_cs_server(cs_server_url: str) -> ServerInfo:
        try:
            cs_server = connect(cs_server_url)
        except ConnectionRefusedError as ex:
            # TODO - Include this message in the exception.
            # print_msg(
            #     f"Connection could not be opened to cs_server @ {cs_server_url}. "
            #     f"Please make sure that cs_server is running at the URL provided",
            #     msg_level="error",
            # )
            raise ex
        except Exception as ex:
            ex.args = (
                f"Connection could not be opened to cs_server @ {cs_server_url}. "
                f"Following error occurred - {str(ex)}",
            )
            raise ex
        return cs_server


###############################################################################
# Factory methods below
###############################################################################


def create_session(*, hw_server_url: str, cs_server_url: Optional[str] = None, **kwargs) -> Session:
    """
    Create a new session for hw_server and optionally, cs_server

    Example:

        ::

            my_session = create_session(hw_server_url="localhost:3121",
                                        cs_server_url="localhost:3042")

    .. note:: In the case of multiple clients sharing a single hw_server, it may be
        necessary to disable the intrusive core scanning in the second
        instance (See below for the "disable_core_scan" argument usage).
        This uses cached debug core values for all devices in the session.
        This will be automated in the future and the argument will be
        disabled.
        Example:

            ::

                my_session = create_session(hw_server_url="existing_hw_server_host:3121",
                                            cs_server_url="localhost:3042",
                                            disable_core_scan=True)

    Args:
        hw_server_url: Hardware server URL. Format ``<hostname>:<port>``
        cs_server_url: ChipScope server URL. Format ``<hostname>:<port>``

    Returns:
        New session object.

    """

    # Optional arguments in kwargs -
    #    disable_core_scan - This determines how devices setup the debug cores.
    #         It is possible to disable the setup_debug_cores detection
    #         if it is likely to interfere with an existing hw_server
    disable_core_scan = kwargs.get("disable_core_scan", False)
    bypass_version_check = kwargs.get("bypass_version_check", True)
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
    Delete a session

    Args:
        session: The session object to delete

    """
    disconnect(session.hw_server)

    if session.cs_server is None:
        return

    session.cs_server.disconnect_remote(f"TCP:{session.hw_server.url}")
    disconnect(session.cs_server)
