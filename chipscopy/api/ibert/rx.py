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

from typing import TYPE_CHECKING, List, Optional

from chipscopy.api.ibert.aliases import (
    ALIAS_DICT,
    HANDLE_NAME,
    MODIFIABLE_ALIASES,
    PROPERTY_ENDPOINT,
    TYPE,
    RX_RESET,
)
from chipscopy.api.ibert.serial_object_base import SerialObjectBase
from typing_extensions import final

if TYPE_CHECKING:
    from chipscopy.api.ibert.gt import GT
    from chipscopy.api.ibert.link import Link
    from chipscopy.api.ibert.pll import PLL
    from chipscopy.api.ibert.scan import EyeScan


@final
class RX(SerialObjectBase["GT", None]):
    def __init__(self, name, parent, tcf_node, configuration: dict):
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

        self.link: Optional[Link] = None
        """Link the RX is part of"""

        self.eye_scan: Optional[EyeScan] = None
        """Most recently run eye scan"""

        self.eye_scan_names: List[str] = list()
        """Name of all the eye scans run"""

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "type": self.type, "handle": self.handle}

    def __repr__(self) -> str:
        return self.name

    @property
    def pll(self) -> PLL:
        """
        PLL driving the RX

        Returns:
            :py:class:`~chipscopy.api.ibert.pll.PLL` : PLL object
        """
        return self.parent.pll

    def reset(self):
        """
        Reset the RX
        """
        if RX_RESET not in self.property_for_alias:
            raise RuntimeError(f"Rx '{self.handle}' cannot be reset!")

        props = {self.property_for_alias[RX_RESET]: 0x1}
        self.property.set(**props)
        self.property.commit(self.property_for_alias[RX_RESET])
