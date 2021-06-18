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
