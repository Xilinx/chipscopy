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

from .. import protocol, channel


class DelegatingEventListener(channel.EventListener):
    def __init__(self, _callable):
        self._callable = _callable

    def event(self, name, data):
        try:
            args = channel.fromJSONSequence(data)
            self._callable(self.svc_name, name, *args)
        except Exception as x:
            protocol.log("Error decoding event data", x)


def _print_event(service, name, *args):
    print("Event: %s.%s%s" % (service, name, tuple(args)))


def get_event_printer():
    return DelegatingEventListener(_print_event)


class EventRecorder(object):
    def __init__(self, channel):
        self._channel = channel
        self._events = []
        self._listeners = {}
        self._lock = threading.RLock()
        self._filter = None

    def __del__(self):
        if self._channel.state == channel.STATE_OPEN:
            self.stop()

    def record(self, service, enable=True):
        with self._lock:
            listener = self._listeners.get(service)
            if listener:
                if not enable:
                    protocol.invokeLater(self._channel.removeEventListener,
                                         service, listener)
            elif enable:
                recorder = self

                class Listener(channel.EventListener):
                    def event(self, name, data):
                        e = Event(service, name, data)
                        recorder._event(e)
                listener = Listener()
                self._listeners[service] = listener
                protocol.invokeLater(self._channel.addEventListener, service,
                                     listener)
            self._recording = enable

    def stop(self, service=None):
        if service:
            self.record(service, False)
        else:
            for service in list(self._listeners.keys()):
                self.record(service, False)

    def get(self):
        with self._lock:
            events = self._events
            self._events = []
        return events

    def _event(self, e):
        with self._lock:
            self._events.append(e)

    def __str__(self):
        events = self.get()
        return "\n".join(map(str, events))
    __repr__ = __str__


class Event(object):
    def __init__(self, service, name, data):
        self.service = service
        self.name = name
        try:
            self.args = channel.fromJSONSequence(data)
        except Exception as x:
            protocol.log("Error decoding event data", x)

    def __str__(self):
        return "Event: %s.%s%s" % (self.service, self.name, tuple(self.args))
    __repr__ = __str__
