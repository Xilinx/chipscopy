# %% [markdown]
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
# # ChipScoPy SPTG Perfmon Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This example demonstrates how to configure a Versal for taking NoC performance measurements.
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 installed and running
# - Xilinx cs_server 2022.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2022.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`
# - Matplotlib support installed - Please do so, using the command `pip install chipscopy[core-addons]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - Paths to server(s) and files are set correctly

# %%
import os
from time import sleep
import matplotlib  # for nbconvert'd script
from chipscopy.api.noc import (
    TC_BEW,
    TC_BER,
    NoCPerfMonNodeListener,
    PerfTGController,
)
from chipscopy.api.noc.plotting_utils import MeasurementPlot
from chipscopy import create_session, report_versions
from chipscopy import get_design_files

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
versal_device = session.devices.filter_by(family="versal").get()
versal_device.program(PROGRAMMING_FILE)

# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - The cs_server is initialized and ready for use

# %%
versal_device.discover_and_setup_cores(noc_scan=True, ltx_file=PROBES_FILE)
print(f"Debug cores setup and ready for use.")

# %% [markdown]
# ## 5 - Setup NoC core
#
# Ensure scan nodes are enabled in the design.

# %%
# We begin by enumerating the debug cores (hard and soft) present in the design.
# Then we ask the design for the supported timebases. And, finally:
# The NoC is scanned to determine the activated elements.

noc = versal_device.noc_core.get()

scan_nodes = ["DDRMC_X0Y0", "NOC_NMU512_X0Y0"]
print("\nEnumerating nodes: ", end="")
for node in scan_nodes:
    print(f"{node}, ", end="")
print("...", end="")

# this will setup the nodes on the server side and return the nodes successfully enumerated
enable_list = noc.enumerate_noc_elements(scan_nodes)
print("complete!")

# %%
supported_periods = noc.get_supported_sampling_periods(
    100/3, 100/3, {'DDRMC_X0Y0': 800.0}
)
print("Supported sampling periods:")
for domain, periods in supported_periods.items():
    print(f"  {domain}:")
    for p in periods:
        print(f"    {p:.0f}ms", end="")
    print()

# %%
# Select Timebase and Nodes to Monitor
#
# For the two clock domains we must select a sampling period from the hardware supported values. The debug cable used will dictate how much bandwidth is available, so high frequency sampling may not actually produce data at the specified rate. Recommendation is ~500ms for jtag.
#
# Then the user must decide what to monitor--again the bandwidth is a definite consideration here. Plot performance may become the bottleneck (Optimizations will come later in the renderer or agg backend). The guidance here is to pick up to 4 nodes to monitor.

desired_period = 500  # ms
sampling_intervals = {}

for domain in supported_periods.keys():
    sampling_intervals[domain] = 0
    for sp in supported_periods[domain]:
        if sp > desired_period:
            sampling_intervals[domain] = sp
            break

    if sampling_intervals[domain] == 0:
        print(
            f"Warning, desired period {desired_period}ms is slower than "
            f"longest supported period {supported_periods[domain][-1]}ms [{domain} domain] "
            f"defaulting to this value."
        )
        sampling_intervals[domain] = supported_periods[-1]

print(f"Sampling period selection:")
for domain, freq in sampling_intervals.items():
    print(f"  {domain}: {freq:.0f}ms")

# %%
# Configure Monitors
#
# As a precaution, it's a good idea to validate the desired nodes are enabled for the design.
# Using the set of nodes and the desired sampling periods it's time to ask the service to start pushing metric data. Two additional arguments are required to this API.
#
# Traffic class
#
# This is a bit-or field of the requested traffic classes. Note, One monitor is dedicated to read traffic classes and the other to write--so all read TCs will apply to one channel and all write TCs to the other. `Best effort` is a good place to start.
#
# Number of Samples
#
# The number of samples allows for a burst of measurements to be taken and then the underlying service will tear down the monitors and stop pumping data back to the client. `-1` denotes that sampling shall continue indefinitely.

# total number of samples to capture (-1 for continuous mode)
num_samples = -1

print("Setting up monitors for: ")
for node in enable_list:
    print(node)

# When overflow occurs the precision of the monitors must be traded for range
# See the server API for more information
extended_monitor_config = {"NOC_NMU512_X0Y0": {"tslide": 0x3}}  # or None
noc.configure_monitors(
    enable_list, sampling_intervals, (TC_BEW | TC_BER), num_samples, None, extended_monitor_config
)


# %% [markdown]
# ## 6 - Traffic Generator Configuration
#
# Release the traffic generator from reset.

# %%
vio_cores = versal_device.vio_cores
for index, vio_core in enumerate(vio_cores):
    print(f"\nVIO Core Index {index}")
    print("NAME       :", vio_core.name)
    print("UUID       :", vio_core.uuid)
    print("PORT_NAMES :", vio_core.port_names)
    print("PROBE_NAMES:", vio_core.probe_names)

# tg_vio_bc = "sptg_axi_i"
tg_vio_bc = "chipscopy_i/noc_tg_bc"
tg_vio_name = f"{tg_vio_bc}/axis_vio_0"
print(tg_vio_name)
tg_vio = versal_device.vio_cores.get(name=tg_vio_name)

tg_vio.reset_vio()
tg_vio.write_probes(
    {f"{tg_vio_bc}/noc_sim_trig_rst_n": 0x1, f"{tg_vio_bc}/noc_tg_tg_rst_n": 0x1}
)  # clear nrst on trigger and tg

first_tg_ba = 0x201_8000_0000
tg = PerfTGController(first_tg_ba, versal_device, vio=tg_vio)

# %% [markdown]
# ## 7 - Create plotter and listener
#
# Attach both to running view

# %%
record_to_file = False  # True | False
node_listener = NoCPerfMonNodeListener(
    sampling_intervals,
    num_samples,
    enable_list,
    record_to_file,
    extended_monitor_config=extended_monitor_config,
)
session.chipscope_view.add_node_listener(node_listener)

plotter = MeasurementPlot(enable_list, mock=False, figsize=(10, 7.5), tg=tg)
node_listener.link_plotter(plotter)

# Build Plotting Graphs
matplotlib.use("Qt5Agg")
plotter.build_graphs()

# %% [markdown]
# ## 8 - Main Event Loop
#
# This loop runs until you close the plotter.
# If you are using a finite amount of measurement samples, you can uncomment the if --> break statement to automatically return from execution of this cell upon completion of the burst.

# %%
# Run Main Event Loop
loop_count = 0
while True:
    session.chipscope_view.run_events()
    sleep(0.1)
    plotter.fig.canvas.draw()
    plotter.fig.canvas.flush_events()
    if not plotter.alive:
        break
    # Below will return on burst completion - uncomment if you want to try.
    # if all([x <= 0 for x in node_listener.num_samples.values()]):
    #     break

# %%
# Reset Traffic Generator
# This allows for a hard block-level reset of the traffic generator.

tg.block_reset()
