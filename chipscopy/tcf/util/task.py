# *****************************************************************************
# Copyright (c) 2011, 2013, 2016 Wind River Systems, Inc. and others.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License 2.0
# which accompanies this distribution, and is available at
# https://www.eclipse.org/legal/epl-2.0/
#
# Contributors:
#     Wind River Systems - initial API and implementation
# *****************************************************************************

import threading
from .. import protocol, channel


class Task(object):
    """A <tt>Task</tt> is an utility class that represents the result of an
    asynchronous communication over TCF framework.

    Methods are provided to check if the communication is complete, to wait for
    its completion, and to retrieve the result of the communication.

    Task is useful when communication is requested by a thread other then TCF
    dispatch thread.
    If client has a global state, for example, cached remote data,
    multithreading should be avoided,
    because it is extremely difficult to ensure absence of racing conditions or
    deadlocks in such environment.
    Such clients should consider message driven design, see DataCache and its
    usage as an example.

    If a client is extending Task it should implement run() method to perform
    actual communications.
    The run() method will be execute by TCF dispatch thread, and client code
    should then call either done() or error() to indicate that task
    computations are complete.
    """
    __result = None
    __is_done = False
    __error = None
    __canceled = False
    __channel_listener = None

    def __init__(self, target=None, *args, **kwargs):
        """
        Construct a TCF task object and schedule it for execution.
        """
        if target:
            kwargs["done"] = self.__done
        else:
            target = self.run

        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._lock = threading.Condition()
        self.__channel = kwargs.pop("channel", None)
        protocol.invokeLater(self.__doRun)
        timeout = kwargs.pop("timeout", None)
        if timeout:
            protocol.invokeLaterWithDelay(timeout, self.cancel)

    def __doRun(self):
        try:
            if self.__channel:
                if self.__channel.getState() != channel.STATE_OPEN:
                    raise Exception("Channel is closed")
                task = self

                class CancelOnClose(channel.ChannelListener):
                    def onChannelClosed(self, error):
                        task.cancel(True)
                self.__channel_listener = CancelOnClose()
                self.__channel.addChannelListener(self.__channel_listener)
            self._target(*self._args, **self._kwargs)
        except Exception as x:
            if not self.__is_done and self.__error is None:
                self.error(x)

    def __done(self, error, result):
        if error:
            self.error(error)
        else:
            self.done(result)

    def run(self, *args, **kwargs):
        raise NotImplementedError("Abstract method")

    def done(self, result):
        with self._lock:
            assert protocol.isDispatchThread()
            if self.__canceled:
                return
            assert not self.__is_done
            assert not self.__error
            assert self.__result is None
            self.__result = result
            self.__is_done = True
            if self.__channel:
                self.__channel.removeChannelListener(self.__channel_listener)
            self._lock.notifyAll()

    def error(self, error):
        """
        Set a error and notify all threads waiting for the task to complete.
        The method is supposed to be called in response to executing of run()
        method of this task.

        @param error - computation error.
        """
        assert protocol.isDispatchThread()
        assert error
        with self._lock:
            if self.__canceled:
                return
            assert self.__error is None
            assert self.__result is None
            assert not self.__is_done
            self.__error = error
            if self.__channel:
                self.__channel.removeChannelListener(self.__channel_listener)
            self._lock.notifyAll()

    def cancel(self):
        assert protocol.isDispatchThread()
        with self._lock:
            if self.isDone():
                return False
            self.__canceled = True
            self.__error = Exception("Canceled")
            if self.__channel:
                self.__channel.removeChannelListener(self.__channel_listener)
            self._lock.notifyAll()
        return True

    def get(self, timeout=None):
        """
        Waits if necessary for the computation to complete, and then
        retrieves its result.

        @return the computed result
        @throws CancellationException if the computation was canceled
        @throws ExecutionException if the computation threw an
        exception
        @throws InterruptedException if the current thread was interrupted
        while waiting
        """
        assert not protocol.isDispatchThread()
        with self._lock:
            while not self.isDone():
                self._lock.wait(timeout)
                if timeout and not self.isDone():
                    raise TimeoutException("Timed out")
            if self.__error:
                raise Exception("TCF task aborted", self.__error)
            return self.__result

    def isCancelled(self):
        """
        Returns <tt>true</tt> if this task was canceled before it completed
        normally.

        @return <tt>true</tt> if task was canceled before it completed
        """
        with self._lock:
            return self.__canceled

    def isDone(self):
        """
        Returns <tt>true</tt> if this task completed.

        Completion may be due to normal termination, an exception, or
        cancellation -- in all of these cases, this method will return
        <tt>true</tt>.

        @return <tt>true</tt> if this task completed.
        """
        with self._lock:
            return self.__error or self.__is_done

    def getError(self):
        """
        Return task execution error if any.
        @return Exception object or None
        """
        return self.__error

    def getResult(self):
        return self.__result


class TimeoutException(Exception):
    pass
