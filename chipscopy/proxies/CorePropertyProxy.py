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

from abc import ABC
from typing import Dict, List, Any, Union
from chipscopy.dm.request import DoneCallback


class CorePropertyProxy(ABC):
    def get_property(
        self, node_id: str, property_names: List[str], done: DoneCallback
    ) -> Dict[str, Any]:
        return self.send_xicom_command("getProperty", (node_id, property_names), done)

    def get_property_group(
        self, node_id: str, groups: List[str], done: DoneCallback
    ) -> Dict[str, Any]:
        return self.send_xicom_command(
            "getPropertyGroup",
            (
                node_id,
                groups,
            ),
            done,
        )

    def report_property(
        self, node_id: str, property_names: List[str], done: DoneCallback
    ) -> Dict[str, Dict[str, Any]]:
        return self.send_xicom_command(
            "reportProperty",
            (
                node_id,
                property_names,
            ),
            done,
        )

    def report_property_group(
        self, node_id: str, groups: List[str], done: DoneCallback
    ) -> Dict[str, Dict[str, Any]]:
        return self.send_xicom_command(
            "reportPropertyGroup",
            (
                node_id,
                groups,
            ),
            done,
        )

    def reset_property(self, node_id: str, property_names: List[str], done: DoneCallback):
        return self.send_xicom_command(
            "resetProperty",
            (
                node_id,
                property_names,
            ),
            done,
        )

    def reset_property_group(
        self, node_id: str, property_group_names: List[str], done: DoneCallback
    ):
        return self.send_xicom_command(
            "resetPropertyGroup",
            (
                node_id,
                property_group_names,
            ),
            done,
        )

    def set_property(self, node_id: str, property_values: Dict[str, Any], done: DoneCallback):
        return self.send_xicom_command(
            "setProperty",
            (
                node_id,
                property_values,
            ),
            done,
        )

    def set_property_group(self, node_id: str, property_values: Dict[str, Any], done: DoneCallback):
        return self.send_xicom_command(
            "setPropertyGroup",
            (
                node_id,
                property_values,
            ),
            done,
        )

    def list_property_groups(self, node_id: str, done: DoneCallback) -> list:
        return self.send_xicom_command("listPropertyGroups", (node_id,), done)

    def commit_property_group(self, node_id: str, groups: List[str], done: DoneCallback):
        return self.send_xicom_command(
            "commitPropertyGroup",
            (
                node_id,
                groups,
            ),
            done,
        )

    def refresh_property_group(
        self, node_id: str, groups: List[str], done: DoneCallback
    ) -> Dict[str, Any]:
        return self.send_xicom_command("refreshPropertyGroup", (node_id, groups), done)

    def add_to_property_watchlist(
        self, node_id: str, property_names: Union[str, List[str]], *, done: DoneCallback = None
    ):
        return self.send_xicom_command("add_to_property_watchlist", (node_id, property_names), done)

    def remove_from_property_watchlist(
        self, node_id: str, property_names: Union[str, List[str]], *, done: DoneCallback = None
    ):
        return self.send_xicom_command(
            "remove_from_property_watchlist", (node_id, property_names), done
        )

    def commit_memory(
        self,
        node_id: str,
        property_name: str,
        data: bytearray,
        start_byte_index: int,
        word_byte_length: int,
        done: DoneCallback = None,
    ) -> None:
        return self.send_xicom_command(
            "commitMemory", (node_id, property_name, data, start_byte_index, word_byte_length), done
        )

    def refresh_memory(
        self,
        node_id: str,
        property_name: str,
        byte_count: int,
        start_byte_index: int,
        word_byte_length: int,
        done: DoneCallback = None,
    ) -> None:
        return self.send_xicom_command(
            "refreshMemory",
            (node_id, property_name, byte_count, start_byte_index, word_byte_length),
            done,
        )
