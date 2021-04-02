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
from chipscopy.api.ibert import create_links, delete_links, get_all_links
from chipscopy.api.ibert.aliases import PATTERN, RX_LOOPBACK
from chipscopy.api.ibert.link.manager import LinkManager


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

    one_link = one(create_links(rxs=ch_0.rx, txs=ch_0.tx))
    print(f"Created new link '{one_link}'")
    assert len(get_all_links()) == 1

    assert one_link.rx == ch_0.rx
    assert one_link.tx == ch_0.tx
    assert one_link.name == f"{LinkManager.link_name_prefix}{LinkManager.last_link_number}"
    assert one_link.link_group is None
    assert one_link.handle == f"{ch_0.tx.handle}-->{ch_0.rx.handle}"

    three_links = create_links(rxs=[ch_1.rx, ch_2.rx, ch_3.rx], txs=[ch_1.tx, ch_2.tx, ch_3.tx])
    print(f"Created new links {three_links}")
    assert len(get_all_links()) == 4

    delete_links([one_link, *three_links])
    assert len(get_all_links()) == 0
    print("Deleted all links")

    delete_session(session)


@pytest.mark.board_needed
@pytest.mark.parametrize("board", [pytest.param(BoardRequest("vck190[S80-prod]"))], indirect=True)
def test_property_modification(board):
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

    for link in four_links:
        print(f"Setting both patterns to 'PRBS 7' + Loopback to 'Near-End PCS' for {link}")
        props = {
            link.rx.property_for_alias[PATTERN]: "PRBS 7",
            link.rx.property_for_alias[RX_LOOPBACK]: "Near-End PCS",
        }

        link.rx.property.set(**props)
        link.rx.property.commit(list(props.keys()))

        props = {link.rx.property_for_alias[PATTERN]: "PRBS 7"}
        link.tx.property.set(**props)
        link.tx.property.commit(list(props.keys()))

        # Without PLL lock, the link will most likely not lock even if TX and RX patterns are same
        if link.rx.pll.locked and link.tx.pll.locked:
            print(f"RX and TX PLLs are locked for {link}. Checking for link lock...")
            assert link.status != "No link"
            print(f"{link} is linked as expected")
        else:
            print(f"RX and/or TX PLL are NOT locked for {link}. Skipping link lock check...")

        link.refresh()
        link.generate_report()

    assert len(get_all_links()) == 4

    delete_links(four_links)
    assert len(get_all_links()) == 0
    print("Deleted all links")

    delete_session(session)
