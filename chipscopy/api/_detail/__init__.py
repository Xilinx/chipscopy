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
from dataclasses import fields
from typing import Tuple


def dataclass_fields(cls: type) -> Tuple[str]:
    """Make tuple with data class member names."""
    return tuple([f.name for f in fields(cls)])


def filter_props(props: {}, prop_filter: [str]) -> {}:
    return {n: v for n, v in props.items() if n in prop_filter}
