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

import enum
from dataclasses import dataclass
from pprint import pformat
from typing import Dict, Any

from chipscopy.client.axis_ila_core_client import (
    ILATriggerCondition as TCF_ILATriggerCondition,
    ILATriggerMode as TCF_ILATriggerMode,
    ILACaptureCondition as TCF_ILACaptureCondition,
    ILACaptureMode as TCF_ILACaptureMode,
)
from chipscopy.api import dataclass_fields, filter_props
from chipscopy.shared.ila_util import (
    prop_to_enum,
    replace_enum_values,
)

""" Constant for indicating 'trigger in the middle of waveform window."""
ILA_TRIGGER_POSITION_HALF = -1

""" Constant for 'Maximum window sample depth."""
ILA_WINDOW_SIZE_MAX = -1


class ILACaptureCondition(enum.Enum):
    """
    For Basic Capture Control, the global boolean operator of participating probe comparators.

    ==================== ================================
    Enum Value           Description
    ==================== ================================
    ALWAYS               Capture all samples.
    AND                  AND probe comparators to filter data.
    OR                   OR probe comparators to filter data.
    NAND                 NAND probe comparators to filter data.
    NOR                  NOR probe comparators to filter data.
    ==================== ================================

    """

    ALWAYS = 4
    OR = 0
    AND = 1
    NOR = 2
    NAND = 3


class ILATriggerCondition(enum.Enum):
    """
    For Trigger Condition, set trigger mode including basic trigger global boolean operator
    of participating probe comparators

    =====================  ================================
    Enum Value             Description
    =====================  ================================
    AND                    Basic Trigger mode: AND probe comparators.
    OR                     Basic Trigger mode: OR probe comparators.
    NAND                   Basic Trigger mode: NAND probe comparators.
    NOR                    Basic Trigger mode: NOR probe comparators.
    IMMEDIATELY            Trigger now.
    TRIGGER_STATE_MACHINE  Advanced Trigger mode: TSM file decides when to trigger.
    =====================  ================================

    """

    OR = 0
    AND = 1
    NOR = 2
    NAND = 3
    IMMEDIATELY = 4
    TRIGGER_STATE_MACHINE = 5


class ILATrigInMode(enum.Enum):
    """
    =====================  ================================
    Enum Value             Description
    =====================  ================================
    DISABLED               No TRIG-IN port use.
    TRIG_IN_ONLY           Trigger only on TRIG-IN port.
    TRIGGER_OR_TRIG_IN     Trigger on basic/trigger mode or on TRIG-IN port.
    =====================  ================================

    """

    DISABLED = 0
    TRIG_IN_ONLY = 1
    TRIGGER_OR_TRIG_IN = 2


class ILATrigOutMode(enum.Enum):
    """
    Choices for Trig-Out port.

    ==================== ================================
    Enum Value           Description
    ==================== ================================
    DISABLED             Disables the TRIG_OUT port.
    TRIGGER_ONLY         Result of the basic/advanced trigger condition.
    TRIG_IN_ONLY         Propagates the TRIG_IN port to the TRIG_OUT port.
    TRIGGER_OR_TRIG_IN   OR-ing of the basic/advanced trigger and TRIG_IN port.
    ==================== ================================

    """

    DISABLED = 0
    TRIGGER_ONLY = 1
    TRIG_IN_ONLY = 2
    TRIGGER_OR_TRIG_IN = 3


class ILAState(enum.Enum):
    """
    ILA State Transitions:
        IDLE -> PRE_TRIGGER -> TRIGGER -> POST_TRIGGER -> IDLE

    =====================  ================================
    Enum Value             Description
    =====================  ================================
    IDLE                   Not armed.
    PRE_TRIGGER            Capturing pre-trigger samples.
    TRIGGER                Waiting for trigger.
    POST_TRIGGER           Capturing post-trigger samples.
    =====================  ================================

    """

    IDLE = 0
    PRE_TRIGGER = 1
    TRIGGER = 2
    POST_TRIGGER = 3


@dataclass(frozen=True)
class ILAControl:
    """Trigger setup"""

    capture_condition: ILACaptureCondition
    """Basic capture cntrol global boolean operator. See :class:`ILACaptureCondition`"""
    trig_in_mode: ILATrigInMode
    """Usage of TRIG-IN port. See :class:`ILATrigInMode`"""
    trig_out_mode: ILATrigOutMode
    """Usage of TRIG-OUT port. See :class:`ILATrigOutMode`"""
    trigger_condition: ILATriggerCondition
    """Global boolean operator, for trigger probes. See :class:`ILATriggerCondition`"""
    trigger_position: int
    """Trigger position index, within data window."""
    trigger_state_machine: str
    """Trigger State Machine, as a string."""
    window_count: int
    """Number of data windows."""
    window_size: int
    """Sample count for a window."""

    def __str__(self) -> str:
        return pformat(self.__dict__, 2)


ILA_CONTROL_MEMBERS = dataclass_fields(ILAControl)


@dataclass(frozen=True)
class ILAStatus:
    """Dynamic status of ILA capture controller"""

    capture_state: ILAState
    """Capture state. See :class:`ILAState`"""
    is_armed: bool
    """Trigger is armed."""
    is_full: bool
    """Data buffer is full."""
    is_trigger_at_startup: bool
    """ILA is armed at startup."""
    samples_captured: int
    """Number of samples captured in current data window."""
    windows_captured: int
    """Number of fully captured data windows."""
    samples_requested: int
    """Number of samples per window, as requested when was ILA armed."""
    windows_requested: int
    """Number of windows, as requested when ILA was armed."""
    trigger_position_requested: int
    """Trigger position, as requested when ILA was armed."""

    def __str__(self) -> str:
        return pformat(self.__dict__, 2)


ILA_STATUS_MEMBERS = dataclass_fields(ILAStatus)


# ILAStatus functions
def post_process_status(props: {}) -> None:
    props["capture_state"] = ILAState[props["capture_state"]]
    props["is_trigger_at_startup"] = props.get("is_tas", False)
    props["samples_requested"] = props.get("window_depth_readback")
    props["windows_requested"] = props.get("window_count_readback")
    props["trigger_position_requested"] = props.get("trigger_pos_readback")


def tcf_props_to_status(props: {}) -> ILAStatus:
    """ Make immutable ILAStatus instance from status dict."""
    post_process_status(props)
    return ILAStatus(**filter_props(props, ILA_STATUS_MEMBERS))


def tcf_refresh_status(tcf_node) -> ILAStatus:
    """Read dynamic status."""
    props = tcf_node.refresh_property_group(["status"])
    return tcf_props_to_status(props)


# ILAControl functions
__enum_control = (
    ("capture_condition", ILACaptureCondition),
    ("trig_out_mode", ILATrigOutMode),
    ("trigger_condition", ILATriggerCondition),
)


def control_from_tcf(props: {}) -> ILAControl:
    # No translation for trigger_position, window_count, window_size, trigger_out_mode
    cc = props.copy()

    is_tsm = props["trigger_mode"] in [
        TCF_ILATriggerMode.ADVANCED_OR_TRIG_IN.name,
        TCF_ILATriggerMode.ADVANCED_ONLY.name,
    ]
    is_trigger_or_trig_in = props["trigger_mode"] in [
        TCF_ILATriggerMode.BASIC_OR_TRIG_IN.name,
        TCF_ILATriggerMode.ADVANCED_OR_TRIG_IN.name,
        TCF_ILATriggerMode.TRIG_IN_ONLY.name,
    ]

    # trigger condition
    del cc["trigger_mode"]
    if is_tsm:
        cc["trigger_condition"] = ILATriggerCondition.TRIGGER_STATE_MACHINE

    # trig_in_mode
    if is_trigger_or_trig_in:
        cc["trig_in_mode"] = (
            ILATrigInMode.TRIGGER_OR_TRIG_IN if is_trigger_or_trig_in else ILATrigInMode.TRIG_IN
        )
    else:
        cc["trig_in_mode"] = ILATrigInMode.DISABLED

    # capture mode, capture condition
    del cc["capture_mode"]
    if props["capture_mode"] == TCF_ILACaptureMode.ALWAYS:
        cc["capture_condition"] = ILACaptureCondition.ALWAYS

    # trigger_state_machine not yet supported.
    cc["trigger_state_machine"] = ""

    prop_to_enum(cc, __enum_control)
    return ILAControl(**filter_props(cc, ILA_CONTROL_MEMBERS))


def control_to_tcf(cc: ILAControl) -> Dict[str, Any]:
    # trigger condition
    if cc.trigger_condition == ILATriggerCondition.TRIGGER_STATE_MACHINE:
        tcf_t_condition = TCF_ILATriggerCondition.AND.name
    else:
        tcf_t_condition = cc.trigger_condition.name

    # trigger mode
    if cc.trig_in_mode == ILATrigInMode.TRIG_IN_ONLY:
        tcf_t_mode = TCF_ILATriggerMode.TRIG_IN_ONLY.name
    elif cc.trigger_condition == ILATriggerCondition.TRIGGER_STATE_MACHINE:
        if cc.trig_in_mode == ILATrigInMode.TRIGGER_OR_TRIG_IN:
            tcf_t_mode = TCF_ILATriggerMode.ADVANCED_OR_TRIG_IN.name
        else:
            tcf_t_mode = TCF_ILATriggerMode.ADVANCED.name
    elif cc.trig_in_mode == ILATrigInMode.TRIGGER_OR_TRIG_IN:
        tcf_t_mode = TCF_ILATriggerMode.BASIC_OR_TRIG_IN.name
    else:
        tcf_t_mode = TCF_ILATriggerMode.BASIC_ONLY.name

    # capture mode, capture condition
    if cc.capture_condition == ILACaptureCondition.ALWAYS:
        tcf_capture_mode = TCF_ILACaptureMode.ALWAYS.name
        tcf_capture_condition = TCF_ILACaptureCondition.AND.name
    else:
        tcf_capture_mode = TCF_ILACaptureMode.BASIC
        tcf_capture_condition = cc.capture_condition.name

    res = {
        "capture_mode": tcf_capture_mode,
        "capture_condition": tcf_capture_condition,
        "trig_out_mode": cc.trig_out_mode.name,
        "trigger_mode": tcf_t_mode,
        "trigger_condition": tcf_t_condition,
        "trigger_position": cc.trigger_position,
        "window_count": cc.window_count,
        "window_size": cc.window_size,
    }
    replace_enum_values(res)

    return res
