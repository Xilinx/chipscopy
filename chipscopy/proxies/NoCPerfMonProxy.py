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

NOC_PERFMON_SERVICE_NAME = "NoCPerfMon"


class NoCPerfMonService(Service):
    def getName(self) -> str:
        return NOC_PERFMON_SERVICE_NAME


class NoCPerfMonProxy(CorePropertyProxy, NoCPerfMonService):
    def __init__(self, channel):
        super(NoCPerfMonProxy, self).__init__(channel)
        self.listeners = {}

    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("initialize", (node_id,), done)

    def discover_noc_elements(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("discoverNOCElements", (node_id,), done)

    def configure_monitors(self, params, done: DoneHWCommand) -> None:
        return self.send_xicom_command("configureMonitors", (params["node_id"], params), done)

    def get_supported_sampling_periods(self, params, done: DoneHWCommand):
        return self.send_xicom_command(
            "getSupportedSamplingPeriods", (params["node_id"], params), done
        )

    def get_clk_info(self, node_id: str, done: DoneHWCommand):  # pragma: no cover
        return self.send_xicom_command("getClkInfo", (node_id,), done)

    def enumerate_noc_elements(self, params, done: DoneHWCommand):
        return self.send_xicom_command("enumerateNocElements", (params["node_id"], params), done)
