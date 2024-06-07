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

import json
from typing import Optional
from dataclasses import dataclass, InitVar

from chipscopy.utils import printer
from chipscopy.client import ServerInfo
from chipscopy.vivado_version import __vivado_version__
import re


class ServerVersionInfo:
    """ServerVersionInfo tracks the connected build and version information
    for a connected hw_server or cs_server.
    """

    url: str
    build: str
    version: str
    timestamp: str
    server_type: str
    package: Optional[str] = None
    artifact: Optional[str] = None
    pytcf_version: Optional[str] = None

    def __init__(self, server: ServerInfo, server_type: str):
        self.server_type = server_type
        if server_type == "hw_server":
            xicom_service = server.get_sync_service("Xicom")
            self.url = server.url
            version_dict = xicom_service.get_hw_server_version_info().get()
            self.build = version_dict["build_number"]
            self.version = version_dict["version"]
            self.timestamp = version_dict["timestamp"]
        elif server_type == "cs_server":
            cs_service = server.get_sync_service("ChipScope")
            self.url = server.url
            version_info = cs_service.get_chipscope_server_version_info().args
            if isinstance(version_info, str):
                version_dict = json.loads(version_info)
            elif isinstance(version_info, dict):
                version_dict = version_info
            else:
                raise TypeError(
                    f"Unsupported return type from getChipscopeServerVersionInfo {type(version_info)}"
                )
            self.build = version_dict["build_number"]
            self.version = version_dict["version"]
            self.timestamp = version_dict["timestamp"]
            self.package = version_dict["package_version"]
            self.artifact = version_dict["artifact_type"]
            if "pytcf_version" in version_dict.keys():
                self.pytcf_version = version_dict["pytcf_version"]
        else:
            raise (ValueError("Invalid server_type - must be hw_server or cs_server"))

    def __str__(self):
        retval = (
            f"\tBuild        : {self.build}\n"
            f"\tVersion      : {self.version}\n"
            f"\tTimestamp    : {self.timestamp}\n"
        )

        if self.server_type == "cs_server":
            retval += f"\tPackage      : {self.package}\n"
            retval += f"\tArtifact Type: {self.artifact}"
            if self.pytcf_version:
                retval += f"\n\tPyTCF Version: {self.pytcf_version}"

        return retval

    def __repr__(self):
        retval = (
            f"{type(self).__name__}("
            f"server_type='{self.server_type}', "
            f"version='{self.version}', timestamp='{self.timestamp}', build='{self.build}', "
            f"package='{self.package}', artifact='{self.artifact}'"
            f")"
        )
        return retval


@dataclass
class VersionDetails:
    version: InitVar[str]
    year: int = 0
    major: int = 0
    minor: int = 0

    def __repr__(self):
        return f"{self.year}.{self.major}.{self.minor}"

    def __post_init__(self, version: str):
        # expected string format: YYYY.MM.mm
        #                         |||| - YEAR code (ideally 4 digits but not enforced) must be decimal digits
        #                             . - delimiter (strictly enforced)
        #                              MM - Major code (ideally one or more decimal digits) but KSB breaks this
        #                                . - delimiter if minor is present it must be delimited by a '.'
        #                                 mm - minor (ideally one or more decimal digits but may contain _PATCH(s) as
        #                                      they are applied
        split_data = version.split(".")
        if len(split_data) not in [2, 3]:
            raise TypeError(
                f"invalid version string: {version}, 2 or 3 dot delimited version specifiers expected"
            )

        # YEAR
        self.year = int(split_data[0])

        # Major
        # KSB branch hw_server identifies itself this way: '2023.2_ksb_rc2' special handling to extract the version
        # for this style of version string .* - covers zero non-digit characters following the match group
        match = re.match(
            r"(\d+).*", split_data[1]
        )  # match grouping of digits immediately following the '.' delim
        if match:
            self.major = int(match.groups()[0])
        else:
            raise TypeError(f"invalid version string: {version} - Major decode error")

        # Minor
        if len(split_data) == 3:
            match = re.match(
                r"(\d+).*", split_data[2]
            )  # match grouping of digits immediately following the '.' delim
            if match:
                self.minor = int(match.groups()[0])
            else:
                self.minor = 0
        else:
            self.minor = 0


def version_consistency_check(
    hw_server: ServerInfo, cs_server: Optional[ServerInfo], bypass_version_check: bool
):
    """
    This function will look at the version triplet for ChipScoPy, hw_server and
    cs_server(if applicable), compare their year and major fields i.e. for
    version triplet "2020.2.3", year = 2020 and major = 2 and emit an error if they
    aren't equal.

    The user can chose to bypass this error message and continue using the APIs by
    providing 'bypass_version_check=True' while creating the session.
    """
    mismatch_detected = False
    chipscopy_version = VersionDetails(__vivado_version__)
    hw_server_version = VersionDetails(ServerVersionInfo(hw_server, "hw_server").version)

    # First compare chipscopy and hw_server
    if (
        chipscopy_version.year
        != hw_server_version.year
        # or chipscopy_version.major != hw_server_version.major
    ):
        mismatch_detected = True

    cs_server_version = None
    if cs_server:
        cs_server_version = VersionDetails(ServerVersionInfo(cs_server, "cs_server").version)

        # Next compare cs_server with chipscopy and hw_server
        if (
            chipscopy_version.year != cs_server_version.year
            # or chipscopy_version.major != cs_server_version.major
            or hw_server_version.year != cs_server_version.year
            # or hw_server_version.major != cs_server_version.major
        ):
            mismatch_detected = True

    if mismatch_detected:
        msg = (
            "A client/server version mismatch was detected while connecting!"
            f"\n   ChipScoPy client version - {chipscopy_version}"
            f"\n   hw_server version        - {hw_server_version}"
        )
        if cs_server_version is not None:
            msg += f"\n   cs_server version        - {cs_server_version}"

        if not bypass_version_check:
            msg += (
                "\nResolution - Verify that your ChipScoPy client matches "
                "the hw_server and cs_server(if applicable) and connect again."
                "\nIf you would like to continue using your ChipScoPy client with the "
                "mismatched server(s), please pass "
                'kwarg "bypass_version_check=True" while creating the session.\n'
            )
            raise RuntimeError(msg)

        printer(msg, level="warning")
