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

from typing import TYPE_CHECKING

from chipscopy.api.ibert.aliases import (
    ALIAS_DICT,
    HANDLE_NAME,
    MODIFIABLE_ALIASES,
    PLL_LOCK_STATUS,
    PROPERTY_ENDPOINT,
    TYPE,
    PLL_RESET,
)
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from typing_extensions import final

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.gt_group import GT


@final
class PLL(SerialObjectBase["GTGroup", None]):
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

    def __repr__(self) -> str:
        return self.name

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
