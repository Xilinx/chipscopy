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

from typing import List
from chipscopy.tcf import services
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy
from chipscopy.client.core_property_client import PropertyValues

SERVICE_NAME = "AxisDDR"


class AxisDDRProxy(CorePropertyProxy, services.Service):
    def __init__(self, channel):
        super().__init__(channel)
        self._listeners = {}

    #
    #  General methods
    #
    def getName(self):
        return SERVICE_NAME

    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("initialize", (node_id,), done)

    def terminate(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("terminate", (node_id,), done)

    def refresh_property(
        self, node_id: str, prop_names: List[str], done: DoneHWCommand
    ) -> PropertyValues:
        return self.send_xicom_command("refreshProperty", (node_id, prop_names), done)

    def refresh_cal_status(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("refreshCalStatus", (node_id,), done)

    def refresh_cal_margin(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("refreshCalMargin", (node_id,), done)

    def get_cal_margin_mode(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("getCalMarginMode", (node_id,), done)
