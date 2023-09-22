# Copyright 2023 Xilinx, Inc.
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

from typing import Dict, List, Any, NewType
from chipscopy.tcf import channel, errors
from chipscopy.tcf.services import DoneHWCommand, memory

MemoryNode = NewType("MemoryNode", Dict[str, Any])

Memory_SERVICE = "Memory"


class Range(object):
    offs = 0
    size = 0
    stat = 0
    msg = None

    def __lt__(self, o):
        return self.__cmp__(o) == -1

    def __cmp__(self, o):
        if self.offs < o.offs:
            return -1
        if self.offs > o.offs:
            return +1
        return 0


class MemoryErrorReport(errors.ErrorReport, memory.MemoryError, memory.ErrorOffset):
    def __init__(self, msg, attrs, addr, ranges):
        super(MemoryErrorReport, self).__init__(msg, attrs)
        if ranges is None:
            self.ranges = None
        else:
            self.ranges = []
            for m in ranges:
                r = Range()
                x = m.get(memory.ErrorOffset.RANGE_KEY_ADDR)
                if isinstance(x, str):
                    y = int(x)
                else:
                    y = x
                r.offs = y - addr
                r.size = m.get(memory.ErrorOffset.RANGE_KEY_SIZE)
                r.stat = m.get(memory.ErrorOffset.RANGE_KEY_STAT)
                key = memory.ErrorOffset.RANGE_KEY_MSG
                r.msg = errors.toErrorString(m.get(key))
                assert r.offs >= 0
                assert r.size >= 0
                self.ranges.append(r)
            self.ranges.sort()

    def getMessage(self, offset):
        if self.ranges is None:
            return None
        l = 0
        h = len(self.ranges) - 1
        while l <= h:
            n = int((l + h) / 2)
            r = self.ranges[n]
            if r.offs > offset:
                h = n - 1
            elif offset >= r.offs + r.size:
                l = n + 1
            else:
                return r.msg
        return None

    def getStatus(self, offset):
        if self.ranges is None:
            return memory.ErrorOffset.BYTE_UNKNOWN
        l = 0
        h = len(self.ranges) - 1
        while l <= h:
            n = int((l + h) / 2)
            r = self.ranges[n]
            if r.offs > offset:
                h = n - 1
            elif offset >= r.offs + r.size:
                l = n + 1
            else:
                return r.stat
        return memory.ErrorOffset.BYTE_UNKNOWN


def toMemoryError(service, cmd, addr, data, ranges):
    if data is None:
        return None
    code = data.get(errors.ERROR_CODE)
    if len(cmd) > 72:
        cmd = cmd[0:72] + "..."
    msg = "TCF command exception:\nCommand: %s\n" % cmd + "Exception: %s\nError code: %d" % (
        errors.toErrorString(data),
        code,
    )
    e = MemoryErrorReport(msg, data, addr, ranges)
    return e


class MemContext(memory.MemoryContext):
    def __init__(self, service, props):
        super(MemContext, self).__init__(props)
        self.service = service

    def fill(self, addr, word_size, value, size, mode, done):
        service = self.service
        context_id = self.getID()
        done = service._makeCallback(done)
        cmd = "fill"

        def done_hw(self, token, error, args):
            e = None
            if error:
                # XXX : fle : Exception.message does not exist in python3,
                #             better use str(Exception)
                e = error
            else:
                assert len(args) == 2
                e = toMemoryError(service.getName(), cmd, addr, args[0], args[1])
            done.doneMemory(token, e)

        return service.send_old_command(
            cmd, (context_id, addr, word_size, size, mode, value), done_hw
        )

    def get(self, addr, word_size, buf, offs, size, mode, done):
        service = self.service
        context_id = self.getID()
        done = service._makeCallback(done)
        cmd = "get"

        def done_hw(token, error, args):
            e = None
            if error:
                # Exception.message does not exist in python3, better use
                # str(Exception)
                e = memory.MemoryError(str(error))
            else:
                assert len(args) == 3
                byts = channel.toByteArray(args[0])
                assert len(byts) <= size
                buf[offs : offs + len(byts)] = byts
                e = toMemoryError(service.getName(), cmd, addr, args[1], args[2])
            done.doneMemory(token, e)

        return service.send_old_command(cmd, (context_id, addr, word_size, size, mode), done_hw)

    def set(self, addr, word_size, buf, offs, size, mode, done):
        service = self.service
        context_id = self.getID()
        done = service._makeCallback(done)
        cmd = "set"

        def done_hw(token, error, args):
            e = None
            if error:
                # XXX : fle : Exception.message does not exist in python3,
                #             better use str(Exception)
                e = memory.MemoryError(str(error))
            else:
                assert len(args) == 2
                e = toMemoryError(service.getName(), cmd, addr, args[0], args[1])
            done.doneMemory(token, e)

        return service.send_old_command(
            cmd,
            (context_id, addr, word_size, size, mode, bytearray(buf[offs : offs + size])),
            done_hw,
        )


class MemoryProxy(memory.MemoryService):
    """TCF Memory service interface."""

    def __init__(self, channel):
        super(MemoryProxy, self).__init__(channel)
        self.listeners = {}

    def getName(self):
        """
        Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return Memory_SERVICE

    def get_context(self, context_id: str, done: DoneHWCommand) -> Dict[str, Any]:
        """
        Gets context information on a given context id

        :param context_id: Context id of the context
        :param done: Callback with result and any error.
        :return: A dictionary of context parameters
        """
        done = self._makeCallback(done)
        service = self

        class DoneContext(DoneHWCommand):
            def doneHW(self, token, error, args):
                ctx = None
                if not error:
                    assert len(args) == 1
                    if args[0]:
                        ctx = MemContext(service, args[0])
                done.doneGetContext(token, error, ctx)

        return self.send_command("getContext", (context_id,), DoneContext())

    def get_children(self, context_id: str, done: DoneHWCommand) -> List[str]:
        """
        Gets the children of a given context.  If no context is given then gets top level contexts.

        :param context_id: Context id of desired context
        :param done: Callback with result and any error.
        :return: List of child contexts
        """
        done = self._makeCallback(done)
        if not context_id:
            context_id = ""

        class DoneChildren(DoneHWCommand):
            def doneHW(self, token, error, args):
                contexts = None
                if not error:
                    assert len(args) == 1
                    contexts = args[0]
                done.doneGetChildren(token, error, contexts)

        return self.send_command("getChildren", (context_id,), DoneChildren())

    def add_listener(self, listener):
        """Add Memory service event listener.
        :param listener: Event listener implementation.
        """
        l = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, l)
        self.listeners[listener] = l

    def remove_listener(self, listener):
        """Remove Memory service event listener.
        :param listener: Event listener implementation.
        """
        l = self.listeners.get(listener)
        if l:
            del self.listeners[listener]
            self.channel.removeEventListener(self, l)

    getContext = get_context
    getChildren = get_children
    addListener = add_listener
    removeListener = remove_listener


class ChannelEventListener(channel.EventListener):
    def __init__(self, service, listener):
        self.service = service
        self.listener = listener
        self._event_handlers = {
            "contextAdded": self._context_added,
            "contextChanged": self._context_changed,
            "contextRemoved": self._context_removed,
            "memoryChanged": self._memory_changed,
        }

    def _context_added(self, args):
        assert len(args) == 1
        self.listener.contextAdded(_toContextArray(self.service, args[0]))

    def _context_changed(self, args):
        assert len(args) == 1
        self.listener.contextChanged(_toContextArray(self.service, args[0]))

    def _context_removed(self, args):
        assert len(args) == 1
        self.listener.contextRemoved(args[0])

    def _memory_changed(self, args):
        assert len(args) == 2
        self.listener.memoryChanged(args[0], _toAddrArray(args[1]), _toSizeArray(args[1]))


def _toContextArray(svc, o):
    if o is None:
        return None
    ctx = []
    for m in o:
        ctx.append(MemContext(svc, m))
    return ctx


def _toSizeArray(o):
    if o is None:
        return None
    return [m.get("size", 0) for m in o]


def _toAddrArray(o):
    if o is None:
        return None
    return [m.get("addr") for m in o]
