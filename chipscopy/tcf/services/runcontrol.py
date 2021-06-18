# *****************************************************************************
# * Copyright (c) 2011, 2013-2014, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""TCF Runcontrol service interface.

.. |detach| replace:: :meth:`~RunControlContext.detach`
.. |doneGetState| replace:: :meth:`~DoneGetState.doneGetState`
.. |getAddress| replace:: :meth:`~RunControlISA.getAddress`
.. |getChildren| replace:: :meth:`~RunControlService.getChildren`
.. |getContext| replace:: :meth:`~RunControlService.getContext`
.. |getISA| replace:: :meth:`~RunControlContext.getISA`
.. |getSize| replace:: :meth:`~RunControlISA.getSize`
.. |getState| replace:: :meth:`~RunControlContext.getState`
.. |resume| replace:: :meth:`~RunControlContext.resume`
.. |suspend| replace:: :meth:`~RunControlContext.suspend`
.. |terminate| replace:: :meth:`~RunControlContext.terminate`
.. |DoneGetChildren| replace:: :class:`DoneGetChildren`
.. |DoneCommand| replace:: :class:`DoneCommand`
.. |DoneGetContext| replace:: :class:`DoneGetContext`
.. |DoneGetISA| replace:: :class:`DoneGetISA`
.. |MemoryContext| replace:: :class:`~tcf.services.memory.MemoryContext`
.. |RunControlContext| replace:: :class:`RunControlContext`
.. |RunControlISA| replace:: :class:`RunControlISA`
.. |RunControlListener| replace:: :class:`RunControlListener`

Properties
----------
RunControl Context Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+--------------------+--------------+-----------------------------------------+
| Name               | Type         | Description                             |
+====================+==============+=========================================+
| PROP_BP_GROUP      | |basestring| | Context ID of a breakpoints group that  |
|                    |              | contains the context. Members of same   |
|                    |              | group share same breakpoint instances:  |
|                    |              | a breakpoint is planted once for the    |
|                    |              | group, no need to plant the breakpoint  |
|                    |              | for each member of the group.           |
+--------------------+--------------+-----------------------------------------+
| PROP_CAN_COUNT     | |int|        | Bit-set of `Resume Modes`_ values that  |
|                    |              | can be used with count > 1.             |
+--------------------+--------------+-----------------------------------------+
| PROP_CAN_DETACH    | |bool|       | **True** if detach command is supported |
|                    |              | by the context.                         |
+--------------------+--------------+-----------------------------------------+
| PROP_CAN_RESUME    | |bool|       | Bit-set of `Resume Modes`_ values that  |
|                    |              | are supported by the context.           |
+--------------------+--------------+-----------------------------------------+
| PROP_CAN_SUSPEND   | |bool|       | **True** if suspend command is supported|
|                    |              | by the context.                         |
+--------------------+--------------+-----------------------------------------+
| PROP_CAN_TERMINATE | |bool|       | **True** if terminate command is        |
|                    |              | supported by the context.               |
+--------------------+--------------+-----------------------------------------+
| PROP_CREATOR_ID    | |basestring| | ID of a context that created this       |
|                    |              | context.                                |
+--------------------+--------------+-----------------------------------------+
| PROP_HAS_STATE     | |bool|       | **True** if context has execution       |
|                    |              | state - can be suspended/resumed.       |
+--------------------+--------------+-----------------------------------------+
| PROP_ID            | |basestring| | Run control context ID.                 |
+--------------------+--------------+-----------------------------------------+
| PROP_IS_CONTAINER  | |bool|       | **True** if the context is a container. |
|                    |              | Container can propagate run control     |
|                    |              | commands to his children.               |
+--------------------+--------------+-----------------------------------------+
| PROP_NAME          | |basestring| | Human readable context name.            |
+--------------------+--------------+-----------------------------------------+
| PROP_PARENT_ID     | |basestring| | Context parent (owner) ID, for a thread |
|                    |              | it is same as process ID.               |
+--------------------+--------------+-----------------------------------------+
| PROP_PROCESS_ID    | |basestring| | Context process (memory space) ID.      |
+--------------------+--------------+-----------------------------------------+
| PROP_RC_GROUP      | |basestring| | Context ID of a run control group that  |
|                    |              | contains the context. Members of same   |
|                    |              | group are always suspended and resumed  |
|                    |              | together: resuming/suspending a context |
|                    |              | resumes/suspends all members of the     |
|                    |              | group.                                  |
+--------------------+--------------+-----------------------------------------+
| PROP_SYMBOLS_GROUP | |basestring| | Context ID of a symbols group that      |
|                    |              | contains the context. Members of a      |
|                    |              | symbols group share same symbol reader  |
|                    |              | configuration settings, like user       |
|                    |              | defined memory map entries and source   |
|                    |              | lookup info.                            |
+--------------------+--------------+-----------------------------------------+

.. _RunControl-Resume-Modes:

Resume Modes
^^^^^^^^^^^^
All resume modes are of type |int|.

+----------------------------+------------------------------------------------+
| RM_RESUME                  | Resume context.                                |
+----------------------------+------------------------------------------------+
| RM_REVERSE_RESUME          | Start running backwards. Execution will        |
|                            | continue until suspended by command or         |
|                            | breakpoint.                                    |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_INTO       | Reverse of ``RM_STEP_INTO``. This effectively  |
|                            | "un-executes" the previous instruction.        |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_INTO_LINE  | Reverse of ``RM_STEP_INTO_LINE``, Resume       |
|                            | backward execution of given context until      |
|                            | control reaches an instruction that belongs to |
|                            | a different line of source code. If a function |
|                            | is called, stop at the beginning of the last   |
|                            | line of the function code. Error is returned if|
|                            | line number information not available.         |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_INTO_RANGE | Reverse of ``RM_STEP_INTO_RANGE``.             |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_OUT        | Reverse of ``RM_STEP_OUT``. Resume backward    |
|                            | execution of the given context until control   |
|                            | reaches the point where the current function   |
|                            | was called.                                    |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_OVER       | Reverse of ``RM_STEP_OVER`` - run backwards    |
|                            | over a single instruction. If the instruction  |
|                            | is a function call then don't stop until get   |
|                            | out of the function.                           |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_OVER_LINE  | Reverse of ``RM_STEP_OVER_LINE``. Resume       |
|                            | backward execution of given context until      |
|                            | control reaches an instruction that belongs to |
|                            | a different source line. If the line contains  |
|                            | a function call then don't stop until get out  |
|                            | of the function. Error is returned if line     |
|                            | number information not available.              |
+----------------------------+------------------------------------------------+
| RM_REVERSE_STEP_OVER_RANGE | Reverse of ``RM_STEP_OVER_RANGE``.             |
+----------------------------+------------------------------------------------+
| RM_REVERSE_UNTIL_ACTIVE    | Run reverse until the context becomes active.  |
+----------------------------+------------------------------------------------+
| RM_STEP_INTO               | Step a single instruction. If the instruction  |
|                            | is a function call then stop at first          |
|                            | instruction of the function.                   |
+----------------------------+------------------------------------------------+
| RM_STEP_INTO_LINE          | Step a single source code line.  If the line   |
|                            | contains a function call then stop at first    |
|                            | line of the function.                          |
+----------------------------+------------------------------------------------+
| RM_STEP_INTO_RANGE         | Step instruction until PC is outside the       |
|                            | specified range for any reason.                |
+----------------------------+------------------------------------------------+
| RM_STEP_OUT                | Run until control returns from current         |
|                            | function.                                      |
+----------------------------+------------------------------------------------+
| RM_STEP_OVER               | Step over a single instruction. If the         |
|                            | instruction is a function call then don't stop |
|                            | until the function returns.                    |
+----------------------------+------------------------------------------------+
| RM_STEP_OVER_LINE          | Step over a single source code line. If the    |
|                            | line contains a function call then don't stop  |
|                            | until the function returns.                    |
+----------------------------+------------------------------------------------+
| RM_STEP_OVER_RANGE         | Step over instructions until PC is outside the |
|                            | specified range. Any function call within the  |
|                            | range is considered to be in range.            |
+----------------------------+------------------------------------------------+
| RM_UNTIL_ACTIVE            | Run until the context becomes active -         |
|                            | scheduled to run on a target CPU.              |
+----------------------------+------------------------------------------------+

State Reasons
^^^^^^^^^^^^^
State change reason of a context. Reason can be any text, but if it is one of
predefined strings, a generic client might be able to handle it better.

+---------------------+-------------------------------------------------------+
| Name                | Description                                           |
+=====================+=======================================================+
| REASON_BREAKPOINT   | Context has been suspended by a breakpoint hit.       |
+---------------------+-------------------------------------------------------+
| REASON_CONTAINER    | Context is supspended because it container is         |
|                     | suspended.                                            |
+---------------------+-------------------------------------------------------+
| REASON_ERROR        | Context has been suspended by an error.               |
+---------------------+-------------------------------------------------------+
| REASON_EXCEPTION    | Context has been suspended by an exception.           |
+---------------------+-------------------------------------------------------+
| REASON_SHAREDLIB    | Context has been suspended by a sharedlib.            |
+---------------------+-------------------------------------------------------+
| REASON_SIGNAL       | Context has been suspended by a signal.               |
+---------------------+-------------------------------------------------------+
| REASON_STEP         | Context has been suspended by a step request.         |
+---------------------+-------------------------------------------------------+
| REASON_USER_REQUEST | Context has been suspended by user request.           |
+---------------------+-------------------------------------------------------+
| REASON_WATCHPOINT   | Context has been suspended by a watchpoint hit.       |
+---------------------+-------------------------------------------------------+

State Optional Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^
Those information may appear in the context state. See the *param* parameter
of |doneGetState|.

+--------------------------+--------------+-----------------------------------+
| Name                     | Type         | Description                       |
+==========================+==============+===================================+
| STATE_BREAKPOINT_IDS     | |list|       | Breakpoint IDs the context is     |
|                          |              | suspended on.                     |
+--------------------------+--------------+-----------------------------------+
| STATE_PC_ERROR           | |int|        | Program counter the error occurred|
|                          |              | at.                               |
+--------------------------+--------------+-----------------------------------+
| STATE_REVERSING          | |bool|       | true if the context is running in |
|                          |              | reverse.                          |
+--------------------------+--------------+-----------------------------------+
| STATE_SIGNAL             | | int|       | Signal number.                    |
+--------------------------+--------------+-----------------------------------+
| STATE_SIGNAL_DESCRIPTION | |basestring| | Signal description.               |
+--------------------------+--------------+-----------------------------------+
| STATE_SIGNAL_NAME        | |basestring| | Signal name.                      |
+--------------------------+--------------+-----------------------------------+

Resume Optional Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^
Some resume modes may need optional parameters. See *params* parameter of the
|resume| command.

All resume optional paramters are of type |int|.

+----------------+------------------------------------------------------------+
| Name           | Description                                                |
+================+============================================================+
| RP_RANGE_END   | Ending address of step range, exclusive.                   |
+----------------+------------------------------------------------------------+
| RP_RANGE_START | Starting address of step range, inclusive.                 |
+----------------+------------------------------------------------------------+

Instruction Set Architecture Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------+--------------+-----------------------------------+
| Name                     | Type         | Description                       |
+==========================+==============+===================================+
| ISA_ADDRESS              | |int|        | The address the Instruction Set   |
|                          |              | Architecture is valid at.         |
+--------------------------+--------------+-----------------------------------+
| ISA_ALIGNMENT            | |int|        | Instruction alignmement for the   |
|                          |              | Instruction Set Architecture.     |
+--------------------------+--------------+-----------------------------------+
| ISA_DEFAULT              | |basestring| | Name of the default ISA.          |
+--------------------------+--------------+-----------------------------------+
| ISA_MAX_INSTRUCTION_SIZE | |int|        | Maximum instruction size for ISA. |
+--------------------------+--------------+-----------------------------------+
| ISA_NAME                 | |basestring| | Name of the ISA.                  |
+--------------------------+--------------+-----------------------------------+
| ISA_SIZE                 | |int|        | Size of the ISA. Another ISA may  |
|                          |              | be defined after                  |
|                          |              | ``ISA_ADDRESS`` + ``ISA_SIZE``    |
+--------------------------+--------------+-----------------------------------+


Service Methods
---------------
.. autodata:: NAME
.. autoclass:: RunControlService

addListener
^^^^^^^^^^^
.. automethod:: RunControlService.addListener

getChildren
^^^^^^^^^^^
.. automethod:: RunControlService.getChildren

getContext
^^^^^^^^^^
.. automethod:: RunControlService.getContext

getName
^^^^^^^
.. automethod:: RunControlService.getName

removeListener
^^^^^^^^^^^^^^
.. automethod:: RunControlService.removeListener

detach
^^^^^^
.. automethod:: RunControlContext.detach

getISA
^^^^^^
.. automethod:: RunControlContext.getISA

getState
^^^^^^^^
.. automethod:: RunControlContext.getState

resume
^^^^^^
.. automethod:: RunControlContext.resume

suspend
^^^^^^^
.. automethod:: RunControlContext.suspend

terminate
^^^^^^^^^
.. automethod:: RunControlContext.terminate

Callback Classes
----------------
DoneCommand
^^^^^^^^^^^
.. autoclass:: DoneCommand
    :members:

DoneGetChildren
^^^^^^^^^^^^^^^
.. autoclass:: DoneGetChildren
    :members:

DoneGetContext
^^^^^^^^^^^^^^
.. autoclass:: DoneGetContext
    :members:

DoneGetISA
^^^^^^^^^^
.. autoclass:: DoneGetISA
    :members:

DoneGetState
^^^^^^^^^^^^
.. autoclass:: DoneGetState
    :members:

Listeners
---------
RunControlListener
^^^^^^^^^^^^^^^^^^
.. autoclass:: RunControlListener
    :members:

Helper Classes
--------------
RunControlContext
^^^^^^^^^^^^^^^^^
.. autoclass:: RunControlContext
    :members:

RunControlError
^^^^^^^^^^^^^^^
.. autoclass:: RunControlError
    :members:
    :show-inheritance:

RunControlISA
^^^^^^^^^^^^^
.. autoclass:: RunControlISA
    :members:
"""

from .. import services

NAME = "RunControl"
"""RunControl service name."""

# Context property names.

PROP_ID = "ID"
PROP_PARENT_ID = "ParentID"
PROP_PROCESS_ID = "ProcessID"
PROP_CREATOR_ID = "CreatorID"
PROP_NAME = "Name"
PROP_IS_CONTAINER = "IsContainer"
PROP_HAS_STATE = "HasState"
PROP_CAN_RESUME = "CanResume"
PROP_CAN_COUNT = "CanCount"
PROP_CAN_SUSPEND = "CanSuspend"
PROP_CAN_TERMINATE = "CanTerminate"
PROP_RC_GROUP = "RCGroup"
PROP_BP_GROUP = "BPGroup"
PROP_CAN_DETACH = "CanDetach"
PROP_SYMBOLS_GROUP = "SymbolsGroup"

# Context resume modes.

RM_RESUME = 0
RM_STEP_OVER = 1
RM_STEP_INTO = 2
RM_STEP_OVER_LINE = 3
RM_STEP_INTO_LINE = 4
RM_STEP_OUT = 5
RM_REVERSE_RESUME = 6
RM_REVERSE_STEP_OVER = 7
RM_REVERSE_STEP_INTO = 8
RM_REVERSE_STEP_OVER_LINE = 9
RM_REVERSE_STEP_INTO_LINE = 10
RM_REVERSE_STEP_OUT = 11
RM_STEP_OVER_RANGE = 12
RM_STEP_INTO_RANGE = 13
RM_REVERSE_STEP_OVER_RANGE = 14
RM_REVERSE_STEP_INTO_RANGE = 15
RM_UNTIL_ACTIVE = 16
RM_REVERSE_UNTIL_ACTIVE = 17

# Suspended reasons

REASON_USER_REQUEST = "Suspended"
REASON_STEP = "Step"
REASON_BREAKPOINT = "Breakpoint"
REASON_EXCEPTION = "Exception"
REASON_CONTAINER = "Container"
REASON_WATCHPOINT = "Watchpoint"
REASON_SIGNAL = "Signal"
REASON_SHAREDLIB = "Shared Library"
REASON_ERROR = "Error"
REASON_ACTIVE = "Active"

# Optional parameters of context state.

STATE_SIGNAL = "Signal"
STATE_SIGNAL_NAME = "SignalName"
STATE_SIGNAL_DESCRIPTION = "SignalDescription"
STATE_BREAKPOINT_IDS = "BPs"
STATE_PC_ERROR = "PCError"
STATE_REVERSING = "Reversing"

# Optional parameters of resume command.

RP_RANGE_START = "RangeStart"
RP_RANGE_END = "RangeEnd"

# Instruction Set Architecture properties

ISA_ADDRESS = "Addr"
ISA_ALIGNMENT = "Alignment"
ISA_DEFAULT = "DefISA"
ISA_MAX_INSTRUCTION_SIZE = "MaxInstrSize"
ISA_NAME = "ISA"
ISA_SIZE = "Size"


class RunControlService(services.Service):
    """RunControl service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def getContext(self, contextID, done):
        """Retrieve context properties for given context ID.

        :param contextID: ID of the context to retrieve.
        :type contextID: |basestring|
        :param done: Callback interface called when operation is completed.
        :type done: |DoneGetContext|

        :returns: Pending command handle.
        """
        raise NotImplementedError("Abstract method")

    def getChildren(self, parent_context_id, done):
        """Retrieve children of given context.

        :param parent_context_id: parent context ID. Can be **None** - to
                                  retrieve top level of the hierarchy, or one
                                  of context IDs retrieved by previous
                                  |getChildren| commands.
        :type parent_context_id: |basestring| or **None**
        :param done: Callback interface called when operation is completed.
        :type done: |DoneGetChildren|

        :returns: Pending command handle.
        """
        raise NotImplementedError("Abstract method")

    def addListener(self, listener):
        """Add run control event listener.

        :param listener: RunControl event listener to add.
        :type listener: |RunControlListener|

        :returns: **None**, always.
        """
        raise NotImplementedError("Abstract method")

    def removeListener(self, listener):
        """Remove run control event listener.

        :param listener: run control event listener to remove.
        :type listener: |RunControlListener|
        """
        raise NotImplementedError("Abstract method")


class RunControlError(Exception):
    """RunControl error class interface."""
    pass


class RunControlISA(object):
    """Instruction Set Architecture.

    :param props: The properties to initialise object with. See
                  `Instruction Set Architecture Properties`_.
    :type props: |dict|
    """
    def __init__(self, props):
        self._properties = props or {}

    def __repr__(self):
        return self.__class__.__name__ + '(' + str(self.getProperties()) + ')'

    def __str__(self):
        res = self.__class__.__name__ + ' ['
        res += 'Name=' + str(self.getName()) + ', '
        res += 'Address=' + str(self.getAddress()) + ', '
        res += ISA_SIZE + '=' + str(self.getSize()) + ', '
        res += ISA_ALIGNMENT + '=' + str(self.getAlignment()) + ', '
        res += ISA_MAX_INSTRUCTION_SIZE + '='
        res += str(self.getMaxInstructionSize()) + ', '
        res += 'Default=' + str(self.getDefault())
        res += ']'
        return res

    def getAddress(self):
        """Get the address this ISA is defined at.

        :returns: An |int| representing the address at which this ISA is
                  defined, or **0** if it is not known.
        """
        return self._properties.get(ISA_ADDRESS, 0)

    def getAlignment(self):
        """Get the address alignment for this ISA.

        :returns: An |int| representing the address alignment for this ISA, or
                  **0** if it is not known.
        """
        return self._properties.get(ISA_ALIGNMENT, 0)

    def getDefault(self):
        """Get the default name of this ISA.

        :returns: A |basestring| representing the default name of this ISA,
                  or **None** if it is not known.
        """
        return self._properties.get(ISA_DEFAULT, None)

    def getMaxInstructionSize(self):
        """Get the maximum size of an instruction for this ISA.

        :returns: An |int| representing the maximum instruction size for this
                  ISA, or **0** if it is not known.
        """
        return self._properties.get(ISA_MAX_INSTRUCTION_SIZE, 0)

    def getName(self):
        """Get the name of this ISA.

        :returns: A |basestring| representing the name of this ISA, or **None**
                  if it is not known.
        """
        return self._properties.get(ISA_NAME, None)

    def getProperties(self):
        """Get the properties defining this ISA.

        :returns: A |dict| representing all the defined properties for this
                  ISA.
        """
        return self._properties

    def getSize(self):
        """Get the size of this ISA.

        Starting from |getAddress|, this ISA is valid only for |getSize| bytes.
        Another |getISA| request should be performed for further addresses.

        :returns: An |int| representing the size for this ISA, or **0** if it
                  is not known.
        """
        return self._properties.get(ISA_MAX_INSTRUCTION_SIZE, 0)


class DoneGetISA(object):
    """Client call back interface for |getISA|."""
    def doneGetISA(self, token, error, isa):
        """Called when |getISA| command execution is complete.

        :param token: Pending command handle.
        :param error: Command execution error or **None**.
        :param isa: A |RunControlISA| object result of the request.
        :type isa: |RunControlISA|
        """
        pass


class DoneGetState(object):
    """Client call back interface for |getState|."""
    def doneGetState(self, token, error, suspended, pc, reason, params):
        """Called when |getState| command execution is complete.

        :param token: Pending command handle.
        :param error: Pommand execution error or **None**.
        :param suspended: **True** if the context is suspended.
        :type suspended: |bool|
        :param pc: Program counter of the context (if suspended).
        :type pc: |int|
        :param reason: Suspend reason (if suspended), see `State Reasons`_.
        :type reason: |basestring|
        :param params: Additional target specific data about context state,
                       see `State Optional Parameters`_.
        :type params: |dict|
        """
        pass


class DoneCommand():
    """Client call back interface for |detach|, |resume|, |suspend| and
    |terminate|."""

    def doneCommand(self, token, error):
        """Called when run control command execution is complete.

        :param token: Pending command handle.
        :param error: Command execution error or **None**.
        """
        pass


class DoneGetContext():
    "Client callback interface for |getContext|."

    def doneGetContext(self, token, error, context):
        """Called when context data retrieval is done.

        :param token: Pending command handle.
        :param error: Error description if operation failed, **None** if
                      succeeded.
        :param context: Context data.
        :type context: |RunControlContext|
        """
        pass


class DoneGetChildren(object):
    """Client callback interface for |getChildren|."""

    def doneGetChildren(self, token, error, context_ids):
        """Called when context list retrieval is done.

        :param token: Pending command handle.
        :param error: Error description if operation failed, **None** if
                      succeeded.
        :param context_ids: array of available context IDs.
        :type context_ids: |list|
        """
        pass


class RunControlContext(object):
    """A context corresponds to an execution thread, process, address space,
    etc.

    A context can belong to a parent context. Contexts hierarchy can be simple
    plain list or it can form a tree. It is up to target agent developers to
    choose layout that is most descriptive for a given target. Context IDs are
    valid across all services. In other words, all services access same
    hierarchy of contexts, with same IDs, however, each service accesses its
    own subset of context's attributes and functionality, which is relevant to
    that service.

    :param props: a `dict` of properties to initialise this RunControl context
                  with. See all the `RunControl Context Properties`_ constants.
    """
    def __init__(self, props):
        self._props = props or {}

    def __str__(self):
        return "[Run Control Context %s]" % self._props

    def getProperties(self):
        """Get context properties.

        See `RunControl Context Properties`_ definitions for property names.

        Context properties are read only, clients should not try to modify
        them.

        :returns: A |dict| of context properties.
        """
        return self._props

    def getID(self):
        """Retrieve context ID.

        :returns: A |basestring| representing this RunControl context ID.
        """
        return self._props.get(PROP_ID)

    def getParentID(self):
        """Retrieve parent context ID.

        :returns: A |basestring| representing this RunControl parent context
                  ID or **None**.
        """
        return self._props.get(PROP_PARENT_ID)

    def getProcessID(self):
        """Retrieve context process ID.

        :returns: A |basestring| representing this RunControl process ID. This
                  value is also meant to be the ID of the |MemoryContext|
                  this RunControl context belongs to.
        """
        return self._props.get(PROP_PROCESS_ID)

    def getCreatorID(self):
        """Retrieve context creator ID.

        :returns: A |basestring| representing this RunControl creator context
                  ID or **None**.
        """
        return self._props.get(PROP_CREATOR_ID)

    def getName(self):
        """Retrieve human readable context name.

        :returns: A |basestring| representing this RunControl context name or
                  **None**
        """
        return self._props.get(PROP_NAME)

    def isContainer(self):
        """Check if this context is a RunControl Context container.

        Executing resume or suspend command on a container causes all its
        children to resume or suspend.

        :returns: A |bool| stating if this context is a container or not.
        """
        return self._props.get(PROP_IS_CONTAINER)

    def hasState(self):
        """Check if this context has a state.

        Only context that has a state can be resumed or suspended.

        :returns: A |bool| stating if this context has a state or not.
        """
        return self._props.get(PROP_HAS_STATE)

    def canSuspend(self):
        """Check if this context can be suspended.

        Value **True** means suspend command is supported by the context,
        however the method does not check that the command can be executed
        successfully in the current state of the context. For example, the
        command still can fail if context is already suspended.

        :return: A |bool| stating if this context can be suspended or not.
        """
        return self._props.get(PROP_CAN_SUSPEND)

    def canResume(self, mode):
        """Check if this context can resume with given *mode*.

        Value **True** means resume command is supported by the context,
        however the method does not check that the command can be executed
        successfully in the current state of the context. For example, the
        command still can fail if context is already resumed.

        :param mode: Resume mode. See `Resume Modes`_.
        :type mode: |int|

        :returns: A |bool| stating if this context can resume with given
                  *mode*.
        """
        b = self._props.get(PROP_CAN_RESUME) or 0
        return (b & (1 << mode)) != 0

    def canCount(self, mode):
        """Check if context can count resumes of given *mode*.

        Value **True** means resume command with count other than 1 is
        supported by the context, however the method does not check that the
        command can be executed successfully in the current state of the
        context. For example, the command still can fail if context is already
        resumed.

        :param mode: Resume mode. See `Resume Modes`_.
        :type mode: |int|

        :returns: A |bool| stating if this context can count resumes on given
                  *mode*.
        """
        b = self._props.get(PROP_CAN_COUNT) or 0
        return (b & (1 << mode)) != 0

    def canTerminate(self):
        """Check if context can be terminated.

        Value **True** means terminate command is supported by the context,
        however the method does not check that the command can be executed
        successfully in the current state of the context. For example, the
        command still can fail if context is already exited.

        :returns: A |bool| stating if this context can be terminated.
        """
        return self._props.get(PROP_CAN_TERMINATE)

    def getRCGroup(self):
        """Get the context RunControl Group ID.

        The RunContol Group ID is the context ID of a run control group that
        contains the context.

        Members of same group are always suspended and resumed together:
        resuming/suspending a context resumes/suspends all members of the
        group.

        :returns: A |basestring| representing this context RC group or
                  **None**.
        """
        return self._props.get(PROP_RC_GROUP)

    def getBPGroup(self):
        """Get this context Breakpoints group ID.

        The Breakpoints group ID is the context ID of a breakpoints group that
        contains the context.

        Members of same group share same breakpoint instances: a breakpoint is
        planted once for the group, no need to plant the breakpoint for each
        member of the group

        :returns: A |basestring| representing this context Breakpoints group
                  ID, or **None** if the context does not support breakpoints.
        """
        return self._props.get(PROP_BP_GROUP)

    def getSymbolsGroup(self):
        """Get this context Symbols group ID.

        The Symbols group ID is the context ID of a symbols group that contains
        the context.

        Members of a symbols group share same symbol reader configuration
        settings, like user defined memory map entries and source lookup info.

        :returns: A |basestring| representing this context Symbols group ID, or
                  **None** if the context is not a member of a symbols group.
        """
        return self._props.get(PROP_SYMBOLS_GROUP)

    def canDetach(self):
        """Check if this context can be detached.

        Value **True** means detach command is supported by the context,
        however the method does not check that the command can be executed
        successfully in the current state of the context. For example, the
        command still can fail if the context already has exited.

        :returns: A |bool| stating if this context can be detached or not.
        """
        return self._props.get(PROP_CAN_DETACH)

    def detach(self, done):
        """Send a command to detach a context.

        :param done: Command result call back object
        :type done: |DoneCommand|

        :returns: Pending command handle, can be used to cancel the command.
        """
        raise NotImplementedError("Abstract method")

    def getISA(self, address, done):
        """Send a command to retrieve current Instruction Set Architecture of a
        context.

        :param address: The memory address to get ISA for.
        :type address: |int|
        :param done: Command result call back object.
        :type done: |DoneGetISA|

        :returns: Pending command handle, can be used to cancel the command.
        """
        raise NotImplementedError("Abstract method")

    def getState(self, done):
        """Send a command to retrieve current state of a context.

        :param done: Command result call back object.
        :type done: |DoneGetState|

        :returns: Pending command handle, can be used to cancel the command.
        """
        raise NotImplementedError("Abstract method")

    def suspend(self, done):
        """Send a command to suspend a context.

        Also suspends children if context is a container.

        :param done: Command result call back object.
        :type done: |DoneCommand|

        :returns: Pending command handle, can be used to cancel the command.
        """
        raise NotImplementedError("Abstract method")

    def resume(self, mode, count, params, done):
        """Send a command to resume a context.

        Also resumes children if context is a container.

        :param mode: Defines how to resume the context. See `Resume Modes`.
        :type mode: |int|
        :param count: If mode implies stepping, defines how many steps to
                      perform.
        :type count: |int|
        :param params: Resume parameters, for example, step range definition,
                       see `Resume Optional Parameters`_.
        :type params: |dict|
        :param done: command result call back object
        :type done: |DoneCommand|

        :returns: Pending command handle, can be used to cancel the command.
        """
        raise NotImplementedError("Abstract method")

    def terminate(self, done):
        """Send a command to terminate a context.

        :param done: Command result call back object.
        :type done: |DoneCommand|

        :returns: Pending command handle, can be used to cancel the command.
        """
        raise NotImplementedError("Abstract method")


class RunControlListener(object):
    """RunControl service events listener interface."""

    def contextAdded(self, contexts):
        """Called when new contexts are created.

        :param contexts: List of new context properties. A |RunControlContext|
                         can be initialised with those |dict| properties.
        :type contexts: |list| of |dict|
        """
        pass

    def contextChanged(self, contexts):
        """Called when a context properties changed.

        :param contexts: List of new context properties. A `RunControlContext`
                         can be initialised with those |dict| properties.
        :type contexts: |list| of |dict|
        """
        pass

    def contextRemoved(self, context_ids):
        """Called when contexts are removed.

        :param context_ids: List of removed context IDs.
        :type context_ids: |list|
        """
        pass

    def contextStateChanged(self, context):
        """Called when context state changes and the context is not and was not
        in suspended state.

        Changes to and from suspended state should be reported by other events:
        contextSuspended, contextResumed, containerSuspended, containerResumed.

        :param context: ID of a context that changed state.
        :type context: |basestring|
        """
        pass

    def contextSuspended(self, context, pc, reason, params):
        """Called when a thread is suspended.

        :param context: ID of a context that was suspended.
        :type context: |basestring|
        :param pc: Program counter of the context.
        :type pc: |int| or **None**
        :param reason: Human readable description of suspend reason. See
                       `State Reasons`_.
        :type reason: |basestring|
        :param params: Additional, target specific data about suspended
                       context. See `State Optional Parameters`_.
        :type params: |dict|
        """
        pass

    def contextResumed(self, context):
        """Called when a thread is resumed.

        :param context: ID of a context that was resumed.
        :type context: |basestring|
        """
        pass

    def containerSuspended(self, context, pc, reason, params, suspended_ids):
        """Called when target simultaneously suspends multiple threads in a
        container (process, core, etc.).

        :param context: ID of a context responsible for the event. It can be
                        container ID or any one of container children, for
                        example, it can be thread that hit "suspend all"
                        breakpoint. Client expected to move focus (selection)
                        to this context.
        :type context: |basestring|
        :param pc: program counter of the context.
        :type pc: |int|
        :param reason: Suspend reason, see `State Reasons`_.
        :type reason: |basestring|
        :param params: Additional target specific data about context state,
                       see `State Reasons`_.
        :type params: |dict|
        :param suspended_ids: full list of all contexts that were suspended.
        :type suspended_ids: |list|
        """
        pass

    def containerResumed(self, context_ids):
        """Called when target simultaneously resumes multiple threads in a
        container (process, core, etc.).

        :param context_ids: Full list of all contexts that were resumed.
        :type context_ids: |list|
        """
        pass

    def contextException(self, context, msg):
        """Called when an exception is detected in a target thread.

        :param context: ID of a context that caused an exception.
        :type context: |basestring|
        :param msg: Human readable description of the exception.
        :type msg: |basestring|
        """
        pass
