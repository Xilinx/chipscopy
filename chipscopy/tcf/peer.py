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

"""Both hosts and targets are represented by objects implementing Peer
interface.

A peer can act as host or target depending on services it implements. List of
currently known peers can be retrieved by calling |getPeers|.

A TCF agent houses one or more service managers. A service manager has a one or
more services to expose to the world. The service manager creates one or more
peers to represent itself, one for every access path the agent is reachable by.

For example, in agents accessible via TCP/IP, the service manager would create
a peer for every subnet it wants to participate in. All peers of particular
service manager represent identical sets of services.

.. |getPeers| replace:: :meth:`tcf.services.locator.LocatorService.getPeers`
.. |invokeAndWait| replace:: :func:`~tcf.protocol.invokeAndWait`
.. |AssertionError| replace:: :exc:`~exception.AssertionError`

Properties
----------
+-------------------------+--------------+------------------------------------+
| Name                    | Type         | Description                        |
+=========================+==============+====================================+
| ATTR_ID                 | |basestring| | Peer unique ID.                    |
+-------------------------+--------------+------------------------------------+
| ATTR_SERVICE_MANAGER_ID | |basestring| | Unique ID of service manager that  |
|                         |              | is represented by this peer.       |
+-------------------------+--------------+------------------------------------+
| ATTR_AGENT_ID           | |basestring| | Agent unique ID.                   |
+-------------------------+--------------+------------------------------------+
| ATTR_NAME               | |basestring| | Peer name.                         |
+-------------------------+--------------+------------------------------------+
| ATTR_OS_NAME            | |basestring| | Name of the peer operating system. |
+-------------------------+--------------+------------------------------------+
| ATTR_TRANSPORT_NAME     | |basestring| | Transport name, for example TCP,   |
|                         |              | SSL ...                            |
+-------------------------+--------------+------------------------------------+
| ATTR_PROXY              | |bool|       | If present, indicates that the peer|
|                         |              | can forward traffic to other peers.|
+-------------------------+--------------+------------------------------------+
| ATTR_IP_HOST            | |basestring| | Host DNS name or IP address.       |
+-------------------------+--------------+------------------------------------+
| ATTR_IP_ALIASES         | |list|       | Optional list of host aliases.     |
+-------------------------+--------------+------------------------------------+
| ATTR_IP_ADDRESSES       | |list|       | Optional list of host addresses.   |
+-------------------------+--------------+------------------------------------+
| ATTR_IP_PORT            | |int|        | IP port number, must be decimal    |
|                         |              | number.                            |
+-------------------------+--------------+------------------------------------+


Classes
-------
Peer
^^^^
.. autoclass:: Peer
    :members:
"""

import os
import time
from . import protocol, transport, services, channel
from .services import locator

ATTR_ID = "ID"
ATTR_SERVICE_MANAGER_ID = "ServiceManagerID"
ATTR_AGENT_ID = "AgentID"
ATTR_NAME = "Name"
ATTR_OS_NAME = "OSName"
ATTR_TRANSPORT_NAME = "TransportName"
ATTR_PROXY = "Proxy"
ATTR_IP_HOST = "Host"
ATTR_IP_ALIASES = "Aliases"
ATTR_IP_ADDRESSES = "Addresses"
ATTR_IP_PORT = "Port"


class Peer(object):
    """TCF agent peer.

    :param attrs: Peer attributes to initialise this peer with.
    :type attrs: |dict|
    """
    def __init__(self, attrs):
        self.attrs = attrs or {}

    def __repr__(self):
        return str(self.__class__.__name__) + '(' + repr(self.attrs) + ')'

    def __str__(self):
        res = str(self.__class__.__name__) + ' ['
        res += ATTR_ID + '=' + str(self.attrs.get(ATTR_ID))
        res += ', ' + ATTR_NAME + '=' + str(self.attrs.get(ATTR_NAME))
        res += ', ' + ATTR_PROXY + '=' + str(self.attrs.get(ATTR_PROXY))
        res += ', ' + ATTR_OS_NAME + '=' + str(self.attrs.get(ATTR_OS_NAME))
        res += ', ' + ATTR_AGENT_ID + '=' + str(self.attrs.get(ATTR_AGENT_ID))
        res += ', ' + ATTR_IP_ADDRESSES + '=' + \
               str(self.attrs.get(ATTR_IP_ADDRESSES))
        res += ', ' + ATTR_IP_ALIASES + '=' + \
               str(self.attrs.get(ATTR_IP_ALIASES))
        res += ', ' + ATTR_IP_HOST + '=' + str(self.attrs.get(ATTR_IP_HOST))
        res += ', ' + ATTR_IP_PORT + '=' + str(self.attrs.get(ATTR_IP_PORT))
        res += ', ' + ATTR_SERVICE_MANAGER_ID + '=' + \
               str(self.attrs.get(ATTR_SERVICE_MANAGER_ID))
        res += ', ' + ATTR_TRANSPORT_NAME + '=' + \
               str(self.attrs.get(ATTR_TRANSPORT_NAME))
        res += ']'
        return res

    def getAddresses(self):
        """Get this peer IP addresses.

        :returns: A |list| representing this peer possible IP addresses, or an
                  empty list.
        """
        return self.attrs.get(ATTR_IP_ADDRESSES, [])

    def getAgentID(self):
        """Get this peer agent ID.

        :returns: This peer's agent unique ID or an empty string

        :raises: An |AssertionError| if this method is not called from the
                 dispatch thread.

        .. seealso:: |invokeAndWait|
        """
        assert protocol.isDispatchThread()
        return self.attrs.get(ATTR_AGENT_ID, '')

    def getAliases(self):
        """Get this peer host name aliases.

        :returns: A |list| representing this peer possible host name aliases,
                  or an empty list.
        """
        return self.attrs.get(ATTR_IP_ALIASES, [])

    def getAttributes(self):
        """Get this peer attributes.

        :returns: A |dict| of this peer attributes.
        """
        return self.attrs

    def getID(self):
        """Get this peer ID.

        :returns: A |basestring| representing this peer unique ID, or an empty
                  string.
        """
        return self.attrs.get(ATTR_ID, '')

    def getHost(self):
        """Get this peer host name.

        :returns: A |basestring| representing this peer host name, or an empty
                  string.
        """
        return self.attrs.get(ATTR_IP_HOST, '')

    def getName(self):
        """Get this peer name.

        :returns: A |basestring| representing this peer name, or an empty
                  string.
        """
        return self.attrs.get(ATTR_NAME, '')

    def getOSName(self):
        """Get this peer's agent OS name.

        :returns: A |basestring| representing this peer agent OS name or an
                  empty string.
        """
        return self.attrs.get(ATTR_OS_NAME, '')

    def getPort(self):
        """Get this peer's communication port.

        :returns: A |basestring| representing this peer communication port
                  number.
        """
        return self.attrs.get(ATTR_IP_PORT, '')

    def getServiceManagerID(self):
        """Get the peer service manager ID.

        :returns: A |basestring| representing this peer's service manager
                  unique ID, or an empty string.

        :raises: An |AssertionError| if this method is not
                 called from the dispatch thread.
        """
        assert protocol.isDispatchThread()
        return self.attrs.get(ATTR_SERVICE_MANAGER_ID, '')

    def getTransportName(self):
        """Get this peer's transport name.

        :returns: this peer agent transport name or an empty string

        .. seealso:: |invokeAndWait|
        """
        return self.attrs.get(ATTR_TRANSPORT_NAME, '')

    def isProxy(self):
        """Check if this peer is a proxy.

        :returns: A |bool| stating if this peer is a proxy or not.
        """
        return self.attrs.get(ATTR_PROXY, False)

    def openChannel(self):
        """Open channel to communicate with this peer.

        .. note:: The channel is not fully open yet when this method returns.
                  Its state is channel.STATE_OPENING.
                  Protocol.ChannelOpenListener and channel.ChannelListener
                  listeners will be called when the channel will change state
                  to open or closed. Clients are supposed to register
                  channel.ChannelListener right after calling openChannel(),
                  or, at least, in same dispatch cycle.

        For example:

        .. code-block:: python

            import tcf.peer as peer

            channel = peer.openChannel()
            channel.addChannelListener(...)
        """
        raise RuntimeError("Abstract method")


class TransientPeer(Peer):
    """
    Transient implementation of IPeer interface.
    Objects of this class are not tracked by Locator service.
    See AbstractPeer for IPeer objects that should go into the Locator table.
    """
    def __init__(self, attrs):
        self.rw_attrs = {}
        self.rw_attrs.update(attrs)
        # TODO readonly map
        ro_attrs = {}
        ro_attrs.update(self.rw_attrs)
        super(TransientPeer, self).__init__(ro_attrs)

    def openChannel(self):
        return transport.openChannel(self)


class LocalPeer(TransientPeer):
    """
    LocalPeer object represents local end-point of TCF communication channel.
    There should be exactly one such object in a TCF agent.
    The object can be used to open a loop-back communication channel that
    allows the agent to access its own services same way as remote services.
    Note that "local" here is relative to the agent, and not same as in
    "local host".
    """
    def __init__(self):
        super(LocalPeer, self).__init__(self.createAttributes())

    def createAttributes(self):
        attrs = {
            ATTR_ID: "TCFLocal",
            ATTR_SERVICE_MANAGER_ID: services.getServiceManagerID(),
            ATTR_AGENT_ID: protocol.getAgentID(),
            ATTR_NAME: "Local Peer",
            ATTR_OS_NAME: os.name,
            ATTR_TRANSPORT_NAME: "Loop"
        }
        return attrs


class AbstractPeer(TransientPeer):
    """
    Abstract implementation of IPeer interface.
    Objects of this class are stored in Locator service peer table.
    The class implements sending notification events to Locator listeners.
    See TransientPeer for IPeer objects that are not stored in the Locator
    table.
    """

    def __init__(self, attrs):
        super(AbstractPeer, self).__init__(attrs)
        assert protocol.isDispatchThread()
        self.last_heart_beat_time = 0
        _id = self.getID()
        assert _id
        peers = protocol.getLocator().getPeers()
        if isinstance(peers.get(_id), RemotePeer):
            peers.get(_id).dispose()
        assert _id not in peers
        peers[_id] = self
        self.sendPeerAddedEvent()

    def dispose(self):
        assert protocol.isDispatchThread()
        _id = self.getID()
        assert _id
        peers = protocol.getLocator().getPeers()
        assert peers.get(_id) == self
        del peers[_id]
        self.sendPeerRemovedEvent()

    def onChannelTerminated(self):
        # A channel to this peer was terminated:
        # not delaying next heart beat helps client to recover much faster.
        self.last_heart_beat_time = 0

    def updateAttributes(self, attrs):
        equ = True
        assert attrs.get(ATTR_ID) == self.rw_attrs.get(ATTR_ID)
        for key in list(self.rw_attrs.keys()):
            if self.rw_attrs.get(key) != attrs.get(key):
                equ = False
                break
        for key in list(attrs.keys()):
            if attrs.get(key) != self.rw_attrs.get(key):
                equ = False
                break
        timeVal = int(time.time() * 1000)
        if not equ:
            self.rw_attrs.clear()
            self.rw_attrs.update(attrs)
            for l in protocol.getLocator().getListeners():
                try:
                    l.peerChanged(self)
                except Exception as x:
                    protocol.log("Unhandled exception in Locator listener", x)
            try:
                args = [self.rw_attrs]
                protocol.sendEvent(locator.NAME, "peerChanged",
                                   channel.toJSONSequence(args))
            except IOError as x:
                protocol.log("Locator: failed to send 'peerChanged' event", x)
            self.last_heart_beat_time = timeVal
        elif self.last_heart_beat_time + \
                int(locator.DATA_RETENTION_PERIOD / 4) < timeVal:
            for l in protocol.getLocator().getListeners():
                try:
                    l.peerHeartBeat(attrs.get(ATTR_ID))
                except Exception as x:
                    protocol.log("Unhandled exception in Locator listener", x)
            try:
                args = [self.rw_attrs.get(ATTR_ID)]
                protocol.sendEvent(locator.NAME, "peerHeartBeat",
                                   channel.toJSONSequence(args))
            except IOError as x:
                protocol.log(
                    "Locator: failed to send 'peerHeartBeat' event", x)
            self.last_heart_beat_time = timeVal

    def sendPeerAddedEvent(self):
        for l in protocol.getLocator().getListeners():
            try:
                l.peerAdded(self)
            except Exception as x:
                protocol.log("Unhandled exception in Locator listener", x)
        try:
            args = [self.rw_attrs]
            protocol.sendEvent(locator.NAME, "peerAdded",
                               channel.toJSONSequence(args))
        except IOError as x:
            protocol.log("Locator: failed to send 'peerAdded' event", x)
        self.last_heart_beat_time = int(time.time() * 1000)

    def sendPeerRemovedEvent(self):
        for l in protocol.getLocator().getListeners():
            try:
                l.peerRemoved(self.rw_attrs.get(ATTR_ID))
            except Exception as x:
                protocol.log("Unhandled exception in Locator listener", x)
        try:
            args = [self.rw_attrs.get(ATTR_ID)]
            protocol.sendEvent(locator.NAME, "peerRemoved",
                               channel.toJSONSequence(args))
        except IOError as x:
            protocol.log("Locator: failed to send 'peerRemoved' event", x)


class RemotePeer(AbstractPeer):
    """
    RemotePeer objects represent TCF agents that Locator service discovered on
    local network.
    This includes both local host agents and remote host agents.
    Note that "remote peer" means any peer accessible over network,
    it does not imply the agent is running on a "remote host".
    If an agent binds multiple network interfaces or multiple ports, it can be
    represented by multiple RemotePeer objects - one per each network
    address/port combination.
    RemotePeer objects life cycle is managed by Locator service.
    """

    def __init__(self, attrs):
        super(RemotePeer, self).__init__(attrs)
        self.last_update_time = int(time.time() * 1000)

    def updateAttributes(self, attrs):
        super(RemotePeer, self).updateAttributes(attrs)
        self.last_update_time = int(time.time() * 1000)

    def getLastUpdateTime(self):
        return self.last_update_time
