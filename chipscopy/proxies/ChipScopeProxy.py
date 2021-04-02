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

from typing import List, Dict, Any
from chipscopy.tcf.channel import EventListener, fromJSONSequence
from chipscopy.tcf.services import Service, DoneHWCommand, Token
from chipscopy.tcf.services.arguments import from_xargs


NAME = "ChipScope"
"""ChipScope service name."""


class InvalidContextException(Exception):
    pass


class ChipScopeListener(object):
    """Debug node event listener is notified when debug node hierarchy changes,
    and when node is modified by DebugCore service commands.
    """

    def node_added(self, node_ctx: str, props: Dict[str, Any]):
        """
        Called when a new Debug Node was added
        :param node_ctx: Debug node context id
        :param props: Debug node properties added
        """
        pass

    def node_changed(self, node_ctx: str, props: Dict[str, Any]):
        """
        Called when a new Debug Node was changed
        :param node_ctx: Debug node context id
        :param props: Debug node properties changed
        """
        pass

    def node_removed(self, node_ctx: str):
        """
        Called when a new Debug Node was removed
        :param node_ctx: Debug node context id
        """
        pass


class ChipScopeProxy(Service):
    """TCF ChipScope service interface."""

    def __init__(self, channel):
        super(ChipScopeProxy, self).__init__(channel)
        self.listeners = {}

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def get_chipscope_server_version_info(self, done: DoneHWCommand) -> Token:
        """
        Returns the current package version
        :param done:
        :return: dict containing release specific version info
        """
        return self.send_xicom_command("getChipscopeServerVersionInfo", (), done)

    def get_children(self, parent_id: str, done: DoneHWCommand) -> Token:
        """
        Gets list of child nodes on a given hw_server channel and context id of parent node ("" is root).
        :param parent_id: Parent node ID
        :param done: Callback when command is complete
        :return: Token of request
        """
        return self.send_xicom_command("getChildren", (parent_id,), done)

    def get_context(self, node_id: str, done: DoneHWCommand) -> Token:
        """
        Gets context properties of a nodes on a given hw_server channel.
        :param node_id: Context node ID
        :param done: Callback when command is complete
        :return: Token of request
        """
        return self.send_xicom_command("getContext", (node_id,), done)

    def setup_debug_cores(
        self, node_id: str, debug_hub_addrs: List[int] = None, done: DoneHWCommand = None
    ) -> Token:
        """
        Sets up debug core environment from a given list of DebugHub
        :param node_id: Parent Context node ID
        :param debug_hub_addrs: List of DebugHub addresses
        :param done: Callback when command is complete
        :returns: Token of command request
        """
        props = {}
        if debug_hub_addrs:
            props["debug_hub_addrs"] = debug_hub_addrs
        return self.send_xicom_command("setupDebugCores", (node_id, props), done)

    def remove_debug_cores(self, node_id: str, done: DoneHWCommand = None) -> Token:
        """
        Removes debug nodes under a given parent debug node
        :param node_id: Parent Context node ID
        :param done: Callback when command is complete
        :returns: Token of command request
        """
        return self.send_xicom_command("removeDebugCores", (node_id,), done)

    def remote_connect_xvc(
        self,
        remote_id: str,
        xvc_host: str,
        xvc_port: str,
        idcode: int = 0,
        done: DoneHWCommand = None,
    ) -> Token:
        """
        Send a request to a remote server to connect to an xvc server at xvc_host:xvc_port
        :param remote_id: Remote server id or ChipScope manager id
        :param xvc_host: Hostname or ip address of XVC server
        :param xvc_port: Port of XVC server
        :param idcode: Optional parameter to force the XVC server to show a specific idcode
        :param done: Callback when command is complete
        :return: Token of request
        """
        return self.send_xicom_command(
            "remoteConnectXvc", (remote_id, xvc_host, xvc_port, idcode), done
        )

    def remote_disconnect_xvc(
        self, xvc_node_id: str, optional_args: Dict[str, Any] = None, done: DoneHWCommand = None
    ) -> Token:
        """
        Send a request to the remote server through which the XVC node is connected

        :param xvc_node_id: Context id of XVC node
        :param optional_args: Optional additional arguments
        +-------------------+----------------------+------------------------------------------+
        | Name              | Type                 | Description                              |
        +===================+======================+==========================================+
        | stop              | |bool|               | Stop the XVC prior to disconnect         |
        +-------------------+----------------------+------------------------------------------+
        :param done: Callback when command is complete
        :return: Token of request
        """
        if optional_args:
            args = (xvc_node_id, optional_args)
        else:
            args = (xvc_node_id,)
        return self.send_xicom_command("remoteDisconnectXvc", args, done)

    def get_css_param(self, param_names: List[str], done: DoneHWCommand = None) -> Token:
        return self.send_xicom_command("getCssParam", (param_names,), done)

    def set_css_param(self, param_names: Dict[str, Any], done: DoneHWCommand = None) -> Token:
        return self.send_xicom_command("setCssParam", (param_names,), done)

    def add_listener(self, listener: ChipScopeListener):
        """Add DebugCore service event listener.
        :param listener: Event listener implementation.
        """
        channel_listener = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, channel_listener)
        self.listeners[listener] = channel_listener

    def remove_listener(self, listener: ChipScopeListener):
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
            "nodesAdded": self._nodes_added,
            "nodeChanged": self._node_changed,
            "nodesRemoved": self._nodes_removed,
        }

    def _nodes_added(self, args):
        args = from_xargs(args)
        assert len(args) == 1
        nodes_props = args[0]
        for node_id, props in nodes_props.items():
            self.listener.node_added(node_id, props)

    def _node_changed(self, args):
        args = from_xargs(args)
        assert len(args) == 1
        for node_id, props in args[0].items():
            self.listener.node_changed(node_id, props)

    def _nodes_removed(self, args):
        args = from_xargs(args)
        assert len(args) == 1
        for node_id in args[0]:
            self.listener.node_removed(node_id)

    def event(self, name, data):
        try:
            args = fromJSONSequence(data)
            try:
                handler = self._event_handlers[name]
                handler(args)
            except KeyError:
                raise IOError("ChipScope service: unknown event: " + name)
        except Exception as x:
            import sys

            x.tb = sys.exc_info()[2]
            self.service.channel.terminate(x)


ChipScopeService = ChipScopeProxy
