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

import sys
import json
import time
from typing import Set
from pathlib import Path
from colorama import Fore
from collections import defaultdict

import pytest
from pyboardbarn import set_log_file_directory
from pyboardbarn.barn_manager import BarnManager

from tests.utils import LocalBoard, BoardRequest


arrow = f"{Fore.GREEN}->{Fore.RESET}"

barn_manager: BarnManager = None
local_boards = dict()
uuid_for_board = dict()
unavailable_boards = set()


@pytest.fixture(name="board")
def get_board(request):
    board_request_obj = request.param

    if board_request_obj in unavailable_boards:
        pytest.skip(f"Couldn't acquire requested board ({board_request_obj})...")

    if board_request_obj.name in local_boards:
        yield board_request_obj, local_boards[board_request_obj.name]

    else:
        try:
            board = barn_manager.rented_boards[uuid_for_board[board_request_obj]]
        except KeyError:
            for _, board_obj in barn_manager.rented_boards.items():
                # NOTE - AFAIK the board names on the boardfarm are only separated using '-'
                split_data = board_obj.name.split("-")
                if board_request_obj.name in split_data:
                    board = board_obj
                    break
            else:
                raise RuntimeError(
                    f"Suitable board object for '{board_request_obj.name}' was not found!"
                )

        hw_server_path = None
        if request.config.getoption("--hw_server_path") != "":
            hw_server_path = request.config.getoption("--hw_server_path")

        board.start_hw_server(path=hw_server_path)

        yield board_request_obj, board

        board.stop_hw_server()
        # Power cycle the board to clean the slate for the next test
        board.power_cycle()


def pytest_addoption(parser):
    parser.addoption(
        "--local-boards",
        action="store_true",
        default=False,
        help="Read from the local_board.json file to get boards locally available for tests",
    )
    parser.addoption(
        "--local-boards-only",
        action="store_true",
        default=False,
        help="Only use local boards. Skip tests that require boards from the boardfarm.",
    )
    parser.addoption(
        "--hw_server_path",
        default="",
        help="Path to hw_server. Used when starting hw_server on boards from board farm. "
        "This has no effect on local boards.",
    )


@pytest.mark.trylast
def pytest_collection_modifyitems(config, items):

    # Scan through all the collected tests and get the boards needed to run them
    boards_needed: Set[BoardRequest] = set()
    tests_for_board = defaultdict(set)

    for item in items:
        markers = {marker.name for marker in item.own_markers}
        if "board_needed" not in markers or "skip" in markers:
            continue

        for marker in item.own_markers:
            # We are interested only in the parameterize argument
            if marker.name != "parametrize" or marker.args[0] != "board":
                continue

            for param_set in marker.args[1]:
                board_request = param_set.values[0]
                boards_needed.add(board_request)
                tests_for_board[board_request.name].add(item)

    print()

    boards_needed_from_boardfarm = boards_needed

    if len(boards_needed) > 0:
        # The user might have access to certain boards locally and might want to use them for
        # testing, instead of getting the boards from the boardfarm.
        # The "local_boards.json" file is used to get the local board information, which should
        # be present in the same folder as this (i.e. conftest.py) file.
        # In order to read from the file, we expect
        #  - the Path to be valid and the Path to point to a file
        #  - the "--local-boards" option to be specified while starting pytest

        if config.getoption("--local-boards") or config.getoption("--local-boards-only"):
            local_boards_path = Path(__file__).parent.joinpath("local_boards.json")

            if local_boards_path.exists() and local_boards_path.is_file():
                with local_boards_path.open("r") as json_file:
                    file_data = json.load(json_file)

                locally_available = set()
                local_boards_from_file = file_data.keys()

                boards_needed_from_boardfarm = set()

                for board_req_obj in boards_needed:
                    if board_req_obj.name in local_boards_from_file:
                        locally_available.add(board_req_obj)
                        local_boards[board_req_obj.name] = LocalBoard(
                            name=board_req_obj.name, hw_server_url=file_data[board_req_obj.name]
                        )

                    else:
                        boards_needed_from_boardfarm.add(board_req_obj)

                if len(locally_available) > 0:
                    print(
                        f"{arrow} {Fore.BLUE}Local board(s) provided{Fore.RESET} - "
                        f"{list(local_boards.keys())}."
                    )
                    print(
                        f"{arrow} {Fore.YELLOW}NOTE{Fore.RESET} - "
                        f"The test runner will not be able to automatically "
                        f"power cycle local boards + restart hw_server between test runs."
                    )
            else:
                print(f"{arrow} {Fore.RED}ERROR{Fore.RESET} - Did not find local_boards.json file!")

        # If all boards were provided locally, no need to go the boardfarm.
        if len(boards_needed_from_boardfarm) > 0:
            if config.getoption("--local-boards-only"):
                unavailable_boards.update(boards_needed_from_boardfarm)
                print(
                    f"{arrow} {Fore.YELLOW}NOTE{Fore.RESET} - Skipping barn manager creation, "
                    f"since user has specified to only use local boards."
                )

            else:
                print(f"{arrow} {Fore.BLUE}Creating BarnManager{Fore.BLUE}...")

                global barn_manager

                # Logs are stored in the "logs" folder at the same level as this file.
                # This directory is created if it doesn't exists.
                log_directory = Path(__file__).parent.joinpath("logs")
                if not log_directory.exists():
                    log_directory.mkdir()

                # If it exists, its contents are cleared out before starting the test run
                else:
                    for file in log_directory.iterdir():
                        file.unlink()

                set_log_file_directory(log_directory)

                barn_manager = BarnManager()

                print(f"{arrow} {Fore.BLUE}Board(s) required by tests{Fore.RESET}")
                for board in boards_needed_from_boardfarm:
                    print(f"\t{board}")

                print(
                    f"{arrow} {Fore.BLUE}Trying to acquire board(s) from boardfarm{Fore.RESET}..."
                )

                # Get the boards from the barn manager.
                # Store unavailable board names so that the "board" fixture can skip those tests
                for board_request_obj in boards_needed_from_boardfarm:
                    try:
                        extra_args = {}
                        if board_request_obj.exclude is not None:
                            extra_args["exclude"] = board_request_obj.exclude

                        new_board = barn_manager.request_board(board_request_obj.name, **extra_args)

                        uuid_for_board[board_request_obj] = str(new_board.unique_id)
                    except Exception:
                        unavailable_boards.add(board_request_obj)

                if len(barn_manager.rented_boards) > 0:
                    print(
                        f"{arrow} {Fore.CYAN}Acquired{Fore.RESET} - "
                        f"{[board.name for board in barn_manager.rented_boards.values()]}"
                    )

                    if len(unavailable_boards) > 0:
                        print(
                            f"{arrow} {Fore.MAGENTA}Board(s) {unavailable_boards} couldn't "
                            f"be acquired; corresponding tests will be skipped{Fore.RESET}..."
                        )
                else:
                    print(
                        f"{arrow} {Fore.MAGENTA}No board(s) could be acquired; "
                        f"corresponding tests will be skipped{Fore.RESET}..."
                    )


@pytest.mark.trylast
def pytest_unconfigure():
    print()

    global barn_manager

    if barn_manager is not None:
        print_released_msg = True if len(barn_manager.rented_boards) > 0 else False

        barn_manager.end_session()
        del barn_manager

        if print_released_msg:
            print(f"{arrow} {Fore.CYAN}Released all boards back to the barn{Fore.RESET}")

    # NOTE - This is not neat, I know, but for some reason the pytest session doesn't
    #  release control after the testing is done
    sys.exit(0)
