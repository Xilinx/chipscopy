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
# Description
# -----------
#
# This demo shows how to do three things:
#
# 1. Connect to a Versal target device via ChipScope Server (cs_server) and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Examine DDR results

# %%
import pprint
import os
from chipscopy import get_examples_dir_or_die
from chipscopy import create_session, report_versions

# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
BOARD = os.getenv("HW_SERVER_BOARD", "vck190/production/2.0")

EXAMPLES_DIR = get_examples_dir_or_die()
PDI_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.pdi"
LTX_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/ks_demo/ks_demo_wrapper.ltx"

print(f"HW_URL: {HW_URL}")
print(f"CS_URL: {CS_URL}")
print(f"PROGRAMMING_FILE: {PDI_FILE}")
print(f"PROBES_FILE:{LTX_FILE}")

# %%
# Start of the connection
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %%
# Use the first available device and setup its debug cores
versal_device = session.devices[0]
# Program
print(f"Programming {PDI_FILE}...")
versal_device.program(PDI_FILE)

# %%
print(f"Discovering debug cores...")
versal_device.discover_and_setup_cores()

# %%
# print(f"Getting DDR by DDRMC Index")
# ddr = versal_device.get_ddr(0)
# props = ddr.get_property_group([])
# print(pprint.pformat(sorted(props.items()), indent=2))

ddr_list = versal_device.ddrs

# ** Getting individual DDR from the list and exercise properties **
# ddr = ddr_list.at(0)
# props = ddr.ddr_node.get_property_group([])
# print(pprint.pformat(sorted(props.items()), indent=2))

for ddr in ddr_list:
    if ddr.is_enabled:
        # Use Status string base API directly
        print(ddr.name, "is enabled.")
        print("Calibration status is: ", ddr.get_cal_status())

        # Use Property Group to get dictionary base of results
        props = ddr.ddr_node.get_property_group(["status"])
        print(pprint.pformat(props, indent=2))

        # Use get Cal Stages API directly to also get dictionary results
        props = ddr.get_cal_stages()
        print(pprint.pformat(sorted(props.items()), indent=2))

        # Use a single report command to get all latest essential
        # Status and decoded data collected as it presents
        ddr.report()
        # Specify True to argument 1, and name/path to argument 2
        # to get the report output generated and saved to a file
        ddr.report(True, "test_out.txt")
        print("Report Done.\n")
    else:
        print(ddr.name, "is NOT enabled.")

# %%
