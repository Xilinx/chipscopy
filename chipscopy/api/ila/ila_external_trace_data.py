# Copyright 2022 Xilinx, Inc.
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
from dataclasses import dataclass, field
from typing import Optional, List
from chipscopy.shared.ila_data import TraceInfo


@dataclass
class DataSegment:
    """
    DataSegment refer to data section of raw data consisting of consecutive data records,
    or refers to one gap record in the raw data.
    """

    start: int
    end: int
    sample_count: int
    is_gap: bool


@dataclass
class DataWindow:
    data: memoryview
    last_record_offset: int
    """ Points to next address after record."""
    sample_count: int
    last_gap_count: int
    segments: List[DataSegment] = field(default_factory=lambda: [])


def decode_external_data(
    data: bytearray, trace_info: TraceInfo, beyond_last_record_addrs: [int], last_gap_counts: [int]
) -> (bytearray, bool):
    # Input data records are aligned on 64 byte boundary.
    # MSB, in record, is record type. 1 for gap record. 0 got regular sample record.
    # Returns: (data formatted for ILAWaveform.data, "data has gap flag")

    # todo: if no gaps, skip gap column.
    in_sample_byte_size = ((trace_info.data_width + 1 + 511) // 512) * 64
    out_sample_byte_size = (trace_info.data_width + 1 + 7) // 8
    gap_block_size = 1024 if trace_info.window_size >= 1024 else trace_info.window_size
    gap_sample = None

    def get_gap_sample_count(window_data: memoryview, offset: int) -> int:
        # offset points to the just beyond the record.
        # sample "block" count is in the lower 32-bits
        read_count = int.from_bytes(
            window_data[offset - in_sample_byte_size : offset - in_sample_byte_size + 4],
            byteorder="little",
            signed=False,
        )

        if trace_info.window_size <= 1024:
            # All samples lost
            count = trace_info.window_size
        else:
            # blocks of 1024 lost.
            count = read_count * 1024
        return count

    def unroll_window(dw: DataWindow) -> None:
        # The resulting unroll-ed window has the last record at the end of the window buffer.
        # If any gaps, the beginning of the buffer is garbage, until real records begin.
        if dw.last_record_offset == len(data):
            return
        buf = bytearray(len(dw.data))
        buf[0 : len(dw.data) - dw.last_record_offset] = data[dw.last_record_offset :]
        buf[len(dw.data) - dw.last_record_offset :] = dw.data[: dw.last_record_offset]
        data[:] = buf[:]

    def find_data_segments(dw: DataWindow) -> None:
        samples_to_process = dw.sample_count

        def flush_data_segment(start_offset: int, end_offset: Optional[int]) -> None:
            if start_offset is None or end_offset is None:
                return None
            seg_sample_count = (end_offset - start_offset) // in_sample_byte_size
            seg = DataSegment(start_offset, end_offset, seg_sample_count, is_gap=False)
            dw.segments.append(seg)
            return None

        if dw.last_gap_count:
            # Insert any gaps after last written record to DDR.
            seg = DataSegment(None, None, dw.last_gap_count, is_gap=True)
            dw.segments.append(seg)
            samples_to_process -= dw.last_gap_count

        current_data_end = None
        current_record_start = None
        for offset in range(len(dw.data), 0, -in_sample_byte_size):
            if samples_to_process <= 0:
                break
            current_record_start = offset - in_sample_byte_size
            # Gap records has msb set to '1'.
            is_gap = dw.data[offset - 1] & 0x80 != 0
            if is_gap:
                current_data_end = flush_data_segment(offset, current_data_end)
                gap_sample_count = get_gap_sample_count(dw.data, offset)
                seg = DataSegment(current_record_start, offset, gap_sample_count, is_gap)
                dw.segments.append(seg)
                samples_to_process -= gap_sample_count
            else:
                if current_data_end is None:
                    current_data_end = offset
                samples_to_process -= 1

        flush_data_segment(current_record_start, current_data_end)
        if dw.segments is not None:
            dw.segments.reverse()

        # Handle too many gap samples at in the beginning of the window.
        if samples_to_process < 0 and dw.segments and dw.segments[0].is_gap:
            if dw.segments[0].sample_count + samples_to_process > 0:
                dw.segments[0].sample_count += samples_to_process

        if samples_to_process > 0:
            raise ValueError("Waveform data is corrupted. Did not find all samples in window.")

    def order_samples_expand_gaps(dw: DataWindow) -> None:
        # Put data segments first in the window.
        nonlocal gap_sample
        to_offset = 0
        for seg in dw.segments:
            if seg.is_gap:
                if gap_sample is None:
                    gap_sample = (1 << trace_info.data_width).to_bytes(
                        in_sample_byte_size, byteorder="little", signed=False
                    )
                next_to_offset = to_offset + seg.sample_count * in_sample_byte_size
                dw.data[to_offset:next_to_offset] = gap_sample * seg.sample_count
            else:
                next_to_offset = to_offset + seg.end - seg.start
                dw.data[to_offset:next_to_offset] = dw.data[seg.start : seg.end]
            to_offset = next_to_offset

    def remove_sample_high_bytes(data: bytearray, total_sample_count: int) -> bytearray:
        if out_sample_byte_size == in_sample_byte_size:
            return data

        # Remove most significant bytes, from each sample.
        move_len = out_sample_byte_size
        to_addr = 0
        for sample_index, from_addr in enumerate(range(0, len(data), in_sample_byte_size)):
            if sample_index >= total_sample_count:
                break
            data[to_addr : to_addr + move_len] = data[from_addr : from_addr + move_len]
            to_addr += move_len
        return data[:to_addr]

    #
    data_windows: List[DataWindow] = []
    total_sample_count = 0
    window_byte_count = in_sample_byte_size * trace_info.window_size
    data_mv = memoryview(data)
    for window_index, window_addr in enumerate(range(0, len(data), window_byte_count)):
        if trace_info.partial_window_sample_count and window_index == trace_info.window_count - 1:
            samples_in_window = trace_info.partial_window_sample_count
        else:
            samples_in_window = trace_info.window_size
        total_sample_count += samples_in_window

        window_memory = data_mv[window_addr : window_addr + window_byte_count]
        beyond_last_record_addr = beyond_last_record_addrs[window_index] - window_addr
        last_gap_count = last_gap_counts[window_index]
        if beyond_last_record_addr == 0:
            beyond_last_record_addr = window_byte_count
        data_windows.append(
            DataWindow(window_memory, beyond_last_record_addr, samples_in_window, last_gap_count)
        )

    for data_window in data_windows:
        unroll_window(data_window)
        find_data_segments(data_window)
        order_samples_expand_gaps(data_window)

    res = remove_sample_high_bytes(data, total_sample_count)
    return res, gap_sample is not None
