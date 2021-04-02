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
# ILA Basic Trigger Example
# =========================

# %% [markdown]
# Description
# -----------
# This demo shows how to do four things:
# 1. Connect to a Versal target device via ChipScope Server (cs_server)
#    and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Run a basic trigger on the ILA core
# 4. Retrieve and dump the data buffer captured by the ILA core
#
# Requirements
# ------------
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. 2021.1 cs_server and hw_server applications
# 3. Python 3.8 environment
# 4. A clone of the chipscopy git enterprise repository:
#    - https://gitenterprise.xilinx.com/chipscope/chipscopy
#
# ---

# %% [markdown]
# ## Step 1 - Set up environment

# %%
import os
from enum import Enum
from chipscopy import get_examples_dir_or_die, null_callback
from statistics import mean, median
from chipscopy.api.ila import export_waveform, get_waveform_probe_data, get_waveform_data

# %%
# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")

# %%
EXAMPLES_DIR = get_examples_dir_or_die()
PDI_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
assert os.path.isfile(PDI_FILE)
LTX_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.ltx"
assert os.path.isfile(LTX_FILE)

# %%
print(f"HW_URL={HW_URL}")
print(f"CS_URL={CS_URL}")
print(f"PDI={PDI_FILE}")
print(f"LTX={LTX_FILE}")

# %% [markdown]
# ## Step 2 - Create a session and connect to the server(s)
# Here we create a new session and print out some versioning information for diagnostic purposes.
# The session is a container that keeps track of devices and debug cores.

# %%
import chipscopy
from chipscopy import create_session, report_versions

# %%
print(f"Using chipscopy api version: {chipscopy.__version__}")
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## Step 3 - Get our device from the session

# %%
# Use the first available device and setup its debug cores
if len(session.devices) == 0:
    raise ValueError("No devices detected")
print(f"Device count: {len(session.devices)}")
versal_device = session.devices[0]

# %% [markdown]
# ## Step 4 - Program the device with our example PDI

# %%
print(f"Programming {PDI_FILE}...")
versal_device.program(PDI_FILE)

# %% [markdown]
# ## Step 5 - Detect Debug Cores

# %%
print(f"Discovering debug cores...")
versal_device.discover_and_setup_cores(ltx_file=LTX_FILE)

# %%
ila_count = len(versal_device.ila_cores)
print(f"\nFound {ila_count} ILA cores in design")

# %%
if ila_count == 0:
    print("No ILA core found! Exiting...")
    raise ValueError("No ILA cores detected")

# %%
# List all detected ILA Cores
ila_cores = versal_device.ila_cores
for index, ila_core in enumerate(ila_cores):
    print(f"    ILA Core #{index}: NAME={ila_core.name}, UUID={ila_core.core_info.uuid}")

# %% [markdown]
# ### Some ways to query debug cores

# %%
# Get the ila cores matching a given name. filter_by returns a list, even if just one item is present.
ila_by_name = versal_device.ila_cores.filter_by(name="ks_demo_i/ila_slow_counter_0")[0]
# Get ILA by uuid:
ila_by_uuid = versal_device.ila_cores.filter_by(uuid="CA49247E0AB35CCBB6093B473F933C0E")[0]
# This also works to get an ila by index:
ila_by_index = versal_device.ila_cores[3]

# %%
assert ila_by_name is ila_by_uuid
assert ila_by_name is ila_by_index

# %%
my_ila = ila_by_name

# %%
print(f"USING ILA: {my_ila.name}")

# %% [markdown]
# ## Step 6 - Get Information for this ILA Core
#

# %%
from pprint import pformat

# %%
print("\nILA Name:", my_ila.name)
print("\nILA Core Info", my_ila.core_info)
print("\nILA Static Info", my_ila.static_info)
print("\nILA ports:", pformat(my_ila.ports, 2))
print("\nILA probes:", pformat(my_ila.probes, 2))


# %% [markdown]
# ## Step 7 - Trigger on a probe value
#
# This ILA core is connected to a counter on probe 'ks_demo_i/slow_counter_0_Q_1'.
# Here we will trigger on the hex value equal to 0xXXXX_ABCD'
#
# Once the buffer is full of captured data, status['is_full'] == True

# %%
print("Running trigger on probe 'ks_demo_i/slow_counter_0_Q_1' ...")

# %%
# Set probe compare value to hex 0xXXXX_ABCD
my_ila.set_probe_trigger_value("ks_demo_i/slow_counter_0_Q_1", ["==", "0xXXXX_ABCD"])

# %%
# default values: trigger position in middle of window, trigger condition AND.
my_ila.run_basic_trigger(window_count=3, window_size=8, trigger_position=0)

# %%
my_ila.refresh_status()
print("\nILA Status", my_ila.status)

# %% [markdown]
# ## Step 8 - Upload captured waveform
# Wait at most half a minutes, for ILA to trigger and capture data.

# %%
my_ila.monitor_status(max_wait_minutes=0.5)
my_ila.upload()
if not my_ila.waveform:
    print("\nUpload failed!")

# %% [markdown]
# ### Print out probe 'ks_demo_i/slow_counter_0_Q_1' data, in CSV format.
#
# Below is a snippet that gets values for probe 'ks_demo_i/slow_counter_0_Q_1' in a list.
# The list contains namedtuples for each probe 'ks_demo_i/slow_counter_0_Q_1' sample captured.

# %%
print("\nDump signal ks_demo_i/slow_counter_0_Q_1 waveform to stdout in CSV format:\n")
export_waveform(my_ila.waveform, export_format="CSV", probe_names=["ks_demo_i/slow_counter_0_Q_1"])


# %% [markdown]
# ### Get samples for probe 'ks_demo_i/slow_counter_0_Q_1'. Dump in decimal and hex.
#
# The waveform data is put into a sorted dict.
# First 4 entries in sorting order are: trigger, sample index, window index, window sample index.
# The comes probe values. In this case only the requested probe 'ks_demo_i/slow_counter_0_Q_1'.

# %%
print("\nGet ILA captured values for ks_demo_i/slow_counter_0_Q_1, dump in decimal and hex.")
samples = get_waveform_data(
    my_ila.waveform,
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
# ### Print mean and median for probe 'ks_demo_i/slow_counter_0_Q_1' values.

# %%
mean_value = mean(samples["ks_demo_i/slow_counter_0_Q_1"])
print(f"\nMean Value: {mean_value}")

# %%
values = get_waveform_probe_data(my_ila.waveform, "ks_demo_i/slow_counter_0_Q_1")
median_value = median(values)
print(f"Median Value: {median_value}")

# %%
