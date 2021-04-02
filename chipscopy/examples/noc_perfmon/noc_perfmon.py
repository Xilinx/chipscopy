#!/usr/bin/env python
# coding: utf-8
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

# %%

# NoC Perfmon Example Dashboard
# =============================

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
# 2. 2020.2+ cs_server and hw_server applications
# 3. Python 3.7 environment
# 4. chipscopy package installed in your environment
#
# ---

# ## Step 1 - Set up environment

# %%


import os
import matplotlib  # used by nbconvert'd script

# Specify locations of the running hw_server and cs_server below.
from time import sleep

# TODO: dbk cleanup before release
from chipscopy.client.util.xsa_utils import XSA
from chipscopy.api.noc import (
    TC_BEW,
    TC_BER,
    NoCPerfMonNodeListener,
)
from chipscopy.api.noc.plotting_utils import MeasurementPlot


CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
XSA_FILE = os.getenv("XSA_FILE", None)

print(f"HW_URL={HW_URL}")
print(f"CS_URL={CS_URL}")

assert XSA_FILE is not None


# ## Step 2 - Create a session and connect to the server(s)
# Here we create a new session and print out some versioning information for diagnostic purposes.

# %%


from chipscopy import __version__
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

xsa = XSA(XSA_FILE)
hw_handoff = xsa.hardware_handoff
if program_device:
    print("Programming device with PDI from supplied xsa")
    versal_device.program(xsa.design_fileset[".pdi"])

print(f"Discovering debug cores...", end="")
versal_device.discover_and_setup_cores(noc_scan=True)
print("Complete!")

noc = versal_device.noc_core

print()
scan_nodes = ["DDRMC_MAIN_0", "NOC_NMU512_X0Y0"]
print("Enumerating nodes: ", end="")
for node in scan_nodes:
    print(f"{node}, ", end="")
print("...", end="")

# this will setup the nodes on the server side and return the nodes successfully enumerated
enable_list = noc.enumerate_noc_elements(scan_nodes)
print("complete!")


supported_periods = noc.get_supported_sampling_periods(
    *hw_handoff.get_ref_clk_freqs(), hw_handoff.get_ddrmc_freq_mhz()
)

# done with XSA
if XSA_FILE:
    xsa.close()

print("Supported sampling periods:")
for domain, periods in supported_periods.items():
    print(f"  {domain}:")
    for p in periods:
        print(f"    {p:.0f}ms", end="")
    print()


# ## Select Timebase and Nodes to Monitor
#
# For the various clock domains we must select a sampling period from the hardware supported values. The debug cable used will dictate how much bandwidth is available, so high frequency sampling may not actually produce data at the specified rate. Recommendation is ~500ms for jtag.
#
# Then the user must decide what to monitor--again the bandwidth is a definite consideration here. Plot performance may become the bottleneck (Optimizations will come later in the renderer or agg backend). The guidance here is to pick up to 4 nodes to monitor.

# %%


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
for domain, period in sampling_intervals.items():
    print(f"  {domain}: {period:.0f}ms")


# ### Configure Monitors
#
#
# As a precaution, it's a good idea to use the set mutually inclusive '&' operator to make sure that an invalid node context isn't supplied to the configure API.
#
# Using the set of nodes and the desired sampling periods it's time to ask the service to start pushing metric data. Two additional arguments are required to this API.
#
# #### Traffic class
#
# This is a bit-or field of the requested traffic classes. Note, One monitor is dedicated to read traffic classes and the other to write--so all read TCs will apply to one channel and all write TCs to the other. `Best effort` is a good place to start.
#
# #### Number of Samples
#
# The number of samples allows for a burst of measurements to be taken and then the underlying service will tear down the monitors and stop pumping data back to the client. `-1` denotes that sampling shall continue indefinitely.

# %%


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


# ## Create Event Listener and Plotter

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

plotter = MeasurementPlot(enable_list, mock=False, figsize=(10, 7.5), tg=None)
node_listener.link_plotter(plotter)


# ### Build Plotting Graphs

# %%


matplotlib.use("Qt5Agg")
plotter.build_graphs()


# ###  Run Main Event Loop
#
# This loop does not exit. Interrupt this kernel if you want to make changes and rerun prior cells.
#
# If you are using a finite amount of measurement samples, you can uncomment the if --> break statement to automatically return from execution of this cell upon completion of the burst.

# %%


loop_count = 0
while True:
    session.chipscope_view.run_events()
    sleep(0.1)
    plotter.fig.canvas.draw()
    plotter.fig.canvas.flush_events()
    if not plotter.alive:
        break
    # if all([x <= 0 for x in node_listener.num_samples.values()]):
    #     break
