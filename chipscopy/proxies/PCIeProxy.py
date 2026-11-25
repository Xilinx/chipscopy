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

from chipscopy.tcf.services import Service, DoneHWCommand
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy
from chipscopy.utils.logger import get_logger

PCIE_SERVICE_NAME = "PCIe"

logger = get_logger("proxy_pcie")


class PCIeService(Service):
    def getName(self) -> str:
        return PCIE_SERVICE_NAME


class PCIeProxy(CorePropertyProxy, PCIeService):
    def __init__(self, channel):
        super(PCIeProxy, self).__init__(channel)
        self.listeners = {}

    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        logger.debug("Sending initializeCmd")
        return self.send_xicom_command("initialize", (node_id,), done)

    def read_ltssm_trace(self, node_id: str, done: DoneHWCommand):
        logger.debug("Sending readLtssmTraceCmd")
        return self.send_xicom_command("readLtssmTrace", (node_id,), done)

    def reset_core(self, node_id: str, done: DoneHWCommand):
        logger.debug("Sending resetCoreCmd")
        return self.send_xicom_command("resetCore", (node_id,), done)
