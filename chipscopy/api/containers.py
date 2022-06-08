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
from inspect import getattr_static
from typing import TypeVar, Sequence, Any
from collections import UserDict, UserList

# This along with the Generic[T] base class for QueryList is needed to allow type hints such as
# QueryList[VIO] - Implies the QueryList contains only VIO cores
T = TypeVar("T")


# The Generic[T] adds the ability to subscript i.e. use the [], for QueryList in type hints
class QueryList(UserList, Sequence[T]):
    """
    QueryList is a simple custom list with a few extra bells and whistles.

    QueryList elements can be any object. If the elements contain a dictionary member called "filter_by",
    those key/value pairs in the dictionary are used for filtering.

    A custom matching function can be specified in this querylist using set_custom_match_function. Any
    custom match function takes priority when matching over the optional filter_by attribute.
    """

    def __init__(self, initlist=None):
        self.custom_match_function = None
        super().__init__(initlist=initlist)

    def __str__(self):
        s = ",\n    ".join([f"'{str(item)}'" for item in self])
        return f"[\n    {s}\n]"

    def set_custom_match_function(self, match_function):
        """Sets an optional custom match function for the QueryList. If a custom match function is set,
        each list item is compared using the match function. The match function is expected to return
        True if the list_item matches the passed in key/value pair.

        Args:
            match_function(list_item, key, value):: A custom list element matching function
        """
        self.custom_match_function = match_function

    def all(self) -> "QueryList[T]":
        """
        Returns: every element in list
        """
        return self

    def get(self, **filters: Any) -> T:
        """Get one list item matching the filter. If exactly one list item does not match the filter, a ValueError
        is raised.

        Args:
            \*\*filters:

        Returns:
            The one element matching the filter
        """
        if filters:
            filtered_result = self.filter_by(**filters)
        else:
            filtered_result = self.all()

        if len(filtered_result) != 1:
            raise ValueError(
                f"Error:QueryList:get() - returned {len(filtered_result)} objects instead of exactly 1"
            )
        return filtered_result[0]

    def at(self, index) -> T:
        """
        Return value from index

        Args:
            index: Index of the element to get

        Returns:
            Element at index
        """
        return self[index]

    def filter_by(self, **filters: Any) -> "QueryList[T]":
        """
        Iterate through list and return only those elements that match specifications in filters.
        For an item to qualify as 'filterable', the item must be an object and have an attribute
        named `filter_by` of type Dict[str, Any].

        This function will use the filters provided to it and match all the specifications
        against the data in the `filter_by` attribute of the each element in the list.

        Args:
            \*\*filters: attribute=`value` syntax, will try to access this attribute of the object and if there is a
            match objects with matching values for said attribute shall be returned. Example: family="versal"

        Returns:
            List of elements that match the specifications provided
        """
        retval = QueryList()
        retval.set_custom_match_function(self.custom_match_function)

        for list_item in self:
            # First priority is a custom match function set on this QueryList.
            # Custom match function works across all list elements without regard to filter_by property.
            if self.custom_match_function:
                # Non-default match function - this is the first priority to check for a match
                matched = True
                for key, value in filters.items():
                    if not self.custom_match_function(list_item, key, value):
                        matched = False
                if matched:
                    retval.append(list_item)
            else:
                # To support filtering the object must have 'filter_by' attribute as a second priority to
                # the custom match function.
                # filter_by is a dict where the key is a property name, and value is a property value.
                if not hasattr(list_item, "filter_by"):
                    continue
                matched = True
                for key, value in filters.items():
                    # If the object has it's own staticmethod 'check_for_filter_match()', call it
                    # else use the static 'check_for_filter_match' in this class
                    match_function = QueryList.check_for_filter_match
                    try:
                        _ = getattr_static(list_item, "check_for_filter_match")
                        match_function = list_item.check_for_filter_match
                    except AttributeError:
                        pass
                    if not match_function(list_item.filter_by, key, value):
                        matched = False
                if matched:
                    retval.append(list_item)

        return retval

    @staticmethod
    def check_for_filter_match(filters_dict, filter_name, match_value) -> bool:
        if filter_name not in filters_dict:
            return False

        pattern = str(match_value)
        string_to_match = str(filters_dict[filter_name])
        match_result = re.fullmatch(pattern, string_to_match)
        return match_result is not None


class QueryDict(UserDict):
    """
    Dictionary with bells and whistles
    """

    def flatten(self, sort_by_key: bool = True, separator: str = "/"):
        """
        Flatten a nested dictionary

        Args:
            sort_by_key: True if keys should be sorted alphabetically

            separator: The character(s) to use when joining parent and child key

        """

        def flattener(input_dict):
            return_val = dict()
            for key, value in input_dict.items():
                if not isinstance(value, dict):
                    return_val[key] = value
                else:
                    for k, v in value.items():
                        if not isinstance(v, dict):
                            return_val[f"{key + separator + k}"] = v
                        else:
                            return_val.update(flattener({f"{key + separator + k}": v}))
            return return_val

        x = QueryDict(flattener(self))
        if sort_by_key:
            return {key: x[key] for key in sorted(x.keys())}
        return x
