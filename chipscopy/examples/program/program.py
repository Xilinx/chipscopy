# ### License
# Copyright (C) 2021-2022, Xilinx, Inc.
# <br>
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.
# <p>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# <p>
# You may obtain a copy of the License at <a href="http://www.apache.org/licenses/LICENSE-2.0"?>http://www.apache.org/licenses/LICENSE-2.0</a><br><br>
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# # ChipScoPy Device Programming Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# ## Description
# This example demonstrates how to program a device using the ChipScoPy Python API.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2024.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2024.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - Paths to server(s) and files are set correctly

import os
from chipscopy import get_design_files
from chipscopy import create_session, report_versions, delete_session

# +
# Make sure to start the hw_server prior to running.
# Specify location of the running hw_server below.
# The default is localhost - but can be other locations on the network.
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")

# The get_design_files() function tries to find the programming and probes
# files for an included example design.
PROGRAMMING_FILE = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced").programming_file

print(f"HW_URL: {HW_URL}")
print(f"PROGRAMMING_FILE: {PROGRAMMING_FILE}")
# -

# ## 2 - Create a session and connect to the hw_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout
#
# *NOTE*: No cs_server is required for this example.

session = create_session(hw_server_url=HW_URL)
report_versions(session)

# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
device.program(PROGRAMMING_FILE)

## When done with testing, close the connection
delete_session(session)
