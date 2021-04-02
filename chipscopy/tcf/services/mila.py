# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

"""
.. |state| replace::   :class:`MILAState`
.. |tc|    replace::   :class:`MILATriggerCondition`
.. |tpos|  replace::   :class:`MILATriggerPosition`
.. |csel|  replace::   :class:`MILAClockSelect`
.. |dsel|  replace::   :class:`MILADataSelect`

MILA Service Overview
---------------------

The MILA Service communicates with DDRMC Mini ILA cores.

*Data Model*

The MILA model is kept in "properties". The properties are divided into groups:

* `Static Config Properties`_ - Core capabilities and dimensions.
* `Status Properties`_ - Current core dynamic state.
* `Control Properties`_ - Control of the core.
* `Data Properties`_ - Uploaded waveform.
* `Data Select Properties`_ - Input Data Probe Selection MUX and associated properties.
* `Mux Local Enable Properties`_ - Mux Node local input enable vs enable of previous Mux Node lane input.
* `Mux Local Select Properties`_ - Mux Node local input selection per lane, when lane has local input enabled.


*Methods*

The Service methods are of the following types:

* `Property Methods`_ - Set/get/reset/report properties.
* `Probe Methods`_ - Create/delete probes. Set/get probe match values.
* `Mux Tree Methods`_ - Setup/report the Mux Tree Node settings.
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

+----------------------------------+-------+------------------------------------------+
| Name                             | Type  | Description                              |
+==================================+=======+==========================================+
| PROP_GROUP_STATIC_INFO           | |str| | Read-only properties giving              |
|                                  |       | capabilities and dimensions.             |
+----------------------------------+-------+------------------------------------------+
| PROP_GROUP_STATUS                | |str| | Read-only properties showing current     |
|                                  |       | dynamic state.                           |
+----------------------------------+-------+------------------------------------------+
| PROP_GROUP_CONTROL               | |str| | Write/Read properties to control core.   |
+----------------------------------+-------+------------------------------------------+
| PROP_GROUP_DATA                  | |str| | Read-only properties holding waveform.   |
+----------------------------------+-------+------------------------------------------+
| PROP_GROUP_DATA_SELECT           | |str| | Properties for register ila_cntrl.       |
+----------------------------------+-------+------------------------------------------+
| PROP_GROUP_MUX_LOCAL_ENABLE      | |int| | Mux select between local/lane inputs.    |
|                                  |       | One value {0,1} per lane.                |
+----------------------------------+-------+------------------------------------------+
| PROP_GROUP_MUX_LOCAL_SELECT      | |int| | Mux select which input signal "group",   |
|                                  |       | when MUX_LOCAL_ENABLE, selects "local".  |
|                                  |       | One value {0-7} per lane.                |
+----------------------------------+-------+------------------------------------------+

Static Config Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^
*Static Config* are read-only properties giving the dimensions and feature set of
the core.

+--------------------------+--------+-----------------------------------------+
| Name                     | Type   | Description                             |
+==========================+========+=========================================+
| PROP_DATA_DEPTH          | |int|  | Sample depth of waveform data.          |
+--------------------------+--------+-----------------------------------------+
| PROP_DATA_WIDTH          | |int|  | Bit width of waveform data.             |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_CAPTURE_CONTROL | |bool| | True if core has capture control.       |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_CIN             | |bool| | True if core has carry in port.         |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_COUT            | |bool| | True if core has carry out port.        |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_MU              | |bool| | True if core has match units            |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_STORAGE         | |bool| | True if core stores waveform data.      |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_SYNC            | |bool| | True if synchronized logic is included  |
|                          |        | to control control input ports.         |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_TRIGGER_IN      | |bool| | True if core has trigger in port.       |
+--------------------------+--------+-----------------------------------------+
| PROP_HAS_TRIGGER_OUT     | |bool| | True if core has trigger out port.      |
+--------------------------+--------+-----------------------------------------+
| PROP_TRIGGER_LEVELS      | |int|  | Number of sequential trigger levels.    |
+--------------------------+--------+-----------------------------------------+

Status Properties
^^^^^^^^^^^^^^^^^^^
*Status* properties are read-only, which show the dynamic atatus of the core.

+--------------------------+--------+-----------------------------------------+
| Name                     | Type   | Description                             |
+==========================+========+=========================================+
| PROP_CARRY               | |bool| | True if all match units match.          |
+--------------------------+--------+-----------------------------------------+
| PROP_DONE                | |bool| | True if waveform data buffer is full.   |
+--------------------------+--------+-----------------------------------------+
| PROP_SAMPLE_COUNT        | |int|  | Current number of captured samples.     |
+--------------------------+--------+-----------------------------------------+
| PROP_STATE               | |state|| State of capture controller.            |
+--------------------------+--------+-----------------------------------------+
| PROP_TRIGGER_SAMPLE      | |int|  | Trigger location within capture buffer. |
|                          |        | Used by service to organize waveform    |
|                          |        | data.                                   |
+--------------------------+--------+-----------------------------------------+

Control Properties
^^^^^^^^^^^^^^^^^^^^
*Control* read/write properties are used to control the core.
Some control properties have list value, with one entry per match unit.
The ILA has 3 match units, which can work in sequence A -> B -> C.

+--------------------------+--------------+-----------------------------------------+
| Name                     | Type         | Description                             |
+==========================+==============+=========================================+
| PROP_ARM                 | |bool|       | Set to True, to arm the core.           |
+--------------------------+--------------+-----------------------------------------+
| PROP_CARRY_IN_ENABLE     | List[|str|]  | Enable carry-out hold value.            |
|                          |              | One char string per match unit [A,B,C]  |
|                          |              | see :ref:`prop_match_value_mm_table`    |
+--------------------------+--------------+-----------------------------------------+
| PROP_CARRY_OUT_HOLD      | List[|bool|] | Enable carry-out hold value.            |
|                          |              | One value per match unit [A,B,C]        |
+--------------------------+--------------+-----------------------------------------+
| PROP_CLK_SEL             | |csel|       | Set clock sel mux for probe input       |
+--------------------------+--------------+-----------------------------------------+
| PROP_ENABLE              | |bool|       | Set to False, to reset core.            |
+--------------------------+--------------+-----------------------------------------+
| PROP_MATCH_VALUE         | List[|str|]  | Bit values in a string. MSB to LSB.     |
|                          |              | For valid bit values:                   |
|                          |              | see :ref:`prop_match_value_mm_table`    |
|                          |              | One string value per match unit [A,B,C] |
+--------------------------+--------------+-----------------------------------------+
| PROP_TRIGGER_POSITION    | |tpos|       | Trigger position within trace buffer.   |
+--------------------------+--------------+-----------------------------------------+
| PROP_WINDOW_SIZE         | |int|        | Sample count per window. The value must |
|                          |              | be a power-of-two. Property value only  |
|                          |              | applied when trigger position is a zero.|
+--------------------------+--------------+-----------------------------------------+
| PROP_TRIGGER_CONDITION   | List[|tc|]   | Trigger condition: AND, OR.             |
|                          |              | One value per match unit [A,B,C]        |
+--------------------------+--------------+-----------------------------------------+

Data Properties
^^^^^^^^^^^^^^^^^
The *Data* read-only properties represent the uploaded waveform.

The samples in the trace_data are aligned on byte boundaries.

This formula can be used to read a bit from the trace_data:
::

    bytes_per_sample = len(trace_data) // trace_sample_count

    def get_bit_value(trace_data: bytearray, bytes_per_sample: int, sample_index: int, data_bit_index: int) -> bool:
        byte_value = trace_data[sample_index * bytes_per_sample + data_bit_index // 8]
        mask = 1 << (data_bit_index & 0x7)
        return (byte_value & mask) != 0

+--------------------------+-----------------+--------------------------------+
| Name                     | Type            | Description                    |
+==========================+=================+================================+
| trace_data               | |bytearray|     | Waveform bit values.           |
+--------------------------+-----------------+--------------------------------+
| trace_width              | |int|           | Data sample bit width.         |
+--------------------------+-----------------+--------------------------------+
| trace_sample_count       | |int|           | Sample count.                  |
+--------------------------+-----------------+--------------------------------+
| trace_trigger_position   | List[|int|]     | List of trigger positions.     |
|                          |                 | One value, per window.         |
+--------------------------+-----------------+--------------------------------+
| trace_window_size        | |int|           | Sample count per window.       |
+--------------------------+-----------------+--------------------------------+

Data Select Properties
^^^^^^^^^^^^^^^^^^^^^^
The *Data Select* properties represent the device ila_capture_data register.
These properties are read from the device when the MILA Service is initialized and written to the device
during the 'arm' command. Property data_sel, is set by method mux_select_inputs.

+----------------+--------+---------------------------------------------------------------------+
| Name           | Type   | Description                                                         |
+================+========+=====================================================================+
| sel_fifo_empty | |int|  | XPI related.                                                        |
+----------------+--------+---------------------------------------------------------------------+
| phy_nib_sel    | |int|  | Physical nibble selection for GT Status or signals mapped physically|
+----------------+--------+---------------------------------------------------------------------+
| channel_sel    | |int|  | Channel selection when used for XPI selections of debug data.       |
+----------------+--------+---------------------------------------------------------------------+
| byte_sel       | |int|  | Byte selection when used for Cal/XPI selections of debug dataC      |
+----------------+--------+---------------------------------------------------------------------+
| data_sel       | |dsel| | ila_capture_data_sel mux selection.                                 |
+----------------+--------+---------------------------------------------------------------------+

Mux Local Enable Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. line-block::

    The *Mux Local Enable* properties choose for each Mux Node output lane, between
    local input or input from previous Mux Node.
    Default value is [0,0,0,0,0,0,0,0]
    which means that none of the 8 local input data chunks are selected.
    With the default value, all Mux Node lanes are feedthroughs from previous Mux Node.

+----------------+-------------+-------------------------------------------+
| Name           | Type        | Description                               |
+================+=============+===========================================+
|\*.local_enable | List[|int|] | 8 values. '1' for local input.            |
|                |             | '0' choose previous Mux Node lane output. |
+----------------+-------------+-------------------------------------------+


Mux Local Select Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. line-block::

    The *Mux Local Select* properties select which local inputs to connect to lane outputs,
    when a lane local enable is '1'.
    Default value for these properties are [0,0,0,0,0,0,0,0].

+----------------+--------------+---------------------------------------------------------------------+
| Name           | Type         | Description                                                         |
+================+==============+=====================================================================+
|\*.local_select | List[|int|]  | 8 values. When local enabled for output lane, selects local inputs. |
+----------------+--------------+---------------------------------------------------------------------+



Property Value Types
--------------------

.. _prop_match_value_mm_table:

Match Value Bits
^^^^^^^^^^^^^^^^
=====  ===========================
Value  Description
=====  ===========================
'0'    Zero.
'1'    One.
'R'    Rising edge. Transition '0' to '1'.
'F'    Falling edge. Transition '1' to '0'.
'B'    Both. Either rising or falling.
'N'    No edge. No transition.
'X'    Don't care. Any value.
'_'    Separator for readability.
=====  ===========================

_PropertyPermission Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.client.core_property_client.PropertyPermission
    :members:
    :undoc-members:

Capture State Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.tcf.services.mila.MILAState
    :members:
    :undoc-members:

Trigger Position Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.tcf.services.mila.MILATriggerPosition
    :members:
    :undoc-members:

Trigger Condition Enum Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: chipscopy.tcf.services.mila.MILATriggerCondition
    :members:
    :undoc-members:

Param Types
-----------

PropertyValues
^^^^^^^^^^^^^^
.. autodata:: PropertyValues

Dict to hold property values.

::

    PropertyValues = Dict[str, Any]

=============== ================
Key             Value
=============== ================
property name   property value
=============== ================


.. _MILAProbeDefs:

MILAProbeDefs
^^^^^^^^^^^^^
.. autodata:: MILAProbeDefs

Dict type to hold probe definitions.
::

    MILAProbeDefs = Dict[str, List[int]]

============ ===============================================
Key          Value
============ ===============================================
probe name   List with left bit index, right bit index.`
============ ===============================================

Example: Two probes named *sensor* and *enable* which are 8 bits and 1 bit wide.
::

    pp = {
        'sensor': [15, 8],
        'enable': [2, 2]
    }



General Methods
---------------

getName
^^^^^^^
.. automethod:: MILAService.getName

connect
^^^^^^^
.. automethod:: MILAService.connect

initialize
^^^^^^^^^^
.. automethod:: MILAService.initialize

terminate
^^^^^^^^^
.. automethod:: MILAService.terminate

Property Methods
----------------

get_property
^^^^^^^^^^^^
.. automethod:: MILAService.get_property

get_property_group
^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.get_property_group

report_property
^^^^^^^^^^^^^^^
.. automethod:: MILAService.report_property

report_property_group
^^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.report_property_group

reset_property
^^^^^^^^^^^^^^
.. automethod:: MILAService.reset_property

reset_property_group
^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.reset_property_group

set_property
^^^^^^^^^^^^
.. automethod:: MILAService.set_property

set_property_group
^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.set_property_group


Probe Methods
-------------

define_probe
^^^^^^^^^^^^
.. automethod:: MILAService.define_probe

undefine_probe
^^^^^^^^^^^^^^
.. automethod:: MILAService.undefine_probe

get_probe
^^^^^^^^^
.. automethod:: MILAService.get_probe

get_probe_match_value
^^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.get_probe_match_value

set_probe_match_value
^^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.set_probe_match_value

Core Communication Methods
--------------------------

arm
^^^
.. automethod:: MILAService.arm

commit_property_group
^^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.commit_property_group

refresh_property_group
^^^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.refresh_property_group


upload
^^^^^^
.. automethod:: MILAService.upload


Mux Tree Methods
----------------

mux_add_node
^^^^^^^^^^^^
.. automethod:: MILAService.mux_add_node

mux_build_tree
^^^^^^^^^^^^^^
.. automethod:: MILAService.mux_build_tree

mux_select_inputs
^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.mux_select_inputs

mux_get_selected_inputs
^^^^^^^^^^^^^^^^^^^^^^^
.. automethod:: MILAService.mux_get_selected_inputs

mux_commit
^^^^^^^^^^
.. automethod:: MILAService.mux_commit

mux_refresh
^^^^^^^^^^^
.. automethod:: MILAService.mux_refresh

mux_report
^^^^^^^^^^
.. automethod:: MILAService.mux_report


"""

import enum
from typing import Any, Dict, List, Union, Tuple
from chipscopy.tcf.services import Service, DoneHWCommand
from chipscopy.client.core_property_client import PropertyValues

# Property Group Names
PROP_GROUP_STATIC_INFO      = 'static_info'
PROP_GROUP_STATUS           = 'status'
PROP_GROUP_CONTROL          = 'control'
PROP_GROUP_DATA             = 'data'
PROP_GROUP_DATA_SELECT      = 'data_select'
PROP_GROUP_MUX_LOCAL_ENABLE = 'mux_local_enable'
PROP_GROUP_MUX_LOCAL_SELECT = 'mux_local_select'

# Static Info Property Names
PROP_DATA_DEPTH      = 'data_depth'
PROP_DATA_WIDTH      = 'data_width'
PROP_HAS_CAPTURE     = 'has_capture_control'
PROP_HAS_CIN         = 'has_cin'
PROP_HAS_COUT        = 'has_cout'
PROP_HAS_MU          = 'has_mu'
PROP_HAS_STORAGE     = 'has_storage'
PROP_HAS_SYNC        = 'has_sync'
PROP_HAS_TRIGGER_IN  = 'has_trigger_in'
PROP_HAS_TRIGGER_OUT = 'has_trigger_out'
PROP_LEVELS          = 'levels'

# Status Property Names
PROP_CARRY           = 'carry'
PROP_DONE            = 'done'
PROP_SAMPLE_COUNT    = 'sample_count'
PROP_STATE           = 'state'
PROP_TRIGGER_SAMPLE  = 'trigger_sample'

# Control Property Names
PROP_ARM                = 'arm'
PROP_CARRY_IN_ENABLE    = 'carry_in_enable'
PROP_CARRY_OUT_HOLD     = 'carry_out_hold'
PROP_CLK_SEL            = 'clk_sel'
PROP_ENABLE             = 'enable'
PROP_MATCH_VALUE        = 'match_value'
PROP_TRIGGER_POSITION   = 'trigger_position'
PROP_WINDOW_SIZE        = 'window_size'
PROP_TRIGGER_CONDITION  = 'trigger_condition'

# Data Property Names
PROP_TRACE_DATA             = 'trace_data'
PROP_TRACE_WIDTH            = 'trace_width'
PROP_TRACE_SAMPLE_COUNT     = 'trace_sample_count'
PROP_TRACE_TRIGGER_POSITION = 'trace_trigger_position'
PROP_TRACE_WINDOW_SIZE      = 'trace_window_size'

MILAProbeDefs = Dict[str, List[int]]
""" 
Dictionary type, to hold probe definitions.

Key: probe name
Value: Two item list with left_bit_index and right_bit_index.
"""


class MILAState(enum.Enum):
    """
    *Trigger states:*

    IDLE -> START -> PRE_TRIGGER -> TRIGGER -> POST_TRIGGER -> IDLE

    START is "starting capture (mostly here for one cycle)".
    PRE_TRIGGER is "Circular buffer is filling to the point where trigger is set"
    TRIGGER is "circular buffer is full and capture logic is looking for matching condition".
    When passing as values to/from API functions, use string values.
    """

    START = 0
    PRE_TRIGGER = 1
    TRIGGER = 2
    POST_TRIGGER = 3
    IDLE = 4


class MILATriggerPosition(enum.Enum):
    """
    The value of enum indicates percentage of buffer to capture before the trigger.
    Enum *EVERY_SAMPLE*, means every sample is a trigger sample.

    When passing as values to/from API functions, use string values.
    """

    FIRST = 0
    ONE_QUARTER = 25
    HALF = 50
    THREE_QUARTERS = 75
    LAST = 100
    EVERY_SAMPLE = 1000


class MILATriggerCondition(enum.Enum):
    """
    Trigger condition can be *AND* or *OR*.

    When passing as values to/from API functions, use string values.
    """

    OR = 0
    AND = 1


class MILAClockSelect(enum.Enum):
    """
    Selection of clock domain for ILA input data.

    When passing as values to/from API functions, use string values.
    """

    MC = 0
    INOC = 1


class MILADataSelect(enum.Enum):
    """
    Selection for Ila_capture_data_sel MUX.

    When passing as values to/from API functions, use string values.
    """

    DDRMC = 0
    XPI_WRITE = 1
    XPI_READ = 2
    CAL = 3
    RPI = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12
    THIRTEEN = 13
    FOURTEEN = 14
    FIFTEEN = 15


# Service name.
NAME = "MILA"
"""
MILA service name.
"""


class MILAService(Service):
    """TCF MILA Service interface."""

    def getName(self) -> str:
        """
        Get service name of this service.

        :returns: Service name :const:`NAME`.
        """
        return NAME

    def connect(self, ctx: str, target: Dict[str, Any], done: DoneHWCommand):
        """
        Connect to hw_server. This function does not belong here. Move to other "Service".

        :param ctx: Core context id.
        :param target: Values for 'HOST', 'PORT', 'CORE_OFFSETS'
        :param done: Callback with result and any error.
        """

    def initialize(self, ctx: str, done: DoneHWCommand) -> None:
        """
        Initialize data model for the MILA core.

        :param ctx: Core context id.
        :param done: Callback with result and any error.
        """

    def terminate(self, ctx: str, done: DoneHWCommand) -> None:
        """
        Remove data model for the MILA core.

        :param ctx: Core context id.
        :param done: Callback with result and any error.
        """

    def write32(self, ctx: str, write_addr: int, data: int, domain_index: int, done: DoneHWCommand) -> None:
        """
        Write 32 bit register.

        :param ctx: Core context id.
        :param write_addr: Address.
        :param data: 32 bit data
        :param domain_index: 0 for DDRMC_MAIN, 1 for DDRMC_NOC
        """

    def read32(self, ctx: str, read_addr: int, read_word_count: int, domain_index: int, done: DoneHWCommand) \
            -> Union[List[int], int]:
        """
        Read 32 bit register

        :param ctx: Core context id.
        :param read_addr: address to read from.
        :param read_word_count: number of 32 bit words.
        :param domain_index: 0 for DDRMC_MAIN, 1 for DDRMC_NOC
        :return int value if read_word_count == 1. Otherwise list of int values.
        """


    #
    # Property Methods
    #
    def get_property(self, ctx: str, property_names: List[str], done: DoneHWCommand)\
            -> PropertyValues:
        """
        Get values for properties.

        :param ctx: Core context id.
        :param property_names: List of property names. Empty list means get all properties.
        :param done: Callback with result and any error.
        :return: Property name/value pairs in a dict. See :data:`PropertyValues`.
        """
        raise NotImplementedError("Abstract method")

    def get_property_group(self, ctx: str, property_group_names: List[str], done: DoneHWCommand)\
            -> PropertyValues:
        """
        Get property values for property groups.

        :param ctx: Core context id.
        :param property_group_names: List of property group names. Empty list means all properties.
        :param done: Callback with result and any error.
        :return: Properties for named group names. :data:`PropertyValues`
        """
        raise NotImplementedError("Abstract method")

    def report_property(self, ctx: str, property_names: List[str], done: DoneHWCommand)\
            -> Dict[str, Dict[str, Any]]:

        """
        Return description of properties.

        Example: Description of property 'state'
        ::

            Attributes:

            group_name - Property group which the property belongs to.
            type - Property value type
            permission - Permissions control which methods can operate on property.
            name - Name of property
            default_value - Reset value for property.
            value - Current value of the property.

            {
                'state': {
                    'group_name': 'status',
                    'type': 'MILAState'),
                    'permission': 6,        # corresponds to bitwise enum value <_PropertyPermission.REFRESH|GET: 6>,
                    'name': 'state',
                    'default_value': 'IDLE' # corresponds to enum value <MILAState.IDLE: 4>,
                    'value': 'IDLE'         # <MILAState.IDLE: 4>)
                }
            }

        For further information about 'permission', see :class:`_PropertyPermission`

        :param ctx: Core context id.
        :param property_names: List of property names. Empty list means get all properties.
        :param done: Callback with result and any error.
        :return: Dict of property description dicts.
        """
        raise NotImplementedError("Abstract method")

    def report_property_group(self, ctx: str, groups: List[str], done: DoneHWCommand) \
            -> Dict[str, Dict[str, Any]]:
        """
        Return description of properties, which belong to argument 'groups'.

        :param ctx: Core context id.
        :param groups: List of property group names. Empty list means all properties.
        :param done: Callback with result and any error.
        :return: Dict of property description dicts.
        """
        raise NotImplementedError("Abstract method")

    def reset_property(self, ctx: str, property_names: List[str], done: DoneHWCommand) -> None:
        """
        Reset property values, to default values.

        :param ctx: Core context id.
        :param property_names: List of property names. Empty list means all resetable properties.
           Properties in property groups 'control' and 'data' are resettable,
           e.g. the trigger capture will be set to trigger on any value.
        :param done: Callback with result and any error.
        """

        raise NotImplementedError("Abstract method")

    def reset_property_group(self, ctx: str, groups: List[str], done: DoneHWCommand) -> None:
        """

        :param ctx: Core context id.
        :param groups:  List of property group names. Empty list means all resettable properties.
           Property groups 'control' and 'data' are resettable.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def set_property(self, ctx: str, property_values: PropertyValues, done: DoneHWCommand) -> None:
        """
        Set properties. If no properties specified, do nothing.
        Validates properties values for correctness.

        :param ctx: Core context id.
        :param property_values: Property name/value pairs.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def set_property_group(self, ctx: str, property_values: PropertyValues, done: DoneHWCommand) -> None:
        """
        Same behaviour as :meth:`set_property`

        :param ctx: Core context id.
        :param property_values: Property name/value pairs.
        :param done: Callback with result and any error.
        """

        self.set_property(ctx, property_values, done)

    #
    # Mux Tree Methods
    #
    def mux_add_node(self, ctx: str,
                     memory_domain: str,
                     addr: Union[int,None],
                     name: str,
                     long_name: str,
                     has_local_inputs: bool,
                     in0: str,
                     in1: str,
                     done: DoneHWCommand) -> None:
        """
        Defines a mux_node and declares which mux nodes feed into this mux_node.

        Example: Adding 3 mux nodes.
        ::

            # Using function alias for convenience.
            an = service.mux_add_node

            an(ctx, DDRMC_MAIN, 0x1450, 'ACAM0'  , 'd_0_13', in1='PT0'  )
            an(ctx, DDRMC_MAIN, 0x1454, 'DBUF0.1', 'd_0_14', in0='DBUF0.0', in1='ACAM0', has_local_inputs=False)
            an(ctx, DDRMC_MAIN, 0x1458, 'COM.0'  , 'd_0_15', in1='DBUF0.1')

        :param ctx: Core context id.
        :param memory_domain: DDRMC_MAIN or DDRMC_NOC
        :param addr: Address offset for mux node register
        :param name: Name of mux node. Must be unique.
        :param long_name: Description or other name.
        :param has_local_inputs: True if node has local inputs. False if "inputs" connected to other mux node.
        :param in0: Name of mux node, connecting to "data inputs", when no local inputs.
        :param in1: Name of mux node, connecting to channel inputs.
        """

    def mux_build_tree(self, ctx: str,
                       clk_sel_is_1_mux: str,
                       ila_capture_data_sel_muxes: [str],
                       done: DoneHWCommand) -> None:
        """
        .. line-block::

            Specifies which mux nodes, are connected to ila_cntrl.clk_sel and ila_capture_data_sel muxes.
            Builds tree data structure for the mux nodes.
            All calls to mux_add_node, need to be prior to calling this function.

            Defines local_enable, local_select properties for mux nodes which have register addresses.
            A mux node named 'xmpu' would get two registers: 'xmpu.in_mux' and 'xmpu.out_mux'.
            An in_mux property represents the local input selection mux.
            Default in_mux value is [False,False,False,False,False,False,False,False]
            An out_mux property represents the output channel selection mux.
            Default out_mux value is [0,1,2,3,4,5,6,7].
            The defaults correspond the mux node is a straight feed-through for the 8 channels.
            
        Example: Call to mux_build_tree
        ::

            service.mux_build_tree('ADEC',['COM.2', 'XPI_WRITE', 'XPI_READ', 'CAL', 'RPI'])


        :param ctx: Core context id.
        :param clk_sel_is_1_mux: Name of mux node, selected when ila_cntrl.clk_sel mux is '1'
        :param ila_capture_data_sel_muxes: list of mux nodes, connected to ila_capture_data_sel.
        """

    def mux_select_inputs(self, ctx: str, mux_node_inputs:[Tuple[str, int]],
                          done: DoneHWCommand) -> None:
        """
        Select in order which 16 bit input data chunks are connected to the MILA.
        The setting will be applied to the in_mux/out_mux properties.

        Example: Connect up first 4 input chunks from mux node 'MRS0' and every 2nd chunks from 'RETRY1'.
        ::

            service.mux_select_inputs([('MRS0', 0), ('MRS0', 1), ('MRS0', 2), ('MRS0', 3),
                                       ('RETRY1', 0), ('RETRY1', 2), ('RETRY1', 4), ('RETRY1', 6)])

        :param ctx: Core context id.
        :param mux_node_inputs: List of (node_name, input_chunk_index) pairs.
        """

    def mux_get_selected_inputs(self, ctx: str, done: DoneHWCommand) \
            -> [Union[None, Tuple[str, int]]]:
        """
        Based on property values, determined which input chunks are connected to the MILA.

        :param ctx: Core context id.
        :return: List of entry. Each entry is either a (node_name, input_chunk_index) pair or None for no input chunk.
        """

    def mux_commit(self, ctx: str, done: DoneHWCommand) -> None:
        """
        Write mux node '*.local_enable' and '*.local_select' property settings to device MILA registers.
        Note! ila_cntrl.clk_sel and ila_captur_data_sel settings are not written to MILA registers.

        :param ctx: Core context id.
        """

    def mux_refresh(self, ctx: str, done: DoneHWCommand) -> dict:
        """
        Read device mux node MILA registers to update mux node '*.local_enable' and '*.local_select' properties.
        Note! ila_cntrl.clk_sel and ila_capture_data_sel settings are not updated.

        :param ctx: Core context id.
        :return: local_enable/local_select property name-value pairs.
        """
    def mux_report(self, ctx: str, skip_default: bool, done: DoneHWCommand) -> str:
        """
        Report mux node settings, based on property values.

        :param ctx: Core context id.
        :param skip_default: If True, mux nodes set as "straight feed-throughs" are excluded from the report.
        :return: report as a text string.
        """


    #
    # Probe Methods
    #
    def define_probe(self, ctx: str, probe_defs: MILAProbeDefs, done: DoneHWCommand) -> None:
        """
        Create MILA probe(s), which are used to set/get a slice range
        of the MILA core property PROP_MATCH_VALUE.
        A probe has a left_index and a right_index, defining the bit range the probe use of the match word.

        Example: Two probes named *sensor* and *enable* which are 8 bits and 1 bit wide.
        ::

            pdefs = {
                'sensor': [15,8],
                'enable': [2,2]
            }
            service.create_probe( ctx, pdefs)

        :param ctx: Core context id.
        :param probe_defs: Property definitions.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def undefine_probe(self, ctx: str, probe_names: List[str], done: DoneHWCommand) -> None:
        """
        Delete probes.

        :param ctx: Core context id.
        :param probe_names: List of probe names. Empty list means delete every probe.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def get_probe(self, ctx: str, probe_names: List[str], done: DoneHWCommand) -> MILAProbeDefs:
        """
        Return probe definitions. Bit ranges of probes.

        :param ctx: Core context id.
        :param probe_names: Probe name or list of probe names. Empty list means every probe.
        :param done: Callback with result and any error.
        :return: See :ref:`MILAProbeDefs`. A Dict. Key is probe name. Value is 2-item list giving probe bit range.
        """
        raise NotImplementedError("Abstract method")

    def get_probe_match_value(self, ctx: str, probe_names: List[str], done: DoneHWCommand)\
            -> Dict[str, str]:
        """
        Get match match value for probe(s).

        :param ctx: Core context id.
        :param probe_names: Probe name list. Empty list means get all probe match values.
        :param done: Callback with result and any error.
        :return: Probe name/probe match value pairs.
        """
        raise NotImplementedError("Abstract method")

    def set_probe_match_value(self, ctx: str, match_pairs: Dict[str, str], done: DoneHWCommand) -> None:
        """

        :param ctx: Core context id.
        :param match_pairs: Probe name/probe match value pairs.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    #
    # Core Communication Methods
    #
    def arm(self, ctx: str, done: DoneHWCommand) -> None:
        """
        Arm the core with current *control* property settings.

        :param ctx: Core context id.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def commit_property_group(self, ctx: str, groups: List[str], done: DoneHWCommand) -> None:
        """
        Write current property group values to the core.

        :param ctx: Core context id.
        :param groups: Group name or list of names.
            Empty list means property groups, which can be written to the core.
            Only the property group 'control' can be written to the MILA core.
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def refresh_property_group(self, ctx: str, groups: List[str], done: DoneHWCommand) -> PropertyValues:
        """
        Read values from the core, update MILA properties
        and return those property values to caller.

        :param ctx: Core context id.
        :param groups: List of group names.
            Empty list means all MILA refreshable groups.
            All MILA groups are refreshable, except 'static_info'.
        :param done: Callback with result and any error.
        :returns: Property name/value pairs.
        """
        raise NotImplementedError("Abstract method")

    def upload(self, ctx: str, done: DoneHWCommand) -> bool:
        """
        Checks if core trace buffer is full. If full will upload waveform and set property group 'Data'
        with waveform data.

        :param ctx: Core context id.
        :param done: Callback with result and any error.
        :return: True, if command uploaded a waveform.
        """
        raise NotImplementedError("Abstract method")
