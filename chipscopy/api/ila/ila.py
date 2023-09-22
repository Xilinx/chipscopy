# Copyright (C) 2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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

import enum
import functools
import json
import sys
from io import TextIOBase
from dataclasses import dataclass, asdict
from pprint import pformat
from typing import Dict, List, Union, Optional, Tuple

from chipscopy.api.ila.tsm.ila_tsm_reader import ILATsmReader
from chipscopy.dm import request
from chipscopy.shared.ila_util import to_bin_str
from chipscopy.api._detail.ltx import Ltx, LtxStreamRef
from chipscopy.client.axis_ila_core_client import AxisIlaCoreClient as TCF_AxisIlaCoreClient
from chipscopy.api.ila import (
    ILACaptureCondition,
    ILATriggerCondition,
    ILATrigInMode,
    ILATrigOutMode,
    ILAControl,
    ILA_TRIGGER_POSITION_HALF,
    ILA_WINDOW_SIZE_MAX,
    ILAStatus,
    ILA_STATUS_MEMBERS,
)
from chipscopy.api import CoreInfo, dataclass_fields, filter_props
from chipscopy.api.ila import ILAPort, ILAProbe, ILAProbeValues, ILABitRange
from chipscopy.api.ila import ILAWaveformProbe, ILAWaveform
from chipscopy.api.ila.ila_capture import (
    tcf_refresh_status,
    post_process_status,
    control_from_tcf,
    control_to_tcf,
    tcf_props_to_status,
)
from chipscopy.api.ila.ila_probe import (
    ports_from_tcf_props,
    verify_ports,
    verify_probe_value,
    create_probes_from_ports_and_ltx,
    ILAProbeRadix,
    verify_probe_enum_def,
)
from chipscopy.api.ila.ila_waveform import (
    tcf_get_waveform_data,
)
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy import CoreType
from chipscopy.utils import Enum2StrEncoder, deprecated_api


def ensure_ila_init(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self._initialize()
        result = method(self, *args, **kwargs)
        return result

    return wrapper


@dataclass(frozen=True)
class ILAStaticInfo:
    """Feature set and dimensions of the ILA core."""

    data_depth: int
    """Data depth in samples."""
    data_width: int
    """Waveform data sample width, in bits."""
    has_advanced_trigger: bool
    """ILA has advanced trigger mode."""
    has_capture_control: bool
    """ILA has basic capture control."""
    has_trig_in: bool
    """ILA has TRIG-IN port."""
    has_trig_out: bool
    """ILA has TRIG-OUT port."""
    match_unit_count: int
    """Total number of probe compare match units."""
    port_count: int
    """Number of probe ports."""
    tsm_counter_widths: List[int]
    """Bit widths of Advanced Trigger Counters."""

    def __str__(self) -> str:
        return pformat(self.__dict__, 2)


ILA_STATIC_INFO_MEMBERS = dataclass_fields(ILAStaticInfo)


class ILA(DebugCore["AxisIlaCoreClient"]):
    """
    Data read-only attributes are accessible by dot-notation', e.g.  *my_ila.static_info.status*

    ============= =========================================== ===========================================
    Attribute     Type                                        Description
    ============= =========================================== ===========================================
    name          str                                         Name of ILA core instance.
    core_info     :class:`~chipscopy.api.CoreInfo`            Debug core version information.
    static_info   :class:`.ILAStaticInfo`                     Feature set and dimensions of the ILA core.
    status        :class:`.ILAStatus`                         Dynamic status of ILA capture controller.
    control       :class:`.ILAControl`                        Trigger setup.
    ports         [:class:`.ILAPort`]                         List of ILA core ports.
    probes        {str, :class:`.ILAProbe`}                   Probes by probe name.
    probe_values  {str, :class:`.ILAProbeValues`}             Probe compare values.
    waveform      :class:`.ILAWaveform`                       Last uploaded waveform data, or None.
    ============= =========================================== ===========================================

    """

    __next_ila_number = 1  # simple incrementing number tracking - hw_ila_1, hw_ila_2, etc

    def __init__(self, tcf_ila: TCF_AxisIlaCoreClient, device, ltx: Ltx):
        DebugCore.__init__(self, core_type=CoreType.AXIS_ILA, core_tcf_node=tcf_ila)
        ltx_core = ltx.get_core(CoreType.AXIS_ILA, self.core_info.uuid) if ltx else None
        if ltx and not ltx_core:
            raise IndexError(
                f"Unable to find ILA core with uuid:{self.core_info.uuid} in LTX file."
            )

        self.name = ltx_core.cell_name if ltx_core else f"hw_ila_{ILA.__next_ila_number}"
        ILA.__next_ila_number += 1
        self._device = device
        self.waveform = None
        # Data members to be initialized later.
        self._static_info: ILAStaticInfo = None
        self._status: ILAStatus = None
        self._control: ILAControl = None
        self._ports: [ILAPort] = None
        self._probes: {str, ILAProbe} = None
        self._probe_values: {str, ILAProbeValues} = None
        self._probe_to_port_seqs: {str, [ILABitRange]} = None
        self._downstreams_refs: [LtxStreamRef] = None
        self._tsm_state_names: Dict[int, str] = {}

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "uuid": self.core_info.uuid}
        self._initialize_complete = False

    def _initialize(self):
        if self._initialize_complete:
            return

        # Initialize ILA service, for this ILA, in the cs_server
        self.core_tcf_node.initialize()
        init_vals = ILA._init(self.core_tcf_node, self.core_info, self._device.ltx)

        self._static_info: ILAStaticInfo = init_vals["static_info"]
        self._status: ILAStatus = init_vals["status"]
        self._control: ILAControl = init_vals["control"]
        self._ports: [ILAPort] = init_vals["ports"]
        self._probes: {str, ILAProbe} = init_vals["probes"]
        self._probe_values: {str, ILAProbeValues} = init_vals["probe_values"]
        self._probe_to_port_seqs: {str, [ILABitRange]} = init_vals["probe_to_port_seqs"]
        self._downstreams_refs: [LtxStreamRef] = (
            self._device.ltx.get_downstream_refs(self.name) if self._device.ltx else []
        )
        self._tsm_state_names: Dict[int, str] = {}
        self._initialize_complete = True

    @property
    def static_info(self) -> ILAStaticInfo:
        self._initialize()
        return self._static_info

    @property
    def status(self) -> ILAStatus:
        self._initialize()
        return self._status

    @property
    def control(self) -> ILAControl:
        self._initialize()
        return self._control

    @property
    def ports(self) -> [ILAPort]:
        self._initialize()
        return self._ports

    @property
    def probes(self) -> {str, ILAProbe}:
        self._initialize()
        return self._probes

    @property
    def probe_values(self) -> {str, ILAProbeValues}:
        self._initialize()
        return self._probe_values

    def __str__(self) -> str:
        """Returns instance name"""
        return self.name

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self) -> Dict:
        d = {}
        # super().to_dict() holds the standard core_info
        d.update(super().to_dict())
        d.update(
            {
                "name": self.name,
                "static_info": asdict(self.static_info),
                "status": asdict(self.status),
                "control": asdict(self.control),
                "ports": [asdict(port) for port in self.ports],
                "probes": {key: asdict(val) for key, val in self.probes.items()},
                "probe_values": {key: asdict(val) for key, val in self.probe_values.items()},
            }
        )
        return dict(sorted(d.items()))

    def to_json(self) -> str:
        json_dict = json.dumps(self.to_dict(), cls=Enum2StrEncoder, indent=4)
        return json_dict

    @ensure_ila_init
    def refresh_status(self) -> None:
        """Read dynamic status and store in attribute 'ila.status'."""
        self._status = tcf_refresh_status(self.core_tcf_node, self._tsm_state_names)

    @ensure_ila_init
    def run_trigger_immediately(
        self,
        trigger_position: int = 0,
        window_count: int = 1,
        window_size: int = ILA_WINDOW_SIZE_MAX,
        trig_out: ILATrigOutMode = ILATrigOutMode.DISABLED,
    ) -> None:
        """Trigger ILA immediately.

        Args:
            trigger_position (int): sample marker inside the window at which the trigger shall appear.
                Range [0..window_size-1], default value: 0.
            window_count (int): Number of windows to capture. Default value: 1.
            window_size (int): Number of samples per window. Must be a power-of-two value.
                Default value: :attr:`.ILA_WINDOW_SIZE_MAX`
            trig_out (ILATrigOutMode): Specify what drives TRIG-OUT port.
                Default value: :attr:`.ILATrigOutMode.DISABLED`

        """
        self._run_trigger(
            trigger_position,
            window_count,
            window_size,
            ILATriggerCondition.IMMEDIATELY,
            ILACaptureCondition.ALWAYS,
            ILATrigInMode.DISABLED,
            trig_out,
        )
        """"""

    @ensure_ila_init
    def run_basic_trigger(
        self,
        trigger_position: int = ILA_TRIGGER_POSITION_HALF,
        window_count: int = 1,
        window_size: int = ILA_WINDOW_SIZE_MAX,
        trigger_condition: ILATriggerCondition = ILATriggerCondition.AND,
        capture_condition: ILACaptureCondition = ILACaptureCondition.ALWAYS,
        trig_in: ILATrigInMode = ILATrigInMode.DISABLED,
        trig_out: ILATrigOutMode = ILATrigOutMode.DISABLED,
    ) -> None:
        """Trigger using probe compare values.

        Args:
            trigger_position (int): denotes the middle of the window. Range [0..window_size-1].
                Default value: :attr:`~.ILA_TRIGGER_POSITION_HALF`
            window_count (int): Number of windows to capture. Default value: 1.
            window_size (int): Number of samples per window. Must be a power-of-two value.
                Default value: :attr:`.ILA_WINDOW_SIZE_MAX`
            trigger_condition (ILATriggerCondition): Trigger condition global boolean operator.
            capture_condition (ILACaptureCondition): Capture condition global boolean operator, to filter samples.
            trig_in (ILATrigInMode): Usage of TRIG-IN Port. Default value: :attr:`.ILATrigInMode.DISABLED`
            trig_out (ILATrigOutMode): Specify what drives TRIG-OUT port. Default value: :attr:`ILATrigOutMode.DISABLED`

        """
        self._run_trigger(
            trigger_position,
            window_count,
            window_size,
            trigger_condition,
            capture_condition,
            trig_in,
            trig_out,
        )

    @ensure_ila_init
    def run_advanced_trigger(
        self,
        trigger_state_machine: Union[TextIOBase, str],
        trigger_position: int = ILA_TRIGGER_POSITION_HALF,
        window_count: int = 1,
        window_size: int = ILA_WINDOW_SIZE_MAX,
        capture_condition: ILACaptureCondition = ILACaptureCondition.ALWAYS,
        trig_in: ILATrigInMode = ILATrigInMode.DISABLED,
        trig_out: ILATrigOutMode = ILATrigOutMode.DISABLED,
        compile_only: bool = False,
    ) -> Tuple[int, str]:
        """Trigger based on Trigger State Machine (TSM) description.

        Args:
            trigger_state_machine (Union[TextIOBase, str]): File object handle or filepath string, for TSM text.
            trigger_position (int): denotes the middle of the window. Range [0..window_size-1].
                Default value: :attr:`~.ILA_TRIGGER_POSITION_HALF`
            window_count (int): Number of windows to capture. Default value: 1.
            window_size (int): Number of samples per window. Must be a power-of-two value.
                Default value: :attr:`.ILA_WINDOW_SIZE_MAX`
            capture_condition (ILACaptureCondition): Capture condition global boolean operator, to filter samples.
            trig_in (ILATrigInMode): Usage of TRIG-IN Port. Default value: :attr:`.ILATrigInMode.DISABLED`
            trig_out (ILATrigOutMode): Specify what drives TRIG-OUT port. Default value: :attr:`ILATrigOutMode.DISABLED`
            compile_only (bool): Default is False. If True, it will only parse the TSM file for correctness.

        Returns (Tuple[int, str):
            If compile_only is True, error-count and an error message string will be returned.
            If compile_only is False, any error in the TSM file will result in an exception with error messages.

        """
        if not self.static_info.has_advanced_trigger:
            raise ValueError(f'ILA {self.name} does not support "Advanced Trigger Mode".')

        self._tsm_state_names = {}
        probe_enums = {
            name: pval.enum_def for name, pval in self.probe_values.items() if pval.enum_def
        }
        reader = ILATsmReader(
            trigger_state_machine,
            self.ports,
            self.probes,
            probe_enums,
            self.static_info.tsm_counter_widths,
            self.static_info.has_capture_control,
        )
        error_count, error_msg, tsm_regs = reader.parse()
        if compile_only:
            return error_count, error_msg

        if error_count:
            error_count_str = "1 error" if error_count == 1 else f"{error_count} errors"
            raise ValueError(
                f"Advanced trigger state machine description has {error_count_str}\n\n" + error_msg
            )

        self._tsm_state_names = reader.get_state_names()

        self._run_trigger(
            trigger_position,
            window_count,
            window_size,
            ILATriggerCondition.TRIGGER_STATE_MACHINE,
            capture_condition,
            trig_in,
            trig_out,
            tsm_registers=tsm_regs,
        )
        return 0, ""

    def _run_trigger(
        self,
        trigger_position: int = ILA_TRIGGER_POSITION_HALF,
        window_count: int = 1,
        window_size: int = ILA_WINDOW_SIZE_MAX,
        trigger_condition: ILATriggerCondition = ILATriggerCondition.AND,
        capture_condition: ILACaptureCondition = ILACaptureCondition.ALWAYS,
        trig_in: ILATrigInMode = ILATrigInMode.DISABLED,
        trig_out: ILATrigOutMode = ILATrigOutMode.DISABLED,
        tsm_registers: Dict = None,
    ) -> None:
        """Trigger using probe compare values.

        Args:
            trigger_position (int): denotes the middle of the window. Range [-1..window_size-1].
                Default value: :attr:`~.ILA_TRIGGER_POSITION_HALF`
            window_count (int): Number of windows to capture. Default value: 1.
            window_size (int): Number of samples per window. Must be a power-of-two value.
                Default value: :attr:`.ILA_WINDOW_SIZE_MAX`
            trigger_condition (ILATriggerCondition): Trigger condition global boolean operator.
            capture_condition (ILACaptureCondition): Capture condition global boolean operator, to filter samples.
            trig_in (ILATrigInMode): Usage of TRIG-IN Port. Default value: :attr:`.ILATrigInMode.DISABLED`
            trig_out (ILATrigOutMode): Specify what drives TRIG-OUT port. Default value: :attr:`ILATrigOutMode.DISABLED`

        """

        def to_tcf_trigger_value(values: [], bit_width: int, enum_def: enum.EnumMeta) -> [str]:
            it = iter(values)
            res = [op + to_bin_str(val, bit_width, enum_def) for op, val in zip(it, it)]
            return res

        def probe_values_to_dict(probe_values: {str, ILAProbeValues}) -> {}:
            res = {}
            for name, p_values in probe_values.items():
                vals = {}
                if (
                    p_values.trigger_value
                    and trigger_condition != ILATriggerCondition.TRIGGER_STATE_MACHINE
                ):
                    vals["trigger_value"] = to_tcf_trigger_value(
                        p_values.trigger_value, p_values.bit_width, p_values.enum_def
                    )
                if self.static_info.has_capture_control and p_values.capture_value:
                    vals["capture_value"] = to_tcf_trigger_value(
                        p_values.capture_value, p_values.bit_width, p_values.enum_def
                    )
                if vals:
                    res[name] = vals
            return res

        # Window size must be an exponent-of-two.
        w_size = (
            self.static_info.data_depth // window_count
            if window_size == ILA_WINDOW_SIZE_MAX
            else window_size
        )
        t_pos = w_size // 2 if trigger_position == ILA_TRIGGER_POSITION_HALF else trigger_position
        control: ILAControl = ILAControl(
            capture_condition, trig_in, trig_out, trigger_condition, t_pos, window_count, w_size
        )

        self._control = control
        # Set probe trigger values.
        self.core_tcf_node.reset_probe(reset_trigger_values=True, reset_capture_values=True)
        tcf_probe_values = probe_values_to_dict(self.probe_values)
        if tcf_probe_values:
            self.core_tcf_node.set_probe(tcf_probe_values)

        control_props = control_to_tcf(self.control)
        self.core_tcf_node.set_property(control_props)
        if tsm_registers:
            self.core_tcf_node.set_property({"__mu_tc_mapping": tsm_registers})
        self._arm()
        self.waveform = None

    def _arm(self):
        self._arm2()
        self.core_tcf_node.arm()

    def _arm2(self):
        # NYI feature
        pass

    @ensure_ila_init
    def upload(self) -> bool:
        """
        Upload waveform. If the ILA has not triggered yet, it will return with value *False*.
        The uploaded waveform is at *self.waveform*.

        Returns (bool):
            True, if a waveform was uploaded.
        """

        self.waveform = None
        uploaded = self.core_tcf_node.upload()
        if uploaded:
            wave = tcf_get_waveform_data(self.core_tcf_node)
            wave["probes"] = self._make_waveform_probes()
            self.waveform = ILAWaveform(**wave)
        return uploaded

    @ensure_ila_init
    def wait_till_done(self, max_wait_minutes: float = None) -> ILAStatus:
        """
        Wait until all data has been captured, or until timeout.
        Call this function after arming the ILA, before uploading the waveform.

        Args:
            max_wait_minutes (float): Max time in minutes for command. If *None*, status monitor never times out.

        Returns (:class:`.ILAStatus`): ILA capture status.
        """
        return self.monitor_status(max_wait_minutes)

    @ensure_ila_init
    def monitor_status(
        self, max_wait_minutes: float = None, progress=None, done: request.DoneFutureCallback = None
    ) -> ILAStatus or request.CsFutureRequestSync:
        """
        Function monitors ILA capture status and waits until all data has been captured, or until timeout
        or the function is cancelled.
        Call this function after arming the ILA, before uploading the waveform.
        The command operates in synchronous mode if *done* argument has default value *None* .

        **Synchronous Mode**

        - Calling this function in synchronous mode, is the same as calling function ILA.wait_until_done().
        - Function waits until all data has been captured in the ILA core, or timeout.
        - Use default argument value *None* for arguments *progress* and *done* .
        - Returns an ILAStatus object.

        **Asynchronous Mode**

        - This mode is useful for reporting the capture status to stdout or a GUI.
        - Function does not block. The main thread continues with the next statement.
        - Returns a *future* object, which represents the monitor.
        - A blocking function should be called later on the *future* object, in order to wait on the calling
          thread until the status monitor has completed.
        - Asynchronous Mode is selected, by specifying a *done* function, which is called after the function has completed.
        - If no user defined callback is needed, set *done* argument to dummy function *chipscopy.null_callback* ,
          to enable asynchronous mode.

        **Future Object**

        When the *monitor_status* function is called in asynchronous mode, it will return a *future* object.
        The *future* object has blocking attributes and functions, which will block the current thread until
        the status monitor has completed.

        Blocking Attributes:

        - *future.result* (None or ILAStatus) - ILAStatus object if capture completed successfully, without timeout.
        - *future.error* - (None or Exception) - None if no error otherwise an exception object, e.g. timeout exception.

        Non-blocking Attribute:

        - *future.progress* (None or ILAStatus) - Access in *progress function*, to read the ILA capture status.

        Blocking Function:

        - *future.wait(timeout=None)* - *None* means wait until status monitor completed. Argument *timeout* is in seconds.

        Non-blocking Function:

        - *future.cancel()*  - Cancels the status monitor. An exception will be raised, in the thread which
          called the function *ILA.monitor_status* .

        **Progress Function**

        - User-defined function which takes one argument *future* .
        - Useful for reporting ILA capture status.
        - The *progress function* is only called when the ILA capture status changes.
        - The *progress function* is called in the TCF Event Thread. The *progress function* must not call any
          ChipScoPy API function, which interacts with the cs_server or the device.

        Example:
        ::

             def monitor_status_done(future):
                if not future.error:
                    # future.result holds an ILAStatus object.
                    print_status(future.progress)


        Args:
            max_wait_minutes (float): Max time in minutes for status monitor. If *None*, status monitor never times out.
            progress(progress_fn) : See Asynchronous Mode, above. This function runs in the TCF Event Thread.
            done(request.DoneFutureCallback): Done callback. This function runs in the TCF Event Thread.

        Returns (:class:`.ILAStatus` or request.CsFutureRequestSync or None):
        """

        def final(future):  # called on main thread
            if future._result:
                self._status = future._result

        def status_process(props: {}) -> ILAStatus:
            return tcf_props_to_status(props, self._tsm_state_names)

        if progress and not done:
            raise ValueError(
                "Function ila.monitor_status(): Cannot specify *progress* argument when argument *done* is None."
            )

        future = self.core_tcf_node.future(done=done, final=final, progress=progress)
        return future.monitor_status(status_process, max_wait_minutes=max_wait_minutes)

    @ensure_ila_init
    def reset_probes(
        self, reset_trigger_values: bool = True, reset_capture_values: bool = True
    ) -> None:
        """Reset probe compare values, to dont-cares.

        Args:
           reset_trigger_values (bool): Resets trigger compare values, for all core probes.
           reset_capture_values (bool): Resets basic capture control compare value, for all probes.
        """
        if reset_trigger_values:
            for values in self.probe_values.values():
                values.trigger_value = []

        if reset_capture_values:
            for values in self.probe_values.values():
                values.capture_value = []

    @ensure_ila_init
    def set_probe_trigger_value(self, name: str, trigger_value: []) -> None:
        """For basic trigger mode, set probe compare value(s).

            A compare value consists of a pair: <operator> and <value>
            <value> may be of type int or binary string of the correct bit_width.
            An empty list is a don't-care value.

            Hex values start with a '0x' prefix.
            Note! String values for 3-bit probes are always interpreted as binary values,
            e.g. "0x0", "0x1", "0xx", "011".


                Example: Test for LSB is '0' on a 4-bit probe.
                   ['==',   'XXX0']

                Example: Range check, assuming the global Trigger Condition is ILATriggerCondition.AND:
                   ['>=',   '0011',   '<=',   '1010']

                Example: Range check, assuming the global Trigger Condition is ILATriggerCondition.AND:
                   ['>=',   3,   '<=',   10]

                Example: Test equal to any of 3 numbers, assuming the global Trigger Condition is ILATriggerCondition.OR:
                   ['==',   '0011',   '==',   '0111',   '==',   '1111']

                Example: 4-bit dont-care value.
                   ['==',   'XXXX']

                Example: Dont-care value, written as an empty list.
                   []

            Some probes have associated enum values, which can be used when setting values.

                Example: Use an Enum value.
                    ['==', Colors.BLUE]

                Example: Use Enum name string.
                    ['==', "BLUE"]

        Args:
           name (str): Probe name.
           trigger_value (list): [<operator>, <value>, ...]   See :class:`~.ILAProbeValues`
        """
        self._set_probe_value(name, trigger_value, is_trigger=True)

    @ensure_ila_init
    def set_probe_capture_value(self, name: str, capture_value: []) -> None:
        """For basic capture mode, set probe compare value to filter samples.

        Args:
           name (str): Probe name.
           capture_value: List with two items: [<operator>, <value>].   See :class:`~.ILAProbeValues`
        """
        if not self.static_info.has_capture_control:
            raise ValueError(
                f'Cannot set capture value for Probe "{name}", '
                f'since ILA "{self.name}" does not support basic capture control.'
            )
        self._set_probe_value(name, capture_value, is_trigger=False)

    @ensure_ila_init
    def get_probe_trigger_value(self, name: str) -> []:
        """Get basic trigger mode compare value(s) for a probe.

        Args:
           name (str): Probe name.

        returns:
           List of <operator>/<value> pairs.  See :class:`~.ila_probe.ILAProbeValues`
        """
        values = self.probe_values.get(name, None)
        if not values:
            raise KeyError(f"Probe {name} is not a defined trigger probe.")
        return values.trigger_value

    @ensure_ila_init
    def get_probe_capture_value(self, name: str) -> []:
        """Get basic capture mode compare value for a probe.

        Args:
           name (str): Probe name.

        returns:
           List with two items [<operator>, <value>].   See :class:`~.ILAProbeValues`
        """
        values = self.probe_values.get(name, None)
        if not values:
            raise KeyError(f"Probe {name} is not a defined trigger probe.")
        return values.capture_value

    def _set_probe_value(self, name: str, value: [], is_trigger: bool) -> None:
        probe = self.probes.get(name, None)
        values: ILAProbeValues = self.probe_values.get(name, None)
        if not probe or not values:
            raise KeyError(f"Probe {name} is not a defined trigger probe.")
        verify_probe_value(value, is_trigger, probe, values.enum_def)
        if is_trigger:
            values.trigger_value = value
        else:
            values.capture_value = value

    @staticmethod
    def _init(tcf_ila: TCF_AxisIlaCoreClient, core_info: CoreInfo, ltx: Optional[Ltx]):
        props = tcf_ila.get_property_group(["static_info", "status", "control"])
        post_process_status(props, None)

        props["tsm_counter_widths"] = [props["tsm_counter_width" + str(idx)] for idx in range(4)]
        static_info = ILAStaticInfo(**filter_props(props, ILA_STATIC_INFO_MEMBERS))
        status = ILAStatus(**filter_props(props, ILA_STATUS_MEMBERS))
        control = control_from_tcf(props)
        ports = ports_from_tcf_props(props)
        if ltx:
            verify_ports(ltx, core_info.uuid, ports)

        probes, probe_to_port_seqs, enum_defs = create_probes_from_ports_and_ltx(
            tcf_ila, ports, ltx, core_info.uuid
        )
        probe_values = {
            probe.name: ILAProbeValues(
                probe.bit_width,
                [],
                [],
                ILAProbeRadix.ENUM if probe.name in enum_defs else ILAProbeRadix.HEX,
                enum_defs.get(probe.name, None),
            )
            for probe in probes.values()
        }
        return {
            "core_info": core_info,
            "static_info": static_info,
            "status": status,
            "control": control,
            "ports": ports,
            "probes": probes,
            "probe_to_port_seqs": probe_to_port_seqs,
            "probe_values": probe_values,
        }

    @ensure_ila_init
    def get_probe_enum(self, name: str) -> Optional[enum.EnumMeta]:
        """Get enum class, which defines valid enum values for the probe.

        Args:
           name (str): Probe name.

        Returns:
            Enum class defining the enum values or None.
        """
        probe = self.probes.get(name, None)
        values: ILAProbeValues = self.probe_values.get(name, None)
        if not probe or not values:
            raise KeyError(f"Probe {name} is not a defined probe.")
        return values.enum_def

    @ensure_ila_init
    def set_probe_enum(
        self, name: str, enum_def: enum.EnumMeta, display_as_enum: bool = True
    ) -> None:
        """Set enum values for a probe, by providing a enum class.

        Args:
           name (str): Probe name.
           enum_def (enum.EnumMeta): Enum class defining enum values, e.g. an enum.IntEnum class.
           display_as_enum (bool): If true, sets probe display index to ``ILAProbeRadix.ENUM``
        """

        probe = self.probes.get(name, None)
        values: ILAProbeValues = self.probe_values.get(name, None)
        if not probe or not values:
            raise KeyError(f"Probe {name} is not a defined probe.")
        verify_probe_enum_def(probe, enum_def)
        values.enum_def = enum_def
        if display_as_enum:
            values.display_radix = ILAProbeRadix.ENUM

    def _make_waveform_probes(self) -> {str, ILAWaveformProbe}:
        return {
            p.name: ILAWaveformProbe(
                p.name,
                p.map,
                self._probe_to_port_seqs[p.map],
                p.is_bus,
                p.bus_left_index,
                p.bus_right_index,
                self.probe_values[p.name].display_radix,
                self.probe_values[p.name].enum_def,
            )
            for p in self.probes.values()
            if p.is_data
        }


@deprecated_api(release="2023.2", replacement="<waveform object>.export_waveform()")
def export_waveform(
    waveform: ILAWaveform,
    export_format: str = "CSV",
    fh_or_filepath: Union[TextIOBase, str] = sys.stdout,
    probe_names: Optional[List[str]] = None,
    start_window_idx: int = 0,
    window_count: Optional[int] = None,
    start_sample_idx: int = 0,
    sample_count: Optional[int] = None,
    include_gap: bool = False,
) -> None:
    """Deprecated function. Use <waveform object>.export_waveform()"""
    if not waveform:
        raise TypeError('Function export_waveform() called with argument "waveform" set to "None".')
    waveform.export_waveform(
        export_format,
        fh_or_filepath,
        probe_names,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
        include_gap,
    )


@deprecated_api(release="2023.2", replacement="<waveform object>.get_data()")
def get_waveform_data(
    waveform: ILAWaveform,
    probe_names: Optional[List[str]] = None,
    start_window_idx: int = 0,
    window_count: Optional[int] = None,
    start_sample_idx: int = 0,
    sample_count: Optional[int] = None,
    include_trigger: bool = False,
    include_sample_info: bool = False,
    include_gap: bool = False,
) -> Dict[str, List[int]]:
    """
    Deprecated function. Use <waveform object>.get_data()
    """
    if not waveform:
        raise TypeError(
            'Function get_waveform_data() called with argument "waveform" set to "None".'
        )

    return waveform.get_data(
        probe_names,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
        include_trigger,
        include_sample_info,
        include_gap,
    )


@deprecated_api(release="2023.2", replacement="<waveform object>.get_probe_data()")
def get_waveform_probe_data(
    waveform: ILAWaveform,
    probe_name: str,
    start_window_idx: int = 0,
    window_count: Optional[int] = None,
    start_sample_idx: int = 0,
    sample_count: Optional[int] = None,
) -> List[int]:
    """
    Deprecated function. Use <waveform object>.get_probe_data()
    """
    if not waveform:
        raise TypeError(
            'Function get_waveform_probe_data() called with argument "waveform" set to "None".'
        )

    return waveform.get_probe_data(
        probe_name,
        start_window_idx,
        window_count,
        start_sample_idx,
        sample_count,
    )
