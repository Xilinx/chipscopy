# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

import threading
from .. import compat
from .StreamChannel import StreamChannel, ESC


class CircularQueue(object):
    def __init__(self, maxsize):
        self.queue = bytearray(maxsize)
        self.head = 0
        self.tail = 0
        self.sent = 0
        self.last_byte = 0
        self.eom_bytes = (1, 2, 3)
        self.maxsize = maxsize
        self.mutex = threading.Lock()
        self.not_empty = threading.Condition(self.mutex)
        self.not_full = threading.Condition(self.mutex)

    def _next(self, i):
        return (i + 1) % self.maxsize

    def full(self):
        return self._next(self.tail) == self.head

    def empty(self):
        return self.head == self.sent

    def put(self, data):
        update_empty = self.empty()

        tail = self._next(self.tail)
        if tail == self.head:
            with self.not_full:
                self.not_full.wait()

        self.queue[tail] = data
        self.tail = tail

        if self.last_byte == ESC and data in self.eom_bytes:
            self.sent = tail

            if update_empty:
                with self.not_empty:
                    self.not_empty.notify()

        self.last_byte = data
        return True

    def wait_for_not_empty(self):
        with self.not_empty:
            self.not_empty.wait()

    def get(self):
        update_full = self.full()

        if self.head == self.sent:
            with self.not_empty:
                self.not_empty.wait()

        head = self._next(self.head)
        data = self.queue[head]
        self.head = head

        if update_full:
            with self.not_full:
                self.not_full.notify()

        return data

    def size(self):
        if self.tail >= self.head:
            return self.tail - self.head
        return self.maxsize - (self.head - self.tail)


class LoopbackChannel(StreamChannel):
    def __init__(self, remote_peer, local_peer=None):
        super(LoopbackChannel, self).__init__(remote_peer, local_peer)
        self.closed = False
        self.queue = CircularQueue(0x1000)
        self.start()

    def getBuf(self, buf):
        if self.closed:
            return -1
        if self.queue.empty():
            self.queue.wait_for_not_empty()
        count = min(self.queue.size(), len(buf))
        for n in range(count):
            buf[n] = self.queue.get()
        return count

    def get(self):
        if self.closed:
            return -1
        return self.queue.get()

    @staticmethod
    def str2bytes(data):
        if isinstance(data, compat.strings):
            return bytearray([ord(x) for x in data])
        elif isinstance(data, int):
            return bytearray([data])
        return data

    def put(self, b):
        if self.closed:
            return
        s = self.str2bytes(b)
        for p in s:
            self.queue.put(p)

    def putBuf(self, buf):
        if self.closed:
            return
        if isinstance(buf, (bytes, bytearray)):
            s = buf
        else:
            s = self.str2bytes(buf)
        for p in s:
            self.queue.put(p)

    def flush(self):
        pass

    def stop(self):
        self.closed = True
