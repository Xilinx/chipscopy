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

"""Python manifest validation for ChipScoPy MESA.

Provides JSON schema-like validation for manifest files using only the
Python standard library.

Validation Approach for Inherited Manifests:
1. Load base manifest (recursively if base also has inheritance)
2. Merge base + overrides using ``deep_merge`` (same as runtime)
3. Validate the fully merged result against the complete schema

This ensures that invalid or misspelled values in override manifests are
detected during validation, not at runtime.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .utils import ManifestError, read_manifest_dict_with_inheritance


class ValidationError(Exception):
    """Validation error exception."""


class ManifestValidator:
    """Validates ChipScoPy manifest files using native Python."""

    # Tied to ChipScoPy API: session.devices.filter_by(family=...).
    # Must match manifest_schema.json `family` enum.
    VALID_FAMILIES = [
        "versal",
        "artixuplus",
        "kintexu",
        "kintexuplus",
        "spartanu",
        "virtexu",
        "virtexuplus",
        "zynquplus",
    ]
    # Code logic in mesa.py program_device dispatch depends on these exact values.
    VALID_FLOWS = ["flat", "segmented"]
    VALID_MEMORY_TYPES = ["DDR3", "DDR4", "DDR5", "LPDDR4", "LPDDR5", "HBM"]

    PATTERN_SNAKE_CASE = re.compile(r"^[a-z0-9_]+$")
    PATTERN_PLATFORM = re.compile(r"^[a-z0-9_]+$")
    PATTERN_DEVICE = re.compile(r"^xc[a-z0-9]+$")
    PATTERN_DATE = re.compile(r"^[0-9]{2,4}[-/][0-9]{1,2}[-/][0-9]{1,4}$")
    PATTERN_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
    PATTERN_HEX = re.compile(r"^0x[0-9A-Fa-f]+$")

    def __init__(self, schema: Optional[Dict] = None):
        self.schema = schema or self._get_default_schema()
        self.errors: List[str] = []

    @staticmethod
    def _get_default_schema() -> Dict:
        """Get the default ChipScoPy manifest schema.

        ``additional_properties: False`` mirrors the JSON schema's
        ``additionalProperties: false``; together they reject typo'd or
        unknown field names so silent drift between schema and runtime
        consumers cannot creep in.
        """
        debug_core_properties = {
            "enabled": {"type": "boolean"},
            "description": {"type": "string"},
            "features": {"type": "array", "items": {"type": "string"}},
            "quad_names": {"type": "array", "items": {"type": "string"}},
            "memory_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ManifestValidator.VALID_MEMORY_TYPES,
                },
            },
            "core_instances": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name"],
                    "additional_properties": False,
                    "properties": {
                        "name": {"type": "string", "min_length": 1},
                        "probe_prefix": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
            "node_names": {"type": "array", "items": {"type": "string"}},
            "trigger_base_address": {"type": "string", "pattern": "hex"},
            "probe_mapping": {"type": "object"},
            "vio_hierarchy": {"type": "string"},
        }

        return {
            "type": "object",
            "required": ["design_info", "debug_cores", "supported_examples", "metadata"],
            "additional_properties": False,
            "properties": {
                "extends": {
                    "type": "string",
                    "description": "Path to base manifest for inheritance",
                },
                "design_info": {
                    "type": "object",
                    "required": [
                        "design_name",
                        "hw_platform",
                        "programming_flow",
                        "design_path",
                        "family",
                        "device",
                    ],
                    "additional_properties": False,
                    "properties": {
                        "design_name": {"type": "string", "pattern": "snake_case", "min_length": 1},
                        "description": {"type": "string"},
                        "hw_platform": {
                            "type": "string",
                            "pattern": "platform",
                            "min_length": 3,
                        },
                        "programming_flow": {
                            "type": "string",
                            "enum": ManifestValidator.VALID_FLOWS,
                        },
                        "design_path": {"type": "string", "min_length": 1},
                        "family": {"type": "string", "enum": ManifestValidator.VALID_FAMILIES},
                        "device": {"type": "string", "pattern": "device"},
                        "board": {"type": "string"},
                        "boot_pdi_pattern": {"type": "string", "min_length": 1},
                        "pld_pdi_pattern": {"type": "string", "min_length": 1},
                        "idcode": {"type": "string", "pattern": "hex"},
                        "idcode_list": {
                            "type": "array",
                            "min_items": 1,
                            "items": {"type": "string", "pattern": "hex"},
                        },
                    },
                },
                "debug_cores": {
                    "type": "object",
                    "additional_properties_schema": {
                        "type": "object",
                        "required": ["enabled", "description"],
                        "additional_properties": False,
                        "properties": debug_core_properties,
                    },
                },
                "supported_examples": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "snake_case"},
                    "unique_items": True,
                },
                "metadata": {
                    "type": "object",
                    "required": ["created_date", "version"],
                    "properties": {
                        "created_date": {"type": "string", "pattern": "date"},
                        "version": {"type": "string", "pattern": "version"},
                        "maintainer": {"type": "string"},
                        "last_updated": {"type": "string", "pattern": "date"},
                        "notes": {"type": "string"},
                    },
                },
            },
        }

    def validate(self, data: Any, schema: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """Validate ``data`` against ``schema`` (default: full manifest schema)."""
        self.errors = []
        schema = schema or self.schema
        self._validate_value(data, schema, path="root")
        return len(self.errors) == 0, self.errors

    def _validate_value(self, value: Any, schema: Dict, path: str) -> None:
        expected_type = schema.get("type")
        if expected_type and not self._check_type(value, expected_type):
            self.errors.append(
                f"{path}: Expected type '{expected_type}', got '{type(value).__name__}'"
            )
            return

        if expected_type == "object":
            self._validate_object(value, schema, path)
        elif expected_type == "array":
            self._validate_array(value, schema, path)
        elif expected_type == "string":
            self._validate_string(value, schema, path)
        elif expected_type == "integer":
            self._validate_integer(value, schema, path)

    def _check_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "object": dict,
            "array": list,
            "string": str,
            "integer": int,
            "boolean": bool,
            "number": (int, float),
        }
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True
        return isinstance(value, expected_python_type)

    def _validate_object(self, obj: Dict, schema: Dict, path: str) -> None:
        if not isinstance(obj, dict):
            return

        required = schema.get("required", [])
        for field in required:
            if field not in obj:
                self.errors.append(f"{path}: Missing required field '{field}'")

        properties = schema.get("properties", {})
        for key, value in obj.items():
            if key in properties:
                self._validate_value(value, properties[key], f"{path}.{key}")

        if schema.get("additional_properties") is False and properties:
            for key in obj:
                if key not in properties:
                    self.errors.append(
                        f"{path}: Unknown field '{key}' (not allowed by schema)"
                    )

        # When ``debug_cores`` is reached we validate every entry against
        # the same nested schema (matching JSON schema's ``additionalProperties``
        # being a sub-schema). This catches typos in per-core fields like
        # ``quad_namez`` that would otherwise slip through.
        entry_schema = schema.get("additional_properties_schema")
        if entry_schema:
            for key, value in obj.items():
                self._validate_value(value, entry_schema, f"{path}.{key}")

    def _validate_array(self, arr: List, schema: Dict, path: str) -> None:
        if not isinstance(arr, list):
            return

        if schema.get("unique_items") and len(arr) != len(set(arr)):
            self.errors.append(f"{path}: Array items must be unique")

        min_items = schema.get("min_items")
        if min_items is not None and len(arr) < min_items:
            self.errors.append(
                f"{path}: Array length {len(arr)} is less than minimum {min_items}"
            )

        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(arr):
                self._validate_value(item, items_schema, f"{path}[{i}]")

    def _validate_string(self, s: str, schema: Dict, path: str) -> None:
        if not isinstance(s, str):
            return

        min_length = schema.get("min_length")
        if min_length is not None and len(s) < min_length:
            self.errors.append(f"{path}: String length {len(s)} is less than minimum {min_length}")

        enum_values = schema.get("enum")
        if enum_values and s not in enum_values:
            self.errors.append(f"{path}: Value '{s}' not in allowed values {enum_values}")

        pattern = schema.get("pattern")
        if pattern:
            self._validate_pattern(s, pattern, path)

    def _validate_pattern(self, s: str, pattern: str, path: str) -> None:
        pattern_messages = {
            "snake_case": (self.PATTERN_SNAKE_CASE, "does not match snake_case pattern"),
            "platform": (
                self.PATTERN_PLATFORM,
                "must contain only lowercase letters, numbers, and underscores",
            ),
            "device": (
                self.PATTERN_DEVICE,
                "must start with 'xc' and contain only lowercase letters and numbers",
            ),
            "date": (
                self.PATTERN_DATE,
                "does not match expected format (YYYY-MM-DD or MM-DD-YYYY)",
            ),
            "version": (
                self.PATTERN_VERSION,
                "does not match semantic versioning (e.g., '1.0.0')",
            ),
            "hex": (
                self.PATTERN_HEX,
                "is not a hex string (expected format like '0x14CA8093')",
            ),
        }
        regex, suffix = pattern_messages.get(pattern, (None, None))
        if regex is None:
            return
        if not regex.match(s):
            label = "Value" if pattern == "snake_case" or pattern == "hex" else pattern.title()
            self.errors.append(f"{path}: {label} '{s}' {suffix}")

    def _validate_integer(self, n: int, schema: Dict, path: str) -> None:
        if not isinstance(n, int):
            return

        minimum = schema.get("minimum")
        if minimum is not None and n < minimum:
            self.errors.append(f"{path}: Value {n} is less than minimum {minimum}")

        maximum = schema.get("maximum")
        if maximum is not None and n > maximum:
            self.errors.append(f"{path}: Value {n} is greater than maximum {maximum}")


def validate_manifest(manifest_data: Dict) -> Tuple[bool, List[str]]:
    """Validate an in-memory manifest dict against the MESA schema."""
    return ManifestValidator().validate(manifest_data)


def validate_manifest_file(filepath: str) -> Tuple[bool, List[str]]:
    """Validate a manifest file (resolving any ``extends`` chain first).

    Returns ``(is_valid, errors)``. Inheritance is resolved exactly as it
    will be at runtime so override-only typos are caught here.
    """
    try:
        merged_data = read_manifest_dict_with_inheritance(Path(filepath))
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except FileNotFoundError as e:
        return False, [str(e) if str(e) else f"File not found: {filepath}"]
    except ManifestError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Error loading base manifest: {e}"]

    return validate_manifest(merged_data)


class ManifestValidationReporter:
    """CLI-friendly reporter that wraps :func:`validate_manifest_file`.

    Adds non-schema lint warnings (missing recommended ``description`` /
    ``maintainer`` fields, empty ``supported_examples``) on the fully merged
    manifest and formats the result for terminal output. All authoritative
    schema rules still live in :class:`ManifestValidator`; this class only
    layers CLI presentation on top.
    """

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_manifest(self, manifest_path: str) -> bool:
        """Validate one manifest file and collect lint warnings on the merged dict."""
        self.errors = []
        self.warnings = []

        is_valid, validation_errors = validate_manifest_file(manifest_path)
        if not is_valid:
            self.errors.extend(validation_errors)
            return False

        try:
            merged = read_manifest_dict_with_inheritance(Path(manifest_path))
        except Exception as e:
            self.errors.append(f"Failed to load manifest for lint: {e}")
            return False

        self._collect_lint_warnings(merged)
        return True

    def _collect_lint_warnings(self, merged: Dict[str, Any]) -> None:
        design_info = merged.get("design_info", {})
        if not design_info.get("description"):
            self.warnings.append("design_info.description is recommended but missing")

        for core_name, core in (merged.get("debug_cores") or {}).items():
            if isinstance(core, dict) and core.get("enabled") and not core.get("description"):
                self.warnings.append(f"debug_cores.{core_name}: missing description")

        if not merged.get("supported_examples"):
            self.warnings.append("supported_examples is empty")

        metadata = merged.get("metadata", {})
        if not metadata.get("maintainer"):
            self.warnings.append("metadata.maintainer is recommended but missing")

    def get_validation_report(self) -> str:
        """Format collected errors and warnings for CLI output."""
        report: List[str] = []

        if self.errors:
            report.append("ERRORS:")
            report.extend(f"  - {error}" for error in self.errors)

        if self.warnings:
            report.append("WARNINGS:")
            report.extend(f"  - {warning}" for warning in self.warnings)

        if not self.errors and not self.warnings:
            report.append("VALIDATION PASSED")

        return "\n".join(report)
