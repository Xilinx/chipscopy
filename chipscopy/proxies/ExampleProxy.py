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


from chipscopy.tcf.services import Service

NAME = "Example"
"""Example service name."""


class ExampleProxy(Service):
    """TCF Example service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def __init__(self, channel):
        super(ExampleProxy, self).__init__(channel)
        self.listeners = {}

    def add_numbers(self, a, b, done):
        return self.send_xicom_command("addNumbers", (a, b), done)

    def parse_bin(self, device_type, data, done):
        params = {"device_type": device_type}
        return self.send_xicom_command("parseBin", (params, data), done)

    def mrd(self, node_id, addr, word_count, done):
        return self.send_xicom_command("mrd", (node_id, addr, word_count), done)

    def mwr(self, node_id, addr, words, word_count, done):
        return self.send_xicom_command("mwr", (node_id, addr, words, word_count), done)

    def run_vio_test(self, node_id, done):
        args = {"node_id": node_id}
        return self.send_xicom_command("runVIOTest", args, done)

    def run_mila_test(self, node_id, done):
        return self.send_xicom_command("runMILATest", (node_id,), done)
