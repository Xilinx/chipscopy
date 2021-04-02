# Copyright 2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DebugCorePolling service provides operations to manage polling for DebugCore nodes in the Hardware Server.

.. |DebugCorePoll| replace:: :class:`DebugCorePoll`

General Flow:

1. Searches through list of polls and re-uses if desired
2. Register polling DebugCore sequence with hw_server
3. hw_server runs registered polls periodically
    a) performs some matching (determining whether some condition is hit)
    b) sends events when condition is met
4. Deregister poll(s) with hw_server

DebugCoreSequence
^^^^^^^^^^^^^^^^^
List of property |dict| describing a transaction sequence

+-------------------+----------------------+------------------------------------------+
| Name              | Type                 | Description                              |
+===================+======================+==========================================+
| type              | |str|                | Transaction type                         |
|                   |                      |   Read: 'r'                              |
|                   |                      |     Reads from an address                |
|                   |                      |     and returns data                     |
|                   |                      |   Write: 'w'                             |
|                   |                      |     Writes to an address                 |
|                   |                      |   Packet: 'p'                            |
|                   |                      |     Runs a data packet on a node and     |
|                   |                      |     returns result data                  |
+-------------------+----------------------+------------------------------------------+
| name              | |str|                | Name of the seq given by the client      |
+-------------------+----------------------+------------------------------------------+
| addr              | |int|                | Starting byte address of transaction     |
+-------------------+----------------------+------------------------------------------+
| data              | |bytearray|          | Data buffer for transaction.  Used for   |
|                   |                      | both writing and reading buffers         |
+-------------------+----------------------+------------------------------------------+
| size              | |int|                | Number of bytes to read during Read      |
|                   |                      | (default size=4)                         |
|                   |                      | (not used for Write and Packet types)    |
+-------------------+----------------------+------------------------------------------+
| read_size         | |int|                | Number of bytes to read during Packet    |
|                   |                      | transaction.  If not set or zero, don't  |
|                   |                      | read back.                               |
+-------------------+----------------------+------------------------------------------+

Examples
--------
Read/Write/Read Sequence:

::

    seq = [{'type':'r','addr':0x100,'size':4},{'type':'w',addr:0x100,'data':b'ABCD'},{'type':'r','addr':0x100,'size':4}]

    result = [{'type':'r','addr':0x100,'data':b'\x00\x00\x00\x00'},{'type':'r','addr':0x100,'data':b'ABCD'}]


DebugCorePoll
^^^^^^^^^^^^^
Dictionary of properties for a poll

+-------------------+----------------------+------------------------------------------+
| Name              | Type                 | Description                              |
+===================+======================+==========================================+
| name              | |str|                | Name of the Poll given by the client     |
+-------------------+----------------------+------------------------------------------+
| seq               | `DebugCoreSequence`_ | DebugCore Sequence to run at each poll   |
+-------------------+----------------------+------------------------------------------+
| period            | |int|                | Minimum time between polls (ms)          |
+-------------------+----------------------+------------------------------------------+

Extension of `DebugCoreSequence`_ for polling
---------------------------------------------

+-------------------+----------------------+------------------------------------------+
| Name              | Type                 | Description                              |
+===================+======================+==========================================+
| cond              | |str|                | Matching condition string used for       |
|                   |                      | determining a triggering condition.      |
|                   |                      | `Condition Syntax`_                      |
+-------------------+----------------------+------------------------------------------+
| cond_offset       | |int|                | Bit offset of condition matching.        |
|                   |                      | For 'p' type default is 32bits, 0 for 'r'|
+-------------------+----------------------+------------------------------------------+
| bitwise_op        | |str|                | Bitwise operation:                       |
|                   |                      |   'and':                                 |
|                   |                      |     all bits must meet conditions        |
|                   |                      |   'or':                                  |
|                   |                      |     any bit meets condition (default)    |
+-------------------+----------------------+------------------------------------------+

Condition Syntax
----------------
A string indicating how each bit of transaction result is to be matched, low-endian. If any bit in the string meets
the condition then the whole poll is considered triggered.  The remaining transactions are completed and then the
results of the sequence are sent as an event to the listeners of the poll.

+-------------+----------------------------------+
|'X'          | don't care                       |
+-------------+----------------------------------+
|'0'          | match on 0                       |
+-------------+----------------------------------+
|'1'          | match on 1                       |
+-------------+----------------------------------+
|'T'          | toggled value                    |
+-------------+----------------------------------+
|'R'          | rising edge - 0 to 1             |
+-------------+----------------------------------+
|'F'          | falling edge - 1 to 0            |
+-------------+----------------------------------+

Short hand supported strings:

+-------------+----------------------------------+
|'always'     | always throw an event            |
+-------------+----------------------------------+
|'any_one'    | check is any bit is set          |
+-------------+----------------------------------+
|'changes'    | check for a change in any bit    |
+-------------+----------------------------------+

Example:

::

    Check only bit 4 for a changed value = "XXXXTXXXXXXXXXXXXXXXXXXXXXXXXXXX"

    Check if any bit is a changed value = "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT" or "changes"


Service Interface
^^^^^^^^^^^^^^^^^
.. autoclass:: DebugCorePollingProxy
    :members: get_polls, get_context, add_listener, remove_listener, add_poll, remove_poll, retain_poll


Service Events
^^^^^^^^^^^^^^
.. autoclass:: DebugCorePollingListener
    :members:

"""

from typing import Dict, Any, NewType
from chipscopy.tcf.channel import EventListener, fromJSONSequence
from chipscopy.tcf.services import Service, DoneHWCommand, Token
from chipscopy.tcf.services.arguments import from_xargs


NAME = "DebugCorePolling"
"""DebugCorePolling service name."""

DebugCorePoll = NewType("DebugCorePoll", Dict[str, Any])

DebugCoreSequence = NewType("DebugCoreSequence", Dict[str, Any])


class DebugCorePollingListener(object):
    """Debug node event listener is notified when a poll for a DebugNode has been triggered."""

    def poll_added(self, poll: DebugCorePoll):
        """
        Called when a new poll has been registered

        :param poll: Properties of poll
        """
        pass

    def poll_removed(self, poll_ctx: str):
        """
        Called when a poll has been removed.

        :param poll_ctx: Poll context id
        """
        pass

    def poll_event(self, poll_ctx: str, props: Dict):
        """
        Called a registered poll condition has been triggered.

        :param poll_ctx: Poll context id
        :param props: Result sequence and other properties of triggering poll
        """
        pass


class DebugCorePollingProxy(Service):
    """TCF DebugCorePolling service interface."""

    def __init__(self, channel):
        super(DebugCorePollingProxy, self).__init__(channel)
        self.listeners = {}

    def getName(self):
        return NAME

    def get_polls(self, node_id: str = "", done: DoneHWCommand = None) -> Token:
        """
        Gets list of polls registered for the given node ("" means give all polls).

        :param node_id: Context Node ID
        :param done: Callback when command is complete
        :return: Token of request
        :done result: List of `DebugCorePoll`_
        """
        return self.send_xicom_command("getPolls", (node_id,), done)

    def get_context(self, poll_id: str, done: DoneHWCommand) -> Token:
        """
        Gets context properties of a poll.

        :param poll_id: Context Poll ID
        :param done: Callback when command is complete
        :return: Token of request
        """
        return self.send_xicom_command("getContext", (poll_id,), done)

    def add_poll(self, node_id: str, poll: DebugCorePoll, done: DoneHWCommand = None) -> Token:
        """
        Registers a new `DebugCorePoll`_ with the Hardware Server.

        :param node_id: Context node ID
        :param poll: Dict describing the poll
        :param done: Callback when command is complete
        :returns: Token of command request
        :done result: Context ID of new `DebugCorePoll`_
        """
        return self.send_xicom_command("addPoll", (node_id, poll), done)

    def remove_poll(self, poll_id: str, done: DoneHWCommand = None) -> Token:
        """
        Deregisters a `DebugCorePoll`_ with the Hardware Server.

        :param poll_id: Context poll ID
        :param done: Callback when command is complete
        :returns: Token of command request
        """
        return self.send_xicom_command("removePoll", (poll_id,), done)

    def retain_poll(self, poll_id: str, done: DoneHWCommand = None) -> Token:
        """
        Keeps a poll even if the original requestor of the poll removes it.  This also adds this peer to the list of
        listeners of the poll from the Hardware Server.

        :param poll_id: Context poll ID
        :param done: Callback when command is complete
        :returns: Token of command request
        """
        return self.send_xicom_command("retainPoll", (poll_id,), done)

    def add_listener(self, listener: DebugCorePollingListener):
        """Add DebugCore service event listener.

        :param listener: Event listener implementation.
        """
        channel_listener = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, channel_listener)
        self.listeners[listener] = channel_listener

    def remove_listener(self, listener: DebugCorePollingListener):
        """Remove DebugCore service event listener.

        :param listener: Event listener implementation.
        """
        channel_listener = self.listeners.get(listener)
        if channel_listener:
            del self.listeners[listener]
            self.channel.removeEventListener(self, channel_listener)


class ChannelEventListener(EventListener):
    def __init__(self, service, listener):
        self.service = service
        self.listener = listener
        self._event_handlers = {
            "pollAdded": self._poll_add,
            "pollRemoved": self._poll_remove,
            "pollEvent": self._poll_event,
        }

    def _poll_add(self, args):
        args = from_xargs(args)
        assert len(args) == 1
        poll = args[0]
        self.listener.poll_added(poll)

    def _poll_remove(self, args):
        args = from_xargs(args)
        assert len(args) == 1
        poll_id = args[0]
        self.listener.poll_removed(poll_id)

    def _poll_event(self, args):
        args = from_xargs(args)
        assert len(args) == 2
        poll_id = args[0]
        props = args[1]
        self.listener.poll_event(poll_id, props)

    def event(self, name, data):
        try:
            args = fromJSONSequence(data)
            try:
                handler = self._event_handlers[name]
                handler(args)
            except KeyError:
                raise IOError("DebugCorePolling service: unknown event: " + name)
        except Exception as x:
            import sys

            x.tb = sys.exc_info()[2]
            self.service.channel.terminate(x)


DebugCorePollingService = DebugCorePollingProxy
