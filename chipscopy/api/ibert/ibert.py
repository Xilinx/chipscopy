# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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

from rich.tree import Tree
from typing import TYPE_CHECKING

from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.aliases import GT_GROUP_KEY, HANDLE_NAME, IBERT_KEY, DISPLAY_NAME
from chipscopy.api.ibert.gt_group import GTGroup
from chipscopy.api.report import report_hierarchy
from chipscopy.utils import deprecated_api
from typing_extensions import Final, final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.client.ibert_core_client import IBERTCoreClient  # noqa


@final
class IBERT(DebugCore["IBERTCoreClient"]):
    """
    Main API class to use IBERT (Integrated Bit Error Ratio Tester) debug core.
    """

    def __init__(self, ibert_tcf_node):
        super(IBERT, self).__init__(CoreType.IBERT, ibert_tcf_node)
        _, core_info = self.core_tcf_node.initialize_architecture().popitem()

        self._gt_groups_discovery_complete: bool = False

        self.type: Final[str] = IBERT_KEY
        """Serial object type"""

        self.children: QueryList[GTGroup] = QueryList()
        """Children of IBERT"""

        self.name: str = core_info[DISPLAY_NAME]
        """Name of the IBERT core"""

        self.handle = core_info[HANDLE_NAME]
        """Handle from cs_server"""

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

    def __repr__(self) -> str:
        return self.name

    def __rich_tree__(self):
        root = Tree(self.name)

        for child in self.children:
            root.add(child.__rich_tree__())

        return root

    @property
    def gt_groups(self) -> QueryList[GTGroup]:
        """GT Group children of the IBERT core"""
        self.discover_gt_groups()
        return self.children.filter_by(type=GT_GROUP_KEY)

    def discover_gt_groups(self, *, include_uninstantiated: bool = False):
        """
        Discover all GT Groups that are instantiated by the design.

        Args:
            include_uninstantiated (bool): If you wish to include un-instantiated GT Groups in the discovery process,
                set this to 'True'.

        Returns:
            None
        """
        if self._gt_groups_discovery_complete:
            return

        gt_group_handles = self.core_tcf_node.discover_gt_groups(include_uninstantiated)
        if isinstance(gt_group_handles, str):
            gt_group_handles = [gt_group_handles]

        for handle in gt_group_handles:
            obj_info = self.core_tcf_node.get_obj_info(handle, include_property="client_visible")
            self.children.append(GTGroup(obj_info, self, self.core_tcf_node))

        self._gt_groups_discovery_complete = True

    def reset(self):
        """
        Reset all RXs, TXs and PLLs in the GT Groups
        """
        for gt_group in self.gt_groups:
            gt_group.reset()

    @deprecated_api(release="2021.1", replacement="report_hierarchy(<Any serial object>)")
    def print_hierarchy(self):
        """
        Prints hierarchy of IBERTs child objects like the GT Group, GT, PLL etc to stdout.
        The format is similar to the output of the unix command - `tree`
        """
        report_hierarchy(self)
