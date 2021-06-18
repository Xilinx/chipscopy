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

from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class EyeScanParam:
    name: str
    """Name of the eye scan param"""

    modifiable: bool = False
    """Can the parameter value be modified"""

    valid_values: List[Union[int, str]] = None
    """Valid values for the parameter, if it can be modified"""

    default_value: Union[int, str] = None
    """Default value of the parameter"""

    value: Optional[Union[int, str]] = None
    """Value set by the user. Taken into consideration only if the param is modifiable"""
