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

"""
ChipScoPy report generation. This module keeps stdout reporting in one place for convenience.

All reporting functions that generate stdout reports should be here with a function prefixed with "report_"
hand have a meaningful function name in this file. Other modules should call this one to do the reporting.

Should we want to replace rich in the future, most rich reporting and formatting code is conveniently in one place.

Don't add stdout prints in other locations. This is an API to interact with hardware so we want stdout to
 be optional and well controlled.

The idea is to have the ChipScoPy API generate data that can pipe into other functions.
"""

import datetime
import json
from typing import Optional, Union, List, TYPE_CHECKING

from rich.table import Table
from rich.box import SQUARE as BOX_SQUARE

import chipscopy
from chipscopy.utils.printer import printer
from chipscopy.utils.version import ServerVersionInfo

if TYPE_CHECKING:
    from chipscopy.api.device.device import Device
    from chipscopy.api.session import Session


def _create_server_report(server_version: ServerVersionInfo):
    """Generate a pretty report for the connected server status."""
    report = Table(box=BOX_SQUARE)
    report.add_column("Attribute", justify="right")
    report.add_column("Value", justify="left")
    report.add_row("Status", "Connected")
    report.add_row("Build", f"{server_version.build}")
    report.add_row("Version", f"{server_version.version}")
    report.add_row("Timestamp", f"{server_version.timestamp}")
    if server_version.server_type == "cs_server":
        report.add_row("Package", f"{server_version.package}")
        report.add_row("Artifact type", f"{server_version.artifact}")
    return report


def report_versions(session: Optional["Session"] = None):
    """
    Generate a version report for the servers and ChipScoPy API.

    Args:
        session: Instance of :py:class:`~chipscopy.api.session.Session`

    """
    report = Table(title="ChipScoPy Version Information", box=BOX_SQUARE)
    report.add_column("Entity", justify="right")
    report.add_column("Version", justify="left")

    chipscopy_report = Table(box=BOX_SQUARE)
    chipscopy_report.add_column("Attribute", justify="right")
    chipscopy_report.add_column("Value", justify="left")
    chipscopy_report.add_row("Build", chipscopy.__version__)
    chipscopy_report.add_row(
        "Timestamp",
        datetime.datetime.fromtimestamp(int(chipscopy.__version__.split(".")[-1])).strftime(
            "%b %d %Y-%H:%M:%S"
        ),
    )

    report.add_row("ChipScoPy", chipscopy_report)

    if session and session.hw_server:
        hw_server_version_info = ServerVersionInfo(session.hw_server, "hw_server")
        hw_server_report = _create_server_report(hw_server_version_info)
        report.add_row("", "")
        report.add_row(
            f"hw_server @ {session.hw_server.url}",
            hw_server_report,
        )

    if session and session.cs_server:
        cs_server_version_info = ServerVersionInfo(session.cs_server, "cs_server")
        cs_server_report = _create_server_report(cs_server_version_info)
        report.add_row("", "")
        report.add_row(f"cs_server @ {session.cs_server.url}", cs_server_report)

    printer("\n")
    printer(report)
    printer("\n")


def _create_device_report(device: "Device", title="ChipScoPy Device"):
    report = Table(title=title, box=BOX_SQUARE)
    json_data = device.to_dict()
    report.add_column("Property", justify="left")
    report.add_column("Value", justify="left")
    for key in ["part", "dna", "cable_name", "cable_context", "jtag_index"]:
        report.add_row(key, str(json_data[key]))
    for target_dict in json_data["node_identification"]:
        report.add_row(target_dict["hier_name"], target_dict["context"])
    return report


def report_devices(arg: Optional[Union[List["Device"], "Device", "Session"]] = None):
    from chipscopy.api.device.device import Device
    from chipscopy.api.session import Session

    devices = []
    if isinstance(arg, Session):
        devices = arg.devices
    elif isinstance(arg, Device):
        # convert to a list
        devices = [arg]
    elif isinstance(arg, list):
        devices = arg
    for device in devices:
        sub_report = _create_device_report(device, "Device report")
        printer("\n")
        printer(sub_report)
        printer("\n")


# TODO: Add other report_* functions in this file for report generation.
# TODO: report_devices(dna=123456, ...)
# TODO: report_targets(jtag=true, memory=true, ...)
# TODO: report_cores(...)


def report_hierarchy(obj: Union["IBERT"]):
    """
    Reports the child object hierarchy for any given parent object.

    .. note: Not all objects support reporting hierarchy. No output will be generated for
        such objects.

    Args:
        obj: Parent object

    """
    try:
        printer(obj.__rich_tree__())
    except AttributeError:
        pass
