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
# # ChipScoPy System Monitor Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
#
#
# This demo shows how to take and display measurements with the System Monitor.
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
EXAMPLE_ID = "sysmon_sync_example"
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
device.discover_and_setup_cores(sysmon_scan=True, ddr_scan=False)
print(f"System monitor is set up and ready for use.")

# %% [markdown]
# ## 5 - Initialize System Monitor
#
# Get reference to the system monitor and initialize all sensors.
# grab the measurement schedule

# %%
sysmon = device.sysmon_root[0]

print("Initializing sensors")
active_nodes = sysmon.initialize_sensors()

print("Refresh measurement schedule")
schedule = sysmon.refresh_measurement_schedule()

print("Sensor Schedule:")
for sensor in schedule.values():
    print(f"  {sensor}")
print()

# %% [markdown]
# ## 6 - Refresh values from hardware
#
# Perform individual sensor read

# %%
# Verify this design supports synchronous sampling before proceeding
if design_manifest and not design_manifest.has_feature("sysmon", "synchronous_sampling"):
    raise RuntimeError(
        f"Platform '{HW_PLATFORM}' does not support synchronous_sampling for sysmon. "
        f"Available sysmon features: {design_manifest.debug_cores['sysmon'].features if design_manifest and design_manifest.has_core('sysmon') else 'N/A'}"
    )
print(f"Synchronous sampling feature confirmed for platform: {HW_PLATFORM}")

sensor_to_read = 'VCCAUX'
current_value = sysmon.read_sensor(sensor_to_read)
print(f"\nIndividual sensor read of {sensor_to_read}")
print(f'->{sensor_to_read}: {current_value:.3f}V')
print()

# %% [markdown]
# ## 7 - Run measurement for 5 seconds
#
# Grab samples once a second for 5 seconds then exit.

# %%
# Take measurements for 5 seconds then exit.
print("Group of sensors read")
sensors_to_read = ['VCC_PMC', 'VCC_PSLP', 'VCC_PSFP', 'VCC_SOC']
for x in range(5):
    current_sensor_values = sysmon.read_sensors(sensors_to_read)
    for sensor, value in current_sensor_values.items():
        print(f'  {sensor}: {value:.3f}V')
    temps = sysmon.read_temp()
    for temp, value in temps.items():
        print(f'  {temp}: {value:.1f}' + u"\u00b0C")
    print()
    time.sleep(1)


print("Measurement done.")

# %%
## When done with testing, close the connection
delete_session(session)
