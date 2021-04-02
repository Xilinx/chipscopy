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
# VIO Example
# ===========

# %% [markdown]
# Description
# -----------
# This demo shows how to do three things:
# 1. Connect to a Versal target device via ChipScope Server (cs_server)
#    and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Communicate with a VIO debug core in hardware
#
# Requirements
# ------------
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. cs_server and hw_server applications
# 3. Python 3.7 environment
# 4. Pip-installed chipscopy python package
#
# ---

# %% [markdown]
# ## Step 1 - Set up environment

# %% pycharm={"name": "#%%\n"}
import os
from chipscopy import get_examples_dir_or_die

# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")

EXAMPLES_DIR = get_examples_dir_or_die()
PDI_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
assert os.path.isfile(PDI_FILE)
LTX_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.ltx"
assert os.path.isfile(LTX_FILE)

print(f"HW_URL={HW_URL}")
print(f"CS_URL={CS_URL}")
print(f"PDI={PDI_FILE}")
print(f"LTX={LTX_FILE}")

# %% [markdown]
# ## Step 2 - Create a session and connect to the server(s)
# Here we create a new session and print out version information for diagnostic purposes.
# The session is a container that keeps track of devices and debug cores.

# %% pycharm={"name": "#%%\n"}
import chipscopy
from chipscopy import create_session, report_versions

print(f"Using chipscopy api version: {chipscopy.__version__}")
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## Step 3 - Get our device from the session

# %% pycharm={"name": "#%%\n"}

# Use the first available device and setup its debug cores
if len(session.devices) == 0:
    raise ValueError("No devices detected")
versal_device = session.devices[0]

# %% [markdown]
# ## Step 4 - Program the device with our example PDI

# %% pycharm={"name": "#%%\n"}
print(f"Programming {PDI_FILE}...")
versal_device.program(PDI_FILE)

# %% [markdown]
# ## Step 5 - Detect Debug Cores

# %% pycharm={"name": "#%%\n"}

print(f"Discovering debug cores...")
versal_device.discover_and_setup_cores(ltx_file=LTX_FILE)

vio_count = len(versal_device.vio_cores)
print(f"\nFound {vio_count} VIO cores in design")
assert vio_count == 2

# %% [markdown]
# ### Find the VIO cores
# This shows some different ways to find the VIO core - by name, by uuid, or by index
# and how to print port names and probe names.

# %% pycharm={"name": "#%%\n"}
vio_cores = versal_device.vio_cores
for index, vio_core in enumerate(vio_cores):
    print(f"\nVIO Core Index {index}")
    print("NAME       :", vio_core.name)
    print("UUID       :", vio_core.uuid)
    print("PORT_NAMES :", vio_core.port_names)
    print("PROBE_NAMES:", vio_core.probe_names)

# Get VIO by uuid:
vio_by_uuid = versal_device.vio_cores.filter_by(uuid="499D80541CE65035B25919B9E0CD7838")[0]

my_vio = vio_by_uuid

# %% [markdown] pycharm={"name": "#%% md\n"}
# ## Step 6 - Read and Write Ports
# - Write known value to port "probe_out4"
# - Verify value was written to port "probe_out4"
# - Reset port to default value

# %% pycharm={"name": "#%%\n"}
my_vio.reset_vio()
print("\nPort Data before write:", my_vio.read_ports(["probe_out4"]))
new_port_values = {"probe_out4": 12345678}
my_vio.write_ports(new_port_values)
print(f"Wrote {12345678} to probe_out4")
print("Port Data after write:", my_vio.read_ports(["probe_out4"]))

# %% [markdown]
# ## Step 7 - Read and Write Probes
# - Port probe_out4 is the same as probe ks_demo_i/slow_counter_0_L
# - Write known value to port probe_out4
# - Read value back from probe ks_demo_i/slow_counter_0_L
# - Verify value is the same as written to probe_out4

# %% pycharm={"name": "#%%\n"}
my_vio.reset_vio()
print("\nPort Data before write:", my_vio.read_ports(["probe_out4"]))
print("Probe Data before write:", my_vio.read_probes(["ks_demo_i/slow_counter_0_L"]))
my_vio.write_ports(new_port_values)
new_port_values = {"probe_out4": 12345678}
my_vio.write_ports(new_port_values)
print(f"Wrote {12345678} to probe_out4")
print("Port Data after write:", my_vio.read_ports(["probe_out4"]))
print("Probe Data after write:", my_vio.read_probes(["ks_demo_i/slow_counter_0_L"]))
