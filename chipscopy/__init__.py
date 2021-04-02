# Copyright 2021 Xilinx, Inc.
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

import importlib_metadata
import os
import errno
import inspect

# NOTE - Only utility functions that are user visible should be added here to avoid circular imports
from chipscopy.api import CoreType
from chipscopy.api.session import create_session, delete_session
from chipscopy.dm.request import null_callback
from chipscopy.api.report import report_versions, report_devices, report_hierarchy

__author__ = "Xilinx, Inc."
__copyright__ = "Copyright 2020, Xilinx, Inc."
__email__ = "labtools@xilinx.com"
try:
    __version__ = importlib_metadata.version(__package__)
except importlib_metadata.PackageNotFoundError:  # for frozen app support, enter correct version here
    __version__ = "XXXXXXX"


def get_examples_dir_or_die():
    # Examples are provided for Jupyter and Commandline flows. This returns the
    # examples directory in both flows.

    # First priority - locally installed examples with the default directory name
    # Case for most users that installed examples.
    examples_dir = os.path.realpath(os.getcwd() + "./chipscopy-examples")
    if os.path.isdir(examples_dir):
        return examples_dir

    # If we get here, try to find examples in the site-libraries area or wherever
    # we are running chipscopy from. This makes life easier for developers working
    # who want to use examples directly from the chipscopy/examples directory.
    if os.path.isfile(inspect.getfile(inspect.currentframe())):
        # __file__ does not work in jupyter flows
        examples_dir = os.path.realpath(
            os.path.dirname(inspect.getfile(inspect.currentframe())) + "/examples"
        )
    else:
        # Likely in a jupyter environment - examples will likely be in the same dir as the cwd
        examples_dir = os.path.dirname(os.path.realpath(os.getcwd() + "./examples"))
    if not os.path.isdir(examples_dir):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), examples_dir)
    return examples_dir
