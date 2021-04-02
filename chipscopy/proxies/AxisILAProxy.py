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

# AxisILAProxy.py
from typing import Any, Dict, List
from chipscopy.tcf.services import DoneHWCommand, Service
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy


# Service name.
NAME = "AxisILA"
"""
ILA service name.
"""


class AxisILAService(Service):
    def getName(self) -> str:
        """
        Get service name of this service.

        :returns: Service name :const:`NAME`.
        """
        return NAME


class AxisILAProxy(CorePropertyProxy, AxisILAService):
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

    #
    # Probe Methods
    #
    def define_probe(
        self, node_id: str, probe_defs: List[Dict[str, Any]], done: DoneHWCommand
    ) -> None:
        return self.send_xicom_command(
            "defineProbe",
            (
                node_id,
                probe_defs,
            ),
            done,
        )

    def define_port_probes(
        self, node_id: str, options: Dict[str, Any], done: DoneHWCommand
    ) -> None:
        return self.send_xicom_command(
            "definePortProbes",
            (
                node_id,
                options,
            ),
            done,
        )

    def undefine_probe(self, node_id: str, probe_names: List[str], done: DoneHWCommand) -> None:
        return self.send_xicom_command(
            "undefineProbe",
            (
                node_id,
                probe_names,
            ),
            done,
        )

    def get_probe(
        self, node_id: str, probe_names: List[str], attrs: List[str], done: DoneHWCommand
    ) -> Dict[str, Dict[str, Any]]:
        return self.send_xicom_command("getProbe", (node_id, probe_names, attrs), done)

    def set_probe(
        self, node_id: str, attrs: Dict[str, Dict[str, Any]], done: DoneHWCommand
    ) -> None:
        return self.send_xicom_command("setProbe", (node_id, attrs), done)

    def reset_probe(
        self,
        node_id: str,
        reset_trigger_values: bool,
        reset_capture_values: bool,
        done: DoneHWCommand,
    ) -> None:
        return self.send_xicom_command(
            "resetProbe", (node_id, reset_trigger_values, reset_capture_values), done
        )

    #
    # Core Communication Methods
    #
    def arm(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("arm", (node_id,), done)

    def get_trigger_registers(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_xicom_command("getTriggerRegisters", (node_id,), done)

    def upload(self, node_id: str, done: DoneHWCommand) -> bool:
        return self.send_xicom_command("upload", (node_id,), done)
