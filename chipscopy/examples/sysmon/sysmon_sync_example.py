# ### License
# Copyright (C) 2021-2022, Xilinx, Inc.
# <br>
# Copyright (C) 2022-2024, Advanced Micro Devices, Inc.
# <p>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# <p>
# You may obtain a copy of the License at <a href="http://www.apache.org/licenses/LICENSE-2.0"?>http://www.apache.org/licenses/LICENSE-2.0</a><br><br>
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# # ChipScoPy System Monitor Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# ## Description
#
#
# This demo shows how to take and display measurements with the System Monitor.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2024.1 installed and running
# - Xilinx cs_server 2024.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2024.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - URL paths are set correctly
# - File paths to example files are set correctly

import os
import time
from chipscopy import get_design_files
from chipscopy import __version__, dm
from chipscopy import create_session, report_versions, delete_session

# +
# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
PROG_DEVICE = os.getenv("PROG_DEVICE", 'True').lower() in ('true', '1', 't')

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")

PROGRAMMING_FILE = design_files.programming_file
PROBES_FILE = design_files.probes_file

print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")
print(f"PROGRAMMING_FILE: {PROGRAMMING_FILE}")
print(f"PROBES_FILE:{PROBES_FILE}")
# -

# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
if PROG_DEVICE:
    device.program(PROGRAMMING_FILE)
else:
    print("skipping programming")

# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - The cs_server is initialized and ready for use

device.discover_and_setup_cores(sysmon_scan=True, ddr_scan=False)
print(f"System monitor setup and ready for use.")

# ## 5 - Initialize System Monitor
#
# Get reference to the system monitor and initialize all sensors.
# grab the measurement schedule

# +
sysmon = device.sysmon_root[0]

print("Initializing sensors")
active_nodes = sysmon.initialize_sensors()

print("Refresh measurement schedule")
schedule = sysmon.refresh_measurement_schedule()

print("Sensor Schedule:")
for sensor in schedule.values():
    print(f"  {sensor}")
print()
# -

# ## 6 - Refresh values from hardware
#
# Perform individual sensor read

sensor_to_read = 'VCCAUX'
current_value = sysmon.read_sensor(sensor_to_read)
print(f"Individual sensor read of {sensor_to_read}")
print(f'->{sensor_to_read}: {current_value:.3f}V')
print()

# ## 7 - Run measurement for 5 seconds
#
# Grab samples once a second for 5 seconds then exit.

# +
# Take measurements for 5 seconds then exit.
print("Group of sensors read")
sensors_to_read = ['VCC_PMC', 'VCC_PSLP', 'VCC_PSFP', 'VCC_SOC']
for x in range(5):
    current_sensor_values = sysmon.read_sensors(sensors_to_read)
    for sensor, value in current_sensor_values.items():
        print(f'  {sensor}: {value:.3f}V')
    temps = sysmon.read_temp()
    for temp, value in temps.items():
        print(f'  {temp}: {value:.1f}' + u"\u00b0C")
    print()
    time.sleep(1)


print("Measurement done.")
# -

## When done with testing, close the connection
delete_session(session)
