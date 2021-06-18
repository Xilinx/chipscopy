# *****************************************************************************
# * Copyright (c) 2011, 2014, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

import socket

from .. import compat
from .. import protocol
from .StreamChannel import StreamChannel


class ChannelTCP(StreamChannel):
    """ChannelTCP is a channel implementation that works on top of TCP sockets
    as a transport."""

    def __init__(self, remote_peer, host, port, client_socket = None):
        super(ChannelTCP, self).__init__(remote_peer)
        self.closed = False
        self.started = False
        channel = self

        class CreateSocket(object):
            def __call__(self):
                nonlocal host
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # NOTE - Useful for when on VPN.
                    if host.upper() == socket.gethostname().upper():
                        host = "localhost"

                    sock.connect((host, port))
                    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    channel.socket = sock
                    channel._onSocketConnected(None)
                except Exception as x:
                    channel._onSocketConnected(x)
        if not client_socket:
            protocol.invokeLater(CreateSocket())
        else:
            channel.socket = client_socket
            protocol.invokeLater(self._onSocketConnected, None)

    def _onSocketConnected(self, x):
        if x:
            self.terminate(x)
            self.closed = True
        if self.closed:
            try:
                if hasattr(self, 'socket') and self.socket:
                    self.socket.close()
            except socket.error as y:
                protocol.log("Cannot close socket", y)
        else:
            self.started = True
            self.start()

    def get(self):
        if self.closed:
            return -1
        try:
            return ord(self.socket.recv(1))
        except socket.error as x:
            if self.closed:
                return -1
            raise x

    def getBuf(self, buf):
        if self.closed:
            return -1
        try:
            return self.socket.recv_into(buf)
        except TypeError:
            # see http://bugs.python.org/issue7827
            # use super implementation
            self.getBuf = super(ChannelTCP, self).getBuf
            return self.getBuf(buf)
        except (ConnectionResetError, ConnectionAbortedError):
            protocol.invokeLater(self.close)
            return -1
        except socket.error as x:
            if self.closed:
                return -1
            raise x

    def str2bytes(self, data):
        if isinstance(data, compat.strings):
            return bytearray([ord(x) for x in data])
        elif isinstance(data, int):
            return bytearray([data])
        return data

    def put(self, b):
        if self.closed:
            return
        s = self.str2bytes(b)
        self.socket.send(s)

    def putBuf(self, buf):
        if self.closed:
            return
        if isinstance(buf, (bytes, bytearray)):
            s = buf
        else:
            s = self.str2bytes(buf)
        self.socket.sendall(s)

    def flush(self):
        pass

    def stop(self):
        self.closed = True
        if self.started:
            self.socket.close()
