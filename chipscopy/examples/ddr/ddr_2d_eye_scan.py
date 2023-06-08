# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.10.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# + [markdown] papermill={"duration": 0.008991, "end_time": "2023-06-07T21:00:04.525682", "exception": false, "start_time": "2023-06-07T21:00:04.516691", "status": "completed"} tags=[]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (c) 2021-2022 Xilinx, Inc.<br>
# Copyright (c) 2022-2023 Advanced Micro Devices, Inc.<br><br>
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

# + [markdown] papermill={"duration": 0.005247, "end_time": "2023-06-07T21:00:04.536741", "exception": false, "start_time": "2023-06-07T21:00:04.531494", "status": "completed"} tags=[]
# # ChipScoPy DDR 2D Eye Margin Scan Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# + [markdown] papermill={"duration": 0.005302, "end_time": "2023-06-07T21:00:04.547271", "exception": false, "start_time": "2023-06-07T21:00:04.541969", "status": "completed"} tags=[]
# ## Description
# This demo shows how to exercise and run Versal DDRMC 2D Margin Scan features
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.2 installed and running
# - Xilinx cs_server 2022.2 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2022.2 installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command `pip install chipscopy[core-addons]`

# + [markdown] papermill={"duration": 0.005261, "end_time": "2023-06-07T21:00:04.557922", "exception": false, "start_time": "2023-06-07T21:00:04.552661", "status": "completed"} tags=[]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - URL paths are set correctly
# - File paths to example files are set correctly

# + papermill={"duration": 0.34377, "end_time": "2023-06-07T21:00:04.907155", "exception": false, "start_time": "2023-06-07T21:00:04.563385", "status": "completed"} tags=[]
import sys
import os
import pprint
from chipscopy import create_session, delete_session, report_versions
from chipscopy import get_design_files
from ddr_scan_util import convert_vref_pct_to_code

# + papermill={"duration": 0.013876, "end_time": "2023-06-07T21:00:04.927523", "exception": false, "start_time": "2023-06-07T21:00:04.913647", "status": "completed"} tags=[]
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

# + papermill={"duration": 0.010039, "end_time": "2023-06-07T21:00:04.942982", "exception": false, "start_time": "2023-06-07T21:00:04.932943", "status": "completed"} tags=[]
# Which DDRMC target (0..3) for given ACAP
DDR_INDEX = 0
# Which Rank of the memory interface
RANK = 0
# Read or Write Margin : "READ" "WRITE"
MARGIN_MODE = "READ"
# Data pattern used for margin check : "SIMPLE" "COMPLEX"
DATA_PATTERN = "COMPLEX"
# VREF Percentage Minimum (reccommended: Read :DDR4 25, LP4 5 , Write : DDR4 60  , LP4 10)
VREF_PCT_MIN = 25
# VREF Percentage Maximum (reccommended: Read:DDR4 50 , LP4 35 , Write : DDR4 90  , LP4 30)
VREF_PCT_MAX = 50
# Steps to show in the 2D eye scan  ( 1 step takes ~1 second to capture)
STEPS = 15
# Which nibble (read mode) or byte lane (write) to display
DISPLAY_INDEX = 1

# + [markdown] papermill={"duration": 0.005374, "end_time": "2023-06-07T21:00:04.953764", "exception": false, "start_time": "2023-06-07T21:00:04.948390", "status": "completed"} tags=[]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# + papermill={"duration": 0.870798, "end_time": "2023-06-07T21:00:05.829840", "exception": false, "start_time": "2023-06-07T21:00:04.959042", "status": "completed"} tags=[]
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# + [markdown] papermill={"duration": 0.005467, "end_time": "2023-06-07T21:00:05.841828", "exception": false, "start_time": "2023-06-07T21:00:05.836361", "status": "completed"} tags=[]
# ## 3 - Program the device with the example design
#
# After this step,
# - Device is programmed with the example programming file

# + papermill={"duration": 5.552341, "end_time": "2023-06-07T21:00:11.399767", "exception": false, "start_time": "2023-06-07T21:00:05.847426", "status": "completed"} tags=[]
# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
device.program(PROGRAMMING_FILE)

# + [markdown] papermill={"duration": 0.006105, "end_time": "2023-06-07T21:00:11.412757", "exception": false, "start_time": "2023-06-07T21:00:11.406652", "status": "completed"} tags=[]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - The cs_server is initialized and ready for use

# + papermill={"duration": 0.502661, "end_time": "2023-06-07T21:00:11.921223", "exception": false, "start_time": "2023-06-07T21:00:11.418562", "status": "completed"} tags=[]
device.discover_and_setup_cores(ltx_file=PROBES_FILE)
print(f"Debug cores setup and ready for use.")

# + [markdown] papermill={"duration": 0.006506, "end_time": "2023-06-07T21:00:11.934883", "exception": false, "start_time": "2023-06-07T21:00:11.928377", "status": "completed"} tags=[]
# ## 5 - Get a list of the integrated DDR Memory Controllers

# + papermill={"duration": 2.223944, "end_time": "2023-06-07T21:00:14.165739", "exception": false, "start_time": "2023-06-07T21:00:11.941795", "status": "completed"} tags=[]
ddr_list = device.ddrs
print(f"{len(ddr_list)} integrated DDRMC cores exist on this device.")

ddr_index = 0
for ddr in ddr_list:
    if ddr.is_enabled:
        print(f" DDRMC instance {ddr_index} is enabled")
    else:
        print(f" DDRMC instance {ddr_index} is disabled")
    ddr_index += 1

# + [markdown] papermill={"duration": 0.005839, "end_time": "2023-06-07T21:00:14.179025", "exception": false, "start_time": "2023-06-07T21:00:14.173186", "status": "completed"} tags=[]
# ## 6- Select a target DDR by index and display calibration status

# + papermill={"duration": 0.054787, "end_time": "2023-06-07T21:00:14.239597", "exception": false, "start_time": "2023-06-07T21:00:14.184810", "status": "completed"} tags=[]
try:
    ddr = ddr_list[DDR_INDEX]
    props = ddr.ddr_node.get_property(["cal_status"])
    print(f"Calibration status of DDRMC instance {DDR_INDEX} is {props['cal_status']}")
except:
    print(f"The DDR controller at index {DDR_INDEX} is not in use")

# + papermill={"duration": 0.260414, "end_time": "2023-06-07T21:00:14.505819", "exception": false, "start_time": "2023-06-07T21:00:14.245405", "status": "completed"} tags=[]
## Initialize and activate the Margin Check feature in the DDRMC
ddr.ddr_node.set_property({"mgchk_enable": 1})
ddr.ddr_node.commit_property_group([])
ddr.ddr_node.set_property({"mgchk_enable": 0})
ddr.ddr_node.commit_property_group([])
print("Initialization complete.")

# + [markdown] papermill={"duration": 0.0063, "end_time": "2023-06-07T21:00:14.518907", "exception": false, "start_time": "2023-06-07T21:00:14.512607", "status": "completed"} tags=[]
# ## 7 - Setting the 2D eye scan read or write mode

# + papermill={"duration": 0.1759, "end_time": "2023-06-07T21:00:14.701502", "exception": false, "start_time": "2023-06-07T21:00:14.525602", "status": "completed"} tags=[]
if MARGIN_MODE == "READ":
    print("Setting 2D eye for READ margin")
    ddr.set_eye_scan_read_mode()
elif MARGIN_MODE == "WRITE":
    print("Setting 2D eye for WRITE margin")
    ddr.set_eye_scan_write_mode()
else:
    print(
        f" ERROR: MARGIN_MODE is set to {MARGIN_MODE} which is an illegal value, only READ or WRITE is allowed"
    )


# + [markdown] papermill={"duration": 0.006109, "end_time": "2023-06-07T21:00:14.715427", "exception": false, "start_time": "2023-06-07T21:00:14.709318", "status": "completed"} tags=[]
# ## 8 - Setting the 2D eye scan data pattern mode

# + papermill={"duration": 0.143983, "end_time": "2023-06-07T21:00:14.865642", "exception": false, "start_time": "2023-06-07T21:00:14.721659", "status": "completed"} tags=[]
if DATA_PATTERN == "SIMPLE":
    print("Setting 2D eye for SIMPLE data pattern")
    ddr.set_eye_scan_simple_pattern()
elif DATA_PATTERN == "COMPLEX":
    print("Setting 2D eye for COMPLEX data pattern")
    ddr.set_eye_scan_complex_pattern()
else:
    print(
        f" ERROR: DATA_PATTERN is set to {DATA_PATTERN} which is an illegal value, only SIMPLE or COMPLEX is allowed"
    )

# + [markdown] papermill={"duration": 0.006278, "end_time": "2023-06-07T21:00:14.879812", "exception": false, "start_time": "2023-06-07T21:00:14.873534", "status": "completed"} tags=[]
# ## 9 - Setting the Vref sample min/max range

# + papermill={"duration": 0.366876, "end_time": "2023-06-07T21:00:15.253388", "exception": false, "start_time": "2023-06-07T21:00:14.886512", "status": "completed"} tags=[]
print("Vref Min setting...")
vref_min_code = convert_vref_pct_to_code(ddr, MARGIN_MODE, VREF_PCT_MIN)
print("Vref Max setting...")
vref_max_code = convert_vref_pct_to_code(ddr, MARGIN_MODE, VREF_PCT_MAX)

ddr.set_eye_scan_vref_min(vref_min_code)
ddr.set_eye_scan_vref_max(vref_max_code)
ddr.set_eye_scan_vref_steps(STEPS)
print(f"Dividing the Vref range into {STEPS} steps")


# + [markdown] papermill={"duration": 0.008217, "end_time": "2023-06-07T21:00:15.268997", "exception": false, "start_time": "2023-06-07T21:00:15.260780", "status": "completed"} tags=[]
# ## 10 - Run 2D Margin Scan after settings

# + papermill={"duration": 15.148415, "end_time": "2023-06-07T21:00:30.424088", "exception": false, "start_time": "2023-06-07T21:00:15.275673", "status": "completed"} tags=[]
ddr.run_eye_scan()

# + [markdown] papermill={"duration": 0.006677, "end_time": "2023-06-07T21:00:30.438038", "exception": false, "start_time": "2023-06-07T21:00:30.431361", "status": "completed"} tags=[]
# ## 11 - Display Scan Plots by a given Unit(nibble/byte) index
#
# You can display static or dynamic plots. The display_type controls the display output.
# - "static" is a simple image that can be saved.
# - "dynamic" is an interactive javascript plot.
# - The default is "dynamic".

# + papermill={"duration": 1.271679, "end_time": "2023-06-07T21:00:31.716284", "exception": false, "start_time": "2023-06-07T21:00:30.444605", "status": "completed"} tags=[]
ddr.display_eye_scan(DISPLAY_INDEX, display_type="static")

# + [markdown] papermill={"duration": 0.007736, "end_time": "2023-06-07T21:00:31.732936", "exception": false, "start_time": "2023-06-07T21:00:31.725200", "status": "completed"} tags=[]
# Optionally you can return figures as a list for later operations.

# + papermill={"duration": 0.047331, "end_time": "2023-06-07T21:00:31.788557", "exception": false, "start_time": "2023-06-07T21:00:31.741226", "status": "completed"} tags=[]
figs = ddr.display_eye_scan(DISPLAY_INDEX + 1, return_as_list=True)

# + [markdown] papermill={"duration": 0.007497, "end_time": "2023-06-07T21:00:31.805149", "exception": false, "start_time": "2023-06-07T21:00:31.797652", "status": "completed"} tags=[]
# The following loop demonstrates how you can display the graphs from a list created previously.
# It is easy to display interactive or static images.
#
# Here we get the list of figures and output them to png format.

# + papermill={"duration": 0.118201, "end_time": "2023-06-07T21:00:31.930807", "exception": false, "start_time": "2023-06-07T21:00:31.812606", "status": "completed"} tags=[]
from IPython.display import Image, display

for fig in figs:
    # To display interactive images, uncomment the following line:
    # fig.show()

    # To display a static png image:
    image_bytes = fig.to_image(format="png")
    ipython_image = Image(image_bytes)
    display(ipython_image)


# + [markdown] papermill={"duration": 0.008646, "end_time": "2023-06-07T21:00:31.951390", "exception": false, "start_time": "2023-06-07T21:00:31.942744", "status": "completed"} tags=[]
# ## 12 - Save the Eye Scan data from latest run

# + papermill={"duration": 0.136502, "end_time": "2023-06-07T21:00:32.096268", "exception": false, "start_time": "2023-06-07T21:00:31.959766", "status": "completed"} tags=[]
ddr.save_eye_scan_data("myoutput.csv")

# + [markdown] papermill={"duration": 0.008415, "end_time": "2023-06-07T21:00:32.114381", "exception": false, "start_time": "2023-06-07T21:00:32.105966", "status": "completed"} tags=[]
# ## 13 - Load Eye Scan data from a given data file

# + papermill={"duration": 0.017727, "end_time": "2023-06-07T21:00:32.140439", "exception": false, "start_time": "2023-06-07T21:00:32.122712", "status": "completed"} tags=[]
ddr.load_eye_scan_data("myoutput.csv")

# + [markdown] papermill={"duration": 0.00836, "end_time": "2023-06-07T21:00:32.157240", "exception": false, "start_time": "2023-06-07T21:00:32.148880", "status": "completed"} tags=[]
# ## 14 - Review overall Scan status and Control group detail from latest run

# + papermill={"duration": 0.016436, "end_time": "2023-06-07T21:00:32.182040", "exception": false, "start_time": "2023-06-07T21:00:32.165604", "status": "completed"} tags=[]
props = ddr.ddr_node.get_property_group(["eye_scan_stat", "eye_scan_ctrl"])
print(pprint.pformat(props, indent=2))

# + [markdown] papermill={"duration": 0.00848, "end_time": "2023-06-07T21:00:32.199254", "exception": false, "start_time": "2023-06-07T21:00:32.190774", "status": "completed"} tags=[]
# ## 15 - (Optional) Report Full DDR config and calibration/margin Info

# + papermill={"duration": 0.012806, "end_time": "2023-06-07T21:00:32.220812", "exception": false, "start_time": "2023-06-07T21:00:32.208006", "status": "completed"} tags=[]
# (uncomment to see report)
# ddr.report()

# + papermill={"duration": 0.023363, "end_time": "2023-06-07T21:00:32.252635", "exception": false, "start_time": "2023-06-07T21:00:32.229272", "status": "completed"} tags=[]
## When done with testing, close the connection
delete_session(session)
