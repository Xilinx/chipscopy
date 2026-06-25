#!/usr/bin/env python3
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

"""ChipScoPy MESA management command-line tool (internal).

This module is private to the ``mesa`` package. ChipScoPy maintainers invoke
it as ``python -m chipscopy.examples.mesa._cli`` to ``validate``, ``test``,
``generate``, ``add-example``, ``lint``, ``new-example``, and ``report`` on
manifests and example notebooks. End users are not expected to call it.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from chipscopy import get_examples_dir_or_die

from ._template_engine import NotebookTemplateEngine
from .manifest_validator import ManifestValidationReporter, validate_manifest_file
from .mesa import Manifest
from .utils import ManifestError, find_manifest_files, get_designs_directory


_TEMPLATE_ENGINE = NotebookTemplateEngine()


def _examples_dir() -> Path:
    """Return the canonical chipscopy examples directory.

    Defers to :func:`chipscopy.get_examples_dir_or_die`, which honors the
    ``CHIPSCOPY_EXAMPLES`` environment variable and falls back to the
    in-repo / site-packages location used by every other ChipScoPy
    example. Centralizing here keeps the MESA CLI in lockstep with the
    rest of the package instead of computing its own offset.
    """
    return Path(get_examples_dir_or_die())


def list_all_platforms() -> Dict[str, List[str]]:
    """List all platforms and their available designs by scanning directory structure."""
    platforms: Dict[str, List[str]] = {}

    designs_dir = _examples_dir() / "designs"
    if not designs_dir.exists():
        return platforms

    for platform_dir in designs_dir.iterdir():
        if (
            not platform_dir.is_dir()
            or platform_dir.name.startswith(".")
            or platform_dir.name.startswith("_")
        ):
            continue

        designs: List[str] = []
        for design_path in platform_dir.glob("**/*/"):
            if (design_path / "manifest.json").exists():
                designs.append(str(design_path.relative_to(platform_dir)))

        if designs:
            platforms[platform_dir.name] = designs

    return platforms


def get_example_id_from_filepath(filepath: str) -> str:
    """Generate example ID from file name (without extension)."""
    return Path(filepath).stem


def get_example_category_from_filepath(filepath: str) -> str:
    """Infer example category from file path."""
    path = Path(filepath)
    if "examples" in path.parts:
        examples_index = path.parts.index("examples")
        if len(path.parts) > examples_index + 1:
            return path.parts[examples_index + 1]
    return "general"


def discover_example_files(examples_dir: Path) -> List[Path]:
    """Discover example notebooks under ``examples_dir``.

    Notebooks (``.ipynb``) are the single source of truth for ChipScoPy
    examples. The matching ``.py`` files are auto-generated at release
    time from the notebooks, so we do not enumerate them here. Files
    under Jupyter checkpoint directories are filtered out; nothing else
    needs to be excluded because the glob already ignores other file
    types.
    """
    return [
        nb
        for nb in examples_dir.glob("**/*.ipynb")
        if ".ipynb_checkpoints" not in nb.parts
    ]


def list_examples_by_category(examples_dir: Path) -> Dict[str, List[Dict[str, str]]]:
    """List all examples grouped by category using file discovery."""
    categories: Dict[str, List[Dict[str, str]]] = {}
    example_files = discover_example_files(examples_dir)

    examples_by_id: Dict[str, Dict[str, str]] = {}
    for file_path in example_files:
        category = get_example_category_from_filepath(str(file_path))
        example_id = get_example_id_from_filepath(str(file_path))
        examples_by_id[example_id] = {
            "id": example_id,
            "category": category,
            "file_path": str(file_path),
        }

    for example_info in examples_by_id.values():
        category = example_info["category"]
        categories.setdefault(category, []).append(
            {
                "id": example_info["id"],
                "description": f"Example for {category} functionality",
                "file_path": example_info["file_path"],
            }
        )

    return categories


def get_example_info(example_id: str, examples_dir: Path) -> Dict[str, Any]:
    """Get example information by ID using file discovery."""
    for file_path in discover_example_files(examples_dir):
        if get_example_id_from_filepath(str(file_path)) == example_id:
            category = get_example_category_from_filepath(str(file_path))
            return {
                "id": example_id,
                "category": category,
                "description": f"Example for {category} functionality",
                "file_path": str(file_path),
            }
    return {}


_KNOWN_PLATFORMS = ["vck190", "vpk120", "vmk180", "vhk158", "vcu128", "vek280", "vek385"]
_PLATFORM_PATTERN = re.compile(r"^[a-z0-9_]+$")


class ManifestGenerator:
    """Generates manifest files for design directories containing PDI and LTX files."""

    def __init__(self) -> None:
        self.generated_files: List[str] = []
        self.failed_generations: List[tuple] = []

    def generate_manifest(self, design_dir: str, output_path: Optional[str] = None) -> bool:
        try:
            design_path = Path(design_dir)
            if not design_path.exists():
                print(f"Design directory does not exist: {design_dir}")
                return False

            design_info = self._analyze_design_directory(design_path)
            if not design_info:
                print(f"Could not analyze design directory: {design_dir}")
                return False

            manifest_content = self._create_manifest_content(design_info)

            manifest_path = Path(output_path) if output_path else design_path / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest_content, f, indent=2)

            print(f"Generated manifest: {manifest_path}")
            self.generated_files.append(str(manifest_path))
            return True

        except Exception as e:
            print(f"Failed to generate manifest for {design_dir}: {str(e)}")
            self.failed_generations.append((design_dir, str(e)))
            return False

    def _analyze_design_directory(self, design_path: Path) -> Optional[Dict[str, Any]]:
        pdi_files = list(design_path.glob("*.pdi"))
        ltx_files = list(design_path.glob("*.ltx"))

        if not pdi_files:
            print(f"WARNING: No PDI files found in {design_path}")
            return None
        if not ltx_files:
            print(f"WARNING: No LTX files found in {design_path}")
            return None

        path_parts = design_path.parts
        design_name = design_path.name
        platform: Optional[str] = None

        for part in reversed(path_parts):
            if part in _KNOWN_PLATFORMS:
                platform = part
                break

        if not platform:
            for p in _KNOWN_PLATFORMS:
                if p in design_name.lower():
                    platform = p
                    break

        if not platform:
            for part in reversed(path_parts):
                if (
                    _PLATFORM_PATTERN.match(part)
                    and len(part) >= 3
                    and part not in ["production", "debug", "designs"]
                ):
                    platform = part
                    break

        if not platform:
            print(f"WARNING: Could not determine platform from path: {design_path}")

        design_type_keywords = {
            "ibert": "ibert",
            "ila": "ila_demo",
            "vio": "vio_demo",
            "memory": "memory_debug",
            "sysmon": "sysmon",
            "noc": "noc_perfmon",
        }
        design_type: Optional[str] = None
        for keyword, dtype in design_type_keywords.items():
            if keyword in design_name.lower():
                design_type = dtype
                break
        if not design_type:
            design_type = "general"

        debug_cores = self._analyze_ltx_file(ltx_files[0]) if ltx_files else {}

        return {
            "platform": platform or "unknown",
            "design_type": design_type,
            "design_name": design_name,
            "pdi_files": [f.name for f in pdi_files],
            "ltx_files": [f.name for f in ltx_files],
            "debug_cores": debug_cores,
            "path": str(design_path),
        }

    def _analyze_ltx_file(self, ltx_path: Path) -> Dict[str, Any]:
        debug_cores: Dict[str, Any] = {}

        try:
            ltx_name = ltx_path.stem.lower()

            if "ibert" in ltx_name:
                if "gty" in ltx_name:
                    debug_cores["ibert_gty"] = {
                        "enabled": True,
                        "description": "IBERT GTY core for high-speed serial link testing",
                    }
                elif "gtm" in ltx_name:
                    debug_cores["ibert_gtm"] = {
                        "enabled": True,
                        "description": "IBERT GTM core for high-speed serial link testing",
                    }
                else:
                    debug_cores["ibert_gty"] = {
                        "enabled": True,
                        "description": "IBERT core for high-speed serial link testing",
                    }

            if "ila" in ltx_name:
                debug_cores["ila"] = {
                    "enabled": True,
                    "description": "Integrated Logic Analyzer for signal capture and analysis",
                }

            if "vio" in ltx_name:
                debug_cores["vio"] = {
                    "enabled": True,
                    "description": "Virtual Input/Output for runtime signal control",
                }

            if "sysmon" in ltx_name or "system_monitor" in ltx_name:
                debug_cores["sysmon"] = {
                    "enabled": True,
                    "description": "System Monitor for temperature and voltage monitoring",
                }

            if "memory" in ltx_name or "ddr" in ltx_name:
                debug_cores["memory"] = {
                    "enabled": True,
                    "description": "Memory debugging and calibration core",
                }

            if "noc" in ltx_name or "perfmon" in ltx_name:
                debug_cores["noc_perfmon"] = {
                    "enabled": True,
                    "description": "Network on Chip performance monitoring",
                }

            if not debug_cores:
                debug_cores["general"] = {
                    "enabled": True,
                    "description": "General purpose debug core",
                }

        except Exception as e:
            print(f"WARNING: Could not analyze LTX file {ltx_path}: {str(e)}")
            debug_cores["general"] = {"enabled": True, "description": "General purpose debug core"}

        return debug_cores

    def _create_manifest_content(self, design_info: Dict[str, Any]) -> Dict[str, Any]:
        supported_examples = self._determine_supported_examples(design_info["debug_cores"])
        platform = design_info["platform"] or "unknown"

        design_path_str = design_info["path"]
        designs_marker = "/designs/"
        if designs_marker in design_path_str:
            design_path_str = design_path_str.split(designs_marker, 1)[1]
        else:
            design_path_str = f"{platform}/{design_info['design_name']}"

        return {
            "design_info": {
                "design_name": design_info["design_name"],
                "description": f"Auto-generated manifest for {design_info['design_name']} -- review and update",
                "hw_platform": platform,
                "programming_flow": "flat",
                "design_path": design_path_str,
                "family": "versal",
                "device": "xc_PLACEHOLDER",
                "board": platform.upper(),
            },
            "debug_cores": design_info["debug_cores"],
            "supported_examples": supported_examples,
            "metadata": {
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0.0",
                "maintainer": "auto-generated -- update with team name",
                "notes": f"Auto-generated from: {design_info['path']}. Review family, device, and supported_examples.",
            },
        }

    def _determine_supported_examples(self, debug_cores: Dict[str, Any]) -> List[str]:
        supported = ["program"]
        core_to_examples = {
            "ibert_gty": ["link_and_eye_scan"],
            "ibert_gtm": ["yk_scan_example", "link_and_eye_scan"],
            "ibert_gtyp": ["cpm_decoupling", "link_and_eye_scan"],
            "ibert_usp_gty": ["link_and_eye_scan"],
            "ila": ["ila_and_vio", "ila_advanced_trigger", "ila_monitor_status"],
            "vio": ["ila_and_vio", "vio"],
            "sysmon": ["sysmon_example", "sysmon_sync_example"],
            "memory": ["ddr_example", "memory_example"],
            "noc_perfmon": ["noc_perfmon", "noc_perfmon_basic"],
            "pcie": ["pcie_basic_monitoring"],
        }
        for core_name, core_info in debug_cores.items():
            if core_info.get("enabled", False) and core_name in core_to_examples:
                supported.extend(core_to_examples[core_name])
        return list(dict.fromkeys(supported))


def validate_all_manifests(designs_dir: Path) -> Dict[str, bool]:
    """Validate every ``manifest.json`` under ``designs_dir`` and return per-file results."""
    validator = ManifestValidationReporter()
    results: Dict[str, bool] = {}

    for manifest_path in find_manifest_files(designs_dir):
        manifest_str = str(manifest_path)
        print(f"\nValidating: {manifest_str}")
        is_valid = validator.validate_manifest(manifest_str)
        print(validator.get_validation_report())
        results[manifest_str] = is_valid

    return results


def _extract_compliance_text(file_path: str) -> str:
    """Return the concatenated code-cell text of a notebook."""
    path = Path(file_path)
    if path.suffix != ".ipynb":
        raise ValueError(
            f"Compliance checks only run on .ipynb notebooks, got: {file_path}"
        )
    with path.open("r", encoding="utf-8") as f:
        nb = json.load(f)
    chunks: List[str] = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", [])
        chunks.append("".join(src) if isinstance(src, list) else src)
    return "\n\n".join(chunks)


def check_example_compliance(file_path: str) -> bool:
    """Score a notebook against the canonical MESA pattern.

    Notebooks are the single source of truth for examples; the matching
    ``.py`` files are auto-generated from notebooks at release time and are
    therefore not checked here.

    Required:
      - imports ``resolve_example_design`` from the MESA package
      - calls ``resolve_example_design(...)``
      - declares an ``EXAMPLE_ID`` literal
      - declares an ``HW_PLATFORM`` value (literal or pulled from env)

    Recommended (warnings, not failures):
      - calls ``example_design.program_device(...)``
      - calls ``example_design.print_summary()``
      - uses the ``design_manifest`` alias for the resolved manifest
    """
    try:
        content = _extract_compliance_text(file_path)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    required = {
        "Imports resolve_example_design": (
            "from chipscopy.examples.mesa import" in content
            and "resolve_example_design" in content
        ),
        "Calls resolve_example_design(...)": "resolve_example_design(" in content,
        "Declares EXAMPLE_ID": bool(
            re.search(r"\bEXAMPLE_ID\s*=\s*[\"']", content)
            or re.search(r"\bEXAMPLE_ID(?:_\d+)?\s*=\s*", content)
        ),
        "Declares HW_PLATFORM": bool(
            re.search(r"\bHW_PLATFORM(?:_\d+)?\s*=\s*[\"']", content)
            or "HW_PLATFORM" in content
            and "os.getenv(" in content
        ),
    }
    recommended = {
        "Calls example_design.program_device(...)": "example_design" in content
        and ".program_device(" in content,
        "Calls example_design.print_summary()": "example_design" in content
        and ".print_summary(" in content,
        "Uses design_manifest alias": "design_manifest" in content,
    }

    print(f"\nTesting: {file_path}")
    all_required_passed = True
    for label, passed in required.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {label}")
        if not passed:
            all_required_passed = False
    for label, passed in recommended.items():
        status = "[ OK ]" if passed else "[hint]"
        print(f"  {status} {label}")

    return all_required_passed


def _split_cell_source(source: str) -> List[str]:
    lines = source.splitlines(keepends=True)
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1].rstrip("\n")
    return lines


def create_new_example(example_id: str, template: str, output_dir: Path) -> None:
    """Create a new MESA-powered example notebook from a canonical template.

    Notebooks are the single source of truth for examples; the matching
    ``.py`` files are auto-generated from the notebooks at release time.
    Generated notebooks use ``resolve_example_design`` for setup and
    ``example_design.program_device(device)`` for programming, so they
    work in both MESA mode and direct PDI/LTX mode without any changes.
    """
    available_templates = _TEMPLATE_ENGINE.available_body_templates()
    if not available_templates:
        print(
            "No MESA body templates were found. The templates directory "
            "(chipscopy/examples/mesa/templates/) is missing from this install."
        )
        return
    if template not in available_templates:
        print(f"Unknown template: {template}")
        print(f"   Available templates: {', '.join(available_templates)}")
        return

    example_title = example_id.replace("_", " ").title()

    output_file = output_dir / f"{example_id}.ipynb"
    if output_file.exists():
        print(f"File already exists: {output_file}")
        print("   Remove the existing file or choose a different example ID")
        return

    try:
        setup_source = _TEMPLATE_ENGINE.render_setup_cell(example_id)
        program_source = _TEMPLATE_ENGINE.render_program_cell()
        body_source = _TEMPLATE_ENGINE.render_body(template)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Cannot scaffold example: {exc}")
        return

    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": _split_cell_source(
                    f"# {example_title}\n"
                    "\n"
                    "ChipScoPy MESA example. The setup cell uses "
                    "`resolve_example_design` so the same notebook works in "
                    "MESA mode (manifest-driven) or direct mode "
                    "(user-supplied PDI/LTX).\n"
                ),
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _split_cell_source(setup_source),
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": _split_cell_source(
                    "## Program the device\n"
                    "\n"
                    "`example_design.program_device` handles flat and "
                    "segmented programming flows when MESA is used and "
                    "falls back to a plain `device.program(...)` in "
                    "direct mode.\n"
                ),
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _split_cell_source(program_source),
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": _split_cell_source(f"## {example_title}\n"),
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _split_cell_source(body_source),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"Created MESA-powered notebook example: {output_file}")
    print("\nNext steps:")
    print(f"   1. Open {output_file} in Jupyter to fill in the example body.")
    print(
        "   2. Add to MESA manifests with:\n"
        f"      python -m chipscopy.examples.mesa._cli "
        f"add-example --example-id {example_id}"
    )
    print(f"   3. Run with: HW_PLATFORM=vck190 jupyter notebook {output_file}")


def add_example_to_manifests(
    example_id: str, platform: Optional[str] = None, dry_run: bool = True
) -> None:
    """Add a new example to compatible MESA manifest files."""
    print(f"Adding example '{example_id}' to MESA manifests...")
    if platform:
        print(f"  Platform filter: {platform}")
    if dry_run:
        print("  Mode: DRY RUN (no changes will be made)")

    designs_dir = get_designs_directory()
    manifest_files = find_manifest_files(designs_dir)

    updated_count = 0
    compatible_manifests = []

    for manifest_path in manifest_files:
        try:
            manifest = Manifest.from_file(Path(manifest_path))
        except ManifestError as e:
            print(f"WARNING: Could not load manifest {manifest_path}: {e}")
            continue

        if platform and manifest.design_info.hw_platform != platform:
            continue

        if example_id in manifest.supported_examples:
            print(f"Already present in {manifest_path}")
            continue

        compatible_manifests.append((manifest_path, manifest))

    if not compatible_manifests:
        print(f"INFO: No compatible manifests found for example '{example_id}'")
        if platform:
            print(f"   (Platform filter: {platform})")
        return

    print(f"\nFound {len(compatible_manifests)} compatible manifests:")
    for manifest_path, manifest in compatible_manifests:
        platform_name = manifest.design_info.hw_platform
        design_name = manifest.design_info.design_name
        available_cores = list(manifest.debug_cores.keys())
        print(f"  - {manifest_path}")
        print(f"    Platform: {platform_name}, Design: {design_name}")
        print(f"    Available cores: {available_cores}")

    if dry_run:
        print(f"\nWould add '{example_id}' to {len(compatible_manifests)} manifest files")
        return

    print(f"\nAdding '{example_id}' to manifest files...")
    rolled_back = 0
    for manifest_path, manifest in compatible_manifests:
        try:
            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)
            original_text = json.dumps(manifest_data, indent=2, sort_keys=False)

            if "supported_examples" not in manifest_data:
                manifest_data["supported_examples"] = []

            if example_id in manifest_data["supported_examples"]:
                print(f"Already in {manifest_path}")
                continue

            manifest_data["supported_examples"].append(example_id)
            manifest_data["supported_examples"].sort()

            with open(manifest_path, "w") as f:
                json.dump(manifest_data, f, indent=2, sort_keys=False)

            is_valid, validation_errors = validate_manifest_file(str(manifest_path))
            if not is_valid:
                with open(manifest_path, "w") as f:
                    f.write(original_text)
                print(f"ERROR: {manifest_path} failed validation after edit; rolled back.")
                for err in validation_errors:
                    print(f"  - {err}")
                rolled_back += 1
                continue

            print(f"Updated {manifest_path}")
            updated_count += 1

        except Exception as e:
            print(f"ERROR: Error updating {manifest_path}: {str(e)}")
            continue

    print("\nSUMMARY:")
    print(f"  Updated: {updated_count}")
    if rolled_back:
        print(f"  Rolled back: {rolled_back}")
    if updated_count > 0:
        print(f"  Successfully added '{example_id}' to {updated_count} manifest files")


def lint_manifests_and_examples(examples_dir: Path, designs_dir: Path) -> None:
    """Lint MESA manifests and examples to detect mismatches and issues.

    Per-manifest schema and recommended-field warnings live in
    :class:`ManifestValidationReporter`. This function adds the cross-manifest
    checks that need a global view (orphan examples, duplicate IDs, missing
    referenced examples).
    """
    print("CHIPSCOPY MESA LINTER")
    print("Validating Manifest Example System for All-platforms\n")
    print("=" * 60)

    example_files = discover_example_files(examples_dir)
    example_ids = {get_example_id_from_filepath(str(f)) for f in example_files}
    print(f"\nDiscovered {len(example_ids)} unique examples in filesystem")

    manifest_files = find_manifest_files(designs_dir)
    manifests: List[tuple] = []
    for manifest_path in manifest_files:
        try:
            manifest = Manifest.from_file(Path(manifest_path))
        except ManifestError as e:
            print(f"WARNING: Could not load manifest {manifest_path}: {e}")
            continue
        manifests.append((str(manifest_path), manifest))

    print(f"Loaded {len(manifests)} design manifests\n")

    manifest_example_ids: set = set()
    for _, manifest in manifests:
        manifest_example_ids.update(manifest.supported_examples)

    errors: List[str] = []
    warnings: List[str] = []

    missing_examples = manifest_example_ids - example_ids
    for example_id in sorted(missing_examples):
        errors.append(
            f"Example '{example_id}' referenced in manifests but no corresponding file found"
        )
        errors.append(
            f"  Expected file: {examples_dir}/**/{example_id}.ipynb"
        )

    standalone_examples = {"jtag_example"}
    unreferenced_examples = example_ids - manifest_example_ids - standalone_examples
    for example_id in sorted(unreferenced_examples):
        warnings.append(
            f"Example '{example_id}' exists in filesystem but not referenced in any manifest"
        )
        warnings.append(
            f"  Tip: Add to manifests with: python -m chipscopy.examples.mesa._cli "
            f"add-example --example-id {example_id}"
        )

    example_id_dirs: Dict[str, List[Path]] = {}
    for file_path in example_files:
        example_id = get_example_id_from_filepath(str(file_path))
        example_id_dirs.setdefault(example_id, []).append(file_path.parent)

    for example_id, parents in example_id_dirs.items():
        unique_parents = set(parents)
        if len(unique_parents) > 1:
            warnings.append(
                f"Example '{example_id}' is defined in multiple directories: "
                + ", ".join(str(p) for p in sorted(unique_parents))
                + " (consider giving them distinct example IDs to avoid manifest "
                "ambiguity)"
            )

    reporter = ManifestValidationReporter()
    for manifest_path, _ in manifests:
        reporter.validate_manifest(manifest_path)
        for w in reporter.warnings:
            warnings.append(f"{manifest_path}: {w}")

    print("\n" + "=" * 60)
    if errors:
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")

    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  {warning}")

    if not errors and not warnings:
        print("NO ISSUES FOUND")
        print("\nAll manifests and examples are properly synchronized!")
    else:
        print("\n" + "=" * 60)
        print(f"Summary: {len(errors)} errors, {len(warnings)} warnings")
        if errors:
            print("\nFix errors before proceeding. Warnings are recommendations.")


def generate_compatibility_report(examples_dir: Path) -> None:
    """Generate a comprehensive MESA compatibility report."""
    print("CHIPSCOPY MESA COMPATIBILITY REPORT")
    print("Manifest Example System for All-platforms\n")
    print("=" * 60)

    platforms = list_all_platforms()

    print(f"\nPLATFORMS: {len(platforms)}")
    for platform, designs in platforms.items():
        print(f"  {platform}: {designs}")

    print("\nEXAMPLES BY CATEGORY:")
    categories = list_examples_by_category(examples_dir)
    for category, examples in categories.items():
        print(f"  {category.upper()}: {len(examples)} examples")
        for example in examples:
            print(f"    - {example['id']}: {example['description']}")

    print("\nPLATFORM-EXAMPLE COMPATIBILITY:")
    print("  (Platform-example mapping available through design manifests)")
    print(f"  Total discovered examples: {sum(len(examples) for examples in categories.values())}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ChipScoPy MESA Management Tool - Manifest Example System for All-platforms"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    validate_parser = subparsers.add_parser("validate", help="Validate MESA manifest files")
    validate_parser.add_argument("--manifest", type=str, help="Specific manifest file to validate")
    validate_parser.add_argument(
        "--all", action="store_true", help="Validate all MESA manifest files"
    )

    test_parser = subparsers.add_parser(
        "test", help="Test a MESA example notebook for compliance"
    )
    test_parser.add_argument(
        "--file", type=str, required=True, help="Example .ipynb notebook to test"
    )

    subparsers.add_parser("report", help="Generate MESA compatibility report")

    generate_parser = subparsers.add_parser("generate", help="Generate MESA manifest files")
    generate_parser.add_argument(
        "--design-dir",
        type=str,
        required=True,
        help="Path to design directory containing PDI and LTX files",
    )
    generate_parser.add_argument(
        "--output",
        type=str,
        help="Custom output path for manifest file (default: design_dir/manifest.json)",
    )

    add_example_parser = subparsers.add_parser("add-example", help="Add example to MESA manifests")
    add_example_parser.add_argument(
        "--example-id",
        type=str,
        required=True,
        help="Example ID to add (matches notebook file name without .ipynb extension)",
    )
    add_example_parser.add_argument(
        "--platform",
        type=str,
        help="Target platform (e.g., vck190, vpk120). If not specified, adds to all platforms",
    )
    add_example_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated without making changes"
    )

    subparsers.add_parser("lint", help="Lint MESA manifests and examples")

    new_example_parser = subparsers.add_parser(
        "new-example", help="Create new MESA-powered example"
    )
    new_example_parser.add_argument(
        "--example-id",
        type=str,
        required=True,
        help="Example ID (will be used as notebook filename without .ipynb extension)",
    )
    available_templates = _TEMPLATE_ENGINE.available_body_templates()
    new_example_parser.add_argument(
        "--template",
        type=str,
        choices=available_templates or None,
        default="basic" if "basic" in available_templates else (
            available_templates[0] if available_templates else None
        ),
        help="Body template to use (default: basic)",
    )
    new_example_parser.add_argument(
        "--output-dir", type=str, help="Output directory (default: current directory)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    examples_dir = _examples_dir()
    designs_dir = examples_dir / "designs"

    if args.command == "validate":
        if args.manifest:
            validator = ManifestValidationReporter()
            is_valid = validator.validate_manifest(args.manifest)
            print(validator.get_validation_report())
            sys.exit(0 if is_valid else 1)
        if args.all:
            results = validate_all_manifests(designs_dir)
            failed_count = sum(1 for valid in results.values() if not valid)
            print("\nVALIDATION SUMMARY:")
            print(f"  Total manifests: {len(results)}")
            print(f"  Valid: {len(results) - failed_count}")
            print(f"  Invalid: {failed_count}")
            sys.exit(0 if failed_count == 0 else 1)
        print("Please specify --manifest or --all")
        return

    if args.command == "test":
        is_compliant = check_example_compliance(args.file)
        sys.exit(0 if is_compliant else 1)

    if args.command == "report":
        generate_compatibility_report(examples_dir)
        return

    if args.command == "generate":
        generator = ManifestGenerator()
        success = generator.generate_manifest(args.design_dir, args.output)

        if not success:
            print(f"Failed to generate manifest for {args.design_dir}")
            sys.exit(1)

        print(f"\nSuccessfully generated manifest for {args.design_dir}")

        manifest_path = args.output or os.path.join(args.design_dir, "manifest.json")
        print("Validating generated manifest...")
        validator = ManifestValidationReporter()
        is_valid = validator.validate_manifest(manifest_path)
        print(validator.get_validation_report())

        if is_valid:
            print("Generated manifest is valid!")
        else:
            print("Generated manifest has validation issues (but was still created)")
        return

    if args.command == "add-example":
        add_example_to_manifests(
            example_id=args.example_id, platform=args.platform, dry_run=args.dry_run
        )
        return

    if args.command == "lint":
        lint_manifests_and_examples(examples_dir, designs_dir)
        return

    if args.command == "new-example":
        output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
        create_new_example(
            example_id=args.example_id,
            template=args.template,
            output_dir=output_dir,
        )
        return


if __name__ == "__main__":
    main()
