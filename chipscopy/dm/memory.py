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
from chipscopy.tcf.services import memory as mem_service
from chipscopy.tcf.services import runcontrol as rc_service
from . import CsManager, Node, _managers, add_manager, remove_manager

MANAGER_TYPE = "memory"

csm_pattern = re.compile(r".+\." + MANAGER_TYPE)


def get_managers():
    for name, csm in _managers.items():
        if csm_pattern.match(name):
            yield csm


def add_manager_from_channel(channel):
    mem = channel.getRemoteService(mem_service.MemoryService)
    if not mem:
        raise Exception("Server does not have Memory Service")

    # set up memory view manager
    name = "{}.{}".format(channel.remote_peer.getID(), MANAGER_TYPE)
    for manager in get_managers():
        if manager.name == name:
            if manager.channel != channel:
                remove_manager(manager)
                break
            return manager

    cs_manager = MemoryManager(name, channel)
    add_manager(cs_manager)

    # add channel listener for disconnection event
    channel.addChannelListener(ManagerChannelListener(cs_manager))

    # trigger update
    cs_manager.update_nodes()
    return cs_manager


class MemoryListener(mem_service.MemoryListener):
    def __init__(self, manager):
        self.manager = manager

    def contextAdded(self, contexts):
        # print(f"Memory Event contextAdded {context_ids}")
        for context in contexts:
            parent_ctx = context.getParentID()
            if parent_ctx is None:
                parent_ctx = ""
            node = self.manager.add_node(context.getID(), parent_ctx)
            node.mem = context
            node.update(context.getProperties())

    def contextChanged(self, contexts):
        # print(f"Memory Event contextChanged {context_ids}")
        for context in contexts:
            parent_ctx = context.getParentID()
            if parent_ctx is None:
                parent_ctx = ""
            node = self.manager.add_node(context.getID(), parent_ctx)
            node.mem = context
            node.update(context.getProperties())

    def contextRemoved(self, context_ids):
        # print(f"Memory Event contextRemoved {context_ids}")
        for context_id in context_ids:
            try:
                node = self.manager[context_id]
                node.invalidate()
            except KeyError:
                pass

    def memoryChanged(self, context_id, addr, size):
        # print(f"Event memoryChanged {context_id}, addr {addr}, size {size}")
        try:
            node = self.manager[context_id]
            node["mem_changed_count"] = node.mem_changed_count + 1 if node.mem_changed_count else 1
        except KeyError:
            pass


class RunControlListener(rc_service.RunControlListener):
    def __init__(self, manager):
        self.manager = manager

    def contextAdded(self, contexts):
        # print(f"Memory Event contextAdded {context_ids}")
        for context in contexts:
            parent_ctx = context.getParentID()
            if parent_ctx is None:
                parent_ctx = ""
            node = self.manager.add_node(context.getID(), parent_ctx)
            node.update(context.getProperties())

    def contextChanged(self, contexts):
        # print(f"Memory Event contextChanged {context_ids}")
        for context in contexts:
            parent_ctx = context.getParentID()
            if parent_ctx is None:
                parent_ctx = ""
            node = self.manager.add_node(context.getID(), parent_ctx)
            node.update(context.getProperties())

    def contextRemoved(self, context_ids):
        # print(f"Memory Event contextRemoved {context_ids}")
        for context_id in context_ids:
            try:
                node = self.manager[context_id]
                node.invalidate()
            except KeyError:
                pass


class MemoryManager(CsManager):
    def __init__(self, name: str = "", channel=None):
        super(MemoryManager, self).__init__(name, channel)
        mem = self.channel.getRemoteService(mem_service.MemoryService)
        rc = self.channel.getRemoteService(rc_service.RunControlService)
        mem.addListener(MemoryListener(self))
        rc.addListener(RunControlListener(self))

    def update_nodes(self):
        self._update_children(self)

    def _update_children(self, parent):
        mem = self.channel.getRemoteService(mem_service.MemoryService)
        rc = self.channel.getRemoteService(rc_service.RunControlService)
        cs_manager = self

        def done_get_children(token, error, context_ids):
            if not error:
                cs_manager.set_children(parent, context_ids)

                for context in context_ids:
                    if context not in cs_manager._nodes:
                        node = cs_manager.add_node(context, parent.ctx)
                        cs_manager._update_static_info(node)
                        cs_manager._update_children(node)
            cs_manager.remove_pending(token)

        if mem:
            self.add_pending(mem.getChildren(parent.ctx, done_get_children))
        if rc:
            self.add_pending(rc.getChildren(parent.ctx, done_get_children))

    def _update_static_info(self, node: Node):
        mem = self.channel.getRemoteService(mem_service.MemoryService)
        rc = self.channel.getRemoteService(rc_service.RunControlService)

        def done_get_context(token, error, context):
            if not error:
                props = context.getProperties()
                node.mem = context
                node.update(props)
                if self.node_auto_upgrader:
                    self.node_auto_upgrader(node)
            node.remove_pending(token)

        def done_get_rc_context(token, error, context):
            if not error:
                props = context.getProperties()
                node.update(props)
                if self.node_auto_upgrader:
                    self.node_auto_upgrader(node)
            node.remove_pending(token)

        if rc:
            node.add_pending(rc.getContext(node.ctx, done_get_rc_context))
        if mem:
            node.add_pending(mem.getContext(node.ctx, done_get_context))


class ChannelOpenListener(protocol.ChannelOpenListener):
    def onChannelOpen(self, channel):
        add_manager_from_channel(channel)


class ManagerChannelListener(ChannelListener):
    def __init__(self, cs_manager: MemoryManager):
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
