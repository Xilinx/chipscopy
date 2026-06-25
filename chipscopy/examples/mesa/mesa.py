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

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple

from chipscopy import get_design_files

from .utils import (
    ManifestError,
    find_manifest_files,
    get_designs_directory,
    read_manifest_dict_with_inheritance,
)


# ============================================================================
# Type-safe manifest dataclasses
# ============================================================================


@dataclass
class DebugCore:
    """Represents a debug core configuration."""

    enabled: bool
    description: str
    features: List[str] = field(default_factory=list)
    quad_names: Optional[List[str]] = None
    memory_types: Optional[List[str]] = None
    core_instances: Optional[List[Dict[str, Any]]] = None
    node_names: Optional[List[str]] = None
    trigger_base_address: Optional[str] = None
    probe_mapping: Optional[Dict[str, str]] = None
    vio_hierarchy: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebugCore":
        return cls(
            enabled=data.get("enabled", False),
            description=data.get("description", ""),
            features=data.get("features", []),
            quad_names=data.get("quad_names"),
            memory_types=data.get("memory_types"),
            core_instances=data.get("core_instances"),
            node_names=data.get("node_names"),
            trigger_base_address=data.get("trigger_base_address"),
            probe_mapping=data.get("probe_mapping"),
            vio_hierarchy=data.get("vio_hierarchy"),
        )


@dataclass
class DesignInfo:
    """Represents design information."""

    design_name: str
    hw_platform: str
    programming_flow: str
    design_path: Path
    family: str
    device: str
    board: Optional[str] = None
    description: Optional[str] = None
    boot_pdi_pattern: Optional[str] = None
    pld_pdi_pattern: Optional[str] = None
    idcode: Optional[str] = None
    idcode_list: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DesignInfo":
        try:
            return cls(
                design_name=data["design_name"],
                hw_platform=data["hw_platform"],
                programming_flow=data["programming_flow"],
                design_path=Path(data["design_path"]),
                family=data["family"],
                device=data["device"],
                board=data.get("board"),
                description=data.get("description"),
                boot_pdi_pattern=data.get("boot_pdi_pattern"),
                pld_pdi_pattern=data.get("pld_pdi_pattern"),
                idcode=data.get("idcode"),
                idcode_list=data.get("idcode_list"),
            )
        except KeyError as e:
            raise ManifestError(f"design_info: missing required field {e}")


@dataclass
class ManifestMetadata:
    """Represents manifest metadata."""

    created_date: str
    version: str
    maintainer: Optional[str] = None
    last_updated: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManifestMetadata":
        try:
            return cls(
                created_date=data["created_date"],
                version=data["version"],
                maintainer=data.get("maintainer"),
                last_updated=data.get("last_updated"),
                notes=data.get("notes"),
            )
        except KeyError as e:
            raise ManifestError(f"metadata: missing required field {e}")


@dataclass
class Manifest:
    """Type-safe MESA manifest representation.

    Provides IDE autocomplete and type checking for manifest fields.
    """

    MEM_TYPE_MAP: ClassVar[Dict[int, str]] = {1: "DDR4", 2: "LPDDR4", 4: "DDR5", 5: "LPDDR5"}
    IDCODE_PLACEHOLDER: ClassVar[str] = "0x00000000"

    design_info: DesignInfo
    debug_cores: Dict[str, DebugCore]
    supported_examples: List[str]
    metadata: ManifestMetadata
    manifest_path: Path

    @staticmethod
    def get_mem_type_name(mem_type_val: int) -> str:
        """Translate DDR memory type integer code to human-readable name.

        Args:
            mem_type_val: Integer from ``ddr_node.get_property(["mem_type"])["mem_type"]``.

        Returns:
            String name like ``"DDR4"``, ``"LPDDR4"``, ``"DDR5"``, ``"LPDDR5"``,
            or ``"Unknown(N)"``.
        """
        return Manifest.MEM_TYPE_MAP.get(mem_type_val, f"Unknown({mem_type_val})")

    def has_core(self, core_name: str) -> bool:
        """Check if a debug core is present and enabled."""
        return core_name in self.debug_cores and self.debug_cores[core_name].enabled

    def has_all_cores(self, *core_names: str) -> bool:
        """Check if all specified cores are present and enabled."""
        return all(self.has_core(core) for core in core_names)

    def get_enabled_cores(self) -> List[str]:
        """Get list of all enabled core names."""
        return [name for name, core in self.debug_cores.items() if core.enabled]

    def has_feature(self, core_name: str, feature: str) -> bool:
        """Check if a specific feature is available for a core."""
        if not self.has_core(core_name):
            return False
        return feature in self.debug_cores[core_name].features

    def supports_example(self, example_id: str) -> bool:
        """Check if this manifest supports a specific example."""
        return example_id in self.supported_examples

    def get_first_enabled_core_by_prefix(
        self,
        prefix: str,
        filter_fn: Optional[Callable[[str, DebugCore], bool]] = None,
        index: int = 0,
    ) -> Optional[Tuple[str, DebugCore]]:
        """Get enabled core by prefix with optional filtering and indexing.

        Args:
            prefix: Core name prefix to match (e.g., ``"ibert_"``, ``"ila"``, ``"vio"``).
            filter_fn: Optional ``(core_name, core) -> bool`` for custom filtering.
            index: Index of matching core to return (default ``0``).

        Returns:
            Tuple of ``(core_name, DebugCore)`` or ``None``.
        """
        seen = 0
        for core_name, core in self.debug_cores.items():
            if not core.enabled or not core_name.startswith(prefix):
                continue
            if filter_fn and not filter_fn(core_name, core):
                continue
            if seen == index:
                return core_name, core
            seen += 1
        return None

    def get_all_enabled_cores_by_prefix(
        self,
        prefix: str,
        filter_fn: Optional[Callable[[str, DebugCore], bool]] = None,
    ) -> List[Tuple[str, DebugCore]]:
        """Get all enabled cores whose name starts with ``prefix`` (with optional filter)."""
        results: List[Tuple[str, DebugCore]] = []
        for core_name, core in self.debug_cores.items():
            if not core.enabled or not core_name.startswith(prefix):
                continue
            if filter_fn and not filter_fn(core_name, core):
                continue
            results.append((core_name, core))
        return results

    def get_core_config(self, core_name: str, config_key: str, default=None):
        """Get a platform-specific configuration value from a debug core.

        For platform-specific hardware details like quad names, node names,
        and core instances. Algorithm parameters (scan patterns, step sizes,
        thresholds) should remain visible in notebooks for learning.
        """
        if not self.has_core(core_name):
            return default
        return getattr(self.debug_cores[core_name], config_key, default)

    def get_core_instance(self, core_name: str, index: int = 0) -> Optional[Dict]:
        """Get a specific core instance by name and index.

        Thin wrapper around :meth:`get_core_config` that returns the entry
        from the core's ``core_instances`` list at ``index``.
        """
        instances = self.get_core_config(core_name, "core_instances")
        if not instances or index >= len(instances):
            return None
        return instances[index]

    def get_ibert_core(
        self,
        filter_fn: Optional[Callable[[str, DebugCore], bool]] = None,
        index: int = 0,
    ) -> Optional[Tuple[str, DebugCore]]:
        """Get IBERT core (any type) with optional custom filtering and indexing."""
        return self.get_first_enabled_core_by_prefix("ibert_", filter_fn, index)

    def get_all_ibert_cores(
        self,
        filter_fn: Optional[Callable[[str, DebugCore], bool]] = None,
    ) -> List[Tuple[str, DebugCore]]:
        """Get all enabled IBERT cores with optional filtering."""
        return self.get_all_enabled_cores_by_prefix("ibert_", filter_fn)

    def program_device(
        self,
        device,
        design_files,
        *,
        delay_after_program: int = 0,
        show_progress_bar: bool = True,
        progress=None,
        done=None,
    ) -> None:
        """Program ``device`` according to the manifest's programming flow.

        Dispatches to the appropriate flow handler based on
        ``design_info.programming_flow``. Adding a new flow is one entry in
        :attr:`_FLOW_HANDLERS`.
        """
        flow = self.design_info.programming_flow
        handler = self._FLOW_HANDLERS.get(flow)
        if handler is None:
            raise ValueError(
                f"Unknown programming_flow: '{flow}'. "
                f"Expected one of {sorted(self._FLOW_HANDLERS)}"
            )
        handler(
            self,
            device,
            design_files,
            delay_after_program=delay_after_program,
            show_progress_bar=show_progress_bar,
            progress=progress,
            done=done,
        )

    def _program_flat(
        self,
        device,
        design_files,
        *,
        delay_after_program: int,
        show_progress_bar: bool,
        progress,
        done,
    ) -> None:
        pdi_file = design_files.programming_file
        print(f"Programming device (flat): {pdi_file}")
        device.program(
            pdi_file,
            delay_after_program=delay_after_program,
            show_progress_bar=show_progress_bar,
            progress=progress,
            done=done,
        )

    def _program_segmented(
        self,
        device,
        design_files,
        *,
        delay_after_program: int,
        show_progress_bar: bool,
        progress,
        done,
    ) -> None:
        design_path = Path(design_files.programming_file).parent
        boot_pdi, pld_pdi, _, _ = _resolve_segmented_design_paths(
            self.design_info, design_path, require_ltx=False
        )

        print("Programming device (segmented):")
        for label, pdi, skip_reset in (("1. Boot PDI", boot_pdi, False), ("2. PLD PDI", pld_pdi, True)):
            suffix = " (skip_reset=True)" if skip_reset else ""
            print(f"  {label}: {pdi}{suffix}")
            device.program(
                pdi,
                skip_reset=skip_reset,
                delay_after_program=delay_after_program,
                show_progress_bar=show_progress_bar,
                progress=progress,
                done=done,
            )

        print("Segmented programming complete")

    @staticmethod
    def _first_match_or_raise(directory: Path, pattern: str, label: str) -> str:
        matches = list(directory.glob(pattern))
        if not matches:
            raise RuntimeError(
                f"{label} not found in {directory} with pattern '{pattern}'\n"
                f"For segmented programming flow, {label} is required."
            )
        return str(matches[0])

    @staticmethod
    def _first_match_optional(directory: Path, pattern: str) -> str:
        matches = list(directory.glob(pattern))
        return str(matches[0]) if matches else ""

    _FLOW_HANDLERS: ClassVar[Dict[str, Callable[..., None]]] = {
        "flat": _program_flat,
        "segmented": _program_segmented,
    }

    def verify_device_idcode(self, device) -> bool:
        """Verify device JTAG IDCODE matches manifest expectation.

        Returns ``True`` if no IDCODE constraint is specified, if all
        IDCODEs are placeholders, or if the device IDCODE matches any
        configured value. Returns ``False`` only when a real IDCODE is
        specified and the device does not match.
        """
        if not self.design_info.idcode and not self.design_info.idcode_list:
            return True

        has_real_idcode = (
            (self.design_info.idcode and self.design_info.idcode != self.IDCODE_PLACEHOLDER)
            or (
                self.design_info.idcode_list
                and any(ic != self.IDCODE_PLACEHOLDER for ic in self.design_info.idcode_list)
            )
        )
        if not has_real_idcode:
            return True

        jtag_node = getattr(device, "jtag_node", None)
        device_idcode = getattr(jtag_node, "idCode", None) if jtag_node is not None else None
        if device_idcode is None:
            print("WARNING: Could not read device IDCODE, skipping verification")
            return True

        acceptable_idcodes: set = set()
        if self.design_info.idcode:
            acceptable_idcodes.add(int(self.design_info.idcode, 16))
        if self.design_info.idcode_list:
            for ic in self.design_info.idcode_list:
                acceptable_idcodes.add(int(ic, 16))

        if device_idcode not in acceptable_idcodes:
            print("ERROR: Device IDCODE mismatch!")
            print(f"  Device reports:  0x{device_idcode:08X}")
            print(f"  Manifest expects: {[hex(x) for x in sorted(acceptable_idcodes)]}")
            print(f"  Design device:   {self.design_info.device}")
            return False

        return True

    @classmethod
    def from_dict(cls, data: Dict[str, Any], manifest_path: Path) -> "Manifest":
        """Create Manifest from a dictionary that has already been merged with its bases."""
        if "design_info" not in data:
            raise ManifestError("manifest is missing required top-level field 'design_info'")
        if "metadata" not in data:
            raise ManifestError("manifest is missing required top-level field 'metadata'")

        debug_cores = {
            name: DebugCore.from_dict(core_data)
            for name, core_data in data.get("debug_cores", {}).items()
        }

        return cls(
            design_info=DesignInfo.from_dict(data["design_info"]),
            debug_cores=debug_cores,
            supported_examples=data.get("supported_examples", []),
            metadata=ManifestMetadata.from_dict(data["metadata"]),
            manifest_path=manifest_path,
        )

    @classmethod
    def from_file(cls, path: Path) -> "Manifest":
        """Load and return a Manifest from ``path``, resolving any ``extends`` chain.

        Raises :class:`~chipscopy.examples.mesa.utils.ManifestError` for any
        load / parse / merge / required-field problem so callers can catch a
        single exception type.
        """
        try:
            merged = read_manifest_dict_with_inheritance(path)
        except FileNotFoundError:
            raise ManifestError(
                f"Manifest file not found: {path}\n"
                f"   Make sure the file exists at the specified path."
            )
        except json.JSONDecodeError as e:
            raise ManifestError(
                f"Invalid JSON in manifest file: {path}\n"
                f"   JSON parse error at line {e.lineno}, column {e.colno}: {e.msg}\n"
                f"   Fix the JSON syntax and try again."
            )

        return cls.from_dict(merged, path)


# ============================================================================
# Manifest registry with mtime-based caching
# ============================================================================


class ManifestRegistry:
    """MESA manifest registry for design discovery.

    Manifests are loaded lazily and cached by file path. Each cached entry
    is keyed on the file's mtime so notebook reruns automatically pick up
    edits without an explicit invalidate call.
    """

    def __init__(self) -> None:
        self._by_path: Dict[Path, Tuple[Manifest, float]] = {}

    def get_designs_directory(self) -> Path:
        """Get the designs directory path (delegates to :func:`get_designs_directory`)."""
        return get_designs_directory()

    def find_manifest_files(self) -> List[Path]:
        """Find all manifest.json files under the configured designs directory."""
        return find_manifest_files(self.get_designs_directory())

    def invalidate_cache(self, platform: Optional[str] = None) -> None:
        """Drop cached manifests. Filters by platform when one is given."""
        if platform is None:
            self._by_path.clear()
            return
        for path in [p for p, (m, _) in self._by_path.items() if m.design_info.hw_platform == platform]:
            del self._by_path[path]

    def invalidate_directory_cache(self) -> None:
        """Backward-compatible alias for :meth:`invalidate_cache`."""
        self.invalidate_cache()

    def _load_path(self, path: Path) -> Optional[Manifest]:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return None

        cached = self._by_path.get(path)
        if cached and cached[1] == mtime:
            return cached[0]

        try:
            manifest = Manifest.from_file(path)
        except ManifestError:
            return None

        self._by_path[path] = (manifest, mtime)
        return manifest

    def get_manifest(self, platform: str, example_id: Optional[str] = None) -> Optional[Manifest]:
        """Get MESA manifest for ``platform`` and optional ``example_id``.

        Returns the first manifest whose ``hw_platform`` matches and that
        either supports the requested example or - if no example is given -
        is just the first match. Returns ``None`` when no manifest matches.
        """
        matching: List[Manifest] = []

        for manifest_path in self.find_manifest_files():
            manifest = self._load_path(manifest_path)
            if manifest is None or manifest.design_info.hw_platform != platform:
                continue

            matching.append(manifest)
            if example_id is None:
                return manifest
            if manifest.supports_example(example_id):
                return manifest

        if example_id and matching:
            self._print_example_not_supported_error(platform, example_id, matching)

        return None

    def _print_example_not_supported_error(
        self, platform: str, example_id: str, manifests: List[Manifest]
    ) -> None:
        print(
            f"ERROR: MESA Error: Example '{example_id}' is not supported on platform '{platform}'\n"
        )
        print(
            f"   The platform '{platform}' was found, but the example is not listed in any MESA manifest."
        )
        print(f"   Available examples for '{platform}':\n")

        for manifest in manifests:
            design_name = manifest.design_info.design_name
            print(f"   Design: {design_name}")
            for ex in manifest.supported_examples:
                print(f"     - {ex}")

    def get_all_platforms(self) -> List[str]:
        """Get sorted list of all available platforms across all manifests."""
        platforms: set = set()
        for manifest_path in self.find_manifest_files():
            manifest = self._load_path(manifest_path)
            if manifest is not None:
                platforms.add(manifest.design_info.hw_platform)
        return sorted(platforms)


_registry = ManifestRegistry()


def get_manifest(platform: str, example_id: Optional[str] = None) -> Optional[Manifest]:
    """Get MESA manifest for platform and optional example ID."""
    return _registry.get_manifest(platform, example_id)


def get_all_platforms() -> List[str]:
    """Get list of all available platforms."""
    return _registry.get_all_platforms()


# ============================================================================
# Notebook setup helper
# ============================================================================


def _ltx_pattern_from_pdi_pattern(pdi_pattern: str) -> str:
    if ".pdi" in pdi_pattern:
        return pdi_pattern.replace(".pdi", ".ltx", 1)
    return pdi_pattern


def _resolve_segmented_design_paths(
    design_info: DesignInfo,
    design_dir: Path,
    *,
    require_ltx: bool = True,
) -> Tuple[str, str, str, str]:
    """Resolve boot/PLD PDI paths and optional matching LTX paths under ``design_dir``.

    PDIs are always required. When ``require_ltx`` is True, Boot and PLD LTX files
    derived from the manifest PDI glob patterns must exist. When False, missing
    LTX paths are returned as empty strings (programming does not need LTX).
    """
    boot_pdi_pat = design_info.boot_pdi_pattern or "*_boot.pdi"
    pld_pdi_pat = design_info.pld_pdi_pattern or "*_pld.pdi"
    boot_pdi = Manifest._first_match_or_raise(design_dir, boot_pdi_pat, "Boot PDI")
    pld_pdi = Manifest._first_match_or_raise(design_dir, pld_pdi_pat, "PLD PDI")
    boot_ltx_pat = _ltx_pattern_from_pdi_pattern(boot_pdi_pat)
    pld_ltx_pat = _ltx_pattern_from_pdi_pattern(pld_pdi_pat)
    if require_ltx:
        boot_ltx = Manifest._first_match_or_raise(design_dir, boot_ltx_pat, "Boot LTX")
        pld_ltx = Manifest._first_match_or_raise(design_dir, pld_ltx_pat, "PLD LTX")
    else:
        boot_ltx = Manifest._first_match_optional(design_dir, boot_ltx_pat)
        pld_ltx = Manifest._first_match_optional(design_dir, pld_ltx_pat)
    return boot_pdi, pld_pdi, boot_ltx, pld_ltx


@dataclass
class ExampleDesign:
    """Resolved design files for an example notebook.

    Hides whether the notebook is running in MESA mode (manifest-driven) or
    direct mode (user-supplied PDI/LTX), so the rest of the notebook uses one
    consistent interface.

    Attributes:
        manifest:         Loaded :class:`Manifest` when MESA resolved the design,
                          or ``None`` when the user supplied design files directly.
        design_files:     ``DesignFiles`` object from
                          :func:`chipscopy.get_design_files` when MESA is used,
                          ``None`` otherwise.
        programming_file: Path to the PDI / programming file used by the device.
        probes_file:      Path to the LTX / probes file used by the device.
        device_family:    Device family string suitable for
                          ``session.devices.filter_by(family=...)``.
        hw_platform:      Hardware platform identifier (e.g. ``"vck190"``).
        example_id:       Example ID requested by the notebook.
        programming_files: Ordered programming file paths (boot then PLD when segmented).
        probes_files:      Ordered LTX paths when resolved (boot then PLD when both exist).
                          May be shorter than ``programming_files`` or empty when no LTX
                          is available; probe files are optional and not required for
                          :meth:`program_device`.
    """

    manifest: Optional["Manifest"]
    design_files: Optional[Any]
    programming_file: str
    probes_file: str
    device_family: str
    hw_platform: str
    example_id: str
    programming_files: List[str] = field(default_factory=list)
    probes_files: List[str] = field(default_factory=list)

    @property
    def using_manifest(self) -> bool:
        """True when this design was resolved through a MESA manifest."""
        return self.manifest is not None

    def verify_device_idcode(self, device) -> bool:
        """Verify the device JTAG IDCODE matches the resolved design.

        Returns ``True`` in direct mode (no manifest constraint) and
        delegates to :meth:`Manifest.verify_device_idcode` in MESA mode.
        """
        if self.manifest is None:
            return True
        return self.manifest.verify_device_idcode(device)

    def program_device(self, device, **program_options) -> None:
        """Program the device using the resolved design files.

        In MESA mode this delegates to :meth:`Manifest.program_device`, which
        handles flat vs. segmented programming flows. In direct mode it falls
        back to ``device.program(self.programming_file)``.
        """
        if self.manifest is not None and self.design_files is not None:
            self.manifest.program_device(device, self.design_files, **program_options)
        else:
            print(f"Programming device: {self.programming_file}")
            device.program(self.programming_file, **program_options)

    def print_summary(self) -> None:
        """Print the server-independent design details used by the notebook."""
        mode = "MESA manifest" if self.using_manifest else "user-provided files"
        print(f"Design source:    {mode}")
        print(f"HW_PLATFORM:      {self.hw_platform}")
        print(f"DEVICE_FAMILY:    {self.device_family}")
        print(f"PROGRAMMING_FILE: {self.programming_file}")
        print(f"PROBES_FILE:      {self.probes_file}")
        print(f"PROGRAMMING_FILES: {self.programming_files}")
        print(f"PROBES_FILES:      {self.probes_files}")


def resolve_example_design(
    hw_platform: str,
    example_id: str,
    *,
    programming_file: str = "",
    probes_file: str = "",
    device_family: str = "versal",
) -> ExampleDesign:
    """Resolve programming and probes files for an example notebook.

    Two paths are supported, in this order:

    1. **Direct mode**: if ``programming_file`` is non-empty the MESA manifest
       lookup is skipped entirely. The notebook can run with any user-provided
       PDI/LTX combination - no manifest is required.

    2. **MESA mode**: otherwise the design is resolved from the MESA manifest
       for ``hw_platform`` and ``example_id``. The platform's ``design_path``
       is converted into actual file paths via
       :func:`chipscopy.get_design_files`, and ``device_family`` is taken from
       the manifest.

    Raises:
        RuntimeError: In MESA mode when no compatible manifest is found.
    """
    if programming_file:
        return ExampleDesign(
            manifest=None,
            design_files=None,
            programming_file=programming_file,
            probes_file=probes_file,
            programming_files=[programming_file],
            probes_files=[probes_file] if probes_file else [],
            device_family=device_family,
            hw_platform=hw_platform,
            example_id=example_id,
        )

    manifest = get_manifest(hw_platform, example_id)
    if manifest is None:
        raise RuntimeError(
            f"No compatible MESA design found for platform '{hw_platform}' "
            f"and example '{example_id}'.\n"
            f"Either set HW_PLATFORM to a supported board, add this example "
            f"to a manifest's supported_examples, or pass programming_file=... "
            f"and probes_file=... to bypass MESA and run with your own files."
        )

    design_files = get_design_files(str(manifest.design_info.design_path))
    if manifest.design_info.programming_flow == "segmented":
        design_dir = Path(design_files.programming_file).parent
        boot_pdi, pld_pdi, boot_ltx, pld_ltx = _resolve_segmented_design_paths(
            manifest.design_info, design_dir, require_ltx=False
        )
        probes_scalar = pld_ltx or boot_ltx or (design_files.probes_file or "")
        design_files = design_files._replace(programming_file=pld_pdi, probes_file=probes_scalar)
        programming_file = pld_pdi
        probes_file = probes_scalar
        programming_files = [boot_pdi, pld_pdi]
        probes_files = [p for p in (boot_ltx, pld_ltx) if p]
    else:
        programming_file = design_files.programming_file or ""
        probes_file = design_files.probes_file or ""
        programming_files = [programming_file] if programming_file else []
        probes_files = [probes_file] if probes_file else []

    return ExampleDesign(
        manifest=manifest,
        design_files=design_files,
        programming_file=programming_file,
        probes_file=probes_file,
        programming_files=programming_files,
        probes_files=probes_files,
        device_family=manifest.design_info.family,
        hw_platform=hw_platform,
        example_id=example_id,
    )


# ============================================================================
# Utility functions
# ============================================================================


def print_manifest_info(manifest: Manifest, detailed: bool = False) -> None:
    """Print manifest information in a formatted way."""
    print("=" * 80)
    print(f"DESIGN: {manifest.design_info.design_name}")
    print("=" * 80)

    print(f"\nPlatform:     {manifest.design_info.hw_platform}")
    print(f"Device:       {manifest.design_info.device}")
    print(f"Family:       {manifest.design_info.family}")
    print(f"Board:        {manifest.design_info.board or 'N/A'}")

    if manifest.design_info.description:
        print(f"Description:  {manifest.design_info.description}")

    print("\nEnabled Debug Cores:")
    for core_name in manifest.get_enabled_cores():
        core = manifest.debug_cores[core_name]
        print(f"  - {core_name}: {core.description}")
        if detailed and core.features:
            print(f"    Features: {', '.join(core.features)}")

    print(f"\nSupported Examples ({len(manifest.supported_examples)}):")
    for i, example_id in enumerate(manifest.supported_examples, 1):
        print(f"  {i:2}. {example_id}")

    print("=" * 80)
