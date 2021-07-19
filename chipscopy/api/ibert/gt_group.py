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

from typing import TYPE_CHECKING, Dict, Union

from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.aliases import (
    ALIAS_DICT,
    CHILDREN,
    GT_KEY,
    HANDLE_NAME,
    MODIFIABLE_ALIASES,
    PLL_KEY,
    PROPERTY_ENDPOINT,
    TYPE,
)
from chipscopy.api.ibert.gt import GT
from chipscopy.api.ibert.pll import PLL
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.ibert import IBERT


@final
class GTGroup(SerialObjectBase["IBERT", Union[GT, PLL]]):
    def __init__(self, name, parent, tcf_node, configuration):
        SerialObjectBase.__init__(
            self,
            name=name,
            type=configuration[TYPE],
            parent=parent,
            handle=configuration[HANDLE_NAME],
            core_tcf_node=tcf_node,
            property_for_alias=configuration.get(ALIAS_DICT, dict()),
            is_property_endpoint=configuration.get(PROPERTY_ENDPOINT, False),
            modifiable_aliases=configuration.get(MODIFIABLE_ALIASES, set()),
        )

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

        if CHILDREN not in configuration:
            return

        # Build the child objects
        for child_name, child_configuration in configuration[CHILDREN].items():
            if child_configuration[TYPE] == GT_KEY:
                child_class = GT
            elif child_configuration[TYPE].startswith(PLL_KEY):
                child_class = PLL
            else:
                continue

            new_child = child_class(
                name=child_name,
                parent=self,
                tcf_node=self.core_tcf_node,
                configuration=child_configuration,
            )
            self.children.append(new_child)

        self.gts: QueryList[GT] = self.children.filter_by(type=GT_KEY)
        """GT children"""

        self.plls: QueryList[PLL] = self.children.filter_by(type=PLL_KEY)
        """PLL children"""

        # Do this after self.plls has been populated;
        # update_pll() looks through self.plls to determine the PLL for the GT
        for gt in self.gts:
            gt.update_pll()

    def __repr__(self) -> str:
        return self.name

    def reset(self):
        """
        Reset the RXs, TXs and PLLs that are part of the GT Group
        """
        for gt in self.gts:
            gt.reset()
        for pll in self.plls:
            pll.reset()
