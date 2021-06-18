# Copyright 2021 Xilinx, Inc.
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

"""
ChipScope Client Overview

Server Connection
^^^^^^^^^^^^^^^^^
.. automethod:: chipscope.client.connect

"""

import threading
from chipscopy.dm import request
from chipscopy.tcf import protocol, channel, peer
from chipscopy.tcf.channel.AbstractChannel import AbstractChannel
from chipscopy.utils.logger import log
from .server_info import ServerInfo
from .util import process_param_str, sync_call, parse_params
from chipscopy import proxies


proxies.init()

_connections = {}
_lock = threading.Lock()


def _setup_channel_listener(params, chan: channel):
    with _lock:
        _connections[params] = chan

    class DisconnectListener(channel.ChannelListener):
        def onChannelClosed(self, error):
            with _lock:
                for peer, c in _connections.items():
                    if c == chan and c.getState() == channel.STATE_CLOSED:
                        log.client.info(f"Channel {peer} closed")
                        _connections.pop(peer)
                        break

    chan.addChannelListener(DisconnectListener())


def connect_channel(params, done: request.DoneCallback = None):
    if not protocol.getEventQueue():
        protocol.startEventQueue()
    wait = ~protocol.isDispatchThread() and not done
    p = peer.TransientPeer(parse_params(process_param_str(params)))
    if wait:
        c = sync_call(_openChannel, p)
    else:
        c = protocol.invokeAndWait(_openChannel, p, done)
    return c


def connect(url: str, done: request.DoneCallback = None) -> ServerInfo:
    """
    Connects to a ChipScope or Hardware server

    :param url: A url in the form of "<hostname or IP>:<port>"
    :param done: Done callback if called asynchronously
    :return: Server Info object
    """

    def done_connect(token, error, result):
        done(token, error, ServerInfo(result))

    if done:
        return connect_channel(url, done_connect)
    return ServerInfo(connect_channel(url))


# @DEPRECATED
def connect_xicom(url):
    url = process_param_str(url)
    c = connect_channel(url)
    return ServerInfo(c)


def disconnect(server):
    chan = None
    if isinstance(server, ServerInfo):
        chan = server.channel
    elif isinstance(server, AbstractChannel):
        chan = server
    if chan:
        protocol.invokeAndWait(chan.close)


def connections():
    with _lock:
        return list(_connections.keys())


def get_channel(peer):
    with _lock:
        return _connections.get(peer)


def _openChannel(p, done=None):
    assert protocol.isDispatchThread()
    log.client.debug(f"Connecting to {p.getID()}")
    c = p.openChannel()
    if done is None:
        return c

    class ChannelListener(channel.ChannelListener):
        def onChannelOpened(self):
            log.client.info(f"Connected to {p.getID()}")
            c.removeChannelListener(self)
            _setup_channel_listener(c.remote_peer.getID(), c)
            done(c, None, c)

        def onChannelClosed(self, error):
            log.client.error(f"Failed to connect to {p.getID()}")
            done(c, error, None)

    c.addChannelListener(ChannelListener())
