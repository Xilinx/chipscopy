# Copyright 2022 Xilinx, Inc.
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

from chipscopy.client.axis_trace_core_client import SERVICE_NAME
from chipscopy.tcf.services import DoneHWCommand, Service
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy


class AxisTraceService(Service):
    def getName(self) -> str:
        return SERVICE_NAME


class AxisTraceProxy(CorePropertyProxy, AxisTraceService):
    def __init__(self, channel):
        super().__init__(channel)
        self._listeners = {}

    #
    #  General methods
    #
    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("initialize", (node_id,), done)

    def terminate(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("terminate", (node_id,), done)

    def acquire(
        self,
        node_id: str,
        input_index: int,
        input_name: str,
        destination_address: int,
        memory_depth: int,
        done: DoneHWCommand,
    ) -> None:
        return self.send_xicom_command(
            "acquire", (node_id, input_index, input_name, destination_address, memory_depth), done
        )

    def release(
        self, node_id: str, input_index: int, input_name: str, force: bool, done: DoneHWCommand
    ) -> None:
        return self.send_xicom_command("release", (node_id, input_index, input_name, force), done)
