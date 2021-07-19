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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Union

from chipscopy.api.containers import QueryList

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.link import Link


@dataclass
class LinkGroup:
    """
    Container class for holding links.
    **Please do not** create an instance of this class directly. Please use the factory method
    :py:func:`~chipscopy.api.ibert.create_link_group` instead.
    """

    name: str
    """Name of the link group"""

    description: str
    """Description of this link group"""

    _links: Dict[str, "Link"]
    filter_by: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.filter_by = {"name": self.name}

    def __repr__(self) -> str:
        return f"{self.name} - {[link for link in self._links]}"

    @property
    def links(self) -> QueryList["Link"]:
        return QueryList(self._links.values())

    def invalidate(self):
        for link in self._links.values():
            link.link_group = None

        self.name = ""
        self.description = ""
        self._links.clear()

    def add(self, links: Union["Link", List["Link"], QueryList["Link"]]):
        """
        Add link(s) to the link group

        Args:
            links: Link(s) to add

        """
        if not isinstance(links, list) and not isinstance(links, QueryList):
            links = [links]

        for link in links:
            link.link_group = self
            self._links[link.name] = link

    def remove(self, links: Union["Link", List["Link"], QueryList["Link"]] = None):
        """
        Remove link(s) from the link group

        Args:
            links: **(Optional)** Link(s) to remove

        .. note::
            If no link(s) is(are) provided, all links in the link group, will be removed

        """
        if links is None:
            links = [link for link in self._links]

        if not isinstance(links, list) and not isinstance(links, QueryList):
            links = [links]

        for link in links:
            link.link_group = None
            del self._links[link.name]
