# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.10.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

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
# IBERT link example
# ==================

# %% [markdown]
# Description
# -----------
# This demo shows how to do four things:
# 1. Connect to a Versal target device via ChipScope Server (cs_server) and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Create single and multiple links
# 4. Do a simple loopback test for the links
#
# Requirements
# ------------
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. 2020.2 cs_server and hw_server applications
# 3. Python 3.7 environment
# 4. ChipScoPy pip installed
# 5. Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# %% [markdown]
# ## Step 1 - Setup the environment

# %% pycharm={"name": "#%%\n"}
from pathlib import Path
from more_itertools import one

from chipscopy import create_session, report_versions
from chipscopy.api.ibert import create_links, get_all_links, create_link_groups, create_eye_scans
from chipscopy.api.ibert.aliases import (
    PATTERN,
    RX_LOOPBACK,
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_VERT_RANGE,
    EYE_SCAN_VERT_STEP,
    EYE_SCAN_HORZ_STEP,
    EYE_SCAN_TARGET_BER,
)
from chipscopy.utils.printer import printer

CS_URL = "TCP:localhost:3042"
HW_URL = "TCP:localhost:3121"

# NOTE - To get refclk info for this design,
#  please see the DESIGN_INFO.txt file in the same folder as the PDI
EXAMPLES_DIR = Path.cwd().parent.parent
PDI_FILE = EXAMPLES_DIR.joinpath(
    "designs", "vck190", "production", "2.0", "GTY", "all_quads_10G", "all_quads_10G.pdi"
)

# %% [markdown]
# ## Step 2 - Create a session and connect to the server

# %% pycharm={"name": "#%%\n"}
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

device = session.devices.at(index=0)

# %% [markdown]
# ## Step 3 - Program the device with our example PDI

# %% pycharm={"name": "#%%\n"}
device.program(PDI_FILE)

# %% [markdown]
# ## Step 4 - Discover and setup the IBERT core

# %% pycharm={"name": "#%%\n"}
device.discover_and_setup_cores(ibert_scan=True)

if len(device.ibert_cores) == 0:
    printer("No IBERT core found! Exiting...", level="info")
    exit()

# Use the first available IBERT core from the device
ibert = device.ibert_cores.at(index=0)

ibert.print_hierarchy()

if len(ibert.gt_groups) == 0:
    printer("No GT Groups available for use! Exiting...", level="info")
    exit()

printer(
    f"GT Groups available - {[gt_group_obj.name for gt_group_obj in ibert.gt_groups]}", level="info"
)

# %% [markdown]
# ## Step 5 - Get first available Quad and all the 4 channels in it

# %% pycharm={"name": "#%%\n"}
first_quad = ibert.gt_groups.at(0)
ch_0 = one(first_quad.gts.filter_by(name="CH_0"))
ch_1 = one(first_quad.gts.filter_by(name="CH_1"))
ch_2 = one(first_quad.gts.filter_by(name="CH_2"))
ch_3 = one(first_quad.gts.filter_by(name="CH_3"))

# %% [markdown]
# ## Step 6 - Create links

# %% pycharm={"name": "#%%\n"}
all_links = create_links(
    rxs=[ch_0.rx, ch_1.rx, ch_2.rx, ch_3.rx], txs=[ch_0.tx, ch_1.tx, ch_2.tx, ch_3.tx]
)
printer(f"Created new links {all_links}", level="info")

# %% [markdown]
# ## Step 7 - Iterate over all links and do loopback test for each link
# #### Only if the PLLs are locked for the links, check for link lock. Without PLL lock there is no guarantee that links  will be locked when set to same RX and TX pattern

# %% pycharm={"name": "#%%\n"}
for link in get_all_links():
    printer(
        f"Setting both patterns to 'PRBS 7' + Loopback to 'Near-End PCS' for {link}", level="info"
    )

    props = {
        link.rx.property_for_alias[PATTERN]: "PRBS 7",
        link.rx.property_for_alias[RX_LOOPBACK]: "Near-End PCS",
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))

    props = {link.tx.property_for_alias[PATTERN]: "PRBS 7"}
    link.tx.property.set(**props)
    link.tx.property.commit(list(props.keys()))

    # Without PLL lock, the link will most likely not lock even if TX and RX patterns are the same
    if link.rx.pll.locked and link.tx.pll.locked:
        printer(f"RX and TX PLLs are locked for {link}. Checking for link lock...", level="info")
        assert link.status != "No link"
        printer(f"{link} is linked as expected", level="info")
    else:
        printer(
            f"RX and/or TX PLL are NOT locked for {link}. Skipping link lock check...", level="info"
        )

    link.refresh()
    link.generate_report()


# %% [markdown]
# ## Step 8 - Organize the links by putting them into a link group

# %%
link_group_0 = one(create_link_groups("Link group with all loopback'd links"))
printer(f"Created new link group {link_group_0}", level="info")
link_group_0.add(all_links)

# %% [markdown]
# ## Step 9 - Create an eye scan for a link

# %%
# This will create the eye scan and attach it to the RX in the link
create_eye_scans(target_objs=all_links.at(0))

link_with_scan = all_links.at(0)
eye_scan_for_link = link_with_scan.eye_scan
printer(f"Supported params for {eye_scan_for_link.name}", level="info")
for param in eye_scan_for_link.params.values():
    print(
        f"{param.name}\n"
        f"\tModifiable: {param.modifiable}\n"
        f"\tValid values: {param.valid_values}\n"
        f"\tDefault value: {param.default_value}\n"
    )

# %% [markdown]
# ## Step 10 - Set the eye scan params and run it

# %%
eye_scan_for_link.params[EYE_SCAN_HORZ_STEP].value = 4
eye_scan_for_link.params[EYE_SCAN_VERT_STEP].value = 4
eye_scan_for_link.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
eye_scan_for_link.params[EYE_SCAN_VERT_RANGE].value = "100%"
eye_scan_for_link.params[EYE_SCAN_TARGET_BER].value = 1e-5

eye_scan_for_link.start()

eye_scan_for_link.wait_till_done()

# %% [markdown]
# ## Step 11 - View the scan
# #### This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.3/ibert/scan.html#scan-plots)
# #### The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %%
eye_scan_for_link.plot.show()

# %%
