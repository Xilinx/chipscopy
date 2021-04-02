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

from chipscopy.tcf.services import Service, DoneHWCommand
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy
from chipscopy.utils.logger import log

AXIS_PCIE_NODE_NAME = "pcie"
AXIS_PCIE_SERVICE_NAME = "AxisPCIe"

DOMAIN_NAME = "proxy_pcie"


class AxisPCIeService(Service):
    def getName(self) -> str:
        return AXIS_PCIE_SERVICE_NAME


class AxisPCIeProxy(CorePropertyProxy, AxisPCIeService):
    def __init__(self, channel):
        super(AxisPCIeProxy, self).__init__(channel)
        self.listeners = {}

    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        log[DOMAIN_NAME].debug("Sending initializeCmd")
        return self.send_xicom_command("initialize", (node_id,), done)

    def read_data(self, node_id: str, done: DoneHWCommand) -> bool:
        return self.send_xicom_command("read_data", (node_id,), done)

    def reset_core(self, node_id: str, done: DoneHWCommand) -> bool:
        return self.send_xicom_command("reset_core", (node_id,), done)
