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
from typing import ClassVar, Dict, List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass

from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.link import RX, TX, Link, LinkGroup
from chipscopy.dm import request
from chipscopy.api.ibert.aliases import PATTERN, RX_STATUS

if TYPE_CHECKING:
    from chipscopy.api.session import Session
    from chipscopy.api.device.device import Device
    from chipscopy.api.ibert import IBERT
    from chipscopy.api.ibert.gt_group import GTGroup
    from chipscopy.api.ibert.gt import GT

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

    def detect_links(
        target: [list[Session | Device | IBERT | GTGroup | GT]] = None,
        done: request.DoneFutureCallback = None,
        progress: request.ProgressFutureCallback = None,
    ) -> QueryList | request.CsFuture:
        """
        Automatically create link(s) for given session :py:class:`~Session` object(s).

        Args:
            :param target: GT or GTGroup or IBERT or Device or Session object(s) to use for link detection
            :param Optional: done: future done callback
            :param Optional: progress: future progress callback

        Returns:
            Newly created :py:class:`Link` object(s)
            CsFuture if progress or done callback provided
                CsFuture.progress returns status of the request any new link found
                    dataclass (info, percent_complete, new_links)
                        WHERE
                        str info is current status
                        int progress is percentage complete
                        list new_link is the newly created Link :py:class:`Link` object a
                CsFuture.result returns status of the request and all new links found
                    dataclass (info, percent_complete, new_links)
                        WHERE
                        str info is current status
                        int progress is percentage complete
                        list new_link is a List of all newly created :py:class:`Link` object(s)

        .. NOTE:: All TXs and RXs that are part of a link already will be ignored.

        """

        # Importing here to avoid circular dependency.
        # Session objects depend on Device objects which depend on IBERT objects.
        # IBERT->link class won't be created if Session and Device Objects are imported on top of module.
        from chipscopy.api.session import Session
        from chipscopy.api.device.device import Device
        from chipscopy.api.ibert import IBERT
        from chipscopy.api.ibert.gt_group import GTGroup
        from chipscopy.api.ibert.gt import GT

        # user provided a session/device/ibert/GTGroup object or list of these objects
        txs = list()
        rxs = list()

        def get_all_tx_rx_from_session(arg: Union[List["Session"], "Session"]):
            if not isinstance(arg, list):
                arg = [arg]
            for session in arg:
                devices = session.devices
                for device in devices:
                    get_all_tx_rx_from_device(device)

        def get_all_tx_rx_from_device(arg: Union[List["Device"], "Device"]):
            if not isinstance(arg, list):
                arg = [arg]
            for device in arg:
                iberts = device.ibert_cores
                for ibert in iberts:
                    get_all_tx_rx_from_ibert_core(ibert)

        def get_all_tx_rx_from_ibert_core(arg: Union[List["IBERT"], "IBERT"]):
            if not isinstance(arg, list):
                arg = [arg]
            for ibert in arg:
                for gtgroup in ibert.gt_groups:
                    get_all_tx_rx_from_gt_group(gtgroup)

        def get_all_tx_rx_from_gt_group(arg: Union[List["GTGroup"], "GTGroup"]):
            if not isinstance(arg, list):
                arg = [arg]
            for gtgroup in arg:
                for gt in gtgroup.gts:
                    get_all_tx_rx_from_gt(gt)

        def get_all_tx_rx_from_gt(arg: Union[List["GT"], "GT"]):
            if not isinstance(arg, list):
                arg = [arg]
            for gt in arg:
                if gt.rx.link is None:
                    txs.append(gt.tx)
                    rxs.append(gt.rx)

        # Sanitize the input
        if not isinstance(target, list):
            target = [target]

        if all(isinstance(x, Session) for x in target) == True:
            get_all_tx_rx_from_session(target)
        elif all(isinstance(x, Device) for x in target) == True:
            get_all_tx_rx_from_device(target)
        elif all(isinstance(x, IBERT) for x in target) == True:
            get_all_tx_rx_from_ibert_core(target)
        elif all(isinstance(x, GTGroup) for x in target) == True:
            get_all_tx_rx_from_gt_group(target)
        elif all(isinstance(x, GT) for x in target) == True:
            get_all_tx_rx_from_gt(target)
        else:
            raise ValueError(
                "Valid formats for link detection are\n"
                "- session = Session obj\n"
                "- sessions = list[Session objs]\n"
                "- device = Device obj\n"
                "- devices = list[Device objs]\n"
                "- ibert = IBERT obj\n"
                "- iberts = list[IBERT objs]\n"
                "- gtgroup = GTGroup obj\n"
                "- gtgroups = list[GTGroup objs]\n"
                "- gt= GT obj\n"
                "- gts = list[GT objs]\n"
            )

        new_links = QueryList()
        detect_future = None

        if not txs or not rxs:
            return

        @dataclass
        class LinkDetectionProgress:
            info: str
            progress: float
            new_link: Link

        def _detect_links(
            txs: [Union[TX, List[TX]]] = None, rxs: [Union[RX, List[RX]]] = None
        ) -> bool or QueryList[Link]:
            nonlocal detect_future
            tx_pattern_map = dict()
            rx_pattern_map = dict()
            percent_complete = 0.0

            error = None

            if detect_future:
                detect_future.set_progress(
                    progress_status=LinkDetectionProgress(
                        info="Starting link detection...", progress=percent_complete, new_link=None
                    )
                )

            for rx in rxs:
                # create a dict with tx_handle and original pattern
                rx_pattern_map.update(
                    {
                        rx.handle: list(
                            rx.property.refresh(rx.property_for_alias[PATTERN]).values()
                        )[0]
                    }
                )

                # set pattern values to "first pattern" = PRBS7 for all rx in list
                props = {rx.property_for_alias[PATTERN]: "PRBS 7"}
                rx.property.set(**props)
                rx.property.commit(list(props.keys()))

            for tx in txs:
                # create a dict with tx_handle and original pattern
                tx_pattern_map.update(
                    {
                        tx.handle: list(
                            tx.property.refresh(tx.property_for_alias[PATTERN]).values()
                        )[0]
                    }
                )

                # set pattern values to "first pattern" = PRBS7 for all tx in list
                props = {tx.property_for_alias[PATTERN]: "PRBS 7"}
                tx.property.set(**props)
                tx.property.commit(list(props.keys()))

            total_rx = len(rxs)
            txs_to_skip = set()
            rxs_processed = set()

            for rx in filter(lambda rx: rx.handle not in rxs_processed, rxs):
                percent_complete = "{:.2f}".format((len(rxs_processed) / total_rx) * 100)
                if detect_future:
                    detect_future.set_progress(
                        progress_status=LinkDetectionProgress(
                            info="Running link detection...",
                            progress=percent_complete,
                            new_link=None,
                        )
                    )

                _, status = rx.property.refresh(rx.property_for_alias[RX_STATUS]).popitem()
                if status != "No link":
                    for tx in filter(lambda tx: tx.handle not in txs_to_skip, txs):
                        props = {tx.property_for_alias[PATTERN]: "PRBS 15"}
                        tx.property.set(**props)
                        tx.property.commit(list(props.keys()))

                        _, status = rx.property.refresh(rx.property_for_alias[RX_STATUS]).popitem()
                        if status == "No link":
                            # link found
                            txs_to_skip.add(tx.handle)
                            LinkManager.last_link_number += 1
                            link_name = (
                                f"{LinkManager.link_name_prefix}{LinkManager.last_link_number}"
                            )

                            try:
                                new_link = Link(rx, tx, link_name)
                                new_links.append(new_link)
                                LinkManager.links.update({link.name: link for link in new_links})
                                if detect_future:
                                    detect_future.set_progress(
                                        progress_status=LinkDetectionProgress(
                                            info="Found new link!",
                                            progress=percent_complete,
                                            new_link=new_link,
                                        )
                                    )
                            except Exception as e:
                                # IF creation fails, decrement by 1 since we didn't create a link
                                LinkManager.last_link_number -= 1
                                error = e
                            break

                rxs_processed.add(rx.handle)
                if error:
                    break

            # reset rx pattern for to original value for all Rxs
            for rx in rxs:
                props = {rx.property_for_alias[PATTERN]: rx_pattern_map[rx.handle]}
                rx.property.set(**props)
                rx.property.commit(list(props.keys()))

            # reset tx pattern for to original value for all Txs
            for tx in txs:
                props = {tx.property_for_alias[PATTERN]: tx_pattern_map[tx.handle]}
                tx.property.set(**props)
                tx.property.commit(list(props.keys()))

            if error:
                if detect_future:
                    detect_future.set_exception(error)
                raise error

            if detect_future:
                detect_future.set_result(
                    result=LinkDetectionProgress(
                        info=f"Auto link detection completed! number of links found = {len(new_links)}",
                        progress=100.0,
                        new_link=new_links,
                    )
                )
            else:
                return new_links

        if progress or done:
            detect_future = request.CsFutureSync(done=done, progress=progress)
            return detect_future.run_worker(_detect_links, txs=txs, rxs=rxs)
        return _detect_links(txs=txs, rxs=rxs)


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
