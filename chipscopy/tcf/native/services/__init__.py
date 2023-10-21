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

from typing import NewType
import threading
import inspect
import importlib
from .. import protocol
from ...channel import *
import pytcf

_providers = []
_lock = threading.RLock()

TokenType = NewType("TokenType", Token)


class TCFError(Exception):
    pass


class DoneHWCommand(object):
    """Client call back interface for generic commands."""
    def doneHW(self, token, error, args):
        """Called when memory operation command command is done.
        :param token: Command handle.
        :param error: Error object or **None**.
        """
        pass

    def __call__(self, token, error, args):
        return self.doneHW(token, error, args)


class ServiceProvider(object):
    """Clients can implement this abstract class if they want to provide
    implementation of a local service or remote service proxy.
    """

    def get_local_service(self, channel):
        pass

    def get_service_proxy(self, channel, service_name):
        pass


def add_service_provider(provider):
    with _lock:
        _providers.append(provider)


def removeServiceProvider(provider):
    with _lock:
        _providers.remove(provider)


def onChannelCreated(channel, services_by_name):
    with _lock:
        for provider in _providers:
            try:
                arr = provider.get_local_service(channel)
                if not arr:
                    continue
                for service in arr:
                    if service.getName() in services_by_name:
                        continue
                    services_by_name[service.getName()] = service
            except Exception as x:
                protocol.log("Error calling TCF service provider", x)


def onChannelOpened(channel, service_names, services_by_name):
    with _lock:
        for name in service_names:
            for provider in _providers:
                try:
                    service = provider.get_service_proxy(channel, name)
                    if not service:
                        continue
                    services_by_name[name] = service
                    break
                except Exception as x:
                    protocol.log("Error calling TCF service provider", x)
            if name in services_by_name:
                continue
            services_by_name[name] = GenericProxy(channel, name)


def getServiceManagerID():
    # In current implementation ServiceManager is a singleton,
    # so its ID is same as agent ID.
    return protocol.getAgentID()


class GenericCallback(object):

    def __init__(self, callback):
        self.callback = callback

    def __getattr__(self, attr):
        if attr.startswith("done"):
            return self.callback


class Service(object):
    """TCF service base class."""
    def getName(self):
        """Abstract method to get the service name.

        :returns: This service name
        """
        raise NotImplementedError("Abstract method")

    def __init__(self, channel):
        self.channel = channel

    def __str__(self):
        """TCF service string representation.

        :returns: The name of the service.
        """
        return self.getName()

    def _makeCallback(self, done):
        """Turn *done* into a callable.

        If *done* is already a :class:`collections.Callable`, it is returned
        as is, else, it is made callable, and returned.

        :param done: The item to make callable.

        :returns: The callable value of *done*
        """
        if inspect.isfunction(done) or inspect.ismethod(done):
            return GenericCallback(done)
        return done

    def send_command(self, cmd, args, done=None, progress=None):
        if not pytcf.is_dispatch_thread():
            return pytcf.post_event_and_wait(self.send_command, cmd, args, done, progress)
        token = None

        def reply_handler(chan, error):
            if not error:
                data = pytcf.read_command_args(chan)
                error = data[0] if len(data) > 0 else error
                data = data[1:] if len(data) > 1 else ()
            else:
                data = ()

            if done:
                done(token, error, data)

        def progress_handler(chan):
            data = pytcf.read_command_args(chan)
            if progress:
                progress(token, data)

        token = pytcf.send_command(
            self.channel,
            self.getName(),
            cmd,
            reply_handler if done else None,
            progress_handler if progress else None)
        pytcf.write_command_args(self.channel, args)
        return token

    def send_xicom_command(self, cmd, args, done, progress=None):
        if not pytcf.is_dispatch_thread():
            return pytcf.post_event_and_wait(self.send_command, cmd, args, done, progress)
        token = None

        def reply_handler(chan, error):
            if not error:
                data = pytcf.read_command_args(chan)
                error = data[0] if len(data) > 0 else error
                if isinstance(error, dict) and 'Format' in error:
                    e = Exception(error['Format'])
                    try:
                        mod = importlib.import_module(error['Module'])
                        cls = getattr(mod, error["Class"])
                        e = cls(f"TCF Error: {self.getName()} {cmd}: {error['Format']}")
                    except Exception:
                        pass
                    error = e
                data = data[1:] if len(data) > 1 else ()
                if data and len(data) == 1:
                    data = data[0]
            else:
                data = ()

            if done:
                done(token, error, data)

        def progress_handler(chan):
            data = pytcf.read_command_args(chan)
            if progress:
                progress(token, data)

        token = pytcf.send_command(
            self.channel,
            self.getName(),
            cmd,
            reply_handler if done else None,
            progress_handler if progress else None)
        pytcf.write_command_args(self.channel, args)
        return token

    def send_old_xicom_command(self, cmd, args, done):
        if not pytcf.is_dispatch_thread():
            return pytcf.post_event_and_wait(self.send_command, cmd, args, done)
        token = None

        def reply_handler(chan, error):
            if not error:
                data = pytcf.read_command_args(chan)
                # error = data[0] if len(data) > 0 else error
                # data = data[1:] if len(data) > 1 else ()
            else:
                data = ()

            if done:
                done(token, error, data)

        token = pytcf.send_command(
            self.channel,
            self.getName(),
            cmd,
            reply_handler if done else None,
            None)
        pytcf.write_command_args(self.channel, args, True)
        return token

    send_old_command = send_old_xicom_command


class ServiceSync(object):
    def __init__(self, channel, service_name, raise_on_error=False):
        self.service_name = service_name
        self.chan = channel
        self.result = None
        self.raise_on_error = raise_on_error

        #services = protocol.invokeAndWait(self.chan.getRemoteServices)
        # if service_name not in services:
        #     raise Exception('No service {} found'.format(service_name))

    def __getattr__(self, attr):
        return CommandWrapper(self, attr)

    def _doneCommand(self, token, error, args):
        self.result = CommandResult(token, error, args)

    def invoke(self, command, *args, **kwargs):
        cond = threading.Condition()
        self.result = None

        def callCommand(command, *args, **kwargs):
            serv = self.chan.getRemoteService(self.service_name)

            def doneHW(token, error, args):
                self._doneCommand(token, error, args)
                with cond:
                    cond.notify()

            try:
                kwargs['done'] = doneHW
                f = getattr(serv, command, None)
                f(*args, **kwargs)
            except TypeError as e:
                error = '{} service {} error: {}'.format(serv, command, str(e))
                self._doneCommand(Token(), error, [])
                with cond:
                    cond.notify()

        if protocol.isDispatchThread():
            callCommand(command, *args, **kwargs)
        else:
            with cond:
                protocol.invokeLater(callCommand, command, *args, **kwargs)
                # When inside the debugger wait longer, don't time out.
                # todo: move this feature to the command line???
                cond.wait(None if __debug__ else 60)

        if self.raise_on_error and self.result and self.result.error:
            if isinstance(self.result.error, Exception):
                raise self.result.error
            else:
                raise Exception(self.service_name + ':' + command + ': ' + str(self.result.error))
        return self.result


class CommandResult(object):
    def __init__(self, token, error, args):
        self.token = token
        self.error = error
        # unwrap result if only one element
        # if args and len(args) == 1 and \
        #         not isinstance(args, dict):
        #     args = args[0]
        self.args = args

    def __str__(self):
        if self.error:
            return "[%s] error: %s" % (self.token.id, self.error)
        return "[%s] result: %s" % (self.token.id, self.args)
    __repr__ = __str__

    def __iter__(self):
        yield self.error
        yield self.args

    def get(self, key=None):
        if key:
            return self.args.get(key)
        return self.args


class CommandWrapper(object):
    def __init__(self, control, command):
        self._control = control
        self._command = command

    def __call__(self, *args, **kwargs):
        return self._control.invoke(self._command, *args, **kwargs)


class GenericProxy(Service):
    """Objects of GenericProxy class represent remote services, which don't
    have a proxy class defined for them.

    Clients still can use such services, but framework will not provide
    service specific utility methods for message formatting and parsing.
    """

    def __init__(self, channel, name):
        self.__channel = channel
        self.name = name

    def getName(self):
        return self.name

    def getChannel(self):
        return self.__channel
class DefaultServiceProvider(ServiceProvider):
    package_base = str(__package__) + ".remote"

    def get_local_service(self, channel):
        # TODO DiagnosticsService
        # return [DiagnosticsService(channel)]
        return []

    def get_service_proxy(self, channel, service_name):
        # package_base = str(__package__) + "...services.remote"
        package_base = "chipscopy.tcf.services.remote"
        service = None
        try:
            # Xicom_v1.XX special case
            if 'Xicom_v1' in service_name:
                service_name = "Xicom"
            clsName = service_name + "Proxy"
            clsName = clsName.replace('.', '_')
            package = package_base + "." + clsName
            clsModule = __import__(package, fromlist=[clsName],
                                   globals=globals())
            cls = clsModule.__dict__.get(clsName)
            service = cls(channel)
            # assert service_name == service.getName()
        except ImportError:
            pass
        except Exception as x:
            protocol.log("Cannot instantiate service proxy for " +
                         service_name, x)
        return service


add_service_provider(DefaultServiceProvider())
