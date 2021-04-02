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

from abc import abstractmethod
from collections import namedtuple, defaultdict
from dataclasses import dataclass
from datetime import datetime
from io import TextIOBase
from itertools import islice
from pprint import pformat
from typing import Generator, Dict, List, Union, Optional
from chipscopy.api.ila import ILABitRange, ILAProbeRadix
import chipscopy
from chipscopy.shared.ila_util import bin_reversed_to_hex_values


@dataclass
class ILAWaveformProbe:
    """Probe location in a data sample."""

    name: str
    """Name of probe."""
    map: str
    """Location string"""
    map_range: [ILABitRange]
    """List of bit ranges. See :class:`~chipscopy.api.ila.ILABitRange`"""
    display_radix: ILAProbeRadix = ILAProbeRadix.HEX
    """Display radix, when exporting waveform data. Default is ILAProbeRadix.HEX"""

    def length(self) -> int:
        return sum(mr.length for mr in self.map_range)


@dataclass
class ILAWaveform:
    """Waveform data, with data probe information."""

    # todo: remove 'trace_' from member names.
    trace_width: int
    """Sample bit width."""
    trace_sample_count: int
    """Number of data samples."""
    trace_trigger_position: [int]
    """Trigger position index, for each data window."""
    trace_window_size: int
    """Number of samples in a window."""
    trace_probes: {str, ILAWaveformProbe}
    """Dict of {probe name, waveform probe}   See :class:`ILAWaveformProbe`"""
    trace_data: bytearray
    """
    Waveform data.

    Samples are aligned on byte boundary. 

    This formula can be used to read a bit from the trace_data:
    ::

        bytes_per_sample = len(trace_data) // trace_sample_count

        def get_bit_value(trace_data: bytearray, bytes_per_sample: int,
                          sample_index: int, data_bit_index: int) -> bool:
            byte_value = trace_data[sample_index * bytes_per_sample + data_bit_index // 8]
            mask = 1 << (data_bit_index & 0x7)
            return (byte_value & mask) != 0

    """

    def get_window_count(self) -> int:
        return len(self.trace_trigger_position)

    def get_data_for_probes(self, probe_names: [str]):
        # Deprecated. Used in AIE demo.
        probes = [
            self.trace_probes[p_name] for p_name in probe_names if p_name in self.trace_probes
        ]

        def get_probe_bit_ranges() -> [ILABitRange]:
            ranges = []
            for probe in probes:
                ranges.extend(probe.map_range)
            return ranges

        bit_ranges: [ILABitRange] = get_probe_bit_ranges()
        trace_data = self.trace_data
        window_sample_count = self.trace_window_size
        bytes_per_sample = (self.trace_width + 7) // 8
        data_masks = [(1 << bit_width) - 1 for idx, bit_width in bit_ranges]

        ProbeData = namedtuple("ProbeData", "window_index sample_index sample_value is_trigger")
        probe_data_list = []
        for idx, byte_idx in enumerate(range(0, len(trace_data), bytes_per_sample)):
            sample_value = int.from_bytes(
                trace_data[byte_idx : byte_idx + bytes_per_sample], byteorder="little", signed=False
            )
            # Loop probes
            hex_strs = ""
            probe_value = 0
            for data_probe, data_mask, bit_range in zip(probes, data_masks, bit_ranges):
                probe_value = (sample_value >> bit_range.index) & data_mask
                hex_strs += f" {probe_value:X}".zfill((bit_range.length + 3) // 4)

            window_index, sample_index = divmod(idx, window_sample_count)
            sample_value = probe_value
            is_trigger = (
                True if sample_index == self.trace_trigger_position[window_index] else False
            )
            probe_data = ProbeData(window_index, sample_index, sample_value, is_trigger)
            probe_data_list.append(probe_data)

        return probe_data_list

    def __str__(self) -> str:
        return pformat(self.__dict__, 2)


class WaveformWriter(object):
    def __init__(self, file_handle: Union[TextIOBase, None], probes: [ILAWaveformProbe]):
        self._file_handle = file_handle
        self._probes = probes
        self._probe_count = len(probes)
        self._probe_names = [p.name for p in probes]
        self._probe_widths = [p.length() for p in probes]

    def handle(self) -> TextIOBase:
        return self._file_handle

    def write(self, msg: str):
        self._file_handle.write(msg)

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def write_sample(
        self,
        sample_position: int,
        window_index: int,
        sample_in_window_index: int,
        is_trigger: bool,
        probe_binary_reversed_values: [str],
        is_last_sample: bool,
    ) -> None:
        """

        Args:
            sample_position (int):
            window_index (int):
            sample_in_window_index (int):
            is_trigger (bool):
            probe_binary_reversed_values ([str]): binary string values each start lsb at position zero.
            is_last_sample(bool): Last sample in waveform.

        Returns:

        """
        pass


class WaveformWriterCSV(WaveformWriter):
    def __init__(self, file_handle: TextIOBase, probes: [ILAWaveformProbe]):
        WaveformWriter.__init__(self, file_handle, probes)

    def init(self):
        self.write("Sample in Buffer,Sample in Window,TRIGGER,")
        self.write(",".join(self._probe_names))
        self.write("\nRadix - UNSIGNED,UNSIGNED,UNSIGNED,")
        # currently HEX is the only supported radix
        self.write(",".join(["HEX"] * self._probe_count))
        self.write("\n")

    def write_sample(
        self,
        sample_position: int,
        window_index: int,
        sample_in_window_index: int,
        is_trigger: bool,
        probe_binary_reversed_values: [str],
        is_last_sample: bool,
    ) -> None:
        hex_values = bin_reversed_to_hex_values(probe_binary_reversed_values)
        hex_values_str = ",".join(hex_values)
        trig_mark = "1" if is_trigger else "0"
        self.write(f"{sample_position},{sample_in_window_index},{trig_mark},{hex_values_str}\n")


class WaveformWriterToDict(WaveformWriter):
    def __init__(
        self, probes: [ILAWaveformProbe], include_trigger: bool, include_sample_info: bool
    ):
        WaveformWriter.__init__(self, None, probes)
        self._include_trigger = include_trigger
        self._include_sample_info = include_sample_info
        self._result = defaultdict(list)

    def init(self):
        return

    def get_result(self) -> Dict[str, List[int]]:
        return self._result

    def write_sample(
        self,
        sample_position: int,
        window_index: int,
        sample_in_window_index: int,
        is_trigger: bool,
        probe_binary_reversed_values: [str],
        is_last_sample: bool,
    ) -> None:
        if self._include_trigger:
            self._result["__TRIGGER"].append(1 if is_trigger else 0)
        if self._include_sample_info:
            self._result["__SAMPLE_INDEX"].append(sample_position)
            self._result["__WINDOW_INDEX"].append(window_index)
            self._result["__WINDOW_SAMPLE_INDEX"].append(sample_in_window_index)

        int_values = [int(r_val[::-1], 2) for r_val in probe_binary_reversed_values]
        for probe_name, val in zip(self._probe_names, int_values):
            self._result[probe_name].append(val)


class WaveformWriterVCD(WaveformWriter):
    """Value Change Dump format. See Wikipedia and IEEE Std 1364-2001."""

    def __init__(self, file_handle: TextIOBase, probes: [ILAWaveformProbe]):
        WaveformWriter.__init__(self, file_handle, probes)
        self._values = None
        self._vars = None
        self._trigger_var = None
        self._window_var = None
        self._prev_sample_is_trigger = None
        self._prev_window_index = None

    @staticmethod
    def _generate_vars() -> Generator[str, None, None]:
        """Supports up to 94 + 94*94 + 94*94*94 = 839,514 probes (or variables)."""
        for x in range(ord("!"), ord("~")):
            yield chr(x)
        for xx in range(ord("!"), ord("~")):
            for yy in range(ord("!"), ord("~")):
                yield chr(xx) + chr(yy)
        for xxx in range(ord("!"), ord("~")):
            for yyy in range(ord("!"), ord("~")):
                for zzz in range(ord("!"), ord("~")):
                    yield chr(xxx) + chr(yyy) + chr(zzz)

    def _write_variable_definitions(self):
        self._values = [None] * self._probe_count
        self._trigger_var, self._window_var, *self._vars = islice(
            WaveformWriterVCD._generate_vars(), self._probe_count + 2
        )

        self._trigger_var = self._trigger_var
        for width, var, probe_name in zip(self._probe_widths, self._vars, self._probe_names):
            self.write(f"$var reg {width} {var} {probe_name} $end\n")
        self.write(
            f"$var reg 1 {self._trigger_var} _TRIGGER $end\n"
            f"$var reg 1 {self._window_var} _WINDOW $end\n"
        )

    def init(self):
        now = "{:%Y-%m-%d %H:%M:%S}".format(datetime.now())
        # adjust for trigger position
        hdr_1 = f"$date\n        {now}\n$end\n"

        hdr_2 = (
            "$version\n"
            + f"        ChipScoPy Version {chipscopy.__version__}\n"
            + "$end\n"
            + "$timescale\n        1ps\n$end\n"
            + "$scope module dut $end\n"
        )

        hdr_3 = "$upscope $end\n$enddefinitions $end\n"

        self.write(hdr_1 + hdr_2)
        self._write_variable_definitions()
        self.write(hdr_3)

    def write_sample(
        self,
        sample_position: int,
        window_index,
        sample_in_window_index,
        is_trigger,
        probe_binary_reversed_values: [str],
        is_last_sample,
    ):
        time_written = False

        def write_value(var: str, reversed_value: str) -> None:
            nonlocal time_written
            if not time_written:
                self.write(f"#{sample_position}\n")
                time_written = True

            if len(reversed_value) == 1:
                self.write(f"{reversed_value}{var}\n")
                return

            # Remove leading zeroes
            msb_idx = reversed_value.rfind("1")
            if msb_idx < 0:
                msb_idx = 0
            value = reversed_value[msb_idx::-1]
            self.write(f"b{value} {var}\n")

        # Write time, for last sample, even if no changes.
        if is_last_sample:
            self.write(f"#{sample_position}\n")
            time_written = True

        # Trigger value
        if is_trigger != self._prev_sample_is_trigger:
            write_value(self._trigger_var, "1" if is_trigger else "0")
            self._prev_sample_is_trigger = is_trigger

        # Window marker.
        if window_index != self._prev_window_index:
            write_value(self._window_var, "1" if window_index % 2 else "0")
            self._prev_window_index = window_index

        # Regular values
        for idx, new_val in enumerate(probe_binary_reversed_values):
            if new_val == self._values[idx]:
                continue

            self._values[idx] = new_val
            write_value(self._vars[idx], new_val)


def export_waveform_to_stream(
    waveform: ILAWaveform,
    export_format: str,
    stream_handle: TextIOBase,
    probe_names: [str],
    start_window_idx: int,
    window_count: Optional[int],
    start_sample_idx: int,
    sample_count: Optional[int],
) -> None:
    """Arguments documented in calling API function"""
    if probe_names:
        probes = [waveform.trace_probes.get(p_name, None) for p_name in probe_names]
        if not all(probes):
            bad_names = set(probe_names) - set(waveform.trace_probes.keys())
            raise Exception(
                f"export_waveform() called with non-existent probe_name:\n  {bad_names}"
            )
    else:
        probes = waveform.trace_probes.values()

    if export_format.upper() == "CSV":
        waveform_writer = WaveformWriterCSV(stream_handle, probes)
    elif export_format.upper() == "VCD":
        waveform_writer = WaveformWriterVCD(stream_handle, probes)
    else:
        raise Exception(f'export_waveform() called with non-supported format "{export_format}"')

    _export_waveform(
        waveform,
        waveform_writer,
        probes,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
        "export_waveform()",
    )


def get_waveform_data_values(
    waveform: ILAWaveform,
    probe_names: [str],
    start_window_idx: int,
    window_count: Optional[int],
    start_sample_idx: int,
    sample_count: Optional[int],
    include_trigger: bool,
    include_sample_info: bool,
) -> Dict[str, List[int]]:
    """Arguments documented in calling API function"""
    if probe_names:
        probes = [waveform.trace_probes.get(p_name, None) for p_name in probe_names]
        if not all(probes):
            bad_names = set(probe_names) - set(waveform.trace_probes.keys())
            raise Exception(
                f"get_waveform_probe_data() called with non-existent probe_name:\n  {bad_names}"
            )
    else:
        probes = waveform.trace_probes.values()

    waveform_writer = WaveformWriterToDict(probes, include_trigger, include_sample_info)
    _export_waveform(
        waveform,
        waveform_writer,
        probes,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
        "get_waveform_data()",
    )

    return waveform_writer.get_result()


def _export_waveform(
    waveform: ILAWaveform,
    writer: WaveformWriter,
    probes: [ILAWaveformProbe],
    start_window_idx: int,
    window_count: Optional[int],
    start_sample_idx: int,
    sample_count: Optional[int],
    calling_function: str,
) -> None:
    def get_sample_binary_values(sample_data: memoryview) -> [str]:
        sample_int_value = int.from_bytes(sample_data, byteorder="little", signed=False)
        reversed_bin_value = f"{sample_int_value:0{waveform.trace_width}b}"[::-1]
        values = []
        for probe in probes:
            # Each probe value can be made up of multiple bit range slices.
            slices = [reversed_bin_value[br.index : br.index + br.length] for br in probe.map_range]
            p_val = "".join(slices)
            values.append(p_val)
        return values

    if not window_count:
        window_count = waveform.get_window_count()
    if not sample_count:
        sample_count = waveform.trace_window_size

    w_size = waveform.trace_window_size
    max_window_count = (waveform.trace_sample_count + w_size - 1) // w_size
    if start_window_idx < 0 or start_window_idx >= max_window_count:
        raise Exception(
            f'{calling_function} function argument start_window="{start_window_idx}" '
            f"must be in the range [0-{max_window_count - 1}]"
        )
    if start_sample_idx < 0 or start_sample_idx >= w_size:
        raise Exception(
            f'{calling_function} function argument "start_sample="{start_sample_idx}" '
            f"must be in the range [0-{w_size - 1}]"
        )
    if sample_count < 1 or sample_count > w_size - start_sample_idx:
        raise Exception(
            f'{calling_function} function argument "sample_count="{sample_count}" '
            f"must be in the range [1-{w_size - start_sample_idx}], "
            f'since start_sample_idx="{start_sample_idx}".'
        )
    if window_count < 1 or window_count > max_window_count - start_window_idx:
        raise Exception(
            f'{calling_function} function argument "window_count="{window_count}" '
            f"must be in the range [1-{max_window_count - start_window_idx}], "
            f'since start_window_idx="{start_window_idx}".'
        )

    sample_byte_count = (waveform.trace_width + 7) // 8
    raw_samples = memoryview(waveform.trace_data)

    writer.init()

    for window_idx in range(start_window_idx, start_window_idx + window_count):
        window_start_sample_idx = window_idx * w_size
        trigger_sample_idx = waveform.trace_trigger_position[window_idx]
        for sample_idx in range(
            window_start_sample_idx + start_sample_idx,
            window_start_sample_idx + start_sample_idx + sample_count,
        ):
            if sample_idx >= waveform.trace_sample_count:
                # last window is not full.
                break
            raw_sample_idx = sample_idx * sample_byte_count
            raw_sample_idx_end = raw_sample_idx + sample_byte_count
            sample_idx_in_window = sample_idx - window_start_sample_idx
            bin_values = get_sample_binary_values(raw_samples[raw_sample_idx:raw_sample_idx_end])
            writer.write_sample(
                sample_idx,
                window_idx,
                sample_idx_in_window,
                sample_idx_in_window == trigger_sample_idx,
                bin_values,
                sample_idx + 1 == waveform.trace_sample_count,
            )
