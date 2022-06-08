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

"""
.. |JtagContext| replace::   :class:`JtagContext`

Jtag service provides basic operations to run Jtag-based transactions on a target.


.. _properties:

Properties
^^^^^^^^^^
+--------------------------+-------+------------------------------------------+
| Name                     | Type  | Description                              |
+==========================+=======+==========================================+
| ID                       | |str| | Context ID of the node in the hw_server  |
+--------------------------+-------+------------------------------------------+
| ParentID                 | |str| | Context ID of the parent node in the     |
|                          |       | hw_server.                               |
+--------------------------+-------+------------------------------------------+
| Name                     | |str| | Name of Jtag node                        |
+--------------------------+-------+------------------------------------------+
| idCode                   | |int| | IDCODE of Jtag node                      |
+--------------------------+-------+------------------------------------------+
| irLen                    | |int| | IR length Jtag node                      |
+--------------------------+-------+------------------------------------------+
| isTap                    | |int| | flag indicating if node is a JTAG tap    |
+--------------------------+-------+------------------------------------------+
| isMux                    | |int| | flag indicating if node is a mux         |
+--------------------------+-------+------------------------------------------+
| isBranch                 | |int| | flag indicating whether node is branched |
+--------------------------+-------+------------------------------------------+
| isActive                 | |int| | flag indicating whether node is active   |
+--------------------------+-------+------------------------------------------+

"""

from typing import Dict, List, Any, NewType, ByteString
from chipscopy.tcf import channel
from chipscopy.tcf.services import Service, DoneHWCommand, Token

JtagNode = NewType("JtagNode", Dict[str, Any])

JTAG_SERVICE = "Jtag"


class JtagContext(object):
    """Jtag context class.
    :param props: Properties to initialise this context with. See
    `Properties`_.
    :type props: |dict|
    """

    def __init__(self, service, props):
        self._props = {
            "ID": "",
            "ParentID": "",
            "Name": "",
            "idCode": 0,
            "irLen": 0,
            "isTap": False,
            "isMux": False,
            "isBranch": False,
            "isActive": False,
        }
        self._props.update(props)
        self.service = service

    def __str__(self):
        return "[Jtag Context %s]" % self._props

    @property
    def props(self):
        """Get context properties. See `Properties`_ definitions for property
        names.
        Context properties are read only, clients should not try to modify
        them.
        :returns: A |dict| of context properties.
        """
        return self._props

    def __getattr__(self, item):
        return self._props.get(item)


class JtagListener(object):
    """Jtag event listener is notified when jtag context hierarchy changes,
    and when jtag is modified by Jtag service commands.
    """

    def contextAdded(self, contexts: List[JtagNode]):
        """Called when a new jtag access context(s) is created.
        :param contexts: A list of |JtagContext| properties which have been
        added to jtag space.
        :type contexts: |list|

        """
        pass

    def contextChanged(self, contexts: List[JtagNode]):
        """Called when a jtag access context(s) properties changed.
        :param contexts: A list of |JtagContext| properties which have been
        changed in jtag space.

        :type contexts: |list|

        """
        pass

    def contextRemoved(self, context_ids: List[str]):
        """Called when jtag access context(s) is removed.
        :param context_ids: A list of the IDs of jtag contexts which have
        been removed from jtag space.

        :type context_ids: |list|

        """
        pass


class JtagProxy(Service):
    """TCF Jtag service interface."""

    def __init__(self, channel):
        super(JtagProxy, self).__init__(channel)
        self.listeners = {}

    def getName(self):
        """
        Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return JTAG_SERVICE

    def get_context(self, context_id: str, done: DoneHWCommand) -> Dict[str, Any]:
        """
        Gets context information on a given context id

        :param context_id: Context id of the context
        :param done: Callback with result and any error.
        :return: A dictionary of context parameters
        """
        done = self._makeCallback(done)
        service = self

        class DoneContext(DoneHWCommand):
            def doneHW(self, token, error, args):
                context = None
                if not error and len(args) > 0:
                    context = JtagContext(service, args[0])
                done.doneHW(token, error, context)

        return self.send_command("getContext", (context_id,), DoneContext())

    def get_children(self, context_id: str, done: DoneHWCommand) -> List[str]:
        """
        Gets the children of a given context.  If no context is given then gets top level contexts.

        :param context_id: Context id of desired context
        :param done: Callback with result and any error.
        :return: List of child contexts
        """
        done = self._makeCallback(done)
        if not context_id:
            context_id = ""

        class DoneChildren(DoneHWCommand):
            def doneHW(self, token, error, args):
                context_ids = []
                if not error and len(args) > 0:
                    context_ids = args[0]
                done.doneHW(token, error, context_ids)

        return self.send_command("getChildren", (context_id,), DoneChildren())

    def get_capabilities(self, context_id: str, done: DoneHWCommand) -> Dict[str, Any]:
        """
        Gets the capabilites of a given context.

        :param context_id: Context id of the context
        :param done: Callback with result and any error.
        :return: A dictionary of the capabilities
        """
        done = self._makeCallback(done)
        return self.send_command("getCapabilities", (context_id,), done)

    def set_option(
        self, context_id: str, key: str, value: str or int, done: DoneHWCommand
    ) -> Token:
        """
        Sets an option for a Jtag context

        :param context_id: Context id of the context
        :param key: Name of the option
        :param value: New value of the option
        :param done: Callback with the result and any error
        :return: Token of request
        """
        return self.send_xicom_command("setOption", (context_id, key, value), done)

    def get_option(self, context_id: str, key: str, done: DoneHWCommand) -> Token:
        """
        Retrieves an option value for a specific Jtag context.  The value is returned in the results

        :param context_id: Context id of the context
        :param key: Name of the option
        :param done: Callback with the result and any error
        :return: Token of request
        """
        return self.send_xicom_command("getOption", (context_id, key), done)

    def lock(self, context_id: str, done: DoneHWCommand) -> Token:
        """
        Locks a specific Jtag context

        :param context_id: Context id of the context
        :param done: Callback with the result and any error
        :return: Token of request
        """
        return self.send_xicom_command("lock", (context_id,), done)

    def unlock(self, context_id: str, done: DoneHWCommand) -> Token:
        """
        Unlocks a specific Jtag context

        :param context_id: Context id of the context
        :param done: Callback with the result and any error
        :return: Token of request
        """
        return self.send_xicom_command("unlock", (context_id,), done)

    def sequence(
        self, context_id: str, commands: list, data: ByteString, done: DoneHWCommand
    ) -> Token:
        """
        Run JTAG sequence operations contained in list of commands

        :param context_id: Context id of the context
        :param commands: List of JTAG sequence operations and their parameters
        :param data: Byte string of data corresponding to specified list of commands
        :param done: Callback with the result and any error
        :return: Token of request
        """
        return self.send_xicom_command("sequence", (context_id, dict(), commands, data), done)

    def add_listener(self, listener: JtagListener):
        """Add Jtag service event listener.
        :param listener: Event listener implementation.
        """
        l = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, l)
        self.listeners[listener] = l

    def remove_listener(self, listener: JtagListener):
        """Remove Jtag service event listener.
        :param listener: Event listener implementation.
        """
        l = self.listeners.get(listener)
        if l:
            del self.listeners[listener]
            self.channel.removeEventListener(self, l)


class ChannelEventListener(channel.EventListener):
    def __init__(self, service, listener):
        self.service = service
        self.listener = listener

    def event(self, name, data):
        try:
            args = channel.fromJSONSequence(data)
            if name == "contextAdded":
                assert len(args) == 1
                self.listener.contextAdded(_toContextArray(self.service, args[0]))
            elif name == "contextChanged":
                assert len(args) == 1
                self.listener.contextChanged(_toContextArray(self.service, args[0]))
            elif name == "contextRemoved":
                assert len(args) == 1
                self.listener.contextRemoved(args[0])
            else:
                raise IOError("Memory service: unknown event: " + name)
        except Exception as x:
            import sys

            x.tb = sys.exc_info()[2]
            self.service.channel.terminate(x)


def _toContextArray(svc, o):
    if o is None:
        return None
    ctx = []
    for m in o:
        ctx.append(JtagContext(svc, m))
    return ctx
