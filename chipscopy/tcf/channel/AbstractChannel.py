# *****************************************************************************
# * Copyright (c) 2011, 2013, 2015-2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

import sys
import threading
import time

from .. import compat, protocol, transport, services, peer, errors
from ..services import locator
from ..channel import STATE_CLOSED, STATE_OPEN, STATE_OPENING
from ..channel import Token, fromJSONSequence, toJSONSequence, ChannelListener

EOS = -1  # End Of Stream
EOM = -2  # End Of Message


class Message(object):
    def __init__(self, typeCode):
        if isinstance(typeCode, int):
            typeCode = chr(typeCode)
        self.type = typeCode
        self.service = None
        self.name = None
        self.data = None
        self.is_canceled = None
        self.is_sent = None
        self.token = None
        self.trace = ()

    def __str__(self):
        return "%s %s %s %s" % (self.type, str(self.token), self.service, self.name)


class ReaderThread(threading.Thread):
    def __init__(self, channel, handleInput):
        super(ReaderThread, self).__init__(name="TCF Reader Thread")
        self.channel = channel
        self.handleInput = handleInput
        self.buf = bytearray()
        self.eos_err_report = None
        self.daemon = True

    def error(self):
        raise IOError("Protocol syntax error")

    def readBytes(self, end, buf=None):
        if buf is None:
            buf = bytearray()
        while True:
            n = self.channel.read()
            if n <= 0:
                if n == end:
                    break
                if n == EOM:
                    raise IOError("Unexpected end of message")
                if n < 0:
                    raise IOError("Communication channel is closed by " +
                                  "remote peer")
            buf.append(n)
        return buf

    def readString(self):
        del self.buf[:]
        return self.readBytes(0, self.buf).decode("UTF8")

    def run(self):
        try:
            while True:
                n = self.channel.read()
                if n == EOM:
                    continue
                if n == EOS:
                    try:
                        self.eos_err_report = self.readBytes(EOM)
                        reportLen = len(self.eos_err_report)
                        if reportLen == 0 or reportLen == 1 and \
                           self.eos_err_report[0] == 0:
                            self.eos_err_report = None
                    except:
                        pass
                    break
                msg = Message(n)
                if self.channel.read() != 0:
                    self.error()
                typeCode = msg.type
                if typeCode == 'C':
                    msg.token = Token(self.readBytes(0))
                    msg.service = self.readString()
                    msg.name = self.readString()
                    msg.data = self.readBytes(EOM)
                elif typeCode in 'PRN':
                    msg.token = Token(self.readBytes(0))
                    msg.data = self.readBytes(EOM)
                elif typeCode == 'E':
                    msg.service = self.readString()
                    msg.name = self.readString()
                    msg.data = self.readBytes(EOM)
                elif typeCode == 'F':
                    msg.data = self.readBytes(EOM)
                else:
                    self.error()
                protocol.invokeLater(self.handleInput, msg)
                delay = self.channel.local_congestion_level
                if delay > 0:
                    time.sleep(delay / 1000.0)
            protocol.invokeLater(self.handleEOS)
        except Exception as x:
            try:
                x.tb = sys.exc_info()[2]
                protocol.invokeLater(self.channel.terminate, x)
            except:
                # TCF event dispatcher has shut down
                pass

    def handleEOS(self):
        if not self.channel.out_tokens and not self.eos_err_report:
            self.channel.close()
        else:
            x = IOError("Communication channel is closed by remote peer")
            if self.eos_err_report:
                try:
                    args = fromJSONSequence(self.eos_err_report)
                    if len(args) > 0 and args[0] is not None:
                        x.caused_by = Exception(errors.toErrorString(args[0]))
                except IOError:
                    pass
            self.channel.terminate(x)


class AbstractChannel(object):
    """
    AbstractChannel implements communication link connecting two end points
    (peers). The channel asynchronously transmits messages: commands, results
    and events. Clients can subclass AbstractChannel to support particular
    transport (wire) protocol.

    .. see also: see StreamChannel for stream oriented transport protocols.
    """

    def __init__(self, remote_peer, local_peer=None):
        self.remote_peer = remote_peer
        self.local_peer = local_peer  # TODO
        self.inp_thread = ReaderThread(self, self.__handleInput)
        self.out_thread = threading.Thread(target=self.__write_output,
                                           name="TCF Channel Transmitter")
        self.out_thread.daemon = True
        self.out_tokens = {}
        self.out_queue = []
        self.out_lock = threading.Condition()
        self.pending_command_limit = 32
        self.remote_service_by_class = {}
        self.local_service_by_name = {}
        self.remote_service_by_name = {}
        self.channel_listeners = []
        self.event_listeners = {}
        self.command_servers = {}
        self.redirect_queue = []
        self.redirect_command = None
        self.notifying_channel_opened = False
        self.registered_with_trasport = False
        self.state = STATE_OPENING
        self.proxy = None
        self.zero_copy = False

        self.local_congestion_level = -100
        self.remote_congestion_level = -100
        self.local_congestion_cnt = 0
        self.local_congestion_time = 0
        self.local_service_by_class = {}
        self.trace_listeners = []
        self.linked_channels = {}

    def add_linked_channel(self, other_channel):
        channel = self

        class CloseListener(ChannelListener):
            def onChannelClosed(self, error):
                try:
                    del channel.linked_channels[other_channel]
                except KeyError:
                    return
                if not channel.linked_channels:
                    channel.close()

        if other_channel not in self.linked_channels:
            self.linked_channels[other_channel] = CloseListener()
            other_channel.addChannelListener(self.linked_channels[other_channel])

    @property
    def is_closed(self):
        return self.state == STATE_CLOSED

    def __write_output(self):
        try:
            while True:
                msg = None
                last = False
                with self.out_lock:
                    while len(self.out_queue) == 0:
                        self.out_lock.wait()
                    msg = self.out_queue.pop(0)
                    if not msg:
                        break
                    last = len(self.out_queue) == 0
                    if msg.is_canceled:
                        if last:
                            self.flush()
                        continue
                    msg.is_sent = True
                if msg.trace:
                    protocol.invokeLater(self.__traceMessageSent, msg)
                self.write(msg.type)
                self.write(0)
                if msg.token:
                    self.write(msg.token.id)
                    self.write(0)
                if msg.service:
                    self.write(msg.service.encode("UTF8"))
                    self.write(0)
                if msg.name:
                    self.write(msg.name.encode("UTF8"))
                    self.write(0)
                if msg.data:
                    self.write(msg.data)
                self.write(EOM)
                delay = 0
                level = self.remote_congestion_level
                if level > 0:
                    delay = level * 10
                if last or delay > 0:
                    self.flush()
                if delay > 0:
                    time.sleep(delay / 1000.0)
                # else yield()
            self.write(EOS)
            self.write(EOM)
            self.flush()
        except Exception as x:
            try:
                protocol.invokeLater(self.terminate, x)
            except:
                # TCF event dispatcher has shut down
                pass

    def __traceMessageSent(self, m):
        for l in m.trace:
            try:
                tokenID = None
                if m.token is not None:
                    tokenID = m.token.getID()
                l.onMessageSent(m.type, tokenID, m.service, m.name, m.data)
            except Exception as x:
                x.tb = sys.exc_info()[2]
                protocol.log("Exception in channel listener", x)

    def start(self):
        assert protocol.isDispatchThread()
        protocol.invokeLater(self.__initServices)
        self.inp_thread.start()
        self.out_thread.start()

    def __initServices(self):
        try:
            if self.proxy:
                return
            if self.state == STATE_CLOSED:
                return
            services.onChannelCreated(self, self.local_service_by_name)
            self.__makeServiceByClassMap(self.local_service_by_name,
                                         self.local_service_by_class)
            args = list(self.local_service_by_name.keys())
            self.sendEvent(protocol.getLocator(), "Hello",
                           toJSONSequence((args,)))
        except IOError as x:
            self.terminate(x)

    def redirect_id(self, peer_id):
        """
        Redirect this channel to given peer using this channel remote peer
        locator service as a proxy.
        @param peer_id - peer that will become new remote communication
        endpoint of this channel.
        """
        peerMap = {}
        peerMap[peer.ATTR_ID] = peer_id
        self.redirect(map)

    def redirect(self, peer_attrs):
        """
        Redirect this channel to given peer using this channel remote peer
        locator service as a proxy.
        @param peer_attrs - peer that will become new remote communication
        endpoint of this channel.
        """
        if isinstance(peer_attrs, compat.strings):
            # support for redirect(peerId)
            attrs = {}
            attrs[peer.ATTR_ID] = peer_attrs
            peer_attrs = attrs
        channel = self
        assert protocol.isDispatchThread()
        if self.state == STATE_OPENING:
            self.redirect_queue.append(peer_attrs)
        else:
            assert self.state == STATE_OPEN
            assert self.redirect_command is None
            try:
                l = self.remote_service_by_class.get(locator.LocatorService)
                if not l:
                    raise IOError("Cannot redirect channel: peer " +
                                  self.remote_peer.getID() +
                                  " has no locator service")
                peer_id = peer_attrs.get(peer.ATTR_ID)
                if peer_id and len(peer_attrs) == 1:
                    _peer = l.getPeers().get(peer_id)
                    if not _peer:
                        # Peer not found, must wait for a while until peer is
                        # discovered or time out
                        class Callback(object):
                            found = None

                            def __call__(self):
                                if self.found:
                                    return
                                channel.terminate(Exception("Peer " + peer_id +
                                                            " not found"))
                        cb = Callback()
                        delay = locator.DATA_RETENTION_PERIOD / 3
                        protocol.invokeLaterWithDelay(delay, cb)

                        class Listener(locator.LocatorListener):
                            def peerAdded(self, new_peer):
                                if new_peer.getID() == peer_id:
                                    cb.found = True
                                    channel.state = STATE_OPEN
                                    l.removeListener(self)
                                    channel.redirect_id(peer_id)
                        l.addListener(Listener())
                    else:
                        class DoneRedirect(locator.DoneRedirect):
                            def doneRedirect(self, token, exc):
                                assert channel.redirect_command is token
                                channel.redirect_command = None
                                if channel.state != STATE_OPENING:
                                    return
                                if exc:
                                    channel.terminate(exc)
                                channel.remote_peer = _peer
                                channel.remote_service_by_class.clear()
                                channel.remote_service_by_name.clear()
                                channel.event_listeners.clear()
                        self.redirect_command = l.redirect(peer_id,
                                                           DoneRedirect())
                else:
                    class TransientPeer(peer.TransientPeer):
                        def __init__(self, peer_attrs, parent):
                            super(TransientPeer, self).__init__(peer_attrs)
                            self.parent = parent

                        def openChannel(self):
                            c = self.parent.openChannel()
                            c.redirect(peer_attrs)

                    class DoneRedirect(locator.DoneRedirect):
                        def doneRedirect(self, token, exc):
                            assert channel.redirect_command is token
                            channel.redirect_command = None
                            if channel.state != STATE_OPENING:
                                return
                            if exc:
                                channel.terminate(exc)
                            parent = channel.remote_peer
                            channel.remote_peer = TransientPeer(peer_attrs,
                                                                parent)
                            channel.remote_service_by_class.clear()
                            channel.remote_service_by_name.clear()
                            channel.event_listeners.clear()
                    self.redirect_command = l.redirect(peer_attrs,
                                                       DoneRedirect())
                self.state = STATE_OPENING
            except Exception as x:
                self.terminate(x)

    def __makeServiceByClassMap(self, by_name, by_class):
        for service in list(by_name.values()):
            by_class[service.__class__] = service
            for clazz in service.__class__.__bases__:
                if clazz == services.Service:
                    continue
                # TODO
                # if (!IService.class.isAssignableFrom(fs)) continue
                by_class[clazz] = service

    def getState(self):
        return self.state

    def addChannelListener(self, listener):
        assert protocol.isDispatchThread()
        assert listener
        self.channel_listeners.append(listener)

    def removeChannelListener(self, listener):
        assert protocol.isDispatchThread()
        self.channel_listeners.remove(listener)

    def addTraceListener(self, listener):
        if self.trace_listeners is None:
            self.trace_listeners = []
        else:
            self.trace_listeners = self.trace_listeners[:]
        self.trace_listeners.append(listener)

    def removeTraceListener(self, listener):
        self.trace_listeners = self.trace_listeners[:]
        self.trace_listeners.remove(listener)
        if len(self.trace_listeners) == 0:
            self.trace_listeners = None

    def addEventListener(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        listener.svc_name = svc_name
        lst = self.event_listeners.get(svc_name) or []
        lst.append(listener)
        self.event_listeners[svc_name] = lst

    def removeEventListener(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        lst = self.event_listeners.get(svc_name)
        if not lst:
            return
        for i in range(len(lst)):
            if lst[i] is listener:
                if len(lst) == 1:
                    del self.event_listeners[svc_name]
                else:
                    del lst[i]
                return

    def addCommandServer(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        if self.command_servers.get(svc_name):
            raise Exception("Only one command server per service is allowed")
        self.command_servers[svc_name] = listener

    def removeCommandServer(self, service, listener):
        assert protocol.isDispatchThread()
        svc_name = str(service)
        if self.command_servers.get(svc_name) is not listener:
            raise Exception("Invalid command server")
        del self.command_servers[svc_name]

    def close(self):
        assert protocol.isDispatchThread()
        if self.state == STATE_CLOSED:
            return
        try:
            for chan, listener in self.linked_channels.items():
                chan.removeChannelListener(listener)
            self.__sendEndOfStream(10000)
            self._close(None)
        except Exception as x:
            self._close(x)

    def terminate(self, error):
        assert protocol.isDispatchThread()
        if self.state == STATE_CLOSED:
            return
        try:
            self.__sendEndOfStream(500)
        except Exception as x:
            if not error:
                error = x
        self._close(error)

    def __sendEndOfStream(self, timeout):
        with self.out_lock:
            del self.out_queue[:]
            self.out_queue.append(None)
            self.out_lock.notify()
        self.out_thread.join(timeout)

    def _close(self, error):
        assert self.state != STATE_CLOSED
        self.state = STATE_CLOSED
        # Closing channel underlying streams can block for a long time,
        # so it needs to be done by a background thread.
        thread = threading.Thread(target=self.stop, name="TCF Channel Cleanup")
        thread.daemon = True
        thread.start()
        if error and isinstance(self.remote_peer, peer.AbstractPeer):
            self.remote_peer.onChannelTerminated()
        if self.registered_with_trasport:
            self.registered_with_trasport = False
            transport.channelClosed(self, error)
        if self.proxy:
            try:
                self.proxy.onChannelClosed(error)
            except Exception as x:
                x.tb = sys.exc_info()[2]
                protocol.log("Exception in channel listener", x)
        channel = self

        class Runnable(object):
            def __call__(self):
                if channel.out_tokens:
                    x = None
                    if isinstance(error, Exception):
                        x = error
                    elif error:
                        x = Exception(error)
                    else:
                        x = IOError("Channel is closed")
                    for msg in list(channel.out_tokens.values()):
                        try:
                            s = str(msg)
                            if len(s) > 72:
                                s = s[:72] + "...]"
                            y = IOError("Command " + s + " aborted")
#                            y.initCause(x)
                            msg.token.getListener().terminated(msg.token, y)
                        except Exception as e:
                            protocol.log("Exception in command listener", e)
                    channel.out_tokens.clear()
                if channel.channel_listeners:
                    for l in channel.channel_listeners:
                        if not l:
                            break
                        try:
                            l.onChannelClosed(error)
                        except Exception as x:
                            x.tb = sys.exc_info()[2]
                            protocol.log("Exception in channel listener", x)
                if channel.trace_listeners:
                    for l in channel.trace_listeners:
                        try:
                            l.onChannelClosed(error)
                        except Exception as x:
                            x.tb = sys.exc_info()[2]
                            protocol.log("Exception in channel listener", x)
                if error:
                    protocol.log("TCF channel terminated", error)
        protocol.invokeLater(Runnable())

    def getCongestion(self):
        assert protocol.isDispatchThread()
        level = len(self.out_tokens) * 100 / self.pending_command_limit - 100
        if self.remote_congestion_level > level:
            level = self.remote_congestion_level
        if level > 100:
            level = 100
        return level

    def getLocalPeer(self):
        assert protocol.isDispatchThread()
        return self.local_peer

    def getRemotePeer(self):
        assert protocol.isDispatchThread()
        return self.remote_peer

    def get_local_services(self):
        assert protocol.isDispatchThread()
        assert self.state != STATE_OPENING
        return list(self.local_service_by_name.keys())

    def getRemoteServices(self):
        assert protocol.isDispatchThread()
        assert self.state != STATE_OPENING
        return list(self.remote_service_by_name.keys())

    def get_local_service(self, cls_or_name):
        assert protocol.isDispatchThread()
        assert self.state != STATE_OPENING
        if isinstance(cls_or_name, compat.strings):
            return self.local_service_by_name.get(cls_or_name)
        else:
            return self.local_service_by_class.get(cls_or_name)

    def getRemoteService(self, cls_or_name):
        assert protocol.isDispatchThread()
        assert self.state != STATE_OPENING
        if isinstance(cls_or_name, compat.strings):
            return self.remote_service_by_name.get(cls_or_name)
        else:
            return self.remote_service_by_class.get(cls_or_name)

    def setServiceProxy(self, service_interface, service_proxy):
        if not self.notifying_channel_opened:
            raise Exception("setServiceProxe() can be called only from " +
                            "channel open call-back")
        proxy = self.remote_service_by_name.get(service_proxy.getName())
        if not isinstance(proxy, services.GenericProxy):
            raise Exception("Proxy already set")
        if self.remote_service_by_class.get(service_interface):
            raise Exception("Proxy already set")
        self.remote_service_by_class[service_interface] = service_proxy
        self.remote_service_by_name[service_proxy.getName()] = service_proxy

    def setProxy(self, proxy, services):
        self.proxy = proxy
        self.sendEvent(protocol.getLocator(), "Hello",
                       toJSONSequence((services,)))
        self.local_service_by_class.clear()
        self.local_service_by_name.clear()

    def addToOutQueue(self, msg):
        msg.trace = self.trace_listeners
        with self.out_lock:
            self.out_queue.append(msg)
            self.out_lock.notify()

    def sendCommand(self, service, name, args, listener):
        assert protocol.isDispatchThread()
        if self.state == STATE_OPENING:
            raise Exception("Channel is waiting for Hello message")
        if self.state == STATE_CLOSED:
            raise Exception("Channel is closed")
        msg = Message('C')
        msg.service = str(service)
        msg.name = name
        msg.data = args
        channel = self

        class CancelableToken(Token):
            def __init__(self, listener):
                super(CancelableToken, self).__init__(listener=listener)

            def cancel(self):
                assert protocol.isDispatchThread()
                if channel.state != STATE_OPEN:
                    return False
                with channel.out_lock:
                    if msg.is_sent:
                        return False
                    msg.is_canceled = True
                del channel.out_tokens[msg.token.getID()]
                return True
        token = CancelableToken(listener)
        msg.token = token
        self.out_tokens[token.getID()] = msg
        self.addToOutQueue(msg)
        return token

    def sendProgress(self, token, results):
        assert protocol.isDispatchThread()
        if self.state != STATE_OPEN:
            raise Exception("Channel is closed")
        msg = Message('P')
        msg.data = results
        msg.token = token
        self.addToOutQueue(msg)

    def sendResult(self, token, results):
        assert protocol.isDispatchThread()
        if self.state != STATE_OPEN:
            raise Exception("Channel is closed")
        msg = Message('R')
        msg.data = results
        msg.token = token
        self.addToOutQueue(msg)

    def rejectCommand(self, token):
        assert protocol.isDispatchThread()
        if self.state != STATE_OPEN:
            raise Exception("Channel is closed")
        msg = Message('N')
        msg.token = token
        self.addToOutQueue(msg)

    def sendEvent(self, service, name, args):
        assert protocol.isDispatchThread()
        if not (self.state == STATE_OPEN or self.state == STATE_OPENING and
                isinstance(service, locator.LocatorService)):
            raise Exception("Channel is closed")
        msg = Message('E')
        msg.service = str(service)
        msg.name = name
        msg.data = args
        self.addToOutQueue(msg)

    def isZeroCopySupported(self):
        return self.zero_copy

    def __traceMessageReceived(self, m):
        for l in self.trace_listeners:
            try:
                messageID = None
                if m.token is not None:
                    messageID = m.token.getID()
                l.onMessageReceived(m.type, messageID, m.service, m.name,
                                    m.data)
            except Exception as x:
                x.tb = sys.exc_info()[2]
                protocol.log("Exception in channel listener", x)

    def __handleInput(self, msg):
        assert protocol.isDispatchThread()
        if self.state == STATE_CLOSED:
            return
        if self.trace_listeners:
            self.__traceMessageReceived(msg)
        try:
            token = None
            typeCode = msg.type
            if typeCode in 'PRN':
                token_id = msg.token.getID()
                cmd = self.out_tokens.get(token_id)
                if cmd is None:
                    raise Exception("Invalid token received: " + token_id)
                if typeCode != 'P':
                    del self.out_tokens[token_id]
                token = cmd.token
            if typeCode == 'C':
                if self.state == STATE_OPENING:
                    raise IOError("Received command " + msg.service + "." +
                                  msg.name + " before Hello message")
                if self.proxy:
                    self.proxy.onCommand(msg.token, msg.service, msg.name,
                                         msg.data)
                else:
                    token = msg.token
                    cmds = self.command_servers.get(msg.service)
                    if cmds:
                        cmds.command(token, msg.name, msg.data)
                    else:
                        self.rejectCommand(token)
            elif typeCode == 'P':
                token.getListener().progress(token, msg.data)
                self.__sendCongestionLevel()
            elif typeCode == 'R':
                token.getListener().result(token, msg.data)
                self.__sendCongestionLevel()
            elif typeCode == 'N':
                report = errors.ErrorReport("Command is not recognized",
                                            errors.TCF_ERROR_INV_COMMAND)
                token.getListener().terminated(token, report)
            elif typeCode == 'E':
                hello = msg.service == locator.NAME and msg.name == "Hello"
                if hello:
                    self.remote_service_by_name.clear()
                    self.remote_service_by_class.clear()
                    data = fromJSONSequence(msg.data)[0]
                    services.onChannelOpened(self, data,
                                             self.remote_service_by_name)
                    self.__makeServiceByClassMap(self.remote_service_by_name,
                                                 self.remote_service_by_class)
                    self.zero_copy = "ZeroCopy" in self.remote_service_by_name
                if self.proxy and self.state == STATE_OPEN:
                    self.proxy.onEvent(msg.service, msg.name, msg.data)
                elif hello:
                    assert self.state == STATE_OPENING
                    self.state = STATE_OPEN
                    assert self.redirect_command is None
                    if self.redirect_queue:
                        self.redirect(self.redirect_queue.pop(0))
                    else:
                        self.notifying_channel_opened = True
                        if not self.registered_with_trasport:
                            transport.channelOpened(self)
                            self.registered_with_trasport = True
                        for l in tuple(self.channel_listeners):
                            if not l:
                                break
                            try:
                                l.onChannelOpened()
                            except Exception as x:
                                x.tb = sys.exc_info()[2]
                                protocol.log("Exception in channel listener",
                                             x)
                        self.notifying_channel_opened = False
                else:
                    lst = self.event_listeners.get(msg.service)
                    if lst:
                        for l in lst:
                            l.event(msg.name, msg.data)
                    self.__sendCongestionLevel()
            elif typeCode == 'F':
                length = len(msg.data)
                if length > 0 and msg.data[length - 1] == 0:
                    length -= 1
                self.remote_congestion_level = int(msg.data[:length])
            else:
                assert False
        except Exception as x:
            x.tb = sys.exc_info()[2]
            self.terminate(x)

    def __sendCongestionLevel(self):
        self.local_congestion_cnt += 1
        if self.local_congestion_cnt < 8:
            return
        self.local_congestion_cnt = 0
        if self.state != STATE_OPEN:
            return
        timeVal = int(time.time() * 1000)
        if timeVal - self.local_congestion_time < 500:
            return
        assert protocol.isDispatchThread()
        level = protocol.getCongestionLevel()
        if level == self.local_congestion_level:
            return
        i = int((level - self.local_congestion_level) / 8)
        if i != 0:
            level = self.local_congestion_level + i
        self.local_congestion_time = timeVal
        with self.out_lock:
            msg = None
            if self.out_queue:
                msg = self.out_queue[0]
            if msg is None or msg.type != 'F':
                msg = Message('F')
                self.out_queue.insert(0, msg)
                self.out_lock.notify()
            data = "%i\0" % self.local_congestion_level
            msg.data = data
            msg.trace = self.trace_listeners
            self.local_congestion_level = level

    def read(self):
        """
        Read one byte from the channel input stream.
        @return next data byte or EOS (-1) if end of stream is reached,
        or EOM (-2) if end of message is reached.
        @raises IOError
        """
        raise NotImplementedError("Abstract method")

    def writeByte(self, n):
        """
        Write one byte into the channel output stream.
        The method argument can be one of two special values:
        - EOS (-1) end of stream marker
        - EOM (-2) end of message marker.
        The stream can put the byte into a buffer instead of transmitting it
        right away.
        @param n - the data byte.
        @raises IOError
        """
        raise NotImplementedError("Abstract method")

    def flush(self):
        """
        Flush the channel output stream.
        All buffered data should be transmitted immediately.
        @raises IOError
        """
        raise NotImplementedError("Abstract method")

    def stop(self):
        """
        Stop (close) channel underlying streams.
        If a thread is blocked by read() or write(), it should be
        resumed (or interrupted).
        @raises IOError
        """
        raise NotImplementedError("Abstract method")

    def write(self, buf):
        """
        Write array of bytes into the channel output stream.
        The stream can put bytes into a buffer instead of transmitting it right
        away.
        @param buf
        @raises IOError
        """
        assert threading.currentThread() == self.out_thread
        for i in buf:
            self.writeByte(ord(buf[i]) & 0xff)
