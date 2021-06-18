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

import struct
from typing import ByteString, List, Iterable, Union, NewType, Callable, Dict
from enum import Flag, auto
from chipscopy import xvc
from chipscopy.utils import bytes_from_words, words_from_bytes, word_align, WORD_SIZE


class RW(Flag):
    READ = auto()
    WRITE = auto()
    RW = READ | WRITE


class UnwritableException(Exception):
    def __init__(self, reg: "XVCRegister"):
        self.reg = reg

    def __str__(self):
        return f"Unable to write register {self.reg}"


class XVCRegister(object):
    def __init__(self, addr: int, length: int = WORD_SIZE, rw: RW = RW.RW, value: ByteString = b""):
        """

        :param addr:
        :param length:
        :param rw:
        :param value:
        """
        self.addr = addr
        self.length = length
        self.rw = rw
        self._value = bytearray(self.length)
        self.set_value(0, value)

    def valid_addr(self, addr: int):
        return self.addr >= addr < self.addr + self.length

    def read_reg(self) -> ByteString:
        """
        Designed for custom reg override
        :return: Data for reg
        """
        return b""

    def write_reg(self):
        """
        Designed for custom reg override
        The byte value is stored in self._value.  Can also use self.get_words and self.get_word
        to simplify reading value
        """
        pass

    def get_reg(self, addr: int, length: int) -> ByteString:
        length = min(length, self.length)
        if not self.valid_addr(addr) or not self.rw & RW.READ:
            return bytes(length)
        offset = addr - self.addr
        data = self.read_reg()
        if data:
            return data[offset : offset + length]
        if not self._value:
            return bytes(length)
        return self._value[offset : offset + length]

    def set_reg(self, addr: int, data: ByteString) -> int:
        if not self.valid_addr(addr) or not self.rw & RW.WRITE:
            raise UnwritableException(self)
        length = self.set_value(addr - self.addr, data)
        self.write_reg()
        return length

    def set_value(self, offset: int, data: ByteString) -> int:
        if not self._value:
            return self.length
        length = min(len(data), self.length - offset)
        for i in range(length):
            self._value[offset + i] = data[i]
        return length

    def get_words(self, index: int = 0, num_words: int = 1) -> List[int]:
        offset = index * WORD_SIZE
        length = num_words * WORD_SIZE
        if not offset < self.length and offset + length > self.length:
            raise IndexError
        words = words_from_bytes(self._value[offset : offset + length])
        return words

    def set_words(self, words: Iterable[int], index: int = 0):
        offset = index * WORD_SIZE
        data = bytes_from_words(words)
        length = len(data)
        if not offset < self.length and offset + length > self.length:
            raise IndexError
        self.set_value(offset, data)

    def get_word(self, index: int = 0):
        return self.get_words(index)[0]

    def set_word(self, word: int, index: int = 0):
        self.set_words((word,), index)


class XVCRegisterHandler(xvc.XVCHandler):
    def __init__(self, regs: Iterable[XVCRegister], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registers = [reg for reg in sorted(regs, key=lambda x: x.addr)]

    def get_mem(self, flags: int, addr: int, num_bytes: int):
        addr = word_align(addr)
        data = bytearray()
        try:
            i = iter(self.registers)
            reg = next(i)
            while num_bytes > 0:
                # get next register
                while reg.addr + reg.length <= addr:
                    reg = next(i)
                if reg.addr <= addr < reg.addr + reg.length:
                    reg_data = reg.get_reg(addr, num_bytes)
                    length = len(reg_data)
                    data += reg_data
                else:
                    # padd up to reg.addr
                    length = min(reg.addr - addr, num_bytes)
                    pad_data = bytes(length)
                    data += pad_data
                addr += length
                num_bytes -= length
        except StopIteration:
            # no more regs, pad remaining data
            data += bytes(num_bytes)

        return data

    def set_mem(self, flags: int, addr: int, data: ByteString):
        addr = word_align(addr)
        offset = 0
        length = len(data)
        i = iter(self.registers)
        try:
            reg = next(i)
            while offset < length:
                # get next register
                while reg.addr + reg.length <= addr:
                    reg = next(i)
                if reg.addr <= addr < reg.addr + reg.length:
                    num_bytes = min(length - offset, reg.length)
                    num_bytes = reg.set_reg(addr, data[offset : offset + num_bytes])
                else:
                    # padd up to reg.addr
                    num_bytes = min(reg.addr - addr, length - offset)
                offset += num_bytes
                addr += num_bytes
        except StopIteration:
            pass

    def add_reg(self, new_registers: Union[XVCRegister, Iterable[XVCRegister]]):
        if not isinstance(new_registers, list):
            new_registers = [new_registers]
        self.registers.extend(new_registers)
        self.registers = [reg for reg in sorted(self.registers, key=lambda x: x.addr)]


class XVCCore(XVCRegister):
    def __init__(self, core_type=0xFF, value_byte_len=0x40, drv_ver=0x1):
        super().__init__(0, value_byte_len)
        self.core_type = core_type
        self.drv_ver = drv_ver
        self.core_minor_ver = 1
        self.core_major_ver = 19
        self.tool_minor_ver = 1
        self.tool_major_ver = 19
        self.uuid = bytearray(range(16))

    def handle_core_info(self):
        self.set_value(
            0,
            struct.pack(
                "<xxxx2H4B16s",
                self.core_type,
                self.drv_ver,
                self.core_minor_ver,
                self.core_major_ver,
                self.tool_minor_ver,
                self.tool_major_ver,
                self.uuid,
            ),
        )

    def write_reg(self):
        # handle packet and write back to value
        words = words_from_bytes(self._value)
        if words[0] == 0xC0000003:
            self.handle_core_info()


class XVCDebugHub(XVCRegisterHandler):
    def __init__(
        self,
        cores: Iterable[XVCCore] = (),
        addr: int = 0,
        length: int = 0x1FFFFF,
        axi_data_width=0x0,
        *args,
        **kwargs,
    ):
        hub = self

        class CoreInfoPacket(XVCRegister):
            """
            Reg[7:0]   - This register contains the number of debug core connected to the debug hub over a pair of
                         AXI4-Stream interfaces.
            Reg[15:8]  - Points to the current debug core being written to.
            Reg[23:16] - Points to the current debug core being read from.
            Reg[31:24] - Points to the data width of the AXI4-MM interface as configured.
                         0x0 - 512bits;
                         0x1 - 256bits;
                         0x2 - 128bits;
                         0x4 - 64bits;
                         0x8 - 32bits
            """

            def read_reg(self):
                num_cores = len(hub.cores)
                cur_write_core = 0
                cur_read_core = 0
                return bytes_from_words(
                    (
                        ((hub.axi_data_width & 0xF) << 24)
                        | ((cur_read_core & 0xF) << 16)
                        | ((cur_write_core & 0xF) << 8)
                        | (num_cores & 0xF),
                    )
                )

        class CoreTypeDrv(XVCRegister):
            def read_reg(self):
                word = (hub.drv_ver & 0xFF) << 16 | (hub.core_type & 0xFF)
                return bytes_from_words((word,))

        class HubVersion(XVCRegister):
            def read_reg(self):
                word = (hub.tool_major_ver & 0xF) << 24
                word |= (hub.tool_minor_ver & 0xF) << 16
                word |= (hub.core_major_ver & 0xF) << 8
                word |= hub.core_minor_ver & 0xF
                return bytes_from_words((word,))

        class UUID(XVCRegister):
            def read_reg(self):
                return hub.uuid

        # set up core addresses
        for i, core in enumerate(cores):
            core.addr = 0x1000 * i

        self.cores = [core for core in cores]

        self.axi_data_width = axi_data_width
        self.core_type = 0x1
        self.drv_ver = 0x1
        self.core_minor_ver = 0
        self.core_major_ver = 1
        self.tool_minor_ver = 0
        self.tool_major_ver = 1
        self.uuid = b"0123456789ABCDEF"

        regs = [core for core in cores]
        regs += [
            CoreInfoPacket(0x100000, rw=RW.READ),
            CoreTypeDrv(0x100004, rw=RW.READ),
            HubVersion(0x100008, rw=RW.READ),
            UUID(0x100040, 16, rw=RW.READ),
            XVCRegister(0x1000C0),  # control_reg
        ]

        super(XVCDebugHub, self).__init__(regs, addr, length, *args, **kwargs)


# A handler handles a particular packet opcode and app. specific index.
PacketHandler = NewType("PacketHandler", Callable[[XVCCore, List[int]], None])


class XVCAxisCore(XVCCore):
    def __init__(self, core_type=0x1, value_byte_len=0x90, drv_ver=0x1):
        XVCCore.__init__(self, core_type, value_byte_len=value_byte_len, drv_ver=drv_ver)
        # key is "write packet header" word, as a number.
        self.packet_handlers: Dict[int, PacketHandler] = {}
        self.set_packet_handler(XVCAxisCore.core_info_handler, op_code=0)

    def core_info_handler(self, _: [int]) -> None:
        self.handle_core_info()

    @staticmethod
    def make_write_header_word(op_code: int, index: int) -> int:
        #
        #  http://confluence.xilinx.com/display/XSW/Debug+IP+proposal+for+transaction+exceeding+burst+length
        #
        #  Bits 31:30 - read/write operation. "Read without any specific start address" binary value "11".
        #                                     "Read with start address" binary value "10"
        #  Bits 29:20 - application specific usage (for ILA/VIO, e.g. MU/TC/PROBE_OUT index)
        #  Bits 19:14 - opcode
        #  Bits 13:0  - (sent_byte_count - 1), byte_length includes header word.
        #
        header_word = 0xC0000003 + (op_code << 14) + (index << 20)
        return header_word

    def set_packet_handler(
        self, packet_handler: PacketHandler, op_code: int, index: int = 0, header_word=None
    ):
        hdr = (
            header_word
            if header_word is not None
            else XVCAxisCore.make_write_header_word(op_code, index)
        )
        self.packet_handlers[hdr] = packet_handler

    def get_packet_handler(self, packet_hdr: int) -> PacketHandler:
        return self.packet_handlers.get(packet_hdr, None)

    def write_reg(self):
        # handle packet and write back to value
        words = words_from_bytes(self._value)
        handler = self.get_packet_handler(words[0])
        if not handler:
            raise Exception(f"XVCAxisCore bad packet header: 0x{words[0]:08X}")
        handler(self, words)

    def set_return_packet(self, packet_words: [int]) -> None:
        self.set_value(0, bytes_from_words(packet_words))


class XVCVersalRegisterHandler(XVCRegisterHandler):
    def __init__(self, regs: Iterable[XVCRegister], *args, **kwargs):
        registers = {x.addr: x for x in regs}
        registers[0xF1260114] = XVCRegister(0xF1260114, value=bytes_from_words((0x02000000,)))
        registers[0xF1110884] = XVCRegister(0xF1110884, value=bytes_from_words((0x1,)))
        super().__init__(registers.values(), *args, **kwargs)
