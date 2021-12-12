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

from typing import List, Union, Callable, Any
from chipscopy.tcf.services import DoneHWCommand, Service
from chipscopy.client.core_property_client import PropertyValues
from chipscopy.proxies.CorePropertyProxy import CorePropertyProxy

# Memory Models
MEMORY_MODEL_HBMMC = "memory_model_hbmmc"
HBMMC_DOMAIN_INDEX = 0
NA0_DOMAIN_INDEX = 1
NA1_DOMAIN_INDEX = 2
PHY_DOMAIN_INDEX = 3

# Service name.
SERVICE_NAME = "HBMMC"


class HBMMCService(Service):
    """TCF HBM Service interface."""

    def getName(self) -> str:
        """
        Get service name of this service.

        :returns: Service name :const:`NAME`.
        """
        return SERVICE_NAME


class HBMMCProxy(CorePropertyProxy, HBMMCService):
    def __init__(self, channel):
        super().__init__(channel)
        self._listeners = {}

    #
    #  General methods
    #
    def initialize(self, node_id: str, done: DoneHWCommand) -> None:
        return self.send_command("initialize", (node_id,), done)

    def write32(
        self, node_id: str, write_addr: int, data: int, domain_index: int, done: DoneHWCommand
    ) -> None:
        """
        Write 32 bit register.

        :param node_id: Core context id.
        :param write_addr: Address.
        :param data: 32 bit data
        :param domain_index: HBMMC, NA0, NA1, PHY (0-3)
        """
        return self.send_command("write32", (node_id, write_addr, data, domain_index), done)

    def read32(
        self,
        node_id: str,
        read_addr: int,
        read_word_count: int,
        domain_index: int,
        done: DoneHWCommand,
    ) -> Union[List[int], int]:
        """
        Read 32 bit register

        :param node_id: Core context id.
        :param read_addr: address to read from.
        :param read_word_count: number of 32 bit words.
        :param domain_index: HBMMC, NA0, NA1, PHY (0-3)
        :return int value if read_word_count == 1. Otherwise list of int values.
        """
        return self.send_command(
            "read32", (node_id, read_addr, read_word_count, domain_index), done
        )

    #
    #  Service specific user interfaces
    #
    def refresh_property(
        self, node_id: str, prop_names: List[str], done: DoneHWCommand
    ) -> PropertyValues:
        return self.send_command("refreshProperty", (node_id, prop_names), done)
