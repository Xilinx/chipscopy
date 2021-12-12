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
from chipscopy import dm
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.HBMMCProxy import SERVICE_NAME


class HBMMCClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "hbm_mc"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(SERVICE_NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize(self.ctx, done_cb))

    def write32(self, write_addr: int, data: int, domain_index: int, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.write32(self.ctx, write_addr, data, domain_index, done_cb)
        return self.add_pending(token)

    def read32(
        self, read_addr: int, read_word_count: int, domain_index: int, done: DoneHWCommand = None
    ):
        service, done_cb = self.make_done(done)
        token = service.read32(self.ctx, read_addr, read_word_count, domain_index, done_cb)
        return self.add_pending(token)

    #
    #  Service specific user interfaces
    #
    def refresh_property(self, names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_property(self.ctx, names, done_cb)
        return self.add_pending(token)
