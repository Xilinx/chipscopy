# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
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

"""ChipScoPy MESA (Manifest driven Example System for All-platforms).

MESA provides a manifest-driven framework for managing hardware
designs and examples across all supported platforms.

Notebook setup (preferred):

    from chipscopy.examples.mesa import resolve_example_design

    # MESA mode (uses manifests):
    example_design = resolve_example_design("vck190", "ddr_example")

    # Direct mode (user-supplied files, no manifest required):
    example_design = resolve_example_design(
        "vck190", "ddr_example",
        programming_file="/path/to/my.pdi",
        probes_file="/path/to/my.ltx",
    )

    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")
    example_design.program_device(device)
"""

from .manifest_validator import (
    ManifestValidationReporter,
    validate_manifest,
    validate_manifest_file,
)
from .mesa import (
    DebugCore,
    DesignInfo,
    ExampleDesign,
    Manifest,
    ManifestMetadata,
    ManifestRegistry,
    get_all_platforms,
    get_designs_directory,
    get_manifest,
    print_manifest_info,
    resolve_example_design,
)
from .utils import ManifestError

__all__ = [
    "DebugCore",
    "DesignInfo",
    "ExampleDesign",
    "Manifest",
    "ManifestError",
    "ManifestMetadata",
    "ManifestRegistry",
    "ManifestValidationReporter",
    "get_all_platforms",
    "get_designs_directory",
    "get_manifest",
    "print_manifest_info",
    "resolve_example_design",
    "validate_manifest",
    "validate_manifest_file",
]

__version__ = "1.0.0"
