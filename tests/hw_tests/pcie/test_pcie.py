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

from tests.utils import BoardRequest, create_session_and_setup_core
from chipscopy import delete_session
from pathlib import Path


@pytest.mark.skip
@pytest.mark.board_needed
@pytest.mark.parametrize("board", [pytest.param(BoardRequest("tenzing"))], indirect=True)
def test_pcie_creation(board):
    board_request_obj, board_obj = board

    # TODO - Change path to the design
    session = create_session_and_setup_core(
        hw_server_url=board_obj.hw_server.url,
        pdi_dir_relative_to_designs=["vck190", "production", "2.0", "GTY", "all_quads_10G"],
    )
    assert len(session.devices) == 1

    versal_device = session.devices.at(index=0)
    pcies = versal_device.pcie_cores
    assert len(pcies) == 1

    mydir = Path(__file__)
    designs_directory = mydir.parent.parent.parent.joinpath("chipscopy", "examples", "designs")
    target = designs_directory.joinpath("tenzing", "pcie_spoof", "data_gen3x8.txt")
    bram_address = 0xA4000000

    mem_data = []
    next_file = 0
    with open(target) as f:
        for line in f:
            if line != "":
                try:
                    mem_data.append(int(line.strip(), 0))
                except Exception as e:
                    print(f"Parse error with {d} : {line} not an int!")
                    next_file = 1
                    break
    assert next_file == 0

    # Push the spoofed PCIe data into the design via the BRAM controller
    try:
        versal_device.memory_write(bram_address, mem_data)
    except Exception as e:
        print(f"Problem writing mem data: {e}")
        exit(-1)

    pcies[0].refresh()

    props = pcies[0].get_property([])
    # Make sure core is detected as correct type, has correct PCIe link_info,
    # and the last state visited is L0
    assert props["core_type"] == 4
    assert props["link_info"] == "Gen3x8"
    assert props["state.l0"] == 2
    delete_session(session)
