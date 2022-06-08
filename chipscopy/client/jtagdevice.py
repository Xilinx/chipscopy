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

import os
from typing import Iterable, Any, Dict, NewType, Callable, ByteString
from chipscopy import dm
from chipscopy.dm import request
from chipscopy.tcf.services import xicom
from chipscopy.proxies.XicomProxy import XicomProxy as XicomService
from chipscopy.proxies.JtagProxy import JtagProxy as JtagService
from chipscopy.proxies.JtagCableProxy import JtagCableProxy as JtagCableService
from chipscopy.proxies.JtagDeviceProxy import JtagDeviceProxy as JtagDeviceService
from chipscopy.tcf.protocol import invokeLater
from chipscopy.utils.logger import log


class DoneCmd(xicom.DoneXicom):
    def __init__(self, node, done):
        self.node = node
        self.done = done

    def doneHW(self, token, error, props):
        self.node.update(props)
        self.node.remove_pending(token)  # done state change
        self.done.done_request(token, error, props)


class JtagRegister(object):
    def __init__(self, node: "JtagDevice", reg_ctx: str, definition: Dict):
        self.reg_ctx = reg_ctx
        self.definition = definition
        self.data = None
        self.fields = {}
        self.node = node

    def update(self, done: request.DoneCallback = None):
        proc = self.node.manager.channel.getRemoteService(XicomService)
        done = request._make_callback(done)

        def done_update(token, error, results):
            if not error:
                self.data = results
                self.parse_fields()
            if done:
                done.done_request(token, error, results)

        return proc.jtag_reg_get(self.node.ctx, self.reg_ctx, done_update)

    @property
    def is_static(self):
        return self.definition.get("is_static", False)

    def __str__(self):
        return f"{self.reg_ctx}({self.definition['length']} bits)"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.fields[item]["value"]

    def __getattr__(self, item):
        field = self.fields.get(item)
        return field["value"] if field else None

    def parse_fields(self):
        self.fields = {}
        fields = self.definition.get("fields")
        if fields:
            for field in fields:
                bits = field.get("bits")
                if bits:
                    data_field = {"name": field["name"]}
                    if len(bits) > 1:
                        data_field["bit_range"] = f"{bits[0]}:{bits[-1]}"
                    else:
                        data_field["bit_range"] = f"{bits[0]}"
                    if self.data:
                        value = 0
                        for b in bits:
                            bit = (self.data[int(b / 8)] >> (b % 8)) & 1
                            value = (value << 1) | bit
                        data_field["value"] = value
                    enums = field.get("enums")
                    if enums:
                        data_enums = {}
                        for e in enums:
                            data_enums[e["value"]] = e
                        data_field["enums"] = data_enums
                    self.fields[field["name"]] = data_field

    def print_reg(self):
        hex_str = ""
        if self.data:
            hex_str = "0x" + self.data[::-1].hex()
        print(f"{self.definition['name']} = {hex_str}")

    def print_fields(self):
        self.print_reg()
        max_name_len = 0
        for field in self.fields.values():
            max_name_len = max(max_name_len, len(field["name"]) + len(field["bit_range"]) + 12)
        for field in self.fields.values():
            label = f"{field['name']} (Bits [{field['bit_range']}])"
            value = field["value"]
            if "enums" in field and value in field["enums"]:
                print(f"{label.rjust(max_name_len, ' ')}: {field['enums'][value]['name']}")
            else:
                print(f"{label.rjust(max_name_len, ' ')}: {field['value']}")


DoneGetRegister = NewType("DoneGetRegister", Callable[[Any, Exception or None, JtagRegister], None])


class JtagRegDefManager(object):
    def __init__(self):
        self.reg_defs = {}

    def get_registers(self, node: "JtagDevice", done: DoneGetRegister):
        """
        Gets available registers for a given JTAG device.  The definitions are supplied but data is not set.

        :param node:  JTAG device for which to get registers
        :param done: Done callback
        :return: Token of request
        """
        proc = node.manager.channel.getRemoteService(XicomService)
        assert proc
        ret_token = None
        pending = set()
        regs = {}

        def check_done(error):
            nonlocal done
            if (not pending or error) and done:
                done(ret_token, error, regs)
                done = None

        def done_list(token, error, reg_list):
            if not error:
                for reg in reg_list:
                    if reg not in self.reg_defs:
                        pending.add(proc.jtag_reg_def(reg, handle_done_def(reg)))
                    else:
                        regs[self.reg_defs[reg]["name"]] = JtagRegister(
                            node, reg, self.reg_defs[reg]
                        )
            check_done(error)

        def handle_done_def(reg_ctx):
            def done_def(token, error, reg_def):
                pending.remove(token)
                if not error:
                    self.reg_defs[reg_ctx] = reg_def
                    regs[reg_def["name"]] = JtagRegister(node, reg_ctx, reg_def)
                check_done(error)

            return done_def

        # add pending to indicate that this node is being changed
        ret_token = proc.jtag_reg_list(node.ctx, done_list)
        return ret_token


class JtagNode(dm.Node):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return bool(node.isTap)

    def lock(self, done: request.DoneCallback = None):
        """
        Lock JTAG scan chain containing current JTAG node

        :param done: Request callback when complete

        TODO: Add timeout option in lock to limit wait time. Hardware server already supports this.
        """
        proc = self.manager.channel.getRemoteService(JtagService)
        assert proc

        def done_get_option(token, error, results):
            self.remove_pending(token)
            if done:
                done(token, error, results)

        return self.add_pending(proc.lock(self.ctx, done_get_option))

    def unlock(self, done: request.DoneCallback = None):
        """
        Unlock JTAG scan chain containing current JTAG node

        :param done: Request callback when complete
        """
        proc = self.manager.channel.getRemoteService(JtagService)
        assert proc

        def done_get_option(token, error, results):
            self.remove_pending(token)
            if done:
                done(token, error, results)

        return self.add_pending(proc.unlock(self.ctx, done_get_option))

    def sequence(
        self, commands: list, data: ByteString, done: request.DoneCallback = None
    ) -> bytearray:
        """
        Execute list of JTAG sequence commands

        :param commands: List of commands with options
        :param data: Data to shift
        :param done: Request callback when complete
        """
        proc = self.manager.channel.getRemoteService(JtagService)
        assert proc

        def done_sequence(token, error, results):
            self.remove_pending(token)
            if done:
                done(token, error, results)

        return self.add_pending(proc.sequence(self.ctx, commands, data, done_sequence))


class JtagDevice(JtagNode):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return bool(node.isTap) and node.parent_ctx != ""

    def post_init(self):
        self._update_reg_defs()
        self._update_device_properties()

    @staticmethod
    def get_def_name(reg_name: str):
        """
        Get register bit definition key from a register name
        :param reg_name: register name
        :return: register bit defifinition key
        """
        return reg_name + "_definition"

    def update_regs(
        self, reg_names: Iterable[str] = [], force: bool = False, done: request.DoneCallback = None
    ):
        """
        Updates the register values for all registers that need updating.

        :param reg_names: List of reg_names to update. Empty list means update all that need updating.
        :param force: Forces all registers to update
        :param done: Done callback
        :return: Token of request
        """
        done = request._make_callback(done)
        ret_token = None

        def done_update(token, error, results):
            nonlocal done
            self.remove_pending(token)
            if (self.is_ready or error) and done:
                done.done_request(ret_token, error, self["regs"])
                done = None

        # Start updates for all registers that don't have data already or aren't static
        if reg_names:
            for name in reg_names:
                reg = self["regs"].get(name)
                if reg:
                    ret_token = self.add_pending(reg.update(done_update))
        else:
            for reg in self["regs"].values():
                if force or (not reg.data or not reg.is_static):
                    ret_token = self.add_pending(reg.update(done_update))

        if not ret_token:
            invokeLater(done_update, None, Exception("No registers to update"), None)
        return ret_token

    def config(self, filepath: str, props: Dict[str, Any] = None):
        """
        Configures the device with a given PDI file
        :param filepath: File path of the PDI
        :param props: Configuration properties
        :param done: DoneRequest callback
        :param progress: Progress callback
        :return: Token of request
        """
        assert self.request
        proc = self.manager.channel.getRemoteService(XicomService)
        err = None
        f = open(filepath, "rb")
        total_size = os.stat(filepath).st_size
        total_sent = 0
        total_progress = 0
        chunk_size = 0x4000

        def send_data():
            nonlocal total_sent
            if err:
                config_done(None, err, None)
                return
            while len(self.pending) < 8 and total_sent < total_size:
                data = f.read(chunk_size)
                tok = self.add_pending(proc.config_data(self.ctx, data, config_progress))
                tok.data_size = len(data)
                total_sent += len(data)
                if total_sent >= total_size:
                    self.add_pending(proc.config_end(self.ctx, props, config_wait_for_dpc_ready))

        def config_started(token, error, results):
            nonlocal err
            self.remove_pending(token)
            err = error
            send_data()

        def config_progress(token, error, results):
            nonlocal err
            nonlocal total_progress
            self.remove_pending(token)
            if not err:
                err = error
                if err:
                    config_done(None, err, None)
                    return
                if hasattr(token, "data_size"):
                    total_progress += token.data_size
                self.request.set_progress(total_progress / total_size)
                send_data()

        def config_wait_for_dpc_ready(token, error, results):
            nonlocal err
            if token:
                self.remove_pending(token)
            if not err:
                err = error
            # Wait for DPC to come online by forcing get_children
            # Not doing this can result in a timing issue and timeout exception
            # on subsequent dpc memory read.
            dc_proc = self.manager.channel.getRemoteService("DebugCore")
            assert dc_proc
            self.add_pending(dc_proc.get_children("", config_done))

        def config_done(token, error, results):
            nonlocal err
            if token:
                self.remove_pending(token)

            f.close()
            if not err:
                err = error

            if err:
                self.request.set_exception(err)
            else:
                self.request.set_result(None)

        # add pending to indicate that this node is being changed
        self.add_pending(proc.config_begin(self.ctx, {}, config_started))
        send_data()

    def reset(self):
        """
        Performs a soft reset (SYS_RST IR command)
        :param done: DoneRequest callback
        :return: Token of request
        """
        assert self.request
        proc = self.manager.channel.getRemoteService(XicomService)

        def done_reset(token, error, results):
            self.remove_pending(token)
            if error:
                self.set_exception(error)
            else:
                self.request.set_result(results)

        # add pending to indicate that this node is being changed
        self.add_pending(proc.config_reset(self.ctx, {}, done_reset))

    def status(self, reg_name: str = "jtag_status", done: request.DoneCallback = None):
        """
        Updates and prints the given register.

        :param reg_name: Name of the register
        :param done: Done callback
        :return: Token of request
        """
        done = request._make_callback(done)

        def done_update(token, error, result):
            if not error:
                self.regs[reg_name].print_fields()
            if done:
                done.done_request(token, error, self.regs[reg_name])

        self.update_regs((reg_name,), True, done_update)

    def secure_debug(self, filepath: str, done: request.DoneCallback = None):
        """
        Enables secure debug on a locked device.
        :param filepath: Path to authentication file
        :param done: DoneRequest callback
        :return: Token of request
        """
        proc = self.manager.channel.getRemoteService(XicomService)
        done = request._make_callback(done)
        f = open(filepath, "rb")
        data = f.read()

        def done_run(token, error, results):
            print(f"Done secure debug {token.getID()}")
            self.remove_pending(token)
            if done:
                done.done_request(token, error, results)

        # add pending to indicate that this node is being changed
        return self.add_pending(proc.secure_debug(self.ctx, data, done_run))

    def readback(
        self,
        filepath: str = "",
        readback_word_count: int = 0,
        outfilepath: str = "",
        done: request.DoneCallback = None,
    ):
        """
        Reads back config data.  Requires a PDI to set up the readback through SBI.
        :param filepath: Path to CDO readback PDI
        :param readback_word_count: Optional argument to set the number of words to readback.  If not set it will
        attempt to determine readback size during reading.
        :param outfilepath:  Filepath to output file if desired
        :param done: DoneRequest callback
        :return: Token of request
        """
        proc = self.manager.channel.getRemoteService(XicomService)
        ret_token = None

        def done_run(token, error, results):
            self.remove_pending(token)
            if outfilepath and results:
                with open(outfilepath, "wb") as f:
                    f.write(results)
            if done:
                done(ret_token, error, results)

        def done_config(token, error, results):
            self.remove_pending(token)
            props = {}
            if error and "DONE" in str(error):
                error = None
            if not error:
                if readback_word_count:
                    props["size"] = readback_word_count * 4
                from time import sleep

                sleep(0.5)  # delay to give the readback pdi time to load data into SBI
                return self.add_pending(proc.readback_config(self.ctx, props, done_run))
            elif done:
                done(ret_token, error, results)
            return token

        config_props = {"skip_done_check": True}
        # add pending to indicate that this node is being changed
        if filepath:
            ret_token = self.add_pending(self.config(filepath, config_props, done_config))
        else:
            ret_token = done_config(None, None, None)
        return ret_token

    def _update_reg_defs(self):
        def done_update_reg_defs(token, error, regs):
            self.remove_pending(token)
            if not error:
                if regs:
                    self["regs"] = regs

        self.add_pending(jtag_reg_defs.get_registers(self, done_update_reg_defs))

    def _update_device_properties(self):
        jtag_device = self.manager.channel.getRemoteService(JtagDeviceService)

        def done_get_properties(token, error, props):
            if not error:
                if props:
                    self.update(props)
            self.remove_pending(token)

        self.add_pending(jtag_device.get_properties(self.idCode, done_get_properties))


class JtagCable(JtagNode):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.parent_ctx == "" and node.Name == "whole scan chain"

    def post_init(self):
        self._update_static_properties()
        self.get_option("frequency")
        self.get_option("frequency_list")
        self.get_option("skew")
        self.get_option("timing_class")

    def set_freq(self, freq: int, done: request.DoneCallback = None):
        """ Sets the frequency of the cable """
        proc = self.manager.channel.getRemoteService(JtagService)
        assert proc
        ret_token = None

        def done_get_freg(token, error, results):
            if done:
                done(ret_token, error, results)

        def done_set_freq(token, error, results):
            self.remove_pending(token)
            self.get_option("frequency", done_get_freg)

        ret_token = self.add_pending(proc.set_option(self.ctx, "frequency", freq, done_set_freq))
        return ret_token

    def get_option(self, key: str, done: request.DoneCallback = None):
        """
        Retrieves the frequency of the cable from the hw_server

        :param key: Key of the option
        :param done: Request callback when complete
        """
        proc = self.manager.channel.getRemoteService(JtagService)
        assert proc

        def done_get_option(token, error, results):
            self.remove_pending(token)
            self[key] = results
            if done:
                done(token, error, results)

        return self.add_pending(proc.get_option(self.ctx, key, done_get_option))

    def _update_static_properties(self, done: request.DoneCallback = None):
        proc = self.manager.channel.getRemoteService(JtagCableService)
        assert proc

        def done_update_static(token, error, results):
            self.remove_pending(token)
            self.update(results)
            if done:
                done(token, error, results)

        return self.add_pending(proc.getContext(self.ctx, done_update_static))


jtag_reg_defs = JtagRegDefManager()
