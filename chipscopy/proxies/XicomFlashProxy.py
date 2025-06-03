# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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

from typing import ByteString, Dict, Any
from chipscopy.tcf.services import Service, DoneHWCommand, Token

NAME = "XicomFlash"


class XicomFlashProxy(Service):
    """TCF Xicom service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def __init__(self, channel):
        super(XicomFlashProxy, self).__init__(channel)
        self.listeners = {}

    def get_properties(self, ctx: str, done: DoneHWCommand) -> Token:
        """
        Get's the flash context properties.

        :param ctx: Context ID of the memory/xsdb slave ctx to query
        :param done: Callback when command is complete
        :return: Token of request
        """
        return self.send_xicom_command("getProperties", (ctx,), done)

    def blank_check(
        self, ctx: str, start_address: int, read_size: int, done: DoneHWCommand = None
    ) -> Token:
        """
        Resets the device configuration.

        :param ctx: Context ID of the memory/xsdb slave ctx to query
        :param start_address: Start address of the area to check
        :param read_size: Read size of the area to check
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("blankCheck", (ctx, start_address, read_size), done)

    def erase(self, ctx: str, start_address: int, size: int, done: DoneHWCommand = None) -> Token:
        """
        Resets the device configuration.

        :param ctx: Context ID of the memory/xsdb slave ctx to query
        :param start_address: Start address of the area to check
        :param size: Read size of the area to check
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("erase", (ctx, start_address, size), done)

    def read(self, ctx: str, start_address: int, size: int, done: DoneHWCommand = None) -> Token:
        """
        Reads the device configuration.

        :param ctx: Context ID of the memory/xsdb slave ctx to query
        :param start_address: Start address of the area to read
        :param size: Read size of the area to read
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("read", (ctx, start_address, size), done)

    def program(
        self, ctx: str, start_address: int, data: ByteString, done: DoneHWCommand = None
    ) -> Token:
        """
        Programs flash device.

        :param ctx: Context ID of the memory/xsdb slave ctx to query
        :param start_address: Start address of the area to read
        :param data: Data chunk to program
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("program", (ctx, start_address, data), done)

    def program_verify(
        self,
        ctx: str,
        start_address: int,
        data: ByteString,
        program: bool = True,
        verify: bool = True,
        done: DoneHWCommand = None,
    ) -> Token:
        """
        Programs and/or verifies programming of flash device.

        :param ctx: Context ID of the memory/xsdb slave ctx to query
        :param start_address: Start address of the area to read
        :param data: Data chunk to program
        :param program: Flag to indicate whether should be programmed
        :param verify: Flag to indicate whether to verify programming
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command(
            "programVerify", (ctx, int(program), int(verify), start_address, len(data), data), done
        )


XicomFlashService = XicomFlashProxy
