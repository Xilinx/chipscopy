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
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from io import TextIOBase
from itertools import islice
from pprint import pformat
from typing import Generator, Dict, List, Union, Optional
from chipscopy.api.ila import ILABitRange, ILAProbeRadix
import chipscopy
from chipscopy.shared.ila_util import bin_reversed_to_hex_values
from chipscopy.utils import Enum2StrEncoder


@dataclass
class ILAWaveformProbe:
    """Probe location in a data sample."""

    name: str
    """Name of probe."""
    map: str
    """Location string"""
    map_range: [ILABitRange]
    """List of bit ranges. See :class:`~chipscopy.api.ila.ILABitRange`"""
    is_bus: bool
    """True for bus probes"""
    bus_left_index: Optional[int] = None
    """ Bus left index. E.g. 5 in probe ``counter[5:0]``"""
    bus_right_index: Optional[int] = None
    """Bus right index. E.g. 0 in probe ``counter[5:0]``"""
    display_radix: ILAProbeRadix = ILAProbeRadix.HEX
    """Display radix, when exporting waveform data. Default is ILAProbeRadix.HEX"""

    def length(self) -> int:
        return sum(mr.length for mr in self.map_range)

    def bus_range_str(self) -> str:
        if not self.is_bus:
            res = ""
        elif self.bus_left_index == self.bus_right_index:
            res = f"[{self.bus_left_index}]"
        else:
            res = f"[{self.bus_left_index}:{self.bus_right_index}]"
        return res


@dataclass
class ILAWaveform:
    """Waveform data, with data probe information."""

    width: int
    """Sample bit width."""
    sample_count: int
    """Number of data samples."""
    trigger_position: [int]
    """Trigger position index, for each data window."""
    window_size: int
    """Number of samples in a window."""
    probes: {str, ILAWaveformProbe}
    """Dict of {probe name, waveform probe}   See :class:`ILAWaveformProbe`"""
    data: bytearray
    """
    Waveform data.

    Samples are aligned on byte boundary. 

    This formula can be used to read a bit from the data:
    ::

        bytes_per_sample = len(data) // sample_count

        def get_bit_value(data: bytearray, bytes_per_sample: int,
                          sample_index: int, data_bit_index: int) -> bool:
            byte_value = data[sample_index * bytes_per_sample + data_bit_index // 8]
            mask = 1 << (data_bit_index & 0x7)
            return (byte_value & mask) != 0

    """

    def get_window_count(self) -> int:
        return len(self.trigger_position)

    def __str__(self) -> str:
        items = {key: val for key, val in self.__dict__.items() if key != "data"}
        return pformat(items, 2)

    def __repr__(self) -> str:
        data_size = len(self.data) if self.data else 0
        ret_dict = {
            "width": self.width,
            "sample_count": self.sample_count,
            "trigger_position": self.trigger_position,
            "window_size": self.window_size,
            "probes": {key: asdict(val) for key, val in self.probes.items()},
            "data size": hex(data_size),
        }
        json_dict = json.dumps(ret_dict, cls=Enum2StrEncoder, indent=4)
        return json_dict


def tcf_get_waveform_data(tcf_node) -> {}:
    tcf_props = tcf_node.get_property_group(["data"])
    props = {
        "width": tcf_props["trace_width"],
        "sample_count": tcf_props["trace_sample_count"],
        "trigger_position": tcf_props["trace_trigger_position"],
        "window_size": tcf_props["trace_window_size"],
        "data": tcf_props["trace_data"],
    }
    return props


class WaveformWriter(object):
    def __init__(self, file_handle: Union[TextIOBase, None], probes: [ILAWaveformProbe]):
        self._file_handle = file_handle
        self._probes = probes
        self._probe_count = len(probes)
        self._probe_names = self.make_probe_names()
        self._probe_widths = [p.length() for p in probes]

    def handle(self) -> TextIOBase:
        return self._file_handle

    def write(self, msg: str):
        self._file_handle.write(msg)

    @abstractmethod
    def make_probe_names(self) -> [str]:
        return [p.name for p in self._probes]

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

    def make_probe_names(self) -> [str]:
        return [p.name + p.bus_range_str() for p in self._probes]

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

    def make_probe_names(self) -> [str]:
        return [p.name + " " + p.bus_range_str() for p in self._probes]

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
        probes = [waveform.probes.get(p_name, None) for p_name in probe_names]
        if not all(probes):
            bad_names = set(probe_names) - set(waveform.probes.keys())
            raise Exception(
                f"export_waveform() called with non-existent probe_name:\n  {bad_names}"
            )
    else:
        probes = waveform.probes.values()

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
        probes = [waveform.probes.get(p_name, None) for p_name in probe_names]
        if not all(probes):
            bad_names = set(probe_names) - set(waveform.probes.keys())
            raise Exception(
                f"get_waveform_probe_data() called with non-existent probe_name:\n  {bad_names}"
            )
    else:
        probes = waveform.probes.values()

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
        reversed_bin_value = f"{sample_int_value:0{waveform.width}b}"[::-1]
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
        sample_count = waveform.window_size

    w_size = waveform.window_size
    max_window_count = (waveform.sample_count + w_size - 1) // w_size
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

    sample_byte_count = (waveform.width + 7) // 8
    raw_samples = memoryview(waveform.data)

    writer.init()

    for window_idx in range(start_window_idx, start_window_idx + window_count):
        window_start_sample_idx = window_idx * w_size
        trigger_sample_idx = waveform.trigger_position[window_idx]
        for sample_idx in range(
            window_start_sample_idx + start_sample_idx,
            window_start_sample_idx + start_sample_idx + sample_count,
        ):
            if sample_idx >= waveform.sample_count:
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
                sample_idx + 1 == waveform.sample_count,
            )
