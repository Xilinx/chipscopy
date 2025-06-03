# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2025 Advanced Micro Devices, Inc.<br><br>
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
# # IBERT link and eye scan example between VCK190 (Versal) and VCU128 (US+) boards
#

# %% [markdown]
# ### Description
# This example shows how to use IBERT (Integrated Bit Error Ratio Tester) debug core service via ChipScoPy APIs to create link between two different boards: Versal (VCK190) and  Ultrascale plus (VCU128). 
# The example shows following capabilities:
# - Program a design on the two boards
# - Verify that the expected IBERT quads are instantiated by the design for each of the boards
# - Create links between the two boards and change link settings to get link lock
# - Run and plot eye scans for the links
#
# ### Requirements
# - VCK190 and VCU128 board
# - Xilinx hw_server 2025.1 installed and running
# - Xilinx cs_server 2025.1 installed and running
# - Python 3.9 or greater installed
# - ChipScoPy 2025.1 installed
# - Jupyter notebook support installed - Please do so, using the command pip install chipscopy[jupyter]
# - Plotting support installed - Please do so, using the command pip install chipscopy[core-addons]
#
# ### Setup
# The setup uses hw_server running on two different x86 machines to connect to the two boards over JTAG. A single instance of cs_server running on another host machine communicates with both these hw_servers to provide multi-board support.
#
# ![setup.jpg](./vcu128-vck190-two-hwserver.jpg)

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

from chipscopy import create_session, delete_session, report_versions, report_hierarchy, get_design_files
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
from chipscopy.api.ibert import create_eye_scans, create_links, delete_links

# %%
# Make sure to start the hw_server and cs_server prior to running.
# Specify locations of the running hw_server and cs_server below.
# The default is localhost - but can be other locations on the network.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
# hw_server connected to board_1 (vck190)
HW_URL_1 = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

print(f"HW_URL for VCK190: {HW_URL_1}")

# specify hw and if programming is desired
HW_PLATFORM_1 = os.getenv("HW_PLATFORM_1", "vck190")
PROG_DEVICE_1 = os.getenv("PROG_DEVICE_1", True)

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files(f"{HW_PLATFORM_1}/production/cross_link_debug")
PDI_FILE_1 = design_files.programming_file

print(f"PROGRAMMING_FILE: {PDI_FILE_1}")

# %%
# hw_server connected to board_2 (vcu128)
HW_URL_2 = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

print(f"HW_URL for VCU128: {HW_URL_2}")

# specify hw and if programming is desired
HW_PLATFORM_2 = os.getenv("HW_PLATFORM_2", "vcu128")
PROG_DEVICE_2 = os.getenv("PROG_DEVICE_2", True)

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files(f"{HW_PLATFORM_2}/example_design")

BIT_FILE_2 = design_files.programming_file
print(BIT_FILE_2)

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
session_1 = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL_1)
report_versions(session_1)

# %% [markdown]
# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device_1 = session_1.devices.filter_by(family="versal").get()
if PROG_DEVICE_1:
    device_1.program(PDI_FILE_1)
else:
    print("skipping programming")
print(device_1)

# %% [markdown]
# ## 4 - Discover and setup the IBERT core
#
# Debug core discovery initializes the chipscope server debug cores.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - The first ibert found is used

# %%
device_1.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery done for board 1")

if len(device_1.ibert_cores) == 0:
    print("No IBERT core found with board 1! Exiting...")
    exit()

# Use the first available IBERT core from the device
ibert_0 = device_1.ibert_cores.at(index=0)

if len(ibert_0.gt_groups) == 0:
    print("No GT Groups available for use! Exiting...")
    exit()

print(f"GT Groups available with Board 1 - {[gt_group_obj.name for gt_group_obj in ibert_0.gt_groups]}")

# %% [markdown]
# ## 5 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
session_2 = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL_2)
session = session_2
report_versions(session_2)

# %% [markdown]
# ## 6 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device_2 = session_2.devices.filter_by(family="virtexuplus").get()
if PROG_DEVICE_2:
    device_2.program(BIT_FILE_2)
else:
    print("skipping programming")
print(device_2)

# %% [markdown]
# ## 7 - Discover and setup the IBERT core
#
# Debug core discovery initializes the chipscope server debug cores.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - The first ibert found is used

# %%
device_2.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery done for board 2")

if len(device_2.ibert_cores) == 0:
    print("No IBERT core found with board 1! Exiting...")
    exit()

# Use the first available IBERT core from the device
ibert_2 = device_2.ibert_cores.at(index=1)

if len(ibert_2.gt_groups) == 0:
    print("No GT Groups available for use! Exiting...")
    exit()

print(f"GT Groups available with Board 1 - {[gt_group_obj.name for gt_group_obj in ibert_2.gt_groups]}")

# %% [markdown]
# ## 8 - Print the hierarchy of the IBERT core
#
# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs

# %%
report_hierarchy(ibert_0)

q200_1 = one(ibert_0.gt_groups.filter_by(name="Quad_200"))

# %%
report_hierarchy(ibert_2)

q134_2 = one(ibert_2.gt_groups.filter_by(name="Quad_134"))

# %% [markdown]
# ## 9 - Create links between following TXs and RXs
# - Quad 200 CH0 TX of VCK190 (versal) board to Quad 200 CH0 RX of VCK190 (versal)
# - Quad 134 CH0 TX of VCU128 (US+) board to Quad 134 CH0 RX of VCU128 (US+) board
#
# ![internal-loopback.png](./internal_loopback.png)

# %%
internal_loopback_board1_board2_CH0_links = create_links(
    txs=[q200_1.gts[0].tx, q134_2.gts[0].tx],
    rxs=[q200_1.gts[0].rx, q134_2.gts[0].rx],
 )

print("--> Done creating links for testing intrnal loopback for Versal and US+ GTY")

# %% [markdown]
# ## 10 - Print the valid values for pattern and loopback, set the pattern for the TXs and RXs to "PRBS 31" and set loopback to "Near-End PMA"
#
# In order to lock the internal pattern checker, TX and RX patterns need to match.
#

# %%
for link in internal_loopback_board1_board2_CH0_links:
    print(f"\n----- {link.name} -----")

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

    link.tx.reset()
    link.rx.reset()
    link.rx.reset_ber()

    print(f"link.status= {link.status}")

# %% [markdown]
# ## 11 - Create eye scan objects for all the links, set the scan params and start the scan
#
# The eye scans will be run in parallel

# %%
eye_scans = create_eye_scans(target_objs=[link for link in internal_loopback_board1_board2_CH0_links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 10
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 10
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 12 - Wait for all the eye scans to get done

# %%
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()

# %% [markdown]
# ## 13 - Show Eye Scan report and Eye Scan data

# %%
for eye_scan in eye_scans:
    eye_scan.generate_report()
    print(eye_scan.scan_data.processed)

# %% [markdown]
# ## 14 - View Eye Scan Plot.
#
# This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.2/ibert/scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %% [markdown]
# ## 15 - Get Eye Metric Data

# %%
for eye_scan in eye_scans:
    print(f"{eye_scan.name} Open Area:                                      {eye_scan.metric_data.open_area}")
    print(f"{eye_scan.name} Percentage Open Area:                           {eye_scan.metric_data.open_percentage}")
    print(f"{eye_scan.name} Eye width at zero crossing:                     {eye_scan.metric_data.horizontal_opening}")
    print(f"{eye_scan.name} Percentage horizontal opening at zero crossing: {eye_scan.metric_data.horizontal_percentage}")
    print(f"{eye_scan.name} Eye height at zero crossing:                    {eye_scan.metric_data.vertical_opening}")
    print(f"{eye_scan.name} Percentage vertical opening at zero crossing:   {eye_scan.metric_data.vertical_percentage}")

# %% [markdown]
# ## 16 - Delete the links

# %%
delete_links(internal_loopback_board1_board2_CH0_links)

# %% [markdown]
# ## 17 - Create links between following TXs and RXs
# - Quad 200 CH0 TX of VCK190 (versal) board to Quad 134 CH0 RX of VCU128 (US+) board
# - Quad 134 CH0 TX of VCU128 (US+) board to Quad 200 CH0 RX of VCK190 (versal) board
#
# ![cross_link-loopback.png](./cross_link.png)

# %%
board1_board2_CH0_cross_links = create_links(
    txs=[q200_1.gts[0].tx, q134_2.gts[0].tx],
    rxs=[q134_2.gts[0].rx, q200_1.gts[0].rx],
 )

print("--> Done creating links between Versal GTY CH0 and US+ GTY CH0")

# %% [markdown]
# ## 18 - Print the valid values for pattern and loopback, set the pattern for the TXs and RXs to "PRBS 31" and set loopback to "None"
#
# In order to lock the internal pattern checker, TX and RX patterns need to match.

# %%
for link in board1_board2_CH0_cross_links:
    print(f"\n----- {link.name} -----")

    props = {link.tx.property_for_alias[PATTERN]: "PRBS 31"}
    link.tx.property.set(**props)
    link.tx.property.commit(list(props.keys()))

    props = {
        link.rx.property_for_alias[PATTERN]: "PRBS 31",
        link.rx.property_for_alias[RX_LOOPBACK]: "None",
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))
    print(f"\n--> Set both patterns to 'PRBS 31' & loopback to 'None' for {link}")

    print(f"link.rx.pll.locked = {link.rx.pll.locked} and link.tx.pll.locked = {link.tx.pll.locked}")

    link.tx.reset()
    link.rx.reset()
    link.rx.reset_ber()

    print(f"link.status= {link.status}")

# %% [markdown]
# ## 19 - Create eye scan objects for all the links, set the scan params and start the scan
#
# The eye scans will be run in parallel

# %%
eye_scans = create_eye_scans(target_objs=[link for link in board1_board2_CH0_cross_links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 10
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 10
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 20 - Wait for all the eye scans to get done

# %%
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()

# %% [markdown]
# ## 21 - Show Eye Scan report and Eye Scan data

# %%
for eye_scan in eye_scans:
    eye_scan.generate_report()
    print(eye_scan.scan_data.processed)

# %% [markdown]
# ## 22 - View Eye Scan Plot.
#
# This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.2/ibert/scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %% [markdown]
# ## 23 - Get Eye Metric Data

# %%
for eye_scan in eye_scans:
    print(f"{eye_scan.name} Open Area:                                      {eye_scan.metric_data.open_area}")
    print(f"{eye_scan.name} Percentage Open Area:                           {eye_scan.metric_data.open_percentage}")
    print(f"{eye_scan.name} Eye width at zero crossing:                     {eye_scan.metric_data.horizontal_opening}")
    print(f"{eye_scan.name} Percentage horizontal opening at zero crossing: {eye_scan.metric_data.horizontal_percentage}")
    print(f"{eye_scan.name} Eye height at zero crossing:                    {eye_scan.metric_data.vertical_opening}")
    print(f"{eye_scan.name} Percentage vertical opening at zero crossing:   {eye_scan.metric_data.vertical_percentage}")

# %% [markdown]
# ## 24 - Delete the links

# %%
delete_links(board1_board2_CH0_cross_links)

# %% [markdown]
# ## 25 - Create links between following TXs and RXs
# - Quad 200 CH0 TX of VCK190 (versal) board to Quad 134 CH0 RX of VCU128 (US+) board
# - Quad 200 CH1 TX of VCK190 (versal) board to Quad 134 CH1 RX of VCU128 (US+) board
# - Quad 200 CH2 TX of VCK190 (versal) board to Quad 134 CH2 RX of VCU128 (US+) board
# - Quad 200 CH3 TX of VCK190 (versal) board to Quad 134 CH3 RX of VCU128 (US+) board
# - Quad 134 CH0 TX of VCU128 (US+) board to Quad 200 CH0 RX of VCK190 (versal) board
# - Quad 134 CH1 TX of VCU128 (US+) board to Quad 200 CH1 RX of VCK190 (versal) board
# - Quad 134 CH2 TX of VCU128 (US+) board to Quad 200 CH2 RX of VCK190 (versal) board
# - Quad 134 CH3 TX of VCU128 (US+) board to Quad 200 CH3 RX of VCK190 (versal) board
#
# ![cross_link_all.png](./cross_link_all.png)

# %%
links_board1_tx_board2_rx = create_links(
    txs=[q200_1.gts[0].tx, q200_1.gts[1].tx, q200_1.gts[2].tx, q200_1.gts[3].tx, q134_2.gts[0].tx, q134_2.gts[1].tx, q134_2.gts[2].tx, q134_2.gts[3].tx],
    rxs=[q134_2.gts[0].rx, q134_2.gts[1].rx, q134_2.gts[2].rx, q134_2.gts[3].rx, q200_1.gts[0].rx, q200_1.gts[1].rx, q200_1.gts[2].rx, q200_1.gts[3].rx],
 )

print("--> Done creating links between board 1 tx and board 2 rx")

# %% [markdown]
# ## 26 - Print the valid values for pattern and loopback, set the pattern for the TXs and RXs to "PRBS 31" and set loopback to "None"
#
# In order to lock the internal pattern checker, TX and RX patterns need to match. 

# %%
for link in links_board1_tx_board2_rx:
    print(f"\n----- {link.name} -----")

    props = {link.tx.property_for_alias[PATTERN]: "PRBS 31"}
    link.tx.property.set(**props)
    link.tx.property.commit(list(props.keys()))

    props = {
        link.rx.property_for_alias[PATTERN]: "PRBS 31",
        link.rx.property_for_alias[RX_LOOPBACK]: "None",
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))
    print(f"\n--> Set both patterns to 'PRBS 31' & loopback to 'None' for {link}")

    print(f"link.rx.pll.locked = {link.rx.pll.locked} and link.tx.pll.locked = {link.tx.pll.locked}")

    link.tx.reset()
    link.rx.reset()
    link.rx.reset_ber()

    print(f"link.status= {link.status}")

# %% [markdown]
# ## 27 - Create eye scan objects for all the links, set the scan params and start the scan
#
# The eye scans will be run in parallel

# %%
eye_scans = create_eye_scans(target_objs=[link for link in links_board1_tx_board2_rx])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 10
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 10
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 28 - Wait for all the eye scans to get done

# %%
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()
eye_scans[2].wait_till_done()
eye_scans[3].wait_till_done()
eye_scans[4].wait_till_done()
eye_scans[5].wait_till_done()
eye_scans[6].wait_till_done()
eye_scans[7].wait_till_done()

# %% [markdown]
# ## 29 - Get Eye Scan report and raw data

# %%
for eye_scan in eye_scans:
    eye_scan.generate_report()
    print(eye_scan.scan_data.processed)

# %% [markdown]
# ## 30 - View Eye Scan Plot.
#
# This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.2/ibert/scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %% [markdown]
# ## 31 - Get Eye Metric Data

# %%
for eye_scan in eye_scans:
    print(f"{eye_scan.name} Open Area:                                      {eye_scan.metric_data.open_area}")
    print(f"{eye_scan.name} Percentage Open Area:                           {eye_scan.metric_data.open_percentage}")
    print(f"{eye_scan.name} Eye width at zero crossing:                     {eye_scan.metric_data.horizontal_opening}")
    print(f"{eye_scan.name} Percentage horizontal opening at zero crossing: {eye_scan.metric_data.horizontal_percentage}")
    print(f"{eye_scan.name} Eye height at zero crossing:                    {eye_scan.metric_data.vertical_opening}")
    print(f"{eye_scan.name} Percentage vertical opening at zero crossing:   {eye_scan.metric_data.vertical_percentage}")

# %% [markdown]
# ## 32 - Delete the links

# %%
delete_links(links_board1_tx_board2_rx)

# %% [markdown]
# ## 33 - Delete session

# %%
delete_session(session)
