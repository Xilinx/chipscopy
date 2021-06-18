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

from typing import ClassVar, Dict, List, Optional, Union

from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.link import RX, TX, Link, LinkGroup

UnionLinkListLink = Union[Link, List[Link], QueryList[Link]]
UnionLinkGroupListLinkGroup = Union[LinkGroup, List[LinkGroup], QueryList[LinkGroup]]


class LinkManager:
    links: ClassVar[Dict[str, Link]] = dict()
    last_link_number: ClassVar[int] = -1
    link_name_prefix: ClassVar[str] = "Link_"

    @staticmethod
    def all_links() -> QueryList[Link]:
        """
        Get all :py:class:`~Link` object(s)

        Returns:
            List of link(s)
        """
        return QueryList(LinkManager.links.values())

    @staticmethod
    def create_links(*, rxs: Union[RX, List[RX]], txs: Union[TX, List[TX]]) -> QueryList[Link]:
        """
        Create link(s) for given :py:class:`~RX` object(s) and :py:class:`~TX` object(s).
        None of the RX or TX object(s) must be part of existing links.

        Args:
            rxs: RX object(s) to use for link creation

            txs: TX object(s) to use for link creation

            .. NOTE:: If passing a list of RX objects and TX objects, the length of both the lists
                must be same for link creation to succeed. For link creation, RX and TX objects
                are used in the order they appear in the lists.

        Returns:
            Newly created :py:class:`Link` object(s)

        """
        # Sanitize the input
        if isinstance(rxs, list) and isinstance(txs, list):
            if len(rxs) != len(txs):
                raise ValueError("Number of RXs and TXs provided in the lists must be the same!")

            for index, pair in enumerate(zip(rxs, txs)):
                rx, tx = pair
                if isinstance(rx, str):
                    rxs[index] = None
                if isinstance(tx, str):
                    txs[index] = None

        elif isinstance(rxs, RX) and isinstance(txs, TX):
            rxs = [rxs]
            txs = [txs]

        elif isinstance(rxs, str) and isinstance(txs, TX):
            rxs = [None]
            txs = [txs]

        elif isinstance(rxs, RX) and isinstance(txs, str):
            rxs = [rxs]
            txs = [None]

        else:
            raise ValueError(
                "Valid formats for link creation are\n"
                "- rxs = RX obj, txs = TX obj\n"
                "- rxs = list[RX objs], txs = list[TX objs]; Both the lists must equal in length\n"
                "- Either rxs/txs = 'Unknown', txs/rxs = TX/RX obj\n"
            )

        new_links = QueryList()

        for rx, tx in zip(rxs, txs):
            LinkManager.last_link_number += 1
            link_name = f"{LinkManager.link_name_prefix}{LinkManager.last_link_number}"

            try:
                new_links.append(Link(rx, tx, link_name))
            except Exception as e:
                # IF creation fails, decrement by 1 since we didn't create a link
                LinkManager.last_link_number -= 1
                raise e

        LinkManager.links.update({link.name: link for link in new_links})

        return new_links

    @staticmethod
    def delete_links(links_to_delete: Optional[UnionLinkListLink] = None):
        """
        Delete links that were created previously

        Args:
            links_to_delete: **(Optional)** Link objects to delete.
                .. NOTE::If no link objects are provided, all available links are deleted.
        """
        if links_to_delete is None:
            links_to_delete = [link for link in LinkManager.links.values()]

        if isinstance(links_to_delete, Link):
            links_to_delete = [links_to_delete]

        for link in links_to_delete:
            name = link.name
            LinkManager.links[name].invalidate()
            del LinkManager.links[name]

        # If there are no links left, reset the link numbering
        if len(LinkManager.links) == 0:
            LinkManager.last_link_number = -1


class LinkGroupManager:
    link_groups: ClassVar[Dict[str, LinkGroup]] = dict()
    last_link_group_number: ClassVar[int] = -1
    link_group_name_prefix: ClassVar[str] = "LinkGroup_"

    @staticmethod
    def all_link_groups() -> QueryList[LinkGroup]:
        """
        Get all :py:class:`~LinkGroup` object(s)

        Returns:
            List of link groups(s)
        """
        return QueryList(LinkGroupManager.link_groups.values())

    @staticmethod
    def create_link_groups(descriptions: Union[str, List[str]]) -> QueryList[LinkGroup]:
        """
        Create a link group for with description

        Args:
            descriptions: Description(s) for the link group(s) to create.

        Returns:
            Newly created link groups.

        """
        if isinstance(descriptions, str):
            descriptions = [descriptions]

        new_link_groups = QueryList()

        for description in descriptions:
            LinkGroupManager.last_link_group_number += 1
            group_name = f"{LinkGroupManager.link_group_name_prefix}{LinkGroupManager.last_link_group_number}"

            try:
                new_group = LinkGroup(group_name, description, dict())
            except Exception as e:
                LinkGroupManager.last_link_group_number -= 1
                raise e

            new_link_groups.append(new_group)

        LinkGroupManager.link_groups.update({group.name: group for group in new_link_groups})

        return new_link_groups

    @staticmethod
    def delete_link_groups(
        link_groups: UnionLinkGroupListLinkGroup, *, delete_links_in_group: bool = False
    ):
        """
        Delete link group(s)

        Args:
            link_groups: The link groups to delete

            delete_links_in_group: If set to ``True`` the links within each link group
                are deleted as well. Default behavior is to disassociate the link from the
                link group and not delete the link itself.

        Returns:

        """
        if isinstance(link_groups, LinkGroup):
            link_groups = [link_groups]

        links_to_delete = list()

        for group in link_groups:
            if delete_links_in_group:
                links_to_delete.extend(group.links)

            group_name = group.name
            # This will set the link_group field in the links to None
            group.invalidate()
            del LinkGroupManager.link_groups[group_name]

        # If there are no link groups left, reset the group numbering
        if len(LinkGroupManager.link_groups) == 0:
            LinkGroupManager.last_link_group_number = -1

        LinkManager.delete_links(links_to_delete)
