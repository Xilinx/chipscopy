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

import threading
from socket import AF_INET, SOCK_STREAM, socket, SHUT_RD
from typing import ByteString, Iterable

from chipscopy.utils.logger import log
from chipscopy.utils import bytes_from_words


def recv(sock, size=1):
    c = sock.recv(size)
    if len(c) == 0:  # pragma: no cover
        raise Exception("Disconnected")
    return c


def get_uint_le(sock, size):
    buf = recv(sock, size)
    value = 0
    for byte in buf[size - 1 :: -1]:
        value = (value << 8) | byte
    return value


def set_uint_le(value, size):
    buf = bytearray(size)
    for i in range(size):
        buf[i] = value & 0xFF
        value >>= 8
    return buf


def get_uleb128(sock):
    value = 0
    b = 0
    while True:
        n = recv(sock)[0]
        value |= (n & 0x7F) << b
        b += 7
        if (n & 0x80) == 0:
            break
    return value


def write_uleb128(value):
    buf = bytearray()
    if not value:
        buf = b"\x00"
    while value:
        if value >= 0x80:
            p = (value & 0x7F) | 0x80
        else:
            p = value & 0x7F
        value >>= 7
        buf.append(p)
    return buf


def get_cmd(sock):
    cmd_name = bytearray()
    while True:
        c = recv(sock)
        if c == b":":
            break
        cmd_name += c
    return cmd_name


class XVCPendingError(Exception):
    pass


class XVCHandler(object):
    default_capabilities = [b"memory", b"stop", b"idcode=0x4CA8093", b"idcode2=1"]

    def __init__(
        self,
        addr: int = 0,
        length: int = 0,
        sub_handlers: Iterable["XVCHandler"] = (),
        idcode: int = 0,
        idcode2: int = 0,
    ):
        self.config = {}
        self.addr = addr
        self.length = length
        self.sub_handlers = [h for h in sorted(sub_handlers, key=lambda x: x.addr) if h != self]
        self.idcode = idcode
        self.idcode2 = idcode2

    @property
    def capabilities(self):
        cap = list()
        if self.idcode:
            cap.append(str(f"idcode={self.idcode}").encode("utf-8"))
        if self.idcode2:
            cap.append(str(f"idcode2={self.idcode2}").encode("utf-8"))
        return self.default_capabilities + cap

    def add_sub_handler(self, sub_handler: "XVCHandler"):
        if sub_handler == self:
            return
        for i, h in enumerate(self.sub_handlers):
            if sub_handler.addr < h.addr:
                self.sub_handlers.insert(i, sub_handler)
                return

        self.sub_handlers.append(sub_handler)

    def set_config(self, config_str: str):
        configs = config_str.split(",")
        for config in configs:
            if config[-1] == "+":
                self.config[config[:-1]] = True
            elif config[-1] == "-":
                self.config[config[:-1]] = False
            else:
                name, sep, value = config.partition("=")
                if sep:
                    self.config[name] = value

    def is_valid_addr(self, addr: int):
        return self.addr <= addr < self.addr + self.length

    def read_mem(self, flags: int, addr: int, num_bytes: int) -> ByteString:
        data = bytearray()
        i = iter(self.sub_handlers)
        try:
            handler = next(i)

            while len(data) < num_bytes:
                cur_addr = addr + len(data)
                while handler.addr + handler.length <= addr:
                    handler = next(i)
                if handler.is_valid_addr(cur_addr):
                    loc_addr = cur_addr - handler.addr
                    length = min(num_bytes - len(data), handler.length - loc_addr)
                    data += handler.read_mem(flags, loc_addr, length)
                else:
                    length = min(handler.addr - addr, num_bytes - len(data))
                    data += self.get_mem(flags, cur_addr, length)
        except StopIteration:
            pass
        if len(data) < num_bytes:
            data += self.get_mem(flags, addr + len(data), num_bytes - len(data))

        return data

    def write_mem(self, flags: int, addr: int, data: ByteString):
        offset = 0
        num_bytes = len(data)
        i = iter(self.sub_handlers)
        try:
            handler = next(i)

            while offset < num_bytes:
                while handler.addr + handler.length <= addr:
                    handler = next(i)

                if handler.is_valid_addr(addr):
                    length = min(num_bytes - offset, handler.length - (addr - handler.addr))
                    handler.write_mem(flags, addr - handler.addr, data[offset:length])
                else:
                    length = min(handler.addr - addr, num_bytes - offset)
                    self.set_mem(flags, addr + offset, data[offset:length])
                offset += length
        except StopIteration:
            pass

        if offset < num_bytes:
            length = num_bytes - offset
            self.set_mem(flags, addr + offset, data[offset:length])

    def get_mem(self, flags: int, addr: int, num_bytes: int) -> ByteString:
        """
        Accesses memory from a given location.

        :param flags: Flag bits of memory access (currently unused)
        :param addr: Starting address of memory read
        :param num_bytes: Number of bytes to read
        :return: Data from memory access
        """
        return bytes(num_bytes)

    def set_mem(self, flags: int, addr: int, data: ByteString):
        """
        Writes to given memory location
        :param flags: Flag bits of memory access (currently unused)
        :param addr: Starting address of memory write
        :param data: Data to write
        """
        raise NotImplementedError()

    def shift(self, num_bits: int, tms: ByteString, tdi: ByteString) -> ByteString:
        """
        Performs a JTAG shift transaction
        :param num_bits: Number of bits or TCKs of JTAG shift
        :param tms: JTAG TMS signal vector
        :param tdi: JTAG TDI signal vector
        :return: JTAG TDO signal vector
        """
        return tdi

    def set_tck(self, period: int) -> int:
        """
        Sets JTAG TCK period
        :param period: Desired JTAG TCK period in ns
        :return: Result JTAG TCK period in ns
        """
        return period


class XVCServer(object):
    max_packet_len = 4096

    def __init__(self, port: int = 2542, handler: XVCHandler = None):
        if not handler:
            handler = XVCHandler()
        self.handler = handler
        self.port = port
        self.thread = None
        self.sock = None
        self.listen_sock = None
        self.listening = threading.Condition()
        self.running = False
        self.pending_error = ""

    def process_getinfo(self):
        """
        Gets the XVC Service version

        XVC Format:

        Return Format: 'xvcServer_v<xvc_server_ver>:<xvc_vector_len>\n'
        """
        self.sock.send("xvcServer_v1.1:{}\n".format(self.max_packet_len).encode("utf-8"))

    def process_capabilities(self):
        """
        Gets capabilities of XVC Server

        XVC Format:

        Return Format: [length][capability list]
        [length] ULEB128 indicating length of capability list in bytes
        [capability list] comma separated list of strings
        """
        reply = b",".join(self.handler.capabilities)
        log.xvc.debug("\treply [{}]{}".format(len(reply), reply.decode("utf-8")))
        self.sock.send(write_uleb128(len(reply)) + reply)

    def process_configure(self):
        """
        Sets configuration of XVC server

        XVC Format: [length][configuration strings]

        Params:
        [length] ULEB128 indicating length of [configuration strings] in bytes
        [configuration strings] comma separated list of strings

        Configuration string format:
        name[+|-|=value] where indicates enable, - indicates disable, and =value sets configuration to value

        Return Format: [status]
        [status] error code of status (0x00 for success)
        :return:
        """
        length = get_uleb128(self.sock)
        configs = recv(self.sock, length)
        self.handler.set_config(configs.decode("utf-8"))
        self.sock.send(b"\x00")

    def process_error(self):
        """
        Returns pending error and clears error flag

        XVC Format:

        Return Format: [length][message]
        [length] ULEB128 length of [message] in bytes
        [message] UTF-8 encoded error message

        Special machine decodable errors may be returned from commands as single word all uppercase
        """
        log.xvc.debug(f"\tmessage: {self.pending_error}")
        message = self.pending_error.encode("utf-8")
        self.pending_error = ""
        self.sock.send(write_uleb128(len(message)) + message)

    def process_shift(self):
        """
        Shifts in num bits using the byte vectors tms and tdi

        XVC Format: [num bits][tms vector][tdi vector]

        Params:
        [num_bits] little-ending (LE) number of TCK toggles and bit length of vectors
        [tms] byte sized vector with all the TMS shift bits.  Bit 0 in byte 0 is shifted out first.
        [tdi] like tms, represents all the TDI vectors to be shifted in

        Return Format: [tdo vector]
        [tdo] TDO vector bits for every bit shifted in.  Bit 0 in byte 0 is shifted out first.
        """
        num_bits = get_uint_le(self.sock, 4)
        num_bytes = int((num_bits + 7) / 8)
        tms = recv(self.sock, num_bytes)
        tdi = recv(self.sock, num_bytes)
        self.sock.send(self.handler.shift(num_bits, tms, tdi))

    def process_settck(self):
        """
        Attempts to set the JTAG TCK period

        XVC Format: [period]

        Params:
        [period] LE TCK period in ns

        Return Format: [period]
        [period] LE value of resulting TCK period in ns
        """
        period = get_uint_le(self.sock, 4)
        log.xvc.debug(f"\tperiod: {period}")
        self.sock.send(set_uint_le(self.handler.set_tck(period), 4))

    def process_mwr(self):
        """
        XVC Format: [flags][addr][num bytes][buffer]

        Params:
        [flags] ULEB128 indicating flag bits (currently unused)
        [addr] ULEB128 starting address for mem write
        [num bytes] ULEB128 number of bytes in buffer
        [buffer] byte buffer of data to write

        Return Format: [status]
        [status] error code of status (0x00 for success)
        """
        flags = get_uleb128(self.sock)
        addr = get_uleb128(self.sock)
        num_bytes = get_uleb128(self.sock)
        payload = recv(self.sock, num_bytes)

        log.xvc.debug(
            f"\tflags: {flags}, addr: {addr:X}, num_bytes: {num_bytes}, payload: {payload}"
        )

        if not self.pending_error:
            try:
                self.handler.write_mem(flags, addr, payload)
            except Exception as e:
                self.pending_error = str(e)
                log.xvc.error(self.pending_error)

        if not self.pending_error:
            log.xvc.debug("\tstatus: 0")
            self.sock.send(b"\x00")
        else:
            log.xvc.debug("\tstatus: 1")
            self.sock.send(b"\x01")

    def process_mrd(self):
        """
        XVC Format: [flags][addr][num bytes]

        Params:
        [flags] ULEB128 indicating flag bits (currently unused)
        [addr] ULEB128 starting address for mem read
        [num bytes] ULEB128 number of bytes in buffer

        Return Format: [buffer][status]
        [buffer] byte buffer of data read
        [status] error code of status (0x00 for success)
        """
        flags = get_uleb128(self.sock)
        addr = get_uleb128(self.sock)
        num_bytes = get_uleb128(self.sock)
        log.xvc.debug(f"\tflags: {flags}, addr: {addr:X}, num_bytes: {num_bytes}")

        data = b""
        if not self.pending_error:
            try:
                data = self.handler.read_mem(flags, addr, num_bytes)
            except Exception as e:
                self.pending_error = str(e)
                log.xvc.error(self.pending_error)

        if len(data) < num_bytes:
            data = bytes(num_bytes)
        self.sock.send(data)

        if self.pending_error:
            log.xvc.debug("\tstatus: 1")
            self.sock.send(b"\x01")
        else:
            log.xvc.debug("\tstatus: 0")
            self.sock.send(b"\x00")

    def process_stop(self):
        """
        Stops the XVC service on the server (used during testing).
        Only available when the "stop" capability is returned

        XVC Format:

        Return Format: [status]
        [status] error code of status (0x00 for success)
        """
        self.sock.send(b"\x00")
        self.running = False

    def process_default(self):
        self.pending_error = "Unhandled command"
        self.sock.send(b"\x01")

    def process(self, cmd):
        d = {
            "mwr": self.process_mwr,
            "mrd": self.process_mrd,
            "stop": self.process_stop,
            "getinfo": self.process_getinfo,
            "capabilities": self.process_capabilities,
            "settck": self.process_settck,
            "shift": self.process_shift,
            "error": self.process_error,
        }
        cmd = cmd.decode("utf-8")
        log.xvc.debug(f"{cmd}:")
        func = d.get(cmd, self.process_default)
        func()

    def run(self):
        self.running = True
        self.listen_sock = socket(AF_INET, SOCK_STREAM)
        server_address = ("", self.port)
        self.listen_sock.bind(server_address)
        self.listen_sock.listen(5)
        log.xvc.info(f"Starting service {server_address}")
        with self.listening:
            self.listening.notify()
        while self.running:
            try:
                self.sock, address = self.listen_sock.accept()
            except OSError as e:  # pragma: no cover
                if (
                    e.errno == 22 or e.errno == 10038
                ):  # invalid argument from socket already shuttdown
                    break
                else:
                    print(f"Unhandled OSError: {str(e)}, class {e.__class__}, dict {e.__dict__}")
                    raise e
            log.xvc.info("Accepted connection from {}".format(address))
            while self.running:
                try:
                    cmd = get_cmd(self.sock)
                    if cmd:
                        self.process(cmd)
                except Exception as e:  # pragma: no cover
                    log.xvc.error(f"{str(e)}")
                    break
            log.xvc.info("Connection {} disconnected".format(address))
            self.sock.close()
        self.listen_sock.close()
        log.xvc.info(f"Completed service {server_address}")

    def start(self, wait: int = 0):
        """
        Starts XVC server thread
        :param wait: Waits for listen socket to be listening before returning
        """
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        if wait:
            with self.listening:
                self.thread.start()
                self.listening.wait(wait)
        else:
            self.thread.start()

    def stop(self, wait: int = 5):
        """
        Stops XVC server thread and waits for it to close down.

        :param wait: timeout duration
        """
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:  # pragma: no cover
                pass
        if self.listen_sock:
            try:
                self.listen_sock.shutdown(SHUT_RD)
            except OSError:  # pragma: no cover
                pass
            self.listen_sock.close()
        if self.thread:
            self.thread.join(wait)
        self.thread = None


class XVCMemHandler(XVCHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mem = dict()

    def get_mem(self, flags: int, addr: int, num_bytes: int) -> ByteString:
        data = bytearray()
        for n in range(num_bytes):
            data.append(self.mem.get(addr, 0))
            addr += 1
        return data

    def set_mem(self, flags: int, addr: int, data: ByteString):
        for d in data:
            self.mem[addr] = d
            addr += 1


class XVCVersalMemHandler(XVCMemHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_mem(0, 0xF1260114, bytes_from_words((0x02000000,)))  # npi ref clk enabled
        self.set_mem(0, 0xF1110884, bytes_from_words((0x1,)))  # done bit set
