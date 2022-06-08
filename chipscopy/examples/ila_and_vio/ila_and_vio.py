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
import sys
import os
from chipscopy import get_design_files
from chipscopy import create_session, report_versions
from chipscopy.api.ila import get_waveform_data, export_waveform

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
# - ILA and VIO core instances in the device are reported

# %%
device.discover_and_setup_cores(ltx_file=PROBES_FILE)
print(f"Debug cores setup and ready for use.")

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
# Grab the two cores we are interested in for the demonstration
# As shown above, a counter is connected to the ILA core.
# The VIO core controls the counter.

ila = device.ila_cores.get(name="chipscopy_i/counters/ila_slow_counter_0")
vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")

print(f"Using ILA: {ila.core_info.uuid}  {ila.name}")
print(f"Using VIO: {vio.core_info.uuid}  {vio.name}")


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
# Set up the VIO core to enable counting up from 0
#
vio.reset_vio()
vio.write_probes(
    {
        "chipscopy_i/counters/slow_counter_0_SCLR": 0,
        "chipscopy_i/counters/slow_counter_0_L": 0x00000000,
        "chipscopy_i/counters/slow_counter_0_LOAD": 0,
        "chipscopy_i/counters/slow_counter_0_UP": 1,
        "chipscopy_i/counters/slow_counter_0_CE": 1,
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
ila.set_probe_trigger_value("chipscopy_i/counters/slow_counter_0_Q_1", ["==", "0xXXXX_0000"])
ila.run_basic_trigger(window_count=1, window_size=32, trigger_position=16)
print("ILA is running - looking for trigger")

# %%
# Wait for the ILA trigger with upload.
# Then print the captured ILA samples and mark the trigger position.

ila.wait_till_done(max_wait_minutes=0.1)
upload_successful = ila.upload()
if upload_successful:
    samples = get_waveform_data(
        ila.waveform,
        ["chipscopy_i/counters/slow_counter_0_Q_1"],
        include_trigger=True,
        include_sample_info=True,
    )
    for trigger, sample_index, window_index, window_sample_index, value in zip(*samples.values()):
        trigger = "<-- Trigger" if trigger else ""
        print(
            f"Window:{window_index}  Window Sample:{window_sample_index}  {value:10}  0x{value:08X} {trigger}"
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
#
# After this step,
# - VIO drives counter to count from UP to DOWN
# - ILA triggers on the UP to DOWN signal transition
# - Waveform uploaded with the up/down trigger sample in the center of captured data
#

# %% [markdown]
# <img src="img/edge_trigger.png" width="550" align="left">

# %%
# Set ILA core to capture on a transition of the UP/DOWN toggle switch
# Once transition happens, trigger in the middle of the buffer.

ila.reset_probes()
ila.set_probe_trigger_value("chipscopy_i/counters/slow_counter_0_UP_1", ["==", "B"])
ila.run_basic_trigger(window_count=1, window_size=32, trigger_position=16)

print("ILA is running - looking for trigger")

# %%
# VIO: Turn counter up/down switch to DOWN position.
# This will cause the running ILA to trigger on the transition edge from up to down.

vio.write_probes({"chipscopy_i/counters/slow_counter_0_UP": 0})

print("VIO changed up/down counter to count down")

# %%
# Print the captured ILA samples and mark the trigger position.
# Note that counter counts down after the trigger mark.

ila.wait_till_done(max_wait_minutes=0.1)
upload_successful = ila.upload()
if upload_successful:
    samples = get_waveform_data(
        ila.waveform,
        ["chipscopy_i/counters/slow_counter_0_Q_1"],
        include_trigger=True,
        include_sample_info=True,
    )
    for trigger, sample_index, window_index, window_sample_index, value in zip(*samples.values()):
        trigger = "<-- Trigger" if trigger else ""
        print(
            f"Window:{window_index}  Window Sample:{window_sample_index}  {value:10}  0x{value:08X} {trigger}"
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
    export_waveform(ila.waveform, "VCD", sys.stdout)
