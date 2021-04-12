# %%
# Copyright 2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# %% [markdown]
# ChipScoPy ILA and VIO Example
# =============================

# %% [markdown]
# Description
# -----------
# This example demonstrates how to program and communicate with ILA (Integrated Logic Analyzer) and
# VIO (Virtual IO) cores using the ChipScoPy Python API.
#
# <img src="img/api_overview.png" width="500" align="left">
#

# %% [markdown]
# Requirements
# ------------
# 1. Hardware Server 2021.1+
# 2. ChipScope Server 2021.1+
# 3. Xilinx Versal board such as a VCK190
# 4. Python 3.8 or greater with ChipScoPy 2021.1+ installed

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - URL paths are set correctly
# - File paths to example files are set correctly

# %%
import os
from chipscopy import get_examples_dir_or_die
from chipscopy import create_session, report_versions
from chipscopy.api.ila import get_waveform_data

# %%
# Specify locations of the running hw_server and cs_server below.
# To make things convenient, we default to values from the following environment variables.
# Modify these if needed.

CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")
EXAMPLES_DIR = get_examples_dir_or_die()
PROGRAMMING_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
PROBES_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.ltx"


# %%
# Double check paths look good...
print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")
print(f"PROGRAMMING_FILE: {PROGRAMMING_FILE}")
print(f"PROBES_FILE:{PROBES_FILE}")

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# Create a new session. The session is a container that keeps track of devices and debug cores managed by the hw_server and cs_server
#
# - hw_server_url is the hardware server. It handles low level device communication
# - cs_server_url is the chipscope server. It manages higher level debug core services.
#
# After this step,
#
# - session is initialized, pointing at a running chipscope and hardware server
# - versions of ChipScoPy, hardware server, and chipscope server are known

# %%
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)

# Report version is a convenient command to check versions of ChipScoPy, hw_server, and cs_server.
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with our example bitstream
#
#
# After this step,
# - Device is programmed with the example bitstream
#

# %%
print(f"Programming {PROGRAMMING_FILE}...")
device = session.devices[0]
device.program(PROGRAMMING_FILE)


# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - chipscope server is ready for debug core use
# - ila and vio core instances in the device are reported

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

ila = session.devices[0].ila_cores.get(name="ks_demo_i/ila_slow_counter_0")
vio = session.devices[0].vio_cores.get(name="ks_demo_i/vio_slow_counter_0")

print(f"Using ila: {ila.core_info.uuid}  {ila.name}")
print(f"Using vio: {vio.core_info.uuid}  {vio.name}")


# %% [markdown]
# ### 5a - Configure the counter using VIO output probes
#
# <img src="img/vio_control_counter.png" width="300" align="left">

# %%
# Set up the VIO core to enable counting up from 0
#
vio.reset_vio()
vio.write_probes(
    {
        "ks_demo_i/slow_counter_0_SCLR": 0,
        "ks_demo_i/slow_counter_0_L": 0x00000000,
        "ks_demo_i/slow_counter_0_LOAD": 0,
        "ks_demo_i/slow_counter_0_UP": 1,
        "ks_demo_i/slow_counter_0_CE": 1,
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
ila.set_probe_trigger_value("ks_demo_i/slow_counter_0_Q_1", ["==", "0xXXXX_0000"])
ila.run_basic_trigger(window_count=1, window_size=32, trigger_position=16)
print("ila is running - looking for trigger")

# %%
# Wait for the ila trigger with upload.
# Then print the captured ILA samples and mark the trigger position.

ila.monitor_status(max_wait_minutes=0.1)
ila.upload()
samples = get_waveform_data(
    ila.waveform,
    ["ks_demo_i/slow_counter_0_Q_1"],
    include_trigger=True,
    include_sample_info=True,
)
for trigger, sample_index, window_index, window_sample_index, value in zip(*samples.values()):
    trigger = "<-- Trigger" if trigger else ""
    print(
        f"Window:{window_index}  Window Sample:{window_sample_index}  {value:10}  0x{value:08X} {trigger}"
    )

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
ila.set_probe_trigger_value("ks_demo_i/slow_counter_0_UP_1", ["==", "B"])
ila.run_basic_trigger(window_count=1, window_size=32, trigger_position=16)

print("ila is running - looking for trigger")

# %%
# VIO: Turn counter up/down switch to DOWN position.
# This will cause the running ILA to trigger on the transition edge from up to down.

vio.write_probes({"ks_demo_i/slow_counter_0_UP": 0})

print("vio changed up/down counter to count down")

# %%
# Print the captured ILA samples and mark the trigger position.
# Note that counter counts down after the trigger mark.

ila.monitor_status(max_wait_minutes=0.1)
upload_successful = ila.upload()
if upload_successful:
    samples = get_waveform_data(
        ila.waveform,
        ["ks_demo_i/slow_counter_0_Q_1"],
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
