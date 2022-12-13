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

from rich.tree import Tree
from typing import TYPE_CHECKING, ClassVar, Dict, Optional

from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore
from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.aliases import CHILDREN, GT_GROUP_KEY, HANDLE_NAME, IBERT_KEY, TYPE
from chipscopy.api.ibert.gt_group import GTGroup
from chipscopy.api.report import report_hierarchy
from chipscopy.utils import deprecated_api
from typing_extensions import Final, final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.client.ibert_core_client import IBERTCoreClient


@final
class IBERT(DebugCore["IBERTCoreClient"]):
    """
    Main API class to use IBERT (Integrated Bit Error Ratio Tester) debug core.
    """

    def __init__(self, ibert_tcf_node, *, use_tiered_init: bool):
        super(IBERT, self).__init__(CoreType.IBERT, ibert_tcf_node)

        self.layout = None

        self.type: Final[str] = IBERT_KEY
        """Serial object type"""

        self.children: QueryList[GTGroup] = QueryList()
        """Children of IBERT"""

        if use_tiered_init:
            # START = time.perf_counter()
            tier1_init_data = self.core_tcf_node.tier1_initialize()
            # print(f"Skeleton cmd runtime - {time.perf_counter() - START}")
            self.name: str = tier1_init_data["DISPLAY_NAME"]
            """Name of the IBERT core"""

            self.handle = "NA"
            """Handle from cs_server"""

            # This is used by the filter_by method in QueryList
            self.filter_by = {"name": self.name, "type": self.type}
        else:
            self.setup()

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
        return self.children.filter_by(type=GT_GROUP_KEY)

    def reset(self):
        """
        Reset all RXs, TXs and PLLs in the GT Groups
        """
        for gt_group in self.gt_groups:
            gt_group.reset()

    def setup(self):
        # layout is None in case tiered init was used, else it's a dict with data
        if self.layout is not None:
            return

        self.core_tcf_node.initialize()
        layout = self.core_tcf_node.get_layout()

        # At the top most level only one key = IBERT name is expected
        self.name = list(layout.keys())[0]
        configuration = layout[self.name]

        self.handle = configuration[HANDLE_NAME]

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

        if CHILDREN in configuration:
            # Build the child objects
            for child_name, child_configuration in configuration[CHILDREN].items():
                if child_configuration[TYPE] == GT_GROUP_KEY:
                    child_class = GTGroup
                else:
                    continue

                new_child = child_class(
                    name=child_name,
                    parent=self,
                    tcf_node=self.core_tcf_node,
                    configuration=child_configuration,
                )
                self.children.append(new_child)

    @deprecated_api(release="2021.1", replacement="report_hierarchy(<Any serial object>)")
    def print_hierarchy(self):
        """
        Prints hierarchy of IBERTs child objects like the GT Group, GT, PLL etc to stdout.
        The format is similar to the output of the unix command - `tree`
        """
        report_hierarchy(self)
