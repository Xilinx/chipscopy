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

from typing import List
import struct
import re

from rich.progress import Progress, TextColumn, BarColumn

from chipscopy.tcf.services import ServiceSync
from chipscopy.client.mem import MemoryNode
from chipscopy import dm
from chipscopy.dm.memory import MemoryManager
from chipscopy.client.view_info import SyncNode, TargetFilter
from chipscopy.utils.printer import PercentProgressBar


class DeviceMemory:
    """Provides memory read and memory write service for the device.

    See also: chipscopy/tcf/services/memory.py
              chipscopy/tcf/services/remote/MemoryProxy.py
    """

    def __init__(self, hw_server, device_identification, target=None):
        """
        Args:
            hw_server: hardware server
            device_identification: DeviceIdentification class for this device
            target: APU, RPU, Versal, DPC, PPU, PSM, Cortex, MicroBlaze, etc
        """
        self.memory_node_for_target = device_identification.find_memory_target(hw_server, target)
        self.hw_server = hw_server
        self.device_identification = device_identification
        self.target = target

    @property
    def target_names(self):
        """
        Returns:
            list of target names like DPC. These target names may be
            used to specify where to read or write memory using the target= argument
        """
        target_names = DeviceMemory.get_versal_memory_target_names(
            self.hw_server, self.device_identification
        )
        return target_names

    # TODO: @chipscopy_deprecated("Consider alternative Device.memory_write().")
    def mwr(self, address: int, values: List[int], *, size="w"):
        """Write list of values to given memory address.

        Args:
            address: starting address to write
            values: [list of values] to write
            size: b=byte, h=half-word, w=word(default), d=double-word
        """
        if not self.memory_node_for_target:
            raise KeyError(f"{self.target} is an invalid target")
        DeviceMemory.memory_write(self.memory_node_for_target, address, values, size=size)

    # TODO: @chipscopy_deprecated("Consider alternative Device.memory_read")
    def mrd(self, address: int, num: int = 1, *, size="w") -> List[int]:
        """Read num values from given memory address.

        Args:
            address: starting address to read
            num: number of words to read
            size: b=byte, h=half-word, w=word(default), d=double-word
        Returns:
            list of values read
        """
        if not self.memory_node_for_target:
            raise KeyError(f"{self.target} is an invalid target")
        return DeviceMemory.memory_read(self.memory_node_for_target, address, num, size=size)

    @staticmethod
    def get_versal_memory_target_names(hw_server, device_identification):
        """
        Returns:
            list of target names like DPC. These target names may be used to specify where to read or
            write memory using the target= argument
        """
        valid_memory_targets = (
            r"(Versal .*)|(DPC)|(APU)|(RPU)|(PPU)|(PSM)|(Cortex.*)|(MicroBlaze.*)"
        )
        memory_target_names = list()
        memory_node_list = device_identification.get_memory_target_nodes(hw_server)
        for memory_node in memory_node_list:
            memory_target_name = memory_node.props.get("Name")
            if len(memory_target_name) > 0 and re.search(valid_memory_targets, memory_target_name):
                memory_target_names.append(memory_target_name)
        return memory_target_names

    @staticmethod
    def memory_read(
        memory_tcf_node: MemoryNode, address: int, num: int = 1, *, size="w"
    ) -> List[int]:
        # memory read using memory service
        bytes_per_word_lookup = {"b": 1, "h": 2, "w": 4, "d": 8}
        bytes_per_word = bytes_per_word_lookup[size]
        bytes_to_read = num * bytes_per_word
        words_to_read = bytes_to_read // 4
        if (bytes_to_read % 4) != 0:
            words_to_read += 1
        words_read = memory_tcf_node.mrd(address, words_to_read)
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

    @staticmethod
    def memory_write(memory_tcf_node: MemoryNode, address: int, values: List[int], *, size="w"):
        # memory write using the memory service
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
        memory_tcf_node.mwr(address=address, words=int_word_list)


##############################################################################

DEFAULT_BASE_ADDRESS = 0xF2010000


class MemoryDevice(SyncNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profilers = {}

    def post_init(self):
        self.manager.get_node(self.ctx, MemoryNode)

    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return isinstance(node.manager.cs_manager, MemoryManager)

    def update_profilers(self):
        self.profilers = self.future().get_profilers()

    def hsdp_trace(self, file_path: str, total_bytes: int, address: int = DEFAULT_BASE_ADDRESS):
        """Download trace data from running AIE instance and write to a file.

        Args:
            file_path: Path of file to write all data to
            total_bytes: Total number of bytes of trace data to download
                (0 = download until no more data available)
            address: The address of the trace FIFO on device
        """
        max_read_size = 1024 * 1024
        hsdp_profiler = "SmartTB"

        if not self.profilers or hsdp_profiler not in self.profilers:
            self.update_profilers()

        progress_bar = PercentProgressBar()
        progress_bar.add_task(
            description="HSDP Trace progress", status=PercentProgressBar.Status.STARTING
        )

        try:
            with open(file_path, "wb") as f:
                profiler_service = ServiceSync(self.manager.channel, "Profiler", True)
                total_read = 0
                smarttb = self.profilers[hsdp_profiler]
                smarttb.configure(
                    {"MaxReadSize": min(max_read_size, total_bytes), "Address": address}
                )

                self.future().run_profilers((smarttb,))
                while total_read < total_bytes:
                    data = profiler_service.read(self.ctx).get()
                    total_read += len(data)
                    f.write(data)
                    progress_bar.update(
                        completed=(total_read // total_bytes) * 100,
                        status=PercentProgressBar.Status.IN_PROGRESS,
                    )
                self.future().stop_profilers(())
                progress_bar.update(completed=100, status=PercentProgressBar.Status.DONE)
        except KeyError:
            raise Exception("HSDP Trace is not available")

    @property
    def mem(self):
        return TargetFilter(self.manager, self.ctx, type(self))

    def filter(self, *args, **params):
        return TargetFilter(self.manager, self.ctx, *args, **params)
