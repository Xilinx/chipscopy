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
# This example shows how to interact with landlocked (CPM5-controlled) GTYP resources using ChipScoPy APIs.
# - Program the pcie-ced design with Quad104 and Quad105 onto Production vpk120 board.
# - Verify that the expected IBERT quads are instantiated by the design
# - Decouple the quads from CPM5
# - Change rate for all the links in those quads
# - Plot Eye Scan diagram for these links
#
# ## Requirements
# - AMD vpk120 production board
# - PCIE Loopback card
# - AMD hw_server 2026.1 installed and running
# - AMD cs_server 2026.1 installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports
# Import required functions and classes

# %%
import os

from chipscopy import create_session, delete_session, report_versions, report_hierarchy
from chipscopy.examples.mesa import resolve_example_design
from chipscopy.api.ibert.aliases import (
    PATTERN,
    RX_LOOPBACK,
    EYE_SCAN_HORZ_STEP,
    EYE_SCAN_VERT_STEP,
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_VERT_RANGE,
    EYE_SCAN_TARGET_BER,
)
from chipscopy.api.ibert import create_links, create_eye_scans


# %% [markdown]
# ## 2 - Define helper functions for decoupling
#
# These helpers wrap the low-level register pokes that detach the GTYP quads from CPM5 control, so the rest of the notebook can decouple a quad with a single call instead of repeating the raw register sequence each time.

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
# ## 3 - Define helper functions for rate change
#
# Once a quad is decoupled from CPM5 it no longer follows PCIe LTSSM rate negotiation, so we need these helpers to manually reprogram the PLL/dividers and switch the lanes between Gen1/2/3/4 line rates for the eye scans below.

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
    
def set_rate(quads, rate):
    print(f"\n--------> Setting line rate to {rate}")
    for quad in quads:
        set_channel_rate_using_prop(quad, rate)
        get_current_channel_rate(quad)


# %% [markdown]
# ## 4 - Define helper functions to set and report link properties

# %%
def set_link_properties(links):
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

def print_link_properties(links):
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
# ## 5 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.

# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
EXAMPLE_ID = "cpm_decoupling"
PROG_DEVICE = True

# Direct mode: set these to use your own design files (skips MESA). When
# direct mode is used, the GTYP quad names cannot be read from a manifest, so
# the user MUST set IBERT_QUAD_NAMES to a comma-separated list of the two
# CPM5-controlled quads in the design (e.g. "Quad_104,Quad_105").
PROGRAMMING_FILE = ""
PROBES_FILE = ""
IBERT_QUAD_NAMES = os.getenv("IBERT_QUAD_NAMES", "")

# ============================================================

# --- MESA setup (no edits needed below) ---
example_design = resolve_example_design(
    HW_PLATFORM,
    EXAMPLE_ID,
    programming_file=PROGRAMMING_FILE,
    probes_file=PROBES_FILE,
)
design_manifest = example_design.manifest  # None in direct mode
DEVICE_FAMILY = example_design.device_family
PROGRAMMING_FILE = example_design.programming_file
PROBES_FILE = example_design.probes_file

example_design.print_summary()
print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 6 - Program the device with the VPK120 PCIe CED design and discover cores

# %%
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

if PROG_DEVICE:
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)

# %% [markdown]
# ## 7 - Discover and set up the IBERT core
#
# Debug core discovery initializes the ChipScoPy server debug cores.

# %%
device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery complete")

if len(device.ibert_cores) == 0:
    print("No IBERT core found! Exiting...")
    exit()

# Resolve the GTYP quad names. In MESA mode they come from the manifest; in
# direct mode the user supplies them via IBERT_QUAD_NAMES (comma-separated).
if design_manifest is not None:
    gtyp_quad_names = design_manifest.get_core_config("ibert_gtyp", "quad_names", [])
else:
    gtyp_quad_names = [q.strip() for q in IBERT_QUAD_NAMES.split(",") if q.strip()]
    if not gtyp_quad_names:
        raise RuntimeError(
            "Direct mode (PROGRAMMING_FILE provided) requires IBERT_QUAD_NAMES "
            "to be set to a comma-separated list of the GTYP quad names in the "
            "design (e.g. export IBERT_QUAD_NAMES='Quad_104,Quad_105')."
        )

ibert_core = None
for idx in range(len(device.ibert_cores)):
    candidate = device.ibert_cores.at(index=idx)
    gt_names = [g.name for g in candidate.gt_groups]
    if any(qn in gt_names for qn in gtyp_quad_names):
        ibert_core = candidate
        break

if ibert_core is None:
    raise RuntimeError("No hardware IBERT core matching GTYP quads found on device")

print(f"Matched IBERT core: {ibert_core}")
print(f"GT Groups available - {[g.name for g in ibert_core.gt_groups]}")

# %% [markdown]
# ## 8 - Print the hierarchy of the IBERT core
#
# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs

# %%
report_hierarchy(ibert_core)

# Reuse the GTYP quad list resolved above (manifest in MESA mode, IBERT_QUAD_NAMES
# in direct mode). The decouple flow needs at least two quads (Quad_104, Quad_105).
quad_names = gtyp_quad_names
if len(quad_names) < 2:
    raise RuntimeError(f"Expected at least 2 quads, but only {len(quad_names)} provided")

src = "design_manifest" if design_manifest is not None else "IBERT_QUAD_NAMES env var"
print(f"Using quads from {src}: {quad_names}")

# Retrieve quads by name from design_manifest
q104 = ibert_core.gt_groups.filter_by(name=quad_names[0])[0]
q105 = ibert_core.gt_groups.filter_by(name=quad_names[1])[0]
print(f"Quad 0: {q104.name}, Quad 1: {q105.name}")

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
set_link_properties(links)

# %% [markdown]
# ## 11 - Set rate to Gen1

# %%
#set line rate
set_rate(land_Locked_Quads, 'Gen1')
print_link_properties(links)

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
# ## 13 - Wait for all eye scans to complete

# %%
for i, eye_scan in enumerate(eye_scans):
    eye_scan.wait_till_done()
    print(f"Eye scan {i} complete")

# %% [markdown]
# ## 14 - View the eye-scan plot
#
# This requires Plotly to be installed. See how to install it [here](https://xilinx.github.io/chipscopy/2026.1/ibert/eye_scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %% [markdown]
# ## 15 - Set rate to Gen2

# %%
#set line rate
set_rate(land_Locked_Quads, 'Gen2')
print_link_properties(links)

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
# ## 17 - Wait for all eye scans to complete

# %%
for i, eye_scan in enumerate(eye_scans):
    eye_scan.wait_till_done()
    print(f"Eye scan {i} complete")

# %% [markdown]
# ## 18 - View Eye Scan Plot.A 2D Eye Scan helps perform margin analysis on the RX channel
#

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %% [markdown]
# ## 19 - Set rate to Gen3

# %%
#set line rate
set_rate(land_Locked_Quads, 'Gen3')
print_link_properties(links)

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
# ## 21 - Wait for all eye scans to complete

# %%
for i, eye_scan in enumerate(eye_scans):
    eye_scan.wait_till_done()
    print(f"Eye scan {i} complete")

# %% [markdown]
# ## 22 - View Eye Scan Plot.A 2D Eye Scan helps perform margin analysis on the RX channel
#

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %% [markdown]
# ## 23 - Set rate to Gen4

# %%
#set line rate
set_rate(land_Locked_Quads, 'Gen4')
print_link_properties(links)

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
# ## 25 - Wait for all eye scans to complete

# %%
for i, eye_scan in enumerate(eye_scans):
    eye_scan.wait_till_done()
    print(f"Eye scan {i} complete")

# %% [markdown]
# ## 26 - View Eye Scan PlotA 2D Eye Scan helps perform margin analysis on the RX channel
#

# %%
for eye_scan in eye_scans:
    eye_scan.plot.show()

# %%
delete_session(session)

