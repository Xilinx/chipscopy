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


import pytest
import os
import re
from pathlib import Path
from chipscopy import delete_session

import chipscopy
from tests.utils import create_session_and_setup_core, LocalBoard
from chipscopy import create_session, Session, Device, QueryList, PCIe
import colorama

if "PYCHARM_HOSTED" not in os.environ:
    colorama.init(convert=True)


bram_address = 0x80000000
# data_file = "data_gen3x8_testerr.txt"

# Specify locations of cs_server below.  hw_server is specified by the board or board farm
# spec
CS_URL = os.getenv("CS_SERVER_URL", "localhost:3042")


DESIGN_DIR = f"spoof/"
PDI_FILE = Path(f"{DESIGN_DIR}/pcie_spoof_prod3.pdi")
LTX_FILE = Path(f"{DESIGN_DIR}/pcie_spoof_prod.ltx")


@pytest.mark.board_needed
@pytest.mark.parametrize("board", [pytest.param("tenzing")], indirect=True)
def test_pcie_spoof(board):
    board_for_test, board_obj = board

    # This will configure the device and apply the LTX to find cores
    session = create_session(
        cs_server_url=f"TCP:{CS_URL}", hw_server_url=f"TCP:{board_obj.hw_server.url}"
    )

    print(f"hw_server {session.hw_server.url} info:")
    print(session.hw_server.version_info)
    print()
    print(f"cs_server {session.cs_server.url} info:")
    print(session.cs_server.version_info)
    print("\n")

    device = session.devices.at(index=0)
    device.program(str(PDI_FILE.resolve()))
    device.discover_and_setup_cores(ltx_file=str(LTX_FILE.resolve()))

    # How many PCIe cores did we find?
    pcie_count = len(device.pcie_cores)
    print(f"\nFound {pcie_count} PCIe cores in design")

    if pcie_count == 0:
        print("No PCIe core found! Exiting...")
        exit()

    pcie_cores: QueryList = device.pcie_cores
    for index, pcie_core in enumerate(pcie_cores):
        print(f"    PCIe Core #{index}: NAME={pcie_core.name}, UUID={pcie_core.uuid}")

    pcie: PCIe = pcie_cores[0]
    pcie.reset_core()
    pcie.refresh()

    data_files = []

    # if data_file variable specified, only use that file, otherwise run through all of them
    if "data_file" in globals():
        data_files.append(Path(DESIGN_DIR).joinpath(data_file))
    else:
        for file in Path(DESIGN_DIR).iterdir():
            if file.suffix.lower() == ".txt":
                data_files.append(file)

    for d in data_files:
        print(f"Testing with {d.name}")
        mem_data = []
        next_file = 0
        with open(d) as f:
            for line in f:
                if line != "":
                    try:
                        mem_data.append(int(line.strip(), 0))
                    except Exception as e:
                        print(f"Parse error with {d} : {line} not an int!")
                        next_file = 1
                        break

        if next_file:
            continue

        # Push the spoofed PCIe data into the design via the BRAM controller
        try:
            device.memory_write(bram_address, mem_data)
        except Exception as e:
            print(f"Problem writing mem data: {e}")
            exit()

        pcie.refresh()
        pcie.reset_core()
        print(pcie)

        props = pcie.get_property([])
        s = ""

        for e in sorted(props.keys()):
            s += f"{e} : {props[e]}\n"
        print(s)

        for s in props["state.trace"]:
            print(s)

        plt = pcie.get_plt()
        plt.title(f"PCIe LTSSM Graph: {d.name}")
        plt.show()

    delete_session(session)
