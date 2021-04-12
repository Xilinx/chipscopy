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
# # IBERT eye scan example

# %% [markdown]
# ## Description
# This demo shows how to do four things:
# 1. Connect to a Versal target device via ChipScope Server (cs_server) and Hardware Server (hw_server)
# 2. Program a Versal target device using a design PDI file
# 3. Create eye scans + start/stop them
# 4. View/Save eye scan plots
#
# ## Requirements
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. 2020.2 cs_server and hw_server applications
# 3. Python 3.7 environment
# 4. ChipScoPy pip installed
# 5. Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`
# 6. Plotting support installed - Please do so, using the command `pip install chipscopy[plotly]`

# %% [markdown]
# ## Step 1 - Setup the environment

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
from pathlib import Path
from more_itertools import one

from rich.style import Style

from chipscopy import create_session, report_versions, report_hierarchy
from chipscopy.api.ibert.aliases import (
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_VERT_RANGE,
    EYE_SCAN_VERT_STEP,
    EYE_SCAN_HORZ_STEP,
    EYE_SCAN_TARGET_BER,
)
from chipscopy.api.ibert import create_eye_scans, create_links
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

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

device = session.devices.at(index=0)

# %% [markdown]
# ## Step 3 - Program the device with our example PDI

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
device.program(PDI_FILE)

# %% [markdown]
# ## Step 4 - Discover and setup the IBERT core

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
device.discover_and_setup_cores(ibert_scan=True)

if len(device.ibert_cores) == 0:
    printer("No IBERT core found! Exiting...", level="info")
    exit()

# Use the first available IBERT core from the device
ibert = device.ibert_cores.at(index=0)

report_hierarchy(ibert)

if len(ibert.gt_groups) == 0:
    printer("No GT Groups available for use! Exiting...", level="info")
    exit()

printer(
    f"GT Groups available - {[gt_group_obj.name for gt_group_obj in ibert.gt_groups]}", level="info"
)

# %% [markdown]
# ## Step 5 - Get first available Quad and all the 4 channels in it

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
first_quad = ibert.gt_groups.at(0)
ch_0 = one(first_quad.gts.filter_by(name="CH_0"))
ch_1 = one(first_quad.gts.filter_by(name="CH_1"))
ch_2 = one(first_quad.gts.filter_by(name="CH_2"))
ch_3 = one(first_quad.gts.filter_by(name="CH_3"))

# %% [markdown]
# ## Step 6 - Create scan using RX

# %% pycharm={"name": "#%%\n"}
eye_scan_0 = one(create_eye_scans(target_objs=ch_0.rx))

printer(f"Created new eye scan {eye_scan_0}", level="info")

printer(f"Supported params for {eye_scan_0.name}", level="info")
for param in eye_scan_0.params.values():
    print(
        f"{param.name}\n"
        f"\tModifiable: {param.modifiable}\n"
        f"\tValid values: {param.valid_values}\n"
        f"\tDefault value: {param.default_value}\n"
    )


# %% [markdown]
# ## Step 7 - Set the eye scan parameters, start the eye scan & wait for it to complete

# %% pycharm={"name": "#%%\n"}
eye_scan_0.params[EYE_SCAN_HORZ_STEP].value = 1
eye_scan_0.params[EYE_SCAN_VERT_STEP].value = 1
eye_scan_0.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
eye_scan_0.params[EYE_SCAN_VERT_RANGE].value = "100%"
eye_scan_0.params[EYE_SCAN_TARGET_BER].value = 1e-5

eye_scan_0.start()

eye_scan_0.wait_till_done()

# %% [markdown]
# ## Step 8 - View eye_scan_0.
# #### This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.2/ibert/scan.html#scan-plots)
# #### The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %% pycharm={"name": "#%%\n"}
eye_scan_0.plot.show()

# %% [markdown] pycharm={"name": "#%% md\n"}
# ## Step 9 - Generate report for the scan.

# %% pycharm={"name": "#%%\n"}
eye_scan_0.generate_report()


# %% [markdown]
# ## Step 10 - Create scan using Link

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
link_0 = one(create_links(rxs=ch_1.rx, txs=ch_1.tx))

eye_scan_1 = one(create_eye_scans(target_objs=link_0))

printer(f"Created new eye scan {eye_scan_1}", level="info")

printer(f"Supported params for {eye_scan_1.name}", level="info")
for param in eye_scan_1.params.values():
    print(
        f"{param.name}\n"
        f"\tModifiable: {param.modifiable}\n"
        f"\tValid values: {param.valid_values}\n"
        f"\tDefault value: {param.default_value}\n"
    )

# %% [markdown]
# ## Step 11 - Start the eye scan and wait till it's done

# %% jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
eye_scan_1.params[EYE_SCAN_HORZ_STEP].value = 1
eye_scan_1.params[EYE_SCAN_VERT_STEP].value = 1
eye_scan_1.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
eye_scan_1.params[EYE_SCAN_VERT_RANGE].value = "100%"
eye_scan_1.params[EYE_SCAN_TARGET_BER].value = 1e-5

eye_scan_1.start()

eye_scan_1.wait_till_done()

# %% [markdown]
# ## Step 12 - View eye_scan_1.
# #### This requires Plotly to be installed. See how to install it [here](https://pages.gitenterprise.xilinx.com/chipscope/chipscopy/2020.3/ibert/scan.html#scan-plots)
# #### The plot may not display if this notebook is run in Jupyter Lab. For details, see [link](https://plotly.com/python/getting-started/#jupyterlab-support-python-35)

# %% pycharm={"name": "#%%\n"}
eye_scan_1.plot.show()


# %% [markdown]
# ## Step 13 - Generate report for the scan.

# %% pycharm={"name": "#%%\n"}
eye_scan_1.generate_report()

# %%
