# *****************************************************************************
# * Copyright (c) 2011, 2013-2014 Wind River Systems, Inc. and others.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Wind River Systems - initial API and implementation
# *****************************************************************************

"""Locator service uses transport layer to search for peers and to collect data
about peer's attributes and capabilities (services).

.. |getAgentID| replace:: :meth:`~LocatorService.getAgentID`
.. |redirect| replace:: :meth:`~LocatorService.redirect`
.. |sync| replace:: :meth:`~LocatorService.sync`
.. |DoneGetAgentID| replace:: :class:`DoneGetAgentID`
.. |DoneRedirect| replace:: :class:`DoneRedirect`
.. |DoneSync| replace:: :class:`DoneSync`
.. |LocatorListener| replace:: :class:`LocatorListener`
.. |Peer| replace:: :class:`~tcf.peer.Peer`

Discovery mechanism depends on transport protocol and is part of that protocol
handler. Targets, known to other hosts, can be found through remote instances
of Locator service.

Automatically discovered targets require no further configuration. Additional
targets can be configured manually.

Clients should use :meth:`tcf.protocol.getLocator` to obtain local instance of
locator, then :meth:`LocatorService.getPeers` can be used to get list of
available peers (hosts and targets).

Service Methods
---------------
.. autodata:: NAME
.. autoclass:: LocatorService

addListener
^^^^^^^^^^^
.. automethod:: LocatorService.addListener

getAgentID
^^^^^^^^^^
.. automethod:: LocatorService.getAgentID

getName
^^^^^^^
.. automethod:: LocatorService.getName

getPeers
^^^^^^^^
.. automethod:: LocatorService.getPeers

redirect
^^^^^^^^
.. automethod:: LocatorService.redirect

removeListener
^^^^^^^^^^^^^^
.. automethod:: LocatorService.removeListener

sync
^^^^
.. automethod:: LocatorService.sync

Callback Classes
----------------
DoneGetAgentID
^^^^^^^^^^^^^^
.. autoclass:: DoneGetAgentID
    :members:

DoneRedirect
^^^^^^^^^^^^
.. autoclass:: DoneRedirect
    :members:

DoneSync
^^^^^^^^
.. autoclass:: DoneSync
    :members:

Listener
--------
LocatorListener
^^^^^^^^^^^^^^^
.. autoclass:: LocatorListener
    :members:
"""

from .. import services
from typing import Any, Dict, List

DATA_RETENTION_PERIOD = 60 * 1000
""" Peer data retention period in milliseconds."""
CONF_VERSION = '2'
""" Auto-configuration protocol version."""

# Auto-configuration command and response codes.
CONF_REQ_INFO = 1
CONF_PEER_INFO = 2
CONF_REQ_SLAVES = 3
CONF_SLAVES_INFO = 4
CONF_PEERS_REMOVED = 5

NAME = "Locator"
"""Locator service name."""


class LocatorService(services.Service):
    """TCF Locator service interface."""

    def getAgentID(self, done):
        """Get agent ID of the agent providing the locator service.

        :param done: Call back interface called when operation is completed.
        :type done: |DoneGetAgentID|
        """
        raise NotImplementedError("Abstract method")

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def getPeers(self):
        """Get map (ID -> IPeer) of available peers (hosts and targets).

        The method returns cached (currently known to the framework) list of
        peers. The list is updated according to event received from transport
        layer.

        :returns: A |dict| of Peer ID -> |Peer| association.
        """
        raise NotImplementedError("Abstract method")

    def redirect(self, peer, done):
        """Redirect this service channel to given peer using this service as a
        proxy.

        :param peer: Peer ID or attributes map.
        :type peer: |basestring|
        :param done: Call back interface called when operation is completed.
        :type done: |DoneRedirect|
        """
        raise NotImplementedError("Abstract method")

    def sync(self, done):
        """Call back after TCF messages sent to this target up to this moment
        are delivered.

        This method is intended for synchronization of messages across multiple
        channels.

        .. note:: Cross channel synchronization can reduce performance and
                  throughput. Most clients don't need channel synchronization
                  and should not call this method.

        :param done: Will be executed by dispatch thread after communication
                     messages are delivered to corresponding targets.
        :type done: |DoneSync|

        This is internal API, TCF clients should use module
        :mod:`tcf.protocol`.
        """
        raise NotImplementedError("Abstract method")

    def addListener(self, listener):
        """Add a listener for Locator service events.

        :param listener: Listener to add.
        :type listener: |LocatorListener|
        """
        raise NotImplementedError("Abstract method")

    def removeListener(self, listener):
        """Remove a listener for Locator service events.

        :param listener: Listener to remove.
        :type listener: |LocatorListener|
        """
        raise NotImplementedError("Abstract method")

    def get_remote_peers(self, done: services.DoneHWCommand) -> List[Dict[str, str]]:
        """Get attributes of available peers (hosts and targets) on remote server.

        The method returns cached (currently known to the framework) list of
        peers. The list is updated according to event received from transport
        layer.

        :returns: A |list| of |dict| consisting of |Peer| Attributes.
        """
        raise NotImplementedError("Abstract method")

    def get_remote_channels(self, done: services.DoneHWCommand) -> Dict[str, str]:
        """Get attributes of open channels on a remote server.

        :returns: A |list| of |dict| consisting of |Channel| Attributes.
        """
        raise NotImplementedError("Abstract method")

    def connect_remote_peer(self, peer_attrib: Dict[str, str], done: services.DoneHWCommand) -> Dict[str, str]:
        """Attempts to connect and open a channel with given peer.

        :param peer_attrib: Attributes of the desired peer to which to connect.
        :param done: Callback with result and any error.
        :returns: A |dict| consisting of connected |Peer| Attributes if successful.
        """
        raise NotImplementedError("Abstract method")

    def disconnect_remote_peer(self, peer_attrib: Dict[str, str], done: services.DoneHWCommand) -> bool:
        """Attempts to disconnect and close channel of given peer.

        :param peer_attrib: Attributes of the desired peer to which to disconnect.
        :param done: Callback with result and any error.
        :returns: True if channel is closed.
        """
        raise NotImplementedError("Abstract method")


class DoneGetAgentID(object):
    """Client call back interface for |getAgentID|."""

    def doneGetAgentID(self, token, error, agentID):
        """Called when a peer agent ID request is done.

        :param token: TCF request token corresponding to this done getAgentID
                      call.
        :param error: error description if operation failed, **None** if
                      succeeded.
        :param agentID: Retrieved agent ID.
        :type agentID: |basestring|
        """
        pass


class DoneRedirect(object):
    """Client call back interface for |redirect|."""

    def doneRedirect(self, token, error):
        """Called when a peer redirection request has been done.

        :param token: TCF request token corresponding to this done redirect
                      call.
        :param error: error description if operation failed, **None** if
                      succeeded.
        """
        pass


class DoneSync(object):
    """Client call back interface for |sync|."""
    def doneSync(self, token):
        """Called when a peer sync request has been done.

        :param token: TCF request token corresponding to this done sync call.
        """
        pass


class LocatorListener(object):
    """TCF peer locator listener."""

    def peerAdded(self, peer):
        """Called when a new peer has been added to the known peers.

        :param peer: New peer description.
        :type peer: |Peer|
        """
        pass

    def peerChanged(self, peer):
        """Called when one of the known peers has been modified.

        :param peer: New peer description.
        :type peer: |Peer|
        """
        pass

    def peerRemoved(self, peerID):
        """Called when one of the peers has been shut down.

        :param peerId: Id of the peer which shut down.
        :type peerId: |basestring|
        """
        pass

    def peerHeartBeat(self, peerID):
        """Called when one of the peers says he is alive.

        :param peerId: Id of the peer which sent a heartbeat
        :type peerId: |basestring|
        """
        pass
