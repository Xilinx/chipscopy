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


@pytest.mark.board_needed
@pytest.mark.parametrize("board", [pytest.param(BoardRequest("vck190"))], indirect=True)
def test_vio_creation(board):
    board_request_obj, board_obj = board

    session = create_session_and_setup_core(
        hw_server_url=board_obj.hw_server.url,
        pdi_dir_relative_to_designs=["vck190", "es", "1.0", "ks_demo"],
    )

    assert len(session.devices) == 1

    vios = session.devices.at(index=0).vio_cores
    assert len(vios) == 2
    assert vios[0].uuid == "AE7FA8DC717655FD8A4A6DA9BA263B8C"
    assert vios[0].name == "VIO_1"
    assert vios[0].port_names == [
        "probe_in0",
        "probe_out0",
        "probe_out1",
        "probe_out2",
        "probe_out3",
        "probe_out4",
    ]
    assert vios[0].probe_names == [
        "ks_demo_i/slow_cnt_Q",
        "ks_demo_i/slow_cnt_CE",
        "ks_demo_i/slow_cnt_SCLR",
        "ks_demo_i/slow_cnt_UP",
        "ks_demo_i/slow_cnt_LOAD",
        "ks_demo_i/slow_cnt_L",
    ]

    assert vios[1].uuid == "69DDA00971735FFFBD897586326B79A4"
    assert vios[1].name == "VIO_2"
    assert vios[1].port_names == [
        "probe_in0",
        "probe_out0",
        "probe_out1",
        "probe_out2",
        "probe_out3",
        "probe_out4",
    ]
    assert vios[1].probe_names == [
        "ks_demo_i/fast_cnt_Q",
        "ks_demo_i/fast_cnt_CE",
        "ks_demo_i/fast_cnt_SCLR",
        "ks_demo_i/fast_cnt_UP",
        "ks_demo_i/fast_cnt_LOAD",
        "ks_demo_i/fast_cnt_L",
    ]

    # Setting PORT:probe_out4 to 0xdeadc0de. This value should show up on probe:ks_demo_i/slow_cnt_L
    vios[0].write_ports({"probe_out4": 0xDEADC0DE})
    val = vios[0].read_probes()["ks_demo_i/slow_cnt_L"]
    assert val == 0xDEADC0DE

    # Setting ks_demo_i/slow_cnt_L to 0xdeadc0fe. This value should show up on port probe_out4
    vios[0].write_probes({"ks_demo_i/slow_cnt_L": 0xDEADC0FE})
    val = vios[0].read_ports()["probe_out4"]["value"]
    assert val == 0xDEADC0FE

    # Make sure reset changes output value back to default
    vios[0].reset_vio()
    val = vios[0].read_ports()["probe_out4"]["value"]
    assert val == 0

    delete_session(session)
