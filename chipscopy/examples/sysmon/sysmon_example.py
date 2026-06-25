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
# # ChipScoPy System Monitor Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
#
#
# This demo shows how to take, display, and review measurements with the System Monitor.
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
import time
from chipscopy import __version__, dm
from chipscopy.examples.mesa import resolve_example_design
from chipscopy import create_session, report_versions, delete_session


# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "sysmon_example"
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

# Refer program example to understand how segmented PDI programming is supported by device.program API.

if PROG_DEVICE:
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the ChipScoPy server debug cores. This brings debug cores in the ChipScoPy server online.

# %%
device.discover_and_setup_cores(sysmon_scan=True)
print(f"System monitor is set up and ready for use.")

# %% [markdown]
# ## 5 - Initialize System Monitor
#
# Get reference to the system monitor and initialize all sensors.

# %%
sysmon = device.sysmon_root[0]

print("Initializing sensors")
active_nodes = sysmon.initialize_sensors()

print("Refresh measurement schedule")
schedule = sysmon.refresh_measurement_schedule()

print("Sensors:")
for sensor in schedule.values():
    print(f"  {sensor}")

print("Done.")


# %% [markdown]
# ## 6 - Register a listener for System Monitor Events
#
# The SysMonNodeListener node_changed() will be called every 1000ms with updated system monitor values.

# %%
class SysMonNodeListener(dm.NodeListener):
    def node_changed(self, node, updated_keys):
        if "device_temp" in node.props:
            print(f"Device Temp: {node.props['device_temp']}")
        for supply_idx, named_sensor in schedule.items():
            supply = f"supply{supply_idx}"
            if supply in node.props:
                print(f"{named_sensor}: {node.props[supply]}")
        print()


node_listener = SysMonNodeListener()
session.chipscope_view.add_node_listener(node_listener)

sysmon.stream_sensor_data(1000)
print("Node listener added.")

# %% [markdown]
# ## 7 - Run measurement for 5 seconds
#
# System Monitor will report results for 5 seconds then exit.

# %%
# Take measurements for 5 seconds then exit.

time_end = time.time() + 5

while time.time() < time_end:
    session.chipscope_view.run_events()
    time.sleep(0.1)

print("Measurement done.")

# %% [markdown]
# ## 8 - Stop streaming and clean up
#
# Stopping the sensor data stream and removing our node listener before
# closing the session avoids a deadlock in `delete_session` on some
# platforms, where a still-active stream keeps producing events for a
# listener that is being torn down.

# %%
sysmon.stream_sensor_data(0)
session.chipscope_view.remove_node_listener(node_listener)

delete_session(session)

