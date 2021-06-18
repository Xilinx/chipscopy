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

import binascii
import json

# channel states
STATE_OPENING = 0
STATE_OPEN = 1
STATE_CLOSED = 2


class TraceListener(object):
    def onMessageReceived(self, t, token, service, name, data):
        pass

    def onMessageSent(self, t, token, service, name, data):
        pass

    def onChannelClosed(self, error):
        pass


class Proxy(object):
    def onCommand(self, token, service, name, data):
        pass

    def onEvent(self, service, name, data):
        pass

    def onChannelClosed(self, error):
        pass

_token_cnt = 0


class Token(object):
    def __init__(self, tokenID=None, listener=None):
        if tokenID is None:
            global _token_cnt
            tokenID = str(_token_cnt)
            _token_cnt += 1
        else:
            if isinstance(tokenID, bytearray):
                tokenID = tokenID.decode('utf-8')
            else:
                tokenID = str(tokenID)
        self.id = tokenID
        self.listener = listener

    def getID(self):
        return self.id

    def getListener(self):
        return self.listener

    def cancel(self):
        return False

    def __str__(self):
        return self.id


class ChannelListener(object):
    """
    Channel listener interface.
    """

    def onChannelOpened(self):
        """
        Called when a channel is opened or redirected.
        """
        pass

    def onChannelClosed(self, error):
        """
        Called when channel closed. If it is closed because of an error,
        'error' parameter will describe the error. 'error' is None if channel
        is closed normally by calling Channel.close().
        @param error - channel exception or None
        """
        pass

    def congestionLevel(self, level):
        """
        Notifies listeners about channel out-bound traffic congestion level
        changes.
        When level > 0 client should delay sending more messages.
        @param level - current congestion level
        """
        pass


class EventListener(object):
    """
    A generic interface for service event listener.
    Services usually define a service specific event listener interface,
    which is implemented using this generic listener.
    Clients should user service specific listener interface,
    unless no such interface is defined.
    """
    svc_name = "<unknown>"

    def event(self, name, data):
        """
        Called when service event message is received
        @param name - event name
        @param data - event arguments encoded as bytearray
        """
        pass


class CommandServer(object):
    """
    Command server interface.
    This interface is to be implemented by service providers.
    """
    def command(self, token, name, data):
        """
        Called every time a command is received from remote peer.
        @param token - command handle
        @param name - command name
        @param data - command arguments encoded into array of bytes
        """
        pass


class CommandListener(object):
    """
    Command listener interface. Clients implement this interface to
    receive command results.
    """
    def progress(self, token, data):
        """
        Called when progress message (intermediate result) is received
        from remote peer.
        @param token - command handle
        @param data - progress message arguments encoded into array of bytes
        """
        pass

    def result(self, token, data):
        """
        Called when command result received from remote peer.
        @param token - command handle
        @param data - command result message arguments encoded into array of
        bytes
        """
        pass

    def terminated(self, token, error):
        """
        Called when command is terminated because communication channel was
        closed or command is not recognized by remote peer.
        @param token - command handle
        @param error - exception that forced the channel to close
        """
        pass


def queue_bytes(arg):
    return b'(' + str(len(arg)).encode('utf-8') + b')' + arg


def toJSONSequence(args):
    if args is None:
        return None
    sequence = bytearray()
    for arg in args:
        if isinstance(arg, bytes):
            sequence += queue_bytes(arg)
        elif isinstance(arg, bytearray):
            sequence += queue_bytes(arg)
        elif hasattr(arg, '__json__'):
            sequence += arg.__json__()
        else:
            sequence += json.dumps(arg, separators=(',', ':'), cls=TCFJSONEncoder).encode('utf-8')
        sequence.append(0)
    return sequence


def parse_bin(s):
    n, _, data = s.partition(b')')
    n = int(n[1:].decode('utf-8'))
    return data[:n], data[n+1:]


def chomp_seq(s):
    if s and len(s) > 1 and s[-1] == 0:
        del s[-1]
    return s


def fromJSONSequence(s):
    objects = []
    #chomp_seq(s)
    while s and len(s) > 0:
        ch = s[0]
        if ch == b'('[0]:
            data, s = parse_bin(s)
            objects.append(data)
            continue
        j, _, s = s.partition(b'\x00')
        if j and len(j):
            j = chomp_seq(j)
            # NOTE - This decode and load will fail if an empty list is passed from Vivado
            #  This is a known issue. Solution - Don't send an empty list using the XHWPropertyMap
            objects.append(json.loads(j.decode('utf-8')))
        else:
            objects.append(None)
    return objects


def dumpJSONObject(obj):
    return json.dumps(obj, separators=(',', ':'), cls=TCFJSONEncoder)


def toByteArray(data):
    if data is None:
        return None
    t = type(data)
    if t is bytearray:
        return data
    else:
        return bytearray(binascii.a2b_base64(data))


class TCFJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__json__'):
            return o.__json__()
        elif hasattr(o, '__iter__'):
            return tuple(o)
        else:
            return json.JSONEncoder.default(self, o)
