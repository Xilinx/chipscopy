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
from chipscopy.client import connect_xicom
from chipscopy.client.server_info import ServerInfo
from chipscopy.client.hbm_mc_client import HBMMCClient
from chipscopy.client.core import get_cs_view, CoreParent
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf import protocol
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.dm.request import DoneCallback
from chipscopy.proxies.HBMProxy import SERVICE_NAME, HBMMS_DOMAIN_INDEX


class HBMClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "hbm"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(SERVICE_NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize(self.ctx, done_cb))

    def write32(self, write_addr: int, data: int, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.write32(self.ctx, write_addr, data, HBMMS_DOMAIN_INDEX, done_cb)
        return self.add_pending(token)

    def read32(self, read_addr: int, read_word_count: int, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.read32(self.ctx, read_addr, read_word_count, HBMMS_DOMAIN_INDEX, done_cb)
        return self.add_pending(token)

    def refresh_property(self, names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_property(self.ctx, names, done_cb)
        return self.add_pending(token)

    def terminate(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.terminate(self.ctx, done_cb))

    #
    #  Service specific user interfaces
    #
    def get_hbm_mc(self, index: int, done: DoneCallback):
        mc_count = len(self.children)
        if (index < 0) or (index + 1 == mc_count):
            raise Exception("Invalid HBM MC index given.")

        mc_context = self.children[index]
        hbm_mc = self.manager.get_node(mc_context, HBMMCClient)
        done(result=hbm_mc)
        return

    def get_enabled_mcs_mask(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_enabled_mcs_mask(self.ctx, done_cb)
        return self.add_pending(token)

    def get_init_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_init_status(self.ctx, done_cb)
        return self.add_pending(token)

    def refresh_temp_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_temp_status(self.ctx, done_cb)
        return self.add_pending(token)


def get_hbm(server: ServerInfo, hbm_index=0) -> HBMClient:

    cs_view = get_cs_view(server)
    dpc = None
    for node in cs_view.get_children():
        if "DPC" in node.props.get("Name"):
            dpc = cs_view.get_node(node.ctx, CoreParent)
            break

    # Find HBM stack under DPC with a given HBM index
    hbm = server.cs_target(parent=dpc, type="hbm", index=hbm_index, cls=HBMClient)

    return hbm


def get_hbm_mc(server: ServerInfo, hbm_stack: HBMClient, mc_index=0) -> HBMMCClient:

    # Find HBM MC under specific HBM Stack with a given MC index
    hbm_mc = server.cs_target(parent=hbm_stack, type="hbm_mc", index=mc_index, cls=HBMMCClient)

    return hbm_mc
