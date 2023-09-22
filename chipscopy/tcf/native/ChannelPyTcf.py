import pytcf
from .. import protocol
from .. import services
from ..peer import Peer
from .. import _parse_params
from ..channel.AbstractChannel import AbstractChannel, ChannelListener
from ..channel import STATE_OPEN

_listeners_active = False


def _channel_closed(ci: pytcf.ChannelInfo):
    if hasattr(ci, "outer"):
        chan = ci.outer
        for listener in chan.channel_listeners:
            listener.onChannelClosed(None)


class ChannelPyTcf(AbstractChannel, pytcf.ChannelInfo):
    def __init__(self, chan: pytcf.ChannelInfo = None):
        pytcf.ChannelInfo.__init__(self, chan)
        self.channel_listeners = []
        self.remote_service_by_class = {}
        self.local_service_by_name = {}
        self.remote_service_by_name = {}
        self.event_listeners = {}
        self.linked_channels = set()
        self.remote_peer = Peer(_parse_params(self.url))
        self.local_peer = Peer({})
        self.state = STATE_OPEN
        services.onChannelOpened(self, self.services, self.remote_service_by_name)
        self.__makeServiceByClassMap(self.remote_service_by_name, self.remote_service_by_class)

    # @property
    # def is_closed(self):
    #     return self.ci.is_closed

    def add_linked_channel(self, chan):
        self.linked_channels.add(chan)

    def sendCommand(self, service, name, args, listener):
        s = self.remote_service_by_name.get(service)

        def done(token, error, args):
            listener.done(error, args)

        listener.token = s.send_command(name, args, done)

    def sendResult(self, token, args):
        if len(args) > 1:
            pytcf.write_response_args(token, self, args[0], args[1:])

    def sendProgress(self, token, args):
        pytcf.write_progress_args(token, self, args)

    def addChannelListener(self, listener: ChannelListener):
        global _listeners_active
        assert protocol.isDispatchThread()
        assert listener
        if not _listeners_active:
            pytcf.add_channel_close_listener(_channel_closed)
            _listeners_active = True
        self.channel_listeners.append(listener)

    def removeChannelListener(self, listener):
        assert protocol.isDispatchThread()
        self.channel_listeners.remove(listener)

    def _add_event_listener(self, service, name, handler_name):
        def event(chan):
            args = pytcf.read_command_args(chan)
            for listener in self.event_listeners[service]:
                handler = getattr(listener, handler_name)
                if handler:
                    handler(args)
        pytcf.add_event_handler(self, service, name, event)

    def addEventListener(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        listener.svc_name = svc_name
        lst = self.event_listeners.get(svc_name)
        if lst is None:
            lst = []
            if hasattr(listener, "_event_handlers"):
                for k, v in listener._event_handlers.items():
                    self._add_event_listener(svc_name, k, v.__name__)
        lst.append(listener)
        self.event_listeners[svc_name] = lst

    def removeEventListener(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        lst = self.event_listeners.get(svc_name)
        if not lst:
            return
        for i in range(len(lst)):
            if lst[i] is listener:
                del lst[i]
                return

    def close(self):
        pytcf.disconnect_channel(self)

    def terminate(self, error):
        pytcf.disconnect_channel(self)

    def getLocalPeer(self):
        assert protocol.isDispatchThread()
        return ""

    def get_local_services(self):
        assert protocol.isDispatchThread()
        return list()

    def getRemoteServices(self):
        assert protocol.isDispatchThread()
        return self.services

    def read(self):
        pass

    def writeByte(self, n):
        pass

    def flush(self):
        pass

    def stop(self):
        pass

    def __makeServiceByClassMap(self, by_name, by_class):
        for service in list(by_name.values()):
            by_class[service.__class__] = service
            for clazz in service.__class__.__bases__:
                if clazz == services.Service:
                    continue
                by_class[clazz] = service

pytcf.set_channel_class(ChannelPyTcf)
