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
import os
import re

# %%
import chipscopy
from chipscopy import create_session
import networkx as nx
import matplotlib.pyplot as plt
import colorama

# %%
if "PYCHARM_HOSTED" not in os.environ:
    colorama.init(convert=True)

# %%
server_dict = {
    "ibert-1": {"board": "tenzing", "design_name": "pcie_spoof", "ltx": "pcie_spoof.ltx"},
    "ibert-0": {"board": "tenzing", "design_name": "pcie_spoof", "ltx": "pcie_spoof.ltx"},
    "xsjltlab45": {"board": "v350", "design_name": "pcie_demo", "ltx": "xilinx_pcie_versal_ep.ltx"},
    "XCOIPSLAB30": {
        "board": "v350",
        "design_name": "pcie_demo",
        "ltx": "xilinx_pcie_versal_ep.ltx",
    },
}

# %%
server_name = "ibert-1"

# %% [markdown]
# HUB_ADDRESSES = [0xA4200000]
# HUB_ADDRESSES = [0x00080000000]
# CS_URL = "TCP:localhost:3042"
# HW_URL = "TCP:xsjltlab45:3121"

# %%
# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", f"TCP:{server_name}:3121")

# %%
EXAMPLES_DIR = os.path.dirname(os.path.realpath(__file__ + "/.."))
BOARD = server_dict[server_name]["board"]
# PDI_FILE = f"{EXAMPLES_DIR}/designs/{BOARD}/pcie_demo/pcie_demo_wrapper.pdi"
LTX_FILE = (
    f"{EXAMPLES_DIR}/designs/{BOARD}"
    f"/{server_dict[server_name]['design_name']}/{server_dict[server_name]['ltx']}"
)


# %%
def cap(s):
    return ".".join(i.capitalize() for i in s.split("."))


# %%
if __name__ == "__main__":
    print(f"chipscopy api version: {chipscopy.__version__}")
    print()

    session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)

    print(f"hw_server {session.hw_server.url} info:")
    print(session.hw_server.version_info)
    print()
    print(f"cs_server {session.cs_server.url} info:")
    print(session.cs_server.version_info)
    print("\n")

    # Use the first available device and setup its debug cores
    if len(session.devices) == 0:
        print("\nNo devices detected")

    versal_device = session.devices[0]

    print(f"Discovering debug cores...")
    versal_device.discover_and_setup_cores(ltx_file=LTX_FILE)

    # How many PCIe cores did we find?
    pcie_count = len(versal_device.pcie_cores)
    print(f"\nFound {pcie_count} PCIe cores in design")

    if pcie_count == 0:
        print("No PCIe core found! Exiting...")
        exit()

    pcie_cores = versal_device.pcie_cores
    for index, pcie_core in enumerate(pcie_cores):
        print(f"    PCIe Core #{index}: NAME={pcie_core.name}, UUID={pcie_core.uuid}")

    pcie = pcie_cores[0]

    plt = pcie.get_plt().show()
