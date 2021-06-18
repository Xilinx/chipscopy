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
from chipscopy.proxies import DebugCoreProxy as dc_service
from chipscopy.utils.logger import log
from . import CsManager, Node, add_manager, get_manager, _managers, remove_manager
from .poll import DebugCorePollScheduler

MANAGER_TYPE = "debugcore"

csm_pattern = re.compile(r".+\." + MANAGER_TYPE)


def get_managers():
    return [csm for name, csm in _managers.items() if csm_pattern.match(name)]


def add_manager_from_channel(channel):
    serv = channel.getRemoteService(dc_service.DebugCoreService)
    if not serv:
        raise Exception("Server does not have DebugCore Service")

    # set up memory view manager
    name = "{}.{}".format(channel.remote_peer.getID(), MANAGER_TYPE)
    for manager in get_managers():
        if manager.name == name:
            if manager.channel != channel:
                remove_manager(manager)
                break
            return manager

    cs_manager = DebugCoreManager(name, channel)
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


def id_domain_enable(param, param1):
    pass


class DebugNodeListener(dc_service.DebugNodeListener):
    def __init__(self, manager):
        self.manager = manager

    def node_added(self, node_ctx, props):
        if log.is_domain_enabled("dm", "DEBUG"):
            log.dm.debug(f"{self.manager.name}: Adding Node {node_ctx}: {props}")
        parent_ctx = props.get("ParentID")
        if not parent_ctx:
            parent_ctx = ""
        node = self.manager.add_node(node_ctx, parent_ctx)
        node.update(props)
        additional_props = props.get("additional_props")
        if additional_props and type(additional_props) == dict:
            node.update(additional_props)

    def node_changed(self, node_ctx, props):
        if id_domain_enable("dm", "DEBUG"):
            log.dm.debug(f"{self.manager.name}: Changing Node {node_ctx}: {props}")
        parent_ctx = props.get("ParentID")
        if not parent_ctx:
            parent_ctx = ""
        node = self.manager.add_node(node_ctx, parent_ctx)
        node.update(props)
        additional_props = props.get("additional_props")
        if additional_props and type(additional_props) == dict:
            node.update(additional_props)

    def node_removed(self, node_ctx):
        log.dm.debug(f"{self.manager.name}: Removing Node {node_ctx}")
        try:
            node = self.manager[node_ctx]
            # node.invalidate()
            self.manager.remove_node(node.ctx)
        except KeyError:
            pass


class DebugCoreManager(CsManager):
    def __init__(self, name: str = "", channel=None):
        super(DebugCoreManager, self).__init__(name, channel)
        self.dc = None
        self.poll_scheduler = None
        if self.channel:
            self.dc = self.channel.getRemoteService(dc_service.DebugCoreService)
            self.poll_scheduler = DebugCorePollScheduler(self.channel)
        if self.dc:
            self.dc.add_listener(DebugNodeListener(self))

    def update_nodes(self):
        self._update_children(self)
        self._update_polls()

    def _update_polls(self):
        def done_poll_update(token, error, results):
            self.remove_pending(token)

        if self.poll_scheduler:
            self.add_pending(self.poll_scheduler.update_polls(done=done_poll_update))

    def _update_children(self, parent):
        cs_manager = self

        def done_get_children(token, error, results):
            if not error and results:
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
        if channel.getRemoteService(dc_service.DebugCoreService):
            add_manager_from_channel(channel)


class ManagerChannelListener(ChannelListener):
    def __init__(self, cs_manager: DebugCoreManager):
        self.cs_manager = cs_manager

    def onChannelClosed(self, error):
        if self.cs_manager:
            self.cs_manager.invalidate()
            self.cs_manager.channel.removeChannelListener(self)


initialized = False


def init():
    global initialized
    if not initialized:
        protocol.invokeAndWait(protocol.addChannelOpenListener, ChannelOpenListener())
        initialized = True
