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

# ILA Advanced Trigger Example
# =========================

# Description
# -----------
# This demo shows how to use the ILA Advanced Trigger Mode.
# In this mode, the trigger setup is described in text using the ILA Trigger State Machine (TSM) language.
# See UG908 Vivado Design User Guide: Programming and Debugging, Appendix B "Trigger State Machine Language Description". 
#
#
# Requirements
# ------------
# The following is required to run this demo:
# 1. Local or remote access to a Versal device
# 2. 2024.1 cs_server and hw_server applications
# 3. Python 3.8 environment
# 4. A clone of the chipscopy git enterprise repository:
#    - https://gitenterprise.xilinx.com/chipscope/chipscopy
#
# ---

# ## Step 1 - Set up environment

import os
from enum import Enum
import chipscopy
from chipscopy import (
    create_session,
    get_design_files,
    null_callback,
    report_versions,
    delete_session,
)
from chipscopy.api.ila import ILAStatus, ILAWaveform
from io import StringIO
from pprint import pformat

# +
# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vck190")
PROG_DEVICE = os.getenv("PROG_DEVICE", 'True').lower() in ('true', '1', 't')
# -

design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
PROGRAMMING_FILE = design_files.programming_file
PROBES_FILE = design_files.probes_file
assert os.path.isfile(PROGRAMMING_FILE)
assert os.path.isfile(PROBES_FILE)

print(f"HW_URL={HW_URL}")
print(f"CS_URL={CS_URL}")
print(f"PDI={PROGRAMMING_FILE}")
print(f"LTX={PROBES_FILE}")

# ## Step 2 - Create a session and connect to the server(s)
# Here we create a new session and print out some versioning information for diagnostic purposes.
# The session is a container that keeps track of devices and debug cores.

print(f"Using chipscopy api version: {chipscopy.__version__}")
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# ## Step 3 - Get our device from the session

# Use the first available device and setup its debug cores
if len(session.devices) == 0:
    raise ValueError("No devices detected")
print(f"Device count: {len(session.devices)}")
versal_device = session.devices.get(family="versal")

# ## Step 4 - Program the device with our example programming file

print(f"Programming {PROGRAMMING_FILE}...")
if PROG_DEVICE:
    versal_device.program(PROGRAMMING_FILE)
else:
    print("skipping programming")

# ## Step 5 - Detect Debug Cores

print(f"Discovering debug cores...")
versal_device.discover_and_setup_cores(ltx_file=PROBES_FILE)

ila_count = len(versal_device.ila_cores)
print(f"\nFound {ila_count} ILA cores in design")

if ila_count == 0:
    print("No ILA core found! Exiting...")
    raise ValueError("No ILA cores detected")

# List all detected ILA Cores
ila_cores = versal_device.ila_cores
for index, ila_core in enumerate(ila_cores):
    print(f"    ILA Core #{index}: NAME={ila_core.name}, UUID={ila_core.core_info.uuid}")

# +
# Get the ILA cores matching a given name. filter_by returns a list, even if just one item is present.
my_ila = versal_device.ila_cores.filter_by(name="chipscopy_i/counters/ila_slow_counter_0")[0]

print(f"USING ILA: {my_ila.name}")
# -

# ## Step 6 - Get Information for this ILA Core
# Note:
# - 'has_advanced_trigger' is True. This ILA supports the advanced trigger feature.
# - 'tsm_counter_widths' shows 4 counters of bit width 16.

print("\nILA Name:", my_ila.name)
print("\nILA Core Info", my_ila.core_info)
print("\nILA Static Info", my_ila.static_info)

# ## Step 7 -  Trigger Immediately using Advanced Trigger Mode
#
# Trigger State Machine trigger descriptions may be in a text file, or in a io.StringIO object.
# Some of the ILA status information applies only to Advanced Trigger Mode:
# - tsm_counters
# - tsm_flags
# - tsm_state
# - tsm_state_name

# +
TRIGGER_NOW_TSM = StringIO(
"""
    state my_state0:
        trigger;
"""
)

# Note, if the TSM text is in a file, you can give the file path string as the first argument.
my_ila.run_advanced_trigger(TRIGGER_NOW_TSM, trigger_position=0, window_count=1, window_size=8)


my_ila.refresh_status()
print("\nILA Status:\n")
print("Trigger State Machine counter values:      ", my_ila.status.tsm_counters)
print("Trigger State Machine flags:               ", my_ila.status.tsm_flags)
print("Trigger State Machine current state index: ", my_ila.status.tsm_state)
print("Trigger State Machine current state name : ", my_ila.status.tsm_state_name)
# -

# ## Step 8 - Upload Captured Waveform
# Wait at most half a minutes, for ILA to trigger and capture data.

my_ila.wait_till_done(max_wait_minutes=0.5)
my_ila.upload()
if not my_ila.waveform:
    print("\nUpload failed!")

# ## Step 9 - Print samples for probe 'chipscopy_i/counters/slow_counter_0_Q_1'. 
#
# Using the function ILAWaveform.get_data(), the waveform data is put into a sorted dict.
# First 4 entries in sorting order are: trigger, sample index, window index, window sample index.
# Then comes probe values. In this case just one probe.

# +
counter_probe_name = 'chipscopy_i/counters/slow_counter_0_Q_1'

def print_probe_values(waveform: ILAWaveform, probe_names: [str]):
    samples = waveform.get_data(
        probe_names,
        include_trigger=True,
        include_sample_info=True,
    )
    for trigger, sample_index, window_index, window_sample_index, value in zip(*samples.values()):
        trigger = "<-- Trigger" if trigger else ""
        print(
            f"Window:{window_index}  Window Sample:{window_sample_index}  dec:{value:10}  hex:0x{value:08X} {trigger}"
        )

print_probe_values(my_ila.waveform, [counter_probe_name])
# -

# ## Step 10 - Check if TSM is Valid
# - The TSM below has undefined probe names and undefined states.
# - Use "compile_only=True" argument when just checking if the TSM text is valid.
# - The run_advanced_trigger() function returns a tuple with 2 values: "error_count" and "error_message".

# +
TSM_WITH_ERRORS = StringIO(
    """
    state state_a:
      if (chipscopy_ex_i/counters/slow_counter_0_Q_1 == 32'hXX33_0000 &&
          chipscopy_i/counters/slow_sine_Dout >= 'habcd) then
        trigger;
      elseif (chipscopy_i/counters/slow_sine_Dout >= 'habcd) then
        reset_counter $counter0;
        goto state_2;
      else
        reset_counter $counter1;
        goto state_3;
      endif
    state state_b:
      if (chipscopy_i/counters23/slow_counter_0_Q_1 == 32'h3333_0000) then
        trigger;
      else
        reset_counter $counter3;
        goto state_2;
      endif
    state state_c:
      goto state_3;
    """
)

# Check the TSM text for errors, using "compile_only=True
#
error_count, error_message = my_ila.run_advanced_trigger(TSM_WITH_ERRORS, compile_only=True)
print(f'\n\nThe Advanced Trigger State machine "TSM_WITH_ERRORS" has {error_count} error(s).'
      f'\n\n{error_message}')


# -

# ## Step 11 - Define a Status Progress Monitor Function
# Monitor TSM specific status, when ILA capture is active.

def status_progress(future):
    """Called in Event Thread"""
    st = future.progress

    if st.is_full:
        print(f"\nAll data has been captured.")
    else:
        print(f"State: {st.tsm_state_name}   Counters: {st.tsm_counters}    Flags: {st.tsm_flags}")       


# ## Step 12 - Run Trigger State Machine with Flags and Counters
# In STATE_A:
# - Remain in STATE_A until hex value ending with "33_0000", has occurred 8 times (counter values 0-7).
# - Set \$flag0
# - Go to state STATE_B
#
# In STATE_B:
# - Count hex value ending with "AAA_BBBB" 10 times (counter values 0-9).
# - Then set \$flag1 and trigger.

# +
TSM_FLAGS_COUNTERS = StringIO(
    f"""
    state STATE_A:
        if ( {counter_probe_name} == 32'hxx33_0000 && $counter0 == 'u7) then
            set_flag $flag0;
            goto STATE_B;
        elseif ( {counter_probe_name} == 32'hxx33_0000) then
            increment_counter $counter0;
            goto STATE_A;
        else
            goto STATE_A;
      endif
      
    state STATE_B:
        if ( {counter_probe_name} == 32'hxAAA_BBBB && $counter1 == 'u9) then
            set_flag $flag1;
            trigger;
        elseif ( {counter_probe_name} == 32'hxAAA_BBBB) then
            increment_counter $counter1;
            goto STATE_B;
        else
            goto STATE_B;
      endif
      
"""
)

my_ila.run_advanced_trigger(TSM_FLAGS_COUNTERS, window_size=8)

future = my_ila.monitor_status(max_wait_minutes=1.0, progress=status_progress, done=chipscopy.null_callback)

# future.result is blocking, until monitor_status() function has completed or timed-out or been cancelled.
# Meanwhile, the status_progress() function is called twice per second to print out status.
status = future.result
print(f"\nCounters: {status.tsm_counters}    Flags: {status.tsm_flags}")
# -

# ## Step 13 - Upload Captured Waveform

my_ila.upload()
if not my_ila.waveform:
    print("\nUpload failed!")

# ## Step 14 - Print samples for probe 'chipscopy_i/counters/slow_counter_0_Q_1'. 

print_probe_values(my_ila.waveform, [counter_probe_name])

## When done with testing, close the connection
delete_session(session)
