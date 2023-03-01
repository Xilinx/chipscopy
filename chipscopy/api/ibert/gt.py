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

from typing import TYPE_CHECKING, Dict, Union, Any

from chipscopy.api.ibert.aliases import CHILDREN, RX_KEY, TX_KEY, TYPE, PLL_SOURCE
from chipscopy.api.ibert.rx import RX
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from chipscopy.api.ibert.tx import TX
from more_itertools import one
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.gt_group import GTGroup  # noqa
    from chipscopy.api.ibert.pll import PLL


@final
class GT(SerialObjectBase["GTGroup", Union[TX, RX]]):
    def __init__(self, gt_info: Dict[str, Any], parent, tcf_node):
        SerialObjectBase.__init__(self, gt_info, parent, tcf_node)

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

        self.pll: PLL = None
        "PLL driving this GT"

        self.rx: RX = None
        """RX of the GT"""

        self.tx: TX = None
        """TX of the GT"""

    # def __repr__(self) -> str:
    #     return self.name

    def reset(self):
        """
        Reset the TX and RX in the GT
        """
        self.setup()

        if self.rx:
            self.rx.reset()
        if self.tx:
            self.tx.reset()

    def update_pll(self):
        """Updates the reference to the pll attribute based on the appropriate property value"""
        if not self.setup_done:
            raise RuntimeError("Call this only after setup is complete for the GT")

        if PLL_SOURCE not in self._property_for_alias:
            return
        _, pll_name_for_this_gt = self._property.get(self._property_for_alias[PLL_SOURCE]).popitem()
        for pll in self.parent.plls:
            if pll.name == pll_name_for_this_gt:
                self.pll = pll
                break

    def setup(self):
        if self.setup_done:
            return

        obj_info = self.core_tcf_node.get_obj_info(self.handle)

        self._build_aliases(obj_info)

        if not obj_info.get(CHILDREN):
            return

        # Build the child objects
        for child_name, child_obj_info in obj_info[CHILDREN].items():
            obj: Union[TX, RX]
            if child_obj_info[TYPE] == RX_KEY:
                obj = RX(child_obj_info, self, self.core_tcf_node)
            elif child_obj_info[TYPE] == TX_KEY:
                obj = TX(child_obj_info, self, self.core_tcf_node)
            else:
                continue

            obj.setup()
            self._children.append(obj)

        # We always expect a GT to have one valid RX and one valid TX, no more, no less.
        self.rx = one(
            self._children.filter_by(type=RX_KEY),
            too_short=RuntimeError(f"No RX associated with GT {self.handle}!"),
            too_long=RuntimeError(f"More than one RX found for GT {self.handle}!"),
        )

        self.tx = one(
            self._children.filter_by(type=TX_KEY),
            too_short=RuntimeError(f"No TX associated with GT {self.handle}!"),
            too_long=RuntimeError(f"More than one TX found for GT {self.handle}!"),
        )

        self.setup_done = True
