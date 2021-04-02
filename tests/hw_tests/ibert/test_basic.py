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
from chipscopy.api import CoreType


@pytest.mark.board_needed
@pytest.mark.parametrize("board", [pytest.param(BoardRequest("vck190[S80-prod]"))], indirect=True)
def test_obj_creation(board):
    board_request_obj, board_obj = board

    session = create_session_and_setup_core(
        core_to_setup=CoreType.IBERT,
        hw_server_url=board_obj.hw_server.url,
        pdi_dir_relative_to_designs=["vck190", "production", "2.0", "GTY", "all_quads_10G"],
    )

    iberts = session.devices.at(index=0).ibert_cores
    # For this design we expect only one IBERT
    assert len(iberts) == 1

    # Get the first IBERT.
    ibert_0 = iberts.at(index=0)

    gt_groups = ibert_0.gt_groups

    expected_quads = {
        "Quad_206",
        "Quad_205",
        "Quad_204",
        "Quad_203",
        "Quad_202",
        "Quad_201",
        "Quad_200",
        "Quad_106",
        "Quad_105",
        "Quad_104",
        "Quad_103",
    }
    unexpected_quads = {}

    assert len(gt_groups) == len(expected_quads)

    for quad in expected_quads:
        assert len(gt_groups.filter_by(name=quad)) == 1

    for quad in unexpected_quads:
        assert len(gt_groups.filter_by(name=quad)) == 0

    delete_session(session)
