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

from typing_extensions import Final

TYPE: Final[str] = "Type"
CHILDREN: Final[str] = "Children"
ALIAS_DICT: Final[str] = "Alias dict"
HANDLE_NAME: Final[str] = "Handle name"
PROPERTY_ENDPOINT: Final[str] = "Property endpoint"
MODIFIABLE_ALIASES: Final[str] = "Modifiable aliases"

COUNT_KEY: Final[str] = "Count"
PROPERTIES_KEY: Final[str] = "Properties"
NAME_PREFIX_KEY: Final[str] = "Name prefix"

# -------------------------------------------------------------------
# Serial object types
# -------------------------------------------------------------------
GT_KEY: Final[str] = "GT"
"""GT"""
TX_KEY: Final[str] = "TX"
"""TX"""
RX_KEY: Final[str] = "RX"
"""RX"""
PLL_KEY: Final[str] = "PLL"
"""PLL"""
IBERT_KEY: Final[str] = "IBERT"
"""IBERT"""
GT_GROUP_KEY: Final[str] = "GT_Group"
"""GT Group"""
MICROBLAZE_KEY: Final[str] = "MicroBlaze"
"""MicroBlaze"""
PLL_TYPE_KEY: Final[str] = "PLL_Type"
"""PLL"""

# ----------------------------------------------------------------
# Applicable to both RX and TX
# ----------------------------------------------------------------
PATTERN: Final[str] = "Pattern"
PLL_SOURCE: Final[str] = "PLL Source"
PLL_LOCK_STATUS: Final[str] = "PLL Lock Status"

# ----------------------------------------------------------------
# Applicable to TX only
# ----------------------------------------------------------------
TX_RESET: Final[str] = "Reset"

# ----------------------------------------------------------------
# Applicable to RX only
# ----------------------------------------------------------------
RX_BER: Final[str] = "BER"
RX_RESET: Final[str] = "Reset"
RX_STATUS: Final[str] = "Status"
RX_YK_SCAN: Final[str] = "YK scan"
RX_EYE_SCAN: Final[str] = "Eye scan"
RX_LOOPBACK: Final[str] = "Loopback"
RX_LINE_RATE: Final[str] = "Line Rate"
RX_SUPPORTED_SCANS: Final[str] = "Supported scans"
RX_RECEIVED_BIT_COUNT: Final[str] = "Received Bit Count"
RX_PATTERN_CHECKER_ERROR_COUNT: Final[str] = "Pattern Checker Error Count"

# ----------------------
# Microblaze
# ----------------------
MB_ELF_VERSION: Final[str] = "ELF Version"

# -----------------------------------
# Eye scan related
# -----------------------------------
EYE_SCAN_DONE: Final[str] = "Done"
"""Eye scan completed successfully"""
EYE_SCAN_ABORTED: Final[str] = "Aborted"
"""Eye scan was aborted by user or cs_server"""
EYE_SCAN_NOT_STARTED: Final[str] = "Not Started"
"""Eye scan object created, but scan not started in MB"""
EYE_SCAN_IN_PROGRESS: Final[str] = "In Progress"
"""Eye scan is in progress"""

EYE_SCAN_HORZ_STEP: Final[str] = "Horizontal Step"
"""Alias for horizontal step eye scan parameter"""
EYE_SCAN_VERT_STEP: Final[str] = "Vertical Step"
"""Alias for vertical step eye scan parameter"""
EYE_SCAN_HORZ_RANGE: Final[str] = "Horizontal Range"
"""Alias for horizontal range eye scan parameter"""
EYE_SCAN_VERT_RANGE: Final[str] = "Vertical Range"
"""Alias for horizontal range eye scan parameter"""
EYE_SCAN_TARGET_BER: Final[str] = "Target BER"
"""Alias for target BER eye scan parameter"""
EYE_SCAN_DWELL_TIME: Final[str] = "Dwell Time"
"""Alias for dwell time eye scan parameter"""

YK_SCAN_SNR_VALUE: Final[str] = "YK Scan SNR Value"
YK_SCAN_STOP_TIME: Final[str] = "YK Scan Stop Time"
YK_SCAN_START_TIME: Final[str] = "YK Scan Start Time"
YK_SCAN_SLICER_DATA: Final[str] = "YK Scan Slicer Data"

EYE_SCAN_UT: Final[str] = "UT"
EYE_SCAN_STATUS: Final[str] = "Status"
EYE_SCAN_2D_PLOT: Final[str] = "2D Plot"
EYE_SCAN_RAW_DATA: Final[str] = "Raw Scan Data"
EYE_SCAN_PROGRESS: Final[str] = "Scan Progress"
EYE_SCAN_PRESCALE: Final[str] = "Prescale"
EYE_SCAN_STOP_TIME: Final[str] = "Eye Scan Stop Time"
EYE_SCAN_START_TIME: Final[str] = "Eye Scan Start Time"
EYE_SCAN_ERROR_COUNT: Final[str] = "Error Count"
EYE_SCAN_SAMPLE_COUNT: Final[str] = "Sample Count"
EYE_SCAN_2D_PLOT_DATA: Final[str] = "Data"
EYE_SCAN_SCAN_PARAMETERS: Final[str] = "Scan Parameters"
EYE_SCAN_2D_PLOT_BER_FLOOR_VALUE: Final[str] = "BER Floor Value"
EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_READ: Final[str] = "Total #Data Points Read"
EYE_SCAN_TOTAL_NO_OF_DATA_POINTS_EXPECTED: Final[str] = "Total #Data Points Expected"

# ----------------------------------------------------------------
# PLL related
# ----------------------------------------------------------------
PLL_RESET: Final[str] = "Reset"
