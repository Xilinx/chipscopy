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
        done = self._makeCallback(done)
        service = self

        class GetServerDescriptionsCommand(Command):
            def __init__(self):
                super(GetServerDescriptionsCommand, self).__init__(
                    service.channel, service, "getServerDescriptions", None
                )

            def done(self, error, args):
                argResult = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    argResult = args[1]
                done.doneHW(self.token, error, argResult)

        return GetServerDescriptionsCommand().token

    def getOpenServers(self, done):
        done = self._makeCallback(done)
        service = self

        class GetOpenServersCommand(Command):
            def __init__(self):
                super(GetOpenServersCommand, self).__init__(
                    service.channel, service, "getOpenServers", None
                )

            def done(self, error, args):
                argResult = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    argResult = args[1]
                done.doneHW(self.token, error, argResult)

        return GetOpenServersCommand().token

    def getServerContext(self, server_id, done):
        done = self._makeCallback(done)
        service = self

        class GetServerContextCommand(Command):
            def __init__(self):
                super(GetServerContextCommand, self).__init__(
                    service.channel, service, "getServerContext", (server_id,)
                )

            def done(self, error, args):
                argResult = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    argResult = args[1]
                done.doneHW(self.token, error, argResult)

        return GetServerContextCommand().token

    def getPortDescriptions(self, server_id, done):
        done = self._makeCallback(done)
        service = self

        class GetPortDescriptionsCommand(Command):
            def __init__(self):
                super(GetPortDescriptionsCommand, self).__init__(
                    service.channel, service, "getPortDescriptions", (server_id,)
                )

            def done(self, error, args):
                argResult = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    argResult = args[1]
                done.doneHW(self.token, error, argResult)

        return GetPortDescriptionsCommand().token

    def getContext(self, port_id, done):
        done = self._makeCallback(done)
        service = self

        class GetPortContextCommand(Command):
            def __init__(self):
                super(GetPortContextCommand, self).__init__(
                    service.channel, service, "getContext", (port_id,)
                )

            def done(self, error, args):
                argResult = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    argResult = args[1]
                done.doneHW(self.token, error, argResult)

        return GetPortContextCommand().token

    def openServer(self, server_id, params, done):
        return self.send_xicom_command("openServer", (server_id, params), done)
