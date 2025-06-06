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
from collections import namedtuple
from pathlib import Path

import importlib_metadata
import os
import errno
import inspect

# NOTE - Only utility functions that are user visible should be added here to avoid circular imports
from chipscopy.api import CoreType
from chipscopy.api.session import create_session, delete_session
from chipscopy.dm.request import null_callback
from chipscopy.api.report import report_versions, report_devices, report_hierarchy

__author__ = "Advanced Micro Devices, Inc."
__copyright__ = "Copyright (C) 2022-2024, Advanced Micro Devices, Inc."
__email__ = "support@xilinx.com"
try:
    __version__ = importlib_metadata.version(__package__)
except (
    importlib_metadata.PackageNotFoundError
):  # for frozen app support, enter correct version here
    __version__ = "XXXXXXX"


def get_examples_dir_or_die():
    # Check if the environment variable is set
    env_examples_dir = os.getenv("CHIPSCOPY_EXAMPLES")
    if env_examples_dir and os.path.isdir(env_examples_dir):
        return env_examples_dir

        # Start from the current working directory
    current_dir = os.getcwd()

    while True:
        # Check for 'chipscopy-examples' directory
        examples_dir = os.path.join(current_dir, "chipscopy-examples")
        if os.path.isdir(examples_dir):
            return examples_dir

            # Check for 'examples' directory
        examples_dir = os.path.join(current_dir, "examples")
        if os.path.isdir(examples_dir):
            return examples_dir

            # Move up one directory level
        parent_dir = os.path.dirname(current_dir)

        # If the parent directory is the same as the current directory, we've reached the root
        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    # If we got here, we did not find 'examples' or 'chipscopy-examples'
    # Pre-2024.2 chipscopy delivered examples in the site-packages area, try that as a fallback.
    if os.path.isfile(inspect.getfile(inspect.currentframe())):
        # __file__ does not work in jupyter flows
        examples_dir = os.path.realpath(
            os.path.dirname(inspect.getfile(inspect.currentframe())) + "/examples"
        )
        if os.path.isdir(examples_dir):
            return examples_dir

    error_message = (
        "Could not find the 'examples' or 'chipscopy-examples' directory.\n"
        "Please ensure that one of these directories exists in the current or parent directories.\n"
        "Alternatively, you can set the 'CHIPSCOPY_EXAMPLES' environment variable to the path of the examples directory.\n"
        "Example: export CHIPSCOPY_EXAMPLES=/path/to/your/examples"
    )
    raise FileNotFoundError(errno.ENOENT, error_message)


def _get_design_files_in_dir(p: Path) -> namedtuple:
    ProgrammingFiles = namedtuple("ProgrammingFiles", "programming_file probes_file hwh_file")
    hwh_file = None
    ltx_file = None
    programming_file = None
    if p.is_dir():
        hwh_files = list(p.glob("*.hwh"))
        ltx_files = list(p.glob("*.ltx"))
        pdi_files = list(p.glob("*.pdi"))
        bit_files = list(p.glob("*.bit"))

        if hwh_files:
            hwh_file = str(hwh_files[0])
        if ltx_files:
            ltx_file = str(ltx_files[0])
        if pdi_files:
            programming_file = str(pdi_files[0])
        elif bit_files:
            programming_file = str(bit_files[0])
    return ProgrammingFiles(programming_file, ltx_file, hwh_file)


def get_design_files(board_path: str) -> namedtuple:
    # board_path like "vck190/production/2.0/ks_demo" pointing to a valid board design
    # in one of the repository areas. Must have ltx and bit or pdi files.
    # Prioritized look for designs
    # 1. In current directory deployed by chipscopy-get-examples
    # 2. site-libraries or chipscopy dev area
    # 3. jupyter notebook cwd
    # 4. internal-examples area

    design_dirs = []
    examples_dir = None
    try:
        examples_dir = get_examples_dir_or_die()
    except FileNotFoundError:
        pass

    if examples_dir:
        p = Path(examples_dir)
        p1 = p / "designs" / board_path
        if p1.is_dir():
            design_dirs.append(p1)
        p2 = p / ".." / ".." / "internal-examples" / "designs" / board_path
        if p2.is_dir():
            design_dirs.append(p2)

    files = None
    found_design_files = False
    for design_dir in design_dirs:
        files = _get_design_files_in_dir(design_dir)
        if files.programming_file:
            found_design_files = True
            break
    if not found_design_files:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), board_path)
    return files
