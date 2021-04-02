# +
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
# -

"""
basic_detect.py

Description
-----------
This demo shows how to do three things:
1) Connect to a Versal target device via ChipScope Server (cs_server)
   and Hardware Server (hw_server)
2) Program a Versal target device using a design PDI file (optional)
3) Detect any and all fabric debug cores

Requirements
------------
The following is required to run this demo:
1) Local or remote access to a Versal device
2) 2020.1 cs_server and hw_server applications
3) Python 3.7 environment (i.e., Anaconda from
   https://www.anaconda.com/distribution/)
4) A clone of the chipscopy git enterprise repository:
   - https://gitenterprise.xilinx.com/chipscope/chipscopy
"""

# +
import os
from chipscopy import create_session, report_versions
from chipscopy import get_examples_dir_or_die

# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")
EXAMPLES_DIR = get_examples_dir_or_die()
PROGRAMMING_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
PROBES_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.ltx"
# -

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# +
# Use the first available device and setup its debug cores
versal_device = session.devices[0]

print(f"Programming {PROGRAMMING_FILE}...")
versal_device.program(PROGRAMMING_FILE)

print(f"Discovering debug cores...")
versal_device.discover_and_setup_cores(ltx_file=PROBES_FILE)

# +
ila_count = len(versal_device.ila_cores)
print(f"\tFound {ila_count} ILA cores in design")

vio_count = len(versal_device.vio_cores)
print(f"\tFound {vio_count} VIO cores in design")
