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

from .. import protocol, errors, services
from ..channel import Token, toJSONSequence, fromJSONSequence, dumpJSONObject


class Command(object):
    """This is utility class that helps to implement sending a command and
    receiving command result over TCF communication channel.

    The class uses JSON to encode command arguments and to decode result data.

    The class also provides support for TCF standard error report encoding.

    Clients are expected to subclass <code>Command</code> and override
    <code>done</code> method.

    Note: most clients don't need to handle protocol commands directly and can
    use service APIs instead. Service API does all command encoding/decoding
    for a client.

    Typical usage example:

    def getContext(self, id, done):
        class GetContextCommand(Command):
            def done(self, error, args):
                ctx = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    if args[1]: ctx = Context(args[1])
                done.doneGetContext(self.token, error, ctx)
         command = GetContextCommand(self.channel, self, "getContext", [id])
         return command.token
    """
    __done = False

    def __init__(self, channel, service, command, args):
        if isinstance(service, services.Service):
            service = service.getName()
        self.service = service
        self.command = command
        self.args = args
        t = None
        try:
            # TODO zero_copy
            # zero_copy = channel.isZeroCopySupported()
            t = channel.sendCommand(service, command, toJSONSequence(args),
                                    self)
        except Exception as y:
            t = Token()
            protocol.invokeLater(self._error, y)
        self.token = t

    def _error(self, error):
        assert not self.__done
        self.__done = True
        self.done(error, None)

    def progress(self, token, data):
        assert self.token is token
        error = None
        args = None
        try:
            args = fromJSONSequence(data)
        except Exception as e:
            error = e
        assert not self.__done
        self.progress_update(error, args)

    def result(self, token, data):
        assert self.token is token
        error = None
        args = None
        try:
            args = fromJSONSequence(data)
        except Exception as e:
            error = e
        assert not self.__done
        self.__done = True
        self.done(error, args)

    def terminated(self, token, error):
        assert self.token is token
        assert not self.__done
        self.__done = True
        self.done(error, None)

    def done(self, error, args):
        raise NotImplementedError("Abstract method")

    def getCommandString(self):
        buf = str(self.service) + ' ' + str(self.command)
        if self.args is not None:
            i = 0
            for arg in self.args:
                if i == 0:
                    buf += " "
                else:
                    buf += ", "
                i += 1
                try:
                    buf += dumpJSONObject(arg)
                except Exception as x:
                    # Exception.message does not exist in python3, better use
                    # str(Exception)
                    buf += '***' + str(x) + '***'
        return buf

    def toError(self, data, include_command_text=True):
        if not isinstance(data, dict):
            return None
        errMap = data
        bf = 'TCF error report:\n'
        if include_command_text:
            cmd = self.getCommandString()
            if len(cmd) > 120:
                cmd = cmd[:120] + "..."
            bf += 'Command: ' + str(cmd)
        bf += errors.appendErrorProps(errMap)
        return errors.ErrorReport(bf, errMap)
