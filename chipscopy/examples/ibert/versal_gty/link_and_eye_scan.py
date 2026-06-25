# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2021-2022, Xilinx, Inc.<br>
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
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
# # IBERT link and eye scan example
#
#
# <img src="../../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example shows how to interact with the IBERT (Integrated Bit Error Ratio Tester) debug core service via ChipScoPy APIs. It supports multiple IBERT transceiver types (GTY, GTYP, GTM) across different Versal platforms using the MESA manifest system.
#
# - Program the ChipScoPy CED design onto the target device
# - Discover available IBERT cores and select the appropriate one from the manifest
# - Create links on a user-selected or default quad
# - **Link creation** works on all IBERT types (GTY, GTYP, GTM)
# - **Eye scan and sweep** are only supported on GTY and GTYP cores (not GTM)
# - Run and plot eye scans for the links (when supported)
# - Run a sweep on a link (when supported)
#
# ### User Configuration
# - `IBERT_TYPE` environment variable: Select a specific IBERT core type (e.g., `ibert_gty`, `ibert_gtyp`, `ibert_gtm`). Default: first core with eye scan support.
# - `IBERT_QUAD` environment variable: Select a specific quad (e.g., `Quad_205`). Default: first quad of the selected core.
#
# ## Requirements
# - Local or remote AMD Versal board (VCK190, VMK180, VPK120, VHK158, VEK280, VEK385, etc.)
# - AMD hw_server 2026.1+ installed and running
# - AMD cs_server 2026.1+ installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1+ installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`
# - Optional - [External loopback](https://www.samtec.com/kits/optics-fpga/hspce-fmcp/) (For the sweep example only).

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths

# %%
import os
from itertools import product

from chipscopy import (
    create_session,
    report_versions,
    report_hierarchy,
    delete_session,
)
from chipscopy.examples.mesa import resolve_example_design
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
    RX_COMMON_MODE,
)
from chipscopy.api.ibert import create_eye_scans, create_links, get_all_links,delete_links, detect_links
from chipscopy.dm.request import CsFuture

# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "link_and_eye_scan"
PROG_DEVICE = True

# Optional core/quad selection. Empty string -> auto-pick (first eye_scan-capable
# core, first quad). Works in both MESA and direct mode.
IBERT_TYPE = os.getenv("IBERT_TYPE", "")
IBERT_QUAD = os.getenv("IBERT_QUAD", "")

# Direct mode: set these to use your own design files (skips MESA).
PROGRAMMING_FILE = ""
PROBES_FILE = ""

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

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.

# %%
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design

# %%
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

if PROG_DEVICE:
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)

# %% [markdown]
# ## 4 - Discover IBERT cores and select core/quad
#
# Debug core discovery initializes the ChipScoPy server debug cores. The manifest is queried for all available IBERT core types and their capabilities.

# %%
device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery complete")

if len(device.ibert_cores) == 0:
    print("No IBERT core found! Exiting...")
    exit()

if design_manifest is not None:
    # MESA mode: the manifest enumerates the IBERT core types and their
    # eye_scan capability. Pick one based on IBERT_TYPE or auto-pick the
    # first eye_scan-capable core.
    all_ibert_cores = design_manifest.get_all_ibert_cores()
    if not all_ibert_cores:
        raise RuntimeError("No IBERT cores configured in design_manifest for this platform")

    print("\nIBERT cores available from design_manifest:")
    for core_type, core_config in all_ibert_cores:
        eye_ok = "eye_scan" in core_config.features
        print(f"  {core_type}: quads={core_config.quad_names}, "
              f"eye_scan={'Yes' if eye_ok else 'No'}, features={core_config.features}")

    if IBERT_TYPE:
        selected = next(((t, c) for t, c in all_ibert_cores if t == IBERT_TYPE), None)
        if not selected:
            raise RuntimeError(
                f"IBERT type '{IBERT_TYPE}' not found or not enabled in design_manifest. "
                f"Available: {[t for t, _ in all_ibert_cores]}")
    else:
        eye_scan_cores = [(t, c) for t, c in all_ibert_cores if "eye_scan" in c.features]
        if eye_scan_cores:
            selected = eye_scan_cores[0]
        else:
            selected = all_ibert_cores[0]
            print(f"\nWARNING: No eye_scan-capable IBERT core found. "
                  f"Using {selected[0]} (link creation only).")

    ibert_core_type, ibert_config = selected
    supports_eye_scan = "eye_scan" in ibert_config.features
    available_quads = ibert_config.quad_names or []
else:
    # Direct mode: Point at a specific IBERT core type and quad via env vars.
    if not IBERT_TYPE or not IBERT_QUAD:
        raise RuntimeError(
            "Direct mode (PROGRAMMING_FILE provided) requires IBERT_TYPE and "
            "IBERT_QUAD environment variables (e.g. "
            "export IBERT_TYPE=ibert_gty IBERT_QUAD=Quad_205). In direct mode "
            "we cannot infer the IBERT core type or available quads from a "
            "design_manifest, so the user must specify them explicitly."
        )
    ibert_core_type = IBERT_TYPE
    available_quads = [IBERT_QUAD]

    supports_eye_scan = True
    print(f"\nDirect mode: using {ibert_core_type} with quad {IBERT_QUAD}")

print(f"\nSelected IBERT core: {ibert_core_type}")
print(f"Eye scan support: {'Yes' if supports_eye_scan else 'No (link-only mode)'}")
print(f"Available quads: {available_quads}")

# Pick which quad to scan
if IBERT_QUAD:
    if IBERT_QUAD not in available_quads:
        raise RuntimeError(
            f"Quad '{IBERT_QUAD}' not in {ibert_core_type} quads: {available_quads}")
    selected_quad_names = [IBERT_QUAD]
    print(f"User-selected quad: {IBERT_QUAD}")
else:
    selected_quad_names = available_quads[:1] if available_quads else []
    print(f"Default: using first quad: {selected_quad_names}")

# Find which IBERT core on the live device actually hosts the chosen quad
ibert = None
for idx in range(len(device.ibert_cores)):
    candidate = device.ibert_cores.at(index=idx)
    gt_names = [g.name for g in candidate.gt_groups]
    if any(qn in gt_names for qn in available_quads):
        ibert = candidate
        break

if ibert is None:
    raise RuntimeError(
        f"No hardware IBERT core with quads matching {ibert_core_type} found on device")

print(f"\nMatched hardware IBERT core: {ibert}")
print(f"GT Groups on hardware: {[g.name for g in ibert.gt_groups]}")

# %% [markdown]
# ## 5 - Resolve selected quads to hardware objects
#
# The selected quad names are matched to hardware GT group objects for link creation.

# %%
report_hierarchy(ibert)

quads = []
for quad_name in selected_quad_names:
    quad_list = ibert.gt_groups.filter_by(name=quad_name)
    if quad_list:
        quads.append(quad_list[0])
    else:
        print(f"WARNING: Quad '{quad_name}' not found in hardware")

if not quads:
    raise RuntimeError(f"No usable quads found from selection: {selected_quad_names}")

print(f"Using {len(quads)} quad(s) for link creation: {[q.name for q in quads]}")
if not supports_eye_scan:
    print(f"\nNOTE: {ibert_core_type} does not support eye scan. "
          f"This example will create links but skip eye scan and sweep sections.")

# %% [markdown]
# ## 6 - Create links for testing
#
# Links are created for each selected quad. Link creation works on all IBERT types (GTY, GTYP, GTM).
# One link per quad is created using the first channel for loopback testing.

# %%
txs = []
rxs = []
for quad in quads:
    if len(quad.gts) > 0:
        txs.append(quad.gts[0].tx)
        rxs.append(quad.gts[0].rx)

links = create_links(txs=txs, rxs=rxs)

print(f"--> Created {len(links)} link(s) on {ibert_core_type}")
for link in links:
    print(f"    {link.name}")

# %% [markdown]
# ## 7 - Print the valid values for pattern and loopback, set the pattern for the TXs and RXs to "PRBS 31" and set loopback to "Near-End PMA"
#
# In order to lock the internal pattern checker, TX and RX patterns need to match. We also need to have some kind of loopback, internal/external.
#
# We are assuming that no external cable loopback is present and hence making use of internal loopback.

# %%
PATTERN_VALUE = "PRBS 31"
LOOPBACK_VALUE = "Near-End PMA"

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

    props = {link.tx.property_for_alias[PATTERN]: PATTERN_VALUE}
    link.tx.property.set(**props)
    link.tx.property.commit(list(props.keys()))

    props = {
        link.rx.property_for_alias[PATTERN]: PATTERN_VALUE,
        link.rx.property_for_alias[RX_LOOPBACK]: LOOPBACK_VALUE,
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))
    print(f"\n--> Set both patterns to '{PATTERN_VALUE}' & loopback to '{LOOPBACK_VALUE}' for {link}")

    assert link.rx.pll.locked and link.tx.pll.locked
    print(f"--> RX and TX PLLs are locked for {link}. Checking for link lock...")
    assert link.status != "No link"
    print(f"--> {link} is linked as expected")

# %% [markdown]
# ## 8 - Create eye scan objects for all the links, set the scan params and start the scan
#
# Eye scans are only supported on GTY and GTYP cores. If a GTM core is selected, this section is skipped.
#
# The eye scans will be run in parallel.

# %%
eye_scans = []

if not supports_eye_scan:
    print(f"Eye scan is not supported on {ibert_core_type} cores.")
    print("Skipping eye scan. To run eye scans, use a GTY or GTYP core "
          "(set IBERT_TYPE=ibert_gty or IBERT_TYPE=ibert_gtyp).")
else:
    EYE_SCAN_HORZ_STEP_VALUE = 10
    EYE_SCAN_VERT_STEP_VALUE = 10

    eye_scans = create_eye_scans(target_objs=[link for link in links])
    for eye_scan in eye_scans:
        eye_scan.params[EYE_SCAN_HORZ_STEP].value = EYE_SCAN_HORZ_STEP_VALUE
        eye_scan.params[EYE_SCAN_VERT_STEP].value = EYE_SCAN_VERT_STEP_VALUE
        eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
        eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
        eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5

        eye_scan.start()
        print(f"Started eye scan {eye_scan}")

# %% [markdown]
# ## 9 - Wait for all the eye scans to get done

# %%
if eye_scans:
    for i, eye_scan in enumerate(eye_scans):
        eye_scan.wait_till_done()
        print(f"Eye scan {i} ({eye_scan}) complete")
else:
    print("No eye scans to wait for (skipped for this core type)")

# %% [markdown]
# ## 10 - View Eye Scan Plot.
#
# A 2D Eye Scan helps perform margin analysis on the RX channel
# This requires Plotly to be installed. See how to install it [here](https://xilinx.github.io/chipscopy/2026.1/ibert/eye_scan.html#scan-plots)
#
# NOTE - The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
if eye_scans:
    for i, eye_scan in enumerate(eye_scans):
        print(f"Eye scan plot {i}:")
        eye_scan.plot.show()
else:
    print("No eye scan plots to display (skipped for this core type)")

# %% [markdown]
# # IBERT Sweep Example
#
# **Note: The sweep requires eye scan support (GTY/GTYP cores only). If a GTM core is selected, the sweep section is skipped.**
#
# This step begins the sweep example, in which for a single link we iterate through valid property values for our desired TX/RX properties, creating an eye scan for each combination of values and allowing us to identify the property values corresponding to the best eye scan. 
#
# Note that while the eye scan example assumed that no external cable loopback was present, this example was designed to work for devices with external loopback - regardless of the property values we are sweeping over, using internal loopback would likely cause there to not be any appreciable difference in the eye scans generated by the sweep. 
#
# For an example of an external loopback module utilized in this example, click [here](https://www.samtec.com/kits/optics-fpga/hspce-fmcp/).
#
# The sweep uses the first link created above.

# %% [markdown]
# ## 11 - Cache Properties for Sweep.
#
# As performing a sweep will continuously modify our RX and TX properties, we must begin our sweep by storing the current values in order to restore them after we are done.

# %%
# Bail if this core variant doesn't support eye scan -- the sweep below would be meaningless.
if not supports_eye_scan:
    print(f"Sweep requires eye scan support. Skipping for {ibert_core_type}.")
else:
    link = links[0]

    # Disable RX loopback so the sweep exercises the real channel.
    props = {
        link.rx.property_for_alias[RX_LOOPBACK]: "None"
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))

    print(f"\n----- {link.name} -----")

    # Snapshot the four TX/RX EQ knobs we are about to sweep so step 15 can restore them.
    orig_precursor = list(link.tx.property.refresh(link.tx.property_for_alias[TX_PRE_CURSOR]).values())[0]
    orig_postcursor = list(link.tx.property.refresh(link.tx.property_for_alias[TX_POST_CURSOR]).values())[0]
    orig_diffswing = list(link.tx.property.refresh(link.tx.property_for_alias[TX_DIFFERENTIAL_SWING]).values())[0]
    orig_termvolt = list(link.tx.property.refresh(link.rx.property_for_alias[RX_TERMINATION_VOLTAGE]).values())[0]

    print(f"--> Original value of TX Pre Cursor - {orig_precursor}")
    print(f"--> Original value of TX Post Cursor - {orig_postcursor}")
    print(f"--> Original value of TX Diff Swing - {orig_diffswing}")
    print(f"--> Original value of RX Termination Voltage - {orig_termvolt}")

# %% [markdown]
# ## 12 - Find Properties for Sweep.
# In this step, we find all possible values of the properties we wish to sweep over. For the purposes of this example, only two possible values from each property are used.

# %%
if not supports_eye_scan:
    print("Skipped (no eye scan support)")
else:
    # Ask the device for the legal values each property accepts.
    _, tx_precursor_report = link.tx.property.report(link.tx.property_for_alias[TX_PRE_CURSOR]).popitem()
    _, tx_postcursor_report = link.tx.property.report(link.tx.property_for_alias[TX_POST_CURSOR]).popitem()
    _, tx_diffswing_report = link.tx.property.report(link.tx.property_for_alias[TX_DIFFERENTIAL_SWING]).popitem()
    _, rx_termvolt_report = link.tx.property.report(link.rx.property_for_alias[RX_TERMINATION_VOLTAGE]).popitem()

    # Print them so the reader can see what the device actually accepts.
    print(f"\n----- {link.name} -----")
    print(f"--> Valid values for TX Pre Cursor - {tx_precursor_report['Valid values']}")
    print(f"--> Valid values for TX Post Cursor - {tx_postcursor_report['Valid values']}")
    print(f"--> Valid values for TX Diff Swing - {tx_diffswing_report['Valid values']}")
    print(f"--> Valid values for RX Termination Voltage - {rx_termvolt_report['Valid values']}")

    # Pick the first two values of each as a small demo set (full sweeps explode quickly).
    selected_precurs = tx_precursor_report['Valid values'][0:2]
    selected_postcurs = tx_postcursor_report['Valid values'][0:2]
    selected_diffswing = tx_diffswing_report['Valid values'][0:2]
    selected_termvolt = rx_termvolt_report['Valid values'][0:2]

# %% [markdown]
# ## 13 - Perform the Sweep.
# Iteration over combinations of property values is performed using the itertools product method, imported in the first cell of this example notebook.
#
# This step displays the resulting eye scans, completing the sweep.

# %%
if not supports_eye_scan:
    print("Skipped (no eye scan support)")
    sweep_eye_scans = []
else:
    # Cartesian product of all four knobs: 2 x 2 x 2 x 2 = 16 settings (one eye scan each).
    combinations = list(product(selected_precurs, 
                    selected_postcurs, selected_diffswing, 
                        selected_termvolt))
    print(f"-----Total Eye Scans in this Sweep: {len(combinations)}-----")

    sweep_eye_scans = []
    for (precurs, poscurs, difswing, tervolt) in combinations:
        # Push the three TX EQ values to the device.
        props = {
            link.tx.property_for_alias[TX_PRE_CURSOR]: precurs,
            link.tx.property_for_alias[TX_POST_CURSOR]: poscurs,
            link.tx.property_for_alias[TX_DIFFERENTIAL_SWING]: difswing
        }
        link.tx.property.set(**props)
        link.tx.property.commit(list(props.keys()))
        
        # Push the RX termination voltage.
        props = {
            link.rx.property_for_alias[RX_TERMINATION_VOLTAGE]: tervolt,
        }
        link.rx.property.set(**props)
        link.rx.property.commit(list(props.keys()))
        
        # Configure and run an eye scan for this combination, then stash it for plotting.
        eye_scan = create_eye_scans(target_objs=link)[0]
        eye_scan.params[EYE_SCAN_HORZ_STEP].value = EYE_SCAN_HORZ_STEP_VALUE
        eye_scan.params[EYE_SCAN_VERT_STEP].value = EYE_SCAN_VERT_STEP_VALUE
        eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
        eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
        eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5
        eye_scan.start()
        eye_scan.wait_till_done()
        print(f"Finished eye scan {eye_scan}")    
        title_string = (f"Pre Cursor: {precurs}, Post Cursor: {poscurs}, "
                        f"Diff Swing: {difswing},<br> Termination Voltage: {tervolt}")
        sweep_eye_scans.append([eye_scan, title_string])


# %% [markdown]
# ## 14 - Find the Sweep's Best Eye Scan.
# Using the eye scans that we have created with the sweep, we can deduce which eye scan and its corresponding properties are the most desirable based on many different, often arbitrary metrics. In this example, we will use the proportion of 0 Bit Error Rate within each eye scan. Other ways of identifying eye-scan quality could include calculating the largest width of the dark blue area, or even simply eye-balling the area of the graph. 
#
# In this cell, we calculate our metric using the eye scan's raw data, sorting the resulting eye scans in descending order and printing them out.

# %%
if not supports_eye_scan or not sweep_eye_scans:
    print("Skipped (no eye scan support)")
else:
    for scan in sweep_eye_scans:
        scan.append(sum([1 for i in scan[0].scan_data.raw.error_count if i == 0])/len(scan[0].scan_data.raw.error_count))

    sweep_eye_scans.sort(key=lambda x: x[2], reverse=True)

    for scan in sweep_eye_scans:
        scan[1] += f", Zero Error Rate: {scan[2]}"
        scan[0].plot.show(title=scan[1])

# %% [markdown]
# ## 15 - Restore Original Property Values.
# After completing the sweep, we must finally restore each property to their original values, which we had cached in step 11.

# %%
if not supports_eye_scan:
    print("Skipped (no sweep was performed)")
else:
    props = {
        link.tx.property_for_alias[TX_PRE_CURSOR]: orig_precursor,
        link.tx.property_for_alias[TX_POST_CURSOR]: orig_postcursor,
        link.tx.property_for_alias[TX_DIFFERENTIAL_SWING]: orig_diffswing,
    }    
    link.tx.property.set(**props)  
    link.tx.property.commit(list(props.keys()))

    props = {
        link.rx.property_for_alias[RX_TERMINATION_VOLTAGE]: orig_termvolt,
    }    
    link.rx.property.set(**props)  
    link.rx.property.commit(list(props.keys()))

    print(f"Post-sweep value of TX Pre Cursor: {list(link.tx.property.refresh(link.tx.property_for_alias[TX_PRE_CURSOR]).values())[0]}")
    print(f"Post-sweep value of TX Post Cursor: {list(link.tx.property.refresh(link.tx.property_for_alias[TX_POST_CURSOR]).values())[0]}")
    print(f"Post-sweep value of TX Diff Swing: {list(link.tx.property.refresh(link.tx.property_for_alias[TX_DIFFERENTIAL_SWING]).values())[0]}")
    print(f"Post-sweep value of RX Termination Voltage: {list(link.rx.property.refresh(link.rx.property_for_alias[RX_TERMINATION_VOLTAGE]).values())[0]}")

# %% [markdown]
# # IBERT Auto Link Detection
#
# detect_links API can be used to automatically detect the links in a system.
# This API uses progress and done callback function to allow 

# %%
delete_links(get_all_links())
links_created = None

def done_callback(f:CsFuture):
    global links_created
    result = f.result
    print(f"INFO: {result.info}")
    print(f"Progress : {result.progress}")
    links_created = result.new_link
    print(f"Found {len(links_created)} links!")

def progress_callback(f:CsFuture):
    result = f.progress
    print(f"INFO: {result.info}")
    print(f"Progress : {result.progress}")
    print(f"link : {result.new_link}")

# Detect links in a session
detect_future = detect_links(target=session, done=done_callback, progress=progress_callback)
assert detect_future.error is None 

print(f"Links found - {links_created}")

delete_links(links_created)
assert len(get_all_links()) == 0
print("Deleted all links")

# %%
## When done with testing, close the connection
delete_session(session)
