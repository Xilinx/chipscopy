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

from typing import List, Dict

from chipscopy import dm
from chipscopy.client.core import CoreClient
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.SysMonProxy import SYSMON_SERVICE_NAME


class SysMonCoreClient(CoreClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "sysmon"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(SYSMON_SERVICE_NAME)

    def post_init(self):
        self.refresh_property_group(["status"])

    def refresh_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    #
    #  General methods
    #
    def stream_sensor_data(self, interval: int, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.stream_sensor_data(self.ctx, interval, done_cb))

    def initialize_sensors(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize_sensors(self.ctx, done_cb))

    def refresh_measurement_schedule(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.refresh_measurement_schedule(self.ctx, done_cb))

    def get_measurements(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.get_measurements(self.ctx, done_cb))

    def get_all_sensors(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.get_all_sensors(self.ctx, done_cb))

    def configure_measurement_schedule(
        self, measurements: Dict[str, str], done: DoneHWCommand = None
    ):
        service, done_cb = self.make_done(done)
        return self.add_pending(
            service.configure_measurement_schedule(self.ctx, measurements, done_cb)
        )

    def configure_temp_and_vccint(self, done: DoneHWCommand = None):  # pragma: no cover
        service, done_cb = self.make_done(done)
        return self.add_pending(service.configure_temp_and_vccint(self.ctx, done_cb))
