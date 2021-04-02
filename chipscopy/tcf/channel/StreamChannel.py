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

from .. import compat
from .AbstractChannel import AbstractChannel, EOS, EOM

ESC = 3


class StreamChannel(AbstractChannel):
    """Abstract channel implementation for stream oriented transport protocols.

    StreamChannel implements communication link connecting two end points
    (peers).
    The channel asynchronously transmits messages: commands, results and
    events.

    StreamChannel uses escape sequences to represent End-Of-Message and
    End-Of-Stream markers.

    Clients can subclass StreamChannel to support particular stream oriented
    transport (wire) protocol.
    Also, see ChannelTCP for a concrete IChannel implementation that works on
    top of TCP sockets as a transport.
    """

    def __init__(self, remote_peer, local_peer=None):
        super(StreamChannel, self).__init__(remote_peer, local_peer=local_peer)
        self.bin_data_size = 0
        self.buf = bytearray(0x1000)
        self.buf_pos = 0
        self.buf_len = 0

    def get(self):
        pass

    def put(self, n):
        pass

    def getBuf(self, buf):
        i = 0
        l = len(buf)
        while i < l:
            b = self.get()
            if b < 0:
                if i == 0:
                    return -1
                break
            buf[i] = b
            i += 1
            if i >= self.bin_data_size:
                break
        return i

    def putBuf(self, buf):
        for b in buf:
            self.put(b & 0xff)

    def read(self):
        while True:
            while self.buf_pos >= self.buf_len:
                self.buf_len = self.getBuf(self.buf)
                self.buf_pos = 0
                if self.buf_len < 0:
                    return EOS
            res = self.buf[self.buf_pos] & 0xff
            self.buf_pos += 1
            if self.bin_data_size > 0:
                self.bin_data_size -= 1
                return res
            if res != ESC:
                return res
            while self.buf_pos >= self.buf_len:
                self.buf_len = self.getBuf(self.buf)
                self.buf_pos = 0
                if self.buf_len < 0:
                    return EOS
            n = self.buf[self.buf_pos] & 0xff
            self.buf_pos += 1
            if n == 0:
                return ESC
            elif n == 1:
                return EOM
            elif n == 2:
                return EOS
            elif n == 3:
                for i in range(0, 100000, 7):
                    while self.buf_pos >= self.buf_len:
                        self.buf_len = self.getBuf(self.buf)
                        self.buf_pos = 0
                        if self.buf_len < 0:
                            return EOS
                    m = self.buf[self.buf_pos] & 0xff
                    self.buf_pos += 1
                    self.bin_data_size |= (m & 0x7f) << i
                    if (m & 0x80) == 0:
                        break
            else:
                if n < 0:
                    return EOS
                assert False

    def writeByte(self, n):
        if n == ESC:
            self.put(ESC)
            self.put(0)
        elif n == EOM:
            self.put(ESC)
            self.put(1)
        elif n == EOS:
            self.put(ESC)
            self.put(2)
        else:
            assert n >= 0 and n <= 0xff
            self.put(n)

    def write(self, buf):
        if isinstance(buf, int):
            self.writeByte(buf)
            return
        elif isinstance(buf, compat.strings):
            buf = bytearray(buf, 'utf-8')

        if len(buf) > 32 and self.isZeroCopySupported():
            self.put(ESC)
            self.put(3)
            n = len(buf)
            while True:
                if n <= 0x7f:
                    self.put(n)
                    break
                self.put((n & 0x7f) | 0x80)
                n >>= 7
            self.putBuf(buf)
        else:
            for b in buf:
                n = b & 0xff
                self.put(n)
                if n == ESC:
                    self.put(0)
