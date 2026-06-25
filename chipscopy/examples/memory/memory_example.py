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
# - Local or remote AMD Versal board, such as a VCK190
# - AMD hw_server 2026.1 installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[jupyter, core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths

# %%
import os
from chipscopy import create_session, report_versions, delete_session
from chipscopy.examples.mesa import resolve_example_design


# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
EXAMPLE_ID = "memory_example"
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
# ## 2 - Create a session and connect to the hw_server
#
# The session is a container that keeps track of devices and debug cores.

# %%
session = create_session(hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## Step 3 - Get the device from the session

# %%
versal_device = session.devices.filter_by(family=DEVICE_FAMILY).get()
print(versal_device)

# %% [markdown]
# ## Step 4 - Program the device

# %% [markdown]
# `example_design.program_device()` dispatches to the correct flow (flat vs. segmented) based on the manifest. See [program.ipynb](../program/program.ipynb) for the explicit per-flow code.

# %%
if PROG_DEVICE:
    if not example_design.verify_device_idcode(versal_device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(versal_device)
print("Programming complete.")

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

# %%
print("\nMemory Targets: ", versal_device.memory_target_names)

# %% [markdown]
# ### Simple Write and read memory example
#
# This is the most basic memory_read and memory_write example using the default
# DPC memory target.
#
# Below we write 32-bit values to the specified address and read them back.

# %%
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

# %%
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

# %%
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

# %%
## When done with testing, close the connection
delete_session(session)
