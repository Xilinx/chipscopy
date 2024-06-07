# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
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
# # IBERT Landlocked GTYP decoupling example

# %% [markdown]
# ## Description
# This example shows how to interact with Landlocked (CPM5-controlled) GTYP with ChipScoPy APIs.
# - Program the pcie-ced design with Quad104 and Quad105 onto Production vpk120 board.
# - Verify that the expected IBERT quads are instantiated by the design
# - Decouple the quads from CPM5
# - Change rate for all the links in those quads
# - Plot Eye Scan diagram for these links
#
# ## Requirements
# - Xilinx vpk120 production board
# - PCIE Loopback card
# - Xilinx hw_server 2023.2 installed and running
# - Xilinx cs_server 2023.2 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2023.2 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`
# - Plotting support installed - Please do so, using the command `pip install chipscopy[core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports
# Import required functions and classes

# %%
import os
from more_itertools import one
from itertools import product

from chipscopy import create_session, report_versions, report_hierarchy, get_design_files
from chipscopy.api.ibert.aliases import (
    PATTERN,
    RX_LOOPBACK,
    EYE_SCAN_HORZ_STEP,
    EYE_SCAN_VERT_STEP,
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_VERT_RANGE,
    EYE_SCAN_TARGET_BER,
)
from chipscopy.api.ibert import  create_links, create_eye_scans


# %% [markdown]
# ## 2 - Define some helper functions to achieve decoupling
#

# %%
def is_quad_decoupled(quad):
    prop_name = "CAPTIVE_QUAD_DECOUPLED"
    prop_val = quad.property.refresh(prop_name)[prop_name]
    print(f"{prop_name} = {prop_val}")
    
def decouple_quad_using_prop(quad):
    props = {
        "CAPTIVE_QUAD_DECOUPLE": 1,
    }
    quad.property.set(**props)
    quad.property.commit(list(props.keys()))

def decouple_gtyp_quad(quads):
    print(f"\n--------> Decouple GTYPs from CPM5")
    for quad in quads:
        decouple_quad_using_prop(quad)
        is_quad_decoupled(quad)


# %% [markdown]
# ## 3 - Define some helper functions to achieve rate change
#

# %%
def get_current_channel_rate(quad):
    prop_name = "CAPTIVE_QUAD_PCIE_RATE"
    prop_val = quad.property.refresh(prop_name)[prop_name]
    print(f"{prop_name} = {prop_val}")

def set_channel_rate_using_prop(quad, rate):
    props = {
        "CAPTIVE_QUAD_PCIE_RATE": rate,
    }
    quad.property.set(**props)
    quad.property.commit(list(props.keys()))
    
def setRate(quads, rate):
    print(f"\n--------> Setting line rate to {rate}")
    for quad in quads:
        set_channel_rate_using_prop(quad, rate)
        get_current_channel_rate(quad)


# %% [markdown]
# ## 4- Define helper functions to set and report link properties

# %%
def setLinkProperties(links):
    print("--------> Setting both Tx and RX patterns to 'PRBS 7' & loopback to 'Near-End PMA' for all links")
    for link in links:
        props = {link.tx.property_for_alias[PATTERN]: "PRBS 7"}
        link.tx.property.set(**props)
        link.tx.property.commit(list(props.keys()))

        props = {
            link.rx.property_for_alias[PATTERN]: "PRBS 7",
            link.rx.property_for_alias[RX_LOOPBACK]: "Near-End PMA",
        }
        link.rx.property.set(**props)
        link.rx.property.commit(list(props.keys()))

def printLinkProperties(links):
    for link in links:
        current_txpattern = list(link.tx.property.refresh(link.tx.property_for_alias[PATTERN]).values())[0]
        current_rxpattern = list(link.tx.property.refresh(link.rx.property_for_alias[PATTERN]).values())[0]
        current_rxloopback = list(link.tx.property.refresh(link.rx.property_for_alias[RX_LOOPBACK]).values())[0]
        print(f"\n----- {link.name} -----")
        print(f"Current value of TX pattern - {current_txpattern}")
        print(f"Current value of RX pattern - {current_rxpattern}")
        print(f"Current value of RX loopback - {current_rxloopback}")
        print(f"Line Rate Detected = {link.status}.")


# %% [markdown]
# ## 5- Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 6 - Program the device with vpk120 pcie-ced design and discover cores

# %%
design_files = get_design_files("vpk120/production/pcie_pio_ced/")

PDI_FILE = design_files.programming_file

print(f"PROGRAMMING_FILE: {PDI_FILE}")

device = session.devices.filter_by(family="versal").get()
device.program(PDI_FILE)

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
device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery done")

if len(device.ibert_cores) == 0:
    print("No IBERT core found! Exiting...")
    exit()

# Use the first available IBERT core from the device
ibert_gtyp = one(device.ibert_cores.filter_by(name="IBERT Versal GTYP"))

if len(ibert_gtyp.gt_groups) == 0:
    print("No GT Groups available for use! Exiting...")
    exit()

print(f"GT Groups available - {[gt_group_obj.name for gt_group_obj in ibert_gtyp.gt_groups]}")

# %% [markdown]
# ## 8 - Print the hierarchy of the IBERT core
#
# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs

# %%
report_hierarchy(ibert_gtyp)

gt_group = ibert_gtyp.gt_groups.filter_by(name="Quad_104")[0]

q104 = one(ibert_gtyp.gt_groups.filter_by(name="Quad_104"))
q105 = one(ibert_gtyp.gt_groups.filter_by(name="Quad_105"))

# %% [markdown]
# ## 9 - Create links between following TXs and RXs and set loopback mode
#
# - Quad 104 CH0 TX to Quad 104 CH0 RX
# - Quad 104 CH1 TX to Quad 104 CH1 RX
# - Quad 104 CH2 TX to Quad 104 CH3 RX
# - Quad 104 CH3 TX to Quad 104 CH3 RX
# - Quad 105 CH0 TX to Quad 105 CH0 RX
# - Quad 105 CH1 TX to Quad 105 CH1 RX
# - Quad 105 CH3 TX to Quad 105 CH3 RX
# - Quad 105 CH3 TX to Quad 105 CH3 RX

# %%
links = create_links(
    txs=[q104.gts[0].tx, q104.gts[1].tx, q104.gts[2].tx, q104.gts[3].tx, q105.gts[0].tx, q105.gts[1].tx, q105.gts[2].tx, q105.gts[3].tx],
    rxs=[q104.gts[0].rx, q104.gts[1].rx, q104.gts[2].rx, q104.gts[3].rx, q105.gts[0].rx, q105.gts[1].rx, q105.gts[2].rx, q105.gts[3].rx],
)

print("--> Done creating links")

# %% [markdown]
# ## 10 - Decouple Quads from CPM5

# %%
land_Locked_Quads = [q104,q105]
#Decouple GTYPs from CPM5
decouple_gtyp_quad(land_Locked_Quads)

#set loopback mode with Tx and Rx pattern
setLinkProperties(links)

# %% [markdown]
# ## 11 - Set rate to Gen1

# %%
#set line rate
setRate(land_Locked_Quads, 'Gen1')
printLinkProperties(links)

# %% [markdown]
# ## 12 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %%
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 13 - Wait for all the eye scans to get done

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
# ## 14 - View Eye Scan Plot.
#
# This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2024.1/ibert/eye_scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()

# %% [markdown]
# ## 15 - Set rate to Gen2

# %%
#set line rate
setRate(land_Locked_Quads, 'Gen2')
printLinkProperties(links)

# %% [markdown]
# ## 16 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %%
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 17 - Wait for all the eye scans to get done

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
# ## 18 - View Eye Scan Plot.

# %%
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()

# %% [markdown]
# ## 19 - Set rate to Gen3

# %%
#set line rate
setRate(land_Locked_Quads, 'Gen3')
printLinkProperties(links)

# %% [markdown]
# ## 20 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %%
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 21 - Wait for all the eye scans to get done

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
# ## 22 - View Eye Scan Plot.

# %%
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()

# %% [markdown]
# ## 23 - Set rate to Gen4

# %%
#set line rate
setRate(land_Locked_Quads, 'Gen4')
printLinkProperties(links)

# %% [markdown]
# ## 24 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %%
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 25 - Wait for all the eye scans to get done

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
# ## 26 - View Eye Scan Plot

# %%
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()
