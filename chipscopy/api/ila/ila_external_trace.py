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
from pprint import pformat

from chipscopy.api import dataclass_fields, filter_props
from chipscopy.api.ila import ILA, ILAWaveform
from chipscopy.shared.ila_util import round_up_to_power_of_two, round_down_to_power_of_two
from chipscopy.shared.ila_data import (
    TraceInfo,
    calculate_trace_info_captured,
    calculate_raw_data_upload_byte_count,
    process_raw_data,
    RAW_DATA_SAMPLE_ALIGN_BIT_COUNT_32,
    calculate_data_sample_byte_count,
)


@dataclass(frozen=True)
class ILAExternalTrace:
    """External Trace related data"""

    enabled: bool
    """True to select external trace. False to select the 1024 sample deep ILA internal data buffer."""
    address: int
    """External memory start address."""
    byte_size: int
    """External memory data size."""
    current_address: int
    """Status value updated at upload time."""
    is_armed: bool
    """Status value updated at upload time."""
    is_full: bool
    """Status value updated at upload time."""
    status_error_reserved: int
    """Status value updated at upload time."""

    def __str__(self) -> str:
        p_dict = {
            name: value if isinstance(value, bool) else hex(value)
            for name, value in self.__dict__.items()
        }
        return pformat(p_dict, 2)

    def _arm(self, ila: ILA):
        # todo future - Move function to ILA class
        ila.core_tcf_node.set_property({"deep_storage_enable": self.enabled})
        if not self.enabled:
            return

        if ila.control.window_count != 1:
            raise Exception(
                f'Select "window_count=1. Only one window supported for external trace.'
            )

        needed_byte_count = calculate_external_trace_byte_count(
            ila, ila.control.window_size, ila.control.window_count
        )
        if needed_byte_count > self.byte_size:
            raise Exception(
                f"Not enough external memory reserved. "
                f"Reduce windows size:{ila.control.window_size} or "
                f"window_count:{ila.control.window_count} or "
                f"increase external memory from 0x{self.byte_size:X} "
                f"to 0x{needed_byte_count:X} bytes."
            )

        memory_depth = self.byte_size - (ila.raw_sample_align_bit_count // 8)
        ila.tcf_trace_block.set_property(
            {
                "start": True,
                "halt": False,
                "destination_address": self.address,
                "memory_depth": memory_depth,
            }
        )
        ila.tcf_trace_block.commit_property_group(["control"])


def set_external_trace_sample_alignment(
    ila: ILA, raw_sample_align_bit_count: int = RAW_DATA_SAMPLE_ALIGN_BIT_COUNT_32
):
    """Todo: Remove when no longer needed. Cores should tell us.
    Call before any other external_sample functions.
    """
    ila.raw_sample_align_bit_count = raw_sample_align_bit_count


def set_external_trace(ila: ILA, enable: bool, start_address: int, byte_count: int) -> None:
    """Trace data setup. Applied during run trigger command.

    Args:
        ila (ILA): ILA object
        enable (bool): True for external storage. False for ILA internal storage.
            ILA internal storage has room for 1024 samples.
        start_address (int): Memory address to start writing trace data to.
        byte_count (int): Reserved trace data memory size.
    """

    def become_external_trace_ila():
        def raise_no_external_trace_ila():
            raise Exception(f'ILA "{ila.name}" does not have an associated Trace Block')

        if not ila.core_tcf_node["has_deep_storage"] and not ila._downstreams_refs:
            raise_no_external_trace_ila()
        trace_blocks = ila._device.trace_cores.filter_by(uuid=ila._downstreams_refs[0].uuid)
        if len(trace_blocks) == 0:
            raise_no_external_trace_ila()

        ila.tcf_trace_block = trace_blocks[0].core_tcf_node

    if not ila.tcf_trace_block or not ila.external_trace:
        become_external_trace_ila()

    if enable:
        if byte_count <= 0:
            raise Exception(
                f"External byte count 0x{byte_count:X} is too low to store any samples."
            )
        if start_address < 0:
            raise Exception(f"Invalid external trace start_address 0x{start_address:X}.")

    ila.external_trace = ILAExternalTrace(enable, start_address, byte_count, 0, False, False, 0)


def upload_external_waveform(ila: ILA, show_progress_bar: bool = True) -> bool:
    """
    Upload external waveform from DDR memory.

    Args:
        show_progress_bar (bool): Show progress bar while reading external trace memory.
        ila (ILA): ILA object.

    Returns: True, if waveform is captured and successfully uploaded.
    """

    def halt_external_trace():
        ila.tcf_trace_block.set_property(
            {
                "start": False,
                "halt": True,
            }
        )
        ila.tcf_trace_block.commit_property_group(["control"])

    def read_external_data(addr: int, byte_count: int) -> bytearray:
        buf = bytearray(byte_count)
        ila._device._dpc_read_bytes(addr, buf, show_progress_bar=show_progress_bar)
        return buf

    # Check ila dynamic status.
    if not ila.external_trace and not ila.external_trace.enabled:
        raise Exception(f'External waveform is not enabled for ILA "{ila.name}."')

    ila.refresh_status()
    trace_info = TraceInfo(
        data_width=ila.static_info.data_width,
        trigger_position=ila.core_tcf_node["trigger_pos_readback"],
        window_count=ila.core_tcf_node["window_count_readback"],
        window_size=ila.core_tcf_node["window_depth_readback"],
    )
    trace_info = calculate_trace_info_captured(trace_info, ila.status.__dict__)
    if trace_info.window_count == 0:
        return False

    # At least one window is available. Halt capture.
    ila.core_tcf_node.set_property({"arm_ila": False, "halt": True, "tas_enable": False})
    ila.core_tcf_node.commit_property_group(["__core_config", "control"])
    halt_external_trace()

    # upload and process data
    _, wave_data_byte_count = calculate_raw_data_upload_byte_count(
        trace_info, ila.raw_sample_align_bit_count
    )
    data = read_external_data(ila.external_trace.address, wave_data_byte_count)
    trace = process_raw_data(trace_info, data, ila.raw_sample_align_bit_count)
    if trace_info.partial_window_sample_count:
        full_window_count = trace_info.window_count - 1
    else:
        full_window_count = trace_info.window_count

    # Read external memory status.
    tb_status = ila.tcf_trace_block.refresh_property_group(["status"])
    et_props = ila.external_trace.__dict__
    et_props.update(tb_status)
    ila.external_trace = ILAExternalTrace(**filter_props(et_props, ILA_EXTERNAL_TRACE_MEMBERS))

    # Create waveform instance
    wave_props = {
        "trace_data": trace,
        "trace_width": trace_info.data_width,
        "trace_sample_count": trace_info.window_size * full_window_count
        + trace_info.partial_window_sample_count,
        "trace_trigger_position": [trace_info.trigger_position] * trace_info.window_count,
        "trace_window_size": trace_info.window_size,
        "trace_probes": ila._make_waveform_probes(),
    }

    ila.waveform = ILAWaveform(**wave_props)
    return True


def calculate_external_trace_byte_count(ila: ILA, sample_count: int, window_count: int) -> int:
    """
    Calculate how many bytes are needed to store a certain number of samples.
    Argument "sample_count" is rounded up to nearest power-of-two value.

    Args:
        ila (ILA):
        sample_count (int): Samples per window.
        window_count (int): Number of windows.

    Returns: Number of bytes required to store samples for all windows.
    """
    # Round up sample_count to nearest power-of-two.
    one_window_sample_count = round_up_to_power_of_two(sample_count)
    # One trigger bit in each sample. Align sample on raw data words.
    one_sample_byte_count = calculate_data_sample_byte_count(
        ila.raw_sample_align_bit_count, ila.static_info.data_width + 1
    )
    one_window_byte_count = one_window_sample_count * one_sample_byte_count
    return one_window_byte_count * window_count


def calculate_external_trace_one_window_sample_count(
    ila: ILA, byte_count: int, window_count: int
) -> int:
    """
    Calculate how many samples fit into one window.

    Args:
        ila (ILA): Ila object.
        byte_count (int): Total byte count for all windows.
        window_count (int): Number of windows.

    Returns: Number of samples that fit into one window. The result will be a power-of-two value.

    """
    # One trigger bit in each sample. Align sample on 32-bit words.
    one_sample_byte_count = calculate_data_sample_byte_count(
        ila.raw_sample_align_bit_count, ila.static_info.data_width + 1
    )
    one_window_byte_count = (byte_count // one_sample_byte_count) // window_count
    one_window_byte_count = round_down_to_power_of_two(one_window_byte_count)
    return one_window_byte_count


ILA_EXTERNAL_TRACE_MEMBERS = dataclass_fields(ILAExternalTrace)
