# *****************************************************************************
# * Copyright (c) 2011, 2013-2014 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""Memory service provides basic operations to read/write memory on a target.
.. |fill| replace:: :meth:`~MemoryContext.fill`
.. |get| replace:: :meth:`~MemoryContext.get`
.. |getChildren| replace:: :meth:`~MemoryService.getChildren`
.. |getContext| replace:: :meth:`~MemoryService.getContext`
.. |getMessage| replace:: :meth:`~MemoryError.getMessage`
.. |processes| replace:: :mod:`~tcf.services.processes`
.. |set| replace:: :meth:`~MemoryContext.set`
.. |DoneGetChildren| replace:: :class:`DoneGetChildren`
.. |DoneGetContext| replace:: :class:`DoneGetContext`
.. |DoneMemory| replace:: :class:`DoneMemory`
.. |MemoryContext| replace:: :class:`MemoryContext`
.. |MemoryError| replace:: :class:`MemoryError`
.. |MemoryListener| replace:: :class:`MemoryListener`
Memory Properties
-----------------
.. _Tcf-Memory-Properties:
Properties
^^^^^^^^^^
+-------------------+--------------+------------------------------------------+
| Name              | Type         | Description                              |
+===================+==============+==========================================+
| PROP_ACCESS_TYPES | |list|       | The access types allowed for this        |
|                   |              | context. Target system can support       |
|                   |              | multiple different memory access types,  |
|                   |              | like instruction and data access.        |
|                   |              | Different access types can use different |
|                   |              | logic for address translation and memory |
|                   |              | mapping, so they can end up accessing    |
|                   |              | different data bits, even if address is  |
|                   |              | the same. Each distinct access type      |
|                   |              | should be represented by separate memory |
|                   |              | context. A memory context can represent  |
|                   |              | multiple access types if they are        |
|                   |              | equivalent - all access same memory bits.|
|                   |              | Same data bits can be exposed through    |
|                   |              | multiple memory contexts.                |
|                   |              | See `Access types`_.                     |
+-------------------+--------------+------------------------------------------+
| PROP_ADDRESS_SIZE | |int|        | Size of memory address in bytes.         |
+-------------------+--------------+------------------------------------------+
| PROP_BIG_ENDIAN   | |bool|       | **True** if memory is big-endian.        |
+-------------------+--------------+------------------------------------------+
| PROP_END_BOUND    | |int|        | Highest address (inclusive) which is     |
|                   |              | valid for the context.                   |
+-------------------+--------------+------------------------------------------+
| PROP_ID           | |basestring| | ID of the context.                       |
+-------------------+--------------+------------------------------------------+
| PROP_NAME         | |basestring| | Name of the context, can be used for UI  |
|                   |              | purposes.                                |
+-------------------+--------------+------------------------------------------+
| PROP_PARENT_ID    | |basestring| | ID of a parent context.                  |
+-------------------+--------------+------------------------------------------+
| PROP_PROCESS_ID   | |basestring| | Process ID, see |processes| service.     |
+-------------------+--------------+------------------------------------------+
| PROP_START_BOUND  | |int|        | Lowest address (inclusive) which is      |
|                   |              | valid for the context.                   |
+-------------------+--------------+------------------------------------------+
.. _Tcf-Memory-Access-Types:
Access Types
^^^^^^^^^^^^
All access types are of type |basestring|.
+--------------------+--------------------------------------------------------+
| Name               | Description                                            |
+====================+========================================================+
| ACCESS_CACHE       | Context is a cache.                                    |
+--------------------+--------------------------------------------------------+
| ACCESS_DATA        | Context represents data access.                        |
+--------------------+--------------------------------------------------------+
| ACCESS_HYPERVISOR  | Context represents a hypervisor view to memory.        |
+--------------------+--------------------------------------------------------+
| ACCESS_INSTRUCTION | Context represent instructions fetch access.           |
+--------------------+--------------------------------------------------------+
| ACCESS_IO          | Context represents IO peripherals.                     |
+--------------------+--------------------------------------------------------+
| ACCESS_PHYSICAL    | Context uses physical addresses.                       |
+--------------------+--------------------------------------------------------+
| ACCESS_SUPERVISOR  | Context represents a supervisor (e.g. Linux kernel)    |
|                    | view to memory.                                        |
+--------------------+--------------------------------------------------------+
| ACCESS_TLB         | Context is a TLB memory.                               |
+--------------------+--------------------------------------------------------+
| ACCESS_USER        | Context represents a user (e.g. application running    |
|                    | in Linux) view to memory.                              |
+--------------------+--------------------------------------------------------+
| ACCESS_VIRTUAL     | Context uses virtual addresses.                        |
+--------------------+--------------------------------------------------------+
.. _Tcf-Memory-Command-Modes:
Command Modes
^^^^^^^^^^^^^
All command modes are of type |int|. For the |get|, |fill| or |set| methods,
the possible modes are:
+----------------------+------------------------------------------------------+
| Name                 | Description                                          |
+======================+======================================================+
| MODE_CONTINUEONERROR | Carry on when some of the memory cannot be accessed  |
|                      | and return |MemoryError| at the end if any of the    |
|                      | bytes were not processed correctly.                  |
+----------------------+------------------------------------------------------+
| MODE_VERIFY          | Verify result of memory operations (by reading and   |
|                      | comparing).                                          |
+----------------------+------------------------------------------------------+
Service Methods
---------------
.. autodata:: NAME
.. autoclass:: MemoryService
addListener
^^^^^^^^^^^
.. automethod:: MemoryService.addListener
fill
^^^^
.. automethod:: MemoryContext.fill
get
^^^
.. automethod:: MemoryContext.get
getChildren
^^^^^^^^^^^
.. automethod:: MemoryService.getChildren
getContext
^^^^^^^^^^
.. automethod:: MemoryService.getContext
getName
^^^^^^^
.. automethod:: MemoryService.getName
removeListener
^^^^^^^^^^^^^^
.. automethod:: MemoryService.removeListener
set
^^^
.. automethod:: MemoryContext.set
Callback Classes
----------------
DoneGetChildren
^^^^^^^^^^^^^^^
.. autoclass:: DoneGetChildren
    :members:
DoneGetContext
^^^^^^^^^^^^^^
.. autoclass:: DoneGetContext
    :members:
DoneMemory
^^^^^^^^^^
.. autoclass:: DoneMemory
    :members:
Listener
--------
MemoryListener
^^^^^^^^^^^^^^
.. autoclass:: MemoryListener
    :members:
Helper classes
--------------
ErrorOffset
^^^^^^^^^^^
.. autoclass:: ErrorOffset
    :members:
MemoryContext
^^^^^^^^^^^^^
.. autoclass:: MemoryContext
    :members:
MemoryError
^^^^^^^^^^^
.. autoclass:: MemoryError
    :members:
"""

from .. import services

NAME = "Memory"
"""Memory service name."""

# Context property names.

PROP_ID = "ID"
PROP_PARENT_ID = "ParentID"
PROP_PROCESS_ID = "ProcessID"
PROP_BIG_ENDIAN = "BigEndian"
PROP_ADDRESS_SIZE = "AddressSize"
PROP_NAME = "Name"
PROP_START_BOUND = "StartBound"
PROP_END_BOUND = "EndBound"
PROP_ACCESS_TYPES = "AccessTypes"

ACCESS_INSTRUCTION = "instruction"
ACCESS_DATA = "data"
ACCESS_IO = "io"
ACCESS_USER = "user"
ACCESS_SUPERVISOR = "supervisor"
ACCESS_HYPERVISOR = "hypervisor"
ACCESS_VIRTUAL = "virtual"
ACCESS_PHYSICAL = "physical"
ACCESS_CACHE = "cache"
ACCESS_TLB = "tlb"

MODE_CONTINUEONERROR = 0x1
MODE_VERIFY = 0x2
MODE_BYPASS_ADDR_CHECK = 0x4
MODE_BYPASS_CACHE_SYNC = 0x8


class MemoryContext(object):
    """Memory context class.
    :param props: Properties to initialise this memory context with. See
                  `Properties`_.
    :type props: |dict|
    """

    def __init__(self, props):
        self._props = props or {}

    def __str__(self):
        return "[Memory Context %s]" % self._props

    def getProperties(self):
        """Get context properties. See `Properties`_ definitions for property
        names.
        Context properties are read only, clients should not try to modify
        them.
        :returns: A |dict| of context properties.
        """
        return self._props

    def getID(self):
        """Retrieve context ID.
        :returns: A |basestring| representing this memory context ID or
                  **None**.
        """
        return self._props.get(PROP_ID)

    def getParentID(self):
        """Retrieve parent context ID.
        :returns: A |basestring| representing this memory context parent ID or
                  **None**.
        """
        return self._props.get(PROP_PARENT_ID)

    def getProcessID(self):
        """Retrieve context process ID.
        :returns: A |basestring| representing this memory context process ID or
                  **None**.
        """
        return self._props.get(PROP_PROCESS_ID)

    def isBigEndian(self):
        """Get memory endianness.
        :returns: A |bool| stating if memory is big-endian.
        """
        return self._props.get(PROP_BIG_ENDIAN, False)

    def getAddressSize(self):
        """Get memory address size.
        :returns: An |int| representing the number of bytes used to store
                  memory address value.
        """
        return self._props.get(PROP_ADDRESS_SIZE, 0)

    def getName(self):
        """Get memory context name.
        The name can be used for UI purposes.
        :returns: A |basestring| representing this context name or **None**.
        """
        return self._props.get(PROP_NAME)

    def getStartBound(self):
        """Get lowest address (inclusive) which is valid for the context.
        :returns: An |int| representing the lowest address or **None**.
        """
        return self._props.get(PROP_START_BOUND)

    def getEndBound(self):
        """Get highest address (inclusive) which is valid for the context.
        :returns: An |int| representing the highest address or **None**.
        """
        return self._props.get(PROP_END_BOUND)

    def getAccessTypes(self):
        """Get the access types allowed for this context.
        :returns: A |dict| of access type names or **None**. See
                 `Access Types`_.
        """
        return self._props.get(PROP_ACCESS_TYPES)

    def set(self, addr, ws, buf, offs, sz, mode, done):  # @ReservedAssignment
        """Set target memory.
        If *ws* is 0 it means client does not care about word size.
        :param addr: Address to set for this memory context.
        :type addr: |int|
        :param ws: Word size (alignement) to use for setting memory.
        :type ws: |int|
        :param buf: Data to be written in memory.
        :type buf: |bytearray|
        :param offs: Offset to seek in *buf*.
        :type offs: |int|
        :param sz: Number of bytes to write in memory.
        :type sz: |int|
        :param mode: Memory write mode. See `Command Modes`_.
        :type mode: |int|
        :returns: pending command handle.
        """
        raise NotImplementedError("Abstract method")

    def get(self, addr, word_size, buf, offs, size, mode, done):
        """Read target memory.
        :param addr: Address to get from this memory context.
        :type addr: |int|
        :param ws: word size (alignement) to use for getting memory.
        :type ws: |int|
        :param buf: read data buffer.
        :type buf: |bytearray|
        :param offs: Offset to seek in *buf* to write retrieved data.
        :type offs: |int|
        :param sz: Number of bytes to read in memory.
        :type sz: |int|
        :param mode: Memory read mode. See `Command Modes`_.
        :type mode: |int|
        :returns: pending command handle.
        """
        raise NotImplementedError("Abstract method")

    def fill(self, addr, word_size, value, size, mode, done):
        """Fill target memory with given pattern.
        :param addr: Address to get from this memory context.
        :type addr: |int|
        :param word_size: Word size (alignement) to use for filling memory.
        :type word_size: |int|
        :param buf: Data to be fill memory with.
        :type buf: |bytearray|
        :param offs: Offset to seek in *buf*.
        :type offs: |int|
        :param sz: Number of bytes to write in memory.
        :type sz: |int|
        :param mode: Memory write mode. See `Command Modes`_.
        :type mode: |int|
        :returns: pending command handle.
        """
        raise NotImplementedError("Abstract method")


class DoneMemory(object):
    """Client call back interface for |fill|, |get| and |set| commands."""

    def doneMemory(self, token, error):
        """Called when memory operation command command is done.
        :param token: Command handle.
        :param error: Error object or **None**.
        """
        pass


class MemoryError(Exception):  # @ReservedAssignment
    """Memory errors class.
    Empty class implementing the |Exception| class.
    """
    pass


class ErrorOffset(object):
    """Error offset may be implemented by |MemoryError| object, which is
    returned by |get|, |set| and |fill| commands.
    The command |get|, |set| and |fill| return this exception when memory
    operation failed for some but not all bytes, and **MODE_CONTINUEONERROR**
    has been set in *mode*. (For example, when only part of the request
    translates to valid memory addresses.)
    Method |getMessage| can be used for generalized message of the possible
    reasons of partial memory operation.
    """
    # Error may have per byte information
    BYTE_VALID = 0x00
    BYTE_UNKNOWN = 0x01  # e.g. out of range
    BYTE_INVALID = 0x02
    BYTE_CANNOT_READ = 0x04
    BYTE_CANNOT_WRITE = 0x08

    RANGE_KEY_ADDR = "addr"
    RANGE_KEY_SIZE = "size"
    RANGE_KEY_STAT = "stat"
    RANGE_KEY_MSG = "msg"

    def getStatus(self, offset):
        """Get the error status.
        :param offset: offset to get error status for
        :type offset: |int|
        :returns: The error status for the error which happened at given
                  *offset*.
        """
        raise NotImplementedError("Abstract method")

    def getMessage(self, offset):
        """Get the error message.
        :param offset: Offset to get error message for.
        :type offset: |int|
        :returns: The error message for the error which happened at given
                  *offset*.
        """
        raise NotImplementedError("Abstract method")


class MemoryService(services.Service):
    """TCF memory service interface."""

    def getName(self):
        """Get this service name.
        :returns: The value of string :const:`NAME`
        """
        return NAME

    def getContext(self, contextID, done):
        """Retrieve context info for given context ID.
        :param contextID: ID of the memory context to get.
        :type contextID: |basestring|
        :param done: Call back interface called when operation is completed.
        :type done: |DoneGetContext|
        :returns: Pending command handle.
        """
        raise NotImplementedError("Abstract method")

    def getChildren(self, parent_context_id, done):
        """Retrieve contexts available for memory commands.
        A context corresponds to an execution thread, process, address space,
        etc.
        A context can belong to a parent context. Contexts hierarchy can be
        simple plain list or it can form a tree. It is up to target agent
        developers to choose layout that is most descriptive for a given
        target. Context IDs are valid across all services. In other words, all
        services access same hierarchy of contexts, with same IDs, however,
        each service accesses its own subset of context's attributes and
        functionality, which is relevant to that service.
        :param parent_context_id: parent context ID. Can be **None** - to
                                  retrieve top level of the hierarchy, or one
                                  of context IDs retrieved by previous
                                  |getChildren| commands.
        :type parent_context_id: |basestring|
        :param done: call back interface called when operation is completed.
        :type done: |DoneGetContext|
        :returns: Pending command handle.
        """
        raise NotImplementedError("Abstract method")

    def addListener(self, listener):
        """Add memory service event listener.
        :param listener: Event listener implementation.
        :type listener: |MemoryListener|
        """
        raise NotImplementedError("Abstract method")

    def removeListener(self, listener):
        """Remove memory service event listener.
        :param listener: Event listener implementation.
        :type listener: |MemoryListener|
        """
        raise NotImplementedError("Abstract method")


class MemoryListener(object):
    """Memory event listener is notified when memory context hierarchy changes,
    and when memory is modified by memory service commands.
    """

    def contextAdded(self, contexts):
        """Called when a new memory access context(s) is created.
        :param contexts: A list of |MemoryContext| properties which have been
                         added to memory space.
        :type contexts: |list|
        """
        pass

    def contextChanged(self, contexts):
        """Called when a memory access context(s) properties changed.
        :param contexts: A list of |MemoryContext| properties which have been
                         changed in memory space.
        :type contexts: |list|
        """
        pass

    def contextRemoved(self, context_ids):
        """Called when memory access context(s) is removed.
        :param context_ids: A list of the IDs of memory contexts which have
                            been removed from memory space.
        :type context_ids: |list|
        """
        pass

    def memoryChanged(self, context_id, addr, size):
        """Called when target memory content was changed and clients need to
        update themselves.
        Clients, at least, should invalidate corresponding cached memory data.
        .. note:: Not every change is notified - it is not possible, only
                  those, which are not caused by normal execution of the
                  debuggee.
        :param context_id: ID of the changed memory context.
        :type context_id: |basestring|
        :param addr: Address at which memory has been changed. A value of
                     **None** means that this address is unknown.
        :type addr: |int|
        :param size: Size of the changed memory. A value of **None** means that
                     this size is unknown.
        :type size: |int| or **None**
        """
        pass


class DoneGetContext(object):
    """Client call back interface for |getContext|."""

    def doneGetContext(self, token, error, context):
        """Called when memory context retrieval is done.
        :param token: Command handle.
        :param error: Error description if operation failed, **None** if
                      succeeded.
        :param context: The so retrieved memory context description.
        :type context: |MemoryContext|
        """
        pass


class DoneGetChildren(object):
    """Client call back interface for |getChildren|."""

    def doneGetChildren(self, token, error, context_ids):
        """Called when memory IDs retrieval is done.
        :param token: Command handle.
        :param error: Error description if operation failed, **None** if
                      succeeded.
        :param context_ids: A list of available context IDs.
        :type context_ids: |list|
        """
        pass
