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
from dataclasses import dataclass
from typing import Tuple


@dataclass
class TraceInfo:
    data_width: int
    trigger_position: int
    # 'window_count' includes also any partial window.
    window_count: int
    window_size: int
    partial_window_sample_count: int = 0


RAW_DATA_SAMPLE_ALIGN_BIT_COUNT_32 = 32


def calculate_trace_info_captured(trace_info: TraceInfo, status_props: {}) -> TraceInfo:
    """
    Returns Trace_info, adjusting window_count and partial_window_sample_count
    window_count includes full and partial windows.
    """
    if status_props["is_full"]:
        return trace_info

    captured_window_count = status_props["windows_captured"]
    last_window_sample_count = status_props["samples_captured"] % trace_info.window_size
    if last_window_sample_count > trace_info.trigger_position:
        # Last window has trigger, keep the window
        captured_window_count += 1
    else:
        # Cannot keep partial window since it has not triggered.
        last_window_sample_count = 0

    return TraceInfo(
        data_width=trace_info.data_width,
        trigger_position=trace_info.trigger_position,
        window_count=captured_window_count,
        window_size=trace_info.window_size,
        partial_window_sample_count=last_window_sample_count,
    )


def calculate_raw_data_upload_byte_count(
    trace_info: TraceInfo, align_bit_count: int = RAW_DATA_SAMPLE_ALIGN_BIT_COUNT_32
) -> Tuple[int, int]:
    """
    Calculate total bytes, for all packets to upload.
    Have to upload full windows, even if a window is just partially filled.
    """
    # 1-bit trigger column, in raw data.
    align_byte_count = align_bit_count // 8
    one_sample_byte_count = align_byte_count * (
        (trace_info.data_width + 1 + align_bit_count - 1) // align_bit_count
    )
    wave_data_byte_count = one_sample_byte_count * trace_info.window_size * trace_info.window_count
    return one_sample_byte_count, wave_data_byte_count


def process_raw_data(
    trace_info: TraceInfo,
    raw_trace: bytearray,
    raw_data_align_bit_count=RAW_DATA_SAMPLE_ALIGN_BIT_COUNT_32,
) -> bytearray:
    """
    Order window samples, within samples.
    Remove trigger bit.
    Align samples on 1-byte boundary. (Raw data is aligned on 4-byte boundary)
    Remove invalid data from partially captured window.
    """
    if not raw_trace:
        raise ValueError("Uploaded waveform data is empty.")

    repacked_trace = align_samples_to_1_byte(
        raw_trace,
        trace_info.data_width + 1,
        trace_info.window_count * trace_info.window_size,
        raw_data_align_bit_count,
    )
    unrolled_wave = unroll_data(repacked_trace, trace_info)
    return unrolled_wave


def align_samples_to_1_byte(
    data: bytearray, sample_bit_count: int, sample_count: int, raw_data_sample_align_bit_count: int
) -> bytearray:
    """ Get rid of extra sample align bytes. Get rid of bytes beyond last sample."""
    in_sample_byte_count = calculate_data_sample_byte_count(
        raw_data_sample_align_bit_count, sample_bit_count
    )
    out_sample_byte_count = (sample_bit_count + 7) // 8
    valid_data_byte_count = min(len(data), in_sample_byte_count * sample_count)
    if in_sample_byte_count == out_sample_byte_count:
        return data[:valid_data_byte_count]

    # Remove most significant bytes, from each sample.
    move_len = out_sample_byte_count
    to_addr = 0

    for from_addr in range(0, valid_data_byte_count, in_sample_byte_count):
        data[to_addr : to_addr + move_len] = data[from_addr : from_addr + move_len]
        to_addr += move_len
    return data[:to_addr]


def calculate_data_sample_byte_count(
    data_sample_align_bit_count: int, valid_bit_count_per_sample: int
) -> int:
    """
    Args:
        data_sample_align_bit_count (int): Alignment bit count. Typically 32 bits (=4 bytes) for ILA.
        valid_bit_count_per_sample (int): Valid bits per sample, including any trigger bit.

    Returns: Number of bytes each sample occupies.
    """
    sample_word_count = (
        valid_bit_count_per_sample + data_sample_align_bit_count - 1
    ) // data_sample_align_bit_count
    sample_byte_count = sample_word_count * (data_sample_align_bit_count // 8)
    return sample_byte_count


def unroll_data(data: bytearray, trace_info: TraceInfo) -> bytearray:
    # Expect trigger column to be sample MSB, in in_data.
    # trace_info.data_width does not include trigger bit.
    # Samples aligned on byte boundary.
    # Returned data has no trigger column, which may make each sample one byte shorter.

    sample_byte_count_with_trigger = (trace_info.data_width + 1 + 7) // 8

    def unroll_one_window(window_data: memoryview) -> None:
        trigger_mark_sample_idx = -1
        first_trig_byte_addr, trig_bit_idx = divmod(trace_info.data_width, 8)
        trig_mask = 1 << trig_bit_idx
        for sample_idx, addr in enumerate(
            range(first_trig_byte_addr, len(window_data), sample_byte_count_with_trigger)
        ):
            if window_data[addr] & trig_mask != 0:
                trigger_mark_sample_idx = sample_idx
                break

        if trigger_mark_sample_idx < 0:
            raise ValueError("Corrupt waveform data. Missing window trigger mark.")

        start_of_window_sample = trigger_mark_sample_idx - trace_info.trigger_position
        if start_of_window_sample == 0:
            # Nothing to unroll.
            return

        first_sample_addr = sample_byte_count_with_trigger * start_of_window_sample
        if first_sample_addr < 0:
            # roll around
            first_sample_addr += len(window_data)

        buf = bytearray(len(window_data))
        buf[0 : len(window_data) - first_sample_addr] = window_data[first_sample_addr:]
        buf[len(window_data) - first_sample_addr :] = window_data[:first_sample_addr]
        window_data[:] = buf[:]

    def remove_trigger_byte(data: bytearray) -> bytearray:
        sample_byte_count_no_trigger = (trace_info.data_width + 7) // 8
        if sample_byte_count_no_trigger == sample_byte_count_with_trigger:
            return data

        # Remove most significant byte, from each sample.
        move_len = sample_byte_count_no_trigger
        to_addr = 0
        for from_addr in range(0, len(data), sample_byte_count_with_trigger):
            data[to_addr : to_addr + move_len] = data[from_addr : from_addr + move_len]
            to_addr += move_len
        return data[:to_addr]

    #
    window_byte_count = sample_byte_count_with_trigger * trace_info.window_size
    data_mv = memoryview(data)
    for window_addr in range(0, len(data), window_byte_count):
        # last window is not always full
        if window_addr + window_byte_count > len(data):
            window_byte_count = len(data) - window_addr
        unroll_one_window(data_mv[window_addr : window_addr + window_byte_count])

    res = remove_trigger_byte(data)
    return res
