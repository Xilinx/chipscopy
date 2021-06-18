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

import enum
from abc import abstractmethod
from typing import List, Dict, Any, Union

from chipscopy.client.core import CoreClient
from chipscopy.dm.request import DoneCallback
from chipscopy.utils import listify

PropertyValues = Dict[str, Any]


class PropertyPermission(enum.IntFlag):
    """
        Access allowed for properties.
        Bit field to check what methods are allowed on a particular property.
        See :meth:`AxisILAService.report_property`

        When passing enum values to/from API functions, use int values.

    ::

        COMMIT  = 0x01
        GET     = 0x02
        REFRESH = 0x04
        RESET   = 0x08
        SET     = 0x10
    """

    #: Commit to core
    COMMIT = 0x01

    #: Get from core object
    GET = 0x02

    #: Refresh data in core object with data from the core
    REFRESH = 0x04

    #: Reset the value in the core object
    RESET = 0x08

    #: Set the value in the core object
    SET = 0x10

    @staticmethod
    def get_str_representation(permission_as_int: int) -> List[str]:
        permissions = list()

        permission_as_bin = bin(permission_as_int)[2:].zfill(5)
        if permission_as_bin[-1] == "1":
            permissions.append("COMMIT")

        if permission_as_bin[-2] == "1":
            permissions.append("GET")

        if permission_as_bin[-3] == "1":
            permissions.append("REFRESH")

        if permission_as_bin[-4] == "1":
            permissions.append("RESET")

        if permission_as_bin[-5] == "1":
            permissions.append("SET")

        return permissions


class CorePropertyClient(CoreClient):
    @abstractmethod
    def get_service_proxy(self):
        pass

    def get_property(self, property_names: List[str], done: DoneCallback = None):
        """
        Get values for properties.

        :param property_names: List of property names. Empty list means get all properties.
        :param done: Callback with result and any error.
        :return: Property name/value pairs in a dict. See :data:`PropertyValues`.
        """
        service, done_cb = self.make_done(done)
        token = service.get_property(self.ctx, property_names, done_cb)
        return self.add_pending(token)

    def get_property_group(self, groups: List[str], done: DoneCallback = None):
        """
        Get property values for property groups.

        :param groups: List of property group names. Empty list means all properties.
        :param done: Callback with result and any error.
        :return: Properties for named group names. :data:`PropertyValues`
        """
        service, done_cb = self.make_done(done)
        token = service.get_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def report_property(self, property_names: List[str], done: DoneCallback = None):
        """
        Return description of properties.

        Example: Description of property 'state'
        ::

            Attributes:

            group_name - Property group which the property belongs to.
            type - Property value type
            permission - Permissions control which methods can operate on property.
            name - Name of property
            default_value - Reset value for property.
            value - Current value of the property.

            {
                'state': {
                    'group_name': 'core_info',
                    'type': int),
                    'permission': 2,        # corresponds to bitwise enum value <_PropertyPermission.GET: 2>,
                    'name': 'core_major_ver',
                    'default_value': 0,
                    'value': 3
                }
            }

        For further information about 'permission', see :class:`_PropertyPermission`

        :param property_names: List of property names. Empty list means get all properties.
        :param done: Callback with result and any error.
        :return: Dict of property description dicts.
        """
        service, done_cb = self.make_done(done)
        token = service.report_property(self.ctx, property_names, done_cb)
        return self.add_pending(token)

    def report_property_group(self, groups: List[str], done: DoneCallback = None):
        """
        Return description of properties, which belong to argument 'groups'.

        :param groups: List of property group names. Empty list means all properties.
        :param done: Callback with result and any error.
        :return: Dict of property description dicts.
        """
        service, done_cb = self.make_done(done)
        token = service.report_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def reset_property(self, property_names: List[str], done: DoneCallback = None):
        """
        Reset property values, to default values.

        :param property_names: List of property names. Empty list means all resettable properties.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.reset_property(self.ctx, property_names, done_cb)
        return self.add_pending(token)

    def reset_property_group(self, groups: List[str], done: DoneCallback = None):
        """

        :param groups:  List of property group names. Empty list means all resettable properties.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.reset_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def set_property(self, property_values: Dict[str, Any], done: DoneCallback = None):
        """
        Set properties. If no properties specified, do nothing.
        Validates properties values for correctness.

        :param property_values: Property name/value pairs.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.set_property(self.ctx, property_values, done_cb)
        return self.add_pending(token)

    def set_property_group(self, property_values: Dict[str, Any], done: DoneCallback = None):
        """
        Set properties. If no properties specified, do nothing.
        Validates properties values for correctness.

        :param property_values: Property name/value pairs.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.set_property_group(self.ctx, property_values, done_cb)
        return self.add_pending(token)

    def commit_property_group(self, groups: List[str], done: DoneCallback = None):
        """
        Write current property group values to the core.

        :param groups: Group name or list of names.
            Empty list means property groups, which can be written to the core.
        :param done: Callback with result and any error.
        """
        service, done_cb = self.make_done(done)
        token = service.commit_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def refresh_property_group(self, groups: List[str], done: DoneCallback = None):
        """
        Read values from the core, update ILA properties
        and return those property values to caller.

        :param groups: List of group names.
            Empty list means all refreshable groups.
        :param done: Callback with result and any error.
        :returns: Property name/value pairs.
        """
        service, done_cb = self.make_done(done)
        token = service.refresh_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def list_property_groups(self, done: DoneCallback = None):
        service, done_cb = self.make_done(done)
        token = service.list_property_groups(self.ctx, done_cb)
        return self.add_pending(token)

    def add_to_property_watchlist(
        self, property_names: Union[str, List[str]], *, done: DoneCallback = None
    ):
        service, done_cb = self.make_done(done)
        property_names = listify(property_names)
        token = service.add_to_property_watchlist(property_names, done_cb)
        return self.add_pending(token)

    def remove_from_property_watchlist(
        self, property_names: Union[str, List[str]], *, done: DoneCallback = None
    ):
        service, done_cb = self.make_done(done)
        property_names = listify(property_names)
        token = service.remove_from_property_watchlist(property_names, done_cb)
        return self.add_pending(token)

    def commit_memory(
        self,
        property_name: str,
        data: bytearray,
        start_byte_index: int,
        word_byte_length: int,
        done: DoneCallback = None,
    ):
        """
        Test function to write to debug core memory

        :param property_name: Name of memory property.
        :param data: Binary data to be written.
        :param start_byte_index:  Memory byte index, to start writing data. Must be on word boundary
        :param word_byte_length: Number of bytes per memory word.
        """
        service, done_cb = self.make_done(done)
        token = service.commit_memory(
            self.ctx, property_name, data, start_byte_index, word_byte_length, done_cb
        )
        return self.add_pending(token)

    def refresh_memory(
        self,
        property_name: str,
        byte_count: int,
        start_byte_index: int,
        word_byte_length: int,
        done: DoneCallback = None,
    ):
        """
        Test function to read debug core memory

        :param property_name: Name of memory property
        :param byte_count: Number of bytes to read.
        :param start_byte_index: Memory byte index, to start reading data. Must be on word boundary.
        :param word_byte_length: Number of bytes per memory word.
        :return: bytearray holding read data.
        """
        service, done_cb = self.make_done(done)
        token = service.refresh_memory(
            self.ctx, property_name, byte_count, start_byte_index, word_byte_length, done_cb
        )
        return self.add_pending(token)
