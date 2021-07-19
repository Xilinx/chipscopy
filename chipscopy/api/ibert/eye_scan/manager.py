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
from chipscopy.api.ibert.link import Link
from chipscopy.api.ibert.eye_scan import EyeScan
from chipscopy.utils import printer

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.rx import RX


UnionEyeScanListEyeScan = Union[EyeScan, List[EyeScan], QueryList[EyeScan]]


class EyeScanManager:
    """
    Factory class to manage eye scan creation and destruction
    """

    scans: ClassVar[Dict[str, EyeScan]] = dict()
    last_scan_number: ClassVar[int] = 0
    scan_name_prefix: ClassVar[str] = "EyeScan_"

    @staticmethod
    def all_eye_scans() -> QueryList[EyeScan]:
        """
        Get all :py:class:`EyeScan` object(s)

        Returns:
            List of eye scan object(s)

        """
        return QueryList(EyeScanManager.scans.values())

    @staticmethod
    def create_eye_scans(*, target_objs: Union[RX, Link, List[RX, Link]]) -> QueryList[EyeScan]:
        """
        Create an instance of :py:class:`EyeScan` and attach it to the ``eye_scan`` attribute
        of the ``target_obj`` (s)

        Args:
            target_objs: The object to use for attaching the eye scan instance.
                The object **must** be an instance of ``RX`` or ``Link`` class.

        Returns:
            List of eye scan object(s) created

        """
        if not isinstance(target_objs, list):
            target_objs = [target_objs]

        rxs = list()

        for obj in target_objs:
            if isinstance(obj, Link):
                if obj.rx is None:
                    raise ValueError(f"Cannot create scan since {obj} does not have an RX!")

                rxs.append(obj.rx)

            else:
                rxs.append(obj)

        new_eye_scans = QueryList()

        rx_without_support = list()

        for rx in rxs:
            if not hasattr(rx, "eye_scan"):
                rx_without_support.append(rx.name)
                continue

            EyeScanManager.last_scan_number += 1
            scan_name = f"{EyeScanManager.scan_name_prefix}{EyeScanManager.last_scan_number}"

            try:
                new_scan = EyeScan(rx=rx, name=scan_name)
            except Exception as e:
                EyeScanManager.last_scan_number -= 1
                raise e

            EyeScanManager.scans[new_scan.name] = new_scan
            new_eye_scans.append(new_scan)

        if len(rx_without_support) > 0:
            rxs = "\n".join(rx_without_support)
            printer(
                f"Eye scan creation isn't supported for following RX(s)\n{rxs}", level="warning"
            )

        return new_eye_scans

    @staticmethod
    def delete_eye_scans(scans_to_delete: Optional[UnionEyeScanListEyeScan] = None):
        """
        Delete :py:class:`EyeScan` object(s) that were created previously

        Args:
            scans_to_delete: **(Optional)** Eye scan object(s) to delete.

        .. warning::
            If no eye scan objects are provided, all available eye scans are deleted.

        """
        if scans_to_delete is None:
            scans_to_delete = [eye_scan for eye_scan in EyeScanManager.scans.values()]

        if isinstance(scans_to_delete, EyeScan):
            scans_to_delete = [scans_to_delete]

        for eye_scan in scans_to_delete:
            name = eye_scan.name
            EyeScanManager.scans[name].invalidate()
            del EyeScanManager.scans[name]

        # If there are no scans left, reset the scan numbering
        if len(EyeScanManager.scans) == 0:
            EyeScanManager.last_scan_number = -1
