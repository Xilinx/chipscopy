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

from .. import locator
from ... import protocol, peer, channel
from ...channel.Command import Command


class Peer(peer.TransientPeer):
    def __init__(self, parent, attrs):
        super(Peer, self).__init__(attrs)
        self.parent = parent

    def openChannel(self):
        assert protocol.isDispatchThread()
        c = self.parent.openChannel()
        c.redirect(self.getID())
        return c


class ChannelEventListener(channel.EventListener):
    def __init__(self, proxy):
        self.proxy = proxy
        self.channel = proxy.channel

    def event(self, name, data):
        if self.proxy.peers is None:
            return  # peers not synchronized yet

        try:
            args = channel.fromJSONSequence(data)
            if name == "peerAdded":
                assert len(args) == 1
                _peer = Peer(self.channel.getRemotePeer(), args[0])
                if self.proxy.peers.get(_peer.getID()):
                    protocol.log("Invalid peerAdded event", Exception())
                    return
                self.proxy.peers[_peer.getID()] = _peer
                for l in self.proxy.listeners:
                    try:
                        l.peerAdded(_peer)
                    except Exception as x:
                        protocol.log("Unhandled exception in Locator listener",
                                     x)
            elif name == "peerChanged":
                assert len(args) == 1
                m = args[0]
                if not m:
                    raise Exception("Locator service: invalid peerChanged " +
                                    "event - no peer ID")
                _peer = self.proxy.peers.get(m.get(peer.ATTR_ID))
                if not _peer:
                    return
                self.proxy.peers[_peer.getID()] = _peer
                for l in self.proxy.listeners:
                    try:
                        l.peerChanged(_peer)
                    except Exception as x:
                        protocol.log("Unhandled exception in Locator listener",
                                     x)
            elif name == "peerRemoved":
                assert len(args) == 1
                peerID = args[0]
                _peer = self.proxy.peers.get(peerID)
                if not _peer:
                    return
                del self.proxy.peers[peerID]
                for l in self.proxy.listeners:
                    try:
                        l.peerRemoved(peerID)
                    except Exception as x:
                        protocol.log("Unhandled exception in Locator listener",
                                     x)
            elif name == "peerHeartBeat":
                assert len(args) == 1
                peerID = args[0]
                _peer = self.proxy.peers.get(peerID)
                if not _peer:
                    return
                for l in self.proxy.listeners:
                    try:
                        l.peerHeartBeat(peerID)
                    except Exception as x:
                        protocol.log("Unhandled exception in Locator listener",
                                     x)
            else:
                raise IOError("Locator service: unknown event: " + name)
        except Exception as x:
            import sys
            x.tb = sys.exc_info()[2]
            self.channel.terminate(x)


class LocatorProxy(locator.LocatorService):
    def __init__(self, channel):
        self.channel = channel
        self.peers = None  # not yet synchronized
        self.listeners = []
        self.get_peers_done = False
        self.event_listener = ChannelEventListener(self)
        channel.addEventListener(self, self.event_listener)

    def getAgentID(self, done):
        done = self._makeCallback(done)
        service = self

        class GetAgentIDCommand(Command):
            def __init__(self):
                super(GetAgentIDCommand, self).__init__(service.channel,
                                                        service, "getAgentID",
                                                        None)

            def done(self, error, args):
                agentID = None
                if not error:
                    assert len(args) == 2
                    error = self.toError(args[0])
                    agentID = args[1]
                done.doneGetAgentID(self.token, error, agentID)
        return GetAgentIDCommand().token

    def getPeers(self):
        assert protocol.isDispatchThread()
        return self.peers  # None if not synchronized yet

    def redirect(self, _peer, done):
        done = self._makeCallback(done)
        service = self

        class RedirectCommand(Command):
            def __init__(self):
                super(RedirectCommand, self).__init__(service.channel, service,
                                                      "redirect", [_peer])

            def done(self, error, args):
                if not error:
                    assert len(args) == 1
                    error = self.toError(args[0])

                    if not error and service.peers:
                        # The redirect was a success. Invalidate all the peers
                        # already detected.

                        for peerId in list(service.peers.keys()):
                            del service.peers[peerId]
                            for l in service.listeners:
                                try:
                                    l.peerRemoved(peerId)
                                except Exception as x:
                                    protocol.log("Unhandled exception in "
                                                 "Locator listener", x)

                        assert len(service.peers) == 0
                        service.peers = None
                        service.get_peers_done = False

                done.doneRedirect(self.token, error)
        return RedirectCommand().token

    def sync(self, done):
        done = self._makeCallback(done)
        service = self

        class SyncCommand(Command):
            def __init__(self):
                super(SyncCommand, self).__init__(service.channel, service,
                                                  "sync", None)

            def done(self, error, args):
                if error:
                    service.channel.terminate(error)
                done.doneSync(self.token)
        return SyncCommand().token

    def addListener(self, listener):
        self.listeners.append(listener)
        if not self.get_peers_done:
            service = self

            class GetPeersCommand(Command):
                def __init__(self):
                    super(GetPeersCommand, self).__init__(service.channel,
                                                          service, "getPeers",
                                                          None)

                def done(self, error, args):
                    if not error:
                        assert len(args) == 2
                        error = self.toError(args[0])
                    if error:
                        protocol.log("Locator error", error)
                        return
                    c = args[1]
                    service.peers = {}  # peers list synchronized
                    if c:
                        for m in c:
                            peerID = m.get(peer.ATTR_ID)
                            if service.peers.get(peerID):
                                continue
                            _peer = Peer(service.channel.getRemotePeer(), m)
                            service.peers[peerID] = _peer
                            for l in service.listeners:
                                try:
                                    l.peerAdded(_peer)
                                except Exception as x:
                                    protocol.log("Unhandled exception in " +
                                                 "Locator listener", x)
            GetPeersCommand()
            self.get_peers_done = True

    def removeListener(self, listener):
        self.listeners.remove(listener)

    def get_remote_peers(self, done):
        return self.send_command("getPeers", None, done)

    def get_remote_channels(self, done):
        return self.send_command("getChannels", None, done)

    def connect_remote_peer(self, peer_attrib, done):
        return self.send_command("connectPeer", (peer_attrib,), done)

    def disconnect_remote_peer(self, peer_attrib, done):
        return self.send_command("disconnectPeer", (peer_attrib,), done)
