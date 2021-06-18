# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * Copyright (c) 2011, 2016 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""
Locator service uses transport layer to search
for peers and to collect and maintain up-to-date
data about peer's attributes.
"""

import platform
import threading
import time
import socket

from .. import locator
from ...util import logging
from ...channel import fromJSONSequence, toJSONSequence, STATE_CLOSED
from ...channel.ChannelProxy import ChannelProxy
from ... import compat, protocol, services, channel, peer, errors, transport, process_param_str

# Flag indicating whether tracing of the the discovery activity is enabled.
__TRACE_DISCOVERY__ = False


class SubNet(object):
    def __init__(self, prefix_length, address, broadcast):
        self.prefix_length = prefix_length
        self.address = address
        self.broadcast = broadcast
        self.last_slaves_req_time = 0

    def contains(self, addr):
        if addr is None or self.address is None:
            return False
        a1 = addr.getAddress()
        a2 = self.address.getAddress()
        if len(a1) != len(a2):
            return False
        i = 0
        if self.prefix_length <= len(a1) * 8:
            l = self.prefix_length
        else:
            l = len(a1) * 8
        while i + 8 <= l:
            n = int(i / 8)
            if a1[n] != a2[n]:
                return False
            i += 8
        while i < l:
            n = int(i / 8)
            m = 1 << (7 - i % 8)
            if (a1[n] & m) != (a2[n] & m):
                return False
            i += 1
        return True

    def __eq__(self, o):
        if not isinstance(o, SubNet):
            return False
        return self.prefix_length == o.prefix_length and \
            self.broadcast == o.broadcast and \
            self.address == o.address

    def __hash__(self):
        return hash(self.address)

    def __str__(self):
        return "%s/%d" % (self.address.getHostAddress(), self.prefix_length)


class Slave(object):
    # Time of last packet receiver from self slave
    last_packet_time = 0
    # Time of last REQ_SLAVES packet received from self slave
    last_req_slaves_time = 0

    def __init__(self, address, port):
        self.address = address
        self.port = port

    def __str__(self):
        return "%s/%d" % (self.address.getHostAddress(), self.port)


class AddressCacheItem(object):
    address = None
    time_stamp = 0
    used = False

    def __init__(self, host):
        self.host = host


class InetAddress(object):
    "Mimicking Java InetAddress class"
    def __init__(self, host, addr):
        self.host = host
        self.addr = addr

    def getAddress(self):
        return socket.inet_aton(self.addr)

    def getHostAddress(self):
        return self.addr

    def __eq__(self, other):
        if not isinstance(other, InetAddress):
            return False
        return self.addr == other.addr

    def __str__(self):
        return "%s/%s" % (self.host or "", self.addr)

    def __hash__(self):
        return hash(self.addr)


class InputPacket(object):
    "Wrapper for UDP packet data."
    def __init__(self, data, addr, port):
        self.data = data
        self.addr = addr
        self.port = port

    def getLength(self):
        return len(self.data)

    def getData(self):
        return self.data

    def getPort(self):
        return self.port

    def getAddress(self):
        return self.addr

    def __str__(self):
        return "[address=%s,port=%d,data=\"%s\"]" % \
               (self.getAddress(), self.getPort(), self.data)


def is_matching_peer(peer_info, remote_peer):
    attrs = remote_peer.getAttributes()
    if peer.ATTR_ID in peer_info:
        return attrs[peer.ATTR_ID] == peer_info[peer.ATTR_ID]
    return attrs[peer.ATTR_TRANSPORT_NAME] == peer_info[peer.ATTR_TRANSPORT_NAME] and \
           attrs[peer.ATTR_IP_HOST] == peer_info[peer.ATTR_IP_HOST] and \
           attrs[peer.ATTR_IP_PORT] == peer_info[peer.ATTR_IP_PORT]


def fill_peer_attributes(peer_info):
    if peer.ATTR_ID not in peer_info:
        peer_info[peer.ATTR_ID] = "{}:{}:{}".format(
            peer_info[peer.ATTR_TRANSPORT_NAME],
            peer_info[peer.ATTR_IP_HOST],
            peer_info[peer.ATTR_IP_PORT]
        )
    else:
        if peer.ATTR_TRANSPORT_NAME not in peer_info or \
           peer.ATTR_IP_PORT not in peer_info or \
           peer.ATTR_IP_HOST not in peer_info:
            peer_info[peer.ATTR_ID] = process_param_str(peer_info[peer.ATTR_ID])
            _id = peer_info[peer.ATTR_ID]
            peer_info[peer.ATTR_TRANSPORT_NAME], peer_info[peer.ATTR_IP_HOST], peer_info[peer.ATTR_IP_PORT] = \
                _id.split(":")


DISCOVEY_PORT = 1534
MAX_PACKET_SIZE = 9000 - 40 - 8
PREF_PACKET_SIZE = 1500 - 40 - 8

# TODO: research usage of DNS-SD (DNS Service Discovery) to discover TCF peers


class LocatorService(locator.LocatorService):
    locator = None
    peers = {}  # str->Peer
    listeners = []  # list of LocatorListener
    error_log = set()  # set of str
    addr_list = []
    addr_cache = {}  # str->AddressCacheItem
    addr_request = False
    local_peer = None
    last_master_packet_time = 0

    @classmethod
    def getLocalPeer(cls):
        return cls.local_peer

    @classmethod
    def getListeners(cls):
        return cls.listeners[:]

    @classmethod
    def startup(cls):
        if cls.locator:
            cls.locator._startup()

    @classmethod
    def shutdown(cls):
        if cls.locator:
            cls.locator._shutdown()

    def __init__(self):
        self._error_log_lock = threading.RLock()
        self._alive = False
        LocatorService.locator = self
        LocatorService.local_peer = peer.LocalPeer()

    def _startup(self):
        if self._alive:
            return
        self._alive = True
        self._addr_cache_lock = threading.Condition()
        self.subnets = set()
        self.slaves = []
        self.inp_buf = bytearray(MAX_PACKET_SIZE)
        self.out_buf = bytearray(MAX_PACKET_SIZE)
        service = self

        class TimerThread(threading.Thread):
            def __init__(self, _callable):
                self._callable = _callable
                super(TimerThread, self).__init__()

            def run(self):
                while service._alive:
                    try:
                        time.sleep(locator.DATA_RETENTION_PERIOD / 4 / 1000.)
                        protocol.invokeAndWait(self._callable)
                    except RuntimeError:
                        # TCF event dispatch is shut down
                        return
                    except Exception as x:
                        service._log("Unhandled exception in TCF discovery " +
                                     "timer thread", x)
        self.timer_thread = TimerThread(self.__refresh_timer)

        class DNSLookupThread(threading.Thread):
            def run(self):

                while service._alive:
                    try:
                        itemSet = None
                        with service._addr_cache_lock:
                            period = locator.DATA_RETENTION_PERIOD
                            if not LocatorService.addr_request:
                                service._addr_cache_lock.wait(period)
                            msec = int(time.time() * 1000)
                            items = list(LocatorService.addr_cache.items())
                            for host, a in items:
                                if a.time_stamp + period * 10 < msec:
                                    if a.used:
                                        if itemSet is None:
                                            itemSet = set()
                                        itemSet.add(a)
                                    else:
                                        del LocatorService.addr_cache[host]
                            LocatorService.addr_request = False
                        if itemSet is not None:
                            for a in itemSet:
                                addr = None
                                try:
                                    addr = socket.gethostbyname(a.host)
                                except socket.gaierror:
                                    pass
                                with service._addr_cache_lock:
                                    if addr is None:
                                        a.address = None
                                    else:
                                        a.address = InetAddress(a.host, addr)
                                    a.time_stamp = msec
                                    a.used = False
                    except Exception as x:
                        service._log("Unhandled exception in TCF discovery " +
                                     "DNS lookup thread", x)
        self.dns_lookup_thread = DNSLookupThread()

        class InputThread(threading.Thread):
            def __init__(self, _callable):
                self._callable = _callable
                super(InputThread, self).__init__()

            def run(self):
                try:
                    while service._alive:
                        sock = service.socket
                        try:
                            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
                            if addr and len(addr) >= 2:
                                p = InputPacket(data,
                                                InetAddress(None, addr[0]),
                                                addr[1])
                                protocol.invokeAndWait(self._callable, p)
                        except RuntimeError:
                            # TCF event dispatch is shutdown
                            return
                        except socket.error as x:
                            if sock != service.socket:
                                continue
                            # frequent  error on windows, unknown reason
                            if x.errno == 10054:
                                continue
                            port = sock.getsockname()[1]
                            service._log("Cannot read from datagram socket " +
                                         "at port %d" % port, x)
                            time.sleep(2)
                except Exception as x:
                    service._log("Unhandled exception in socket reading " +
                                 "thread", x)
        self.input_thread = InputThread(self.__handleDatagramPacket)
        try:
            self.loopback_addr = InetAddress(None, "127.0.0.1")
            tcfversion = 'TCF%s\0\0\0\0' % locator.CONF_VERSION
            self.out_buf[0:8] = [ord(c) for c in tcfversion]
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.socket.bind(('', DISCOVEY_PORT))
                if __TRACE_DISCOVERY__:
                    logging.trace("Became the master agent (bound to port " +
                                  "%d)" % self.socket.getsockname()[1])
            except socket.error as x:
                self.socket.bind(('', 0))
                if __TRACE_DISCOVERY__:
                    logging.trace("Became a slave agent (bound to port " +
                                  "%d)" % self.socket.getsockname()[1])
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.input_thread.setName("TCF Locator Receiver")
            self.timer_thread.setName("TCF Locator Timer")
            self.dns_lookup_thread.setName("TCF Locator DNS Lookup")
            self.input_thread.setDaemon(True)
            self.timer_thread.setDaemon(True)
            self.dns_lookup_thread.setDaemon(True)
            self.input_thread.start()
            self.timer_thread.start()
            self.dns_lookup_thread.start()

            class LocatorListener(locator.LocatorListener):
                def peerAdded(self, peer):
                    service._sendPeerInfo(peer, None, 0)

                def peerChanged(self, peer):
                    service._sendPeerInfo(peer, None, 0)

            self.listeners.append(LocatorListener())
            self.__refreshSubNetList()
            self.__sendPeersRequest(None, 0)
            self.__sendAll(None, 0, None, int(time.time() * 1000))
        except Exception as x:
            self._log("Cannot open UDP socket for TCF discovery protocol", x)

    def _shutdown(self):
        if self._alive:
            self._alive = False
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.socket.close()
            except Exception:
                pass
            try:
                with self._addr_cache_lock:
                    self._addr_cache_lock.notify_all()
            except Exception:
                pass

    def __makeErrorReport(self, code, msg):
        err = {}
        err[errors.ERROR_TIME] = int(time.time() * 1000)
        err[errors.ERROR_CODE] = code
        err[errors.ERROR_FORMAT] = msg
        return err

    def _openPeer(self, reply_channel, token, remote_peer):
        c = remote_peer.openChannel()

        class ChannelListener(channel.ChannelListener):
            def onChannelOpened(self):
                c.removeChannelListener(self)
                c.add_linked_channel(reply_channel)
                reply_channel.sendResult(token, toJSONSequence((None, c.remote_peer.getAttributes())))

            def onChannelClosed(self, error):
                reply_channel.sendResult(token, toJSONSequence((str(error), None)))

        c.addChannelListener(ChannelListener())

    def _command(self, channel, token, name, data):
        try:
            if name == "redirect":
                peer_id = fromJSONSequence(data)[0]
                _peer = self.peers.get(peer_id)
                if _peer is None:
                    errNum = errors.TCF_ERROR_UNKNOWN_PEER
                    error = self.__makeErrorReport(errNum, "Unknown peer ID")
                    channel.sendResult(token, toJSONSequence((error,)))
                    return
                channel.sendResult(token, toJSONSequence((None,)))
                if isinstance(_peer, peer.LocalPeer):
                    seq = (channel.get_local_services(),)
                    channel.sendEvent(protocol.getLocator(), "Hello",
                                      toJSONSequence(seq))
                    return
                ChannelProxy(channel, _peer.openChannel())
            elif name == "sync":
                channel.sendResult(token, None)
            elif name == "getPeers":
                arr = []
                for p in list(self.peers.values()):
                    arr.append(p.getAttributes())
                channel.sendResult(token, toJSONSequence((None, arr)))
            elif name == "getChannels":
                channels = transport.getOpenChannels()
                arr = [c.remote_peer.getAttributes() for c in channels]
                channel.sendResult(token, toJSONSequence((None, arr)))
            elif name == "connectPeer":
                peer_info = fromJSONSequence(data)[0]
                fill_peer_attributes(peer_info)
                chan = None
                err = None
                # check channel does not already exist
                channels = transport.getOpenChannels()
                for c in channels:
                    if is_matching_peer(peer_info, c.remote_peer):
                        chan = c
                        break

                if not chan:
                    remote_peer = None
                    # check peer already exists
                    for p in self.peers.values():
                        if is_matching_peer(peer_info, p):
                            remote_peer = p
                            break
                    if not remote_peer:
                        remote_peer = peer.RemotePeer(peer_info)
                    # connect peer
                    if remote_peer:
                        self._openPeer(channel, token, remote_peer)
                else:
                    chan.add_linked_channel(channel)
                    if err:
                        channel.sendResult(token, toJSONSequence((err, None)))
                    else:
                        channel.sendResult(token, toJSONSequence((None, chan.remote_peer.getAttributes())))

            elif name == "disconnectPeer":
                peer_info = fromJSONSequence(data)[0]
                chan = None
                err = None
                # check channel does not already exist
                channels = transport.getOpenChannels()
                for c in channels:
                    if is_matching_peer(peer_info, c.remote_peer):
                        chan = c
                        break

                if chan:
                    chan.close()
                else:
                    err = "Could not find channel to disconnect."

                if err:
                    channel.sendResult(token, toJSONSequence((err, None)))
                else:
                    channel.sendResult(token, toJSONSequence((None, chan.getState() == STATE_CLOSED)))

            else:
                channel.rejectCommand(token)
        except Exception as x:
            channel.terminate(x)

    def _log(self, msg, x):
        if not self._alive:
            return
        # Don't report same error multiple times to avoid filling up the log
        # file.
        try:
            with self._error_log_lock:
                if msg in self.error_log:
                    return
                self.error_log.add(msg)
        except TypeError:
            # If the error_log_lock thread is dead, it just means that we are
            # shutting down. The _alive value does not seem to be up to date
            # in some cases ...
            return
        protocol.log(msg, x)

    def __getInetAddress(self, host):
        if not host:
            return None
        with self._addr_cache_lock:
            i = self.addr_cache.get(host)
            if i is None:
                i = AddressCacheItem(host)
                ch = host[0]
                if ch == '[' or ch == ':' or ch >= '0' and ch <= '9':
                    try:
                        addr = socket.gethostbyname(host)
                        i.address = InetAddress(host, addr)
                    except socket.gaierror:
                        pass
                    i.time_stamp = int(time.time() * 1000)
                else:
                    # socket.gethostbyname() can cause long delay - delegate to
                    # background thread
                    LocatorService.addr_request = True
                    self._addr_cache_lock.notify()
                self.addr_cache[host] = i
            i.used = True
            return i.address

    def __refresh_timer(self):
        tm = int(time.time() * 1000)
        # Cleanup slave table
        if self.slaves:
            i = 0
            while i < len(self.slaves):
                s = self.slaves[i]
                if s.last_packet_time + locator.DATA_RETENTION_PERIOD < tm:
                    del self.slaves[i]
                else:
                    i += 1

        # Cleanup peers table
        stale_peers = None
        for p in list(self.peers.values()):
            if isinstance(p, peer.RemotePeer):
                if p.getLastUpdateTime() + locator.DATA_RETENTION_PERIOD < tm:
                    if stale_peers is None:
                        stale_peers = []
                    stale_peers.append(p)
        if stale_peers is not None:
            for p in stale_peers:
                p.dispose()

        # Try to become a master
        try:
            port = self.socket.getsockname()[1]
        except OSError:
            port = ""
        period = int(locator.DATA_RETENTION_PERIOD / 2)
        if port != DISCOVEY_PORT and \
                self.last_master_packet_time + period <= tm:
            s0 = self.socket
            s1 = None
            try:
                s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s1.bind((socket.gethostname(), DISCOVEY_PORT))
                s1.setsockopt(socket.SOL_UDP, socket.SO_BROADCAST, 1)
                self.socket = s1
                s0.close()
            except:
                pass
        self.__refreshSubNetList()
        if port != DISCOVEY_PORT:
            for subnet in self.subnets:
                self.__addSlave(subnet.address, port, tm, tm)
        self.__sendAll(None, 0, None, tm)

    def __addSlave(self, addr, port, timestamp, time_now):
        for s in self.slaves:
            if s.port == port and s.address == addr:
                if s.last_packet_time < timestamp:
                    s.last_packet_time = timestamp
                return s
        s = Slave(addr, port)
        s.last_packet_time = timestamp
        self.slaves.append(s)
        self.__sendPeersRequest(addr, port)
        self.__sendAll(addr, port, s, time_now)
        self.__sendSlaveInfo(s, time_now)
        return s

    def __refreshSubNetList(self):
        subNetSet = set()
        try:
            self.__getSubNetList(subNetSet)
        except Exception as x:
            self._log("Cannot get list of network interfaces", x)
        for s in tuple(self.subnets):
            if s in subNetSet:
                continue
            self.subnets.remove(s)
        for s in subNetSet:
            if s in self.subnets:
                continue
            self.subnets.add(s)
        if __TRACE_DISCOVERY__:
            buf = "Refreshed subnet list:"
            for subnet in self.subnets:
                buf += "\n\t* address=%s, broadcast=%s" % \
                       (subnet.address, subnet.broadcast)
            logging.trace(buf)

    def __getAllIpAddresses(self):
        import fcntl  # @UnresolvedImport
        import struct
        import array

        nBytes = 8192
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        names = array.array('B', [0] * nBytes)
        ifcfg = struct.unpack(
            'iL', fcntl.ioctl(s.fileno(), 0x8912,
                              struct.pack('iL', nBytes,
                                          names.buffer_info()[0])))[0]

        namestr = names.tostring()
        if namestr and isinstance(namestr[0], int):
            namestr = ''.join(chr(b) for b in namestr)
        res = []

        # the ipconf structure changed at a time, check if there are more than
        # 40 bytes

        ifconfSz = 32
        sz = 32
        altSz = 40

        if len(namestr) > sz:
            # check for name at 32->32+16
            secondName = str(namestr[sz:sz + 16].split('\0', 1)[0])
            secondAltName = str(namestr[altSz:altSz + 16].split('\0', 1)[0])

            if (not secondName.isalnum()) and (secondAltName.isalnum()):
                ifconfSz = 40

        for ix in range(0, ifcfg, ifconfSz):
            ipStartIx = ix + 20
            ipEndIx = ix + 24
            ip = namestr[ipStartIx:ipEndIx]
            res.append(str(ord(ip[0])) + '.' + str(ord(ip[1])) + '.' +
                       str(ord(ip[2])) + '.' + str(ord(ip[3])))

        return (res)

    def __getSubNetList(self, _set):
        hostname = socket.gethostname()
        if len(self.addr_list) == 0:
            # Create the list of IP address for this host
            _, _, self.addr_list = socket.gethostbyname_ex(hostname)
            if "127.0.0.1" not in self.addr_list:
                self.addr_list.append("127.0.0.1")

            # On unix hosts, use sockets to get the other interfaces IPs

            if (platform.system() != 'Windows'):
                for ip_addr in self.__getAllIpAddresses():
                    if ip_addr not in self.addr_list:
                        self.addr_list.append(ip_addr)

        for address in self.addr_list:
            rawaddr = socket.inet_aton(address)
            if len(rawaddr) != 4:
                continue
            if isinstance(rawaddr, str):
                rawaddr = rawaddr[:3] + '\xFF'
            elif isinstance(rawaddr, bytes):
                rawaddr = bytes([b for b in rawaddr[:3]] + [255])
            broadcast = socket.inet_ntoa(rawaddr)
            _set.add(SubNet(24, InetAddress(hostname, address),
                            InetAddress(None, broadcast)))

    def __getUTF8Bytes(self, s):
        return s.encode("UTF-8")

    # Used for tracing
    packetTypes = [
        None,
        "CONF_REQ_INFO",
        "CONF_PEER_INFO",
        "CONF_REQ_SLAVES",
        "CONF_SLAVES_INFO",
        "CONF_PEERS_REMOVED"
    ]

    def __sendDatagramPacket(self, subnet, size, addr, port):
        try:
            if addr is None:
                addr = subnet.broadcast
                port = DISCOVEY_PORT
                for slave in self.slaves:
                    self.__sendDatagramPacket(subnet, size, slave.address,
                                              slave.port)
            if not subnet.contains(addr):
                return False
            if port == self.socket.getsockname()[1] and \
               addr == subnet.address:
                return False

            self.socket.sendto(compat.str2bytes(self.out_buf[:size]),
                               (addr.getHostAddress(), port))

            if __TRACE_DISCOVERY__:
                attrs = None
                if self.out_buf[4] == locator.CONF_PEER_INFO:
                    attrs = self.__parsePeerAttributes(self.out_buf, 8)
                elif self.out_buf[4] == locator.CONF_SLAVES_INFO:
                    attrs = self.__parseIDs(self.out_buf, size)
                elif self.out_buf[4] == locator.CONF_PEERS_REMOVED:
                    attrs = self.__parseIDs(self.out_buf, size)
                self.__traceDiscoveryPacket(False,
                                            self.packetTypes[self.out_buf[4]],
                                            attrs, addr, port)
        except Exception as x:
            self._log("Cannot send datagram packet to %s" % addr, x)
            return False
        return True

    def __parsePeerAttributes(self, data, size):
        """
        Parse peer attributes in CONF_PEER_INFO packet data

        @param data - the packet data
        @param size - the packet size
        @return a map containing the attributes
        """
        attrs = {}
        # Remove packet header
        s = data[8:size].decode("UTF-8")
        l = len(s)
        i = 0
        while i < l:
            i0 = i
            while i < l and s[i] != '=' and s[i] != '\0':
                i += 1
            i1 = i
            if i < l and s[i] == '=':
                i += 1
            i2 = i
            while i < l and s[i] != '\0':
                i += 1
            i3 = i
            if i < l and s[i] == '\0':
                i += 1
            key = s[i0:i1]
            val = s[i2:i3]
            attrs[key] = val
        return attrs

    def __parseIDs(self, data, size):
        """
        Parse list of IDs in CONF_SLAVES_INFO and CONF_PEERS_REMOVED packet
        data.

        @param data - the packet data
        @param size - the packet size
        @return a map containing the IDs
        """
        cnt = 0
        attrs = {}
        s = data[8:].decode("UTF-8")
        l = len(s)
        i = 0
        while i < l:
            i0 = i
            while i < l and s[i] != '\0':
                i += 1
            if i > i0:
                _id = s[i0:i]
                attrs[str(cnt)] = _id
                cnt += 1
            while i < l and s[i] == '\0':
                i += 1
        return attrs

    def __sendPeersRequest(self, addr, port):
        self.out_buf[4] = locator.CONF_REQ_INFO
        for subnet in self.subnets:
            self.__sendDatagramPacket(subnet, 8, addr, port)

    def _sendPeerInfo(self, _peer, addr, port):
        attrs = _peer.getAttributes()
        peer_addr = self.__getInetAddress(attrs.get(peer.ATTR_IP_HOST))
        if peer_addr is None:
            return
        if attrs.get(peer.ATTR_IP_PORT) is None:
            return
        self.out_buf[4] = locator.CONF_PEER_INFO
        i = 8

        for subnet in self.subnets:
            if isinstance(_peer, peer.RemotePeer):
                try:
                    if self.socket.getsockname()[1] != DISCOVEY_PORT:
                        return
                except:
                    pass
                if not subnet.address == self.loopback_addr and \
                   not subnet.address == peer_addr:
                    continue
            if not subnet.address == self.loopback_addr:
                if not subnet.contains(peer_addr):
                    continue
            if i == 8:
                sb = []
                for key in list(attrs.keys()):
                    sb.append(str(key) + '=' + str(attrs.get(key)))
                bt = self.__getUTF8Bytes('\0'.join(sb))
                if i + len(bt) > len(self.out_buf):
                    return
                self.out_buf[i:i + len(bt)] = bt
                i += len(bt)
            if self.__sendDatagramPacket(subnet, i, addr, port):
                subnet.send_all_ok = True

    def __sendEmptyPacket(self, addr, port):
        self.out_buf[4] = locator.CONF_SLAVES_INFO
        for subnet in self.subnets:
            if subnet.send_all_ok:
                continue
            self.__sendDatagramPacket(subnet, 8, addr, port)

    def __sendAll(self, addr, port, sl, tm):
        for subnet in self.subnets:
            subnet.send_all_ok = False
        for peer in list(self.peers.values()):
            self._sendPeerInfo(peer, addr, port)
        if addr is not None and sl is not None and \
           sl.last_req_slaves_time + locator.DATA_RETENTION_PERIOD >= tm:
            self.__sendSlavesInfo(addr, port, tm)
        self.__sendEmptyPacket(addr, port)

    def __sendSlavesRequest(self, subnet, addr, port):
        self.out_buf[4] = locator.CONF_REQ_SLAVES
        self.__sendDatagramPacket(subnet, 8, addr, port)

    def __sendSlaveInfo(self, x, tm):
        ttl = x.last_packet_time + locator.DATA_RETENTION_PERIOD - tm
        if ttl <= 0:
            return
        self.out_buf[4] = locator.CONF_SLAVES_INFO
        for subnet in self.subnets:
            if not subnet.contains(x.address):
                continue
            i = 8
            s = "%d:%s:%s" % (ttl, x.port, x.address.getHostAddress())
            bt = self.__getUTF8Bytes(s)
            self.out_buf[i:i + len(bt)] = bt
            i += len(bt)
            self.out_buf[i] = 0
            i += 1
            for y in self.slaves:
                if not subnet.contains(y.address):
                    continue
                if y.last_req_slaves_time + locator.DATA_RETENTION_PERIOD < tm:
                    continue
                self.__sendDatagramPacket(subnet, i, y.address, y.port)

    def __sendSlavesInfo(self, addr, port, tm):
        self.out_buf[4] = locator.CONF_SLAVES_INFO
        for subnet in self.subnets:
            if not subnet.contains(addr):
                continue
            i = 8
            for x in self.slaves:
                ttl = x.last_packet_time + locator.DATA_RETENTION_PERIOD - tm
                if ttl <= 0:
                    return
                if x.port == port and x.address == addr:
                    continue
                if not subnet.address == self.loopback_addr:
                    if not subnet.contains(x.address):
                        continue
                subnet.send_all_ok = True
                s = "%d:%s:%s" % \
                    (x.last_packet_time, x.port, x.address.getHostAddress())
                bt = self.__getUTF8Bytes(s)
                if i > 8 and i + len(bt) >= PREF_PACKET_SIZE:
                    self.__sendDatagramPacket(subnet, i, addr, port)
                    i = 8
                self.out_buf[i:len(bt)] = bt
                i += len(bt)
                self.out_buf[i] = 0
                i += 1
            if i > 8:
                self.__sendDatagramPacket(subnet, i, addr, port)

    def __isRemote(self, address, port):
        if port != self.socket.getsockname()[1]:
            return True
        for s in self.subnets:
            if s.address == address:
                return False
        return True

    def __handleDatagramPacket(self, p):
        try:
            tm = int(time.time() * 1000)
            buf = p.getData().decode("UTF-8")
            length = p.getLength()
            if length < 8:
                return
            if buf[0] != 'T':
                return
            if buf[1] != 'C':
                return
            if buf[2] != 'F':
                return
            if buf[3] != locator.CONF_VERSION:
                return
            remote_port = p.getPort()
            remote_address = p.getAddress()
            if self.__isRemote(remote_address, remote_port):
                if buf[4] == locator.CONF_PEERS_REMOVED:
                    self.__handlePeerRemovedPacket(p)
                else:
                    sl = None
                    if remote_port != DISCOVEY_PORT:
                        sl = self.__addSlave(remote_address, remote_port, tm,
                                             tm)
                    code = ord(buf[4])
                    if code == locator.CONF_PEER_INFO:
                        self.__handlePeerInfoPacket(p)
                    elif code == locator.CONF_REQ_INFO:
                        self.__handleReqInfoPacket(p, sl, tm)
                    elif code == locator.CONF_SLAVES_INFO:
                        self.__handleSlavesInfoPacket(p, tm)
                    elif code == locator.CONF_REQ_SLAVES:
                        self.__handleReqSlavesPacket(p, sl, tm)
                    for subnet in self.subnets:
                        if not subnet.contains(remote_address):
                            continue
                        delay = int(locator.DATA_RETENTION_PERIOD / 3)
                        if remote_port != DISCOVEY_PORT:
                            delay = int(locator.DATA_RETENTION_PERIOD / 32)
                        elif subnet.address != remote_address:
                            delay = int(locator.DATA_RETENTION_PERIOD / 2)
                        if subnet.last_slaves_req_time + delay <= tm:
                            self.__sendSlavesRequest(subnet, remote_address,
                                                     remote_port)
                            subnet.last_slaves_req_time = tm
                        if subnet.address == remote_address and \
                           remote_port == DISCOVEY_PORT:
                            self.last_master_packet_time = tm
        except Exception as x:
            self._log("Invalid datagram packet received from %s/%s" %
                      (p.getAddress(), p.getPort()), x)

    def __handlePeerInfoPacket(self, p):
        try:
            attrs = self.__parsePeerAttributes(p.getData(), p.getLength())
            if __TRACE_DISCOVERY__:
                self.__traceDiscoveryPacket(True, "CONF_PEER_INFO", attrs, p)
            _id = attrs.get(peer.ATTR_ID)
            if _id is None:
                raise RuntimeError("Invalid peer info: no ID")
            ok = True
            host = attrs.get(peer.ATTR_IP_HOST)
            if host is not None:
                ok = False
                peer_addr = self.__getInetAddress(host)
                if peer_addr is not None:
                    for subnet in self.subnets:
                        if subnet.contains(peer_addr):
                            ok = True
                            break
            if ok:
                _peer = self.peers.get(_id)
                if isinstance(_peer, peer.RemotePeer):
                    _peer.updateAttributes(attrs)
                elif _peer is None:
                    peer.RemotePeer(attrs)
        except Exception as x:
            self._log("Invalid datagram packet received from %s/%s" %
                      (p.getAddress(), p.getPort()), x)

    def __handleReqInfoPacket(self, p, sl, tm):
        if __TRACE_DISCOVERY__:
            self.__traceDiscoveryPacket(True, "CONF_REQ_INFO", None, p)
        self.__sendAll(p.getAddress(), p.getPort(), sl, tm)

    def __handleSlavesInfoPacket(self, p, time_now):
        try:
            attrs = self.__parseIDs(p.getData(), p.getLength())
            if __TRACE_DISCOVERY__:
                self.__traceDiscoveryPacket(True, "CONF_SLAVES_INFO", attrs, p)
            for s in list(attrs.values()):
                i = 0
                l = len(s)
                time0 = i
                while i < l and s[i] != ':' and s[i] != '\0':
                    i += 1
                time1 = i
                if i < l and s[i] == ':':
                    i += 1
                port0 = i
                while i < l and s[i] != ':' and s[i] != '\0':
                    i += 1
                port1 = i
                if i < l and s[i] == ':':
                    i += 1
                host0 = i
                while i < l and s[i] != '\0':
                    i += 1
                host1 = i
                port = int(s[port0:port1])
                timestamp = s[time0:time1]
                host = s[host0:host1]
                if port != DISCOVEY_PORT:
                    addr = self.__getInetAddress(host)
                    if addr is not None:
                        delta = 10006030  # 30 minutes
                        if len(timestamp) > 0:
                            time_val = int(timestamp)
                        else:
                            time_val = time_now
                        if time_val < 3600000:
                            # Time stamp is "time to live" in milliseconds
                            time_val = time_now + int(time_val / 1000) - \
                                locator.DATA_RETENTION_PERIOD
                        elif time_val < int(time_now / 1000) + 50000000:
                            # Time stamp is in seconds
                            time_val = 1000
                        else:
                            # Time stamp is in milliseconds
                            pass
                        if time_val < time_now - delta or \
                           time_val > time_now + delta:
                            msg = "Invalid slave info timestamp: %s -> %s" % (
                                  timestamp,
                                  time.strftime("%Y-%m-%d %H:%M:%S",
                                                time.localtime(time_val /
                                                               1000.)))

                            self._log("Invalid datagram packet received " +
                                      "from %s/%s" % (p.getAddress(),
                                                      p.getPort()),
                                      Exception(msg))
                            time_val = time_now - \
                                int(locator.DATA_RETENTION_PERIOD / 2)
                        self.__addSlave(addr, port, time_val, time_now)
        except Exception as x:
            self._log("Invalid datagram packet received from " +
                      "%s/%s" % (p.getAddress(), p.getPort()), x)

    def __handleReqSlavesPacket(self, p, sl, tm):
        if __TRACE_DISCOVERY__:
            self.__traceDiscoveryPacket(True, "CONF_REQ_SLAVES", None, p)
        if sl is not None:
            sl.last_req_slaves_time = tm
        self.__sendSlavesInfo(p.getAddress(), p.getPort(), tm)

    def __handlePeerRemovedPacket(self, p):
        try:
            attrs = self.__parseIDs(p.getData(), p.getLength())
            if __TRACE_DISCOVERY__:
                self.__traceDiscoveryPacket(True, "CONF_PEERS_REMOVED", attrs,
                                            p)
            for _id in list(attrs.values()):
                _peer = self.peers.get(_id)
                if isinstance(_peer, peer.RemotePeer):
                    _peer.dispose()
        except Exception as x:
            self._log("Invalid datagram packet received from %s/%s" % (
                      p.getAddress(), p.getPort()), x)

    @classmethod
    def getLocator(cls):
        return cls.locator

    def getPeers(self):
        assert protocol.isDispatchThread()
        return self.peers

    def redirect(self, peer, done):
        raise RuntimeError("Channel redirect cannot be done on local peer")

    def sync(self, done):
        raise RuntimeError("Channel sync cannot be done on local peer")

    def addListener(self, listener):
        assert listener is not None
        assert protocol.isDispatchThread()
        self.listeners.append(listener)

    def removeListener(self, listener):
        assert protocol.isDispatchThread()
        self.listeners.remove(listener)

    @classmethod
    def __traceDiscoveryPacket(cls, received, packet_type, attrs, addr,
                               port=None):
        """
        Log that a TCF Discovery packet has be sent or received. The trace is
        sent to stdout. This should be called only if the tracing has been
        turned on.

        @param received
                   True if the packet was sent, otherwise it was received
        @param packet_type
                   a string specifying the type of packet, e.g.,
                   "CONF_PEER_INFO"
        @param attrs
                   a set of attributes relevant to the type of packet
                   (typically a peer's attributes)
        @param addr
                   the network address the packet is being sent to
        @param port
                   the port the packet is being sent to
        """
        assert __TRACE_DISCOVERY__
        if port is None:
            # addr is a InputPacket
            port = addr.getPort()
            addr = addr.getAddress()
        buf = str(packet_type)
        buf += (" sent to ", " received from ")[received]
        buf += "%s/%s" % (addr, port)
        if attrs is not None:
            for key, value in list(attrs.items()):
                buf += "\n\t%s=%s" % (key, value)
        logging.trace(buf)


class LocatorServiceProvider(services.ServiceProvider):
    def get_local_service(self, _channel):
        class CommandServer(channel.CommandServer):
            def command(self, token, name, data):
                LocatorService.locator._command(_channel, token, name, data)
        _channel.addCommandServer(LocatorService.locator, CommandServer())
        return (LocatorService.locator,)

services.add_service_provider(LocatorServiceProvider())
