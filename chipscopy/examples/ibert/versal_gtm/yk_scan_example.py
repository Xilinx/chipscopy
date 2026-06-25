# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2022, Xilinx, Inc.<br>
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
# # IBERT yk scan example

# %% [markdown]
# ## Description
# This example shows how to interact with the IBERT GTM (Integrated Bit Error Ratio Tester) debug core service via ChipScoPy APIs. It demonstrates the YK scan feature, which is unique to GTM transceivers.
#
# - Program the ChipScoPy CED design onto the target device using the MESA manifest
# - Discover the GTM IBERT core and select a quad from the manifest
# - Create a link and configure link properties for loopback testing
# - Run and plot YK scans on the linked receiver
#
# ### User Configuration
# - `IBERT_QUAD` environment variable: Select a specific GTM quad (e.g., `Quad_204`). Default: first GTM quad from manifest.
#
# ## Requirements
# - Local or remote AMD Versal board with GTM transceivers (VPK120, VHK158)
# - AMD hw_server 2026.1+ installed and running
# - AMD cs_server 2026.1+ installed and running
# - Python 3.10 or greater installed
# - ChipScoPy 2026.1+ installed
# - Jupyter notebook support and extra libs needed - Please do so, using the command pip install chipscopy[jupyter, core-addons]
# - [External loopback](https://www.samtec.com/kits/optics-fpga/hspce-fmcp/) (recommended) or internal loopback
#

# %% [markdown]
# ## 1 - Initialization: Imports
#
# After this step:
#
# * Required functions and classes are imported
# * Paths to server(s) and files are set correctly

# %%
import os
import time
from collections import Counter
from threading import Event
import matplotlib

from chipscopy import (
    create_session,
    report_versions,
    report_hierarchy,
    delete_session,
)
from chipscopy.examples.mesa import resolve_example_design
from chipscopy.api.ibert import create_links, create_yk_scans
from chipscopy.api.ibert.aliases import (
    PATTERN,
    RX_LOOPBACK,
)

try:
    # Notebook: interactive ipympl backend for live plot updates
    get_ipython().run_line_magic("matplotlib", "widget")
except NameError:
    # Script (nbconvert'd): use a GUI backend so the plot updates live
    try:
        matplotlib.use("QtAgg")
    except Exception:
        matplotlib.use("TkAgg")

import matplotlib.pyplot as plt

plt.ion()

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step:
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
EXAMPLE_ID = "yk_scan_example"
PROG_DEVICE = True

# Optional GTM quad selection. Empty string -> auto-pick the first quad from the
# design manifest. Works in both MESA and direct mode.
IBERT_QUAD = os.getenv("IBERT_QUAD", "")

# Direct mode: set these to use your own design files (skips MESA).
PROGRAMMING_FILE = ""
PROBES_FILE = ""

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

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
# After this step:
# * Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it using family from manifest
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

if PROG_DEVICE:
    if design_manifest is not None and not design_manifest.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)

# %% [markdown]
# ## 4 - Discover and setup the IBERT GTM core
#
# Debug core discovery initializes the ChipScoPy server debug cores. The manifest is used to find the GTM core specifically (since the device may also have GTYP cores).
#
# After this step:
#
# - The cs_server is initialized and ready for use
# - The GTM IBERT core is identified from the manifest
# - The `yk_scan` feature is verified

# %%
device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery complete")

if len(device.ibert_cores) == 0:
    print("No IBERT core found! Exiting...")
    exit()

# Verify yk_scan feature is available on the GTM core
if design_manifest and not design_manifest.has_feature("ibert_gtm", "yk_scan"):
    raise RuntimeError(
        "YK scan feature not available on this platform's GTM core. "
        "This example requires a GTM IBERT core with yk_scan support."
    )

print(f"IBERT cores on device: {[f'{ibert.name}' for ibert in device.ibert_cores]}")
print("yk_scan feature confirmed for ibert_gtm")

# %% [markdown]
# ## 5 - Select GTM quad and resolve hardware
#
# The manifest provides the GTM quad names. We find the matching IBERT hardware core and select the target quad for link creation and YK scan.

# %%
if design_manifest is not None:
    gtm_core = design_manifest.get_ibert_core(
        filter_fn=lambda name, core: name == "ibert_gtm"
    )
    if not gtm_core:
        raise RuntimeError("No ibert_gtm core found in design_manifest")

    ibert_core_type, ibert_config = gtm_core
    available_quads = ibert_config.quad_names or []

    print(f"GTM core from design_manifest: {ibert_core_type}")
    print(f"Available GTM quads: {available_quads}")
    print(f"Features: {ibert_config.features}")
else:
    # Direct mode: there is no manifest, so the user must point us at a
    # specific GTM quad via env var. The yk_scan capability cannot be
    # verified without a manifest; assume the user enabled it in the design
    # and let the IBERT API surface a clear error later if it isn't.
    if not IBERT_QUAD:
        raise RuntimeError(
            "Direct mode (PROGRAMMING_FILE provided) requires IBERT_QUAD to "
            "be set to the target GTM quad name (e.g. "
            "export IBERT_QUAD=Quad_204). In direct mode we cannot infer the "
            "available GTM quads from a design_manifest, so the user must "
            "specify it explicitly."
        )
    ibert_core_type = "ibert_gtm"
    available_quads = [IBERT_QUAD]
    print(f"Direct mode: using GTM quad {IBERT_QUAD}")

# Select quad (user-specified or default to first)
if IBERT_QUAD:
    if IBERT_QUAD not in available_quads:
        raise RuntimeError(
            f"Quad '{IBERT_QUAD}' not in GTM design_manifest quads: {available_quads}")
    selected_quad_name = IBERT_QUAD
    print(f"User-selected quad: {selected_quad_name}")
else:
    selected_quad_name = available_quads[0]
    print(f"Default: using first quad: {selected_quad_name}")

# Find the GTM IBERT hardware core by matching quad names
ibert_gtm = None
for idx in range(len(device.ibert_cores)):
    candidate = device.ibert_cores.at(index=idx)
    gt_names = [g.name for g in candidate.gt_groups]
    if any(qn in gt_names for qn in available_quads):
        ibert_gtm = candidate
        break

if ibert_gtm is None:
    raise RuntimeError("No hardware IBERT core matching GTM quads found on device")

report_hierarchy(ibert_gtm)

# Resolve selected quad to hardware object
quad_list = ibert_gtm.gt_groups.filter_by(name=selected_quad_name)
if not quad_list:
    raise RuntimeError(f"Quad '{selected_quad_name}' not found in hardware")
gt_group = quad_list[0]

print(f"\nSelected quad: {gt_group.name}")
print(f"Channels in quad: {[gt.name for gt in gt_group.gts]}")

# %% [markdown]
# ## 6 - Create a link and configure for loopback
#
# Before running the YK scan, we create a link on the first channel of the selected GTM quad. We set the TX and RX patterns to match and enable internal loopback so the scan can operate without external cabling (though external loopback is recommended for best results).

# %%
# Create a link on the first channel of the selected quad
tx = gt_group.gts[0].tx
rx = gt_group.gts[0].rx

links = create_links(txs=[tx], rxs=[rx])
link = links[0]
print(f"--> Created link: {link.name}")

# Set TX and RX patterns to match and enable internal loopback
PATTERN_VALUE = "PRBS 31"
LOOPBACK_VALUE = "Near-End PMA"

props = {link.tx.property_for_alias[PATTERN]: PATTERN_VALUE}
link.tx.property.set(**props)
link.tx.property.commit(list(props.keys()))

props = {
    link.rx.property_for_alias[PATTERN]: PATTERN_VALUE,
    link.rx.property_for_alias[RX_LOOPBACK]: LOOPBACK_VALUE,
}
link.rx.property.set(**props)
link.rx.property.commit(list(props.keys()))

print(f"--> Set TX/RX pattern to '{PATTERN_VALUE}' and loopback to '{LOOPBACK_VALUE}'")

link.tx.reset()
link.rx.reset()

# Verify link lock
assert link.rx.pll.locked and link.tx.pll.locked, "PLL not locked!"
print(f"--> RX and TX PLLs are locked")
assert link.status != "No link", f"Link not established: status={link.status}"
print(f"--> Link status: {link.status} - Link is locked")


# %% [markdown]
# ## 7 - Define YK Scan Update Method
#
# This method will be called each time the YK scan updates, allowing it to update its graphs in real time.

# %%
def yk_scan_updates(obj):
    global figure, ax, ax2, ax3

    if ax.lines:
        for line in ax.lines:
            line.set_xdata(range(len(obj.scan_data[-1].slicer)))
            line.set_ydata(list(obj.scan_data[-1].slicer))
    else:
        ax.scatter(range(len(obj.scan_data[-1].slicer)), list(obj.scan_data[-1].slicer), color='blue')

    bin_size = 5
    bin_counts = Counter()
    for sample in obj.scan_data:
        for v in sample.slicer:
            bin_counts[int(v // bin_size) * bin_size] += 1
    bins = range(0, 100, bin_size)
    counts = [bin_counts.get(b, 0) for b in bins]
    max_count = max(counts) if counts else 1
    ax2.cla()
    ax2.barh(list(bins), counts, height=bin_size * 0.8, color='blue', align='edge')
    ax2.set_xlim(0, max_count * 1.1)
    ax2.set_xlabel("Count")
    ax2.set_ylabel("Amplitude (%)")
    ax2.set_ylim(0, 100)
    ax2.set_yticks(range(0, 100, 20))
    ax2.set_title("Histogram")

    if ax3.lines:
        for line3 in ax3.lines:
            if len(obj.scan_data) - 1 > ax3.get_xlim()[1]:
                ax3.set_xlim(0, ax3.get_xlim()[1] + 10)
            line3.set_xdata(list(line3.get_xdata()) + [len(obj.scan_data) - 1])
            line3.set_ydata(list(line3.get_ydata()) + [obj.scan_data[-1].snr])
    else:
        ax3.plot(len(obj.scan_data) - 1, obj.scan_data[-1].snr)

    figure.canvas.draw_idle()


# %% [markdown]
# ## 8 - Create YK Scan
#
# The YK scan is created on the RX of our linked channel. The update callback provides real-time plot updates.

# %%
# Create YK scan on the linked RX channel
yk = create_yk_scans(target_objs=link.rx)[0]

yk.updates_callback = yk_scan_updates
print(f"YK scan created on: {link.rx}")

# %% [markdown]
# ## 9 - Run YK Scan
#
# Initialize the plots and start the YK Scan to begin updating the plots. 
# YK Scan plot should contain three subplots, these plots should look something like:
# ![yk_scan_example.png](./yk_scan_example.png)
# Note: Depending on the hardware setup and loopback mode (internal vs external), the plot might look different.

# %%
#This sets up the subplots necessary for the 
figure, (ax, ax2, ax3) = plt.subplots(3, constrained_layout = True, num="YK Scan")

ax.set_xlabel("ES Sample")
ax.set_ylabel("Amplitude (%)")
ax.set_xlim(0,2000)
ax.set_ylim(0,100)
ax.set_yticks(range(0, 100, 20))
ax.set_title("Slicer eye")

ax2.set_xlabel("Count")
ax2.set_ylabel("Amplitude (%)")
ax2.set_xlim(0,2000)
ax2.set_ylim(0,100)
ax2.set_yticks(range(0, 100, 20))
ax2.set_title("Histogram")

ax3.set_xlabel("SNR Sample")
ax3.set_ylabel("SNR (dB)")
ax3.set_xlim(0,10)
ax3.set_ylim(-10,100)
ax3.set_title("Signal-to-Noise Ratio")

plt.show(block=False)

yk.start()

end_time = time.time() + 10
while time.time() < end_time:
    figure.canvas.draw_idle()
    figure.canvas.flush_events()
    time.sleep(0.1)

# %% [markdown]
# ## 10 - Stop YK Scan
# Stops the YK scan from running.

# %%
# We use Event to wait until the stop callback is sent, or it times out
stopped = Event()
def yk_scan_stop_callback(obj, error):
    print(f"YK Scan {yk.name} stopped")
    if error:
        print(f"YK Scan error: {error}")
    stopped.set()

yk.stop_callback = yk_scan_stop_callback
yk.stop()
# Wait for the stop callback if possible or timeout
STOP_TIMEOUT_SECONDS = 15
if not stopped.wait(timeout=STOP_TIMEOUT_SECONDS):
    print("Failed to stop YK Scan")

# %%
## When done with testing, close the connection
delete_session(session)
