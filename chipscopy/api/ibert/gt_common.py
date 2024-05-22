# Copyright (C) 2024, Advanced Micro Devices, Inc.
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

from chipscopy.api.ibert.aliases import CHILDREN, TYPE, PLL_SOURCE, PLL_KEY
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from chipscopy.api.ibert.pll import PLL
from more_itertools import one
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.gt_group import GTGroup  # noqa


@final
class GTCOMMON(SerialObjectBase["GTGroup", None]):
    def __init__(self, gt_common_info: Dict[str, Any], parent, tcf_node):
        SerialObjectBase.__init__(self, gt_common_info, parent, tcf_node)

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

        self.pll: list[PLL] = []
        "PLL driving this GT_COMMON"

    def setup(self):
        if self.setup_done:
            return

        obj_info = self.core_tcf_node.get_obj_info(self.handle)

        self._build_aliases(obj_info)

        if not obj_info.get(CHILDREN):
            return

        # Build the child objects
        for child_name, child_obj_info in obj_info[CHILDREN].items():
            if child_obj_info[TYPE].startswith(PLL_KEY):
                obj = PLL(child_obj_info, self, self.core_tcf_node)
            else:
                continue

            obj.setup()
            self._children.append(obj)
            self.pll.append(obj)

        self.setup_done = True
