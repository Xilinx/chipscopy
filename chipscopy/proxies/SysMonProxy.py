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

from typing import Dict, List
from chipscopy.tcf.services import Service, DoneHWCommand
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy

SYSMON_SERVICE_NAME = "SysMon"


class SysMonService(Service):
    def getName(self) -> str:
        return SYSMON_SERVICE_NAME


class SysMonProxy(CorePropertyProxy, SysMonService):
    def __init__(self, channel):
        super(SysMonProxy, self).__init__(channel)
        self.listeners = {}

    def stream_sensor_data(self, node_id: str, interval: int, done: DoneHWCommand) -> None:
        return self.send_xicom_command("streamSensorData", (node_id, interval), done)

    def initialize_sensors(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("initializeSensors", (node_id,), done)

    def refresh_measurement_schedule(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("refreshMeasurementSchedule", (node_id,), done)

    def get_measurements(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("getMeasurements", (node_id,), done)

    def get_all_sensors(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("getAllSensors", (node_id,), done)

    def configure_measurement_schedule(
        self, node_id: str, measurements: Dict[str, str], done: DoneHWCommand
    ):
        return self.send_xicom_command(
            "configureMeasurementSchedule", (node_id, measurements), done
        )

    def configure_temp_and_vccint(self, node_id: str, done: DoneHWCommand):  # pragma: no cover
        return self.send_xicom_command("configureTempAndVCCINT", (node_id,), done)
