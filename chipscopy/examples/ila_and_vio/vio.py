# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright 2022 Xilinx, Inc.<br><br>
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
from chipscopy import get_design_files
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
# - Debug cores in the cs_server may be accessed

# %%
device.discover_and_setup_cores(ltx_file=PROBES_FILE)
print(f"Debug cores setup and ready for use.")

# %% [markdown]
# ## 5 - Using The VIO Core
#
# The following cells demonstrate how to perform various operations with the VIO core.
# These are meant to be useful code snippets that can be copy/pasted for your own application.


# %%
# Enumerate all VIO cores in the device.
# Every VIO core has properties including a UUID and instance name.
#
# Print out the VIO core instance UUIDs and instance names
# It is normal for this call to be slower the first time, and faster subsequent iterations.

vio_cores = device.vio_cores
print("       UUID                              INSTANCE NAME")
for index, vio_core in enumerate(vio_cores):
    print(f"VIO-{index}  {vio_core.core_info.uuid}  {vio_core.name}")

# %%
# You can get a VIO core by instance name or uuid
vio_by_instance_name = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")
the_vio_uuid = vio_by_instance_name.uuid

# Grab the same VIO by UUID and ensure it is the same core
vio_by_uuid = device.vio_cores.get(uuid = the_vio_uuid)
assert(vio_by_instance_name == vio_by_uuid)

print("vio_by_instance_name and vio_by_uuid match!")

# %%
# The VIO API knows the mapping between logical probes and ports on the VIO core.
# The code below prints the probe to port mapping.

vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")

print("VIO Port <---> Probe mapping:")
for probe in vio.probes:
    if probe.direction == "in":
        print(f"{probe.port_name} <-- {probe.probe_name}")
    else:
        print(f"{probe.port_name} --> {probe.probe_name}")

# %%
# Writing values
# Values may be written to the ouput ports or logical named probes.

vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")

# Writing values to a logical named probes:
vio.write_probes({
    "chipscopy_i/counters/slow_counter_0_L": 0x12345678
})
print("Wrote 0x12345678 to chipscopy_i/counters/slow_counter_0_L")

# Writing the value to the same VIO port:
vio.write_ports({
    "probe_out4": 0x11223344
})
print("Wrote 0x11223344 to probe_out4")

# %%
# Reading VIO probe values
# Probes are the logical names mapped to VIO ports in the LTX file.

vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")
vio.reset_vio()

# Reading all probes at once and extracting one of interest returns a dictionary of probe data.
#   value is returned as an integer
#   activity is a string, one acivity per bit: N=None, R=Rising, F=Falling, B=Both
all_probe_info = vio.read_probes()
value = all_probe_info["chipscopy_i/counters/slow_counter_0_Q"]["value"]
activity = all_probe_info["chipscopy_i/counters/slow_counter_0_Q"]["activity"]
print(f"Counter Value: {value}, Activity: {activity}")

# Reading from a single named logical probe
# For convenience, you can ask specifically for one or more probes to reduce the data size.
# The returned dictionary format is the same.
one_probe_info = vio.read_probes("chipscopy_i/counters/slow_counter_0_Q")
value = one_probe_info["chipscopy_i/counters/slow_counter_0_Q"]["value"]
activity = one_probe_info["chipscopy_i/counters/slow_counter_0_Q"]["activity"]
print(f"Counter Value: {value}, Activity: {activity}")

# Reading the same value directly from the VIO port "probe_in0" - mapped to the same counter
port_info = vio.read_ports("probe_in0")
value = port_info["probe_in0"]["value"]
activity = port_info["probe_in0"]["activity"]
print(f"Counter Value: {value}, Activity: {activity}")


# %%
# Reading probe values

# %%
# Resetting the VIO core resets all output values to the their default.
# Default values were optionally set during implementation as a property on the VIO IP.

vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")
vio.reset_vio()
print(f"VIO core {vio} reset to initial values.")


# %%
# You can access low level VIO properties as a dictionary or in json.
# This gives easy python access to probe and port information.

import pprint

pp = pprint.PrettyPrinter(indent = 4)

vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")

vio_dict = vio.to_dict()
pp.pprint(vio_dict)

# %%
# The VIO properties can conveniently be accessed as JSON as well.
# This is convenient when interfacing with other languages.
vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")
vio_json = vio.to_json()
print(vio_json)
