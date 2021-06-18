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

from typing import Dict, Any
from chipscopy.tcf.services import Service, DoneHWCommand, Token

JTAG_DEVICE_SERVICE = "JtagDevice"


class JtagDeviceProxy(Service):
    """TCF JtagCable service interface."""

    def __init__(self, channel):
        super(JtagDeviceProxy, self).__init__(channel)
        self.listeners = {}

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return JTAG_DEVICE_SERVICE

    def get_devices(self, done: DoneHWCommand = None) -> Token:
        """
        Get list of known idcodes
        :param done: Done callback
        :return: Token of request
        """
        return self.send_xicom_command("getDevices", (), done)

    def get_properties(self, idcode: int, done: DoneHWCommand = None) -> Token:
        """
        Get properties associated with idcode
        :param idcode: idcode of device
        :param done: Done callback
        :return: Token of request
        """
        return self.send_xicom_command("getProperties", (idcode,), done)

    def set_properties(self, props: Dict[str, Any], done: DoneHWCommand = None) -> Token:
        """
        Set properties associated with idcode
        :param props: Properties to set
        :param done: Done callback
        :return: Token of request
        """
        return self.send_xicom_command("setProperties", (props,), done)
