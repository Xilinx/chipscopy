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

import json
from typing import List
import struct

from chipscopy.client.mem import MemoryNode
from chipscopy import dm
from chipscopy.dm.memory import MemoryManager
from chipscopy.client.view_info import SyncNode, ViewInfo


class Memory(SyncNode):
    """Provides memory read and memory write service for a device.

    Examples: ::

            some_values = device.memory_read(address=0xF2010000, num=2, target="DPC")
            rpu = session.memory.filter_by(name="RPU").at(0)
            some_values = rpu.memory_read(0xF2010000, 2)
            dpc = device.memory.get(name="DPC")
            dpc.memory_write(0xF2010000, [0x12345678, 0xDEADC0FE])
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.props["Name"]

    def __repr__(self):
        return json.dumps(self.props, indent=4, default=lambda o: str(o))

    @property
    def filter_by(self):
        """Specifies the dict used for filtering memory objects in the device and session.
        Filters memory in the QueryList returned by Session.memory and Device.memory.

        Returns:
              dict[str,value]

        """
        # This is used by the filter_by method in QueryList -
        # add a lowercase copy of all keys for filter convenience
        filter_dict_lower = {k.lower(): v for k, v in self.props.items()}
        filter_dict = {**filter_dict_lower, **self.props.copy()}
        return filter_dict

    def post_init(self):
        """Called at the end of node upgrade"""
        self.manager.get_node(self.ctx, MemoryNode)

    @staticmethod
    def check_and_upgrade(memory_view: ViewInfo, node: MemoryNode) -> "Memory":
        """Converts a client MemoryNode to Memory"""
        if isinstance(node, Memory):
            pass
        elif isinstance(node, MemoryNode) or node.props["node_cls"] == MemoryNode:
            node = memory_view.upgrade_node(node, Memory)
        else:
            raise TypeError("Memory:check_and_upgrade - must be type MemoryNode to upgrade")
        return node

    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        """True if Memory is a compatible node type"""
        if node and node.manager and node.manager.cs_manager:
            return isinstance(node.manager.cs_manager, MemoryManager)
        else:
            return False

    def memory_write(self, address: int, values: List[int], size: str = "w"):
        """Write values from list of <values> to memory address specified by
        <address>.

        size defaults to 'w' if not specified.

        size <access-size> can be one of the values below:
          |  b = Bytes accesses
          |  h = Half-word accesses
          |  w = Word accesses (default)
          |  d = Double-word accesses

        Args:
            address: Address for memory write
            values: List of integer values to write
            size: 'b','h','w','d'
        """
        bytes_per_word_lookup = {"b": 1, "h": 2, "w": 4, "d": 8}
        bytes_per_word = bytes_per_word_lookup[size]
        byte_value_list = []
        for val in values:
            for i in range(bytes_per_word):
                byte_value_list.append((val & (0xFF << (i * 8))) >> (i * 8))

        # Leading 0 Pad to 32-bit boundary
        required_padding_bytes = (4 - len(byte_value_list)) % 4
        padding = [0 for i in range(required_padding_bytes)]
        byte_value_list = byte_value_list + padding
        packed_word_list = [
            struct.pack("<BBBB", *byte_value_list[i : i + 4])
            for i in range(0, len(byte_value_list), 4)
        ]
        int_word_list = [struct.unpack("<L", word)[0] for word in packed_word_list]
        self.mwr(address=address, words=int_word_list)

    def memory_read(self, address: int, num: int = 1, size: str = "w") -> List[int]:
        """Read and return <num> data values from the target's memory address
        specified by <address>.

        num defaults to 1 if not specified.
        size defaults to 'w' if not specified.

        size <access-size> can be one of the values below:
          |  b = Bytes accesses
          |  h = Half-word accesses
          |  w = Word accesses (default)
          |  d = Double-word accesses

        Args:
            address: Address for memory write
            num: number of values to read
            size: 'b','h','w','d'
        """
        bytes_per_word_lookup = {"b": 1, "h": 2, "w": 4, "d": 8}
        bytes_per_word = bytes_per_word_lookup[size]
        bytes_to_read = num * bytes_per_word
        words_to_read = bytes_to_read // 4
        if (bytes_to_read % 4) != 0:
            words_to_read += 1
        words_read = self.mrd(address, words_to_read)
        result_byte_array = None
        for word in words_read:
            if result_byte_array is None:
                result_byte_array = bytearray(word.to_bytes(4, byteorder="little", signed=False))
            else:
                result_byte_array += bytearray(word.to_bytes(4, byteorder="little", signed=False))
        result_byte_list = list(result_byte_array)[:bytes_to_read]
        result = [0] * num
        word_index = 0
        for byte_index in range(len(result_byte_list)):
            the_byte = result_byte_list[byte_index]
            shift_left_amount = (byte_index % bytes_per_word) * 8
            result[word_index] |= the_byte << shift_left_amount
            if (byte_index + 1) % bytes_per_word == 0:
                word_index += 1
        return result
