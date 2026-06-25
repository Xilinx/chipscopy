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
# - Local or remote AMD Versal board, such as a VCK190
# - AMD hw_server 2026.1 installed and running
# - AMD cs_server 2026.1 installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths

# %%
import pprint
import os
import json
from chipscopy import create_session, report_versions, delete_session
from chipscopy.examples.mesa import Manifest, resolve_example_design

# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "ddr_example"
PROG_DEVICE = True

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
# Start of the connection
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design

# %% [markdown]
# `example_design.program_device()` dispatches to the correct flow (flat vs. segmented) based on the manifest. See [program.ipynb](../program/program.ipynb) for the explicit per-flow code.

# %%
# Get device using family from example_design
versal_device = session.devices.filter_by(family=DEVICE_FAMILY).get()

# Program device via example_design.program_device(). It dispatches to the right
# flat or segmented programming flow based on the manifest.
if PROG_DEVICE:
    if not example_design.verify_device_idcode(versal_device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(versal_device)
else:
    print("Skipping programming")

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery brings ChipScoPy server debug cores online.

# %%
versal_device.discover_and_setup_cores()
print(f"Debug cores are set up and ready for use.")

# %% [markdown]
# ## 5 - Show enabled DDRs in the device. Pick one to use

# %%
# Enumerate every DDR controller the device exposes, print a one-line
# status table (index / name / enabled / memory type / calibration), and
# collect the enabled ones into `enabled_ddrs` for the rest of the notebook.
ddr_list = versal_device.ddrs
enabled_ddrs = []

print(f"{'Index':<6} {'Name':<30} {'Enabled':<9} {'Type':<10} {'Cal Status'}")
print("-" * 75)
for ddr_node in ddr_list:
    if ddr_node.is_enabled:
        mem_type_val = ddr_node.ddr_node.get_property(["mem_type"])["mem_type"]
        detected_type = Manifest.get_mem_type_name(mem_type_val)
        cal_status = ddr_node.get_cal_status()
        print(f"{ddr_node.mc_index:<6} {ddr_node.name:<30} {'Yes':<9} {detected_type:<10} {cal_status}")
        enabled_ddrs.append({"ddr": ddr_node, "type": detected_type, "cal": cal_status})
    else:
        print(f"{ddr_node.mc_index:<6} {ddr_node.name:<30} {'No':<9} {'N/A':<10} N/A")

if not enabled_ddrs:
    raise RuntimeError("No enabled DDR controllers found on this device")

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

print(f"\nFound {len(enabled_ddrs)} enabled DDR controller(s)")

# %% [markdown]
# ## 6 - Select DDR controller(s)
#
# Set `DDR_INDEX` to a specific index to target one controller, or leave as `"all"` to iterate over every enabled DDRMC.

# %%
# User selection: set to integer index for a specific DDRMC, or "all" for every enabled one
DDR_INDEX = "all"

if DDR_INDEX == "all":
    selected_ddrs = enabled_ddrs
    print(f"Running calibration report on ALL {len(selected_ddrs)} enabled DDR controller(s)")
else:
    idx = int(DDR_INDEX)
    target = [d for d in enabled_ddrs if int(d["ddr"].mc_index) == idx]
    if not target:
        raise RuntimeError(f"DDR index {idx} is not enabled. Enabled indices: {[int(d['ddr'].mc_index) for d in enabled_ddrs]}")
    selected_ddrs = target
    print(f"Running calibration report on DDR index {idx}")

# %% [markdown]
# ## 7 - Getting the Calibration Status
#
# There are several methods available to collect memory calibration information.
# The following cells demonstrate each method on the selected DDR controller(s).

# %% [markdown]
# ### Method 1 - Calibration PASS/FAIL status for each DDR

# %%
for entry in selected_ddrs:
    ddr = entry["ddr"]
    print(f"\n{'='*60}")
    print(f"DDRMC {ddr.mc_index} ({ddr.name}) - Type: {entry['type']}")
    print(f"{'='*60}")
    print(f"  Calibration status: {ddr.get_cal_status()}")

# %% [markdown]
# ### Method 2 - Detailed calibration stages for each DDR

# %%
for entry in selected_ddrs:
    ddr = entry["ddr"]
    print(f"\n{'='*60}")
    print(f"DDRMC {ddr.mc_index} - Calibration Stages")
    print(f"{'='*60}")
    props = ddr.get_cal_stages()
    print(pprint.pformat(sorted(props.items()), indent=2))

# %% [markdown]
# ## 8 - Generate Full DDRMC Report for each DDR
#
# The report() API call creates a full DDRMC status report to stdout or a file. This report includes memory configuration, margin analysis, calibration, and health status information.

# %%
for entry in selected_ddrs:
    ddr = entry["ddr"]
    report_file = f"ddr_report_mc{ddr.mc_index}.txt"
    print(f"\n{'='*60}")
    print(f"Full Report: DDRMC {ddr.mc_index} ({entry['type']})")
    print(f"{'='*60}")
    ddr.report()
    ddr.report(True, report_file)
    print(f"Report saved to {report_file}\n")

# %% [markdown]
# ## 9 - Dump the complete set of internal properties as JSON
#
# This demonstrates how to get a Python dictionary of all the low level DDR properties. These can be converted to JSON easily for export to other tools.

# %%
for entry in selected_ddrs:
    ddr = entry["ddr"]
    print(f"\n{'='*60}")
    print(f"Properties: DDRMC {ddr.mc_index} ({entry['type']})")
    print(f"{'='*60}")
    props = ddr.ddr_node.get_property_group([])
    json_props = json.dumps(props, indent=4)
    print(json_props)

# %%
## When done with testing, close the connection
delete_session(session)
