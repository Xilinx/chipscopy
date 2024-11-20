# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.10.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] papermill={"duration": 0.015954, "end_time": "2023-10-24T22:40:55.720158", "exception": false, "start_time": "2023-10-24T22:40:55.704204", "status": "completed"} tags=[]
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

# %% [markdown] papermill={"duration": 0.008446, "end_time": "2023-10-24T22:40:55.736278", "exception": false, "start_time": "2023-10-24T22:40:55.727832", "status": "completed"} tags=[]
# # IBERT Landlocked GTYP decoupling example

# %% [markdown] papermill={"duration": 0.007036, "end_time": "2023-10-24T22:40:55.751724", "exception": false, "start_time": "2023-10-24T22:40:55.744688", "status": "completed"} tags=[]
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

# %% [markdown] papermill={"duration": 0.007411, "end_time": "2023-10-24T22:40:55.766046", "exception": false, "start_time": "2023-10-24T22:40:55.758635", "status": "completed"} tags=[]
# ## 1 - Initialization: Imports
# Import required functions and classes

# %% papermill={"duration": 0.960631, "end_time": "2023-10-24T22:40:56.734163", "exception": false, "start_time": "2023-10-24T22:40:55.773532", "status": "completed"} tags=[]
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

# %% [markdown] papermill={"duration": 0.009147, "end_time": "2023-10-24T22:40:56.754577", "exception": false, "start_time": "2023-10-24T22:40:56.745430", "status": "completed"} tags=[]
# ## 2 - Define some helper functions to achieve decoupling
#

# %% papermill={"duration": 0.017266, "end_time": "2023-10-24T22:40:56.779406", "exception": false, "start_time": "2023-10-24T22:40:56.762140", "status": "completed"} tags=[]
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

# %% [markdown] papermill={"duration": 0.007301, "end_time": "2023-10-24T22:40:56.795597", "exception": false, "start_time": "2023-10-24T22:40:56.788296", "status": "completed"} tags=[]
# ## 3 - Define some helper functions to achieve rate change
#

# %% papermill={"duration": 0.017986, "end_time": "2023-10-24T22:40:56.821008", "exception": false, "start_time": "2023-10-24T22:40:56.803022", "status": "completed"} tags=[]
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

# %% [markdown] papermill={"duration": 0.007224, "end_time": "2023-10-24T22:40:56.835732", "exception": false, "start_time": "2023-10-24T22:40:56.828508", "status": "completed"} tags=[]
# ## 4- Define helper functions to set and report link properties

# %% papermill={"duration": 0.018453, "end_time": "2023-10-24T22:40:56.861455", "exception": false, "start_time": "2023-10-24T22:40:56.843002", "status": "completed"} tags=[]
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


# %% [markdown] papermill={"duration": 0.069734, "end_time": "2023-10-24T22:40:56.940822", "exception": false, "start_time": "2023-10-24T22:40:56.871088", "status": "completed"} tags=[]
# ## 5- Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %% papermill={"duration": 9.670933, "end_time": "2023-10-24T22:41:06.620088", "exception": false, "start_time": "2023-10-24T22:40:56.949155", "status": "completed"} tags=[]
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown] papermill={"duration": 0.009791, "end_time": "2023-10-24T22:41:06.640201", "exception": false, "start_time": "2023-10-24T22:41:06.630410", "status": "completed"} tags=[]
# ## 6 - Program the device with vpk120 pcie-ced design and discover cores

# %% papermill={"duration": 3.629638, "end_time": "2023-10-24T22:41:10.279438", "exception": false, "start_time": "2023-10-24T22:41:06.649800", "status": "completed"} tags=[]
design_files = get_design_files("vpk120/production/pcie_pio_ced/")

PDI_FILE = design_files.programming_file

print(f"PROGRAMMING_FILE: {PDI_FILE}")

device = session.devices.filter_by(family="versal").get()
device.program(PDI_FILE)

# %% [markdown] papermill={"duration": 0.008729, "end_time": "2023-10-24T22:41:10.298339", "exception": false, "start_time": "2023-10-24T22:41:10.289610", "status": "completed"} tags=[]
# ## 7 - Discover and setup the IBERT core
#
# Debug core discovery initializes the chipscope server debug cores.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - The first ibert found is used

# %% jupyter={"outputs_hidden": false} papermill={"duration": 1.016555, "end_time": "2023-10-24T22:41:11.323183", "exception": false, "start_time": "2023-10-24T22:41:10.306628", "status": "completed"} pycharm={"name": "#%%\n"} tags=[]
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

# %% [markdown] papermill={"duration": 0.008545, "end_time": "2023-10-24T22:41:11.341452", "exception": false, "start_time": "2023-10-24T22:41:11.332907", "status": "completed"} tags=[]
# ## 8 - Print the hierarchy of the IBERT core
#
# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs

# %% jupyter={"outputs_hidden": false} papermill={"duration": 2.838407, "end_time": "2023-10-24T22:41:14.188217", "exception": false, "start_time": "2023-10-24T22:41:11.349810", "status": "completed"} pycharm={"name": "#%%\n"} tags=[]
report_hierarchy(ibert_gtyp)

gt_group = ibert_gtyp.gt_groups.filter_by(name="Quad_104")[0]

q104 = one(ibert_gtyp.gt_groups.filter_by(name="Quad_104"))
q105 = one(ibert_gtyp.gt_groups.filter_by(name="Quad_105"))

# %% [markdown] papermill={"duration": 0.008099, "end_time": "2023-10-24T22:41:14.205991", "exception": false, "start_time": "2023-10-24T22:41:14.197892", "status": "completed"} tags=[]
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

# %% papermill={"duration": 0.019084, "end_time": "2023-10-24T22:41:14.233175", "exception": false, "start_time": "2023-10-24T22:41:14.214091", "status": "completed"} tags=[]
links = create_links(
    txs=[q104.gts[0].tx, q104.gts[1].tx, q104.gts[2].tx, q104.gts[3].tx, q105.gts[0].tx, q105.gts[1].tx, q105.gts[2].tx, q105.gts[3].tx],
    rxs=[q104.gts[0].rx, q104.gts[1].rx, q104.gts[2].rx, q104.gts[3].rx, q105.gts[0].rx, q105.gts[1].rx, q105.gts[2].rx, q105.gts[3].rx],
)

print("--> Done creating links")

# %% [markdown] papermill={"duration": 0.008055, "end_time": "2023-10-24T22:41:14.249873", "exception": false, "start_time": "2023-10-24T22:41:14.241818", "status": "completed"} tags=[]
# ## 10 - Decouple Quads from CPM5

# %% papermill={"duration": 3.723265, "end_time": "2023-10-24T22:41:17.981374", "exception": false, "start_time": "2023-10-24T22:41:14.258109", "status": "completed"} pycharm={"name": "#%%\n"} tags=[]
land_Locked_Quads = [q104,q105]
#Decouple GTYPs from CPM5
decouple_gtyp_quad(land_Locked_Quads)

#set loopback mode with Tx and Rx pattern
setLinkProperties(links)

# %% [markdown] papermill={"duration": 0.008756, "end_time": "2023-10-24T22:41:17.999823", "exception": false, "start_time": "2023-10-24T22:41:17.991067", "status": "completed"} tags=[]
# ## 11 - Set rate to Gen1

# %% papermill={"duration": 3.645192, "end_time": "2023-10-24T22:41:21.653570", "exception": false, "start_time": "2023-10-24T22:41:18.008378", "status": "completed"} pycharm={"name": "#%%\n"} tags=[]
#set line rate
setRate(land_Locked_Quads, 'Gen1')
printLinkProperties(links)

# %% [markdown] papermill={"duration": 0.008976, "end_time": "2023-10-24T22:41:21.673937", "exception": false, "start_time": "2023-10-24T22:41:21.664961", "status": "completed"} tags=[]
# ## 12 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %% papermill={"duration": 130.617844, "end_time": "2023-10-24T22:43:32.301164", "exception": false, "start_time": "2023-10-24T22:41:21.683320", "status": "completed"} tags=[]
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 13 - Wait for all the eye scans to get done

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()
eye_scans[2].wait_till_done()
eye_scans[3].wait_till_done()
eye_scans[4].wait_till_done()
eye_scans[5].wait_till_done()
eye_scans[6].wait_till_done()
eye_scans[7].wait_till_done()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 14 - View Eye Scan Plot.
#
# This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2024.1/ibert/eye_scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 15 - Set rate to Gen2

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} pycharm={"name": "#%%\n"} tags=[]
#set line rate
setRate(land_Locked_Quads, 'Gen2')
printLinkProperties(links)

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 16 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 17 - Wait for all the eye scans to get done

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()
eye_scans[2].wait_till_done()
eye_scans[3].wait_till_done()
eye_scans[4].wait_till_done()
eye_scans[5].wait_till_done()
eye_scans[6].wait_till_done()
eye_scans[7].wait_till_done()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 18 - View Eye Scan Plot.

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 19 - Set rate to Gen3

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} pycharm={"name": "#%%\n"} tags=[]
#set line rate
setRate(land_Locked_Quads, 'Gen3')
printLinkProperties(links)

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 20 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 21 - Wait for all the eye scans to get done

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()
eye_scans[2].wait_till_done()
eye_scans[3].wait_till_done()
eye_scans[4].wait_till_done()
eye_scans[5].wait_till_done()
eye_scans[6].wait_till_done()
eye_scans[7].wait_till_done()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 22 - View Eye Scan Plot.

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 23 - Set rate to Gen4

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
#set line rate
setRate(land_Locked_Quads, 'Gen4')
printLinkProperties(links)

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 24 - Create Eye Scan Diagrams

# %% [markdown]
# #### Check if PLL is locked and link is up before performing Eye Scan 

# %%
for link in links:
    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans = create_eye_scans(target_objs=[link for link in links])
for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = 2
    eye_scan.params[EYE_SCAN_VERT_STEP].value = 2
    eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
    eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
    eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

    eye_scan.start()
    print(f"Started eye scan {eye_scan}")

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 25 - Wait for all the eye scans to get done

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].wait_till_done()
eye_scans[1].wait_till_done()
eye_scans[2].wait_till_done()
eye_scans[3].wait_till_done()
eye_scans[4].wait_till_done()
eye_scans[5].wait_till_done()
eye_scans[6].wait_till_done()
eye_scans[7].wait_till_done()

# %% [markdown] papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
# ## 26 - View Eye Scan Plot

# %% papermill={"duration": null, "end_time": null, "exception": null, "start_time": null, "status": "completed"} tags=[]
eye_scans[0].plot.show()
eye_scans[1].plot.show()
eye_scans[2].plot.show()
eye_scans[3].plot.show()
eye_scans[4].plot.show()
eye_scans[5].plot.show()
eye_scans[6].plot.show()
eye_scans[7].plot.show()
