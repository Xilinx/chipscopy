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

import builtins
import json
from typing import TypeVar, Generic, TYPE_CHECKING, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

from chipscopy.api import CoreInfo, get_core_info
from chipscopy.api._detail.property import PropertyCommands

if TYPE_CHECKING:
    from chipscopy import CoreType


T = TypeVar("T")


@dataclass
class DebugCore(Generic[T]):
    """DebugCore maps a CoreType to the associated tcf_node and core_implementation.

    At the low level, debug cores have a tcf node that is used to get and set properties.
    This high level API hides the tcf nodes by wrapping them with a core implementation.
    During discover_and_setup_cores() core scanning, the device.debug_core_dict
     is set up with CoreType -> _DebugCore mapping for every detected core.
    """

    core_type: "CoreType"
    core_tcf_node: T
    filter_by: Dict[str, Any] = field(default_factory=dict)
    property: PropertyCommands = None
    core_info: Optional[CoreInfo] = None

    def __post_init__(self):
        self.property = PropertyCommands(self)
        self.core_info = get_core_info(self.core_tcf_node)

    @builtins.property
    def context(self) -> str:
        ctx = ""
        if self.core_tcf_node:
            ctx = self.core_tcf_node.ctx
        return ctx

    def get_tcf_props(self) -> Dict:
        d = {}
        if self.core_tcf_node:
            d.update(self.core_tcf_node.props)
            d.update(self.core_tcf_node.get_property_group([]))
        return d

    def to_dict(self) -> Dict:
        d = {}
        if self.core_tcf_node:
            core_info = get_core_info(self.core_tcf_node)
            if core_info:
                d.update({"core_info": asdict(core_info)})
        return d

    def to_json(self) -> str:
        d = self.to_dict()
        d.update({"tcf": self.get_tcf_props()})
        json_dict = json.dumps(dict(sorted(d.items())), indent=4, default=lambda o: str(o))
        return json_dict

    # NOTE - If you want to use the @property to define a property for this class, make sure to
    #  use @builtins.property and not just @property.
    #  This is needed since this class defines an instance var with the same name.
