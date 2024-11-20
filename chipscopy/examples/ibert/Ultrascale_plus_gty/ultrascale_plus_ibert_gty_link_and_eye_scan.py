# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2024, Advanced Micro Devices, Inc.
# <br><br>
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
# # IBERT UltraScale-Plus GTY Example
#

# %% [markdown]
# ### Description
# This example shows how to use IBERT (Integrated Bit Error Ratio Tester) debug core service via ChipScoPy APIs with UltraScale-Plus GTY. The example shows following capabilities:
# - Program a design on VCU128
# - Verify that the expected IBERT quads are instantiated by the design
# - Read/Write register properties from GTY Quad
#
# ### Requirements
# - VCU128 Board
# - Xilinx hw_server 2024.2 installed and running
# - Xilinx cs_server 2024.2 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2024.2 installed
# - Jupyter notebook support installed - Please do so, using the command pip install chipscopy[jupyter]
# - Plotting support installed - Please do so, using the command pip install chipscopy[core-addons]
#

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - Paths to server(s) and files are set correctly

# %%
import os
from more_itertools import one
from itertools import product

from chipscopy import create_session, report_versions, get_design_files, report_hierarchy
from chipscopy.api.ibert.aliases import (
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_VERT_RANGE,
    EYE_SCAN_VERT_STEP,
    EYE_SCAN_HORZ_STEP,
    EYE_SCAN_TARGET_BER,
    PATTERN,
    RX_LOOPBACK,
    TX_PRE_CURSOR,
    TX_POST_CURSOR,
    TX_DIFFERENTIAL_SWING,
    RX_TERMINATION_VOLTAGE,
    RX_COMMON_MODE
)
from chipscopy.api.ibert import  create_links, create_eye_scans


# %%
# Make sure to start the hw_server and cs_server prior to running.
# Specify locations of the running hw_server and cs_server below.
# The default is localhost - but can be other locations on the network.
CS_URL = "TCP:localhost:3042"
HW_URL = "TCP:localhost:3121"


print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files("vcu128/example_design")

BIT_FILE = design_files.programming_file
print(BIT_FILE)

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device = session.devices[0]
print(device)
device.program(BIT_FILE)

# %% [markdown]
# ## 4 - Discover  IBERT cores
#
# Debug core discovery initializes the chipscope server debug cores.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - The first ibert found is used

# %%
device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery done for board")

if len(device.ibert_cores) == 0:
    print("No IBERT core found with board 1! Exiting...")
    exit()
    
for ibert in device.ibert_cores:
    print(f"\n-> {ibert} ({ibert.handle})")

# %% [markdown]
# ## 5 - Discover all GT_Groups available under each IBERT Core

# %%
for ibert in device.ibert_cores:
    for gt_group in ibert.gt_groups:
        print(f"GT Groups available with {ibert.handle} - {[gt_group_obj.name for gt_group_obj in ibert.gt_groups]}")       

# %% [markdown]
# ## 6 - Print Hierarchy for each IBERT Core

# %%
for ibert in device.ibert_cores:
    report_hierarchy(ibert)

# %% [markdown]
# ## 7 - Find all GT and GT_COMMON nodes under each GT Group

# %%
for ibert in device.ibert_cores:
    for child in gt_group.children:
        print(f"name = {child.name}")
        print(f"type = {child.type}")
        print(f"setup_done = {child.setup_done}")
        print(f"children = {child.children}")

# %% [markdown]
# ## 8 - Select a GT Group to work with

# %%
# Use the first available IBERT core from the device
ibert = device.ibert_cores.at(index=0)

if len(ibert.gt_groups) == 0:
    print("No GT Groups available for use! Exiting...")
    exit()

q131 = one(ibert.gt_groups.filter_by(name="Quad_131"))
print(f"q131 ->-> {gt_group.name} | {gt_group.handle} | {gt_group.type}")

# %% [markdown]
# ## 9 - Create links between following TXs and RXs
# - Quad 131 CH0 TX to Quad 131 CH0 RX
# - Quad 131 CH1 TX to Quad 131 CH1 RX
# - Quad 131 CH2 TX to Quad 131 CH2 RX
# - Quad 131 CH3 TX to Quad 131 CH3 RX

# %%
links = create_links(
    txs=[q131.gts[0].tx, q131.gts[1].tx, q131.gts[2].tx, q131.gts[3].tx],
    rxs=[q131.gts[0].rx, q131.gts[1].rx, q131.gts[2].rx, q131.gts[3].rx],
)

# %% [markdown]
# ## 10 - Print the valid values for pattern and loopback, set the pattern for the TXs and RXs to "PRBS 31" and set loopback to "Near-End PMA"
#
# In order to lock the internal pattern checker, TX and RX patterns need to match. We also need to have some kind of loopback, internal/external.
#
# We are assuming that no external cable loopback is present and hence making use of internal loopback.

# %%
for link in links:
    print(f"\n----- {link.name} -----")
    _, tx_pattern_report = link.tx.property.report(link.tx.property_for_alias[PATTERN]).popitem()
    _, rx_pattern_report = link.rx.property.report(link.rx.property_for_alias[PATTERN]).popitem()
    _, rx_loopback_report = link.tx.property.report(
        link.rx.property_for_alias[RX_LOOPBACK]
    ).popitem()

    print(f"--> Valid values for TX pattern - {tx_pattern_report['Valid values']}")
    print(f"--> Valid values for RX pattern - {rx_pattern_report['Valid values']}")
    print(f"--> Valid values for RX loopback - {rx_loopback_report['Valid values']}")

    props = {link.tx.property_for_alias[PATTERN]: "PRBS 31"}
    link.tx.property.set(**props)
    link.tx.property.commit(list(props.keys()))

    props = {
        link.rx.property_for_alias[PATTERN]: "PRBS 31",
        link.rx.property_for_alias[RX_LOOPBACK]: "Near-End PMA",
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))
    print(f"\n--> Set both patterns to 'PRBS 31' & loopback to 'Near-End PMA' for {link}")

    print(f"link.rx.pll.locked = {link.rx.pll.locked} and link.tx.pll.locked = {link.tx.pll.locked}")

    print(f"link.status= {link.status}")
    
    link.generate_report()

# %% [markdown]
# ## 11 - Create eye scan objects for all the links, set the scan params and start the scan
#
# The eye scans will be run in parallel

# %%
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    print (eye_scan.name)

# %% [markdown]
# ## 12 - Start eye scans for all the links

# %%
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 8
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 8
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 13 - Wait for all the eye scans to get done

# %%
for eye_scan in eye_scans:
    eye_scan.wait_till_done()

# %% [markdown]
# ## 14 - View Eye Scan Plot.
#
# This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.2/ibert/scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
for eye_scan in eye_scans:
    eye_scan.generate_report()

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %%
for eye_scan in eye_scans:
    print(f"{eye_scan.name} Open Area: {eye_scan.metric_data.open_area}")
