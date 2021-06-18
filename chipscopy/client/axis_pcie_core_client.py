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

from chipscopy.client.core_property_client import CorePropertyClient

from chipscopy import dm
from chipscopy.client.core import CoreClient
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.utils.logger import log


DOMAIN_NAME = "client_axis_pcie"

AXIS_PCIE_NODE_NAME = "pcie"
AXIS_PCIE_SERVICE_NAME = "AxisPCIe"


class AxisPCIeCoreClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return_val = node.type and node.type == AXIS_PCIE_NODE_NAME
        return return_val

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(AXIS_PCIE_SERVICE_NAME)

    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initializing {AXIS_PCIE_SERVICE_NAME} service")
        token = service.initialize(self.ctx, done_cb)
        return self.add_pending(token)

    def read_data(self, done: DoneHWCommand):
        service, done_cb = self.make_done(done)
        token = service.read_data(self.ctx, done_cb)
        return self.add_pending(token)

    def reset_core(self, done: DoneHWCommand):
        service, done_cb = self.make_done(done)
        token = service.reset_core(self.ctx, done_cb)
        return self.add_pending(token)

    # def read_data_region(self, int start_addr, int num_bytes, done: DoneHWCommand):
    #     service, done_cb = self.make_done(done)
    #     token = service.read_data_region(self.ctx, start_addr, num_bytes, done_cb)
    #     return self.add_pending(token)
