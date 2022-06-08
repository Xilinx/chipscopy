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
from dataclasses import dataclass
from pprint import pformat
from types import MethodType

from chipscopy.api import dataclass_fields, filter_props
from chipscopy.api.ila import ILA, ILAWaveform
from chipscopy.api.ila.ila_external_trace_data import decode_external_data
from chipscopy.shared.ila_util import round_up_to_power_of_two, round_down_to_power_of_two
from chipscopy.shared.ila_data import (
    TraceInfo,
    calculate_trace_info_captured,
    calculate_raw_data_upload_byte_count,
    calculate_data_sample_byte_count,
)


@dataclass(frozen=True)
class ILAExternalTrace:
    """
    Trace Block related information, which get updated by calling one of these functions:

    - set_external_trace
    - upload_external_waveform
    - refresh_external_trace_status
    - run_basic_trigger
    - run_trigger_immediately

    """

    enabled: bool
    """
    
    - True - external trace is selected.
    - False - ILA core internal data buffer, is selected. Maximum data depth is 1024 samples.
    """
    address: int
    """Start address for waveform data in External Memory."""
    byte_size: int
    """Reserved waveform data byte size."""
    current_address: int
    """Trace Block current write address."""
    is_armed: bool
    """Trace Block armed status."""
    is_full: bool
    """Trace Block is_full status."""
    status_error_reserved: int
    """Undocumented."""
    current_stream_input_index: int = 0
    """Trace Block selected source index."""
    current_stream_input_name: str = ""
    """Trace Block selected source ILA cell name. Empty string means "Not reserved"."""

    def __str__(self) -> str:
        p_dict = {
            name: value if isinstance(value, (bool, str)) else hex(value)
            for name, value in self.__dict__.items()
        }
        return pformat(p_dict, 2)

    def _arm(self, ila: ILA):
        ila.core_tcf_node.set_property({"deep_storage_enable": self.enabled})
        if not self.enabled:
            return

        if ila.control.window_size < 1024:
            raise ValueError(f'In external trace mode, "window_size" must be 1024 or larger.')

        if ila.control.window_count != 1:
            raise ValueError(
                f'Select "window_count=1. Only one window supported for external trace.'
            )

        needed_byte_count = calculate_external_trace_byte_count(
            ila, ila.control.window_size, ila.control.window_count
        )
        if needed_byte_count > self.byte_size:
            raise ValueError(
                f"Not enough external memory reserved. "
                f"Reduce windows size:{ila.control.window_size} or "
                f"window_count:{ila.control.window_count} or "
                f"increase external memory from 0x{self.byte_size:X} "
                f"to 0x{needed_byte_count:X} bytes."
            )

        one_sample_size = calculate_external_trace_byte_count(ila, 1, 1)
        ila.tcf_trace_block.acquire(
            ila.external_trace_stream_index,
            ila.name,
            self.address,
            needed_byte_count - one_sample_size,
        )
        refresh_external_trace_status(ila)


def _arm2(self):
    # Todo: move functionality to ILA class, when external trace is no longer hidden.
    self.external_trace._arm(self)


def set_external_trace(ila: ILA, enable: bool, start_address: int, byte_count: int) -> None:
    """Trace Block setup. Applied during run trigger command.

    Args:
        ila (ILA): ILA object.
        enable (bool): True for external trace. False for ILA internal storage. ILA internal storage has room for 1024
        samples.
        start_address (int): Starting external memory address. start_address must be on a 0x1000 byte boundary.
        byte_count (int): Reserved trace data memory size.
    """

    def become_external_trace_ila():
        def raise_no_external_trace_ila():
            raise Exception(f'ILA "{ila.name}" does not have an associated Trace Block')

        # Monkey patch
        ila._arm2 = _arm2
        ila._arm2 = MethodType(_arm2, ila)

        if not ila.core_tcf_node["has_deep_storage"] and not ila._downstreams_refs:
            raise_no_external_trace_ila()
        trace_blocks = ila._device.trace_cores.filter_by(uuid=ila._downstreams_refs[0].uuid)
        if len(trace_blocks) == 0:
            raise_no_external_trace_ila()

        ila.tcf_trace_block = trace_blocks[0].core_tcf_node
        # Deduct 1, since downstream refs for Trace block in is in order "debug_hub", first ila, ...
        ila.external_trace_stream_index = ila._downstreams_refs[0].stream_index - 1

    if not hasattr(ila, "tcf_trace_block") or not hasattr(ila, "external_trace"):
        become_external_trace_ila()

    if enable:
        if byte_count <= 0:
            raise ValueError(
                f"External byte count 0x{byte_count:X} is too low to store any samples."
            )
        if start_address < 0:
            raise ValueError(f"Invalid external trace start_address 0x{start_address:X}.")

        if start_address % 0x1000 != 0:
            raise ValueError(
                f"Invalid external trace start_address 0x{start_address:X}. "
                f"Start address must to be on a 0x1000 byte boundary."
            )

    ila.external_trace = ILAExternalTrace(enable, start_address, byte_count, 0, False, False, 0)
    refresh_external_trace_status(ila)


def upload_external_waveform(ila: ILA, show_progress_bar: bool = True) -> bool:
    """
    Upload external waveform from DDR memory.

    Args:
        ila (ILA): ILA object.
        show_progress_bar (bool): Show progress bar while reading external trace memory.

    Returns: True, if waveform is captured and successfully uploaded.
    """

    def read_external_data(addr: int, byte_count: int) -> bytearray:
        buf = bytearray(byte_count)
        ila._device._dpc_read_bytes(addr, buf, show_progress_bar=show_progress_bar)
        return buf

    # Check ila dynamic status.
    if not ila.external_trace and not ila.external_trace.enabled:
        raise ValueError(f'External waveform is not enabled for ILA "{ila.name}."')

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

    # Apparently some designs need to have "last_sample" register read, before "stopping"
    # the trace block (done by "tcf_trace_block.release")
    tb_last_sample = ila.tcf_trace_block.refresh_property_group(["last_sample"])

    # At least one window is available. Halt capture.
    ila.core_tcf_node.set_property({"arm_ila": False, "halt": True, "tas_enable": False})
    ila.core_tcf_node.commit_property_group(["__core_config", "control"])
    ila.tcf_trace_block.release(ila.external_trace_stream_index, ila.name, False)

    # upload and process data
    _, wave_data_byte_count = calculate_raw_data_upload_byte_count(
        trace_info, EXTERNAL_TRACE_DATA_ALIGNMENT_BIT_COUNT
    )
    data = read_external_data(ila.external_trace.address, wave_data_byte_count)

    trigger_info = ila.core_tcf_node.refresh_property_group(["trigger_info"])
    gap_at_end_sample_count = tb_last_sample["last_gap_count"]
    if trigger_info["last_gap_count_valid"]:
        gap_at_end_sample_count += trigger_info["last_gap_count"]
    # Only one window supported for now. todo: Future add support for multiple windows.
    beyond_last_record_adress = tb_last_sample["last_record_address"] - ila.external_trace.address
    trace, has_gaps = decode_external_data(
        data, trace_info, [beyond_last_record_adress], [gap_at_end_sample_count]
    )
    if trace_info.partial_window_sample_count:
        full_window_count = trace_info.window_count - 1
    else:
        full_window_count = trace_info.window_count

    # Update external memory status.
    refresh_external_trace_status(ila)

    # Create waveform instance
    wave_props = {
        "data": trace,
        "width": trace_info.data_width,
        "sample_count": trace_info.window_size * full_window_count
        + trace_info.partial_window_sample_count,
        "trigger_position": [trace_info.trigger_position] * trace_info.window_count,
        "window_size": trace_info.window_size,
        "probes": ila._make_waveform_probes(),
        "gap_index": trace_info.data_width if has_gaps else None,
    }

    ila.waveform = ILAWaveform(**wave_props)
    # In case trigger sample, was in a gap.
    if trigger_info["trigger_valid"]:
        ila.waveform.set_sample(trace_info.trigger_position, trigger_info["trigger_sample"])
    return True


def refresh_external_trace_status(ila: ILA) -> None:
    """Read Trace Block status. Update ILA.external_trace"""
    tb_status = ila.tcf_trace_block.refresh_property_group(["status"])
    et_props = ila.external_trace.__dict__
    et_props.update(tb_status)
    ila.external_trace = ILAExternalTrace(**filter_props(et_props, ILA_EXTERNAL_TRACE_MEMBERS))


def calculate_external_trace_byte_count(ila: ILA, sample_count: int, window_count: int) -> int:
    """
    Calculate byte count needed to store a certain number of samples.
    Argument "sample_count" is rounded up to nearest power-of-two value.

    Args:
        ila (ILA): ILA object.
        sample_count (int): Samples per window. Must be 1024 or larger.
        window_count (int): Number of windows.

    Returns: Number of bytes required to store samples for all windows.
    """
    # Round up sample_count to nearest power-of-two.
    one_window_sample_count = round_up_to_power_of_two(sample_count)
    # One bit for record type. Align sample on raw data words.
    one_sample_byte_count = calculate_data_sample_byte_count(
        EXTERNAL_TRACE_DATA_ALIGNMENT_BIT_COUNT, ila.static_info.data_width + 1
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

    Returns: Max sample count, which fits into one single window. The result will be a power-of-two value.

    """
    # One bit overhead for record type.
    one_sample_byte_count = calculate_data_sample_byte_count(
        EXTERNAL_TRACE_DATA_ALIGNMENT_BIT_COUNT, ila.static_info.data_width + 1
    )
    one_window_byte_count = (byte_count // one_sample_byte_count) // window_count
    one_window_byte_count = round_down_to_power_of_two(one_window_byte_count)
    return one_window_byte_count


ILA_EXTERNAL_TRACE_MEMBERS = dataclass_fields(ILAExternalTrace)

EXTERNAL_TRACE_DATA_ALIGNMENT_BIT_COUNT = 512
