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

from typing import TYPE_CHECKING, ClassVar, Dict, List, Optional, Union

from chipscopy.api.containers import QueryList
from chipscopy.api.ibert.yk_scan import YKScan
from chipscopy.utils import printer

if TYPE_CHECKING:
    from chipscopy.api.ibert.rx import RX


UnionYKScanListYKScan = Union[YKScan, List[YKScan], QueryList[YKScan]]


class YKScanManager:
    """
    Factory class to manage YK scan creation and destruction
    """

    scans: ClassVar[Dict[str, YKScan]] = dict()
    last_scan_number: ClassVar[int] = 0
    scan_name_prefix: ClassVar[str] = "YKScan_"

    @staticmethod
    def all_yk_scans() -> QueryList[YKScan]:
        """
        Get all :py:class:`YKScan` object(s)

        Returns:
            List of YK scan object(s)

        """
        return QueryList(YKScanManager.scans.values())

    @staticmethod
    def create_yk_scans(*, target_objs: Union[RX, List[RX]]) -> QueryList[YKScan]:
        """
        Create an instance of :py:class:`YKScan` and attach it to the ``yk_scan`` attribute
        of the ``target_obj``(s)

        Args:
            target_objs: The object to use for attaching the YK scan instance.
                The object **must** be an instance of ``RX`` class.

        Returns:
            List of YK scan object(s) created

        """
        rxs = target_objs
        if not isinstance(target_objs, list):
            rxs = [target_objs]

        new_yk_scans = QueryList()

        rx_without_support = list()

        for rx in rxs:
            if not hasattr(rx, "yk_scan"):
                rx_without_support.append(rx.name)
                continue

            YKScanManager.last_scan_number += 1
            scan_name = f"{YKScanManager.scan_name_prefix}{YKScanManager.last_scan_number}"

            try:
                new_scan = YKScan(rx=rx, name=scan_name)
            except Exception as e:
                YKScanManager.last_scan_number -= 1
                raise e

            YKScanManager.scans[new_scan.name] = new_scan
            new_yk_scans.append(new_scan)

        if len(rx_without_support) > 0:
            rxs = "\n".join(rx_without_support)
            printer(f"YK scan creation isn't supported for following RX(s)\n{rxs}", level="warning")

        return new_yk_scans

    @staticmethod
    def delete_yk_scans(scans_to_delete: Optional[UnionYKScanListYKScan] = None):
        """
        Delete :py:class:`YKScan` object(s) that were created previously

        Args:
            scans_to_delete: **(Optional)** YK scan object(s) to delete.

        .. warning::
            If no YK scan objects are provided, all available YK scans are deleted.

        """
        if scans_to_delete is None:
            scans_to_delete = [eye_scan for eye_scan in YKScanManager.scans.values()]

        for eye_scan in scans_to_delete:
            name = eye_scan.name
            YKScanManager.scans[name].invalidate()
            del YKScanManager.scans[name]

        # If there are no scans left, reset the scan numbering
        if len(YKScanManager.scans) == 0:
            YKScanManager.last_scan_number = -1
