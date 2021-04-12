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

# !/usr/bin/env python
# coding: utf-8

# SysMon Example Script
# =====================

# Description
# -----------
# This demo shows how to do four things:
# 1. Connect to a Versal target device via ChipScope Server (cs_server)
#    and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Discover Design Specifics and setup measurements
# 4. Plot live data
#
# Requirements
# ------------
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. 2021.1+ cs_server and hw_server applications
# 3. Python 3.8 environment
# 4. chipscopy package installed in your environment
#
# ---

# ## Step 1 - Set up environment

# %%


import os

# Specify locations of the running hw_server and cs_server below.
from time import sleep
from more_itertools import one

CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")

EXAMPLES_DIR = os.path.realpath(os.getcwd() + "/..")
LTX_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.ltx"
PDI_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
print(f"HW_URL={HW_URL}")
print(f"CS_URL={CS_URL}")


# ## Step 2 - Create a session and connect to the server(s)
# Here we create a new session and print out some versioning information for diagnostic purposes.

# %%


from chipscopy import __version__, dm
from chipscopy import create_session, report_versions

print(f"Using chipscopy api version: {__version__}")
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)
print()


# ## Step 3 - Get our device from the session
# The session is a container that keeps track of devices and debug cores.

# %%

# Use the first available device and setup its debug cores
if len(session.devices) == 0:
    print("\nNo devices detected")
    exit()

print(f"Device count: {len(session.devices)}")
versal_device = session.devices[0]


# ## Discover Cores and Get Running Design Info
#
# 1. We begin by enumerating the debug cores (hard and soft) present in the design.
# 1. Then we ask the design for the supported timebases. And, finally:
# 1. The NoC is scanned to determine the activated elements.

# %%


# set this to false if you do not want to program the device
program_device = True
if program_device:
    print(f"Programming {PDI_FILE}...")
    versal_device.program(PDI_FILE)

print(f"Discovering debug cores...", end="")
versal_device.discover_and_setup_cores(sysmon_scan=True)
print("Complete!")

sysmon = one(versal_device.sysmon_root)


all_sensors = sysmon.get_all_sensors()
for sensor in all_sensors:
    print(f"{sensor}, ", end="")
print()
print()
print("initializing sensors")
active_nodes = sysmon.initialize_sensors()
print("refresh measurement schedule")
schedule = sysmon.refresh_measurement_schedule()
print("Sensors:")
for sensor in schedule.values():
    print(f"  {sensor}")


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

while True:
    session.chipscope_view.run_events()
    sleep(0.1)

print("done")
