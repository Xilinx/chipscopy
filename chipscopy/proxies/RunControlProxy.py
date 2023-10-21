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
from chipscopy.tcf import channel
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.tcf.services import runcontrol

RunControlNode = NewType("RunControlNode", Dict[str, Any])

RunControl_SERVICE = "RunControl"


class RunContext(runcontrol.RunControlContext):
    def __init__(self, service, props):
        super(RunContext, self).__init__(props)
        self.service = service

    def getISA(self, address, done):
        service = self.service
        context_id = self.getID()
        done = service._makeCallback(done)
        cmd = "getISA"

        def done_hw(token, error, args):
            isa = None
            if not error:
                assert len(args) == 2
                error = args[0]
                isa = runcontrol.RunControlISA(args[1])
            done.doneGetISA(token, error, isa)

        return service.send_old_command(cmd, (context_id, address), done_hw)

    def getState(self, done):
        service = self.service
        context_id = self.getID()
        done = service._makeCallback(done)
        cmd = "getState"

        def done_hw(token, error, args):
            susp = False
            pc = None
            reason = None
            states = None
            if not error:
                assert len(args) == 5
                error = args[0]
                susp = args[1]
                if args[2] is not None:
                    pc = int(args[2])
                reason = args[3]
                states = args[4]
            done.doneGetState(token, error, susp, pc, reason, states)

        return service.send_old_command(cmd, (context_id,), done_hw)

    def detach(self, done):
        return self._command("detach", (self.getID(),), done)

    def resume(self, mode, count, params, done):
        if not params:
            return self._command("resume", (self.getID(), mode, count), done)
        else:
            return self._command("resume", (self.getID(), mode, count, params), done)

    def suspend(self, done):
        return self._command("suspend", (self.getID(),), done)

    def terminate(self, done):
        return self._command("terminate", (self.getID(),), done)

    def _command(self, cmd, args, done):
        service = self.service
        done = service._makeCallback(done)

        def done_hw(token, error, args):
            if not error:
                assert len(args) == 1
                error = args[0]
            done.doneCommand(token, error)

        return service.send_old_command(cmd, args, done_hw)


class RunControlProxy(runcontrol.RunControlService):
    """TCF RunControl service interface."""

    def __init__(self, channel):
        super(RunControlProxy, self).__init__(channel)
        self.listeners = {}

    def getName(self):
        """
        Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return RunControl_SERVICE

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
                        ctx = RunContext(service, args[0])
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
        """Add RunControl service event listener.
        :param listener: Event listener implementation.
        """
        l = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, l)
        self.listeners[listener] = l

    def remove_listener(self, listener):
        """Remove RunControl service event listener.
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
            "contextSuspended": self._context_suspended,
            "contextResumed": self._context_resumed,
            "contextAdded": self._context_added,
            "contextChanged": self._context_changed,
            "contextRemoved": self._context_removed,
            "contextException": self._context_exception,
            "containerSuspended": self._container_suspended,
            "containerResumed": self._container_resumed,
            "contextStateChanged": self._context_state_changed,
        }

    def _context_suspended(self, args):
        assert len(args) == 4
        self.listener.contextSuspended(args[0], args[1], args[2], args[3])

    def _context_resumed(self, args):
        assert len(args) == 1
        self.listener.contextResumed(args[0])

    def _context_added(self, args):
        assert len(args) == 1
        self.listener.contextAdded(_toContextArray(self.service, args[0]))

    def _context_changed(self, args):
        assert len(args) == 1
        self.listener.contextChanged(_toContextArray(self.service, args[0]))

    def _context_removed(self, args):
        assert len(args) == 1
        self.listener.contextRemoved(args[0])

    def _context_exception(self, args):
        assert len(args) == 2
        self.listener.contextException(args[0], args[1])

    def _container_suspended(self, args):
        assert len(args) == 5
        self.listener.containerSuspended(args[0], args[1], args[2], args[3], args[4])

    def _container_resumed(self, args):
        assert len(args) == 1
        self.listener.containerResumed(args[0])

    def _context_state_changed(self, args):
        assert len(args) == 1
        self.listener.contextStateChanged(args[0])


def _toContextArray(svc, o):
    if o is None:
        return None
    ctx = []
    for m in o:
        ctx.append(RunContext(svc, m))
    return ctx


def _toSizeArray(o):
    if o is None:
        return None
    return [m.get("size", 0) for m in o]


def _toAddrArray(o):
    if o is None:
        return None
    return [m.get("addr") for m in o]
