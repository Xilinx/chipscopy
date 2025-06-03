# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.
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

from typing import ByteString, Dict, Any, List
from chipscopy.tcf.services import Service, DoneHWCommand, Token

NAME = "StimGen"


class StimGenProxy(Service):
    """TCF Xicom service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def setup_model(self, args: str or dict, done: DoneHWCommand) -> Token:
        """
        Returns the current package version
        :param args: Either explicit arg string to pass to StimGen load command or
        dict of arguments used for setting up StimGen support.
        +-------------------+----------------------+------------------------------------------+
        | Name              | Type                 | Description                              |
        +===================+======================+==========================================+
        | hw_server         | |str|                | URL of hw_server to connect              |
        +-------------------+----------------------+------------------------------------------+
        | sg4db             | |str|                | Path to .sg4db file to use               |
        +-------------------+----------------------+------------------------------------------+
        :param done: Callback with result and any error
        :returns: Token of command request
        :results: Context handle used for further operations via StimGen
        """
        return self.send_xicom_command("SetupModel", (args,), done)

    def por(self, ctx: str, target: str, done: DoneHWCommand) -> Token:
        """
        Performs Power On Reset
        :param ctx: Context handle passed back during setup
        :returns: Token of command request
        """
        return self.send_xicom_command("Por", (ctx, target), done)

    def read_reg(
        self, ctx: str, reg_loc: str, address: int, count: int = 1, done: DoneHWCommand = None
    ) -> Token:
        """
        Reads register
        :param ctx: Context handle passed back during setup
        :param reg_loc: Location of register interface
        :param address: Address of register
        :returns: Token of command request
        :results: Value read from register
        """
        return self.send_xicom_command("ReadReg", (ctx, reg_loc, address, count), done)

    def write_reg(
        self, ctx: str, reg_loc: str, address: int, value: int or List[int], done: DoneHWCommand
    ) -> Token:
        """
        Writes register
        :param ctx: Context handle passed back during setup
        :param reg_loc: Location of register interface
        :param address: Address of register
        :param value: Value(s) to write to register
        :returns: Token of command request
        """
        return self.send_xicom_command("WriteReg", (ctx, reg_loc, address, value), done)

    def send_upi2(
        self,
        ctx: str,
        target: str,
        channel_index: int,
        cmd: str or int,
        params: int or dict,
        done: DoneHWCommand,
    ) -> Token:
        """
        Sends UPI2 packet
        :param ctx: Context handle passed back during setup
        :param target: Target interface
        :param channel_index: Channel index
        :param cmd: Command to send (device dependent)
        :param params: Parameters to send (device dependent)
        :returns: Token of command request
        :results: Value returned from UPI2 request
        """
        return self.send_xicom_command("SendUpi2", (ctx, target, channel_index, cmd, params), done)


StimGenService = StimGenProxy
