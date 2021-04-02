#   Copyright (c) 2020, Xilinx, Inc.
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from pathlib import Path
from typing import Optional, Tuple, List, Set, Union
from dataclasses import dataclass, InitVar

from chipscopy import create_session
from chipscopy.api import CoreType


_last_hash_number: int = -1
_hash_for_board_request_objs = dict()


@dataclass(frozen=True)
class BoardRequest:
    name: str
    exclude: Union[str, List[str], Set[str]] = None

    def __hash__(self):
        generated_id = f"{self.name};"
        if self.exclude is not None:
            if isinstance(self.exclude, str):
                generated_id += f"EXCLUDE-{self.exclude}"
            elif isinstance(self.exclude, list) or isinstance(self.exclude, set):
                generated_id += f"EXCLUDE-{','.join(sorted(self.exclude))}"
            else:
                raise RuntimeError("Dont know how to compute hash for board request object!")

        if generated_id not in _hash_for_board_request_objs:
            global _last_hash_number
            _last_hash_number += 1
            _hash_for_board_request_objs[generated_id] = _last_hash_number

        return _hash_for_board_request_objs[generated_id]


def get_pdi_and_ltx(pdi_dir_relative_to_designs: List[str]) -> Tuple[Path, Optional[Path]]:
    ltx = None
    pdi = None

    designs_directory = Path(__file__).parent.parent.joinpath("chipscopy", "examples", "designs")
    target_folder = designs_directory.joinpath(*pdi_dir_relative_to_designs)

    if not target_folder.is_dir():
        raise ValueError(f"Invalid directory for searching PDI and LTX - {target_folder.resolve()}")

    for file in target_folder.iterdir():
        if file.suffix.lower() == ".ltx":
            ltx = file
        elif file.suffix.lower() == ".pdi":
            pdi = file

    return pdi, ltx


def create_session_and_setup_core(
    pdi_dir_relative_to_designs: List[str],
    hw_server_url: str,
    cs_server_url: str = "localhost:3042",
    *,
    core_to_setup: Union[CoreType, List[CoreType]] = None,
):
    session = create_session(
        cs_server_url=f"TCP:{cs_server_url}", hw_server_url=f"TCP:{hw_server_url}"
    )

    # Set any params as needed
    # params_to_set={"IBERT.Versal.GTY.enable_initialization_check": False},
    # session.set_params(params_to_set)

    # Use the first available device and setup its debug cores
    device = session.devices.at(index=0)

    pdi, ltx = get_pdi_and_ltx(pdi_dir_relative_to_designs)
    device.program(str(pdi.resolve()))

    if core_to_setup:
        if not isinstance(core_to_setup, list):
            core_to_setup = [core_to_setup]
        kwargs_for_setup = dict(
            ila_scan=False,
            vio_scan=False,
            noc_scan=False,
            ddr_scan=False,
            pcie_scan=False,
            ibert_scan=False,
            ltx_file=ltx,
        )
        for core in core_to_setup:
            if core == CoreType.AXIS_ILA:
                kwargs_for_setup["axis_ila"] = True
            if core == CoreType.AXIS_VIO:
                kwargs_for_setup["axis_vio"] = True
            if core == CoreType.NOC_ROOT:
                kwargs_for_setup["noc_scan"] = True
            if core == CoreType.DDR:
                kwargs_for_setup["ddr_scan"] = True
            if core == CoreType.AXIS_PCIE:
                kwargs_for_setup["pcie_scan"] = True
            if core == CoreType.IBERT:
                kwargs_for_setup["ibert_scan"] = True

        device.discover_and_setup_cores(**kwargs_for_setup)
    else:
        # No explicit cores passed in - just do the default
        device.discover_and_setup_cores(ltx_file=ltx)

    return session


@dataclass
class LocalHWServer:
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"{self.host}:{self.port}"


@dataclass
class LocalBoard:
    name: str
    hw_server_url: InitVar[str]
    hw_server: LocalHWServer = None

    def __post_init__(self, hw_server_url: str):
        host, port = hw_server_url.split(":")
        self.hw_server = LocalHWServer(host, int(port))
