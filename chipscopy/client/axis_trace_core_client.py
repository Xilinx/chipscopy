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

from chipscopy import dm
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf.services import DoneHWCommand


SERVICE_NAME = "AxisTrace"


class AxisTraceClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.core_type == 5

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(SERVICE_NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize(self.ctx, done_cb))

    def terminate(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.terminate(self.ctx, done_cb))

    #
    # Trace Core specific methods
    #
    def acquire(
        self,
        input_index: int,
        input_name: str,
        destination_address: int,
        memory_depth: int,
        done: DoneHWCommand = None,
    ):
        service, done_cb = self.make_done(done)
        return self.add_pending(
            service.acquire(
                self.ctx, input_index, input_name, destination_address, memory_depth, done_cb
            )
        )

    def release(self, input_index: int, input_name: str, force: bool, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.release(self.ctx, input_index, input_name, force, done_cb))
