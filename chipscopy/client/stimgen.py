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

from typing import List, Dict
from . import ServerInfo
from chipscopy.dm.request import CsFutureSync


def _stimgen_done(future: CsFutureSync):
    def tcf_done(token, error, result):
        if error:
            future.set_exception(error)
        else:
            future.set_result(result)

    return tcf_done


class StimgenRegister:
    def __init__(self, channel, ctx: str, target: str):
        self.channel = channel
        self.ctx = ctx
        self.target = target

    def async_read(self, address: int, count: int = 1):
        future = CsFutureSync()

        def tcf_read():
            sg = self.channel.getRemoteService("StimGen")
            sg.read_reg(self.ctx, self.target, address, count, _stimgen_done(future))

        return future.run(tcf_read)

    def read(self, address: int, count: int = 1) -> int or List[int]:
        """
        Reads register via StimGen.
        :param address: register address
        :param count: number of registers to read
        :returns: Int value of register or list of values if count > 1
        """
        return self.async_read(address, count).result

    def async_write(self, address: int, value: int):
        future = CsFutureSync()

        def tcf_write():
            sg = self.channel.getRemoteService("StimGen")
            sg.write_reg(self.ctx, self.target, address, value, _stimgen_done(future))

        return future.run(tcf_write)

    def write(self, address: int, value: int or List[int]):
        """
        Writes register via StimGen.
        :param address: register address
        :param value: value(s) to write - either int or list of ints
        """
        return self.async_write(address, value).result

    def __str__(self):
        return f"StimgenRegister('{self.ctx}':'{self.target}')"


class StimgenUpiChannel:
    def __init__(self, client, target: str, channel_index: int):
        self.client = client
        self.target = target
        self.channel_index = channel_index

    def async_send(self, command: str, params):
        future = CsFutureSync()

        def tcf_send():
            sg = self.client.channel.getRemoteService("StimGen")
            sg.send_upi2(
                self.client.ctx,
                self.target,
                self.channel_index,
                command,
                params,
                _stimgen_done(future),
            )

        return future.run(tcf_send)

    def send(self, command: str or int, params: Dict or int):
        """
        Reads register via StimGen.
        :param command: UPI command either string or int
        :param params: params to send
        :returns: Results of transaction
        """
        return self.async_send(command, params).result

    def __str__(self):
        return f"StimgenUpiChannel('{self.target}', Channel Index:'{self.channel_index}')"


class StimgenClient:
    def __init__(self, channel, ctx: str):
        self.channel = channel
        self.ctx = ctx

    def get_register(self, target: str):
        """
        Sets up StimGen register
        :param target: Target register location (e.g. "tap1.gtmp_quad.APB")
        :returns: StimgenRegister instance
        """
        return StimgenRegister(self.channel, self.ctx, target)

    def get_upi2_channel(self, target: str, channel_index: int):
        """
        Sets up StimGen register
        :param target: Target register location (e.g. "tap1.gtmp_quad.APB")
        :returns: StimgenRegister instance
        """
        return StimgenUpiChannel(self, target, channel_index)

    def async_por(self, target: str = ""):
        future = CsFutureSync()

        def tcf_por():
            sg = self.channel.getRemoteService("StimGen")
            sg.por(self.ctx, target, _stimgen_done(future))

        return future.run(tcf_por)

    def por(self, target: str = ""):
        """
        Runs Power on Reset
        """
        return self.async_por(target).result

    def __str__(self):
        return f"StimgenClient('{self.ctx}')"


def async_setup(cs_server: ServerInfo, hw_server: ServerInfo, params: dict):
    def final(future):
        if future._result:
            future._result = StimgenClient(cs_server.channel, future._result)

    future = CsFutureSync(final=final)

    def tcf_setup():
        sg = cs_server.channel.getRemoteService("StimGen")
        if not sg:
            future.set_exception(Exception("StimGen is not connected on server"))
            return
        params["hw_server"] = hw_server.url
        sg.setup_model(params, _stimgen_done(future))

    return future.run(tcf_setup)


def setup(cs_server: ServerInfo, hw_server: ServerInfo, params: dict) -> StimgenClient:
    """
    Sets up StimGen support on the cs_server
    :param cs_server: The cs_server connection
    :param hw_server: The hw_server connection to which connect StimGen
    :param params: Dict of arguments used for setting up StimGen support.
    +-------------------+----------------------+------------------------------------------+
    | Name              | Type                 | Description                              |
    +===================+======================+==========================================+
    | sg4db             | |str|                | Path to .sg4db file to use               |
    +-------------------+----------------------+------------------------------------------+
    :returns: StimgenClient instance
    """
    return async_setup(cs_server, hw_server, params).result
