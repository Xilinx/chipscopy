# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2022, Xilinx, Inc.<br>
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
# # ChipScoPy VIO Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example demonstrates how to program and communicate with
# VIO (Virtual IO) cores using the ChipScoPy Python API.
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
EXAMPLE_ID = "vio"
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
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design

# %% [markdown]
# `example_design.program_device()` dispatches to the correct flow (flat vs. segmented) based on the manifest. See [program.ipynb](../program/program.ipynb) for the explicit per-flow code.

# %%
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

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
# ## 5 - Using The VIO Core
#
# The following cells demonstrate how to perform various operations with the VIO core.
# These are meant to be useful code snippets that can be copy/pasted for your own application.

# %%
# Enumerate all VIO cores in the device.
# Every VIO core has properties including a UUID and instance name.
# It is normal for this call to be slower the first time and faster in later iterations.

vio_cores = device.vio_cores
print("       UUID                              INSTANCE NAME")
for index, vio_core in enumerate(vio_cores):
    print(f"VIO-{index}  {vio_core.core_info.uuid}  {vio_core.name}")

# Choose the VIO instance we will use for the rest of the notebook.
# When running with MESA, prefer the manifest-declared instance so the same
# notebook adapts to per-platform naming differences automatically.
vio_instance = design_manifest.get_core_instance("vio", 0) if design_manifest is not None else None
if vio_instance is not None:
    vio_name = vio_instance["name"]
    vio_probe_prefix = vio_instance.get("probe_prefix", "chipscopy_i/counters/slow_counter_0")
    vio = device.vio_cores.get(name=vio_name)
else:
    vio = vio_cores[0]
    vio_probe_prefix = "chipscopy_i/counters/slow_counter_0"
counter_probe_name = f"{vio_probe_prefix}_Q"
print()
print(f"Using VIO instance: {vio.name}")
print(f"Counter probe prefix: {vio_probe_prefix}")

# %%
# Get VIO instance from design_manifest configuration
if design_manifest and design_manifest.has_core("vio"):
    vio_config = design_manifest.debug_cores["vio"]
    if hasattr(vio_config, 'core_instances') and vio_config.core_instances:
        vio_name = vio_config.core_instances[0]["name"]
        vio = device.vio_cores.get(name=vio_name)
        print(f"Using VIO from design_manifest: {vio_name}")
    else:
        vio = device.vio_cores[0]
        print(f"Using first available VIO (design_manifest did not specify instances)")
else:
    raise RuntimeError(f"VIO core not available for platform {HW_PLATFORM}")

# Get probe prefix from design_manifest for use in read/write operations
if hasattr(vio_config, 'core_instances') and vio_config.core_instances:
    probe_prefix = vio_config.core_instances[0].get("probe_prefix", "chipscopy_i/counters/slow_counter_0")
else:
    probe_prefix = "chipscopy_i/counters/slow_counter_0"

print(f"VIO: {vio.core_info.uuid}  {vio.name}")
print(f"Probe prefix: {probe_prefix}")

# You can also get a VIO core by UUID
the_vio_uuid = vio.uuid
vio_by_uuid = device.vio_cores.get(uuid=the_vio_uuid)
assert(vio == vio_by_uuid)
print("VIO lookup by name and by UUID match!")

# %%
# The VIO API knows the mapping between logical probes and ports on the VIO core.
# The code below prints the probe to port mapping.

print("VIO Port <---> Probe mapping:")
for probe in vio.probes:
    if probe.direction == "in":
        print(f"{probe.port_name} <-- {probe.probe_name}")
    else:
        print(f"{probe.port_name} --> {probe.probe_name}")

# %%
# Writing values
# Values may be written to the output ports or logical named probes.

# Writing values to a logical named probe (using probe_prefix from design_manifest):
load_probe = f"{probe_prefix}_L"
vio.write_probes({
    load_probe: 0x12345678
})
print(f"Wrote 0x12345678 to {load_probe}")

# Writing a value to the same VIO through its port name.
vio.write_ports({
    "probe_out4": 0x11223344
})
print("Wrote 0x11223344 to probe_out4")

# %%
# Reading VIO probe values
# Probes are the logical names mapped to VIO ports in the LTX file.

vio.reset_vio()

# Derive the counter output probe name from the design_manifest probe_prefix
counter_probe = f"{probe_prefix}_Q"

# Reading all probes at once and extracting one of interest returns a dictionary of probe data.
#   value is returned as an integer
#   activity is a string, one activity per bit: N=None, R=Rising, F=Falling, B=Both
all_probe_info = vio.read_probes()
value = all_probe_info[counter_probe]["value"]
activity = all_probe_info[counter_probe]["activity"]
print(f"Counter Value: {value}, Activity: {activity}")

# Reading from a single named logical probe.
# For convenience, you can ask specifically for one or more probes to reduce the data size.
# The returned dictionary format is the same.
one_probe_info = vio.read_probes(counter_probe)
value = one_probe_info[counter_probe]["value"]
activity = one_probe_info[counter_probe]["activity"]
print(f"Counter Value: {value}, Activity: {activity}")

# Reading the same value directly from the VIO port "probe_in0" mapped to the same counter.
port_info = vio.read_ports("probe_in0")
value = port_info["probe_in0"]["value"]
activity = port_info["probe_in0"]["activity"]
print(f"Counter Value: {value}, Activity: {activity}")

# %%
# Reading probe values is often the quickest way to confirm the design is alive.

# %%
# Resetting the VIO core resets all output values to their default.
# Default values were optionally set during implementation as a property on the VIO IP.

vio.reset_vio()
print(f"VIO core {vio.name} reset to initial values.")

# %%
# You can access low level VIO properties as a dictionary or in json.
# This gives easy python access to probe and port information.

import pprint
pp = pprint.PrettyPrinter(indent=4)

vio_dict = vio.to_dict()
pp.pprint(vio_dict)

# %%
# The VIO properties can also be accessed as JSON.
# This is convenient when interfacing with other languages.
vio_json = vio.to_json()
print(vio_json)

# %%
## When done with testing, close the connection
delete_session(session)
