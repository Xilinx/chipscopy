# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright 2021 Xilinx, Inc.<br><br>
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
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 installed and running
# - Xilinx cs_server 2022.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2022.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - URL paths are set correctly
# - File paths to example files are set correctly

# %%
import os
import time
from chipscopy import get_design_files
from chipscopy import __version__, dm
from chipscopy import create_session, report_versions

# %%
# Make sure to start the hw_server and cs_server prior to running.
# Specify locations of the running hw_server and cs_server below.
# The default is localhost - but can be other locations on the network.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files("vck190/production/chipscopy_ced")

PROGRAMMING_FILE = design_files.programming_file
PROBES_FILE = design_files.probes_file

print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")
print(f"PROGRAMMING_FILE: {PROGRAMMING_FILE}")
print(f"PROBES_FILE:{PROBES_FILE}")

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
device.program(PROGRAMMING_FILE)

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - The cs_server is initialized and ready for use

# %%
device.discover_and_setup_cores(sysmon_scan=True)
print(f"System monitor setup and ready for use.")

# %% [markdown]
# ## 5 - Initialize System Monitor
#
# Get reference to the system monitor and initialize all sensors.

# %%
sysmon = device.sysmon_root.get()

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
