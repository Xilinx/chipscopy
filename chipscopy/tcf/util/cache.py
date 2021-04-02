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

from .. import protocol, channel
from .task import Task


class DataCache(object):
    """
    Objects of this class are used to cache TCF remote data.
    The cache is asynchronous state machine. The states are:
     1. Valid - cache is in sync with remote data, use getError() and getData()
        to get cached data
     2. Invalid - cache is out of sync, start data retrieval by calling
        validate()
     3. Pending - cache is waiting result of a command that was sent to remote
        peer
     4. Disposed - cache is disposed and cannot be used to store data.

    A cache instance can be created on any data type that needs to be cached.
    Examples might be context children list, context properties, context state,
    memory data, register data, symbol, variable, etc.
    Clients of cache items can register for cache changes, but don't need to
    think about any particular events since that is handled by the cache item
    itself.

    A typical cache client should implement Runnable interface.
    The implementation of run() method should:

    Validate all cache items required for client task.
    If anything is invalid then client should not alter any shared data
    structures, should discard any intermediate results and register (wait) for
    changes of invalid cache instance(s) state.

    When cache item state changes, client is invoked again and full validation
    is restarted.
    Once everything is valid, client completes its task in a single dispatch
    cycle.

    Note: clients should never retain copies of remote data across dispatch
          cycles! Such data would get out of sync and compromise data
          consistency. All remote data and everything derived from remote data
          should be kept in cache items that implement proper event handling
          and can keep data consistent across dispatch cycles.
    """

    __error = None
    __valid = None
    __posted = False
    __disposed = False
    __data = None

    def __init__(self, channel):
        assert channel
        self._channel = channel
        self._command = None
        self.__waiting_list = None

    def post(self):
        if self.__posted:
            return
        if not self.__waiting_list:
            return
        protocol.invokeLater(self)
        self.__posted = True

    def isValid(self):
        """
        @return True if cache contains up-to-date data or error.
        """
        return self.__valid

    def isPending(self):
        """
        @return True if data retrieval command is in progress.
        """
        return self._command is not None

    def isDisposed(self):
        """
        @return True if cache is disposed.
        """
        return self.__disposed

    def getError(self):
        """
        @return error object if data retrieval ended with an error, or None if
        retrieval was successful.
        Note: It is prohibited to call this method when cache is not valid.
        """
        assert self.__valid
        return self.__error

    def getData(self):
        """
        @return cached data object.
        Note: It is prohibited to call this method when cache is not valid.
        """
        assert protocol.isDispatchThread()
        assert self.__valid
        return self.__data

    def __call__(self):
        """
        Notify waiting clients about cache state change and remove them from
        wait list.
        It is responsibility of clients to check if the state change was one
        they are waiting for.
        Clients are not intended to call this method.
        """
        assert protocol.isDispatchThread()
        self.__posted = False
        if self.__waiting_list:
            arr = self.__waiting_list
            self.__waiting_list = None
            for r in tuple(arr):
                if isinstance(r, DataCache):
                    r.post()
                elif isinstance(r, Task) and not r.isDone():
                    r.run()
                else:
                    r()

                arr.remove(r)

            if self.__waiting_list is None:
                self.__waiting_list = arr

    def wait(self, cb):
        """
        Add a client call-back to cache wait list.
        Client call-backs are activated when cache state changes.
        Call-backs are removed from waiting list after that.
        It is responsibility of clients to check if the state change was one
        they are waiting for.
        @param cb - a call-back object
        """
        assert protocol.isDispatchThread()
        assert not self.__disposed
        assert not self.__valid
        if cb and not self.isWaiting(cb):
            if self.__waiting_list is None:
                self.__waiting_list = []
            self.__waiting_list.append(cb)

    def isWaiting(self, cb):
        """
        Return True if a client call-back is waiting for state changes of this
        cache item.
        @param cb - a call-back object.
        @return True if 'cb' is in the wait list.
        """
        if not self.__waiting_list:
            return False
        return cb in self.__waiting_list

    def __validate(self):
        """
        Initiate data retrieval if the cache is not valid.
        @return True if the cache is already valid
        """
        assert protocol.isDispatchThread()
        if self.__disposed or self._channel.getState() != channel.STATE_OPEN:
            self._command = None
            self.__valid = True
            self.__error = None
            self.__data = None
        else:
            if self._command is not None:
                return False
            if not self.__valid and not self.startDataRetrieval():
                return False
        assert self.__valid
        assert self._command is None
        self.post()
        return True

    def validate(self, cb=None):
        """
        If the cache is not valid, initiate data retrieval and
        add a client call-back to cache wait list.
        Client call-backs are activated when cache state changes.
        Call-backs are removed from waiting list after that.
        It is responsibility of clients to check if the state change was one
        they are waiting for.
        If the cache is valid do nothing and return True.
        @param cb - a call-back object (optional)
        @return True if the cache is already valid
        """
        if not self.__validate():
            self.wait(cb)
            return False
        return True

    def start(self, command):
        """
        Start cache pending state.
        Pending state is when the cache is waiting for a TCF command to return
        results.
        @param command - TCF command handle.
        """
        assert not self.__valid
        assert command
        assert self._command is None
        self._command = command

    def done(self, command):
        """
        End cache pending state, but not mark the cache as valid.
        @param command - TCF command handle.
        """
        if self._command is not command:
            return
        assert not self.__valid
        self._command = None
        self.post()

    def set(self, token, error, data):
        """
        End cache pending state and mark the cache as valid.
        If 'token' != None, the data represent results from a completed
        command.
        The data should be ignored if current cache pending command is not same
        as 'token'.
        It can happen if the cache was reset or canceled during data retrieval.
        @param token - pending command handle or None.
        @param error - data retrieval error or None
        @param data - up-to-date data object
        """
        assert protocol.isDispatchThread()
        if token and self._command is not token:
            return
        self._command = None
        if not self.__disposed:
            assert not self.__valid
            if self._channel.getState() != channel.STATE_OPEN:
                self.__error = None
                self.__data = None
            self.__error = error
            self.__data = data
            self.__valid = True
        self.post()

    def reset(self, data=None):
        """
        Force cache to become valid, cancel pending data retrieval if data is
        provided.
        @param data - up-to-date data object (optional)
        """
        assert protocol.isDispatchThread()
        if data is not None and self._command is not None:
            self._command.cancel()
            self._command = None
        if not self.__disposed:
            self.__data = data
            self.__error = None
            self.__valid = data is not None
        self.post()

    def cancel(self):
        """
        Invalidate the cache.
        Cancel pending data retrieval if any.
        """
        self.reset()
        if self._command is not None:
            self._command.cancel()
            self._command = None

    def dispose(self):
        """
        Dispose the cache.
        Cancel pending data retrieval if any.
        """
        self.cancel()
        self.__valid = True
        self.__disposed = True

    def __str__(self):
        res = '['
        if self.__valid:
            res += 'valid,'
        if self.__disposed:
            res += 'disposed,'
        if self.__posted:
            res += 'posted,'
        if self.__error is not None:
            res += 'error,'
        res += 'data='
        res += str(self.__data)
        res += ']'
        return res

    def startDataRetrieval(self):
        """
        Sub-classes should override this method to implement actual data
        retrieval logic.
        @return True is all done, False if retrieval is in progress.
        """
        raise NotImplementedError("Abstract method")
