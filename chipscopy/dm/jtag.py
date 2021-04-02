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
from chipscopy.proxies.JtagProxy import JtagProxy as JtagService
from chipscopy.utils.logger import log
from . import CsManager, Node, _managers, add_manager, remove_manager

MANAGER_TYPE = "jtag"

csm_pattern = re.compile(r".+\." + MANAGER_TYPE)


def get_managers():
    for name, csm in _managers.items():
        if csm_pattern.match(name):
            yield csm


def add_manager_from_channel(channel):
    jtag = channel.getRemoteService(JtagService)
    if not jtag:
        raise Exception("Server does not have Jtag Service")

    # set up memory view manager
    name = "{}.{}".format(channel.remote_peer.getID(), MANAGER_TYPE)
    for manager in get_managers():
        if manager.name == name:
            if manager.channel != channel:
                remove_manager(manager)
                break
            return manager

    cs_manager = JtagManager(name, channel)
    add_manager(cs_manager)

    # add channel listener for disconnection event
    channel.addChannelListener(ManagerChannelListener(cs_manager))

    # trigger update
    cs_manager.update_nodes()
    return cs_manager


class JtagListener(object):
    def __init__(self, manager):
        self.manager = manager

    def contextAdded(self, contexts):
        log.jtag2.debug(f"Jtag Event contextAdded {[c.ID for c in contexts]}")
        for context in contexts:
            parent_ctx = context.ParentID
            if parent_ctx is None:
                parent_ctx = ""
            node = self.manager.add_node(context.ID, parent_ctx)
            node.jtag = context
            node.update(context.props)
            if self.manager.node_auto_upgrader:
                self.manager.node_auto_upgrader(node)

    def contextChanged(self, contexts):
        log.jtag2.debug(f"Jtag Event contextChanged {[c.ID for c in contexts]}")
        for context in contexts:
            parent_ctx = context.ParentID
            if parent_ctx is None:
                parent_ctx = ""
            node = self.manager.add_node(context.ID, parent_ctx)
            node.jtag = context
            node.update(context.props)

    def contextRemoved(self, context_ids):
        log.jtag2.debug(f"Jtag Event contextRemoved {context_ids}")
        for context_id in context_ids:
            try:
                node = self.manager[context_id]
                node.invalidate()
            except KeyError:
                pass


class JtagManager(CsManager):
    def __init__(self, name: str = "", channel=None):
        super(JtagManager, self).__init__(name, channel)
        jtag = self.channel.getRemoteService(JtagService)
        jtag.add_listener(JtagListener(self))

    def update_nodes(self):
        self._update_children(self)

    def _update_children(self, parent):
        jtag = self.channel.getRemoteService(JtagService)
        cs_manager = self

        def done_get_children(token, error, context_ids):
            if not error:
                cs_manager.set_children(parent, context_ids)

                for context in context_ids:
                    node = cs_manager.add_node(context, parent.ctx)
                    cs_manager._update_static_info(node)
                    cs_manager._update_children(node)
            cs_manager.remove_pending(token)

        if jtag:
            self.add_pending(jtag.get_children(parent.ctx, done_get_children))

    def _update_static_info(self, node: Node):
        jtag = self.channel.getRemoteService(JtagService)

        def done_get_context(token, error, context):
            if not error:
                props = context.props
                node.update(props)
                if self.node_auto_upgrader:
                    self.node_auto_upgrader(node)
            node.remove_pending(token)

        if jtag:
            node.add_pending(jtag.get_context(node.ctx, done_get_context))


class ChannelOpenListener(protocol.ChannelOpenListener):
    def onChannelOpen(self, channel):
        add_manager_from_channel(channel)


class ManagerChannelListener(ChannelListener):
    def __init__(self, cs_manager: JtagManager):
        self.cs_manager = cs_manager

    def onChannelClosed(self, error):
        if self.cs_manager:
            self.cs_manager.invalidate()
        self.cs_manager.channel.removeChannelListener(self)
