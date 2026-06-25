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
# # ChipScoPy NoC Perfmon Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example demonstrates how to configure a Versal for taking NoC performance measurements.
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
from time import sleep
import matplotlib  # for nbconvert'd script
from chipscopy.api.noc import (
    TC_BEW,
    TC_BER,
    NoCPerfMonNodeListener,
)
from chipscopy.examples.mesa import resolve_example_design
from chipscopy.api.noc.plotting_utils import MeasurementPlot
from chipscopy import create_session, report_versions, delete_session


# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "noc_perfmon_basic"
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
versal_device = session.devices.filter_by(family=DEVICE_FAMILY).get()

if PROG_DEVICE:
    if not example_design.verify_device_idcode(versal_device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(versal_device)

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the ChipScoPy server debug cores. This brings debug cores in the ChipScoPy server online.

# %%
versal_device.discover_and_setup_cores(noc_scan=True)
print(f"Debug cores are set up and ready for use.")

# %% [markdown]
# ## 5 - Setup NoC core
#
# Ensure scan nodes are enabled in the design.

# %%
# We begin by enumerating the debug cores (hard and soft) present in the design.
# Then we ask the design for the supported timebases. And, finally:
# The NoC is scanned to determine the activated elements.

noc = versal_device.noc_core[0]

manifest_nodes = (
    design_manifest.get_core_config("noc_perfmon", "node_names", None)
    if design_manifest
    else None
)
scan_nodes = manifest_nodes or ["DDRMC_X0Y0", "NOC_NMU512_X0Y0"]
print(f"Using NoC nodes from {'design manifest' if manifest_nodes else 'defaults'}: {scan_nodes}")

print("\nEnumerating nodes: ", end="")
for node in scan_nodes:
    print(f"{node}, ", end="")
print("...", end="")

# This sets up nodes on the server side and returns the successfully enumerated nodes
enable_list = noc.enumerate_noc_elements(scan_nodes)
print("complete!")

# %%
supported_periods = noc.get_supported_sampling_periods(
    100/3, {'DDRMC_X0Y0': 800.0}
)
print("Supported sampling periods:")
for domain, periods in supported_periods.items():
    print(f"  {domain}:")
    for p in periods:
        print(f"    {p:.0f}ms", end="")
    print()

# %%
# Select Timebase and Nodes to Monitor
#
# For the two clock domains we must select a sampling period from the hardware supported values. The debug cable used will dictate how much bandwidth is available, so high frequency sampling may not actually produce data at the specified rate. Recommendation is ~500ms for jtag.
#
# Then the user must decide what to monitor--again the bandwidth is a definite consideration here. Plot performance may become the bottleneck (Optimizations will come later in the renderer or agg backend). The guidance here is to pick up to 4 nodes to monitor.

desired_period = 500  # ms
sampling_intervals = {}

for domain in supported_periods.keys():
    sampling_intervals[domain] = 0
    for sp in supported_periods[domain]:
        if sp > desired_period:
            sampling_intervals[domain] = sp
            break

    if sampling_intervals[domain] == 0:
        print(
            f"Warning, desired period {desired_period}ms is slower than "
            f"longest supported period {supported_periods[domain][-1]}ms [{domain} domain] "
            f"defaulting to this value."
        )
        sampling_intervals[domain] = supported_periods[-1]

print(f"Sampling period selection:")
for domain, freq in sampling_intervals.items():
    print(f"  {domain}: {freq:.0f}ms")

# %%
# Configure Monitors
#
# As a precaution, it's a good idea to validate the desired nodes are enabled for the design.
# Using the set of nodes and the desired sampling periods it's time to ask the service to start pushing metric data. Two additional arguments are required to this API.
#
# Traffic class
#
# This is a bit-or field of the requested traffic classes. Note, One monitor is dedicated to read traffic classes and the other to write--so all read TCs will apply to one channel and all write TCs to the other. `Best effort` is a good place to start.
#
# Number of Samples
#
# The number of samples allows for a burst of measurements to be taken and then the underlying service will tear down the monitors and stop pumping data back to the client. `-1` denotes that sampling shall continue indefinitely.

# total number of samples to capture per node.
# A finite value runs a bounded burst: the server tears down the monitors
# after the burst and the event loop below exits on its own. Use -1 for
# continuous mode (the loop then runs until the kernel is stopped).
num_samples = 50

print("Setting up monitors for: ")
for node in enable_list:
    print(node)

# When overflow occurs the precision of the monitors must be traded for range
# See the server API for more information
extended_monitor_config = {"NOC_NMU512_X0Y0": {"tslide": 0x3}}  # or None
noc.configure_monitors(
    enable_list, sampling_intervals, (TC_BEW | TC_BER), num_samples, None, extended_monitor_config
)

# %% [markdown]
# ## 7 - Create plotter and listener
#
# Attach both to running view

# %%
record_to_file = False  # True | False
node_listener = NoCPerfMonNodeListener(
    sampling_intervals,
    num_samples,
    enable_list,
    record_to_file,
    extended_monitor_config=extended_monitor_config,
)
node_listener.change_log_level('INFO')
session.chipscope_view.add_node_listener(node_listener)

# %% [markdown]
# ## 8 - Main Event Loop
#
# This loop runs until you close the plotter.
# If you are using a finite amount of measurement samples, you can uncomment the if --> break statement to automatically return from execution of this cell upon completion of the burst.

# %%
# Run Main Event Loop.
#
# In burst mode (finite `num_samples`) the server tears down all monitors once
# the first/fastest monitor has delivered its `num_samples` samples, so slower
# clock domains may receive fewer. We therefore exit as soon as ANY monitored
# node has completed its burst. In continuous mode (`num_samples = -1`) there is
# no stop condition, so the loop runs until the kernel is stopped.
loop_count = 0
while True:
    session.chipscope_view.run_events()
    sleep(0.1)
    if num_samples > 0 and any(
        node.num_samples <= 0 for node in node_listener.unique_elements.values()
    ):
        break

# %%
# Detach the perfmon listener before teardown so channel-close invalidation
# does not dispatch a blocking data-model request on the closing channel
# (which deadlocks the single TCF event-dispatch thread).
session.chipscope_view.remove_node_listener(node_listener)

delete_session(session)
