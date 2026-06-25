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
# # ChipScoPy Device Programming Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example demonstrates how to program a device using the ChipScoPy Python API.
#
# The example automatically handles both programming flows:
# - **Flat programming**: Single PDI file (e.g., VCK190, VPK120, VHK158)
# - **Segmented programming**: Boot PDI + PLD PDI with skip_reset (e.g., VEK385)
#
# The programming flow is determined by the manifest for the selected platform.
#
# ## Requirements
# - Local or remote AMD Versal board, such as a VCK190
# - AMD hw_server 2026.1 installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# MESA (`chipscopy.examples.mesa`) resolves the correct design files (PDI / LTX) for your board automatically based on `HW_PLATFORM`. To use your own design instead, set `PROGRAMMING_FILE` / `PROBES_FILE` below — that bypasses the MESA lookup.

# %%
import os
from chipscopy import create_session, report_versions, delete_session
from chipscopy.examples.mesa import resolve_example_design


# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "program"
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
# ## 2 - Create a session and connect to the hw_server
#
# The session is a container that keeps track of devices and debug cores.
#
# *NOTE*: No `cs_server` is required for this example.

# %%
session = create_session(hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
#
# This cell demonstrates both programming flows:
# - **Flat programming** (`programming_flow: "flat"`): Single PDI file using `device.program()`
# - **Segmented programming** (`programming_flow: "segmented"`): Boot PDI + PLD PDI with `skip_reset=True`
#
# The manifest determines which flow to use based on the platform.

# %%
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

if PROG_DEVICE:
    # Verify the connected device matches the manifest design before programming.
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")

    # This example shows the explicit flat / segmented programming flows so
    # users can see what each step looks like. In other notebooks we just
    # call `example_design.program_device(device)` which dispatches to the
    # correct flow based on the manifest.
    programming_file = example_design.programming_file
    programming_flow = (
        design_manifest.design_info.programming_flow if design_manifest else "flat"
    )

    if programming_flow == "flat":
        print(f"Programming with flat flow: {programming_file}")
        device.program(programming_file)
        print("Device programmed successfully (flat flow)")

    elif programming_flow == "segmented":
        # The design directory contains separate boot and PLD PDI files.
        # We find them using glob patterns from the design_manifest (or defaults).
        from pathlib import Path

        design_path = Path(programming_file).parent

        boot_pattern = (
            design_manifest.design_info.boot_pdi_pattern or "*_boot.pdi"
            if design_manifest
            else "*_boot.pdi"
        )
        boot_files = list(design_path.glob(boot_pattern))
        if not boot_files:
            raise RuntimeError(
                f"Boot PDI not found with pattern '{boot_pattern}' in {design_path}"
            )
        boot_pdi = str(boot_files[0])

        pld_pattern = (
            design_manifest.design_info.pld_pdi_pattern or "*_pld.pdi"
            if design_manifest
            else "*_pld.pdi"
        )
        pld_files = list(design_path.glob(pld_pattern))
        if not pld_files:
            raise RuntimeError(
                f"PLD PDI not found with pattern '{pld_pattern}' in {design_path}"
            )
        pld_pdi = str(pld_files[0])

        print(f"Programming with segmented flow:")
        print(f"  Step 1 - Boot PDI: {boot_pdi}")
        device.program(boot_pdi)
        print("           Boot PDI programmed")

        print(f"  Step 2 - PLD PDI:  {pld_pdi} (skip_reset=True)")
        device.program(pld_pdi, skip_reset=True)
        print("           PLD PDI programmed")
        print("Device programmed successfully (segmented flow)")

    else:
        raise ValueError(f"Unknown programming_flow: '{programming_flow}'")
else:
    print("Skipping programming")

# %%
## When done with testing, close the connection
delete_session(session)
