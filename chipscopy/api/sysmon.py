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

        self.schedule = None

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
        schedule = self.core_tcf_node.refresh_measurement_schedule(done)
        self.schedule = schedule
        return schedule

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

    def read_sensor(self, sensor: str) -> float:
        """
        Read single sensor value from hw
        Args:
            sensor:  the name of the sensor to read

        Returns:
            refreshed value of specific sensor (float) or None if sensor isn't detected in design

        """

        if self.schedule is None:
            print(
                f"warning: read_sensor(): measurement schedule is empty or has not been refreshed"
            )
            return None

        if sensor not in self.schedule.values():
            print(
                f"warning: read_sensor(): requested sensor {sensor} is not in the measurement schedule"
            )
            return None

        supply_idx = None
        for idx, s in self.schedule.items():
            if sensor == s:
                supply_idx = idx
                break

        supply_name = f"supply{supply_idx}"
        # greedy
        current_value = self.core_tcf_node.refresh_property(supply_name)
        return current_value[supply_name]

    def read_sensors(self, sensors: List[str]) -> Dict[str, float]:
        """
        Read a list of sensor values from hw
        Args:
            sensors:  list of the names of the sensors to read

        Returns:
            refreshed values of specific sensors (float)
            if the sensor isn't sequenced in the design then a warning msg is printed and the sensor is dropped from
            the list
        """
        props_to_refresh = []
        out_data = {}
        supply_x_map = {}
        if self.schedule is None:
            print(
                f"warning: read_sensors(): measurement schedule is empty or has not been refreshed"
            )
            return None

        for sensor in sensors:
            if sensor not in self.schedule.values():
                print(
                    f"warning: read_sensors(): requested sensor {sensor} is not in the measurement schedule"
                )
                continue

            supply_idx = None
            for idx, s in self.schedule.items():
                if sensor == s:
                    supply_idx = idx
                    break

            out_data[sensor] = None
            supply_name = f"supply{supply_idx}"
            supply_x_map[supply_name] = sensor
            props_to_refresh.append(supply_name)

        current_sensor_values = self.core_tcf_node.refresh_property(props_to_refresh)
        for supply_name, value in current_sensor_values.items():
            out_data[supply_x_map[supply_name]] = value

        return out_data

    def read_temp(self) -> Dict[str, float]:
        """
        Read temp values from hw
        Args:
            None

        Returns:
            refreshed value of device_temp, max, and min in Celsius
        """
        temp_dict = self.core_tcf_node.refresh_property(
            ["device_temp", "device_temp_max_max", "device_temp_min_min"]
        )
        return temp_dict
