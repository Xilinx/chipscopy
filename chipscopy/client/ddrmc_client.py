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
from chipscopy.client.core import get_cs_view, CoreParent
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf import protocol
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.DDRMCProxy import NAME as DDRMC_NAME


class DDRMCClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "ddrmc_main"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(DDRMC_NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize(self.ctx, done_cb))

    def terminate(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        return self.add_pending(service.terminate(self.ctx, done_cb))

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

    def refresh_cal_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_cal_status(self.ctx, done_cb)
        return self.add_pending(token)

    def refresh_cal_margin(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_cal_margin(self.ctx, done_cb)
        return self.add_pending(token)

    def refresh_health_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_health_status(self.ctx, done_cb)
        return self.add_pending(token)

    def refresh_dqs_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_dqs_status(self.ctx, done_cb)
        return self.add_pending(token)

    def disable_tracking(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.disable_tracking(self.ctx, done_cb)
        return self.add_pending(token)

    def enable_tracking(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.enable_tracking(self.ctx, done_cb)
        return self.add_pending(token)

    def get_cal_status(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_cal_status(self.ctx, done_cb)
        return self.add_pending(token)

    def get_cal_margin_mode(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_cal_margin_mode(self.ctx, done_cb)
        return self.add_pending(token)

    def get_margin_ps_factors(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_margin_ps_factors(self.ctx, done_cb)
        return self.add_pending(token)

    def is_clock_gated(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.is_clock_gated(self.ctx, done_cb)
        return self.add_pending(token)

    def __check_scan_settings(self, done: DoneHWCommand = None) -> bool:
        rw_mode = self["mgchk_rw_mode"]
        vref_min = self["es_vref_min"]
        vref_max = self["es_vref_max"]

        print("Min Vref is set at: ", vref_min)
        print("Max Vref is set at: ", vref_max)

        if rw_mode:
            if (vref_min > 50) or (vref_max > 50):
                print("ERROR: Cannot set Vref values larger than 50 under Write margin mode.")
                return False

        if vref_min > vref_max:
            print("ERROR: Cannot set minimum Vref value larger than maximum Vref value.")
            return False

        return True

    def run_eye_scan(self, data_checked=False, done: DoneHWCommand = None) -> bool:
        service, done_cb = self.make_done(done)

        # Perform logical data check if has not been done from earlier calls
        if not data_checked:
            data_pass = self.__check_scan_settings()
            if not data_pass:
                token = object()
                protocol.invokeLater(done, token, None, False)
                return token

        token = service.run_eye_scan(self.ctx, done=done_cb, progress=None)
        return self.add_pending(token)

    def get_eye_scan_data(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.get_eye_scan_data(self.ctx, done_cb)
        return self.add_pending(token)

    def run_eye_scan_async(self, data_checked=False) -> bool:
        assert self.request
        service = self.get_service_proxy()

        # Perform logical data check if has not been done from earlier calls
        if not data_checked:
            data_pass = self.__check_scan_settings()
            if not data_pass:
                result = False
                self.request.set_result(result)

        def update_progress(token, error, results):
            if not error:
                complete_count = results[0]
                total_count = results[1]
                self.request.set_progress(float(complete_count / total_count))

        def check_result(token, error, result):
            # check if canceled
            if not self.request:
                return

            if error:
                self.request.set_exception(error)
            elif result:
                self.request.set_result(result)
            else:
                self.request.set_exception("Internal error occurred while performing 2D eye scan.")

        service.run_eye_scan(self.ctx, done=check_result, progress=update_progress)


def find_ddrmc(cs_url: str, hw_url: str = "", ddrmc_index=0) -> DDRMCClient:

    if hw_url != "":
        server = connect_xicom(cs_url)
        server.connect_remote(hw_url)
        print(f"Connected to cs_server {cs_url} and hw_server {hw_url}")
    else:
        # single argument passed in is intended to be the actual cs_server
        server = cs_url

    print(f"CS Server services: {server.services}")

    # Set up core detection and get list of found cores along with context properties
    cs_view = get_cs_view(server)
    print(f"Searching for DPC in {cs_view}")
    dpc = None
    for node in cs_view.get_children():
        if "DPC" in node.props.get("Name") or "XVC" in node.ctx:
            dpc = cs_view.get_node(node.ctx, CoreParent)
            break

    print()
    print(f"DPC: {dpc}")

    # Set up all available hardened cores
    dpc.setup_cores()

    print()
    print("ChipScope View:")
    cs_view.print_tree(False)

    # Find DDRMC under DPC with a given index
    ddrmc = server.cs_target(parent=dpc, type="ddrmc_main", index=ddrmc_index, cls=DDRMCClient)

    return ddrmc
