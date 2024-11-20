..
   Copyright (C) 2021-2022, Xilinx, Inc.
   Copyright (C) 2022-2024, Advanced Micro Devices, Inc.
   
     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at
   
         http://www.apache.org/licenses/LICENSE-2.0
   
     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

Details
=======

Core Details
------------
Basic details of the PCIe link are available in the core properties.  These include
    * ``link_info`` - a string to indicate the width and speed of the link, like "Gen3x8"
    * ``first_quad`` - a string to indicate the first Versal GTY Quad used (lane 0 is always the first lane)
    * ``quad_incr`` - a boolean indicating that the index of the quad in increasing or decreasing if it is larger than 4 lanes

LTSSM State Visit Tracking
--------------------------
There are a group of properties that start with ``state.`` followed by the name of LTSSM state.  These properties track
which states have been visited. If a given property value is 1, that means the state has been visited at some point in
time.  If 2, then it's the most recent state visited.  If 0, then the state has never been visited.

LTSSM State Transition Tracking
-------------------------------
In addition to tracking which states have been visited, the API also tracks how many times each transition in the LTSSM
graph has been traversed.  This group of properties start with ``edge.``, and are followed by the two states involved,
separated by an underscore.  For instance, the number of times the LTSSM has gone from the "Detect" to the "Polling"
state will be in the ``edge.detect_polling`` property.  Keep in mind the graph is directed, so to check how many times
the state machine has gone in the reverse direction, you will need to access a different property : ``edge.polling_detect``.

LTSSM Trace
-----------
The entire trace, that is, the historical tracking of all LTSSM transitions, will be stored in the ``state.trace``
property.  This property is an array of strings.  Each entry in the array will either be a single state, a group of
sub-state transitions, or a loop.

For a single state, there will be only the state name with the hex encoding in parentheses::

    r.lock [(0x0b)]

Many of the states in the LTSSM have sub-states.  For instance, the "Detect" state has two substates- "Quiet" and
"Active".  The core is able to detect the traversal of those states as well, and will group them together
into a single ``state.trace`` entry.  So if the trace includes moving from the detect.quiet state to the detect.active
state, then back to the detect.quiet state, the entry in state.trace will be::

    detect [detect.quiet (0x00), detect.active (0x01), detect.quiet (0x00)]

Notice the raw state encoding is in parentheses, and the sub-state traversals are enclosed in square brackets separated
by commas.

Sometimes a group of states is visited again and again in a loop.  To ease visualization of these this, the API detects
and groups those loops together, marking the number of times the loop has occurred.  The formatting is similar to a
sub-state transition grouping::

    Loop (20) [r.lock (0x0b), r.cfg (0x0d), r.idle (0x0e), l0 (0x10)]

The API also checks for illegal state transitions, invalid state encodings, and PCIe resets (an unexpected transition to
the detect.quiet state).  All of these actions will cause an explanatory entry to be inserted into ``state.trace``.

