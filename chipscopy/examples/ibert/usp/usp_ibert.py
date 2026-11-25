# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2025, Advanced Micro Devices, Inc.
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
# # UltraScale+ IBERT
#

# %% [markdown]
# ## Description
#
# This notebook drives UltraScale+ IBERT links from one example while MESA selects the board design, programming artifact, and expected GT group names.
#
# It covers GTH, GTY, In-System IBERT GTH/GTY, and GTM Dual. The scan engine is selected from discovered RX capabilities: RXs advertising `eye_scan_supported` use `create_eye_scans`; RXs advertising `yk_scan_supported` use `create_yk_scans`; RXs advertising neither keep link and BER reporting only.
#
# Use MESA mode for packaged designs. Set `PROGRAMMING_FILE` and `PROBES_FILE` to use your own design files.
#

# %% [markdown]
# ## 1 - Initialization: Imports and File Paths
#

# %%
import os
from threading import Event

from chipscopy import (
    create_session,
    report_versions,
    report_hierarchy,
    delete_session,
)
from chipscopy.examples.mesa import resolve_example_design
from chipscopy.api.ibert.aliases import (
    EYE_SCAN_HORZ_RANGE,
    EYE_SCAN_VERT_RANGE,
    EYE_SCAN_VERT_STEP,
    EYE_SCAN_HORZ_STEP,
    EYE_SCAN_TARGET_BER,
    PATTERN,
    PLL_LOCK_STATUS,
    PLL_SOURCE,
    RX_LOOPBACK,
)
from chipscopy.api.ibert import create_eye_scans, create_links, create_yk_scans


# %%
# ============================================================
# USER CONFIGURATION - Edit these for your own setup / design
# ============================================================
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
HW_PLATFORM = os.getenv("HW_PLATFORM", "vcu128")
EXAMPLE_ID = "usp_ibert"
PROG_DEVICE = True

# Direct mode: set these to use your own design files (skips MESA).
PROGRAMMING_FILE = ""
PROBES_FILE = ""

# ============================================================

# --- MESA setup (no edits needed below) ---
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


# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
#

# %%
session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)


# %% [markdown]
# ## 3 - Program the device with the example design
#

# %%
device = session.devices.filter_by(family=DEVICE_FAMILY).get()

if PROG_DEVICE:
    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)


# %% [markdown]
# ## 4 - Discover IBERT cores and GT groups
#
# Debug core discovery initializes the ChipScoPy IBERT objects. ZCU102 exposes the chipscope hub through a BSCAN-downstream `uplus` alias; SCU200 (JTAG and DPC records now merge into one `spartanu` device) and other platforms use the manifest family.

# %%
DEBUG_FAMILY = "uplus" if HW_PLATFORM.lower() in {"zcu102"} else DEVICE_FAMILY
device = session.devices.filter_by(family=DEBUG_FAMILY).get()

device.discover_and_setup_cores(ibert_scan=True)
print("--> Debug core discovery complete")

if len(device.ibert_cores) == 0:
    raise RuntimeError("No IBERT core found on the selected device.")

for ibert_core in device.ibert_cores:
    gt_group_names = [gt_group.name for gt_group in ibert_core.gt_groups]
    print(f"\n-> {ibert_core} ({ibert_core.handle})")
    print(f"GT groups: {gt_group_names}")


# %% [markdown]
# ## 5 - Optional hierarchy and GT child inspection
#
# Run this cell when you need to confirm whether the discovered topology is Quad-like or Dual-like. The later link creation code only depends on each selected group exposing `gts`, so it works for either topology.
#

# %%
for ibert_core in device.ibert_cores:
    report_hierarchy(ibert_core)
    for gt_group in ibert_core.gt_groups:
        print(f"\nGT group {gt_group.name} children:")
        for child in gt_group.children:
            print(f"name = {child.name}")
            print(f"type = {child.type}")
            print(f"setup_done = {child.setup_done}")
            print(f"children = {child.children}")


# %% [markdown]
# ## 6 - Select the IBERT core and GT group
#
# MESA mode selects the first manifest-declared group with scan support. Direct mode selects the first discovered IBERT core and GT group.
#

# %%
def _has_scan_feature(core_config):
    return bool({"eye_scan", "yk_scan"}.intersection(core_config.features or []))


def _gt_group_names(ibert_core):
    return [gt_group.name for gt_group in ibert_core.gt_groups]


if design_manifest is not None:
    scannable_configs = [
        core_config
        for _, core_config in design_manifest.get_all_ibert_cores()
        if _has_scan_feature(core_config)
    ]
    if not scannable_configs:
        raise RuntimeError("The selected design does not declare an IBERT scan capability.")

    expected_group_names = [
        name
        for core_config in scannable_configs
        for name in (core_config.quad_names or [])
    ]
    ibert = next(
        (
            device.ibert_cores.at(index=index)
            for index in range(len(device.ibert_cores))
            if any(
                name in _gt_group_names(device.ibert_cores.at(index=index))
                for name in expected_group_names
            )
        ),
        None,
    )
    if ibert is None:
        discovered = [
            _gt_group_names(device.ibert_cores.at(index=index))
            for index in range(len(device.ibert_cores))
        ]
        raise RuntimeError(
            f"No hardware IBERT core matches manifest groups {expected_group_names}. "
            f"Discovered groups by core: {discovered}."
        )
    selected_group_name = next(
        name for name in expected_group_names if name in _gt_group_names(ibert)
    )
else:
    ibert = next(
        (
            device.ibert_cores.at(index=index)
            for index in range(len(device.ibert_cores))
            if len(device.ibert_cores.at(index=index).gt_groups) > 0
        ),
        None,
    )
    if ibert is None:
        raise RuntimeError("No discovered IBERT core exposes a GT group.")
    selected_group_name = ibert.gt_groups.at(index=0).name

selected_gt_groups = [ibert.gt_groups.filter_by(name=selected_group_name)[0]]

print(f"Matched hardware IBERT core: {ibert} ({ibert.handle})")
print(f"Hardware groups on matched core: {_gt_group_names(ibert)}")
print(f"Selected GT group: {selected_group_name}")


# %% [markdown]
# ## 7 - Create links for every GT in each selected group
#
# The same loop handles Quad and Dual topologies because it asks each selected group for its discovered GT list.
#

# %%
links = []
for gt_group in selected_gt_groups:
    group_links = create_links(
        txs=[gt.tx for gt in gt_group.gts],
        rxs=[gt.rx for gt in gt_group.gts],
    )
    links.extend(group_links)
    print(f"Created {len(group_links)} links on {gt_group.name}")

if not links:
    raise RuntimeError("No links were created for the selected GT groups.")
print(f"Total links created: {len(links)}")


# %% [markdown]
# ## 8 - Configure patterns and loopback from legal values
#
# The notebook reports the live enum values and chooses compatible values dynamically. It prefers PRBS31-like patterns and near-end loopback when those values exist, but it does not assume exact strings such as `PRBS 31` or `Near-End PMA`.
#

# %%
PROPERTY_VALID_VALUES_KEY = "Valid values"
PATTERN_PREFERENCE_GROUPS = (("prbs", "31"), ("prbs",))
LOOPBACK_PREFERENCE_GROUPS = (("near", "pma"), ("near", "pcs"), ("near",))


def _property_name_for_alias(endpoint, alias):
    property_name = endpoint.property_for_alias.get(alias)
    if property_name is None:
        raise RuntimeError(f"{endpoint} does not expose required property alias {alias!r}.")
    return property_name


def _property_valid_values(endpoint, alias):
    property_name = _property_name_for_alias(endpoint, alias)
    _, report = endpoint.property.report(property_name).popitem()
    raw_values = report.get(PROPERTY_VALID_VALUES_KEY, [])
    if isinstance(raw_values, (list, tuple)):
        values = list(raw_values)
    elif raw_values:
        values = [raw_values]
    else:
        values = []
    if not values:
        raise RuntimeError(f"No legal values reported for {endpoint}.{property_name}")
    return property_name, values


def _choose_preferred_value(values, preference_groups):
    for tokens in preference_groups:
        for value in values:
            value_text = str(value).lower()
            if all(token in value_text for token in tokens):
                return value
    return values[0]


def _choose_common_pattern_value(tx_values, rx_values):
    common_values = [value for value in tx_values if value in rx_values]
    if not common_values:
        raise RuntimeError(
            "No common TX/RX pattern value was reported. "
            f"TX values={tx_values}, RX values={rx_values}"
        )
    return _choose_preferred_value(common_values, PATTERN_PREFERENCE_GROUPS)


def _choose_loopback_value(values):
    preferred_value = _choose_preferred_value(values, LOOPBACK_PREFERENCE_GROUPS)
    if str(preferred_value).lower() != "none":
        return preferred_value
    for value in values:
        if str(value).lower() != "none":
            return value
    return preferred_value


def _pll_lock_reportable(gt_group):
    return all(PLL_SOURCE in gt.property_for_alias for gt in gt_group.gts) and all(
        PLL_LOCK_STATUS in pll.property_for_alias for pll in gt_group.plls
    )


report_pll_lock = all(_pll_lock_reportable(gt_group) for gt_group in selected_gt_groups)
if not report_pll_lock:
    print("This IBERT core does not publish PLL source and lock status; skipping PLL lock reporting.")

for link in links:
    print(f"\n----- {link.name} -----")
    tx_pattern_property, tx_pattern_values = _property_valid_values(link.tx, PATTERN)
    rx_pattern_property, rx_pattern_values = _property_valid_values(link.rx, PATTERN)
    rx_loopback_property, rx_loopback_values = _property_valid_values(link.rx, RX_LOOPBACK)

    pattern_value = _choose_common_pattern_value(tx_pattern_values, rx_pattern_values)
    loopback_value = _choose_loopback_value(rx_loopback_values)

    print(f"--> Valid TX pattern values: {tx_pattern_values}")
    print(f"--> Valid RX pattern values: {rx_pattern_values}")
    print(f"--> Valid RX loopback values: {rx_loopback_values}")

    props = {tx_pattern_property: pattern_value}
    link.tx.property.set(**props)
    link.tx.property.commit(list(props.keys()))

    props = {
        rx_pattern_property: pattern_value,
        rx_loopback_property: loopback_value,
    }
    link.rx.property.set(**props)
    link.rx.property.commit(list(props.keys()))

    print(f"--> Set TX/RX pattern to {pattern_value!r} and RX loopback to {loopback_value!r}")
    if report_pll_lock:
        print(f"PLL locked: RX={link.rx.pll.locked}, TX={link.tx.pll.locked}")
    print(f"Link status: {link.status}")
    link.generate_report()


# %% [markdown]
# ## 9 - Discover scan capabilities
#
# This cell selects the scan engine from each discovered RX object. Links without scan support are left available for link status and BER reporting.
#

# %%
eye_scan_links = []
yk_scan_rxs = []
links_without_scan = []

for link in links:
    if link.rx.eye_scan_supported:
        eye_scan_links.append(link)
        scan_mode = "eye_scan"
    elif link.rx.yk_scan_supported:
        yk_scan_rxs.append(link.rx)
        scan_mode = "yk_scan"
    else:
        links_without_scan.append(link)
        scan_mode = "link_only"
    print(f"{link.name}: RX {link.rx.name} scan mode -> {scan_mode}")

if links_without_scan:
    print(f"Scan acquisition unavailable for {[link.name for link in links_without_scan]}.")
    print("Link status and BER reporting remain available through the link reports above.")
if not eye_scan_links and not yk_scan_rxs:
    print("No selected RX advertises eye_scan_supported or yk_scan_supported.")


# %% [markdown]
# ## 10 - Eye scan acquisition
#
# Eye scans use the traditional 2D eye-scan data model and `EyeScan` reports/plots.
#

# %%
eye_scans = []

if eye_scan_links:
    EYE_SCAN_HORZ_STEP_VALUE = 8
    EYE_SCAN_VERT_STEP_VALUE = 8

    eye_scans = create_eye_scans(target_objs=eye_scan_links)
    for eye_scan in eye_scans:
        eye_scan.params[EYE_SCAN_HORZ_STEP].value = EYE_SCAN_HORZ_STEP_VALUE
        eye_scan.params[EYE_SCAN_VERT_STEP].value = EYE_SCAN_VERT_STEP_VALUE
        eye_scan.params[EYE_SCAN_HORZ_RANGE].value = "-0.500 UI to 0.500 UI"
        eye_scan.params[EYE_SCAN_VERT_RANGE].value = "100%"
        eye_scan.params[EYE_SCAN_TARGET_BER].value = 1e-5
        eye_scan.start()
        print(f"Started eye scan {eye_scan}")
else:
    print("No eye-scan-capable RXs selected; skipping eye scan acquisition.")


# %%
if eye_scans:
    for eye_scan in eye_scans:
        eye_scan.wait_till_done()
        print(f"Eye scan complete: {eye_scan}")
else:
    print("No eye scans to wait for.")


# %% [markdown]
# ## 11 - Eye scan result presentation
#
# This section is intentionally separate from YK scan presentation because the result objects and metrics differ.
#

# %%
if eye_scans:
    for eye_scan in eye_scans:
        eye_scan.generate_report()
        eye_scan.plot.show()
        print(f"{eye_scan.name} Open Area: {eye_scan.metric_data.open_area}")
else:
    print("No eye scan results to display.")


# %% [markdown]
# ## 12 - YK scan acquisition
#
# YK scans stream samples through update callbacks and stop asynchronously. The notebook waits for at least one data-update event, requests stop, and then waits for the stop callback before the session can be disconnected.
#

# %%
YK_UPDATE_TIMEOUT_SECONDS = 30
YK_STOP_TIMEOUT_SECONDS = 15

yk_scans = []
yk_update_events = {}
yk_stop_events = {}
yk_stop_errors = {}
yk_update_timeouts = []


def _make_yk_update_callback(scan_name):
    def yk_scan_update(scan):
        if scan.scan_data:
            latest = scan.scan_data[-1]
            print(
                f"YK update {scan.name}: samples={len(scan.scan_data)}, "
                f"slicer_points={len(latest.slicer)}, snr={latest.snr}"
            )
            yk_update_events[scan_name].set()

    return yk_scan_update


def _make_yk_stop_callback(scan_name):
    def yk_scan_stop(scan, error):
        if error:
            yk_stop_errors[scan_name] = error
        print(f"YK scan {scan.name} stopped")
        yk_stop_events[scan_name].set()

    return yk_scan_stop


if yk_scan_rxs:
    yk_scans = create_yk_scans(target_objs=yk_scan_rxs)
    for yk_scan in yk_scans:
        yk_update_events[yk_scan.name] = Event()
        yk_stop_events[yk_scan.name] = Event()
        yk_stop_errors[yk_scan.name] = None
        yk_scan.updates_callback = _make_yk_update_callback(yk_scan.name)
        yk_scan.stop_callback = _make_yk_stop_callback(yk_scan.name)
        yk_scan.start()
        print(f"Started YK scan {yk_scan.name} on {yk_scan.rx.name}")

    for yk_scan in yk_scans:
        updated = yk_update_events[yk_scan.name].wait(timeout=YK_UPDATE_TIMEOUT_SECONDS)
        if not updated:
            yk_update_timeouts.append(yk_scan.name)
            print(
                f"WARNING: No YK data update for {yk_scan.name} within "
                f"{YK_UPDATE_TIMEOUT_SECONDS} seconds; stopping before failing safely."
            )

    for yk_scan in yk_scans:
        yk_scan.stop()

    for yk_scan in yk_scans:
        stopped = yk_stop_events[yk_scan.name].wait(timeout=YK_STOP_TIMEOUT_SECONDS)
        if not stopped:
            raise RuntimeError(
                f"Timed out waiting for asynchronous stop callback from {yk_scan.name}."
            )
        if yk_stop_errors[yk_scan.name]:
            raise RuntimeError(f"YK scan {yk_scan.name} stopped with error: {yk_stop_errors[yk_scan.name]}")

    if yk_update_timeouts:
        raise RuntimeError(f"No YK data update received before stop for: {yk_update_timeouts}")
else:
    print("No YK-capable RXs selected; skipping YK scan acquisition.")


# %% [markdown]
# ## 13 - YK scan result presentation
#
# YK data is reported as streamed slicer/SNR samples, not as an `EyeScan` open-area metric.
#

# %%
if yk_scans:
    for yk_scan in yk_scans:
        print(f"\n{yk_scan.name} on {yk_scan.rx.name}")
        print(f"  Samples: {len(yk_scan.scan_data)}")
        print(f"  Start time: {yk_scan.start_time}")
        print(f"  Stop time: {yk_scan.stop_time}")
        print(f"  MB ELF version: {yk_scan.elf_version}")
        if yk_scan.scan_data:
            latest = yk_scan.scan_data[-1]
            print(f"  Latest SNR: {latest.snr}")
            print(f"  Latest slicer points: {len(latest.slicer)}")
else:
    print("No YK scan results to display.")


# %% [markdown]
# ## 14 - Disconnect
#
# Run this only after eye scans have completed and YK scans have received their asynchronous stop callbacks.
#

# %%
delete_session(session)

