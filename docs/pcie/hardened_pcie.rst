..
   Copyright (C) 2024-2026, Advanced Micro Devices, Inc.

     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

Hardened Debug PCIe (CPM6)
==========================

The hardened debug PCIe core provides LTSSM state trace debug for the CPM6
hardened PCIe controllers built into Versal silicon. Unlike the soft AXIS-PCIE
debug core (which uses fabric-based BRAM), the hardened core reads trace data
from NoC-accessible external memory.

Discovery
---------
Hardened PCIe cores are discovered alongside other debug cores::

    device.discover_and_setup_cores(hardened_pcie_scan=True)
    pcie_cores = device.hardened_pcie_cores

The ``hardened_pcie_scan`` keyword controls whether these cores are scanned.
It is independent of ``pcie_scan`` which controls the soft AXIS-PCIE cores.

Properties
----------
After initialization, register and alias properties are available::

    props = pcie.get_property()
    print(props["LINK_SPEED"])      # Link speed from status register
    print(props["LTSSM_STATE"])     # Current LTSSM state
    print(props["LT_FEATURE_EN"])   # LTSSM feature enable

Register and alias properties are named in upper case: ``LINK_SPEED``,
``LINK_WIDTH``, ``LTSSM_STATE``, ``LTSSM_ACTIVE``, ``LT_FEATURE_EN``
and ``LT_WRAP_EN``. Properties the server computes rather than reads from a
register are named in lower case: ``link_info``, ``cpm_version``,
``trace_data`` and the ``state.`` / ``edge.`` families below.

Looking an alias up in lower case returns nothing, so prefer
``props.get(name)`` over ``props[name]`` if you need a default.

LTSSM State Visit Tracking
---------------------------
Properties starting with ``state.`` track which LTSSM states have been
visited. A value of 1 means visited, 2 means most recently visited, and
0 means never visited. Same convention as the soft PCIe core.

LTSSM State Transition Tracking
--------------------------------
Properties starting with ``edge.`` count state transitions. For example,
``edge.detect_polling`` counts how many times the LTSSM moved from
Detect to Polling.

LTSSM Trace
-----------
The ``state.trace`` property contains the full LTSSM trace with substate
grouping, trace gap markers (for FIFO overflow / NoC back pressure), and
loop compression::

    pcie.refresh()
    pcie.print_trace()

Raw Trace Data
--------------
The ``get_raw_trace()`` method returns decoded per-word data including
durations (always reported, unlike ``state.trace`` which suppresses
rollover-prone states)::

    for entry in pcie.get_raw_trace():
        print(f"{entry['prev_state']} -> {entry['curr_state']}"
              f"  duration={entry['duration_us']}us"
              f"  overflow={entry['overflow']}")

For the raw hex word list without any decoding, use ``get_trace_data()``::

    hex_words = pcie.get_trace_data()  # ["0x00012345", "0x0005c38e", ...]

Convenience Methods
-------------------
Quick link status and trace summary::

    status = pcie.get_link_status()
    # {"speed": "0x2", "width": "0x3", "ltssm_state": "0x11", "link_info": "Gen3x8"}

    if pcie.is_link_up():
        print("Link is trained")

    summary = pcie.get_trace_summary()
    # {"entry_count": 42, "unique_states": ["detect", "polling", ...],
    #  "loop_count": 3, "current_state": "0x11", "link_info": "Gen3x8"}

Trace Export
------------
Save trace data to a file for offline analysis::

    pcie.save_trace("trace.json", fmt="json")  # Full decoded trace + summary
    pcie.save_trace("trace.csv", fmt="csv")    # Tabular: raw, duration, states

Reset
-----
Reset the LTSSM trace capture to clear the trace buffer and restart::

    pcie.reset_core()

This disables LTSSM capture, zeros trace memory, re-enables capture,
and clears all cached state/edge/trace properties. After reset,
``lt_feature_en`` is restored to 1 and ``ltssm_active`` should become 1.

Visualization
-------------
Graph topology is data-driven from the server's LTSSM encoding file.
The graph automatically adapts to different encodings::

    # DOT format (for Graphviz)
    dot_string = pcie.get_dot()

    # matplotlib graph
    plt = pcie.get_plt()
    plt.show()

States are colored orange (current), green (visited), or gray (unvisited).
Edge labels show transition counts.

Partial Degradation
-------------------
If initialization detects an unsupported mode (e.g., ``gt_direct`` or
``hsdp``), the core remains usable for register property access but
LTSSM trace reading is disabled with an informative reason. Similarly,
if the LTSSM feature is not enabled (``lt_feature_en=0``), register
properties work but trace reading returns an informational message.
