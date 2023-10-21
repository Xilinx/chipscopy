# *****************************************************************************
# * Copyright (c) 2011, 2013, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""
Module protocol provides static methods to access Target Communication
Framework root objects:

1. the framework event queue and dispatch thread
2. local instance of Locator service, which maintains a list of available
   targets
3. list of open communication channels.

It also provides utility methods for posting asynchronous events,
including delayed events (timers).
"""

import sys
import uuid
import pytcf
import atexit

_event_queue = None


def startEventQueue(logfile=""):
    global _event_queue
    pytcf.launch_event_loop(logfile)
    _event_queue = True



@atexit.register
def stopEventQueue():
    global _event_queue
    pytcf.stop_event_loop()
    _event_queue = False


def getEventQueue():
    """
    @return instance of event queue that is used for TCF events.
    """
    return _event_queue


def isDispatchThread():
    """
    Returns true if the calling thread is the TCF event dispatch thread.
    Use this call to ensure that a given task is being executed (or not being)
    on dispatch thread.

    @return true if running on the dispatch thread.
    """
    return pytcf.is_dispatch_thread()


def invokeLater(c, *args, **kwargs):
    """
    Causes callable to be called with given arguments
    in the dispatch thread of the framework.
    Events are dispatched in same order as queued.
    If invokeLater is called from the dispatching thread
    the callable will still be deferred until
    all pending events have been processed.

    This method can be invoked from any thread.

    @param c - the callable to be executed asynchronously
    """
    pytcf.post_event(c, *args, **kwargs)


def invokeLaterWithDelay(delay, c, *args, **kwargs):
    """
    Causes callable event to called in the dispatch thread of the framework.
    The event is dispatched after given delay.

    This method can be invoked from any thread.

    @param delay     milliseconds to delay event dispatch.
                     If delay <= 0 the event is posted into the
                     "ready" queue without delay.
    @param c - the callable to be executed asynchronously.
    """
    pytcf.post_event_with_delay(delay, c, *args, **kwargs)


def invokeAndWait(c, *args, **kwargs):
    """
    Causes callable to be called in the dispatch thread of the framework.
    Calling thread is suspended until the method is executed.
    If invokeAndWait is called from the dispatching thread
    the callable is executed immediately.

    This method can be invoked from any thread.

    @param c  the callable to be executed on dispatch thread.
    """
    return pytcf.post_event_and_wait(c, *args, **kwargs)


_agentID = str(uuid.uuid4())


def getAgentID():
    return _agentID


_logger = None


def setLogger(logger):
    """
    Set framework logger.
    By default sys.stderr is used.

    @param logger - an object implementing Logger interface.
    """
    global _logger
    _logger = logger


def log(msg, x=None):
    """
    Logs the given message.
    @see #setLogger
    This method can be invoked from any thread.
    @param msg - log entry text
    @param x - an exception associated with the log entry or None.
    """
    if not _logger:
        sys.stderr.write(str(msg) + '\n')
        while x:
            import traceback
            sys.stderr.write("%s: %s\n" % (type(x).__name__, x))
            tb = getattr(x, "tb", None) or sys.exc_info()[2]
            if tb:
                traceback.print_tb(tb)
            caused_by = getattr(x, "caused_by", None)
            if caused_by:
                sys.stderr.write("Caused by: " + str(caused_by) + "\n")
                x = caused_by
            else:
                break
    else:
        _logger.log(msg, x)


def startDiscovery():
    pass


def shutdownDiscovery():
    pass


def getLocator():
    """
    Get instance of the framework locator service.
    The service can be used to discover available remote peers.
    @return instance of LocatorService.
    """
    from ..services.local.LocatorService import LocatorService
    return LocatorService.locator


def getOpenChannels():
    """
    Return an array of all open channels.
    @return an array of IChannel
    """
    return pytcf.get_channels()


class ChannelOpenListener(object):
    """
    Interface to be implemented by clients willing to be notified when
    new TCF communication channel is opened.

    The interface allows a client to get pointers to channel objects that were
    opened by somebody else. If a client open a channel itself, it already has
    the pointer and does not need protocol.ChannelOpenListener. If a channel is
    created, for example, by remote peer connecting to the client, the only way
    to get the pointer is protocol.ChannelOpenListener.
    """
    def __init__(self):
        self.active = True

    def onChannelOpen(self, channel):
        pass

    def __call__(self, channel):
        if self.active:
            self.onChannelOpen(channel)


def addChannelOpenListener(listener):
    """
    Add a listener that will be notified when new channel is opened.
    @param listener
    """
    assert isDispatchThread()
    pytcf.add_channel_open_listener(listener)


def removeChannelOpenListener(listener):
    """
    Remove channel opening listener.
    @param listener
    """
    assert isDispatchThread()
    listener.active = False


def sendEvent(service_name, event_name, data):
    """
    Transmit TCF event message.
    The message is sent to all open communication channels - broadcasted.
    """
    assert isDispatchThread()
    pytcf.write_event_args(service_name, event_name, data)
