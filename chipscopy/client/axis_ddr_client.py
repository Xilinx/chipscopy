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

from typing import Dict, List

from chipscopy import dm
from chipscopy.dm import chipscope
from chipscopy.client import connect_xicom
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.AxisDDRProxy import SERVICE_NAME as AXIS_DDR_NAME


class AxisDDRClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "ddrmc"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(AXIS_DDR_NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand):
        service, done_cb = self.make_done(done)
        token = service.initialize(self.ctx, done_cb)
        return self.add_pending(token)

    def terminate(self, done: DoneHWCommand):
        service, done_cb = self.make_done(done)
        token = service.terminate(self.ctx, done_cb)
        return self.add_pending(token)

    def refresh_property(self, names: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_property(self.ctx, names, done_cb)
        return self.add_pending(token)

    def refresh_cal_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_cal_status(self.ctx, done_cb)
        return self.add_pending(token)

    def refresh_cal_margin(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_cal_margin(self.ctx, done_cb)
        return self.add_pending(token)

    def get_cal_margin_mode(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_cal_margin_mode(self.ctx, done_cb)
        return self.add_pending(token)


def setup_debug_hub(cs_url: str, hw_url: str, hub_addrs: List[int]) -> Dict:
    server = connect_xicom(cs_url)
    server.connect_remote(hw_url)
    print(f"Connected to cs_server {cs_url} and hw_server {hw_url}")
    cs_service = server.get_sync_service("ChipScope")
    cs_view = server.get_view(chipscope)

    # Setup Debug Hub with addresses
    for node in cs_view.get_children():
        if "DPC" in node.props.get("Name"):
            print("Running Debug Hub setup")
            cs_service.setup_debug_cores(node.ctx, debug_hub_addrs=hub_addrs).get()
            print()

    print("ChipScope Nodes:")
    cs_view.print_tree(True)
    return cs_view


def get_sddr(view: Dict, mc_index=0) -> AxisDDRClient:
    ddrs = []
    # Find debug hub first and then initialize DDRs
    for node in list(view.get_all()):
        if node.type and node.type == "debug_hub":
            print("Debug Hub found.")
            ddrs.extend(view.find_nodes(node, AxisDDRClient))

    if len(ddrs):
        print("Soft DDR Core found and initialized")
        # Point to the target DDR by index
        ddr = ddrs[mc_index]
        return ddr
    else:
        return None
