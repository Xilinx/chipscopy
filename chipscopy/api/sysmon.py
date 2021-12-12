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

from typing import List, ClassVar, Dict
from dataclasses import dataclass

from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy.tcf.services import DoneHWCommand


@dataclass
class Sysmon(DebugCore["SysMonCoreClient"]):
    """Sysmon is the top level API for accessing System Monitor in Versal."""

    def __init__(self, sysmon_tcf_node):
        super(Sysmon, self).__init__(CoreType.SYSMON, sysmon_tcf_node)

        self.name = sysmon_tcf_node.props["Name"]

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name}

    def __str__(self):
        return self.name

    def initialize_sensors(self, done: DoneHWCommand = None):
        """
        Initializes all of the server side constructs for sysmon, required for most subsequent APIs.

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            No data is returned directly from this method.

        """
        self.core_tcf_node.initialize_sensors(done)

    def refresh_measurement_schedule(self, done: DoneHWCommand = None) -> Dict[int, str]:
        """
        Dynamically scans the SysMon to determine the sensors scheduled into the system, in order.


        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            Returns a dict where the keys are the root IDs and the values are the named sensors.

        """
        sensors = self.core_tcf_node.refresh_measurement_schedule(done)
        return sensors

    def get_measurements(self, done: DoneHWCommand = None) -> List[object]:
        """
        Advanced API

        Returns the measurement objects

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            Returns a list of measurement configuration objects

        """
        sensors = self.core_tcf_node.get_measurements(done)
        return sensors

    def get_all_sensors(self, done: DoneHWCommand = None) -> dict:
        """
        This function is identical to ``get_supported_sensors`` in customer releases. For VnC teams this API offers
        internal sensors. For information on how to use this API please contact @dkopelov or #chipscope.

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            A list of strings representing all sensors for the connected device.

        """
        sensors = self.core_tcf_node.get_all_sensors(done)
        return sensors

    def configure_measurement_schedule(
        self, measurements: Dict[str, str], done: DoneHWCommand = None
    ) -> None:
        self.core_tcf_node.configure_measurement_schedule(measurements, done)

    def stream_sensor_data(self, interval: int, done: DoneHWCommand = None) -> None:
        """
        This API configures polling in hw_server to stream the data from the measurement schedule (including device
        temps) at the specified ``interval``.

        To process the incoming data, a `dm.NodeListener` must be declared and registered on this node.


        node_listener = dm.NodeListener(sysmon)

        session.chipscope_view.add_node_listener(node_listener)

        Args:
            interval: poll period (in ms)
            done: Optional command callback that will be invoked when the response is received.
        """
        self.core_tcf_node.stream_sensor_data(interval, done)
