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
.. |Node|      replace:: :class:`Node`
.. |CsManager| replace:: :class:`CsManager`

Node
^^^^^^^^^^^^^^^
.. autoclass:: Node
    :members:

CsManager
^^^^^^^^^^^^^^^
.. autoclass:: CsManager
    :members:

NodeListener
^^^^^^^^^^^^
.. autoclass:: NodeListener
    :members:

CsManagerListener
^^^^^^^^^^^^^^^^^
.. autoclass:: CsManagerListener
    :members:

"""

import re
from typing import Dict, Type, Any, List, Set, Tuple, NewType, Callable
from collections import deque
from chipscopy.tcf import protocol

NodePropsCallback = NewType("NodePropsCallback", Callable[["Node", Set[str]], None])

_manager_listeners = []

_managers = {}

_manager_match = re.compile(r"\[(.+)\]-(.+)")


def get_manager(name: str) -> "CsManager":
    """
    Gets manager from name (usually based on Channel ID)
    :param name: Name of manager
    :return: Manager object
    """
    return _managers.get(name)


def add_manager(manager: "CsManager"):
    """
    Adds CsManager to map of managers
    :param manager: Manager to add
    """
    _managers[manager.name] = manager


def remove_manager(manager: "CsManager"):
    """
    Removes CsManager from map of managers
    :param manager: Manager to remove
    """
    manager.invalidate()
    del _managers[manager.name]


def node_id_from_context(node: "Node"):
    """
    Creates a ChipScope Server unique ID from the manager's id and node context handle.
    :param node: Node from which to create unique ID
    """
    return "[{}]-{}".format(node.manager.name if node.manager else "ID", node.ctx)


def parse_node_id(node_id: str) -> Tuple[str, str]:
    """
    Parses a node_id and retrieves the manager's name and the node's context handle
    :param node_id: Node ID
    :return: Manager name and node context handle
    """
    # mn, _, ctx = node_id.partition("-")
    m = _manager_match.match(node_id)
    mn = ""
    ctx = ""
    if m:
        mn, ctx = m.group(1, 2)
    return mn, ctx


class Node(object):
    """
    A node is a generic hardware Context.  Node base class provides storage for Context properties provided by the
    hw_server and ChipScope services.  Node objects are intended to be 'upgraded' to Node subclasses to add
    functionality for a particular Context type.

    .. attribute:: node.key

        Returns attribute normal if exists.  Else returns property if exists, or None if not.  Can not be used for
        setting properties.

    .. method:: node[key]

        Return property of node from key.  Raises |KeyError| if property does not exist.

    .. method:: node[key] = value

        Sets value of property for given key.  It also auto updates listeners.
    """

    def __init__(self, ctx: str = "", parent_ctx: str = "", manager: "CsManager" = None):
        self.ctx = ctx
        self.parent_ctx = parent_ctx
        self.manager = manager
        self.children = []
        self._props = {}
        self._updated_props = set()
        self.dirty = False
        self.pending = set()
        self.invalid = False
        self.listeners: NodePropsCallback = list()

    def post_init(self):
        """
        Used to handle initialization where __init__ was called without any parameters were set
        """
        pass

    def de_init(self):
        """
        Used to clean up when this class is being switched away from
        :return:
        """
        pass

    @property
    def props(self) -> Dict[str, Any]:
        """
        Accessor for full list of properties
        :return: Properties
        """
        return self._props

    @property
    def size(self) -> int:
        """
        :return: The number of properties
        """
        return len(self._props)

    @property
    def is_valid(self) -> bool:
        """
        A Node is valid while still existing in the hw_server.  Once the node is removed in the hw_server the
        node here is invalidated rather than removed.  The node is removed once a replacement is found in the hw_server.
        """
        return not self.invalid

    @staticmethod
    def is_compatible(node: "Node") -> bool:
        """
        Overridden by subclasses to test if this node can be converted to subclass instance.  Usually tests available
        properties of the node and/or position in the tree.
        :param node: node instance to test
        :return: True if compatible
        """
        return True

    @property
    def queue_group(self) -> Any:
        """
        Queue groups are used to control the flow of requests on one or more nodes.  Requests on the same queue
        group are handled synchronously to maintain consistent state.  By default the node is in its own queue group to
        maximize the number of asynchronous operations permitted across all nodes.

        :return: Context handle of parent of the queue group
        """
        return self.ctx

    def update(self, props: Dict[str, Any]):
        """
        Updates properties of node and notifies any listeners of the node's changed properties.

        :param props: Properties to update.
        """
        self._props.update(props)
        keys = set(props.keys())
        if self.manager and keys not in self._updated_props:
            self._updated_props.update(keys)
            self._props_updated()

    def __getattr__(self, attr):
        # NOTE uncomment these lines if having trouble debugging __init__() in child class
        if "_props" not in self.__dict__:
            return None
        if attr in self._props:
            return self._props.get(attr)

    def __getitem__(self, item):
        return self._props[item]

    def __setitem__(self, key, value):
        self._props[key] = value
        if self.manager and key not in self._updated_props:
            self._updated_props.add(key)
            self._props_updated()

    def __str__(self):
        return "{}({}, {} props)".format(self.__class__.__name__, self.ctx, len(self._props))

    @property
    def is_ready(self):
        """
        Checks to see if this node is currently available for operation.  Generally will not be ready if there are
        active operations being run on this node (e.g. out standing TCF command to the hw_server)
        :return: True if ready and available
        """
        return not self.pending

    def add_pending(self, token):
        self.pending.add(token)
        return token

    def remove_pending(self, token):
        try:
            self.pending.remove(token)
        except KeyError:
            pass

    def invalidate(self, notify=True):
        if not self.invalid:
            self.invalid = True
            if self.manager:
                for child in self.manager.get_children(self):
                    child.invalidate()
                if notify:
                    self.manager.notify_node_removed(self)
            self.listeners = set()

    def _props_updated(self):
        if not self.dirty:
            self.dirty = True
            if self.manager:
                self.manager.notify_node_changed(self)

    def clear_update(self):
        # clears parameters used to notify on updates
        self.dirty = False
        self._updated_props.clear()

    def add_listener(self, listener: NodePropsCallback):
        self.listeners.append(listener)

    def remove_listener(self, listener: NodePropsCallback):
        self.listeners.remove(listener)

    def call_listeners(self):
        for listener in self.listeners:
            listener(self, self._updated_props)


class NodeAutoUpgrader(object):
    """ Used by a Manager of a view to auto upgrade a node to specific classes """

    def __call__(self, node: Node, **kwargs):
        """ Called by view manager """
        return node


class CsManager(Node):
    """
    Manages Context |Node| objects in a directly accessible dict by their ctx handles and provides means to navigate by
    a node's parent or children.

    .. method:: manager[ctx]

        Return node from given ctx.  Raises |KeyError| if node does not exist.
    """

    node_auto_upgrader: NodeAutoUpgrader = None

    def __init__(self, name: str = "", channel=None):
        super(CsManager, self).__init__(ctx="", manager=self)
        self.channel = channel
        self._nodes = {"": self}  # the manager is always the default "" parent
        self._node_listeners = []
        self._added_nodes = deque()
        self._removed_nodes = deque()
        self.name = name
        self.default_node_cls = Node
        for listener in _manager_listeners:
            listener.manager_added(self)

    def add_node(self, ctx: str, parent_ctx: str = "") -> Node:
        """
        Creates and Adds new node to manager from given ctx and parent's ctx.

        :param ctx: Context handle of new node
        :param parent_ctx: Context handle of parent
        :return: node added
        """
        props = None
        node = self._nodes.get(ctx)
        if node and node.parent_ctx != parent_ctx:
            props = node.props
            node.invalidate()
            node = None

        if node:
            if node.invalid:
                node.invalid = False
                self.notify_node_added(node)
            return node

        # create and add to manager
        node = self.default_node_cls(ctx, parent_ctx, self)
        if props:
            node.props.update(props)
        self._nodes[ctx] = node

        # add to parent's children if not already
        parent = self._nodes.get(parent_ctx)
        if parent:
            if ctx not in parent.children:
                parent.children.append(ctx)

        node.post_init()

        # notify node added
        self.notify_node_added(node)

        return node

    def remove_node(self, ctx: str):
        """
        Removes node and its children from manager at given ctx and removes the node from its parent.

        :param ctx: Context handle of node
        """
        try:
            node = self._nodes.pop(ctx)
        except KeyError:
            return

        node.invalid = True

        # remove from parent
        parent = self._nodes.get(node.parent_ctx)
        if parent:
            try:
                parent.children.remove(ctx)
            except ValueError:  # pragma: no cover
                pass

        self.notify_node_removed(node)

        # remove all children
        for child in node.children:
            self.remove_node(child)

    def remove_all(self):
        """
        Removes all nodes from manager
        """
        while self.children:
            self.remove_node(self.children[0])

    def upgrade_node(self, node: Node, upgrade_cls: type, **kwargs) -> Node:
        """
        Converts node to a Node subclass and maintains node properties and position in manager.

        :param node: Node to convert
        :param upgrade_cls: Node subclass
        :return: new node instance
        """
        node.de_init()
        new = upgrade_cls(**kwargs)
        new.__dict__.update(node.__dict__)
        self._nodes[new.ctx] = new
        new.post_init()
        node.invalid = True
        return new

    def get_children(self, parent: str or Node = "") -> Node:
        """
        Iterates through list of children of given parent

        :param parent: Context handle or node object of parent
        :yield: child node
        """
        if parent is None:
            parent = self
        if isinstance(parent, str):
            parent = self[parent]
        if not parent.children:
            return None

        for child in parent.children:
            yield self._nodes.get(child)

    def get_all(self) -> Node:
        """
        Iterates through all nodes in manager.

        :yield: node object
        """
        for node in self._nodes.values():
            yield node

    def get_node(self, ctx: str, cls: Type[Node] = Node) -> Node or None:
        """
        Gets the node instance of a given class if compatible.  If the node is not currently of the class it's
        'upgraded' in the CsManager to be an instance of that class.  The property values are maintained.

        :param ctx: Context handle of node
        :param cls: Desired class of node
        :return: node of class if compatible; None if not
        """
        node = self._nodes.get(ctx)

        if not node:
            return None

        if isinstance(node, cls):
            return node

        if cls.is_compatible(node):
            return self.upgrade_node(node, cls)

        return None

    def set_children(self, parent: Node or str, children: List[str]):
        """
        Sets the children list of a parent node.  If existing child is not on the new list of children it is removed.

        :param parent: Parent context node
        :param children: List of context handles of new children
        """
        if isinstance(parent, str):
            parent = self[parent]

        remove_children = [child for child in parent.children if child not in children]
        for child in remove_children:
            self.remove_node(child)

        parent.children = children

    def notify_node_changed(self, node: Node):
        if self._node_listeners:
            protocol.invokeLater(self._node_updated, node.ctx)
        else:
            node.clear_update()

    def _node_updated(self, node_ctx: str):
        node = self._nodes.get(node_ctx)
        if node:
            if node._updated_props:
                for listener in self._node_listeners:
                    node.call_listeners()
                    listener.node_changed(node, node._updated_props)
            node.clear_update()

    def notify_node_added(self, node: Node):
        if self._node_listeners:
            if node.ctx not in self._added_nodes:
                should_post = len(self._added_nodes) == 0
                self._added_nodes.append(node.ctx)
                if should_post:
                    protocol.invokeLater(self._node_added)
        else:
            node.clear_update()

    def _node_added(self):
        nodes = []
        if self._added_nodes:
            for ctx in self._added_nodes:
                node = self._nodes.get(ctx)
                if node:
                    nodes.append(node)
                    node.clear_update()
        if nodes:
            for listener in self._node_listeners:
                listener.nodes_added(nodes)
        self._added_nodes.clear()

    def notify_node_removed(self, node: Node):
        if self._node_listeners:
            if node not in self._removed_nodes:
                should_post = len(self._removed_nodes) == 0
                self._removed_nodes.append(node)
                if should_post:
                    protocol.invokeLater(self._node_removed)

    def _node_removed(self):
        if self._removed_nodes:
            for listener in self._node_listeners:
                listener.nodes_removed(self._removed_nodes)
        self._removed_nodes.clear()

    @property
    def size(self) -> int:
        """
        :return: The number of nodes.
        """
        return len(self._nodes)

    def __getitem__(self, item) -> Node:
        return self._nodes[item]

    def __str__(self):
        return "{}({}, {} nodes)".format(self.__class__.__name__, self.name, len(self._nodes))

    @property
    def queue_group(self):
        return self

    def invalidate(self):
        self.invalid = True
        for listener in _manager_listeners:
            listener.manager_removed(self)

        for child in self.get_children():
            child.invalidate()

    def add_node_listener(self, listener: "NodeListener"):
        """
        Adds |Node| event listener to manager.
        :param listener: Node listener to add
        """
        if listener not in self._node_listeners:
            self._node_listeners.append(listener)

    def remove_node_listener(self, listener: "NodeListener"):
        """
        Removes |Node| event listener from manager.
        :param listener: Node listener to remove
        """
        self._node_listeners.remove(listener)


class NodeListener(object):
    """
    |Node| event listener catching when nodes are created, removed, or changed
    """

    def nodes_added(self, nodes: List[Node]):
        """
        Called when a node was added to the manager.

        :param nodes: List of context nodes added
        """
        pass

    def node_changed(self, node: Node, updated_keys: Set[str]):
        """
        Called when a property was changed in a node.
        :param node: Context node changed
        :param updated_keys: List of property keys that have changed
        """
        pass

    def nodes_removed(self, nodes: List[Node]):
        """
        Called when a node is invalidated.
        :param nodes: List of context nodes removed
        """
        pass


class CsManagerListener(object):
    """
    |CsManager| event listener catching when CsManagers are created or removed
    """

    def manager_added(self, cs_manager: CsManager):
        """
        Called when CsManager added.

        :param cs_manager: A manager that has been created
        """
        pass

    def manager_removed(self, cs_manager: CsManager):
        """
        Called when CsManager removed.

        :param cs_manager: A manager that has been removed
        """
        pass

    @staticmethod
    def add_listner(listener: "CsManagerListener"):
        """
        Adds CsManagerListener to list
        :param listener: Listener to add
        """
        if listener not in _manager_listeners:
            _manager_listeners.append(listener)

    @staticmethod
    def remove_listener(listener: "CsManagerListener"):
        """
        Removes CsManagerListener from list of listeners
        :param listener: Listener to remove
        """
        _manager_listeners.remove(listener)
