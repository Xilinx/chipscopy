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

import sys
import time
import threading
import atexit
import tcf  # @UnresolvedImport

from tcf import protocol, channel, errors  # @UnresolvedImport
from tcf.util import sync  # @UnresolvedImport

__TRACE = False


class TraceListener(channel.TraceListener):

    def onMessageReceived(self, msgType, token, service, name, data):
        print("<<< ", msgType, token, service, name, data)

    def onMessageSent(self, msgType, token, service, name, data):
        print(">>>", msgType, token, service, name, data)

    def onChannelClosed(self, error):
        sys.stderr.write("*** closed *** " + str(error) + "\n")

_suspended = []
_memory = []
_services = []


def test():
    global _services
    protocol.startEventQueue()
    atexit.register(protocol.getEventQueue().shutdown)
    # testTimer()
    try:
        c = tcf.connect("TCP:127.0.0.1:1534")
    except Exception as e:
        protocol.log(e)
        sys.exit()
    assert c.state == channel.STATE_OPEN
    if __TRACE:
        protocol.invokeAndWait(c.addTraceListener, TraceListener())
    _services = sorted(protocol.invokeAndWait(c.getRemoteServices))
    print("services=" + str(_services))

    if "RunControl" in _services:
        # RunControl must be first
        _services.remove("RunControl")
        _services.insert(0, "RunControl")
    for service in _services:
        testFct = globals().get("test" + service)
        if testFct:
            print("Testing service '%s'..." % service)
            try:
                testFct(c)
                print("Completed test of service '%s'." % service)
            except Exception as e:
                protocol.log("Exception testing %s" % service, e)
        else:
            print("No test for service '%s' found." % service)
    try:
        testSyncCommands(c)
        testTasks(c)
        testEvents(c)
        testDataCache(c)
    except Exception as e:
        protocol.log(e)

    if c.state == channel.STATE_OPEN:
        time.sleep(5)
        protocol.invokeLater(c.close)
    time.sleep(2)


def testTimer():
    cond = threading.Condition()

    def countdown(left):
        if left == 0:
            print("Ignition sequence started!")
            with cond:
                cond.notify()
            return
        print("%d seconds to go" % left)
        sys.stdout.flush()
        protocol.invokeLaterWithDelay(1000, countdown, left - 1)
    with cond:
        protocol.invokeLaterWithDelay(0, countdown, 10)
        cond.wait(15)


def testRunControl(c):
    lock = threading.Condition()
    from tcf.services import runcontrol  # @UnresolvedImport

    def getContexts():
        rctrl = c.getRemoteService(runcontrol.NAME)
        pending = []

        class DoneGetContext(runcontrol.DoneGetContext):
            def doneGetContext(self, token, error, context):
                pending.remove(token)
                if error:
                    protocol.log("Error from RunControl.getContext", error)
                else:
                    print(context)

                class DoneGetState(runcontrol.DoneGetState):

                    def doneGetState(self, token, error, suspended, pc, reason,
                                     params):
                        pending.remove(token)
                        if error:
                            protocol.log(
                                "Error from RunControl.getState", error)
                        else:
                            print("suspended: " + str(suspended))
                            print("pc:        " + str(pc))
                            print("reason:    " + str(reason))
                            print("params:    " + str(params))
                        if suspended:
                            _suspended.append(context.getID())
                        if len(pending) == 0:
                            with lock:
                                lock.notify()
                if context and context.hasState():
                    pending.append(context.getState(DoneGetState()))
                if len(pending) == 0:
                    with lock:
                        lock.notify()

        class DoneGetChildren(runcontrol.DoneGetChildren):
            def doneGetChildren(self, token, error, context_ids):
                pending.remove(token)
                if error:
                    protocol.log("Error from RunControl.GetChildren", error)
                else:
                    for c in context_ids:
                        pending.append(rctrl.getContext(c, DoneGetContext()))
                        pending.append(rctrl.getChildren(c, self))
                if len(pending) == 0:
                    with lock:
                        lock.notify()
        pending.append(rctrl.getChildren(None, DoneGetChildren()))
    with lock:
        protocol.invokeLater(getContexts)
        lock.wait(5)

    def listenerTest():
        rc = c.getRemoteService(runcontrol.NAME)

        class RCListener(runcontrol.RunControlListener):
            def contextSuspended(self, *args):
                print("context suspended: " + str(args))
                rc.removeListener(self)

            def contextResumed(self, *args):
                print("context resumed: " + str(args))

            def containerSuspended(self, *args):
                print("container suspended: " + str(args))
                rc.removeListener(self)

            def containerResumed(self, *args):
                print("container resumed: " + str(args))
        rc.addListener(RCListener())

        class DoneGetContext(runcontrol.DoneGetContext):
            def doneGetContext(self, token, error, context):
                if error:
                    protocol.log("Error from RunControl.getContext", error)
                    with lock:
                        lock.notify()
                    return

                class DoneResume(runcontrol.DoneCommand):
                    def doneCommand(self, token, error):
                        if error:
                            protocol.log("Error from RunControl.resume", error)
                        else:
                            context.suspend(runcontrol.DoneCommand())
                        with lock:
                            lock.notify()
                context.resume(runcontrol.RM_RESUME, 1, None, DoneResume())
        rc.getContext(_suspended[0], DoneGetContext())

    if _suspended:
        with lock:
            protocol.invokeLater(listenerTest)
            lock.wait(5)
        _suspended.pop(0)


def testBreakpoints(c):
    from tcf.services import breakpoints  # @UnresolvedImport

    def testBPQuery():
        bps = c.getRemoteService(breakpoints.NAME)

        def doneGetIDs(token, error, ids):
            if error:
                protocol.log("Error from Breakpoints.getIDs", error)
                return
            print("Breakpoints : " + str(ids))

            def doneGetProperties(token, error, props):
                if error:
                    protocol.log("Error from Breakpoints.getProperties", error)
                    return
                print("Breakpoint Properties: " + str(props))

            def doneGetStatus(token, error, props):
                if error:
                    protocol.log("Error from Breakpoints.getStatus", error)
                    return
                print("Breakpoint Status: " + str(props))
            for bpid in ids:
                bps.getProperties(bpid, doneGetProperties)
                bps.getStatus(bpid, doneGetStatus)
        bps.getIDs(doneGetIDs)
    protocol.invokeLater(testBPQuery)

    def testBPSet():
        bpsvc = c.getRemoteService(breakpoints.NAME)

        class BPListener(breakpoints.BreakpointsListener):
            def breakpointStatusChanged(self, bpid, status):
                print("breakpointStatusChanged " + str(bpid) + " " +
                      str(status))

            def contextAdded(self, bps):
                print("breakpointAdded " + str(bps))
                bpsvc.removeListener(self)

            def contextChanged(self, bps):
                print("breakpointChanged " + str(bps))

            def contextRemoved(self, ids):
                print("breakpointRemoved " + str(ids))
        bpsvc.addListener(BPListener())

        def doneSet(token, error):
            if error:
                protocol.log("Error from Breakpoints.set", error)
                return
        bp = {
            breakpoints.PROP_ID: "python:1",
            breakpoints.PROP_ENABLED: True,
            breakpoints.PROP_LOCATION: "sysClkRateGet"
        }
        bpsvc.set([bp], doneSet)
    protocol.invokeLater(testBPSet)


def testStackTrace(c):
    from tcf.services import stacktrace  # @UnresolvedImport

    def stackTest(ctx_id):
        stack = c.getRemoteService(stacktrace.NAME)

        class DoneGetChildren(stacktrace.DoneGetChildren):
            def doneGetChildren(self, token, error, ctx_ids):
                if error:
                    protocol.log("Error from StackTrace.getChildren", error)
                    return

                class DoneGetContext(stacktrace.DoneGetContext):
                    def doneGetContext(self, token, error, ctxs):
                        if error:
                            protocol.log(
                                "Error from StackTrace.getContext", error)
                            return
                        if ctxs:
                            for ctx in ctxs:
                                print(ctx)
                stack.getContext(ctx_ids, DoneGetContext())
        stack.getChildren(ctx_id, DoneGetChildren())
    for ctx_id in _suspended:
        protocol.invokeLater(stackTest, ctx_id)


def testDisassembly(c):
    if not _suspended:
        return
    ctl = sync.CommandControl(c)
    try:
        dis = ctl.Disassembly
    except AttributeError:
        # no Disassembly service
        return
    for ctx_id in _suspended:
        frames = ctl.StackTrace.getChildren(ctx_id).get()
        if frames:
            frameData = ctl.StackTrace.getContext(frames).get()
            if frameData:
                addr = frameData[0].get("IP")
                if addr:
                    print("Disassemble context %s from 0x%x" % (ctx_id, addr))
                    lines = dis.disassemble(ctx_id, addr, 256, None).get()
                    if lines:
                        for line in lines:
                            print(line)


def testSymbols(c):
    from tcf.services import symbols  # @UnresolvedImport

    def symTest(ctx_id):
        syms = c.getRemoteService(symbols.NAME)

        class DoneList(symbols.DoneList):
            def doneList(self, token, error, ctx_ids):
                if error:
                    protocol.log("Error from Symbols.list", error)
                    return

                class DoneGetContext(symbols.DoneGetContext):
                    def doneGetContext(self, token, error, ctx):
                        if error:
                            protocol.log(
                                "Error from Symbols.getContext", error)
                            return
                        print(ctx)
                if ctx_ids:
                    for ctx_id in ctx_ids:
                        syms.getContext(ctx_id, DoneGetContext())
        syms.list(ctx_id, DoneList())
    for ctx_id in _suspended:
        protocol.invokeLater(symTest, ctx_id)


def testRegisters(c):
    if not _suspended:
        return
    from tcf.services import registers  # @UnresolvedImport
    lock = threading.Condition()

    def regTest(ctx_id):
        regs = c.getRemoteService(registers.NAME)
        pending = []

        def onDone():
            with lock:
                lock.notify()

        class DoneGetChildren(registers.DoneGetChildren):
            def doneGetChildren(self, token, error, ctx_ids):
                pending.remove(token)
                if error:
                    protocol.log("Error from Registers.getChildren", error)
                if not pending:
                    onDone()

                class DoneGetContext(registers.DoneGetContext):
                    def doneGetContext(self, token, error, ctx):
                        pending.remove(token)
                        if error:
                            protocol.log(
                                "Error from Registers.getContext", error)
                        else:
                            print(ctx)
                            if ctx.isReadable() and not ctx.isReadOnce() \
                                    and ctx.getSize() >= 2:
                                locs = []
                                locs.append(
                                    registers.Location(ctx.getID(), 0, 1))
                                locs.append(
                                    registers.Location(ctx.getID(), 1, 1))

                                class DoneGetM(registers.DoneGet):
                                    def doneGet(self, token, error, value):
                                        pending.remove(token)
                                        if error:
                                            protocol.log(
                                                "Error from Registers.getm",
                                                error)
                                        else:
                                            print("getm " + str(ctx.getID()) +
                                                  " " +
                                                  str(list(map(int, value))))
                                        if not pending:
                                            onDone()
                                pending.append(regs.getm(locs, DoneGetM()))
                            if ctx.isWriteable() and not ctx.isWriteOnce() \
                                    and ctx.getSize() >= 2:
                                locs = []
                                locs.append(
                                    registers.Location(ctx.getID(), 0, 1))
                                locs.append(
                                    registers.Location(ctx.getID(), 1, 1))

                                class DoneSetM(registers.DoneSet):
                                    def doneGet(self, token, error):
                                        pending.remove(token)
                                        if error:
                                            protocol.log(
                                                "Error from Registers.setm",
                                                error)
                                        if not pending:
                                            onDone()
                                pending.append(
                                    regs.setm(locs, (255, 255), DoneSetM()))
                        if not pending:
                            onDone()
                if ctx_ids:
                    for ctx_id in ctx_ids:
                        pending.append(
                            regs.getContext(ctx_id, DoneGetContext()))
        pending.append(regs.getChildren(ctx_id, DoneGetChildren()))
    with lock:
        for ctx_id in _suspended:
            protocol.invokeLater(regTest, ctx_id)
        lock.wait(5)


def testExpressions(c):
    if not _suspended:
        return
    from tcf.services import expressions  # @UnresolvedImport
    ctl = sync.CommandControl(c)
    exprs = ctl.Expressions
    e = exprs.create(_suspended[0], None, "1+2*(3-4/2)").getE()
    eid = e.get(expressions.PROP_ID)
    val, cls = exprs.evaluate(eid).getE()
    print(e.get(expressions.PROP_EXPRESSION) + " = " + str(val))
    exprs.dispose(eid)


def testLineNumbers(c):
    if not _suspended:
        return
    from tcf.services import stacktrace  # @UnresolvedImport
    ctl = sync.CommandControl(c)
    stack = ctl.StackTrace
    lineNumbers = ctl.LineNumbers
    for ctx_id in _suspended:
        bt = stack.getChildren(ctx_id).get()
        if bt:
            bt = stack.getContext(bt).get()
            for frame in bt:
                addr = frame.get(stacktrace.PROP_INSTRUCTION_ADDRESS) or 0
                area = lineNumbers.mapToSource(ctx_id, addr, addr + 1).get()
                print("Frame %d - CodeArea: %s" %
                      (frame.get(stacktrace.PROP_LEVEL), area))


def testSyncCommands(c):
    # simplified command execution
    ctl = sync.CommandControl(c)
    try:
        diag = ctl.Diagnostics
    except AttributeError:
        # no Diagnostics service
        return
    s = "Hello TCF World"
    r = diag.echo(s).getE()
    assert s == r
    pi = 3.141592654
    r = diag.echoFP(pi).getE()
    assert pi == r
    e = errors.ErrorReport("Test", errors.TCF_ERROR_OTHER)
    r = diag.echoERR(e.getAttributes()).getE()
    assert e.getAttributes() == r
    print("Diagnostic tests: " + str(diag.getTestList().getE()))

    for ctx_id in _suspended:
        print("Symbols: " + str(ctl.Symbols.list(ctx_id)))
    for ctx_id in _suspended:
        frame_ids = ctl.StackTrace.getChildren(ctx_id).get()
        if frame_ids:
            error, args = ctl.StackTrace.getContext(frame_ids)
            if not error:
                print("Stack contexts: " + str(args))
    try:
        ctl.Breakpoints
    except AttributeError:
        # no Breakpoints service
        return

    def gotBreakpoints(error, bps):
        print("Got breakpoint list: " + str(bps))
    ctl.Breakpoints.getIDs(onDone=gotBreakpoints)
    try:
        print(ctl.Processes.getChildren(None, False))
    except:
        pass  # no Processes service


def testTasks(c):
    if not _suspended:
        return
    from tcf.services import expressions  # @UnresolvedImport
    from tcf.util import task  # @UnresolvedImport

    def compute(expr, done=None):
        es = c.getRemoteService(expressions.NAME)
        if not es:
            done(Exception("No Expressions service"), None)
            return

        def doneCreate(token, error, ctx):
            if error:
                done(error, None)
                return

            def doneEval(token, error, val):
                done(error, val)
            es.evaluate(ctx.getID(), doneEval)
        es.create(_suspended[0], None, expr, doneCreate)
    t = task.Task(compute, "1+2*(3-4/2)", channel=c)
    val = t.get()
    print("Task result: " + str(val))


def testEvents(c):
    from tcf.util import event  # @UnresolvedImport
    recorder = event.EventRecorder(c)
    recorder.record("RunControl")
    ctl = sync.CommandControl(c)
    try:
        rc = ctl.RunControl
    except AttributeError:
        # no RunControl service
        return
    ctxs = rc.getChildren(None).get()
    if not ctxs:
        return
    ctx = ctxs[0]
    rc.resume(ctx, 0, 1, None).wait()
    print(recorder)
    rc.suspend(ctx).wait()
    print(recorder)
    recorder.stop()


def testDataCache(c):
    from tcf.util import cache  # @UnresolvedImport
    from tcf.services import runcontrol  # @UnresolvedImport
    if runcontrol.NAME not in _services:
        return

    class ContextsCache(cache.DataCache):
        def startDataRetrieval(self):
            rc = self._channel.getRemoteService(runcontrol.NAME)
            if not rc:
                self.set(None, Exception("No RunControl service"), None)
                return
            cache = self
            pending = []
            contexts = []

            class DoneGetChildren(runcontrol.DoneGetChildren):
                def doneGetChildren(self, token, error, context_ids):
                    pending.remove(token)
                    if error:
                        protocol.log(
                            "Error from RunControl.GetChildren", error)
                    else:
                        for c in context_ids:
                            contexts.append(c)
                            pending.append(rc.getChildren(c, self))
                    if len(pending) == 0:
                        cache.set(None, None, contexts)
            pending.append(rc.getChildren(None, DoneGetChildren()))
    contextsCache = ContextsCache(c)

    def done():
        print("ContextsCache is valid: " + str(contextsCache.getData()))
    protocol.invokeLater(contextsCache.validate, done)


def testProcesses(c):
    from tcf.services import processes, processes_v1  # @UnresolvedImport
    lock = threading.Condition()

    def processTest():
        proc = c.getRemoteService(processes_v1.NAME) or \
            c.getRemoteService(processes.NAME)
        if not proc:
            with lock:
                lock.notify()
            return

        class DoneGetChildren(processes.DoneGetChildren):
            def doneGetChildren(self, token, error, context_ids):
                if error:
                    protocol.log("Error from Processes.GetChildren", error)
                else:
                    print("Processes: " + str(context_ids))
                with lock:
                    lock.notify()
        proc.getChildren(None, False, DoneGetChildren())
    with lock:
        protocol.invokeLater(processTest)
        lock.wait(5)


def testFileSystem(c):
    cmd = sync.CommandControl(c)
    try:
        fs = cmd.FileSystem
    except AttributeError:
        # no FileSystem service
        return
    roots = fs.roots().get()
    print("FileSystem roots: " + str(roots))
    user = fs.user().get()
    print("User info: " + str(user))


def testMemory(c):
    lock = threading.Condition()
    from tcf.services import memory  # @UnresolvedImport

    def getContexts():
        mem = c.getRemoteService(memory.NAME)
        pending = []

        class DoneGetContext(memory.DoneGetContext):
            def doneGetContext(self, token, error, context):
                pending.remove(token)
                if error:
                    protocol.log("Error from Memory.getContext", error)
                else:
                    print(context)
                if len(pending) == 0:
                    with lock:
                        lock.notify()

        class DoneGetChildren(memory.DoneGetChildren):
            def doneGetChildren(self, token, error, context_ids):
                pending.remove(token)
                if error:
                    protocol.log("Error from Memory.GetChildren", error)
                else:
                    for c in context_ids:
                        _memory.append(c)
                        pending.append(mem.getContext(c, DoneGetContext()))
                        pending.append(mem.getChildren(c, self))
                if len(pending) == 0:
                    with lock:
                        lock.notify()
        pending.append(mem.getChildren(None, DoneGetChildren()))
    with lock:
        protocol.invokeLater(getContexts)
        lock.wait(5)


def testMemoryMap(c):
    if not _memory:
        return
    cmd = sync.CommandControl(c)
    try:
        mm = cmd.MemoryMap
    except AttributeError:
        # no MemoryMap service
        return
    map_id = _memory[0]
    lock = threading.Condition()
    from tcf.services import memorymap  # @UnresolvedImport

    def getMap():
        mm = c.getRemoteService(memorymap.NAME)

        class DoneGet(memorymap.DoneGet):
            def doneGet(self, token, error, mmap):
                if error:
                    protocol.log("Error from MemoryMap.get", error)
                else:
                    print(mmap)
                with lock:
                    lock.notify()
        mm.get(map_id, DoneGet())
    with lock:
        protocol.invokeLater(getMap)
        lock.wait(1)

    def setMap():
        mm = c.getRemoteService(memorymap.NAME)

        class DoneSet(memorymap.DoneSet):
            def doneSet(self, token, error):
                if error:
                    protocol.log("Error from MemoryMap.set", error)
                with lock:
                    lock.notify()
        mm.set(map_id, {memorymap.PROP_FILE_NAME: "/tmp/system.elf"},
               DoneSet())
    with lock:
        protocol.invokeLater(setMap)
        lock.wait(1)
    mmap = mm.get(map_id).get()
    print("Memory map: " + str(mmap))


def testPathMap(c):
    cmd = sync.CommandControl(c)
    try:
        pm = cmd.PathMap
    except AttributeError:
        # no PathMap service
        return
    lock = threading.Condition()
    from tcf.services import pathmap  # @UnresolvedImport

    def getMap():
        pm = c.getRemoteService(pathmap.NAME)

        class DoneGet(pathmap.DoneGet):
            def doneGet(self, token, error, mmap):
                if error:
                    protocol.log("Error from PathMap.get", error)
                else:
                    print(mmap)
                with lock:
                    lock.notify()
        pm.get(DoneGet())
    with lock:
        protocol.invokeLater(getMap)
        lock.wait(1)

    def setMap():
        pm = c.getRemoteService(pathmap.NAME)

        class DoneSet(pathmap.DoneSet):
            def doneSet(self, token, error):
                if error:
                    protocol.log("Error from PathMap.set", error)
                with lock:
                    lock.notify()
        pm.set({pathmap.PROP_SOURCE: "/tmp",
                pathmap.PROP_DESTINATION: "/home"}, DoneSet())
    with lock:
        protocol.invokeLater(setMap)
        lock.wait(1)
    mmap = pm.get().get()
    print("Path map: " + str(mmap))


def testSysMonitor(c):
    cmd = sync.CommandControl(c)
    try:
        sm = cmd.SysMonitor
    except AttributeError:
        # no SysMonotor service
        return
    lock = threading.Condition()
    from tcf.services import sysmonitor  # @UnresolvedImport
    processes = []

    def getProcesses():
        sm = c.getRemoteService(sysmonitor.NAME)
        pending = []

        class DoneGetChildren(sysmonitor.DoneGetChildren):
            def doneGetChildren(self, token, error, context_ids):
                pending.remove(token)
                if error:
                    protocol.log("Error from SysMonitor.getChildren", error)
                else:
                    class DoneGetContext(sysmonitor.DoneGetContext):
                        def doneGetContext(self, token, error, context):
                            pending.remove(token)
                            if error:
                                protocol.log(
                                    "Error from SysMonitor.getContext", error)
                            else:
                                processes.append(context)
                            if not pending:
                                with lock:
                                    lock.notify()
                    for ctx_id in context_ids:
                        pending.append(
                            sm.getContext(ctx_id, DoneGetContext()))
                if not pending:
                    with lock:
                        lock.notify()
        pending.append(sm.getChildren(None, DoneGetChildren()))
    with lock:
        protocol.invokeLater(getProcesses)
        lock.wait(5)
    print("%d processes found:" % len(processes))
    for p in processes:
        print(p)
        cmdl = sm.getCommandLine(p.getID()).get()
        if cmdl:
            print("Command line: " + str(cmdl))
        envp = sm.getEnvironment(p.getID()).get()
        print("Environment: " + str(envp))

if __name__ == '__main__':
    test()
