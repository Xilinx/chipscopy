# %% [markdown] pycharm={"name": "#%%\n"}
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
# # ChipScoPy Memory Read and Write Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This demo shows how to read and write memory in the device using the ChipScoPy Python API.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2022.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - Paths to server(s) and files are set correctly

# %% pycharm={"name": "#%%\n"}
import os
from chipscopy import get_design_files
from chipscopy import create_session, report_versions

# %%
# Make sure to start the hw_server prior to running.
# Specify location of the running hw_server below.
# The default is localhost - but can be other locations on the network.
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
print(f"HW_URL={HW_URL}")

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout
#
# *NOTE*: No cs_server is required for this example.

# %% pycharm={"name": "#%%\n"}
session = create_session(hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## Step 3 - Get the device from the session

# %% pycharm={"name": "#%%\n"}
# Typical case - one device on the board - get it.
versal_device = session.devices.filter_by(family="versal").get()
print(versal_device)

# %% [markdown]
# ## Step 4 - Reset the device

# %% pycharm={"name": "#%%\n"}
versal_device.reset()
print("Reset complete.")

# %% [markdown]
# ## Step 5 - Write and Read memory
#
#
# ChipScoPy can be used to read and write memory using the hardware server.
# Memory reads and writes work similar to xsdb mrd and mwr commands.
#

# %% [markdown]
# ### Show the list of all memory targets
#
# Memory targets in this list can be used for memory_read and memory_write
# operations.

# %% pycharm={"name": "#%%\n"}
print("\nMemory Targets: ", versal_device.memory_target_names)

# %% [markdown]
# ### Simple Write and read memory example
#
# This is the most basic memory_read and memory_write example using the default
# DPC memory target.
#
# Below we write 32-bit values to the specified address and read them back.

# %% pycharm={"name": "#%%\n"}
addr = 0xF2010000
values_to_write = [0x10111213, 0x14151617]

print("\nWriting [{}]".format(", ".join(hex(x) for x in values_to_write)), "to address:", hex(addr))
# Write to the DPC default target
versal_device.memory_write(addr, values_to_write)

print(f"Reading {len(values_to_write)} values from address: hex(addr)")
read_values = versal_device.memory_read(address=addr, num=len(values_to_write))

print("Readback result: [{}]".format(", ".join(hex(x) for x in read_values)))

assert read_values == values_to_write

# %% [markdown]
# ### Changing Memory Read/Write Word Sizes
#
# It is possible to specify the word size when reading and writing.
# Default is 'w'. Other sizes shown below.
# ```
# 'b'=byte
# 'h'=half
# 'w'=word
# 'd'=double word
# ```

# %% pycharm={"name": "#%%\n"}
addr = 0xF2010000
values_to_write = [0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]

print("\nWriting [{}]".format(", ".join(hex(x) for x in values_to_write)), "to address:", hex(addr))
versal_device.memory_write(addr, values_to_write, size="b")

print("Reading from address: ", hex(addr))
read_values = versal_device.memory_read(address=addr, size="b", num=len(values_to_write))
print("Readback result: [{}]".format(", ".join(hex(x) for x in read_values)))
assert read_values == values_to_write

values_to_write = [0x1000, 0x1234, 0x4321, 0x1313, 0x1414, 0x1515, 0x1616, 0x1717]
print("\nWriting [{}]".format(", ".join(hex(x) for x in values_to_write)), "to address:", hex(addr))
versal_device.memory_write(addr, values_to_write, size="h")

print("Reading from address: ", hex(addr))
read_values = versal_device.memory_read(address=addr, size="h", num=len(values_to_write))
print("Readback result: [{}]".format(", ".join(hex(x) for x in read_values)))
assert read_values == values_to_write

# %% [markdown]
# ### Selecting different memory targets and improving performance
#
# The examples above use the device class for memory_read() and memory_write()
# operations. Using the device read and write is simple, but has additional
# overhead with each call to find the associated memory context.
#
# It is possible to explicitly request the memory context for a desired target.
# Once a memory context is obtained, memory_read and memory_write operations
# can be executed on that target repeatedly.
#
# This eliminate some of the additional overhead.
#
# The example below shows how to get a context to repeatedly read and write from
# different memory targets.

# %% pycharm={"name": "#%%\n"}
addr = 0xF2010000
dpc = versal_device.memory.get(name="DPC")
apu = versal_device.memory.get(name="APU")
for i in range(10):
    values_to_write = [0x12345678 + i, 0xFEDCBA98 - i]
    # Write to the DPC without context lookup overhead
    print(
        "\nDPC: Writing [{}]".format(", ".join(hex(x) for x in values_to_write)),
        "to address:",
        hex(addr),
    )
    dpc.memory_write(addr, values_to_write)
    # Read from the APU without context lookup overhead
    print("APU: Reading from address: ", hex(addr))
    read_values = apu.memory_read(address=addr, num=len(values_to_write))
    print("Readback result: [{}]".format(", ".join(hex(x) for x in read_values)))
    assert read_values == values_to_write
