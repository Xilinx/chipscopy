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

"""
TCF - Target Communication Framework
"""

import types

from . import compat, protocol, peer, channel
from .util import task

__all__ = ('connect', 'peers')


def connect(params, wait=True):
    """Connect to peer. Argument is a string of the form
    <transport>:<host>:<port>, e.g. "TCP:127.0.0.1:1534".
    """
    if isinstance(params, compat.strings):
        params = _parse_params(params)
    elif isinstance(params, dict):
        raise TypeError("Expected string or dict")
    p = peer.TransientPeer(params)
    if wait:
        c = task.Task(_openChannel, p).get()
    else:
        c = protocol.invokeAndWait(p.openChannel)
    return c


def peers():
    "Return list of discovered remote peers"
    locator = protocol.getLocator()
    if locator:
        return protocol.invokeAndWait(locator.getPeers)


def _openChannel(p, done=None):
    assert protocol.isDispatchThread()
    c = p.openChannel()
    if done is None:
        return

    class ChannelListener(channel.ChannelListener):
        def onChannelOpened(self):
            c.removeChannelListener(self)
            done(None, c)

        def onChannelClosed(self, error):
            done(error, None)
    c.addChannelListener(ChannelListener())


def process_param_str(params, default_port="3121"):
    parts = params.split(":", 3)
    if len(parts) < 3:
        parts.insert(0, "TCP")
    if len(parts) < 3:
        parts.append(default_port)
    return ":".join(parts)


def _parse_params(paramStr):
    args = process_param_str(paramStr).split(":")
    if len(args) != 3:
        raise ValueError("Expected format: <transport>:<host>:<port>")
    transp, host, port = args
    return {
        peer.ATTR_ID: paramStr,
        peer.ATTR_IP_HOST: host,
        peer.ATTR_IP_PORT: port,
        peer.ATTR_TRANSPORT_NAME: transp
    }
