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

from chipscopy.tcf.channel.Command import Command
from chipscopy.tcf.services import Service, DoneHWCommand, Token

JTAG_CABLE_SERVICE = "JtagCable"


class JtagCableProxy(Service):
    def __init__(self, channel):
        self.channel = channel
        self.listeners = {}

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return JTAG_CABLE_SERVICE

    def getServerDescriptions(self, done):
        return self.send_xicom_command("getServerDescriptions", (), done)

    def getOpenServers(self, done):
        return self.send_xicom_command("getOpenServers", (), done)

    def getServerContext(self, server_id, done):
        return self.send_xicom_command("getServerContext", (server_id,), done)

    def getPortDescriptions(self, server_id, done):
        return self.send_xicom_command("getPortDescriptions", (server_id,), done)

    def getContext(self, port_id, done):
        return self.send_xicom_command("getContext", (port_id,), done)

    def openServer(self, server_id, params, done):
        return self.send_xicom_command("openServer", (server_id, params), done)
