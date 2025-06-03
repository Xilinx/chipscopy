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

from typing import ByteString, Dict, Any, Tuple, List
from chipscopy.tcf.services import Service, DoneHWCommand, Token

NAME = "Xicom"


class XicomProxy(Service):
    """TCF Xicom service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def __init__(self, channel):
        super(XicomProxy, self).__init__(channel)
        self.listeners = {}

    def get_hw_server_version_info(self, done: DoneHWCommand, **props) -> Token:
        """
        Get's the hw_server version information.

        :param done: Callback when command is complete
        :param props: Property arguments
        :return: Token of request
        """
        return self.send_xicom_command("getHwServerVersionInfo", props, done)

    def config_begin(
        self, ctx: str, props: Dict[str, Any] = None, done: DoneHWCommand = None
    ) -> Token:
        """
        Initiates the configuration process.

        :param ctx: Context ID of the device to configure
        :param props: Configuration properties
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        if not props:
            props = {}
        return self.send_xicom_command("configBegin", (ctx, props), done)

    def config_data(self, ctx: str, data: ByteString, done: DoneHWCommand = None) -> Token:
        """
        Sends chunk of configuration data

        :param ctx: Context ID of the device to configure
        :param data: Data chunk to configure
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("configData", (ctx, data), done)

    def config_end(
        self, ctx: str, props: Dict[str, Any] = None, done: DoneHWCommand = None
    ) -> Token:
        """
        Ends the configuration process.

        :param ctx: Context ID of the device to configure
        :param props: Configuration properties
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        if not props:
            props = {}
        return self.send_xicom_command("configEnd", (ctx, props), done)

    def config_reset(
        self, ctx: str, props: Dict[str, Any] = None, done: DoneHWCommand = None
    ) -> Token:
        """
        Resets the device configuration.

        :param ctx: Context ID of the device to configure
        :param props: Configuration reset properties
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        if not props:
            props = {}
        return self.send_xicom_command("configReset", (ctx, props), done)

    def secure_debug(self, ctx: str, data: ByteString, done: DoneHWCommand = None) -> Token:
        """
        Enables secure debug using authentication data.

        :param ctx: Context ID of the device
        :param data: Authentication data
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("secureDebug", (ctx, data), done)

    def config_in(self, ctx, start_pos, total_bytes, data, done):
        data_count = len(data)
        return self.send_command("configIn", (ctx, start_pos, total_bytes, data_count, data), done)

    def config_start(self, ctx, done):
        return self.send_command("configStart", (ctx,), done)

    def jtag_reg_list(self, ctx: str or int, done: DoneHWCommand = None) -> Token:
        """
        Retrieves list of available JTAG register context IDs

        :param ctx: Context ID of device or idcode of a jtag device
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("jtagRegList", (ctx,), done)

    def jtag_reg_def(self, reg_ctx: str, done: DoneHWCommand = None) -> Token:
        """
        Retrieves the definition of a given JTAG register context ID

        :param reg_ctx: JTAG register context ID
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("jtagRegDef", (reg_ctx,), done)

    def jtag_reg_get(
        self, ctx: str, reg_ctx: str, slr_index: int, done: DoneHWCommand = None
    ) -> Token:
        """
        Retrieves the current value for a given register

        :param ctx: Context ID of device
        :param reg_ctx: JTAG register context ID
        :param slr_index: Index of SLR
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        return self.send_xicom_command("jtagRegGet", (ctx, reg_ctx, slr_index), done)

    def readback_config(
        self, ctx: str, props: Dict[str, Any] = None, done: DoneHWCommand = None
    ) -> Token:
        """
        Reads back configuration through the SBI that has been previously set up with another PDI.

        :param ctx: Context ID of the device
        :param props: Property arguments
        +-------------------+----------------------+------------------------------------------+
        | Name              | Type                 | Description                              |
        +===================+======================+==========================================+
        | size              | |int|                | Byte size of the readback                |
        +-------------------+----------------------+------------------------------------------+
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        if not props:
            props = {}
        return self.send_xicom_command("readbackConfig", (ctx, props), done)

    def plm_log(self, ctx: str, props: Dict[str, Any] = None, done: DoneHWCommand = None) -> Token:
        """
        Reads plm log of a device.

        :param ctx: Context ID of the device to access
        :param props: Plm log properties
        +-------------------+----------------------+------------------------------------------+
        | Name              | Type                 | Description                              |
        +===================+======================+==========================================+
        | skip-rtca         | |bool|               | avoid reading the RTCA and use defaults  |
        +-------------------+----------------------+------------------------------------------+
        | slr               | |int|                | slr index to read                        |
        +-------------------+----------------------+------------------------------------------+
        | log-addr          | |int|                | address to start reading log (optional)  |
        +-------------------+----------------------+------------------------------------------+
        | log-len           | |int|                | length to read log (optional)            |
        +-------------------+----------------------+------------------------------------------+
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        if not props:
            props = {}
        return self.send_xicom_command("plmLog", (ctx, props), done)

    def efuse_read(self, ctx: str, slr: int = 0, done: DoneHWCommand = None) -> Token:
        """
        Reads back configuration through the SBI that has been previously set up with another PDI.

        :param ctx: Context ID of the device
        :param slr: SLR index
        :param done: Callback with the result and any error
        :return: Token of command sent
        """

        def done_read(token, error, result):
            if not error:
                registers = result[0]
                data = result[1]
                result = dict()
                offset = 0
                for register in registers:
                    name, bit_count = register
                    byte_count = int((bit_count + 7) / 8)
                    value = data[offset : byte_count + offset]
                    offset += byte_count
                    result[name] = value
            if done:
                done(token, error, result)

        return self.send_xicom_command("efuseRead", (ctx, slr), done_read)

    def efuse_program(
        self,
        ctx: str,
        slr: int,
        props: List[Tuple[str, int, ByteString]],
        done: DoneHWCommand = None,
    ) -> Token:
        """
        Programs efuse register

        :param ctx: Context ID of the device
        :param slr: SLR index
        :param props: Property arguments in tuple form (name, bit_count, data_value)
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        arg_props = [(name, bit_count) for name, bit_count, _ in props]
        arg_data = bytearray()
        for p in props:
            arg_data.extend(p[2])
        return self.send_xicom_command("efuseProgram", (ctx, slr, arg_props, arg_data), done)

    def get_crc(self, ctx: str, slr: int, key: ByteString, done: DoneHWCommand = None) -> Token:
        """
        Programs efuse register

        :param ctx: Context ID of the device
        :param slr: SLR index
        :param key: Key value
        :param done: Callback with the result and any error
        :return: Token of command sent
        """
        bit_count = len(key) * 8
        return self.send_xicom_command("getCRC", (ctx, slr, bit_count, key), done)


XicomService = XicomProxy
