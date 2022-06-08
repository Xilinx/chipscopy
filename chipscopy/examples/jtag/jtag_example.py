# %% [markdown] pycharm={"name": "#%%\n"}
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright 2022 Xilinx, Inc.<br><br>
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
# # ChipScoPy JTAG Access Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# This demo shows how to perform JTAG operations on cables or devices in scan chain using the ChipScoPy Python API.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 or greater
# - Python 3.8 or greater installed
# - ChipScoPy 2022.1 or greater installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - Paths to server(s) and files are set correctly

# %% pycharm={"name": "#%%\n"}
import os
import sys

from chipscopy import create_session, report_versions
from chipscopy.api.jtag import JtagState, JtagSequence

# %%
# Make sure to start the hw_server prior to running.
# Specify location of the running hw_server below.
# The default is localhost - but can be other locations on the network.
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
print(f"HW_URL={HW_URL}")

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to `hw_server`
# - Versions are detected and reported to stdout
#
# *NOTE*: No `cs_server` is required for this example.

# %% pycharm={"name": "#%%\n"}
session = create_session(hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
#    ## 3 - JTAG Cable Class
#    
#    The JTAG cable class allows operations to run against the whole scan chain. This example finds the first cable in the scan chain and locks the cable to ensure exclusive access.

# %% pycharm={"name": "#%%\n"}
jtag_cables = session.jtag_cables

# Lock JTAG cable. This prevents other clients from performing any JTAG shifts or state changes on 
# the scan chain.
jtag_cables[0].lock()

# %% [markdown]
# ## 4 - JTAG Sequence
#
# A jtag sequence represents a set of operations to perform. This sequence object holds a reference to the cable object upon which the sequence will be run. Multiple commands may be appended to the sequence.

    # %% pycharm={"name": "#%%\n"}
    # Create JTAG sequence object
    seq = JtagSequence(jtag_cables[0])

    # Add command to move JTAG state machine to TEST-LOGIC-RESET state and then generate 5 JTAG clocks
    seq.set_state(JtagState.RESET, 5)

    # Add command to shift 256-bit data in DRSHIFT state
    seq.dr_shift(
        data=0x000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F,
        size=256,
        capture=True,
        end_state=JtagState.IDLE,
    )

    # Add command to shift data in DRSHIFT state. JTAG TDI signal will be set to 1 for 70 clocks (bits)
    seq.dr_shift(tdi=1, size=70, capture=True, end_state=JtagState.IDLE)

    shift_data_size = 16
    shift_data = 0x101112131415161718191A1B1C1D1E1F .to_bytes(shift_data_size, sys.byteorder)
    # Add command to shift data in DRSHIFT state. In this case data is 16 bytes in bytearray format.
    seq.dr_shift(
        data=bytearray(shift_data), size=shift_data_size * 8, capture=True, end_state=JtagState.IDLE
    )

# %% [markdown]
#    ## 5 - Run sequence and print results

    # %% pycharm={"name": "#%%\n"}
    # Run JTAG commands added in the sequence object
    seq_results = seq.run()

    # Convert JTAG sequence result from bytearray to hexadecimal format
    hex_result = [
        hex(int.from_bytes(seq_results[i], sys.byteorder)) for i in range(0, len(seq_results))
    ]
    print("Result of operations in JTAG sequence - ", hex_result)
    # Unlock the locked JTAG device
    jtag_cables[0].unlock()

# %% [markdown]
#    ## Step 6 - JTAG Device Class
#
# JTAG operations can also be performed on individual devices in the scan chain instead of above example of performing JTAG operations on a JTAG cable (whole scan chain). This is a convenience class to target a specific device.

# %% pycharm={"name": "#%%\n"}

    # Get devices on JTAG chain
    jtag_devices = session.jtag_devices

    # Lock first JTAG device. This prevents other clients from performing any JTAG shifts or state changes on the scan
    # chain.
    jtag_devices[0].lock()

    # Create JTAG sequence object
    seq = JtagSequence(jtag_devices[0])

    # Add command to move JTAG state machine to TEST-LOGIC-RESET state and then generate 10 JTAG clocks
    seq.set_state(JtagState.RESET, 10)

    # Add command to shift 128-bit data in DRSHIFT state
    seq.dr_shift(
        data=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=128, capture=True, end_state=JtagState.IDLE
    )

    # Run JTAG commands added in the sequence object
    seq_results = seq.run()

    # Unlock the locked JTAG device
    jtag_devices[0].unlock()

    # Clear JTAG commands in sequence object. After clear, this object can be reused for new set of JTAG operations
    seq.clear()

    # Convert JTAG sequence result from bytearray to hexadecimal format
    hex_result = [
        hex(int.from_bytes(seq_results[i], sys.byteorder)) for i in range(0, len(seq_results))
    ]
    print("Result of operations in JTAG sequence - ", hex_result)
