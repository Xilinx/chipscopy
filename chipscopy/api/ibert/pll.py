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

from typing import TYPE_CHECKING, Any, Dict

from chipscopy.api.ibert.aliases import PLL_LOCK_STATUS, PLL_RESET
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.gt_group import GTGroup  # noqa


@final
class PLL(SerialObjectBase["GTGroup", None]):
    def __init__(self, pll_info: Dict[str, Any], parent, tcf_node):
        SerialObjectBase.__init__(self, pll_info, parent, tcf_node)

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

    # def __repr__(self) -> str:
    #     return self.name

    @staticmethod
    def check_for_filter_match(filters_dict, filter_name, match_value) -> bool:
        if filter_name not in filters_dict:
            return False

        # Special case for "type" filter, since it can be "PLL/<RPLL/LCPLL>".
        # So use startswith instead of ==
        return (
            filters_dict[filter_name].startswith(match_value)
            if filter_name == "type"
            else filters_dict[filter_name] == match_value
        )

    @property
    def locked(self) -> bool:
        _, prop_value = self.property.refresh(self.property_for_alias[PLL_LOCK_STATUS]).popitem()
        return True if prop_value == "Locked" else False

    def reset(self):
        """
        Reset the PLL
        """
        if PLL_RESET not in self.property_for_alias:
            raise RuntimeError(f"PLL '{self.handle}' cannot be reset!")

        props = {self.property_for_alias[PLL_RESET]: 0x1}
        self.property.set(**props)
        self.property.commit(self.property_for_alias[PLL_RESET])
