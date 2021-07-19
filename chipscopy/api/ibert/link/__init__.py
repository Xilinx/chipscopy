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
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from chipscopy.api.ibert.aliases import (
    RX_BER,
    RX_LINE_RATE,
    RX_PATTERN_CHECKER_ERROR_COUNT,
    RX_RECEIVED_BIT_COUNT,
    RX_STATUS,
)
from chipscopy.api.ibert.link.group import LinkGroup
from chipscopy.api.ibert.rx import RX
from chipscopy.api.ibert.tx import TX
from chipscopy.utils.printer import printer
from rich.box import SQUARE as BOX_SQUARE
from rich.table import Table

if TYPE_CHECKING:  # pragma: no cover
    from chipscopy.api.ibert.eye_scan import EyeScan


@dataclass
class Link:
    """
    Class for interacting with links.
    **Please do not** create an instance of this class directly. Please use the factory method
    :py:func:`~chipscopy.api.ibert.create_links` instead.
    """

    rx: Optional[RX]
    """RX attached to this link"""

    tx: Optional[TX]
    """TX attached to this link"""

    name: str
    """Name of this link"""

    handle: str = field(default="")
    """
        Handle in the format ``tx.handle-->rx.handle``. 
        If TX/RX in unknown, replace ``tx/rx.handle`` with ``UnknownTX/RX``
    """

    filter_by: Dict[str, Any] = field(default_factory=dict)

    link_group: Optional[LinkGroup] = None
    """Link group this link belongs to"""

    # NOTE - Either TX or RX can be unknown, not both!
    #  It is assumed the link manager will perform this check before creating link.

    def __repr__(self) -> str:
        return self.name

    def __post_init__(self):
        # Both RX and TX can't be unknown
        if self.rx is None and self.tx is None:
            raise ValueError("Both RX and TX cant be unknown!")

        if self.tx is not None:
            if self.tx.link is not None:
                raise ValueError(f"{self.tx.handle} is already part of {self.tx.link.name}!")

            self.tx.link = self
            self.handle = self.tx.handle
        else:
            self.handle = "UnknownTX"

        self.handle += "-->"

        if self.rx is not None:
            if self.rx.link is not None:
                raise ValueError(f"{self.rx.handle} is already part of {self.rx.link.name}!")

            self.rx.link = self
            self.handle += self.rx.handle
        else:
            self.handle = "UnknownRX"

        # This is used by the filter_by method in QueryList
        self.filter_by = {
            "rx": self.rx,
            "tx": self.tx,
            "name": self.name,
            "link_group": self.link_group,
        }

    def invalidate(self):
        if self.rx is not None:
            self.rx.link = None
        if self.tx is not None:
            self.tx.link = None
        if self.link_group is not None:
            self.link_group.remove(self)

        self.rx = None
        self.tx = None
        self.name = ""
        self.handle = ""
        self.link_group = None

    @property
    def eye_scan(self) -> Optional["EyeScan"]:
        """
        Get the :py:class:`~chipscopy.api.ibert.eye_scan.EyeScan` object attached to
        the :py:class:`~RX` that is part of the link.

        Returns:
            Eye scan object if available in RX

        """
        return self.rx.eye_scan if self.rx is not None else None

    @property
    def ber(self) -> float:
        """
        Refresh and get the BER value.

        .. note::
            There might be some loss of precision when converting the BER value from str to float.

        Returns:
            BER str value converted to float

        """
        _, prop_value = self.rx.property.refresh(self.rx.property_for_alias[RX_BER]).popitem()
        return float(prop_value)

    @property
    def status(self) -> str:
        """
        Refresh and get the status.

        Returns:
            Link status
        """
        _, prop_value = self.rx.property.refresh(self.rx.property_for_alias[RX_STATUS]).popitem()
        return prop_value

    @property
    def line_rate(self) -> str:
        """
        Refresh and get the line rate of the RX

        Returns:
            Line rate
        """
        _, prop_value = self.rx.property.refresh(self.rx.property_for_alias[RX_LINE_RATE]).popitem()
        return prop_value

    @property
    def bit_count(self):
        """
        Refresh and get the bits received by the RX

        Returns:
            Bit count
        """
        _, prop_value = self.rx.property.refresh(
            self.rx.property_for_alias[RX_RECEIVED_BIT_COUNT]
        ).popitem()
        return prop_value

    @property
    def error_count(self):
        """
        Refresh and get the error counter value

        Returns:
            Error counter value
        """
        _, prop_value = self.rx.property.refresh(
            self.rx.property_for_alias[RX_PATTERN_CHECKER_ERROR_COUNT]
        ).popitem()
        return prop_value

    def generate_report(self):
        """
        Generate a report for this link and send it to the "printer" for printing
        """
        report = Table(title=f'Link "{self.handle}" report', box=BOX_SQUARE)
        report.add_column("Property", justify="right")
        report.add_column("Value", justify="left")

        report.add_row(f"Name", f"{self.name}")
        report.add_row(f"RX", f"{None if self.rx is None else self.rx.handle}")
        report.add_row(f"TX", f"{None if self.tx is None else self.tx.handle}")
        report.add_row(
            f"Link Group", f"{None if self.link_group is None else self.link_group.name}"
        )

        report.add_row("", "")

        if self.rx is not None:
            values = self.rx.property.get(list(self.rx.property_for_alias.values()))
            for alias, prop in self.rx.property_for_alias.items():
                report.add_row(f"RX {alias}", f"{values[prop]}")

        report.add_row("", "")

        if self.tx is not None:
            values = self.tx.property.get(list(self.tx.property_for_alias.values()))
            for alias, prop in self.tx.property_for_alias.items():
                report.add_row(f"TX {alias}", f"{values[prop]}")

        printer("\n")
        printer(report)
        printer("\n")

    def refresh(self):
        """
        Refresh the attributes
        """
        if self.rx is not None:
            self.rx.property.refresh(list(self.rx.property_for_alias.values()))
        if self.tx is not None:
            self.tx.property.refresh(list(self.tx.property_for_alias.values()))
