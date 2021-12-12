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

"""
.. |state| replace::   :class:`ILAState`
.. |cc|    replace::   :class:`ILACaptureCondition`
.. |cmod|  replace::   :class:`ILACaptureMode`
.. |tc|    replace::   :class:`ILATriggerCondition`
.. |tmod|  replace::   :class:`ILATriggerMode`
.. |tout|  replace::   :class:`ILATrigOutMode`
.. |prtd|  replace::   :class:`ILAPort`
.. |prtt|  replace::   :class:`ILAPortType`

ILA Service Overview
---------------------

The ILA TCF Service handles one ILA core.

*Data Model*

The ILA features are represented by "properties". The properties are divided into groups:

* `Core Info Properties`_ - Core version and type information.
* `Static Info Properties`_ - Core capabilities and dimensions.
* `Status Properties`_ - Current core dynamic state.
* `Control Properties`_ - Control of the core.
* `Data Properties`_ - Uploaded waveform.

*Methods*

The Service methods are of the following types:

* `Property Methods`_ - Set/get/reset/report properties.
* `Probe Methods`_ - Create/delete probes. Set/get probe match values.
* `Core Communication Methods`_ - Read/write properties from/to core. Arm the core and upload waveform.

Service Name
------------
.. autodata:: NAME

Properties
----------
Property Groups
^^^^^^^^^^^^^^^
Properties are divided into groups. Properties within a group are often have
their values 'set' or 'get' at the same time.

+--------------------------+-------+------------------------------------------+
| Name                     | Type  | Description                              |
+==========================+=======+==========================================+
| PROP_GROUP_CORE_INFO     | |str| | Core version and type information.       |
+--------------------------+-------+------------------------------------------+
| PROP_GROUP_STATIC_INFO   | |str| | Read-only properties giving              |
|                          |       | capabilities and dimensions.             |
+--------------------------+-------+------------------------------------------+
| PROP_GROUP_STATUS        | |str| | Read-only properties showing current     |
|                          |       | dynamic state.                           |
+--------------------------+-------+------------------------------------------+
| PROP_GROUP_CONTROL       | |str| | Write/Read properties to control core.   |
+--------------------------+-------+------------------------------------------+
| PROP_GROUP_DATA          | |str| | Read-only properties holding waveform.   |
+--------------------------+-------+------------------------------------------+

Core Info Properties
^^^^^^^^^^^^^^^^^^^^^^^^
*Core Info* are read-only properties with core type and version information.

+--------------------------+--------+--------------------------------------------+
| Name                     | Type   | Description                                |
+==========================+========+============================================+
| PROP_CORE_TYPE           | |int|  | Core type number.                          |
+--------------------------+--------+--------------------------------------------+
| PROP_DRV_VER             | |int|  | Software core interface version.           |
+--------------------------+--------+--------------------------------------------+
| PROP_CORE_MAJOR_VER      | |int|  | Core major version.                        |
+--------------------------+--------+--------------------------------------------+
| PROP_CORE_MINOR_VER      | |int|  | Core minor version.                        |
+--------------------------+--------+--------------------------------------------+
| PROP_TOOL_MAJOR_VER      | |int|  | Major version of tool, which created core. |
+--------------------------+--------+--------------------------------------------+
| PROP_TOOL_MAJOR_VER      | |int|  | Minor version of tool, which created core. |
+--------------------------+--------+--------------------------------------------+
| PROP_UUID                | |str|  | Hex value, unique core id within design.   |
+--------------------------+--------+--------------------------------------------+

Static Info Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^
*Static Info* are read-only properties giving the dimensions and feature set of
the core.

+---------------------------+--------+-----------------------------------------+
| Name                      | Type   | Description                             |
+===========================+========+=========================================+
| PROP_DATA_DEPTH           | |int|  | Max sample depth of waveform data.      |
+---------------------------+--------+-----------------------------------------+
| PROP_DATA_WIDTH           | |int|  | Bit width of waveform data.             |
+---------------------------+--------+-----------------------------------------+
| PROP_HAS_ADVANCED_TRIGGER | |bool| | True if core has advanced trigger.      |
+---------------------------+--------+-----------------------------------------+
| PROP_HAS_CAPTURE_CONTROL  | |bool| | True if core has capture control.       |
+---------------------------+--------+-----------------------------------------+
| PROP_HAS_TRIG_IN          | |bool| | True if core has trig_in port.          |
+---------------------------+--------+-----------------------------------------+
| PROP_HAS_TRIG_OUT         | |bool| | True if core has trig_out port.         |
+---------------------------+--------+-----------------------------------------+
| PROP_MATCH_UNIT_COUNT     | |bool| | Number of port match units.             |
+---------------------------+--------+-----------------------------------------+
| PROP_PORT_COUNT           | |int|  | Number of ports.                        |
+---------------------------+--------+-----------------------------------------+
| PROP_PORTS                |[|prtd|]| Ordered list of port definitions.       |
+---------------------------+--------+-----------------------------------------+

Status Properties
^^^^^^^^^^^^^^^^^^^
*Status* read-only properties showing the dynamic status of the core.

+--------------------------+--------+-------------------------------------------+
| Name                     | Type   | Description                               |
+==========================+========+===========================================+
| PROP_CAPTURE_STATE       | |state|| State of capture controller.              |
+--------------------------+--------+-------------------------------------------+
| PROP_IS_ARMED            | |bool| | Capture control is armed.                 |
+--------------------------+--------+-------------------------------------------+
| PROP_IS_FULL             | |bool| | True if waveform data buffer is full.     |
+--------------------------+--------+-------------------------------------------+
| PROP_SAMPLES_CAPTURED    | |int|  | Current window captured samples count.    |
+--------------------------+--------+-------------------------------------------+
| PROP_WINDOWS_CAPTURED    | |bool| | Number of fully captured windows.         |
+--------------------------+--------+-------------------------------------------+

Control Properties
^^^^^^^^^^^^^^^^^^^^
*Control* read/write properties are used to control the core.

+--------------------------+--------+-----------------------------------------+
| Name                     | Type   | Description                             |
+==========================+========+=========================================+
| PROP_ARM                 | |bool| | Set to True, to arm the core.           |
+--------------------------+--------+-----------------------------------------+
| PROP_CAPTURE_CONDITION   | |cc|   | Capture condition: AND, OR, NAND, NOR   |
+--------------------------+--------+-----------------------------------------+
| PROP_CAPTURE_MODE        | |cmod| | Capture mode: always or basic.          |
+--------------------------+--------+-----------------------------------------+
| PROP_TRIG_OUT_MODE       | |tout| | Trig out signal choices.                |
+--------------------------+--------+-----------------------------------------+
| PROP_TRIGGER_CONDITION   | |tc|   | Trigger Condition: AND, OR, NAND, NOR,  |
|                          |        |    IMMEDIATELY.                         |
+--------------------------+--------+-----------------------------------------+
| PROP_TRIGGER_MODE        | |tmod| | Trigger mode. What to trigger on.       |
+--------------------------+--------+-----------------------------------------+
| PROP_TRIGGER_POSITION    | |int|  | Trigger position within window.         |
|                          |        | 0 <= trigger position < window size     |
+--------------------------+--------+-----------------------------------------+
| PROP_WINDOW_COUNT        | |int|  | Number of windows.                      |
+--------------------------+--------+-----------------------------------------+
| PROP_WINDOW_SIZE         | |int|  | Sample count per window. The value must |
|                          |        | be a power-of-two.                      |
+--------------------------+--------+-----------------------------------------+

Data Properties
^^^^^^^^^^^^^^^^^
The *Data* read-only properties represent the uploaded waveform.

+--------------------------+-----------------+--------------------------------+
| Name                     | Type            | Description                    |
+==========================+=================+================================+
| trace_data               | |bytearray|     | Waveform bit values.           |
+--------------------------+-----------------+--------------------------------+
| trace_width              | |int|           | Data sample bit width.         |
+--------------------------+-----------------+--------------------------------+
| trace_sample_count       | |int|           | Captured sample count.         |
+--------------------------+-----------------+--------------------------------+
| trace_trigger_position   | [|int|]         | List of trigger positions.     |
|                          |                 | One value, per window.         |
+--------------------------+-----------------+--------------------------------+
| trace_window_size        | |int|           | Sample count per window.       |
+--------------------------+-----------------+--------------------------------+

The samples in the trace_data are aligned on byte boundaries.

This formula can be used to read a bit from the trace_data:
::

    bytes_per_sample = len(trace_data) // trace_sample_count

    def get_bit_value(trace_data: bytearray, bytes_per_sample: int, sample_index: int, data_bit_index: int) -> bool:
        byte_value = trace_data[sample_index * bytes_per_sample + data_bit_index // 8]
        mask = 1 << (data_bit_index & 0x7)
        return (byte_value & mask) != 0

Property Value Types
--------------------

PropertyPermission Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: PropertyPermission
    :members:
    :undoc-members:

Capture State Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILAState
    :members:
    :undoc-members:

Trigger Mode Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILATriggerMode
    :members:
    :undoc-members:

Trigger Condition Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILATriggerCondition
    :members:
    :undoc-members:

Capture Mode Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILACaptureMode
    :members:
    :undoc-members:

Capture Condition Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILACaptureCondition
    :members:
    :undoc-members:

Trig Out Mode Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILATrigOutMode
    :members:
    :undoc-members:




Param Types
-----------

PropertyValues
^^^^^^^^^^^^^^
.. autodata:: PropertyValues

Dict to hold property values.

::

    PropertyValues = {str, Any}


=============== ================
Key             Value
=============== ================
property name   property value
=============== ================

.. _ILAPort:

ILAPort
^^^^^^^^^^^^
.. autodata:: ILAPort

Dict type to hold port attributes.

::

    ILAPort = Dict[str, Any]


============== ======= ========================================================
Key            Type    Value
============== ======= ========================================================
data_bit_index int     Data sample start bit index. '-1' for trigger-only port.
index          int     Port index.
mu_count       int     Port match unit count.
mus            [|int|] List of match unit indices.
port_type      |prtt|  Capabilities of the port.
bit_width      int     Port bit width.
============== ======= ========================================================

.. _ILAPortType:

ILAPortType Enum Constants
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.axis_ila_core_client.ILAPortType
    :members:
    :undoc-members:


.. _ILAProbeAttrs:

ILAProbeAttrs
^^^^^^^^^^^^^
.. autodata:: ILAProbeAttrs

Dict type to hold probe attributes.
::

    ILAProbeAttrs = Dict[str, Any]

================= =========== ==============================================
Key               Value Type  Description
================= =========== ==============================================
bit_width         int         Probe bit width.
capture_value     |str|       One match value string, for capture control.
name              |str|       Probe name.
net_name          |str|       Netlist name
map               |str|       Definition string for probe mapping.
mu_count          |int|       Number of match units for trigger.
port_type         |prtt|      Port type associated with trigger probe.
trigger_value     [|str|]     mu_count of match value strings.
================= =========== ==============================================

.. _ila_prop_match_value_table:

Match values consist of an operator followed by one match character per bit.
::

    Example:
        { 'capture_value':  '==0001_XXXX',
          'trigger_value': ['<=0011_1111', '>0000_0111'] }

========= =================================================================
Operator  Description
========= =================================================================
==        Equal
!=        Not equal
<         Less than
<=        Equal or less than
>         Greater than
>=        Equal or Greater than
||        Reduction OR
========= =================================================================



========= =================================================================
Bit Value Description
========= =================================================================
_         Underscore separator for readability.
X         Don't care bit matches any bit-value.
0         Zero
1         One
F         Falling. Transition 1 -> 0
R         Rising. Transition 0 -> 1
L         Laying. Opposite to R.
S         Staying. Opposite to F.
B         Either Falling or Rising.
N         No change. Opposite to B.
========= =================================================================



General Methods
---------------

initialize
^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.initialize

terminate
^^^^^^^^^
.. automethod:: AxisIlaCoreClient.terminate

Property Methods
----------------

get_property
^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.get_property

get_property_group
^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.get_property_group

report_property
^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.report_property

report_property_group
^^^^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.report_property_group

reset_property
^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.reset_property

reset_property_group
^^^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.reset_property_group

set_property
^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.set_property

set_property_group
^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.set_property_group


Probe Methods
-------------

define_probe
^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.define_probe

define_port_probes
^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.define_port_probes

undefine_probe
^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.undefine_probe

get_probe
^^^^^^^^^
.. automethod:: AxisIlaCoreClient.get_probe

set_probe
^^^^^^^^^
.. automethod:: AxisIlaCoreClient.set_probe

Core Communication Methods
--------------------------

arm
^^^
.. automethod:: AxisIlaCoreClient.arm

commit_property_group
^^^^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.commit_property_group

refresh_property_group
^^^^^^^^^^^^^^^^^^^^^^
.. automethod:: AxisIlaCoreClient.refresh_property_group


upload
^^^^^^
.. automethod:: AxisIlaCoreClient.upload

"""

import enum
import time
from typing import List, Dict, Any

from chipscopy import dm
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.tcf import protocol

# Service name.
NAME = "AxisILA"
"""
ILA service name.
"""


PROP_GROUP_CORE_INFO = "core_info"
PROP_GROUP_STATIC_INFO = "static_info"
PROP_GROUP_STATUS = "status"
PROP_GROUP_CONTROL = "control"
PROP_GROUP_DATA = "data"
PROP_CORE_TYPE = "core_type"
PROP_DRV_VER = "drv_ver"
PROP_CORE_MAJOR_VER = "core_major_ver"
PROP_CORE_MINOR_VER = "core_minor_ver"
PROP_TOOL_MAJOR_VER = "tool_major_ver"
PROP_TOOL_MINOR_VER = "tool_minor_ver"
PROP_UUID = "uuid"
PROP_DATA_DEPTH = "data_depth"
PROP_DATA_WIDTH = "data_width"
PROP_HAS_ADVANCED_TRIGGER = "has_advanced_trigger"
PROP_HAS_CAPTURE_CONTROL = "has_capture_control"
PROP_HAS_TRIG_IN = "has_trig_in"
PROP_HAS_TRIG_OUT = "has_trig_out"
PROP_MATCH_UNIT_COUNT = "match_unit_count"
PROP_PORT_COUNT = "port_count"
PROP_PORTS = "ports"
PROP_CAPTURE_STATE = "capture_state"
PROP_IS_ARMED = "is_armed"
PROP_IS_FULL = "is_full"
PROP_IS_TAS = "is_tas"
PROP_SAMPLE_COUNT_STATUS = "samples_captured"
PROP_WINDOW_COUNT_STATUS = "windows_captured"
PROP_ARM = "arm_ila"
PROP_CAPTURE_CONDITION = "capture_condition"
PROP_CAPTURE_MODE = "capture_mode"
PROP_TRIG_OUT_MODE = "trig_out_mode"
PROP_TRIGGER_CONDITION = "trigger_condition"
PROP_TRIGGER_MODE = "trigger_mode"
PROP_TRIGGER_POSITION = "trigger_position"
PROP_WINDOW_COUNT = "window_count"
PROP_WINDOW_SIZE = "window_size"
PROP_TRACE_DATA = "trace_data"
PROP_TRACE_WIDTH = "trace_width"
PROP_TRACE_SAMPLE_COUNT = "trace_sample_count"
PROP_TRACE_TRIGGER_POSITION = "trace_trigger_position"
PROP_TRACE_WINDOW_SIZE = "trace_window_size"


class ILAPortType(enum.IntFlag):
    """

        Capabilities of a port.

        MU_EQ supports eq, neq match operators.

        MU_EDGE supports edge transition match bit values: 'R', 'F', 'B', 'N'

        MU_REL supports relational match operators: lt, gt, lte, gte.

        When passing enum values to/from API functions, use int values.

    ::

        IS_DATA    = 0x01
        IS_TRIGGER = 0x02
        MU_EDGE    = 0x04
        MU_EQ      = 0x08
        MU_REL     = 0x10

        IS_TRIGGER_DATA = IS_TRIGGER | IS_DATA
        MU_EDGE_EQ_REL = MU_EDGE | MU_EQ | MU_REL


    """

    IS_DATA = 0x01
    IS_TRIGGER = 0x02
    MU_EDGE = 0x04
    MU_EQ = 0x08
    MU_REL = 0x10
    IS_TRIGGER_DATA = IS_TRIGGER | IS_DATA
    MU_EDGE_EQ_REL = MU_EDGE | MU_EQ | MU_REL


ILAPort = Dict[str, Any]
ILAProbeAttrs = Dict[str, Any]


class ILAState(enum.Enum):
    """
        *Trigger states:*

        State transitions, in case of one window.

        IDLE -> PRE_TRIGGER -> TRIGGER -> POST_TRIGGER -> IDLE

        When passing enum values to/from API functions, use string values.

    ::

        IDLE
        PRE_TRIGGER
        TRIGGER
        POST_TRIGGER
    """

    IDLE = 0
    PRE_TRIGGER = 1
    TRIGGER = 2
    POST_TRIGGER = 3


class ILATrigOutMode(enum.Enum):
    """
        Trig_out signal control choices.

        When passing enum values to/from API functions, use string values.

    ::

        DISABLED
        TRIGGER_ONLY
        TRIG_IN_ONLY
        TRIGGER_OR_TRIG_IN
    """

    DISABLED = 0
    TRIGGER_ONLY = 1
    TRIG_IN_ONLY = 2
    TRIGGER_OR_TRIG_IN = 3


class ILATriggerCondition(enum.Enum):
    """
        Trigger condition combining Match Units.

        When passing enum values to/from API functions, use string values.

    ::

        OR
        AND
        NOR
        NAND
        IMMEDIATELY
    """

    OR = 0
    AND = 1
    NOR = 2
    NAND = 3
    IMMEDIATELY = 4


class ILATriggerMode(enum.Enum):
    """
        Choice between basic mode using probe match values, advanced sequential trigger,
        trig_in or a valid combination of them.

        When passing enum values to/from API functions, use string values.

    ::

        BASIC_ONLY
        ADVANCED_ONLY
        BASIC_OR_TRIG_IN
        ADVANCED_OR_TRIG_IN
        TRIG_IN_ONLY
    """

    BASIC_ONLY = 0
    ADVANCED_ONLY = 1
    BASIC_OR_TRIG_IN = 2
    ADVANCED_OR_TRIG_IN = 3
    TRIG_IN_ONLY = 4


class ILACaptureCondition(enum.Enum):
    """
        OR, AND, NAND, NOR are choices to combine probe match values.

        When passing enum values to/from API functions, use string values.

    ::

        OR
        AND
        NOR
        NAND
    """

    OR = 0
    AND = 1
    NOR = 2
    NAND = 3


class ILACaptureMode(enum.Enum):
    """
    BASIC mode, will use capture condition to decide which samples to keep.

    When passing enum values to/from API functions, use string values.
    """

    ALWAYS = 0
    BASIC = 1


class AxisIlaCoreClient(CorePropertyClient):
    """TCF AXIS-ILA Client"""

    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "ila"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(NAME)

    #
    #  General methods
    #
    def initialize(self, done: DoneHWCommand) -> None:
        """
        Initialize data model for the ILA core.

        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.initialize(self.ctx, done_cb)
        return self.add_pending(token)

    def terminate(self, done: DoneHWCommand) -> None:
        """
        Remove data model for the ILA core.

        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.terminate(self.ctx, done_cb)
        return self.add_pending(token)

    #
    # Probe Methods
    #
    def define_probe(self, probe_defs: List[Dict[str, Any]], done: DoneHWCommand) -> None:
        """
        Define ILA probe(s).

        A probe has the following attributes, stored in a :ref:`ILAProbeAttrs` dict:

        ============== ========== ====================================
        Attribute      Value Type Description
        ============== ========== ====================================
        name           |str|      Probe name.
        net_name       |str|      Netlist name
        map            |str|      Definition string for probe mapping.
        ============== ========== ====================================

        Example: Two probes named *sensor* and *enable* which are 8 bits and 1 bit wide.
        ::

            pdefs = [
                {'name': 'sensor', 'net_name': 'sensor', 'map': 'port3[7:0]'},
                {'name': 'enable', 'net_name': 'enable', 'map': 'port1[3]'},
            ]
            self.define_probe(pdefs)


        Example of 'map' values:
        ::

            A 'map' value is a white space separated list of port slices and constants in any order,
             e.g. "111 probe4[7..1] 0" Constants are binary and ports are referred by port index.
            Underline character ('_') is allowed for readability in constants.
            Data only probes, can have constant bits and map multiple ports.
            Trigger ports cannot have constants bits and must map only to one port.

            "0101" - specifies a binary constant value.
            "port0[31:0]" - specifies a 32-bit slice of a port.
            "port0" - No explicit range means all bits of the physical port. "port0" means same as "probe0[31:0]", if the port is 32 bits wide.
            "port0[4]" - Shorter notation for "port0[4:4]
            "0101 port0[31:0] 1101" - specifies a constant and port slice.

        :param probe_defs: Probe definitions.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.define_probe(self.ctx, probe_defs, done_cb)
        return self.add_pending(token)

    def define_port_probes(self, options: Dict[str, Any], done: DoneHWCommand) -> None:
        """
        Define ILA probe(s), one probe per ILA core port. Name of probe will be 'name_prefix' + "port_index".

        ============== ========== ============================================
        Options        Value Type Description
        ============== ========== ============================================
        name_prefix    |str|      Default: 'probe\_'.
        force          |bool|     Default: False. 'True' value will remove
                                    any previous probes with the same names.
        ============== ========== ============================================

        :param options: Property definitions.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.define_port_probes(self.ctx, options, done_cb)
        return self.add_pending(token)

    def undefine_probe(self, probe_names: List[str], done: DoneHWCommand) -> None:
        """
        Delete probes.

        :param probe_names: List of probe names. Empty list means delete every probe.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.undefine_probe(self.ctx, probe_names, done_cb)
        return self.add_pending(token)

    def get_probe(
        self, probe_names: List[str], attrs: List[str], done: DoneHWCommand
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return probe definitions. Bit ranges of probes.

        :param probe_names: Probe name or list of probe names. Empty list means every probe.
        :param attrs: Attributes to return for probes. Empty list means all attributes.
        :return: Top dict key is probe name. Inner dict values are probe attrs :ref:`ILAProbeAttrs` .
        """
        service, done_cb = self.make_done(done)
        token = service.get_probe(self.ctx, probe_names, attrs, done_cb)
        return self.add_pending(token)

    def set_probe(self, attrs: Dict[str, Dict[str, Any]], done: DoneHWCommand) -> None:
        """

        :param attrs: Top dict key is probe name. Inner dict values are dicts with probe attributes :ref:`ILAProbeAttrs`.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.set_probe(self.ctx, attrs, done_cb)
        return self.add_pending(token)

    def reset_probe(
        self, reset_trigger_values: bool, reset_capture_values: bool, done: DoneHWCommand
    ) -> None:
        """
        :param reset_trigger_values: Reset all probe trigger values to don't cares.
        :param reset_capture_values: Reset all probe capture values to don't cares.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.reset_probe(self.ctx, reset_trigger_values, reset_capture_values, done_cb)
        return self.add_pending(token)

    #
    # Core Communication Methods
    #
    def arm(self, done: DoneHWCommand) -> None:
        """
        Arm the core with current *control* property settings.

        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.arm(self.ctx, done_cb)
        return self.add_pending(token)

    def get_trigger_registers(self, done: DoneHWCommand) -> Dict[str, str]:
        """
        Get current trigger register setup as hex string numbers.
        Helpful when preparing a design for trigger-at-startup.

        :param done: Callback with result and any error.
        :return: Register hex values, for trigger setup.

        """
        service, done_cb = self.make_done(done)
        token = service.get_trigger_registers(self.ctx, done_cb)
        return self.add_pending(token)

    def upload(self, done: DoneHWCommand) -> bool:
        """
        Checks if ILA has triggered. If so, will upload waveform and set property group 'Data'
        with waveform data.

        :param done: Callback with result and any error.
        :return: True, if command uploaded a waveform.
        """
        service, done_cb = self.make_done(done)
        token = service.upload(self.ctx, done_cb)
        return self.add_pending(token)

    def monitor_status(self, status_processor_fn, max_wait_minutes=None):
        """
        Keeps checking ILA status until buffer is full or timeout.
        request.result has value None until buffer is full when it is assigned status(ILAStatus).
        request.progress is an chipscopy.ila.ILAStatus instance, with current ILA status.

        :param status_processor_fn: Function which processes status tcf properties.
        :param max_wait_minutes(float: Max number of minutes, until timeout.
        """
        assert self.request
        service = self.get_service_proxy()
        start_time = time.time()
        prev_status = None
        timeout = max_wait_minutes * 60.0 if max_wait_minutes is not None else None

        def check_status(token, error, result):
            nonlocal prev_status
            status = None
            # check if canceled
            if not self.request:
                return
            if not error:
                status = status_processor_fn(result)
                if prev_status != status:
                    prev_status = status
                    self.request.set_progress(status)

            # check for error or positive result
            if error:
                self.request.set_exception(error)
            elif (
                result
                and isinstance(result, dict)
                and (
                    result.get("is_full", False)
                    or result.get("capture_state", ILAState.IDLE) == ILAState.IDLE
                )
            ):
                self.request.set_result(status)
            elif timeout is not None and time.time() - start_time > timeout:
                if not self.request._error:
                    self.request.set_result(None)
            else:  # Buffer not yet full, check again in 500ms
                protocol.invokeLaterWithDelay(
                    500, service.refresh_property_group, self.ctx, ["status"], done=check_status
                )

        service.refresh_property_group(self.ctx, ["status"], check_status)
