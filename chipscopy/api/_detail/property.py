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

import uuid
from collections import defaultdict
from queue import Queue
from typing import (
    Generic,
    Iterable,
    Optional,
    Callable,
    TYPE_CHECKING,
    Set,
    List,
    Dict,
    Any,
    Union,
    Tuple,
    TypeVar,
)
from threading import Lock
from datetime import datetime
from dataclasses import dataclass

from chipscopy.utils.printer import printer

if TYPE_CHECKING:
    from chipscopy.dm import Node


T = TypeVar("T")


@dataclass
class PropertyUpdateEvent:
    names: List[str]
    """Names of properties in this update"""
    values: List[Any]
    """New value of properties"""
    timestamp: datetime
    """Timestamp the update event was received"""

    def __post_init__(self):
        self._max_length = 0
        for name in self.names:
            if len(name) > self._max_length:
                self._max_length = len(name)

    def __repr__(self) -> str:
        retval = f"PropertyUpdateEvent\n\tTime stamp - {str(self.timestamp)}\n"
        for name, value in zip(self.names, self.values):
            retval += f"\t{name}{' ' * (self._max_length - len(name))} = {value}\n"

        return retval


WatchlistEventHandler = Callable[["Queue[PropertyUpdateEvent]"], None]


class Watchlist(Generic[T]):
    def __init__(self, parent: T):
        self.parent = parent
        self.core_tcf_node = self.parent.core_tcf_node

        self._listeners: Dict[str, List[WatchlistEventHandler]] = defaultdict(list)
        self._update_buckets: Dict[str, "Queue[PropertyUpdateEvent]"] = defaultdict(Queue)
        self._watch_ids_for_property: Dict[str, Set[str]] = defaultdict(set)
        self._tcf_event_listener_registered: bool = False

        self._lock = Lock()

    @property
    def active_properties(self):
        return set(self._watch_ids_for_property)

    def _get_uuid(self):
        watch_id = str(uuid.uuid4())
        while watch_id in self._listeners:
            watch_id = str(uuid.uuid4())

        return watch_id

    def add(
        self,
        property_names: Union[str, List[str]],
        *,
        listeners: Optional[Union[WatchlistEventHandler, List[WatchlistEventHandler]]] = None,
    ):
        if listeners is not None and not isinstance(listeners, list):
            listeners = [listeners]

        sanitized_data = PropertyCommands.sanitize_input(property_names, list)

        self.core_tcf_node.add_to_property_watchlist(sanitized_data)

        with self._lock:
            if not self._tcf_event_listener_registered:
                self.parent.core_tcf_node.add_listener(self._mandatory_event_listener)
                self._tcf_event_listener_registered = True

            watch_id = self._get_uuid()
            self._listeners[watch_id].extend(listeners)

            for property_name in sanitized_data:
                self._watch_ids_for_property[property_name].add(watch_id)

    def remove(self, property_names: Union[str, List[str]]):
        sanitized_data = {
            prop
            for prop in PropertyCommands.sanitize_input(property_names, list)
            if prop in self.active_properties
        }

        self.core_tcf_node.remove_from_property_watchlist(sanitized_data)

        with self._lock:
            for prop in sanitized_data:
                del self._watch_ids_for_property[prop]

    def _mandatory_event_listener(self, node: "Node", updated_properties: Set[str]):
        # NOTE - This is called on the TCF event dispatcher thread

        updated_properties = list(updated_properties)
        updated_properties.sort()

        updates_by_id = dict()

        for property_name in updated_properties:
            with self._lock:
                if property_name not in self._watch_ids_for_property:
                    continue

                for watch_id in self._watch_ids_for_property[property_name]:
                    if watch_id not in updates_by_id:
                        # list at index 0 will hold the property names
                        # list at index 1 will hold property names
                        updates_by_id[watch_id]: Tuple[List[str], List[Any]] = (list(), list())

                    updates_by_id[watch_id][0].append(property_name)
                    updates_by_id[watch_id][1].append(node.props[property_name])

        if len(updates_by_id) == 0:
            return

        time_stamp = datetime.now()
        for watch_id, updates in updates_by_id.items():
            names, values = updates
            self._update_buckets[watch_id].put(
                PropertyUpdateEvent(names=names, values=values, timestamp=time_stamp)
            )

        # Call the event_listener registered by the user
        for watch_id in updates_by_id:
            with self._lock:
                if watch_id not in self._listeners or self._listeners[watch_id] is None:
                    continue

                for listener in self._listeners[watch_id]:
                    try:
                        listener(self._update_buckets[watch_id])
                    except Exception as e:
                        printer(
                            f"Unhandled exception when calling listener for watch ID {watch_id}"
                            f"\nException - {str(e)}",
                            level="warning",
                        )


class PropertyCommands(Generic[T]):
    def __init__(self, parent: T):
        self.parent = parent
        self.core_tcf_node = self.parent.core_tcf_node

        self.watchlist: Watchlist["PropertyCommands"] = Watchlist(self)

    @staticmethod
    def sanitize_input(user_input, desired_format):
        if desired_format == list:
            if isinstance(user_input, str):
                return [user_input]
            elif isinstance(user_input, Iterable):
                return list(user_input)

        elif desired_format == dict:
            if isinstance(user_input, dict):
                return user_input

        raise TypeError(f"Unsupported type {type(user_input)}!")

    def get(self, property_names: Union[str, List[str]]):
        return self.core_tcf_node.get_property(
            PropertyCommands.sanitize_input(property_names, list)
        )

    def set(self, **property_dict):
        return self.core_tcf_node.set_property(PropertyCommands.sanitize_input(property_dict, dict))

    def refresh(self, property_names: Union[str, List[str]]):
        return self.core_tcf_node.refresh_property(
            PropertyCommands.sanitize_input(property_names, list)
        )

    def commit(self, property_names: Union[str, List[str]]):
        return self.core_tcf_node.commit_property(
            PropertyCommands.sanitize_input(property_names, list)
        )

    def report(self, property_names: Union[str, List[str]]):
        return self.core_tcf_node.report_property(
            PropertyCommands.sanitize_input(property_names, list)
        )
