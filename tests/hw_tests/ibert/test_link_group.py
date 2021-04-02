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
from more_itertools import one

from tests.utils import BoardRequest, create_session_and_setup_core
from chipscopy import delete_session
from chipscopy.api import CoreType
from chipscopy.api.ibert import (
    create_links,
    get_all_links,
    create_link_groups,
    delete_link_groups,
    get_all_link_groups,
)


@pytest.mark.board_needed
@pytest.mark.parametrize("board", [pytest.param(BoardRequest("vck190[S80-prod]"))], indirect=True)
def test_create_and_delete(board):
    board_request_obj, board_obj = board

    session = create_session_and_setup_core(
        core_to_setup=CoreType.IBERT,
        hw_server_url=board_obj.hw_server.url,
        pdi_dir_relative_to_designs=["vck190", "production", "2.0", "GTY", "all_quads_10G"],
    )

    ibert_0 = session.devices.at(index=0).ibert_cores.at(index=0)

    quad_204 = one(ibert_0.gt_groups.filter_by(name="Quad_204"))
    assert quad_204.name == "Quad_204"

    ch_0 = one(quad_204.gts.filter_by(name="CH_0"))
    assert ch_0.name == "CH_0"
    ch_1 = one(quad_204.gts.filter_by(name="CH_1"))
    assert ch_1.name == "CH_1"
    ch_2 = one(quad_204.gts.filter_by(name="CH_2"))
    assert ch_2.name == "CH_2"
    ch_3 = one(quad_204.gts.filter_by(name="CH_3"))
    assert ch_3.name == "CH_3"

    four_links = create_links(
        rxs=[ch_0.rx, ch_1.rx, ch_2.rx, ch_3.rx], txs=[ch_0.tx, ch_1.tx, ch_2.tx, ch_3.tx]
    )
    print(f"Created new links {four_links}")

    print(
        "--> Create a link group and add one link to it. Test delete group without deleting the link"
    )

    link_group_0 = one(create_link_groups("This is a test link group"))
    link_group_0.add(four_links[0])

    assert one(link_group_0.links).name == four_links[0].name
    assert one(link_group_0.links.filter_by(name="Link_0")).name == four_links[0].name

    assert len(get_all_link_groups()) == 1
    assert one(get_all_link_groups().filter_by(name="LinkGroup_0")).name == link_group_0.name

    print(f"Created {link_group_0}")

    delete_link_groups(link_group_0)

    assert len(get_all_links()) == 4
    assert len(get_all_link_groups()) == 0

    assert four_links[0].name == "Link_0"
    print("Link group deleted. As expected, links are still alive")

    print("--> Create a link group and add 4 links to it. Test delete group with link deletion")

    link_group_1 = one(create_link_groups("This is a test link group"))
    link_group_1.add(four_links)

    assert one(link_group_1.links.filter_by(name="Link_0")).name == four_links[0].name
    assert one(link_group_1.links.filter_by(name="Link_1")).name == four_links[1].name
    assert one(link_group_1.links.filter_by(name="Link_2")).name == four_links[2].name
    assert one(link_group_1.links.filter_by(name="Link_3")).name == four_links[3].name

    assert len(get_all_link_groups()) == 1
    assert one(get_all_link_groups().filter_by(name="LinkGroup_0")).name == link_group_1.name

    print(f"Created {link_group_1}")

    delete_link_groups(link_group_1, delete_links_in_group=True)

    assert len(get_all_links()) == 0
    assert len(get_all_link_groups()) == 0

    assert {"", "", "", ""} == {link.name for link in four_links}
    print("Link group deleted along with the links")

    delete_session(session)
