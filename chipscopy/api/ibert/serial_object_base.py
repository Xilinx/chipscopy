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

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Set, Tuple, Type, TypeVar, Union

from rich.tree import Tree

from chipscopy.api._detail.property import PropertyCommands, Watchlist, WatchlistEventHandler
from chipscopy.api.containers import QueryList
from chipscopy.client.ibert_core_client import IBERTCoreClient
from typing_extensions import Final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert import IBERT


class IBERTWatchlist(Watchlist["IBERTPropertyCommands"]):
    def __init__(self, parent):
        Watchlist.__init__(self, parent)

    def add(
        self,
        property_names: Union[str, List[str]],
        *,
        listeners: Union[WatchlistEventHandler, List[WatchlistEventHandler]] = None,
    ):
        """
        Add properties to the watchlist

        Args:
            property_names: Property name(s)
            listeners: Callback to be called when the property update event is received from cs_server

        """
        if listeners is not None and not isinstance(listeners, list):
            listeners = [listeners]

        sanitized_data = PropertyCommands.sanitize_input(property_names, list)

        self.core_tcf_node.add_to_property_watchlist(sanitized_data, self.parent.endpoint_name)

        if not self._tcf_event_listener_registered:
            self.parent.endpoint_tcf_node.add_listener(self._mandatory_event_listener)
            self._tcf_event_listener_registered = True

        watch_id = self._get_uuid()
        self._listeners[watch_id].extend(listeners)

        for property_name in sanitized_data:
            self._watch_ids_for_property[property_name].add(watch_id)

    def remove(self, property_names: Union[str, List[str]]):
        """
        Remove properties from watchlist

        Args:
            property_names: Property name(s)

        """
        sanitized_data = {
            prop
            for prop in PropertyCommands.sanitize_input(property_names, list)
            if prop in self._watch_ids_for_property
        }

        self.core_tcf_node.remove_from_property_watchlist(sanitized_data, self.parent.endpoint_name)

        for prop in sanitized_data:
            del self._watch_ids_for_property[prop]


class IBERTPropertyCommands(PropertyCommands["SerialObjectBase"]):
    def __init__(self, parent, property_endpoint):
        PropertyCommands.__init__(self, parent)

        self.watchlist = IBERTWatchlist(self)
        self.endpoint_name: Final[str] = property_endpoint.name
        self.endpoint_tcf_node = self.core_tcf_node.get_child_with_name(self.endpoint_name)

    """
    NOTE - The 'endpoint_tcf_node' is different from 'core_tcf_node'.
    core_tcf_node - Points to the IBERTCoreClient class and is needed to call server commands
    _endpoint_tcf_node - Points to the Node class which is a child of core_tcf_node. 
     Needed to access props attached to a node
     
    Example with IBERT hierarchy 
        IBERT Versal GTY  <-- core_tcf_node
        ├── Quad_206 <-- if self.endpoint_name == "Quad_206", endpoint_tcf_node points to this
        ├── Quad_204 <-- if self.endpoint_name == "Quad_204", endpoint_tcf_node points to this 
        ├── Quad_205 <-- if self.endpoint_name == "Quad_205", endpoint_tcf_node points to this 
        ├── Quad_203 <-- if self.endpoint_name == "Quad_203", endpoint_tcf_node points to this 
        ├── Quad_202 <-- if self.endpoint_name == "Quad_202", endpoint_tcf_node points to this  
        └── Quad_201 <-- if self.endpoint_name == "Quad_201", endpoint_tcf_node points to this
    """

    def _segregate_props(self, all_property_names) -> Tuple[Set[str], Set[str]]:
        all_property_names = set(all_property_names)

        client_side = set(self.endpoint_tcf_node.props.keys()).intersection(all_property_names)
        # Only use properties that are still in the watchlist. If a prop is deleted in the server
        # TCF node, it wont get deleted in the client TCF node. The prop value in that case would
        # be stale, since it's no longer updated via TCF property update events from the server.
        client_side.intersection_update(self.watchlist.active_properties)

        server_side = all_property_names.difference(client_side)
        return client_side, server_side

    def get(self, property_names: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Get the property value cached in cs_server

        Args:
            property_names: Property name(s)

        Returns:
            Dictionary with property name and value as key, value pairs.

        """
        sanitized_data = PropertyCommands.sanitize_input(property_names, list)
        client_side_props, server_side_props = self._segregate_props(sanitized_data)

        all_property_values = dict()

        # Fetch client side properties from Node.props
        for property_name in client_side_props:
            all_property_values[property_name] = self.endpoint_tcf_node.props[property_name]

        if len(server_side_props) > 0:
            # If there are properties not available with the client, go to the server to fetch them
            all_property_values.update(
                self.core_tcf_node.get_property(list(server_side_props), self.endpoint_name)
            )

        return all_property_values

    def set(self, **property_dict):
        """
        Set new values for properties in cs_server

        Args:
            \*\*property_dict:
             Unpacked dict with key as property and value as new property value

        """
        sanitized_data = PropertyCommands.sanitize_input(property_dict, dict)
        return self.core_tcf_node.set_property(sanitized_data, self.endpoint_name)

    def refresh(self, property_names: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Refresh the value of properties and update it in cs_server

        Args:
            property_names: Property name(s)

        Returns:
            Dictionary with property name and refreshed value as key, value pairs.

        """
        sanitized_data = PropertyCommands.sanitize_input(property_names, list)
        return self.core_tcf_node.refresh_property(sanitized_data, self.endpoint_name)

    def commit(self, property_names: Union[str, List[str]]):
        """
        Commit the value of properties to HW

        Args:
            property_names: Property name(s)

        """
        sanitized_data = PropertyCommands.sanitize_input(property_names, list)
        return self.core_tcf_node.commit_property(sanitized_data, self.endpoint_name)

    def report(self, property_names: Union[str, List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Generate a report providing detailed information about the properties.

        Args:
            property_names: Property name(s)

        Returns:
            Dictionary with property name and information as key, value pairs.

        """
        sanitized_data = []
        if property_names is not None:
            sanitized_data = PropertyCommands.sanitize_input(property_names, list)
        return self.core_tcf_node.report_property(sanitized_data, self.endpoint_name)


parent_type = TypeVar("parent_type")
child_type = TypeVar("child_type")


class SerialObjectBase(Generic[parent_type, child_type]):
    """
    Abstract base class for all serial objects
    """

    def __init__(
        self,
        *,
        name: str,
        type: str,
        parent: parent_type,
        handle: str,
        core_tcf_node: IBERTCoreClient,
        property_for_alias: Dict[str, str],
        is_property_endpoint: bool,
        modifiable_aliases: Set[str],
    ):
        self.name: Final[str] = name
        """Object name"""

        self.type: Final[str] = type
        """Object type"""

        self.handle: Final[str] = handle
        """Object handle from cs_server"""

        self.parent: Final[parent_type] = parent
        """Parent of this object"""

        self.children: QueryList[child_type] = QueryList()
        """Direct children of this object"""

        self.core_tcf_node: Final[IBERTCoreClient] = core_tcf_node

        self.property_for_alias: Dict[str, str] = property_for_alias
        """Alias to property name mapping"""

        self.modifiable_aliases: Set[str] = modifiable_aliases

        self._property_endpoint: Type[SerialObjectBase]
        if is_property_endpoint:
            self._property_endpoint = self
        else:
            if self.parent._property_endpoint is None:
                raise ValueError(
                    f"Property endpoint for {self.parent.handle} is None! "
                    f"Cannot determine property endpoint for {self.handle}"
                )

            self._property_endpoint = self.parent._property_endpoint

        self.property: IBERTPropertyCommands = IBERTPropertyCommands(
            parent=self,
            property_endpoint=self._property_endpoint,
        )

        self.filter_by = {}

    def __repr__(self):
        return f"{self.type} - {self.name} - {self.handle}"

    def __rich_tree__(self):
        root = Tree(self.name)
        for child in self.children:
            try:
                root.add(child.__rich_tree__())
            except AttributeError:
                root.add(child.name)

        return root

    # Explicitly use property from builtins here, since this class has instance var with same name
    @builtins.property
    def aliases(self) -> Set[str]:
        """

        Returns:

        """
        return set(self.property_for_alias.keys())

    def reset(self):
        raise NotImplementedError(f"Reset is not supported for {self.handle}!")
