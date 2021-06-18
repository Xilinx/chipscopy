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

import threading

from . import protocol, channel
from .services import locator

_channels = []
_listeners = []
_transports = {}
_lock = threading.RLock()


class TransportProvider(object):
    """
    TransportProvider represents communication protocol that can be used to
    open TCF communication channels.
    Examples of transports are: TCP/IP, RS-232, USB.

    Client can implement this interface if they want to provide support for a
    transport that is not supported directly by the framework.
    """

    def getName(self):
        """
        Return transport name. Same as used as peer attribute,
        @see IPeer.ATTR_TRANSPORT_NAME
        @return transport name.
        """
        raise NotImplementedError("Abstract method")

    def openChannel(self, peer):
        """
        Open channel to communicate with this peer using this transport.
        Note: the channel can be not fully open yet when this method returns.
        It's state can be IChannel.STATE_OPENING.
        Protocol.Listener will be called when the channel will be opened or
        closed.
        @param peer - a IPeer object that describes remote end-point of the
                      channel.
        @return TCF communication channel.
        """
        raise NotImplementedError("Abstract method")


def addTransportProvider(transport):
    name = transport.getName()
    assert name
    with _lock:
        if _transports.get(name):
            raise Exception("Already registered: " + name)
        _transports[name] = transport


def removeTransportProvider(transport):
    name = transport.getName()
    assert name
    with _lock:
        if _transports.get(name) == transport:
            del _transports[name]


def openChannel(peer):
    name = peer.getTransportName()
    if not name:
        raise Exception("No transport name")
    with _lock:
        provider = _transports.get(name)
        if not provider:
            raise Exception("Unknown transport name: " + name)
    return provider.openChannel(peer)


def channelOpened(channel):
    assert channel not in _channels
    _channels.append(channel)
    for l in tuple(_listeners):
        try:
            l.onChannelOpen(channel)
        except Exception as x:
            import sys
            x.tb = sys.exc_info()[2]
            protocol.log("Exception in channel listener", x)


def channelClosed(channel, error):
    assert channel in _channels
    _channels.remove(channel)


def getOpenChannels():
    return _channels[:]


def addChannelOpenListener(listener):
    assert listener
    _listeners.append(listener)


def removeChannelOpenListener(listener):
    try:
        _listeners.remove(listener)
    except ValueError:
        pass  # ignore


class TCPTransportProvider(TransportProvider):
    def getName(self):
        return "TCP"

    def openChannel(self, p):
        assert self.getName() == p.getTransportName()
        from . import peer
        attrs = p.getAttributes()
        host = attrs.get(peer.ATTR_IP_HOST)
        port = attrs.get(peer.ATTR_IP_PORT)
        if not host:
            raise RuntimeError("No host name")
        from .channel.ChannelTCP import ChannelTCP
        return ChannelTCP(p, host, _parsePort(port))


class LoopbackTransportProvider(TransportProvider):
    def getName(self):
        return "loopback"

    def openChannel(self, p):
        assert self.getName() == p.getTransportName()
        from .channel.LoopbackChannel import LoopbackChannel
        return LoopbackChannel(p)


def _parsePort(port):
    if not port:
        raise Exception("No port number")
    try:
        return int(port)
    except Exception:
        raise RuntimeError("Invalid value of \"Port\" attribute. Must be " +
                           "decimal number.")


def sendEvent(service_name, event_name, data):
    """
    Transmit TCF event message.
    The message is sent to all open communication channels - broadcasted.

    This is internal API, TCF clients should use protocol.sendEvent().
    """
    for c in _channels:
        # Skip channels that are executing "redirect" command - STATE_OPENING
        if c.getState() == channel.STATE_OPEN:
            s = c.get_local_service(service_name)
            if s:
                c.sendEvent(s, event_name, data)


def sync(done):
    """
    Call back after TCF messages sent by this host up to this moment are
    delivered to their intended targets. This method is intended for
    synchronization of messages across multiple channels.

    Note: Cross channel synchronization can reduce performance and throughput.
    Most clients don't need cross channel synchronization and should not call
    this method.

    @param done will be executed by dispatch thread after communication
    messages are delivered to corresponding targets.

    This is internal API, TCF clients should use protocol.sync().
    """
    tokenSet = set()

    class DoneSync(locator.DoneSync):
        def doneSync(self, token):
            assert tokenSet.contains(token)
            tokenSet.remove(token)
            if len(tokenSet) == 0:
                done()
    done_sync = DoneSync()
    for c in _channels:
        if c.getState() == channel.STATE_OPEN:
            s = c.getRemoteService(locator.NAME)
            if s:
                tokenSet.append(s.sync(done_sync))
    if len(tokenSet) == 0:
        protocol.invokeLater(done)


# initialize TCP and Loopback transports
addTransportProvider(TCPTransportProvider())
addTransportProvider(LoopbackTransportProvider())
