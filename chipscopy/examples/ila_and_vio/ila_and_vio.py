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
# # ChipScoPy ILA and VIO Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example demonstrates how to program and communicate with ILA (Integrated Logic Analyzer) and
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
import sys
from chipscopy import create_session, report_versions, delete_session
from chipscopy.examples.mesa import resolve_example_design

# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "ila_and_vio"
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
# Debug core discovery brings ILA / VIO cores in the device online via `cs_server`.

# %%
device.discover_and_setup_cores(ltx_file=PROBES_FILE)
print(f"Debug cores are set up and ready for use.")

# %%
# Print out the ILA core instance UUIDs and instance names
ila_cores = device.ila_cores
for index, ila_core in enumerate(ila_cores):
    print(f"{index} - {ila_core.core_info.uuid}   {ila_core.name}")

# %%
# Print out the VIO core instance UUIDs and instance names
vio_cores = device.vio_cores
for index, vio_core in enumerate(vio_cores):
    print(f"{index} - {vio_core.core_info.uuid}   {vio_core.name}")

# %% [markdown]
# ## 5 - VIO Control and ILA Capture
#
# ILA and VIO are two important building blocks for debugging applications in hardware.
# This example design design shows how to control IP using a VIO core and capture results with ILA.
#
# In this Design,
# - A VIO core controls the counter (reset, up/down, ce, load)
# - An ILA core captures the counter values
#

# %% [markdown]
# <img src="img/capture_data.png" width="400" align="left">

# %%
# Get ILA instance from design_manifest if available, otherwise use first available
if design_manifest and design_manifest.has_core("ila"):
    ila_config = design_manifest.debug_cores["ila"]
    if hasattr(ila_config, 'core_instances') and ila_config.core_instances:
        ila_name = ila_config.core_instances[0]["name"]
        ila = device.ila_cores.get(name=ila_name)
        print(f"Using ILA from design_manifest: {ila_name}")
    else:
        ila = device.ila_cores[0] if device.ila_cores else None
        print(f"Using first available ILA")
else:
    ila = device.ila_cores[0] if device.ila_cores else None
    print(f"Using first available ILA")

# Get VIO instance from design_manifest if available
if design_manifest and design_manifest.has_core("vio"):
    vio_config = design_manifest.debug_cores["vio"]
    if hasattr(vio_config, 'core_instances') and vio_config.core_instances:
        vio_name = vio_config.core_instances[0]["name"]
        vio = device.vio_cores.get(name=vio_name)
        print(f"Using VIO from design_manifest: {vio_name}")
    else:
        vio = device.vio_cores[0] if device.vio_cores else None
        print(f"Using first available VIO")
else:
    vio = device.vio_cores[0] if device.vio_cores else None
    print(f"Using first available VIO")

if ila:
    print(f"ILA: {ila.core_info.uuid}  {ila.name}")
if vio:
    print(f"VIO: {vio.core_info.uuid}  {vio.name}")

# %% [markdown]
# ### 5a - Configure the counter using VIO output probes
#
# <img src="img/vio_control_counter.png" width="300" align="left">

# %%
# Print all the VIO port and probe names. This is convenient to know which probes are connected to
# VIO ports. Also verifies probe names to pass to other functions.

print("VIO Port <---> Probe mapping:")
for probe in vio.probes:
    if probe.direction == "in":
        print(f"{probe.port_name} <-- {probe.probe_name}")
    else:
        print(f"{probe.port_name} --> {probe.probe_name}")

# %%
# Probe names match the Vivado hierarchy in your LTX file.
# To list available probes for your own design:
#     print([p.probe_name for p in ila.probes])
ila_probe_prefix = "chipscopy_i/counters/slow_counter_0"
vio_probe_prefix = "chipscopy_i/counters/slow_counter_0"

if design_manifest and design_manifest.has_core("ila") and hasattr(design_manifest.debug_cores["ila"], 'core_instances') and design_manifest.debug_cores["ila"].core_instances:
    ila_probe_prefix = design_manifest.debug_cores["ila"].core_instances[0].get("probe_prefix", ila_probe_prefix)

if design_manifest and design_manifest.has_core("vio") and hasattr(design_manifest.debug_cores["vio"], 'core_instances') and design_manifest.debug_cores["vio"].core_instances:
    vio_probe_prefix = design_manifest.debug_cores["vio"].core_instances[0].get("probe_prefix", vio_probe_prefix)

# Set up the VIO core to enable counting up from 0
vio.reset_vio()
vio.write_probes(
    {
        f"{vio_probe_prefix}_SCLR": 0,
        f"{vio_probe_prefix}_L": 0x00000000,
        f"{vio_probe_prefix}_LOAD": 0,
        f"{vio_probe_prefix}_UP": 1,
        f"{vio_probe_prefix}_CE": 1,
    }
)
print("Counter is now free-running and counting up")

# %% [markdown]
# ### 5b - Capture and display free-running counter using the ILA core
#
# <img src="img/free_running_counter.png" width="350" align="left">

# %%
# Trigger ILA on the free running counter. Trigger set to the first time we see 0s in low 16-bits.
# This will show the counter is free running, and counting up

ila.reset_probes()
ila.set_probe_trigger_value(f"{ila_probe_prefix}_Q_1", ["==", "0xXXXX_0000"])
ila.run_basic_trigger(window_count=1, window_size=32, trigger_position=16)
print("ILA is running - looking for trigger")

# %%
# Wait for the ILA trigger with upload.
# Then print the captured ILA samples and mark the trigger position.

ila.wait_till_done(max_wait_minutes=0.1)
upload_successful = ila.upload()
if upload_successful:
    #
    # ila.waveform.get_data() returns data for probes. By default, all probes are included. But here we specify 
    #     slow_counter_0_Q_1 so only the one probe data is returned.
    #
    samples = ila.waveform.get_data(
        [f"{ila_probe_prefix}_Q_1"],
        include_trigger=True,
        include_sample_info=True,
    )
    # Below is a convenient way to iterate over all probe values using a for loop.
    #
    # samples.values() is a list of lists including trigger, sample_index, window_index, window_sample_index, 
    #     and any probes in samples from get_data() above. 
    #
    # for trigger, sample_index, window_index, window_sample_index, probe0, probe1, ..., probeN in zip(*samples.values())
    #
    for trigger, sample_index, window_index, window_sample_index, slow_counter_0_Q_1 in zip(*samples.values()):
        trigger = "<-- Trigger" if trigger else ""
        print(
            f"Window:{window_index}  Window Sample:{window_sample_index}  {slow_counter_0_Q_1:10}  0x{slow_counter_0_Q_1:08X} {trigger}"
        )
else:
    print("Failed to upload ILA data from core")

# %% [markdown]
# ### 5c - Trigger ILA using VIO Up/Down virtual switch
#
# This step demonstrates how VIO and ILA can be combined to form powerful debug building blocks.
#
# ILA is set to trigger when UP/DOWN counter signal edge rises or falls.
# VIO drives the UP/DOWN counter control signal to 0 causing the counter to count down.
# The signal transition causes ILA to trigger and capture data.

# %% [markdown]
# <img src="img/edge_trigger.png" width="550" align="left">

# %%
# Set ILA core to capture on a transition of the UP/DOWN toggle switch
# Once transition happens, trigger in the middle of the buffer.

ila.reset_probes()
ila.set_probe_trigger_value(f"{ila_probe_prefix}_UP_1", ["==", "B"])
ila.run_basic_trigger(window_count=1, window_size=32, trigger_position=16)

print("ILA is running - looking for trigger")

# %%
# VIO: Turn counter up/down switch to DOWN position.
# This will cause the running ILA to trigger on the transition edge from up to down.

vio.write_probes({f"{vio_probe_prefix}_UP": 0})

print("VIO changed up/down counter to count down")

# %%
# Print the captured ILA samples and mark the trigger position.
# Note that counter counts down after the trigger mark.

ila.wait_till_done(max_wait_minutes=0.1)
upload_successful = ila.upload()
if upload_successful:
    samples = ila.waveform.get_data(
        [f"{ila_probe_prefix}_Q_1"],
        include_trigger=True,
        include_sample_info=True,
    )
    for trigger, sample_index, window_index, window_sample_index, slow_counter_0_Q_1 in zip(*samples.values()):
        trigger = "<-- Trigger" if trigger else ""
        print(
            f"Window:{window_index}  Window Sample:{window_sample_index}  {slow_counter_0_Q_1:10}  0x{slow_counter_0_Q_1:08X} {trigger}"
        )
else:
    print("Failed to upload ILA data from core")

# %% [markdown]
# ## 6 - Waveform Export - VCD (or CSV)
#
#  Demonstrate how to export waveform data to a VCD file for visualizing waveform in other tools.
#
#  Export includes complete waveform with probe, _TRIGGER, and _WINDOW.
#
#  - For CSV export, substitute "CSV" for "VCD" argument.
#  - To export to a file, substitute the filename for 'sys.stdout'

# %%
if upload_successful:
    ila.waveform.export_waveform("VCD", sys.stdout)

# %%
## When done with testing, close the connection
delete_session(session)
