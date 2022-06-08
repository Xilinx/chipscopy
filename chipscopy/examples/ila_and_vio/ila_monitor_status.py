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
# # ChipScoPy ILA Monitor Status Example
#
#
# <img src="../img/api_overview.png" width="500" align="left">

# %% [markdown]
# ## Description
# An advanced example showing how to monitor the ILA capture status, by running the function ILA.monitor_status(), in asynchroneous mode.
#
# By calling ChipScoPy ILA API function **monitor_status()**, in asynchronous mode we can do the following:
# - Get periodic updates of ILA core capture status.
# - Call other ChipScoPy API functions, while monitoring the ILA status.
# - Cancel the status monitor early.
#
#
# ## Requirements
# - Local or remote Xilinx Versal board, such as a VCK190
# - Xilinx hw_server 2022.1 installed and running
# - Xilinx cs_server 2022.1 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2022.1 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`

# %% [markdown]
# # Overview
# ### Function monitor_status() Documentation
#     A. Function monitor_status()
#     B. Calling monitor_status() in Synchronous Mode
#     C. Calling monitor_status() in Asynchronous Mode
#     D. Future Object
#     E. Progress Function
#     F. ILAStatus Class
#     G. ILAState Enum Values
# ### Example Steps
#     1.  Initialization: Imports and File Paths
#     2.  Create a session and connect to the hw_server and cs_server
#     3.  Program the Device
#     4.  Discover Debug Cores
#     5.  VIO Control and ILA Capture
#     6.  Configure the counter using VIO output probes
#     7.  Define Status Progress Function
#     8.  Arm ILA to Trigger on VIO Up/Down virtual switch
#     9.  Start Status Monitor
#     10. Toggle Counter Direction - Monitor Status
#     11. Status Monitor Completes
#     12. Upload and Print Data
# --------------------

# %% [markdown]
# ## A. Function monitor_status()
#
#     def monitor_status(
#        self, max_wait_minutes: float = None, progress=None, done: request.DoneFutureCallback = None
#     ) -> ILAStatus or request.CsFutureRequestSync:
#
# This function monitors ILA capture status and waits until all data has been captured, or until timeout
# or the function is cancelled.
# Call this function after arming the ILA and before uploading the waveform.
# The command operates in synchronous mode if *done* argument has default value *None* .
#
#
# Args:
# -  **max_wait_minutes** (float): Max time in minutes for status monitor. If *None*, status monitor never times out.
# -  **progress**(progress_fn) : See Asynchronous Mode, below. This function runs in the TCF Event Thread.
# -  **done**(request.DoneFutureCallback): Done callback. This function runs in the TCF Event Thread.
#
# Returns:
# - ILAStatus when called synchronously.
# - "future object" when called asynchronously.

# %% [markdown]
# ## B. Calling monitor_status() in Synchronous Mode
# - Typical mode when using this function. It is not covered in this example.
# - Function waits until all data has been captured in the ILA core, or timeout.
# - Use default argument value *None* for both arguments *progress* and *done* .
# - Returns an ILAStatus object.

# %% [markdown]
# ## C. Calling monitor_status() in Asynchronous Mode
#
# - This mode is useful for reporting the capture status to stdout or a GUI.
# - Function does not block. The main thread continues with the next statement.
# - Returns a *future* object, which represents the monitor.
# - A blocking function should be called later on the *future* object, in order to let the calling thread wait until the status monitor has completed.
# - Asynchronous Mode is selected, by specifying a *done* function, which is called after the function has completed.
# - If no user defined callback is needed, set *done* argument to dummy function *chipscopy.null_callback*, to enable asynchronous mode.

# %% [markdown]
# ## D. Future Object
#
# When the *monitor_status* function is called in asynchronous mode, it will return a *future* object.
# The *future* object has blocking attributes and functions, which will block the current thread until
# the status monitor has completed.
#
# ###  Blocking Attributes
#
# - *future.result* - Returns *None* or *ILAStatus*. *ILAStatus* object if capture did complete successfully, without timeout.
# - *future.error* - Returns *None* or *Exception*. *None* if no error otherwise an exception object, e.g. timeout exception.
#
# ### Non-blocking Attribute
#
# - *future.progress* - Returns *None* or *ILAStatus*. Read this attribute in the *progress function*, to get the ILA capture status.
#
# ### Blocking Function
#
# - *future.wait(timeout=None)* - *None* value means wait until status monitor completes. Argument *timeout* is in seconds.
#
# ### Non-blocking Function
#
# - *future.cancel()*  - Cancels the status monitor. An exception will be raised in the thread, which called the function *ILA.monitor_status*.

# %% [markdown]
# ## E. Progress Function
#
# - User-defined function which takes one argument *future*.
# - Useful for reporting ILA capture status.
# - The *progress function* is only called when the ILA capture status changes.
# - The *progress function* is called in the TCF Event Thread. The *progress function* must not call any ChipScoPy API function, which interacts with the cs_server or the device.
#
# >    Example:
# >
# >        def monitor_status_done(future):
# >            if not future.error:
# >                # future.result holds an ILAStatus object.
# >                print_status(future.progress)

# %% [markdown]
# ## F. ILAStatus Class
#
# The following data attributes are available to read, when monitoring the ILA capture status.
#
# | Attributes                  | TYPE     | Description                                                 |
# |:--------------------------- |:-------- |:----------------------------------------------------------- |
# | capture_state:              | ILAState | Capture state. See below.                                   |
# | is_armed                    | bool     | Trigger is armed.                                           |
# | is_full                     | bool     | Data buffer is full.                                        |
# | samples_captured            | int      | Number of samples captured in current data window.          |
# | windows_captured            | int      | Number of fully captured data windows.                      |
# | samples_requested           | int      | Requested number of samples per window, when was ILA armed. |
# | windows_requested           | int      | Requested number of windows, when ILA was armed.            |
# | trigger_position_requested  | int      | Requested trigger position, when ILA was armed.             |

# %% [markdown]
# ## G.  ILAState Enum Values
#
# ILA Capture State Transitions:<br>
# >        IDLE -> PRE_TRIGGER -> TRIGGER -> POST_TRIGGER -> IDLE
#
# | Enum Value   | Description
# |:-------------|:-------------------------------- |
# | IDLE         | Not armed.                       |
# | PRE_TRIGGER  | Capturing pre-trigger samples.   |
# | TRIGGER      | Waiting for trigger.             |
# | POST_TRIGGER | Capturing post-trigger samples.  |
#

# %% [markdown]
# # Example Steps

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#
# After this step,
# - Required functions and classes are imported
# - URL paths are set correctly
# - File paths to example files are set correctly

# %%
import os
from time import sleep
import chipscopy
from chipscopy import get_design_files
from chipscopy import get_examples_dir_or_die, null_callback
from chipscopy import create_session, report_versions
from chipscopy.api.ila import export_waveform, get_waveform_data, ILAStatus, ILAState

# %%
# Specify locations of the running hw_server and cs_server below.
# To make things convenient, we default to values from the following environment variables.
# Modify these if needed.

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
# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
device.program(PROGRAMMING_FILE)


# %% [markdown]
# ## 4 - Discover Debug Cores
#
# Debug core discovery initializes the chipscope server debug cores. This brings debug cores in the chipscope server online.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - ILA and VIO core instances in the device are reported

# %%
device.discover_and_setup_cores(ltx_file=PROBES_FILE)
print(f"Debug cores setup and ready for use.")

# %%
# Print out the ILA core instance UUIDs and instance names
ila_cores = device.ila_cores
for index, ila_core in enumerate(ila_cores):
    print(f"{index} - {ila_core.core_info.uuid}   {ila_core.name}")

# %%
# Print out the VIO core instance UUIDs and instance names
vio_cores = device.vio_cores
for index, vio_core in enumerate(vio_cores):
    print(f"{index} - {vio_core.core_info.uuid}   {vio_core.name}")


# %% [markdown]
# ## 5 - VIO Control and ILA Capture
#
# ILA and VIO are two important building blocks for debugging applications in hardware.
# This example design shows how to control IP using a VIO core and capture results with ILA.
#
# In this design,
# - A VIO core controls the counter (reset, up/down, ce, load)
# - An ILA core captures the counter values
#

# %% [markdown]
# <img src="img/capture_data.png" width="400" align="left">

# %%
# Grab the two cores we are interested in for the demonstration
# As shown above, a counter is connected to the ILA core.
# The VIO core controls the counter.

ila = device.ila_cores.get(name="chipscopy_i/counters/ila_slow_counter_0")
vio = device.vio_cores.get(name="chipscopy_i/counters/vio_slow_counter_0")

print(f"Using ILA: {ila.core_info.uuid}  {ila.name}")
print(f"Using VIO: {vio.core_info.uuid}  {vio.name}")


# %% [markdown]
# ## 6 - Configure the counter using VIO output probes
#
# Set up the VIO core to enable counting up, from 0
#
# <img src="img/vio_control_counter.png" width="300" align="left">

# %%
vio.reset_vio()
vio.write_probes(
    {
        "chipscopy_i/counters/slow_counter_0_SCLR": 0,
        "chipscopy_i/counters/slow_counter_0_L": 0x00000000,
        "chipscopy_i/counters/slow_counter_0_LOAD": 0,
        "chipscopy_i/counters/slow_counter_0_UP": 1,
        "chipscopy_i/counters/slow_counter_0_CE": 1,
    }
)
print("Counter is now free-running and counting up")


# %% [markdown]
# ## 7 - Define Status Progress Function
# - The **status_progress** function will be given to the **ila.monitor_status()** function, as an argument.
# - The function is called when status changes, but not more often than twice per second.
# - The argument **future** has a member *progress* of type **ILAStatus**, which contains the status information.
# - The **status_progress** function,
#     - prints status to stdout
#     - cancels the **monitor_status()** function, if 3 waveform windows have been captured.
# - Note: The monitor function will run in the Event Tread, which handles commands sent to the cs_server.
# - Important: Do not call an API function which communicates with the cs_server or device, from inside the monitor function. It may put the program in a deadlock.

# %%
def status_progress(future):
    """Called in Event Thread"""
    st: ILAStatus = future.progress
    if st:
        print_status(st)
        if st.windows_captured >= 3:
            print("\nCancelling ILA Status Monitor")
            future.cancel()


def print_status(st: ILAStatus):
    current_window = min(st.windows_captured + 1, st.windows_requested)
    print(
        f"\nCapture State: {st.capture_state.name} - "
        f" Windows Captured: {st.windows_captured} of {st.windows_requested}.",
        end="",
    )
    if st.is_full:
        print(f" - Capture is complete.")
    else:
        print(f" - Samples in current window: " f"{st.samples_captured} of {st.samples_requested}.")


# %% [markdown]
# ## 8 - Arm ILA to Trigger on VIO Up/Down virtual switch
#
# - Set ILA to trigger when UP/DOWN counter signal edge rises or falls.
# - Set ILA core to capture on a transition of the UP/DOWN toggle switch
# - Once transition happens, trigger in the middle of the buffer.
# - Request 10 windows.

# %% [markdown]
# <img src="img/edge_trigger.png" width="550" align="left">

# %%
ila.reset_probes()
ila.set_probe_trigger_value("chipscopy_i/counters/slow_counter_0_UP_1", ["==", "B"])
ila.run_basic_trigger(window_count=10, window_size=8, trigger_position=4)

print("ILA is armed")


# %% [markdown]
# ## 9 - Start Status Monitor
# - Define a *done* function *monitor_status_done*, which will be called when status monitoring ends.
# - Start the Status Monitor.
# - Passing in the *status_progress* function, defined above.
# - Get the *future* object from the *monitor_status* function.

# %%
def monitor_status_done(future):
    print("\nCallback function monitor_status_done() called.")
    if not future.error:
        # future.result holds an ILAStatus object.
        print_status(future.result)


# Called asynchronously, with done callback function.
# This thread will continue executing while monitoring of the ILA Status will happen in the event thread.
future = ila.monitor_status(
    max_wait_minutes=0.5, progress=status_progress, done=monitor_status_done
)

# %% [markdown]
# ## 10 - Toggle Counter Direction - Monitor Status
# - Use VIO to toggle counter up/down switch 3 times: DOWN/UP/DOWN.
# - This will cause the running ILA to trigger 3 times, capturing 3 windows of data.
# - The *status_progress* function will call *future.cancel()*, after 3 windows.
# - Observe messages:
#     - *status_progress* prints capture status.
#     - *status_progress* prints out message when calling *future.cancel()*.
#     - *done* function *monitor_status_done* prints message when called.

# %%
for switch_value in [0, 1, 0]:
    print("\nChanging counter up/down direction.")
    vio.write_probes({"chipscopy_i/counters/slow_counter_0_UP": switch_value})
    # Sleep 2.0 seconds.
    sleep(2.0)

# %% [markdown]
# ## 11 - Status Monitor Completes
# - *future.result* will block until capture completes or is cancelled.
# - Status monitoring is cancelled.
# - *future.result* thows the cancel exception.

# %%
status = None
try:
    # future.result is blocking, until monitor_status() function has completed or timed-out or been cancelled.
    status = future.result
except Exception as ex:
    # Catch cancel exception here.
    print(f"\n****** Status Monitor raised exception: '{ex}' ******\n")

if status:
    print("Function monitor_status() has completed.")
else:
    ila.refresh_status()

print(f"Windows avaliable to upload: {ila.status.windows_captured}.")

# %% [markdown]
# ## 12 - Upload and Print Data
# - Print the captured ILA samples and mark the trigger position.
# - Note that counter changes direction after the trigger mark.

# %%
ila.upload()
samples = get_waveform_data(
    ila.waveform,
    ["chipscopy_i/counters/slow_counter_0_Q_1"],
    include_trigger=True,
    include_sample_info=True,
)
for trigger, sample_index, window_index, window_sample_index, value in zip(*samples.values()):
    trigger = "<-- Trigger" if trigger else ""
    print(
        f"Window:{window_index}  Window Sample:{window_sample_index}  {value:10}  0x{value:08X} {trigger}"
    )
