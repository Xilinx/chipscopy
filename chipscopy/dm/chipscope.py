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

import re
from chipscopy.tcf import protocol
from chipscopy.tcf.channel import ChannelListener
from chipscopy.proxies.ChipScopeProxy import ChipScopeService, ChipScopeListener as CSListener
from chipscopy.utils.logger import log
from . import CsManager, Node, add_manager, get_manager, _managers, remove_manager

MANAGER_TYPE = "chipscope"

csm_pattern = re.compile(r"(.+)\." + MANAGER_TYPE)


def get_managers():
    for name, csm in _managers.items():
        if csm_pattern.match(name):
            yield csm


def add_manager_from_channel(channel):
    serv = channel.getRemoteService(ChipScopeService)
    if not serv:
        raise Exception("Server does not have ChipScope Service")

    # set up memory view manager
    name = "{}.{}".format(channel.remote_peer.getID(), MANAGER_TYPE)
    for manager in get_managers():
        if manager.name == name:
            if manager.channel != channel:
                remove_manager(manager)
                break
            return manager

    cs_manager = ChipScopeManager(name, channel)
    add_manager(cs_manager)

    # add channel listener for disconnection event
    channel.addChannelListener(ManagerChannelListener(cs_manager))

    # trigger update
    cs_manager.update_nodes()
    return cs_manager


def get_manager_from_channel(channel):
    channel_name = channel.remote_peer.getID()
    return get_manager(f"{channel_name}.{MANAGER_TYPE}")


def get_manager_from_channel_id(channel_id):
    return get_manager(f"{channel_id}.{MANAGER_TYPE}")


class ChipScopeListener(CSListener):
    def __init__(self, manager):
        self.manager = manager

    def node_added(self, node_ctx, props):
        log.dm.debug(f"{self.manager.name}: Adding Node {node_ctx}")
        parent_ctx = props.get("parent_ctx")
        if not parent_ctx:
            parent_ctx = ""
        node = self.manager.add_node(node_ctx, parent_ctx)
        node._props.update(props)  # avoid update notification
        self.manager._node_added()  # send notifications immediately

    def node_changed(self, node_ctx, props):
        log.dm.debug(f"{self.manager.name}: Changing Node {node_ctx}: {props}")
        try:
            node = self.manager[node_ctx]
            node.update(props)
            self.manager._node_updated(node)  # send notifications immediately
        except KeyError:
            # The presumption is that the node_ctx can't be found within the manager
            # this is the case when the server has cached state but the client doesn't know about a node for which
            # a node changed event just fired. In this specific case, we will create the node now
            parent_ctx = props.get("parent_ctx")
            if not parent_ctx:
                parent_ctx = ""
            node = self.manager.add_node(node_ctx, parent_ctx)
            node.update(props)  # avoid update notification
            self.manager._node_added()  # send notifications immediately

    def node_removed(self, node_ctx):
        log.dm.debug(f"{self.manager.name}: Removing Node {node_ctx}")
        try:
            node = self.manager[node_ctx]
            # node.invalidate()
            self.manager.remove_node(node.ctx)
            self.manager._node_removed()
        except KeyError:
            pass


class ChipScopeManager(CsManager):
    def __init__(self, name: str = "", channel=None):
        super(ChipScopeManager, self).__init__(name, channel)
        self.dc = None
        if self.channel:
            self.dc = self.channel.getRemoteService(ChipScopeService)
        if self.dc:
            self.dc.add_listener(ChipScopeListener(self))

    def update_nodes(self):
        self._update_children(self)

    def _update_children(self, parent):
        cs_manager = self

        def done_get_children(token, error, results):
            if not error:
                children = results
                if isinstance(children, str):
                    children = [children]
                cs_manager.set_children(parent, children)

                for ctx in children:
                    node = cs_manager.add_node(ctx, parent.ctx)
                    cs_manager._update_static_info(node)
                    cs_manager._update_children(node)
            cs_manager.remove_pending(token)

        if self.dc:
            self.add_pending(self.dc.get_children(parent.ctx, done_get_children))

    def _update_static_info(self, node: Node):
        def done_get_context(token, error, props):
            if not error:
                node.update(props)
            node.remove_pending(token)

        if self.dc:
            node.add_pending(self.dc.get_context(node.ctx, done_get_context))


class ChannelOpenListener(protocol.ChannelOpenListener):
    def onChannelOpen(self, channel):
        add_manager_from_channel(channel)


class ManagerChannelListener(ChannelListener):
    def __init__(self, cs_manager: ChipScopeManager):
        self.cs_manager = cs_manager

    def onChannelClosed(self, error):
        if self.cs_manager:
            self.cs_manager.invalidate()
            self.cs_manager.channel.removeChannelListener(self)


initialized = False


def init():
    global initialized
    if not initialized:
        if not protocol.getEventQueue():
            protocol.startEventQueue()
        protocol.invokeAndWait(protocol.addChannelOpenListener, ChannelOpenListener())
        initialized = True
