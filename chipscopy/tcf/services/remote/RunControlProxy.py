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

from .. import runcontrol
from ... import channel
from ...channel.Command import Command


class RunContext(runcontrol.RunControlContext):
    def __init__(self, service, props):
        super(RunContext, self).__init__(props)
        self.service = service

    def getISA(self, address, done):
        service = self.service
        done = service._makeCallback(done)
        contextID = self.getID()

        class GetISACommand(Command):
            def __init__(self):
                super(GetISACommand, self).__init__(service.channel, service,
                                                    "getISA",
                                                    (contextID, address))

            def done(self, error, args):
                isa = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    isa = runcontrol.RunControlISA(args[1])
                done.doneGetISA(self.token, error, isa)
        return GetISACommand().token

    def getState(self, done):
        service = self.service
        done = service._makeCallback(done)
        contextID = self.getID()

        class GetStateCommand(Command):
            def __init__(self):
                super(GetStateCommand, self).__init__(service.channel, service,
                                                      "getState", (contextID,))

            def done(self, error, args):
                susp = False
                pc = None
                reason = None
                states = None
                if not error:
                    assert len(args) == 5
                    error = self.toError(args[0])
                    susp = args[1]
                    if args[2] is not None:
                        pc = int(args[2])
                    reason = args[3]
                    states = args[4]
                done.doneGetState(self.token, error, susp, pc, reason, states)
        return GetStateCommand().token

    def detach(self, done):
        return self._command("detach", (self.getID(),), done)

    def resume(self, mode, count, params, done):
        if not params:
            return self._command("resume", (self.getID(), mode, count), done)
        else:
            return self._command("resume", (self.getID(), mode, count, params),
                                 done)

    def suspend(self, done):
        return self._command("suspend", (self.getID(),), done)

    def terminate(self, done):
        return self._command("terminate", (self.getID(),), done)

    def _command(self, cmd, args, done):
        service = self.service
        done = service._makeCallback(done)

        class RCCommand(Command):
            def __init__(self, cmd, args):
                super(RCCommand, self).__init__(service.channel, service, cmd,
                                                args)

            def done(self, error, args):
                if not error:
                    assert len(args) == 1
                    error = self.toError(args[0])
                done.doneCommand(self.token, error)
        return RCCommand(cmd, args).token


class ChannelEventListener(channel.EventListener):
    def __init__(self, service, listener):
        self.service = service
        self.listener = listener

    def event(self, name, data):
        try:
            args = channel.fromJSONSequence(data)
            if name == "contextSuspended":
                assert len(args) == 4
                self.listener.contextSuspended(args[0], args[1], args[2],
                                               args[3])
            elif name == "contextResumed":
                assert len(args) == 1
                self.listener.contextResumed(args[0])
            elif name == "contextAdded":
                assert len(args) == 1
                self.listener.contextAdded(_toContextArray(self.service,
                                                           args[0]))
            elif name == "contextChanged":
                assert len(args) == 1
                self.listener.contextChanged(_toContextArray(self.service,
                                                             args[0]))
            elif name == "contextRemoved":
                assert len(args) == 1
                self.listener.contextRemoved(args[0])
            elif name == "contextException":
                assert len(args) == 2
                self.listener.contextException(args[0], args[1])
            elif name == "containerSuspended":
                assert len(args) == 5
                self.listener.containerSuspended(args[0], args[1], args[2],
                                                 args[3], args[4])
            elif name == "containerResumed":
                assert len(args) == 1
                self.listener.containerResumed(args[0])
            elif name == "contextStateChanged":
                assert len(args) == 1
                self.listener.contextStateChanged(args[0])
            else:
                raise IOError("RunControl service: unknown event: " + name)
        except Exception as x:
            import sys
            x.tb = sys.exc_info()[2]
            self.service.channel.terminate(x)


class RunControlProxy(runcontrol.RunControlService):
    def __init__(self, channel):
        self.channel = channel
        self.listeners = {}

    def addListener(self, listener):
        l = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, l)
        self.listeners[listener] = l

    def removeListener(self, listener):
        l = self.listeners.get(listener)
        if l:
            del self.listeners[listener]
            self.channel.removeEventListener(self, l)

    def getContext(self, context_id, done):
        done = self._makeCallback(done)
        service = self

        class GetContextCommand(Command):
            def __init__(self):
                super(GetContextCommand, self).__init__(service.channel,
                                                        service, "getContext",
                                                        (context_id,))

            def done(self, error, args):
                ctx = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    if args[1]:
                        ctx = RunContext(service, args[1])
                done.doneGetContext(self.token, error, ctx)
        return GetContextCommand().token

    def getChildren(self, parent_context_id, done):
        done = self._makeCallback(done)
        service = self

        class GetChildrenCommand(Command):
            def __init__(self):
                super(GetChildrenCommand, self).__init__(service.channel,
                                                         service,
                                                         "getChildren",
                                                         (parent_context_id,))

            def done(self, error, args):
                contexts = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    contexts = args[1]
                done.doneGetChildren(self.token, error, contexts)
        return GetChildrenCommand().token


def _toContextArray(svc, o):
    if o is None:
        return None
    ctx = []
    for m in o:
        ctx.append(RunContext(svc, m))
    return ctx
