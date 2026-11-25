# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
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

"""Outbound client-channel shim for the tcf-rs transport.

When the chipscope-pyrs server (running on the Rust `tcf_rs` bridge) connects an
outbound peer such as hw_server, the Rust Locator hands the new client channel to
the Python side via `tcf_rs.set_peer_connected_listener`. This module wraps that
bridge channel in an object that looks enough like a `chipscopy.tcf` channel for
the existing remote-service proxies to work: `getRemoteService(...)` returns
proxies built by `services.onChannelOpened`, and their `Command`s route through
`sendCommand` → the bridge's byte-level `send_command`.

Only imported when `tcf_rs` is present (i.e. inside chipscope-pyrs); standalone
chipscopy never loads it.
"""

from . import protocol
from . import services
from . import _parse_params
from . import peer as _peer
from .peer import Peer
from .channel import Token, fromJSONSequence, toJSONSequence
from .channel import STATE_OPEN

# All open outbound channels (returned by protocol.getOpenChannels()).
open_channels = []


class RsChannel(object):
    """A `chipscopy.tcf` channel backed by a Rust `tcf_rs` client channel."""

    #: The transport applies the xargs binary side-channel itself, so callers
    #: must not. Read by `services.send_xicom_command`, which dispatches on the
    #: channel exactly as `Command` does for toJSONSequence.
    xargs_in_transport = True

    def __init__(self, bridge_channel):
        self._bridge = bridge_channel
        self.url = bridge_channel.url
        self.services = list(bridge_channel.services)
        self.remote_service_by_name = {}
        self.remote_service_by_class = {}
        self.event_listeners = {}
        self.channel_listeners = []
        self.state = STATE_OPEN
        try:
            params = _parse_params(self.url)
            params.setdefault(_peer.ATTR_ID, self.url)
            self.remote_peer = Peer(params)
        except Exception:
            self.remote_peer = Peer({_peer.ATTR_ID: self.url})
        self.local_peer = Peer({})
        # setServiceProxy() (called from proxy constructors) only works while the
        # channel is notifying open; mimic AbstractChannel's guard.
        self.notifying_channel_opened = True
        try:
            services.onChannelOpened(self, self.services, self.remote_service_by_name)
        finally:
            self.notifying_channel_opened = False
        self.__make_service_by_class_map()

    # --- service lookup -----------------------------------------------------

    def getRemoteServices(self):
        return list(self.remote_service_by_name.keys())

    def getRemoteService(self, cls_or_name):
        if isinstance(cls_or_name, str):
            return self.remote_service_by_name.get(cls_or_name)
        return self.remote_service_by_class.get(cls_or_name)

    def setServiceProxy(self, service_interface, service_proxy):
        if not self.notifying_channel_opened:
            raise Exception("setServiceProxy() can be called only from channel "
                            "open call-back")
        proxy = self.remote_service_by_name.get(service_proxy.getName())
        if not isinstance(proxy, services.GenericProxy):
            raise Exception("Proxy already set")
        if self.remote_service_by_class.get(service_interface):
            raise Exception("Proxy already set")
        self.remote_service_by_class[service_interface] = service_proxy
        self.remote_service_by_name[service_proxy.getName()] = service_proxy

    def getRemotePeer(self):
        return self.remote_peer

    def getLocalPeer(self):
        return self.local_peer

    # --- command / event I/O (byte-level via the bridge) --------------------

    # Object-level codec: Command encodes/decodes via these (channel-dispatched).
    # Rust does the wire codec, so here they're identity pass-throughs.
    def toJSONSequence(self, args):
        return args

    def fromJSONSequence(self, data):
        return data

    def sendCommand(self, service, name, args, listener):
        assert protocol.isDispatchThread()
        token = Token()

        def done(error, data):
            if error is None:
                listener.result(token, data)
            else:
                listener.terminated(token, Exception("TCF error: %r" % (error,)))

        # `args` is already a Python sequence (Command called our toJSONSequence,
        # an identity); the bridge encodes it to the wire in Rust, applying the
        # xargs side-channel when the command is a xicom one.
        self._bridge.send_command(str(service), name, args, done,
                                  xicom=getattr(listener, "xicom", False))
        return token

    def sendEvent(self, service, name, args):
        # Outbound (client→peer) events are not used by the server services;
        # broadcast support lives in transport.sendEvent for the inbound side.
        raise Exception("RsChannel.sendEvent is not supported")

    def addEventListener(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        handlers = getattr(listener, "_event_handlers", None)
        if handlers and svc_name not in self.event_listeners:
            for ename, meth in handlers.items():
                hname = meth.__name__

                def _dispatch(args, hname=hname):
                    # `args` is already the decoded event payload list (the bridge
                    # decoded it in Rust).
                    for l in self.event_listeners.get(svc_name, []):
                        h = getattr(l, hname, None)
                        if h:
                            h(args)

                # Events carry xargs; Rust splices before the handler runs,
                # which makes the proxies' own from_xargs a no-op.
                self._bridge.subscribe(svc_name, ename, _dispatch, xicom=True)
        self.event_listeners.setdefault(svc_name, []).append(listener)

    def removeEventListener(self, service, listener):
        lst = self.event_listeners.get(str(service))
        if lst and listener in lst:
            lst.remove(listener)

    def addChannelListener(self, listener):
        assert protocol.isDispatchThread()
        self.channel_listeners.append(listener)

    def removeChannelListener(self, listener):
        if listener in self.channel_listeners:
            self.channel_listeners.remove(listener)

    def close(self):
        self._bridge.close()

    def terminate(self, error):
        self._bridge.close()

    def __make_service_by_class_map(self):
        for service in list(self.remote_service_by_name.values()):
            self.remote_service_by_class[service.__class__] = service
            for clazz in service.__class__.__bases__:
                if clazz == services.Service:
                    continue
                self.remote_service_by_class[clazz] = service


def on_peer_connected(bridge_channel):
    """Called (on the dispatch thread) by the Rust Locator when an outbound peer
    connects. Builds the shim, tracks it, and fires channel-open listeners."""
    channel = RsChannel(bridge_channel)
    open_channels.append(channel)
    try:
        from . import transport
        transport.channelOpened(channel)
    except Exception as x:
        protocol.log("RsChannel: channelOpened notification failed", x)
    return channel


def on_peer_disconnected(url):
    """Called (on the dispatch thread) when an outbound channel closes. Fires the
    channel's listeners (e.g. dm's ManagerChannelListener → manager teardown) and
    removes it from the open-channel set / transport registry."""
    for channel in list(open_channels):
        if channel.url != url:
            continue
        open_channels.remove(channel)
        for listener in list(channel.channel_listeners):
            try:
                listener.onChannelClosed(None)
            except Exception as x:
                protocol.log("RsChannel: onChannelClosed listener failed", x)
        try:
            from . import transport
            transport.channelClosed(channel, None)
        except Exception as x:
            protocol.log("RsChannel: channelClosed notification failed", x)
        break
