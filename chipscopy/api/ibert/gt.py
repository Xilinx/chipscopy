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

from typing import TYPE_CHECKING, Dict, Union

from chipscopy.api.ibert.aliases import (
    ALIAS_DICT,
    CHILDREN,
    HANDLE_NAME,
    MODIFIABLE_ALIASES,
    PLL_SOURCE,
    PROPERTY_ENDPOINT,
    RX_KEY,
    TX_KEY,
    TYPE,
)
from chipscopy.api.ibert.rx import RX
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from chipscopy.api.ibert.tx import TX
from more_itertools import one
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.gt_group import GTGroup
    from chipscopy.api.ibert.pll import PLL


@final
class GT(SerialObjectBase["GTGroup", Union[TX, RX]]):
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

        # Create this before creating TX and RX. They will store a reference to this
        self.pll: PLL = None
        """PLL driving the GT"""

        # Build the child objects
        for child_name, child_configuration in configuration[CHILDREN].items():
            if child_configuration[TYPE] == RX_KEY:
                child_class = RX
            elif child_configuration[TYPE] == TX_KEY:
                child_class = TX
            else:
                continue

            new_child = child_class(
                name=child_name,
                parent=self,
                tcf_node=self.core_tcf_node,
                configuration=child_configuration,
            )
            self.children.append(new_child)

        # We always expect a GT to have one valid RX and one valid TX, no more, no less.
        self.rx: RX = one(
            self.children.filter_by(type=RX_KEY),
            too_short=RuntimeError(f"No RX associated with GT {self.handle}!"),
            too_long=RuntimeError(f"More than one RX found for GT {self.handle}!"),
        )
        """RX of the GT"""

        self.tx: TX = one(
            self.children.filter_by(type=TX_KEY),
            too_short=RuntimeError(f"No TX associated with GT {self.handle}!"),
            too_long=RuntimeError(f"More than one TX found for GT {self.handle}!"),
        )
        """TX of the GT"""

    def __repr__(self) -> str:
        return self.name

    def update_pll(self):
        if PLL_SOURCE not in self.property_for_alias:
            return

        _, pll_name_for_this_gt = self.property.get(self.property_for_alias[PLL_SOURCE]).popitem()
        for pll in self.parent.plls:
            if pll.name == pll_name_for_this_gt:
                self.pll = pll
                break

    def reset(self):
        """
        Reset the TX and RX in the GT
        """
        if self.rx:
            self.rx.reset()
        if self.tx:
            self.tx.reset()
