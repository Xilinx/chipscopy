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

import typing
from chipscopy.tcf import services
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy
from chipscopy.utils.logger import log

# NOTE: This name MUST match with the services name defined in the server side AXIS VIO code
AXIS_VIO_SERVICE_NAME = "AxisVIO"
AXIS_VIO_NODE_NAME = "vio"

# NOTE: PLEASE USE THIS DOMAIN NAME IN ALL LOG MESSAGES FROM THIS FILE.
DOMAIN_NAME = "proxy_axis_vio"


class AxisVIOService(services.Service):
    def getName(self) -> str:
        return AXIS_VIO_SERVICE_NAME


class AxisVIOProxy(CorePropertyProxy, AxisVIOService):
    def __init__(self, channel):
        super(AxisVIOProxy, self).__init__(channel)
        self.listeners = {}

    def initialize(self, node_id: str, done: services.DoneHWCommand) -> None:
        log[DOMAIN_NAME].debug("Sending initializeCmd")
        return self.send_xicom_command("initialize", (node_id,), done)

    # ===========================================
    # Core control
    # ===========================================

    def reset_core(
        self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand
    ) -> None:
        log[DOMAIN_NAME].debug("Sending resetCoreCmd")
        return self.send_xicom_command("resetCore", (options["node_id"],), done)

    # ===========================================
    # Port related
    # ===========================================
    def commit_port_out_data(
        self, node_id: str, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand
    ) -> None:
        log[DOMAIN_NAME].debug(f"Sending commitPortOutDataCmd with data {options['port_data']}")
        return self.send_xicom_command("commitPortOutData", (node_id, options), done)

    def refresh_port_out_data(
        self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand
    ) -> None:
        log[DOMAIN_NAME].debug(
            f"Sending refreshPortOutDataCmd with data {options['port_out_numbers']}"
        )
        return self.send_xicom_command("refreshPortOutData", (options["node_id"], options), done)

    def refresh_port_in_data(
        self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand
    ) -> None:
        log[DOMAIN_NAME].debug(f"Sending refreshPortInDataCmd")
        return self.send_xicom_command("refreshPortInData", (options["node_id"],), done)

    def get_port_data(
        self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand
    ) -> None:
        log[DOMAIN_NAME].debug(f"Sending getPortDataCmd")
        return self.send_xicom_command("getPortData", (options["node_id"],), done)

    # ===========================================
    # Probe related
    # ===========================================

    def define_probe(self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand):
        log[DOMAIN_NAME].debug(f"Sending defineProbe with data {options['probe_options']}")
        return self.send_xicom_command("defineProbe", (options["node_id"], options), done)

    def report_probe(self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand):
        log[DOMAIN_NAME].debug(f"Sending reportProbeCmd with data {options['probe_name']}")
        return self.send_xicom_command("reportProbe", (options["node_id"], options), done)

    def undefine_probe(self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand):
        log[DOMAIN_NAME].debug(f"Sending undefineProbeCmd with data {options['probe_name']}")
        return self.send_xicom_command("undefineProbe", (options["node_id"], options), done)

    def refresh_probe(self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand):
        log[DOMAIN_NAME].debug(f"Sending refreshProbeCmd with data {options['probe_name']}")
        return self.send_xicom_command("refreshProbe", (options["node_id"], options), done)

    def commit_probe(self, options: typing.Dict[str, typing.Any], done: services.DoneHWCommand):
        log[DOMAIN_NAME].debug(f"Sending commitProbe with data {options['probe_data']}")
        return self.send_xicom_command("commitProbe", (options["node_id"], options), done)
