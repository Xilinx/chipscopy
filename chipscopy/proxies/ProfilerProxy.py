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

"""
"""

from typing import Dict, List, Any, NewType
from chipscopy.tcf import channel
from chipscopy.tcf.channel.Command import Command
from chipscopy.tcf.services import Service, DoneHWCommand, Token

SERVICE = "Profiler"


class ProfilerProxy(Service):
    """TCF Profiler service interface."""

    def getName(self):
        """
        Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return SERVICE

    def get_capabilities(self, ctx: str, done: DoneHWCommand) -> Dict[str, Any]:
        """
        Gets the capabilites of a given context.

        :param ctx: Context id of the context
        :param done: Callback with result and any error.
        :return: A dictionary of the capabilities
        """
        return self.send_xicom_command("getCapabilities", (ctx,), done)

    def configure(self, ctx: str, params: Dict[str, Any], done: DoneHWCommand) -> Dict[str, Any]:
        """
        Sets the configuration of a given context.

        :param ctx: Context id of the context
        :param params: Configuration parameters to set
        :param done: Callback with result and any error.
        """
        return self.send_xicom_command("configure", (ctx, params), done)

    def read(self, ctx: str, done: DoneHWCommand) -> Dict[str, Any]:
        """
        Reads data available of a given context.

        :param ctx: Context id of the context
        :param done: Callback with result and any error.
        :return: Data if available
        """
        service = self
        name = "read"
        args = (ctx,)

        class ProfileReadCommand(Command):
            def __init__(self):
                super().__init__(service.channel, service.getName(), name, args)

            def result(self, token, data: bytes):
                result = b""
                error = None
                try:
                    mem = memoryview(data)
                    data_count_start = data.find(b"(")
                    if data_count_start >= 0:
                        data_count_start += 1
                        data_count_end = data.find(b")", data_count_start)
                        if data_count_end >= 0:
                            data_count = int(mem[data_count_start:data_count_end])
                            data_start = data_count_end + 1
                            result = mem[data_start : data_start + data_count]
                except Exception as e:
                    error = e
                self.done(error, result)

            def done(self, error, results):
                if done:
                    done(self.token, error, results)

        return ProfileReadCommand().token
