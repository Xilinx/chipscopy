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
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, TYPE_CHECKING, Set, List

from chipscopy.api.ibert.aliases import (
    MB_ELF_VERSION,
    YK_SCAN_START_TIME,
    YK_SCAN_STOP_TIME,
    YK_SCAN_SLICER_DATA,
    YK_SCAN_SNR_VALUE,
)
from chipscopy.api.ibert.rx import RX
from chipscopy.utils.printer import printer

if TYPE_CHECKING:
    from chipscopy.dm import Node


@dataclass
class YKSample:
    slicer: List[float]
    snr: float


@dataclass
class YKScan:
    """
    Class for interacting with YK scans.
    **Please do not** create an instance of this class directly. Please use the factory method
    :py:func:`~chipscopy.api.ibert.create_yk_scans` instead.
    """

    rx: RX
    """:py:class:`RX` object attached to this eye scan"""

    name: str
    """Name of the eye scan"""

    updates_callback: Callable[["YKScan"], None] = None
    """Callback function called when eye scan has ended"""

    filter_by: Dict[str, Any] = field(default_factory=dict)

    scan_data: List[YKSample] = field(default_factory=list)
    """YK scan data samples in the order they are received"""

    stop_time: datetime = None
    """Time stamp of when eye scan was stopped in cs_server"""

    start_time: datetime = None
    """Time stamp of when eye scan was started in cs_server"""

    elf_version: str = None
    """ELF version read from the MicroBlaze"""

    _handle_from_cs_server: Optional[str] = None

    def __repr__(self):
        return self.name

    def __post_init__(self):
        self.rx.yk_scan = self

        self.filter_by = {"rx": self.rx, "name": self.name}

        self.rx.property.endpoint_tcf_node.add_listener(self._update_event_listener)

    def start(self):
        self._handle_from_cs_server = self.rx.core_tcf_node.start_yk_scan(rx_name=self.rx.handle)

    def _update_event_listener(self, node: "Node", updated_properties: Set[str]):
        # NOTE - This is called on the TCF event dispatcher thread
        if len(updated_properties) == 0 or self._handle_from_cs_server not in updated_properties:
            return

        try:
            report = node.props[self._handle_from_cs_server]

            if self.start_time is None and YK_SCAN_START_TIME in report:
                self.start_time = datetime.strptime(
                    report[YK_SCAN_START_TIME], "%Y-%m-%d %H:%M:%S.%f"
                )

            # Not expected to change after scan stop
            if self.stop_time is None and YK_SCAN_STOP_TIME in report:
                self.stop_time = datetime.strptime(
                    report[YK_SCAN_STOP_TIME], "%Y-%m-%d %H:%M:%S.%f"
                )

            # Not expected to change after scan start
            if self.elf_version is None and MB_ELF_VERSION in report:
                self.elf_version = report[MB_ELF_VERSION]

            if YK_SCAN_SLICER_DATA in report and YK_SCAN_SNR_VALUE in report:
                self.scan_data.append(
                    YKSample(report[YK_SCAN_SLICER_DATA], report[YK_SCAN_SNR_VALUE])
                )

            # If user has registered done callback function call it.
            if callable(self.updates_callback):
                try:
                    self.updates_callback(self)
                except Exception as e:
                    printer(
                        f"Unhandled exception during YK scan update callback!\n"
                        f"Exception - {str(e)}",
                        level="warning",
                    )

        except Exception as e:
            printer(
                f"Unhandled YK scan update exception on TCF thread!\nException - {str(e)}",
                level="warning",
            )

    def stop(self):
        """
        Stop eye scan, that is in-progress in the MicroBlaze

        """
        self.rx.core_tcf_node.terminate_yk_scan(rx_name=self.rx.handle)
