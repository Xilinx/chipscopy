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
# # ChipScoPy DDR Reporting Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This demo shows how to print and report DDR calibration status and report detailed information.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 installed and running
# - Xilinx cs_server 2022.1 installed and running
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
import pprint
import os
import json
from chipscopy import create_session, report_versions
from chipscopy import get_design_files

# %%
# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files("vck190/production/chipscopy_ced")

PDI_FILE = design_files.programming_file
LTX_FILE = design_files.probes_file

print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")
print(f"PROGRAMMING_FILE: {PDI_FILE}")
print(f"PROBES_FILE:{LTX_FILE}")

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
# Start of the connection
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
versal_device = session.devices.filter_by(family="versal").get()
versal_device.program(PDI_FILE)

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - The cs_server is initialized and ready for use

# %%
versal_device.discover_and_setup_cores()
print(f"Debug cores setup and ready for use.")

# %% [markdown]
# ## 5 - Show enabled DDRs in the device. Pick one to use

# %%
ddr_list = versal_device.ddrs
for ddr in ddr_list:
    print(ddr, "  Enabled:", ddr.is_enabled)

# Grab the first enabled DDR
for ddr in ddr_list:
    if ddr.is_enabled:
        print("Using Enabled DDR: ", ddr)
        break

# %% [markdown]
# ## 6 - Getting the Calibration Status
#
# There are several methods available to collect memory calibration information.

# %% [markdown]
# ### Method 1 - Calibration PASS/FAIL status

# %%
# Method 1 - Use Status string base API directly
print(ddr, "calibration status:", ddr.get_cal_status())

# %% [markdown]
# ### Method 2 - Calibration from the status property group

# %%
# Use Property Group to get dictionary base of results
props = ddr.ddr_node.get_property_group(["status"])
print(pprint.pformat(props, indent=2))

# %% [markdown]
# ### Method 3 - Detailed calibration status for each stage

# %%
# Use get Cal Stages API directly to also get dictionary results
props = ddr.get_cal_stages()
print(pprint.pformat(sorted(props.items()), indent=2))

# %% [markdown]
# ## 7 - Generate Full DDRMC Report
#
# The report() API call creates a full DDRMC status report to stdout or a file. This report includes memory configuration, margin analysis, calibration, and health status information.

# %%
# Use a single report command to get all latest essential
# Status and decoded data collected as it presents
ddr.report()
# Specify True to argument 1, and name/path to argument 2
# to get the report output generated and saved to a file
ddr.report(True, "test_out.txt")
print("Report Done.\n")

# %% [markdown]
# ## 8 - Dump the complete set of internal properties as json
#
# This demonstrates how to get a Python dictionary of all the low level DDR properties. These can be converted to JSON easily for export to other tools.

# %%
props = ddr.ddr_node.get_property_group([])
json_props = json.dumps(props, indent=4)
print(json_props)
