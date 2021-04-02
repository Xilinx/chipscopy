# *****************************************************************************
# * Copyright (c) 2013-2014, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial implementation
# *****************************************************************************

import atexit
import threading
import os.path
import sys
import time

import tcf as tcf  # @UnresolvedImport
import tcf.protocol as protocol  # @UnresolvedImport

import tcf.services.processes as processes  # @UnresolvedImport
import tcf.services.processes_v1 as processes_v1  # @UnresolvedImport
import tcf.services.runcontrol as runcontrol  # @UnresolvedImport
import tcf.services.streams as streams  # @UnresolvedImport


class TcfProtocolLogger (object):
    """A class to override TCF protocol's default logger.

    As we do not want TCF errors to be logged on the console, this logger
    simply does nothing on TCF protocol log messages.
    """

    def log(self, msg, x):
        """Logs the given message.

        :param msg: log entry text.
        :param x: an exception associated with the log entry or **None**.
        """
        pass

    def __del__(self):
        """Sometimes we get some protocol warnings. I would like to remove them
        by flushing the log cache here.
        """
        pass


class TcfValue(object):
    """TCF value container.

    A simple class to handle the value returned by an asynchronous TCF request.

    :param value: A value to initialise this TCF value class with.
    """
    def __init__(self, value=None):
        self._value = value

    def getValue(self):
        """Get this TCF stored value.

        If this TCF value has been set using the set() method, or at object
        creation time, the so-set value is returned. Else, **None** is
        returned.

        :returns: This TCF stored value, or **None**.
        """
        return (self._value)

    def setValue(self, value):
        """Set this TCF value.

        :param value: TCF value to set.

        :returns: **None**, always.
        """
        self._value = value


class StreamsListener(streams.StreamsListener):
    """A TCF streams service listener.

    :param service: streams service to listen to.
    """
    def __init__(self, service):
        self._service = service

    def created(self, streamType, streamID, contextID):
        """Called when a new stream is created.

        :param streamType: source type of the stream.
        :param streamID: ID of the stream.
        :param contextID: a context ID that is associated with the stream,
                          or **None**. Exact meaning of the context ID depends
                          on stream type. Stream types and context IDs are
                          defined by services that use Streams service to
                          transmit data.
        """
        class DoneRead(streams.DoneRead):
            """Call back interface for StreamsService.read() command.

            :param service: The streams service to read data from.
            :param streamID: The stream ID to read data from.
            :param size: Size of data to read on stream.
            """
            def __init__(self, service, streamID, size):
                self._service = service
                self._streamID = streamID
                self._size = size

            def doneRead(self, token, error, lost_size, data, eos):
                """Called when StreamsService.read() command is done.

                :param token: command handle.
                :param error: error object or **None**.
                :param lost_size: number of bytes that were lost because of
                                  buffer overflow. A *lost_size* of **-1**
                                  means unknown number of bytes were lost. If
                                  both *lost_size* and *data.length* are
                                  non-zero then lost bytes are considered
                                  located right before read bytes.
                :param data: bytes read from the stream.
                :param eos: true if end of stream was reached.
                """
                if data:
                    if isinstance(data, bytearray):
                        s = data.decode('utf-8')
                    else:
                        s = str(data)
                    sys.stdout.write(s)
                if not eos:
                    self._service.read(self._streamID, self._size, self)

        self._service.read(streamID, 4096, DoneRead(self._service, streamID,
                                                    4096))

    def disposed(self, streamType, streamID):
        """Called when a stream is disposed.

        :param streamType: source type of the stream.
        :param streamID: ID of the stream.
        """
        pass


def getService(connection, name):
    """Get a service proxy.

    The service proxy named *name* is retrieved from *connection*. If it
    exists (returned value is not **None**), it is then possible to send it
    TCF requests.

    :param connection: The connection to get service proxy from.
    :param name: The name of the service proxy to get from *connection*.

    :returns: A service proxy or **None**.
    """
    def callGetService(connection, condition, val):
        """Asynchronous request to get service proxy.

        :param connection: The connection to get service proxy from.
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.
        :param val: A TcfValue handling the request returned value.

        :returns: **None**, always.
        """
        svc = connection.getRemoteService(name)
        val.setValue(svc)
        with condition:
            condition.notify()

    # create a condition to wait on, and a value to get the service proxy

    lock = threading.Condition()
    value = TcfValue()

    with lock:
        # Asynchronously call for the callGetService function.
        protocol.invokeLater(callGetService, connection=connection,
                             condition=lock, val=value)
        lock.wait(5)

    # Return TCF service proxy. May be None on timeout or missing service.

    return (value.getValue())


def getChildren(service, contextID=None):
    """Get a TCF context IDs from a given service.

    As many TCF services have a **getChildren()** command, this function is
    intended to implement a service-independant **getChildren()** command.

    :param service: The TCF service to get context list from.
    :param contextID: parent ID of the context list to get from *service*.

    :returns: A tuple of context IDs. Tuple may be empty on error, or if
              *contextID* does not have children.
    """
    def callGetChildren(service, condition, val):
        """Asynchronous request to get context children.

        :param service: The TCF service proxy to send request to.
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.
        :param val: A TcfValue handling the request returned value.

        :returns: **None**, always.
        """
        class DoneGetChildren(object):
            """Client callback class for <service>.getChildren() command."""
            def doneGetChildren(self, token, error, ids):
                """Called when context list retrieval is done.

                :param token: pending command handle.
                :param error: error description if operation failed, **None**
                              if succeeded.
                :param context_ids: array of available context IDs.
                """
                if error:
                    protocol.log("Error from " + service.getName() +
                                 ".getContext()", error)
                else:
                    val.setValue(ids)
                with condition:
                    condition.notify()

        # start the process itself

        service.getChildren(contextID, DoneGetChildren())

    # create a condition to wait on, and a value to get the children ids

    lock = threading.Condition()
    value = TcfValue()

    with lock:
        # TCF requests must be called by the dispatch thread, wait for a
        # maximum of 10 seconds
        protocol.invokeLater(callGetChildren, service=service, condition=lock,
                             val=value)
        lock.wait(10)

    # Return the retrieved children IDs, or an empty tuple

    return (tuple(value.getValue() or []))


def getContext(service, contextID):
    """Get a TCF context from a given service.

    As most of the TCF services have a **getContext()** command, this
    function is intended to define a generic **getContext()** call which
    can address any service.

    As the function returns a context object, it is up to the caller to use it
    appropriately.

    For example, for the runcontrol service, check if the runcontrol context is
    a container :

    .. code-block:: python

        import tcf
        import tcf.services.runcontrol as runcontrol

        c = tcf.connect("TCP:127.0.0.1:1534")
        rcSvc = getService(c, runcontrol.NAME)
        rcIDs = getChildren(rcSvc, None)
        rcContext = getContext(rcSvc, rcIDs[0])

        print('Runcontrol context is a container: ' +
              str(rcContext.isContainer()))

    :param service: The TCF service to get context from.
    :param contextID: ID of the context to get from *service*

    :returns: A context properties dictionnary, or **None** on error.
    """
    def callGetContext(service, condition, val):
        """Asynchronous request to get context properties.

        :param service: The TCF service proxy to send request to.
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.
        :param val: A TcfValue handling the request returned value.

        :returns: **None**, always.
        """
        class DoneGetContext(object):
            """Client callback class for <service>.getContext() command."""
            def doneGetContext(self, token, error, context):
                """Called when context data retrieval is done.

                :param token: pending command handle.
                :param error: error description if operation failed, **None**
                              if succeeded.
                :param context: context data.
                """
                if error:
                    protocol.log("Error from " + service.getName() +
                                 ".getContext()", error)
                else:
                    val.setValue(context)
                with condition:
                    condition.notify()

        # start the process itself

        service.getContext(contextID, DoneGetContext())

    # create a condition to wait on, and a value to get the children ids

    lock = threading.Condition()
    value = TcfValue()

    with lock:
        # TCF requests must be called by the dispatch thread, wait for a
        # maximum of 10 seconds
        protocol.invokeLater(callGetContext, service=service, condition=lock,
                             val=value)
        lock.wait(10)

    # Return the context properties, or None on error

    return (value.getValue())


def resume(context):
    """Resume a runcontrol context.

    The given *context* should be a RunControlContext, so that its resume()
    method may be called.

    :param context: A runcontrol context to resume.
    :type process: RunControlContext

    :returns: **None**, always.
    """
    def callResume(context, condition):
        """Asynchronous request to resume runcontrol context.

        :param context: The TCF RunControlContext to resume.
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.

        :returns: **None**, always.
        """
        class DoneResume(runcontrol.DoneCommand):
            """Client call back interface for RunControlContext.resume()."""
            def doneCommand(self, token, error):
                """Called when run control command execution is complete.

                :param token: pending command handle.
                :param error: command execution error or **None**.
                """
                if error:
                    protocol.log("Error from RunContext.resume", error)
                with condition:
                    condition.notify()

        # Resume context with RM_RESUME mode, 1 time. No resume properties.

        context.resume(runcontrol.RM_RESUME, 1, {}, DoneResume())

    # create a condition to wait on

    lock = threading.Condition()

    with lock:
        # TCF requests must be called by the dispatch thread, wait for a
        # maximum of 10 seconds

        protocol.invokeLater(callResume, context=context, condition=lock)
        lock.wait(10)


def start(connection, path, *args):
    """Start a new process in suspended mode for the given connection.

    :param connection: The TCF connection to use services from.
    :param path: Path of the executable to start.
    :param args: command line arguments.
    """
    def callStart(connection, condition, path, arguments, val):
        """Asynchronous request to start a process.

        :param connection: The TCF connection to get processes service from.
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.
        :param path: Path of the process to start on the target
        :param arguments: A list of program arguments for *path*
        :param val: A TcfValue handling the request returned value.

        :returns: **None**, always.
        """
        # get connection's processes service

        proc = connection.getRemoteService(processes_v1.NAME) or \
            connection.getRemoteService(processes.NAME)

        if not proc:
            with condition:
                print('No processes service available')
                condition.notify()
            return

        class DoneStart(processes.DoneStart):
            """Client callback interface for ProcessesService.start()."""

            def doneStart(self, token, error, process):
                """Called when process start is done.

                :param token: pending command handle.
                :param error: error description if operation failed, **None**
                              if  succeeded.
                :param process: ProcessContext object representing the started
                                process.
                """
                if error:
                    protocol.log("Error from Processes.start", error)
                else:
                    val.setValue(process)
                with condition:
                    condition.notify()

        # depending on the service, the start method only does 'doAttach', or
        # take a dictionnary of options

        if (proc.getName() == processes_v1.NAME):
            opts = {processes_v1.START_ATTACH: True,
                    processes_v1.START_USE_TERMINAL: True}
        else:
            opts = True

        # start the process itself

        cmdLine = [path]
        if arguments:
            cmdLine += arguments

        proc.start(os.path.dirname(path), path, cmdLine, None, opts,
                   DoneStart())

    # create a condition to wait on, and a value to get the children ids

    lock = threading.Condition()
    value = TcfValue()

    with lock:
        # TCF requests must be called by the dispatch thread, wait for a
        # maximum of 10 seconds
        protocol.invokeLater(callStart, connection=connection, condition=lock,
                             path=path, arguments=args, val=value)
        lock.wait(10)

    return (value.getValue())


def state(context):
    """Get the state of a RunControlContext.

    Getting the state of a RunControlContext is asynchronous.

    :param context: The context to get state for.
    :type context: RunControlContext

    :returns: A tuple of four elements representing the RunControl context
              state :

                  - A boolean stating if the context id suspended or not
                  - An integer repesenting the program counter of the context
                    (if it is suspended)
                  - A string representing the reason why the context is
                    suspended
                  - A dictionary of properties stating why the suspended state
                    properties (see runcontrol.STATE_*)
    """
    def callGetState(context, condition, val):
        """Asynchronous request to get the context state.

        :param context: The RunControlContext to get state for.
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.
        :param val: A TcfValue handling the request returned value.

        :returns: **None**, always.
        """
        class DoneGetState(runcontrol.DoneGetState):
            """Client call back class for RunControlContext.getState()."""
            def doneGetState(self, token, error, suspended, pc, reason,
                             params):
                """Called when RunControlContext.getState() command execution
                is complete.

                :param token: pending command handle.
                :param error: command execution error or None.
                :param suspended: true if the context is suspended
                :param pc: program counter of the context (if suspended).
                :param reason: suspend reason (if suspended), see REASON_*.
                :param params: additional target specific data about context
                               state, see STATE_*.
                """
                if error:
                    protocol.log("Error from runcontrol.getState()", error)
                else:
                    val.setValue((suspended, pc, reason, params))
                with condition:
                    condition.notify()

        # start the process itself

        context.getState(DoneGetState())

    # create a condition to wait on, and a value to get the children ids

    lock = threading.Condition()
    value = TcfValue()

    with lock:
        # TCF requests must be called by the dispatch thread, wait for a
        # maximum of 10 seconds
        protocol.invokeLater(callGetState, context=context, condition=lock,
                             val=value)
        lock.wait(10)

    return (value.getValue())


# Some TCF initialisation


def subscribe(svc, streamType, listener):
    """Subscribe to a streams channel.

    :param svc: The TCF streams proxy to subscribe against.
    :param streamType: Type of the stream to register against. For now,
                       I only know of 'Terminals', 'Processes' and
                       'ProcessesV1' types.
    :param listener: The listener to subscribe to *svc*.
    :type listener: tcf.services.streams.StreamsListener

    :returns: **None**, always.
    """
    def callSubscribe(service, streamType, listener, condition):
        """Asynchronous request to subscribe a listener to streams service.

        :param service: The streams service to subscribe listener against.
        :param streamType: Type of the stream to register against. For now,
                           I only know of 'Terminals', 'Processes' and
                           'ProcessesV1' types.
        :param listener: The listener to subscribe to *service*.
        :type listener: tcf.services.streams.StreamsListener
        :param condition: A threading.Condition the caller is pending on.
                          Caller is released from waiting through a
                          Condition.notify() call.

        :returns: **None**, always.
        """
        class DoneSubscribe(streams.DoneSubscribe):
            """Call back interface for StreamsService.subscribe() command."""
            def doneSubscribe(self, token, error):
                """Called when stream subscription is done.

                :param token: pending command handle
                :param error: error description if operation failed, **None**
                              if succeeded.
                """
                if error:
                    protocol.log("Error from streams.subscribe()", error)
                with condition:
                    condition.notify()

        # start the process itself

        service.subscribe(streamType, listener, DoneSubscribe())

    # create a condition to wait on

    lock = threading.Condition()

    with lock:
        # TCF requests must be called by the dispatche thread, wait for a
        # maximum of 10 seconds
        protocol.invokeLater(callSubscribe, service=svc, streamType=streamType,
                             listener=listener, condition=lock)
        lock.wait(10)

# --------------------------------------------------------------------------- #

# TCF initialisation

protocol.startEventQueue()
protocol.setLogger(TcfProtocolLogger())
atexit.register(protocol.getEventQueue().shutdown)

try:
    c = tcf.connect("TCP:127.0.0.1:1534")
except Exception as e:
    protocol.log(e)
    sys.exit()

# If there is a streams service, listen to it

streamsSvc = getService(c, streams.NAME)
if streamsSvc:
    subscribe(streamsSvc, 'ProcessesV1', StreamsListener(streamsSvc))

p = start(c, '/pdi_reader/ls', '-l', '-a')

# this part is a bit tricky, the runcontrol contexts which accept a resume
# command are the contexts which have a state. Recursively try to find the
# runcontrol context which has a state, and resume it.

rcSvc = getService(c, runcontrol.NAME)

if rcSvc is None:
    print('No runcontrol service. Exiting ...')
    sys.exit()

context = getContext(rcSvc, p.getID())
print('Runcontrol context is a container: ' + str(context.isContainer()))

while context and not context.hasState():
    children = getChildren(rcSvc, context.getID())
    for child in children:
        context = getContext(rcSvc, child)
        if context and context.hasState():
            break

if context is None:
    print('No runcontrol context to resume. Exiting ...')
    sys.exit()

# get the state of this context. State is a tuple of
# (suspended, pc, reason, params)

ctxState = state(context)
print('Context state : ' + str(ctxState))

while ctxState and ctxState[0]:
    resume(context)
    # calling resume may end the context ... catch exceptions

    try:
        ctxState = state(context)
        if ctxState:
            print('Context state : ' + str(ctxState))
    except:
        pass

# Let the async calls the time to end ...

time.sleep(2)
