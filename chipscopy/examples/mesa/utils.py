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

"""Runtime helpers shared across the MESA package.

Public helpers:

- :func:`deep_merge`
- :func:`find_manifest_files`
- :func:`read_manifest_dict_with_inheritance`
- :func:`get_designs_directory`

The MESA management CLI (``validate``, ``lint``, ``new-example`` ...) is an
internal tool and lives in :mod:`chipscopy.examples.mesa._cli`.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from chipscopy import get_examples_dir_or_die


class ManifestError(Exception):
    """Raised when a manifest cannot be loaded, parsed or merged."""


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into ``base`` and return a new dict.

    Scalar values from ``override`` replace the corresponding ``base`` value.
    Dictionaries are merged recursively. Lists are concatenated and
    deduplicated while preserving order, so a child manifest can append
    entries (e.g. an extra ``quad_name``) but cannot remove an entry
    inherited from ``base`` through this helper alone. To fully replace an
    inherited list, override the entire containing dict in the child.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = list(dict.fromkeys(result[key] + value))
            else:
                result[key] = value
        else:
            result[key] = value
    return result


def get_designs_directory() -> Path:
    """Return the MESA designs directory.

    Single source of truth for ``examples/designs/`` lookup. Honours the
    ``CHIPSCOPY_EXAMPLES`` environment variable through
    :func:`chipscopy.get_examples_dir_or_die` so notebooks, the registry
    and CLI all agree on the same location.
    """
    designs_dir = Path(get_examples_dir_or_die()) / "designs"
    if not designs_dir.exists():
        raise FileNotFoundError(
            f"MESA designs directory not found: {designs_dir}\n"
            f"Hint: Run 'chipscopy-get-examples' to deliver examples."
        )
    return designs_dir


def find_manifest_files(designs_dir: Path) -> List[Path]:
    """Return every ``manifest.json`` under ``designs_dir`` sorted by path.

    Sorting makes downstream "first manifest for platform X" lookups
    deterministic across machines rather than dependent on filesystem
    traversal order.
    """
    return sorted(Path(designs_dir).glob("**/manifest.json"))


def read_manifest_dict_with_inheritance(manifest_path: Path) -> Dict[str, Any]:
    """Read a manifest JSON and recursively resolve any ``extends`` chain.

    The returned dict matches what the runtime will ultimately consume:
    base manifest first, then ``deep_merge`` of each override on top.

    Base manifests are resolved either relative to the manifest's own
    directory or, as a fallback, relative to the MESA designs directory.
    """
    manifest_path = Path(manifest_path)
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    extends = manifest_data.pop("extends", None)
    if extends is None:
        return manifest_data

    base_path = manifest_path.parent / extends
    if not base_path.exists():
        try:
            base_path = get_designs_directory() / extends
        except FileNotFoundError:
            pass

    if not base_path.exists():
        raise ManifestError(
            f"Base manifest not found: {extends}\n"
            f"   Searched: {base_path}\n"
            f"   Referenced from: {manifest_path}"
        )

    base_data = read_manifest_dict_with_inheritance(base_path)
    return deep_merge(base_data, manifest_data)
