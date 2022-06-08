# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright 2021 Xilinx, Inc.<br><br>
# Licensed under the Apache License, Version 2.0 (the "License");<br>
# you may not use this file except in compliance with the License.<br><br>
# You may obtain a copy of the License at <a href="http://www.apache.org/licenses/LICENSE-2.0"?>http://www.apache.org/licenses/LICENSE-2.0</a><br><br>
# Unless required by applicable law or agreed to in writing, software<br>
# distributed under the License is distributed on an "AS IS" BASIS,<br>
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.<br>
# See the License for the specific language governing permissions and<br>
# limitations under the License.<br>
# </p>
#

# %% [markdown]
# # ChipScoPy Device Programming Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example demonstrates how to program a device using the ChipScoPy Python API.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2022.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - Paths to server(s) and files are set correctly

# %%
import os
from chipscopy import get_design_files
from chipscopy import create_session, report_versions

# %%
# Make sure to start the hw_server prior to running.
# Specify location of the running hw_server below.
# The default is localhost - but can be other locations on the network.
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# The get_design_files() function tries to find the programming and probes
# files for an included example design.
PROGRAMMING_FILE = get_design_files("vck190/production/chipscopy_ced").programming_file

print(f"HW_URL: {HW_URL}")
print(f"PROGRAMMING_FILE: {PROGRAMMING_FILE}")


# %% [markdown]
# ## 2 - Create a session and connect to the hw_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout
#
# *NOTE*: No cs_server is required for this example.

# %%
session = create_session(hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
device.program(PROGRAMMING_FILE)

