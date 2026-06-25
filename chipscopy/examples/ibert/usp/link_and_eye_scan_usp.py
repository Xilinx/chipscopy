# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2025, Advanced Micro Devices, Inc.
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
# # IBERT UltraScale+ Link and Eye Scan Example (GTY and GTH)
#

# %% [markdown]
# ### Description
# This example shows how to use the IBERT (Integrated Bit Error Ratio Tester) debug core via ChipScoPy APIs on AMD UltraScale+ devices. The same notebook adapts to either GTY (e.g. VCU128) or GTH (e.g. SCU200) transceivers: the design manifest declares which IBERT variant is in the design and which quads are present, and the notebook follows the manifest.
#
# The example demonstrates:
#
# - Program the UltraScale+ design selected by the MESA manifest (or by user-supplied files in direct mode)
# - Discover the IBERT cores and their GT quads on the device
# - Create one link per channel on the first manifest-listed quad
# - Configure matching PRBS pattern + internal loopback and verify link lock
# - Run eye scans on all links and report the open-area metric
#
# ### Requirements
# - An AMD UltraScale+ board with an IBERT-enabled design (GTY: VCU128, etc.; GTH: SCU200, etc.)
# - AMD hw_server 2026.1 installed and running
# - AMD cs_server 2026.1 installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths

# %%
import os

from chipscopy import create_session, delete_session, report_versions, report_hierarchy
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
    RX_COMMON_MODE
)
from chipscopy.api.ibert import create_links, create_eye_scans

# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vcu128")
EXAMPLE_ID = "link_and_eye_scan_usp"
PROG_DEVICE = True

# Optional quad selection. Empty string -> use the first quad listed in the
# design manifest (MESA mode) or required-via-env-var (direct mode).
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
# Typical case - one device on the board - get it using family from manifest.
# DEVICE_FAMILY comes from the manifest: `virtexuplus` for VCU128 GTY,
# `spartanu` for SCU200 GTH, etc.
device = session.devices.filter_by(family=DEVICE_FAMILY).get()
print(device)

if PROG_DEVICE:
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    # example_design.program_device() handles flat vs. segmented programming
    # automatically based on the manifest's programming_flow setting.
    example_design.program_device(device, delay_after_program=10)

# %% [markdown]
# Close and reopen the session so cs_server re-scans the freshly programmed XSDB topology, then re-pick the device for debug-core discovery.
#
# On most UltraScale+ boards (e.g. VCU128) the same alias used to program the device also exposes the chipscope hub, so this re-pick is a no-op `filter_by(family=DEVICE_FAMILY)`.
#
# On SCU200, the physical `xcsu200p` shows up as two distinct aliases in `session.devices`: the JTAG-programmable alias (family `spartanu`, used above to load the PDI) and the BSCAN-downstream alias (family `uplus`) which is the only one that exposes a `chipscope_node`. We must therefore filter by `family="uplus"` to discover the IBERT GTH core.

# %%
delete_session(session)
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
if HW_PLATFORM == "scu200":
    device = session.devices.filter_by(family="uplus").get()
else:
    device = session.devices.filter_by(family=DEVICE_FAMILY).get()
print(f"Chipscope device: {device}")

# %% [markdown]
# ## 4 - Discover  IBERT cores
#
# Debug core discovery initializes the ChipScoPy server debug cores.

# %%
device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery complete for board")

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
#
# _(Plumbing.)_ The cell below is bookkeeping: it asks the MESA design manifest which IBERT core / quad this example was built for, then matches that against the IBERT cores actually discovered on the hardware and grabs the right quad object. In direct mode (no manifest) the `IBERT_QUAD` env var picks the quad. The only useful output is `quad` -- the GT-quad we will hang the rest of the notebook off of.

# %%
# ----------------------------------------------------------------------
# PLUMBING: figure out which IBERT core / quad to drive. MESA mode reads
# this from the design manifest; direct mode reads it from IBERT_QUAD.
# The rest of the notebook only consumes `quad`.
# ----------------------------------------------------------------------

if design_manifest is not None:
    # 1) Pull the IBERT-core entry out of the manifest. Each manifest entry
    #    describes one debug core; we want the IBERT one and the quads it
    #    nominates. `get_ibert_core()` picks the first enabled IBERT core,
    #    which adapts to `ibert_usp_gty` on VCU128 and `ibert_usp_gth` on
    #    SCU200 without hardcoding the core name.
    ibert_core = design_manifest.get_ibert_core()
    if not ibert_core:
        raise RuntimeError("No IBERT core found in design_manifest")

    ibert_core_type, ibert_config = ibert_core
    available_quads = ibert_config.quad_names or []

    print(f"Found {ibert_core_type} core in design_manifest")
    print(f"Available quads from design_manifest: {available_quads}")

    if not available_quads:
        raise RuntimeError("No quad names specified in design_manifest")
else:
    # Direct mode: there is no manifest, so the user must point us at a
    # specific quad via env var. Without a manifest we cannot infer which
    # IBERT variant or which quads are present in the design.
    if not IBERT_QUAD:
        raise RuntimeError(
            "Direct mode (PROGRAMMING_FILE provided) requires IBERT_QUAD to "
            "be set to the target quad name (e.g. export IBERT_QUAD=Quad_131). "
            "In direct mode the available quads cannot be inferred from a "
            "design_manifest, so the user must specify it explicitly."
        )
    ibert_core_type = "ibert_usp_*"
    available_quads = [IBERT_QUAD]
    print(f"Direct mode: using quad {IBERT_QUAD}")

# 2) Select the quad name (user override via IBERT_QUAD, or first from manifest).
if IBERT_QUAD:
    if IBERT_QUAD not in available_quads:
        raise RuntimeError(
            f"Quad '{IBERT_QUAD}' not in manifest quads: {available_quads}"
        )
    selected_quad_name = IBERT_QUAD
    print(f"User-selected quad: {selected_quad_name}")
else:
    selected_quad_name = available_quads[0]
    print(f"Default: using first manifest quad: {selected_quad_name}")

# 3) The device may expose multiple IBERT cores (e.g. one per SLR /
#    transceiver bank). Walk them and pick the one that actually
#    contains the selected quad.
ibert = None
for idx in range(len(device.ibert_cores)):
    candidate = device.ibert_cores.at(index=idx)
    gt_names = [g.name for g in candidate.gt_groups]
    if selected_quad_name in gt_names:
        ibert = candidate
        break

if ibert is None:
    raise RuntimeError(
        f"No hardware IBERT core with quad '{selected_quad_name}' found. "
        f"Cores on device expose: "
        f"{[[g.name for g in c.gt_groups] for c in device.ibert_cores]}"
    )

# 4) Grab the GT-quad object from the live hardware that matches the
#    selected quad name.
quad = ibert.gt_groups.filter_by(name=selected_quad_name)[0]
print(f"Selected quad: {quad.name} | {quad.handle} | {quad.type}")

# %% [markdown]
# ## 9 - Create one link per channel on the selected quad
#
# The cell below bundles the TX/RX pair of every channel in `quad` into a
# `Link` object so the rest of the notebook can drive them as a unit
# (set patterns, query status, run eye scans).

# %%
links = create_links(
    txs=[gt.tx for gt in quad.gts],
    rxs=[gt.rx for gt in quad.gts],
)
print(f"Created {len(links)} links on {quad.name}")

# %% [markdown]
# ## 10 - Print the valid values for pattern and loopback, set the pattern for the TXs and RXs to "PRBS 31" and set loopback to "Near-End PMA"
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
# Eye scan step sizes - visible for user learning
EYE_SCAN_HORZ_STEP_VALUE = 8
EYE_SCAN_VERT_STEP_VALUE = 8

for eye_scan in eye_scans:
    eye_scan.params[EYE_SCAN_HORZ_STEP].value = EYE_SCAN_HORZ_STEP_VALUE
    eye_scan.params[EYE_SCAN_VERT_STEP].value = EYE_SCAN_VERT_STEP_VALUE
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
# A 2D Eye Scan helps perform margin analysis on the RX channel
# This requires Plotly to be installed. See how to install it [here](https://xilinx.github.io/chipscopy/2026.1/ibert/scan.html#scan-plots)
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

# %%
## When done with testing, close the connection
delete_session(session)
