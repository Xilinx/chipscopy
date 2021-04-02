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


from typing import ByteString, Dict, Any
from chipscopy.tcf.services import Service, DoneHWCommand, Token

NAME = "ContextXvc"
"""XVC Context service name."""


class ContextXvcProxy(Service):
    """TCF XVC Context service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def open(self, host: str, port: str, idcode: int = 0, done: DoneHWCommand = None) -> Token:
        """
        Create an SVF target.

        :param host: Host name or IP of XVC server
        :param port: Port of XVC server
        :param idcode: Optional parameter to force the XVC server to show a specific idcode
        :param done: Callback with result and any error.
        """
        args = {"host": host, "port": port}
        if idcode:
            args["idcode"] = idcode
        return self.send_xicom_command("open", args, done)

    def close(self, ctx_id: str, stop: bool = False, done: DoneHWCommand = None) -> Token:
        """
        Create an SVF target.

        :param ctx_id: CTX id of XVC Context
        :param stop: Stop the XVC server prior to disconnect
        :param done: Callback with result and any error.
        """
        args = {"id": ctx_id}
        if stop:
            args["stop"] = 1
        return self.send_xicom_command("close", args, done)
