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
# Memory Read and Write Example
# =============================
#
# Description
# -----------
# This demo shows how to do three things:
# 1. Connect to a Versal target device via ChipScope Server (cs_server)
#    and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Read and write memory locations in a design
#
# Requirements
# ------------
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. cs_server and hw_server applications
# 3. Python 3.7 or better
# 4. Pip-installed chipscopy python package
#
# ---

# %% [markdown]
# ## Step 1 - Set up environment

# %%
import os
from chipscopy import get_examples_dir_or_die

# Specify locations of the running hw_server and cs_server below.
# For memory transactions, cs_server is not required.
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")

EXAMPLES_DIR = get_examples_dir_or_die()
PDI_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
assert os.path.isfile(PDI_FILE)

print(f"HW_URL={HW_URL}")
print(f"PDI={PDI_FILE}")

# %% [markdown]
# ## Step 2 - Create a session and connect to the hardware server
# Here we create a new session and print out some versioning information for diagnostic purposes.

# %%
from chipscopy import create_session, report_versions

session = create_session(hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## Step 3 - Get our device from the session
# The session is a container that keeps track of devices and debug cores.

# %%
from more_itertools import one

# %%
# Assume we have exactly one device - get it.
if not session.devices:
    raise ValueError("No devices detected")
versal_device = one(session.devices)

# %% [markdown]
# ## Step 4 - Program the device with our example PDI

# %%
print(f"Programming {PDI_FILE}...")
versal_device.program(PDI_FILE)

# %% [markdown]
# ## Step 5 - Write and Read memory
# Memory writes and reads work similar to xsdb.

# %% [markdown] pycharm={"name": "#%% md\n"}
# ### Show the list of all memory targets

# %% pycharm={"name": "#%%\n"}
print("\nMemory Targets: ", versal_device.memory_target_names)


# %% [markdown] pycharm={"name": "#%% md\n"}
# ### DPC Write and read memory example
# You can specify any target in the memory_target_names list. Not specifying a memory target
# defaults to the DPC.

# %% pycharm={"name": "#%%\n"}
addr = 0xF2010000
values = [0x10111213, 0x14151617]
print("\nWriting [{}]".format(", ".join(hex(x) for x in values)), "to address:", hex(addr))
versal_device.memory_write(addr, values)

print("\nReading from address: ", hex(addr))
result = versal_device.memory_read(address=addr, num=2)
print("Result= [{}]".format(", ".join(hex(x) for x in result)))


# %% [markdown] pycharm={"name": "#%% md\n"}
# ### APU Write and read memory example
# You can specify a different target in the memory_target_names list for memory access.
# Here we use the APU instead of default DPC.

# %% pycharm={"name": "#%%\n"}
addr = 0xF2010000
values = [0x12345678, 0xFEDCBA98]
print("\nWriting [{}]".format(", ".join(hex(x) for x in values)), "to address:", hex(addr))
versal_device.memory_write(addr, values, target="APU")

print("\nReading from address: ", hex(addr))
result = versal_device.memory_read(address=addr, num=2, target="APU")
print("Result= [{}]".format(", ".join(hex(x) for x in result)))


# %% [markdown] pycharm={"name": "#%% md\n"}
# ### Memory Word Sizes
#
# It is possible to specify the word size when reading and writing.
# 'b'=byte, 'h'=half, 'w'=word, 'd'=double word

# %% pycharm={"name": "#%%\n"}
addr = 0xF2010000
values = [0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]
print("\nWriting [{}]".format(", ".join(hex(x) for x in values)), "to address:", hex(addr))
versal_device.memory_write(addr, values, size="b")

print("\nReading from address: ", hex(addr))
result = versal_device.memory_read(address=addr, size="b", num=8)
print("Result= [{}]".format(", ".join(hex(x) for x in result)))

values = [0x1000, 0x1234, 0x4321, 0x1313, 0x1414, 0x1515, 0x1616, 0x1717]
print("\nWriting [{}]".format(", ".join(hex(x) for x in values)), "to address:", hex(addr))
versal_device.memory_write(addr, values, size="h")

print("\nReading from address: ", hex(addr))
result = versal_device.memory_read(address=addr, size="h", num=8)
print("Result= [{}]".format(", ".join(hex(x) for x in result)))
