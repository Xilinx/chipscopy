# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2021-2022, Xilinx, Inc.
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
# # ChipScoPy DDR 2D Eye Margin Scan Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This demo shows how to exercise and run Versal DDRMC 2D Margin Scan features
#
#
# ## Requirements
# - Local or remote AMD Versal board, such as a VCK190
# - AMD hw_server 2026.1 installed and running
# - AMD cs_server 2026.1 installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths

# %%
import sys
import os
import pprint
import chipscopy
from chipscopy import create_session, delete_session, report_versions
from chipscopy.examples.mesa import Manifest, resolve_example_design

_ddr_dir = os.path.join(os.path.dirname(chipscopy.__file__), "examples", "ddr")
if _ddr_dir not in sys.path:
    sys.path.insert(0, _ddr_dir)
from ddr_scan_util import convert_vref_pct_to_code

# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "ddr_2d_eye_scan"
PROG_DEVICE = True

# Direct mode: set these to use your own design files (skips MESA).
PROGRAMMING_FILE = ""
PROBES_FILE = ""

# ============================================================

# --- MESA setup (no edits needed below) ---

# Look up the example design that matches HW_PLATFORM + EXAMPLE_ID. If
# PROGRAMMING_FILE / PROBES_FILE were set above ("direct mode"), MESA is
# bypassed and those paths are used as-is.
example_design = resolve_example_design(
    HW_PLATFORM,
    EXAMPLE_ID,
    programming_file=PROGRAMMING_FILE,
    probes_file=PROBES_FILE,
)

# Pull the resolved files / metadata back out into the names the rest of
# the notebook expects. `design_manifest` is None when running in direct
# mode (no MESA entry was matched).
design_manifest = example_design.manifest  # None in direct mode
DEVICE_FAMILY = example_design.device_family       # e.g. "versal"
PROGRAMMING_FILE = example_design.programming_file # absolute path to .pdi
PROBES_FILE = example_design.probes_file           # absolute path to .ltx (or empty)

example_design.print_summary()
print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")

# %%
# When MESA is in use, the manifest tells us up front which features the
# example design supports for each debug core. Bail out early if 2D eye
# scan is not enabled for this board so the rest of the notebook does not
# fail later with a less-helpful error.
if design_manifest and not design_manifest.has_feature("memory", "2d_eye_scan"):
    # The trailing conditional just falls back to "N/A" if the design
    # has no memory core at all, so the error message is still useful.
    raise RuntimeError(
        f"Platform '{HW_PLATFORM}' does not support 2d_eye_scan for memory. "
        f"Available memory features: {design_manifest.debug_cores['memory'].features if design_manifest.has_core('memory') else 'N/A'}"
    )
print(f"2D eye scan feature confirmed for platform: {HW_PLATFORM}")

# ----------------------------------------------------------------------
# Eye-scan parameters. Tweak these to control which interface / mode the
# scan runs against.
# ----------------------------------------------------------------------

# DDRMC instance to scan. A Versal device can have up to 4 DDR memory
# controllers (DDRMC_X0Y0..DDRMC_X0Y3); 0 picks the first one. Leave at 0
# unless your design enables more than one controller and you want a
# specific one.
DDR_INDEX = 0

# Rank within the DIMM / memory interface. Single-rank parts only have
# rank 0; dual-rank DIMMs expose rank 0 and rank 1 separately.
RANK = 0

# Direction of the eye scan:
#   "READ"  - margin the controller-side RX data eye (memory -> SoC).
#   "WRITE" - margin the memory-side RX data eye (SoC -> memory).
MARGIN_MODE = "READ"

# Traffic pattern run during the scan:
#   "SIMPLE"  - PRBS / walking-1 style; fast, less stressful.
#   "COMPLEX" - data-bus-inversion / crosstalk-heavy patterns; slower
#               but reproduces system-level noise more accurately.
DATA_PATTERN = "COMPLEX"

# Vref sweep range in percent of supply (see step 9 for what Vref is).
# Leaving these at 25 / 50 lets the next cell auto-adjust them based on
# the detected DDR type. Override with explicit values to skip the
# auto-adjust.
#   Recommended ranges:
#     DDR4 READ  : 25-50    DDR4 WRITE : 60-90
#     LPDDR4 READ:  5-35    LPDDR4 WRITE: 10-30
VREF_PCT_MIN = 25
VREF_PCT_MAX = 50

# Number of Vref steps the scan will take across [VREF_PCT_MIN, VREF_PCT_MAX].
# More steps = finer vertical eye resolution, but ~1 second per step.
STEPS = 15

# Which slice of the bus to plot at the end:
#   READ  mode -> nibble  index (4 bits per nibble)
#   WRITE mode -> byte-lane index (8 bits per byte lane)
DISPLAY_INDEX = 1

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.

# %%
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design

# %% [markdown]
# `example_design.program_device()` dispatches to the correct flow (flat vs. segmented) based on the manifest. See [program.ipynb](../program/program.ipynb) for the explicit per-flow code.

# %%
# Get device using family from manifest
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

# Program device using manifest (handles both flat and segmented flows)

if PROG_DEVICE:
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the ChipScoPy server debug cores. This brings debug cores in the ChipScoPy server online.

# %%
device.discover_and_setup_cores(ltx_file=PROBES_FILE)
print(f"Debug cores are set up and ready for use.")

# %% [markdown]
# ## 5 - Get a list of the integrated DDR Memory Controllers

# %%
ddr_list = device.ddrs
print(f"{len(ddr_list)} integrated DDRMC cores exist on this device.\n")

enabled_ddrs = []
print(f"{'Index':<6} {'Enabled':<9} {'Type':<10} {'Cal Status'}")
print("-" * 40)
for ddr_node in ddr_list:
    if ddr_node.is_enabled:
        mem_type_val = ddr_node.ddr_node.get_property(["mem_type"])["mem_type"]
        detected_type = Manifest.get_mem_type_name(mem_type_val)
        cal_status = ddr_node.get_cal_status()
        print(f"{ddr_node.mc_index:<6} {'Yes':<9} {detected_type:<10} {cal_status}")
        enabled_ddrs.append({"ddr": ddr_node, "type": detected_type, "index": int(ddr_node.mc_index)})
    else:
        print(f"{ddr_node.mc_index:<6} {'No':<9} {'N/A':<10} N/A")

if not enabled_ddrs:
    raise RuntimeError("No enabled DDR controllers found")

# Validate detected DDR types against design_manifest memory_types.
# In direct mode (no manifest) we have nothing to compare against, so we skip
# the cross-check and continue with whatever the device reports.
manifest_types = (
    design_manifest.debug_cores["memory"].memory_types
    if (design_manifest is not None and design_manifest.has_core("memory"))
    else []
)
if manifest_types:
    detected_types = set(d["type"] for d in enabled_ddrs)
    for dt in detected_types:
        if dt not in manifest_types:
            print(f"\nWARNING: Device has {dt} but design_manifest expects {manifest_types}")
    print(f"\nManifest memory_types: {manifest_types}")

# Auto-select first enabled DDR if DDR_INDEX was not overridden
if DDR_INDEX == 0:
    DDR_INDEX = enabled_ddrs[0]["index"]
print(f"\nSelected DDRMC index: {DDR_INDEX}")

# %% [markdown]
# ## 6- Select a target DDR by index and display calibration status

# %%
ddr = ddr_list[DDR_INDEX]
props = ddr.ddr_node.get_property(["cal_status"])
cal_status = props['cal_status']
print(f"Calibration status of DDRMC instance {DDR_INDEX} is {cal_status}")
if cal_status != "PASS":
    print(f"The DDR controller at index {DDR_INDEX} is not in use")
    delete_session(session)
    exit()

# Detect DDR type and adapt VREF defaults if user hasn't overridden them
detected_mem_type = ddr.ddr_node.get_property(["mem_type"])["mem_type"]
detected_type_name = Manifest.get_mem_type_name(detected_mem_type)
print(f"Detected memory type: {detected_type_name}")

VREF_DEFAULTS = {
    "DDR4":   {"READ": (25, 50), "WRITE": (60, 90)},
    "LPDDR4": {"READ": (5, 35),  "WRITE": (10, 30)},
}

if detected_type_name in VREF_DEFAULTS:
    defaults = VREF_DEFAULTS[detected_type_name]
    rec_min, rec_max = defaults.get(MARGIN_MODE, (VREF_PCT_MIN, VREF_PCT_MAX))
    if VREF_PCT_MIN == 25 and VREF_PCT_MAX == 50:
        VREF_PCT_MIN, VREF_PCT_MAX = rec_min, rec_max
        print(f"Auto-adjusted VREF range for {detected_type_name} {MARGIN_MODE}: {VREF_PCT_MIN}% - {VREF_PCT_MAX}%")
    else:
        print(f"Using user-specified VREF range: {VREF_PCT_MIN}% - {VREF_PCT_MAX}%")
        print(f"  (Recommended for {detected_type_name} {MARGIN_MODE}: {rec_min}% - {rec_max}%)")
else:
    print(f"No VREF defaults for {detected_type_name}, using specified: {VREF_PCT_MIN}% - {VREF_PCT_MAX}%")

# %%
## Initialize and activate the Margin Check feature in the DDRMC
ddr.ddr_node.set_property({"mgchk_enable": 1})
ddr.ddr_node.commit_property_group([])
ddr.ddr_node.set_property({"mgchk_enable": 0})
ddr.ddr_node.commit_property_group([])
print("Initialization complete.")

# %% [markdown]
# ## 7 - Setting the 2D eye scan read or write mode

# %%
if MARGIN_MODE == "READ":
    print("Setting 2D eye for READ margin")
    ddr.set_eye_scan_read_mode()
elif MARGIN_MODE == "WRITE":
    print("Setting 2D eye for WRITE margin")
    ddr.set_eye_scan_write_mode()
else:
    print(
        f" ERROR: MARGIN_MODE is set to {MARGIN_MODE} which is an illegal value, only READ or WRITE is allowed"
    )

# %% [markdown]
# ## 8 - Setting the 2D eye scan data pattern mode

# %%
if DATA_PATTERN == "SIMPLE":
    print("Setting 2D eye for SIMPLE data pattern")
    ddr.set_eye_scan_simple_pattern()
elif DATA_PATTERN == "COMPLEX":
    print("Setting 2D eye for COMPLEX data pattern")
    ddr.set_eye_scan_complex_pattern()
else:
    print(
        f" ERROR: DATA_PATTERN is set to {DATA_PATTERN} which is an illegal value, only SIMPLE or COMPLEX is allowed"
    )

# %% [markdown]
# ## 9 - Setting the Vref sample min/max range
#
# **What is Vref?** Vref is the *reference voltage* the receiver uses to
# decide whether each data bit is a 1 or a 0. The receiver compares the
# incoming signal against Vref; values above Vref are sampled as 1, values
# below are sampled as 0. Vref is expressed as a percentage of the I/O
# supply (e.g. 50% ≈ mid-rail).
#
# **Why do we sweep it?** A 2D eye scan margins the data eye in *both*
# axes: time (delay) on the horizontal axis, and Vref on the vertical axis.
# Sweeping Vref between `VREF_PCT_MIN` and `VREF_PCT_MAX` traces out how
# much vertical voltage margin the receiver has at each delay step — i.e.
# the height of the eye. Different memory technologies live in different
# Vref windows (DDR4 reads sit near 50%; LPDDR4 reads sit much lower), so
# the range is technology-specific. Step 5 already auto-adjusted these for
# the detected DDR type when the defaults (25 / 50) were left in place.

# %%
# The scan engine programs Vref as a hardware *code* (an integer DAC
# setting), not as a percentage. `convert_vref_pct_to_code` translates
# the percent values from step 5 into the codes the DDRMC expects, using
# tables that depend on the memory type and on READ vs. WRITE.
print("Vref Min setting...")
vref_min_code = convert_vref_pct_to_code(ddr, MARGIN_MODE, VREF_PCT_MIN)
print("Vref Max setting...")
vref_max_code = convert_vref_pct_to_code(ddr, MARGIN_MODE, VREF_PCT_MAX)

# Tell the DDRMC the vertical bounds of the 2D scan and how many discrete
# Vref points to capture between them.
ddr.set_eye_scan_vref_min(vref_min_code)
ddr.set_eye_scan_vref_max(vref_max_code)
ddr.set_eye_scan_vref_steps(STEPS)
print(f"Dividing the Vref range into {STEPS} steps")

# %% [markdown]
# ## 10 - Run 2D Margin Scan after settings

# %%
ddr.run_eye_scan()

# %% [markdown]
# ## 11 - Display Scan Plots by a given Unit(nibble/byte) index
#
# You can display static or dynamic plots. The display_type controls the display output.
# - "static" is a simple image that can be saved.
# - "dynamic" is an interactive javascript plot.
# - The default is "dynamic" if nothing is specified.

# %%
"""Display a figure in both Jupyter and command-line environments"""
from IPython import get_ipython
if get_ipython() is not None and hasattr(get_ipython(), 'kernel'):
    from IPython.display import Image, display
    display_type = "static"  # best for jupyter notebook
else:
    display_type = "dynamic"  # best for terminal

ddr.display_eye_scan(DISPLAY_INDEX, display_type=display_type)

# %% [markdown]
# Optionally you can return figures as a list for later operations.

# %%
figs = ddr.display_eye_scan(DISPLAY_INDEX + 1, return_as_list=True)

# %% [markdown]
# The following loop demonstrates how you can display the graphs from a list created previously.
# It is easy to display interactive or static images.
#
# Here we get the list of figures and output them to png format.

# %%
from IPython.display import Image, display

for fig in figs:
    # To display interactive images, uncomment the following line:
    # fig.show()

    # To display a static png image:
    image_bytes = fig.to_image(format="png")
    ipython_image = Image(image_bytes)
    display(ipython_image)

# %% [markdown]
# ## 12 - Save the Eye Scan data from latest run

# %%
ddr.save_eye_scan_data("myoutput.csv")

# %% [markdown]
# ## 13 - Load Eye Scan data from a given data file

# %%
ddr.load_eye_scan_data("myoutput.csv")

# %% [markdown]
# ## 14 - Review overall Scan status and Control group detail from latest run

# %%
props = ddr.ddr_node.get_property_group(["eye_scan_stat", "eye_scan_ctrl"])
print(pprint.pformat(props, indent=2))

# %% [markdown]
# ## 15 - (Optional) Report Full DDR config and calibration/margin Info

# %%
# (uncomment to see report)
# ddr.report()

# %%
## When done with testing, close the connection
delete_session(session)
