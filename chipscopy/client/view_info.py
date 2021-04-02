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

import copy
from collections import deque
from itertools import islice
from typing import List, Set, Type, Callable, ClassVar
from chipscopy import dm
from chipscopy.dm import request
from chipscopy.tcf import protocol
from chipscopy.utils.logger import log


class TargetFilter(object):
    def __init__(
        self,
        view_info: "ViewInfo",
        parent: dm.Node or str = None,
        node_cls: ClassVar[dm.Node] = dm.Node,
        **params,
    ):
        self.view_info = view_info
        self._filter_params = params
        self.node_cls = node_cls
        self.parent = parent
        it = view_info.get_children(parent) if parent is not None else view_info.get_all()
        self._filtered_targets = filter(self._filter_props, it)

    def __iter__(self):
        return self

    def __next__(self):
        return self.view_info.get_sync_node(next(self._filtered_targets).ctx, self.node_cls)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.get(index=item)
        elif isinstance(item, str):
            return self.get(ctx=item)
        raise ValueError

    def _filter_props(self, node):
        return (
            node.ctx
            and self.node_cls.is_compatible(node)
            and self._filter_params.items() <= node._props.items()
        )

    def filter(self, parent: dm.Node or str = None, node_cls: ClassVar[dm.Node] = None, **params):
        if parent is None:
            parent = self.parent
        if not node_cls:
            node_cls = self.node_cls
        return TargetFilter(self.view_info, parent, node_cls, **params)

    def get(
        self,
        ctx: str = "",
        parent: dm.Node or str = None,
        node_cls: ClassVar[dm.Node] = None,
        index: int = None,
        **params,
    ):
        if ctx:
            return self.view_info.get_node(ctx)
        if parent is None:
            parent = self.parent
        if not node_cls:
            node_cls = self.node_cls
        if not params:
            params = self._filter_params
        tf = TargetFilter(self.view_info, parent, node_cls, **params)
        if index is not None:
            return next(islice(tf, index, None))
        try:
            node = next(tf)
        except StopIteration:
            # raise StopIteration(f"No nodes for filter {tf}")
            return None
        try:
            _ = next(tf)
            raise Exception(f"More than one result for filter {tf}")
        except StopIteration:
            pass
        return node

    def first(self):
        return self.get(index=0)


class SyncNode(dm.Node):
    def __init__(self, node_id: str = "", parent_ctx: str = "", manager: "ViewInfo" = None):
        super(SyncNode, self).__init__(node_id, parent_ctx, manager)
        self._changed_props = set()
        self._has_changed = False

    def __getattr__(self, attr):
        self.update_changed_props()
        value = super(SyncNode, self).__getattr__(attr)
        if not value and hasattr(self.node_cls, attr):
            return getattr(
                request.CsRequestSync(self.manager.cs_manager, self.ctx, self.node_cls), attr
            )
        return value

    def __getitem__(self, item):
        self.update_changed_props()
        return super(SyncNode, self).__getitem__(item)

    def __setitem__(self, key, value):
        self._props[key] = value

    def __str__(self):
        self.update_changed_props()
        cls = self.node_cls if type(self) == SyncNode else type(self)
        return "{}({}, {} properties)".format(cls.__name__, self.ctx, len(self._props))

    def future(self, *args, **kwargs) -> request.CsFutureRequest:
        return request.CsFutureRequestSync(
            self.manager.cs_manager, self.ctx, self.node_cls, *args, **kwargs
        )

    @property
    def props(self):
        self.update_changed_props()
        return self._props

    def add_changed_props(self, _changed_props):
        self._changed_props.update(_changed_props)
        self._has_changed = True

    def update_changed_props(self):
        sync_node = self
        self.manager.run_events()

        class PropsRequest(request.CsRequestSync):
            def run(self):
                for prop_name in sync_node._changed_props:
                    sync_node[prop_name] = copy.copy(self.node[prop_name])
                sync_node._changed_props.clear()
                sync_node._has_changed = False
                return True

        if self._has_changed:
            req = PropsRequest(self.manager.cs_manager, self.ctx)
            req()


class ViewInfo(dm.CsManager):
    def __init__(self, cs_manager: dm.CsManager):
        super(ViewInfo, self).__init__(cs_manager.name + ".observer", cs_manager.channel)
        self.cs_manager = cs_manager
        self.default_node_cls = SyncNode
        self.next_target_id = 0
        self.ctx_target_map = {}
        self.target_ctx_map = {}
        self.event_queue = deque()
        self.running_events = False
        mi = self

        class NodeListener(dm.NodeListener):
            def nodes_added(self, nodes: List[dm.Node]):
                if log.is_domain_enabled("view_info", "INFO"):
                    names = [node.ctx for node in nodes]
                    log.view_info.info(f"{mi.name}: Adding nodes {names}")
                for node in nodes:
                    props = copy.copy(node._props)
                    mi.queue_event(
                        mi.add_sync_node, node.ctx, node.parent_ctx, node.__class__, props
                    )
                mi.queue_event(mi._node_added)

            def nodes_removed(self, nodes: List[dm.Node]):
                if log.is_domain_enabled("view_info", "INFO"):
                    names = [node.ctx for node in nodes]
                    log.view_info.info(f"{mi.name}: Removing nodes {names}")
                for node in nodes:
                    mi.queue_event(mi.remove_node, node.ctx)
                mi.queue_event(mi._node_removed)  # notify view node listeners

            def node_changed(self, node: dm.Node, updated_keys: Set[str]):
                log.view_info.info(f"{mi.name}: Changing node {node.ctx}: {updated_keys}")
                mi.queue_event(mi.node_changed, node.ctx, copy.copy(updated_keys))

        cs_manager.add_node_listener(NodeListener())

        class ManagerListener(dm.CsManagerListener):
            def manager_added(self, cs_manager):
                if cs_manager == mi.cs_manager:
                    mi.invalid = False

            def manager_removed(self, cs_manager):
                if cs_manager == mi.cs_manager:
                    mi.invalidate()

        ManagerListener.add_listner(ManagerListener())

        class GetNodesRequest(request.CsRequestSync):
            def add_children(self, parent=None):
                # start by creating the parent<->child links in the non-tcf thread view class
                # if there isn't a parent (top level nodes) then we use the manager instance
                # before chipscopy #28 was fixed the TCF thread manager was correctly linking children
                # but the view running on the main thread class was not getting the correct linking
                # but only when the server was caching state before the chipscopy connected
                # https://gitenterprise.xilinx.com/chipscope/chipscopy/issues/28
                if not parent:
                    parent = self.cs_manager
                elif isinstance(parent, str):
                    parent = self.cs_manager[parent]
                mi.queue_event(mi.set_children, parent.ctx, parent.children)
                for child in self.cs_manager.get_children(parent):
                    props = copy.copy(child.props)
                    mi.queue_event(
                        mi.add_sync_node, child.ctx, child.parent_ctx, child.__class__, props
                    )
                    self.add_children(child)

            def run(self):
                self.add_children()
                return True

        req = GetNodesRequest(cs_manager)
        req()
        self.run_events()

    def queue_event(self, event, *args, **kwargs):
        log.view_info.debug(f"{self.name}: queue_event {event}")
        self.event_queue.appendleft((event, args, kwargs))

    def run_events(self):
        if self.running_events:
            return
        try:
            self.running_events = True
            while True:
                event, args, kwargs = self.event_queue.pop()
                log.view_info.debug(f"{self.name}: run_event {event}")
                event(*args, **kwargs)
        except IndexError:
            pass
        finally:
            self.running_events = False

    def node_changed(self, ctx, updated_keys):
        try:
            sync_node = self[ctx]
            sync_node.add_changed_props(updated_keys)
            self._node_changed(sync_node)
        except KeyError:
            pass

    def _node_changed(self, node: SyncNode):
        if node._changed_props:
            for listener in self._node_listeners:
                listener.node_changed(node, node._changed_props)

    def get_sync_node(self, ctx: str, sync_node_cls: ClassVar[SyncNode]):
        return super().get_node(ctx, sync_node_cls)

    def add_sync_node(self, ctx, parent_ctx, cls, props) -> dm.Node:
        sync_node = self.add_node(ctx, parent_ctx)
        if not isinstance(sync_node, SyncNode):
            sync_node = self.upgrade_node(sync_node, SyncNode)
        sync_node["node_cls"] = cls
        sync_node._props.update(props)

        if sync_node.ctx not in self.ctx_target_map.keys():
            self.ctx_target_map[sync_node.ctx] = self.next_target_id
            self.target_ctx_map[self.next_target_id] = sync_node.ctx
            self.next_target_id += 1

        sync_node["target_id"] = self.ctx_target_map[sync_node.ctx]
        return sync_node

    def notify_node_added(self, node: SyncNode):
        if self._node_listeners:
            if node.ctx not in self._added_nodes:
                self._added_nodes.append(node.ctx)
        else:
            node.clear_update()

    def notify_node_removed(self, node):
        if self._node_listeners:
            if node not in self._removed_nodes:
                self._removed_nodes.append(node)

    def notify_node_changed(self, node):
        if not self._node_listeners:
            node.clear_update()

    def get_node(
        self, ctx: str, cls: Type[dm.Node] = dm.Node, done: request.DoneCallback = None
    ) -> dm.Node or None:
        self.run_events()
        node = self._nodes.get(ctx)

        if not node:
            if done:
                protocol.invokeLater(done, None, None, None)
            return None

        if not done and issubclass(node.node_cls, cls):
            return node

        if done:
            req = request.CsRequest(self.cs_manager, ctx, cls, done)
        else:
            req = request.CsRequestSync(self.cs_manager, ctx, cls)

        def _get_node(done):
            node_cls = dm.Node
            if req.node:
                node_cls = req.node.__class__
            req.node["node_cls"] = node_cls
            protocol.invokeLater(done, node, None, req.node)
            return node

        req.run_func = _get_node
        req()

        return node

    def get_children(self, parent: str or dm.Node = ""):
        self.run_events()
        return super(ViewInfo, self).get_children(parent)

    def get_all(self):
        self.run_events()
        return super(ViewInfo, self).get_all()

    def __getitem__(self, item):
        self.run_events()
        return super(ViewInfo, self).__getitem__(item)

    @property
    def size(self):
        self.run_events()
        return super(ViewInfo, self).size

    def find_nodes(self, parent: str or dm.Node = "", cls: Type[dm.Node] = dm.Node):
        """
        Finds a node given a parent node.  If no parent node then searches the root.
        :param parent: Parent node or handle of parent
        :param cls: Desired class
        :return: Nodes of desired class if found.  Empty list otherwise.
        """
        # nodes = [self.get_node(node.ctx, cls) for node in self.get_children(parent) if cls.is_compatible(node)]
        # return nodes
        for node in self.get_children(parent):
            if cls.is_compatible(node):
                yield self.get_node(node.ctx, cls)

    def print_tree(self, print_props: bool = False, printer: Callable[[str], None] = print):
        """
        Prints node tree
        :param print_props: Flag to include properties for each node
        :param printer: Optional argument to change where to print.  (E.g. log.<logger name>.debug)
        """
        self.run_events()

        def print_targets(parent=None, level=1):
            for child in self.get_children(parent):
                name = child.Name if child.Name else child.ctx
                if print_props:
                    printer("{}{} {} ({})".format("\t" * level, child.target_id, name, child.props))
                else:
                    printer("{}{} {}".format("\t" * level, child.target_id, name))
                print_targets(child, level + 1)

        print_targets()
