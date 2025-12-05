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

from typing import TYPE_CHECKING, Dict, Union, Any

from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.aliases import CHILDREN, GT_KEY, GT_COMMON_KEY, PLL_KEY, TYPE
from chipscopy.api.ibert.gt import GT
from chipscopy.api.ibert.gt_common import GTCOMMON
from chipscopy.api.ibert.pll import PLL
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.ibert import IBERT  # noqa


@final
class GTGroup(SerialObjectBase["IBERT", Union[GT, PLL]]):
    def __init__(self, gt_group_info: Dict[str, Any], parent, tcf_node):
        SerialObjectBase.__init__(self, gt_group_info, parent, tcf_node)

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

    # def __repr__(self) -> str:
    #     return self.name

    @property
    def gts(self) -> QueryList[GT]:
        """GTs in this GT Group"""
        self.setup()
        return self._children.filter_by(type=GT_KEY)

    @property
    def gtcommons(self) -> QueryList[GT]:
        """GTs in this GT Group"""
        self.setup()
        return self._children.filter_by(type=GT_COMMON_KEY)

    @property
    def plls(self) -> QueryList[PLL]:
        """PLL(s) in this GT Group"""
        self.setup()
        all_gt_group_plls = self._children.filter_by(type=PLL_KEY)
        for child in self.children:
            child.setup()
            all_gt_group_plls.extend(child.children.filter_by(type=PLL_KEY))
        if len(all_gt_group_plls) == 1:
            return all_gt_group_plls[0]
        return all_gt_group_plls

    def reset(self):
        """
        Reset the RXs, TXs and PLLs that are part of the GT Group
        """
        # Needn't call setup() here; Accessing 'gts' and 'plls' will trigger that call
        for gt in self.gts:
            gt.reset()
        for pll in self.plls:
            pll.reset()

    def setup(self):
        if self.setup_done:
            return

        self.core_tcf_node.setup_gt_group(self.name)
        obj_info = self._get_obj_info_with_props()
        self._update_all_props(obj_info)
        self._build_aliases(obj_info)

        if not obj_info.get(CHILDREN):
            return

        for child_info in obj_info[CHILDREN].values():
            obj: Union[GT, PLL]
            if child_info[TYPE] == GT_KEY:
                obj = GT(child_info, self, self.core_tcf_node)
            elif child_info[TYPE] == GT_COMMON_KEY:
                obj = GTCOMMON(child_info, self, self.core_tcf_node)
            elif child_info[TYPE].startswith(PLL_KEY):
                obj = PLL(child_info, self, self.core_tcf_node)
            else:
                continue

            obj.setup()
            self._children.append(obj)

        self.setup_done = True

        # Call this only after setup is complete.
        for gt in self.gts:
            gt.update_pll()
