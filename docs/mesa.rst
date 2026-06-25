..
   Copyright (C) 2021-2022, Xilinx, Inc.
   Copyright (C) 2022-2026, Advanced Micro Devices, Inc.

     Licensed under the Apache License, Version 2.0 (the "License");
     you may not use this file except in compliance with the License.
     You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.

MESA
====

MESA (Manifest driven Example System for All-platforms) is the runtime
helper that every shipped ChipScoPy example notebook uses to locate its
programming and probes files, validate that the connected device matches
the expected design, and program the device with the correct flow
(``flat`` or ``segmented``).

Each design ships with a ``manifest.json`` that captures the platform's
debug cores, programming flow, and supported example IDs. MESA discovers
those manifests, resolves any ``extends`` chain, and exposes a small
typed Python API. Users write one notebook; MESA adapts it to whichever
hardware platform the manifest targets.

.. py:currentmodule:: chipscopy.examples.mesa


Quick start
-----------

Every notebook in ``chipscopy/examples/`` uses the same setup-cell shape,
built around :func:`resolve_example_design`. It returns an
:class:`ExampleDesign` that hides whether the notebook is running in
**MESA mode** (manifest-driven) or **direct mode** (user-supplied PDI /
LTX), so the rest of the example is identical in both cases.

.. code-block:: python
    :emphasize-lines: 13, 21, 23

    import os
    from chipscopy import create_session, delete_session
    from chipscopy.examples.mesa import resolve_example_design

    CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
    HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")
    HW_PLATFORM = "vck190"
    EXAMPLE_ID = "ila_and_vio"

    PROGRAMMING_FILE = ""  # Direct mode: set to your own PDI to skip MESA
    PROBES_FILE = ""

    example_design = resolve_example_design(
        HW_PLATFORM,
        EXAMPLE_ID,
        programming_file=PROGRAMMING_FILE,
        probes_file=PROBES_FILE,
    )
    example_design.print_summary()

    session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
    device = session.devices.filter_by(family=example_design.device_family).get()

    if not example_design.verify_device_idcode(device):
        raise RuntimeError("Device IDCODE does not match the manifest design.")

    example_design.program_device(device)
    device.discover_and_setup_cores(ltx_file=example_design.probes_file)

    # ... your example logic here ...

    delete_session(session)

The ``HW_PLATFORM`` and ``EXAMPLE_ID`` constants are the only things a
notebook author needs to set; everything else is derived from the
manifest.

ExampleDesign paths (flat vs segmented)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`ExampleDesign` exposes string fields ``programming_file`` and
``probes_file`` for the usual notebook pattern (assign to ``PROGRAMMING_FILE``
/ ``PROBES_FILE`` and pass them to APIs such as
``device.discover_and_setup_cores(ltx_file=...)``). It also exposes
``programming_files`` and ``probes_files``: ordered lists of resolved
programming paths and any matching LTX paths. ``probes_files`` may be empty
or shorter than ``programming_files`` when no LTX is present (LTX is for
debug setup, not for ``device.program``).

For ``programming_flow: "flat"``, each list has at most one element matching
the scalar fields when paths exist. For ``"segmented"``, ``programming_files``
is ``[boot, PLD]`` in that order; the scalars are set to the **PLD** pair when
an LTX is resolved so ILA/VIO and other PL-side debug use the correct LTX
without per-notebook branching. If no segmented LTX is found, ``probes_file``
falls back to any LTX returned by :func:`chipscopy.get_design_files`, or is
empty. Boot and PLD PDIs are always required for segmented programming; LTX
files are optional and are resolved with the same manifest glob patterns when
present.

To retarget another board, change ``HW_PLATFORM`` (or override it via
the environment) - any platform that has a manifest will work:

.. code-block:: bash

    HW_PLATFORM=vck190 python my_example.py
    HW_PLATFORM=vpk120 python my_example.py
    HW_PLATFORM=vcu128 python my_example.py


Working with the manifest
-------------------------

The :attr:`ExampleDesign.manifest` attribute returns a typed
:class:`Manifest` (or ``None`` in direct mode). Use it to gate
optional capabilities cleanly instead of hard-coding per-platform
branches in the notebook.

.. code-block:: python

    manifest = example_design.manifest

    if manifest and manifest.has_core("memory"):
        memory = device.memory[0]

    if manifest and manifest.has_all_cores("ila", "vio"):
        ila = device.ila_cores[0]

    if manifest and manifest.has_feature("memory", "2d_eye_scan"):
        run_2d_eye_scan(device)

For platform-specific knobs (quad names, ILA instance paths, NoC node
names), use :meth:`Manifest.get_core_config` so the notebook reads the
value from the manifest rather than embedding it in code:

.. code-block:: python

    quad_names = manifest.get_core_config("ibert_gty", "quad_names", [])
    node_names = manifest.get_core_config("noc_perfmon", "node_names", [])

    ila_instance = manifest.get_core_instance("ila", index=0)
    if ila_instance:
        ila_name = ila_instance["name"]
        probe_prefix = ila_instance.get("probe_prefix", "")


Manifest structure
------------------

Each design directory under ``examples/designs/<platform>/<design>``
contains a ``manifest.json`` like this:

.. code-block:: json

    {
      "extends": "_base/versal_standard_cores.json",
      "design_info": {
        "design_name": "chipscopy_ced",
        "description": "ChipScoPy CED for VCK190",
        "hw_platform": "vck190",
        "programming_flow": "flat",
        "design_path": "vck190/production/chipscopy_ced",
        "family": "versal",
        "device": "xcvc1902",
        "board": "VCK190",
        "idcode": "0x14CA8093"
      },
      "debug_cores": {
        "ibert_gty": {
          "enabled": true,
          "quad_names": ["Quad_205", "Quad_204", "Quad_201", "Quad_105"]
        }
      },
      "supported_examples": [
        "ila_and_vio",
        "link_and_eye_scan",
        "ddr_example"
      ],
      "metadata": {
        "version": "1.0.0",
        "maintainer": "AMD ChipScoPy Team"
      }
    }

Notable fields:

- ``extends`` (optional) - relative path to a base manifest under
  ``_base/``; child manifests deep-merge over the base.
- ``programming_flow`` - must be ``"flat"`` (single PDI) or
  ``"segmented"`` (boot + PLD PDI for partial reconfiguration).
- ``family`` - must match a ChipScoPy device family
  (``versal``, ``virtexuplus``, etc.).
- ``idcode`` / ``idcode_list`` - JTAG IDCODE(s) used by
  :meth:`ExampleDesign.verify_device_idcode` to detect the wrong board
  before programming. Use ``idcode_list`` for multi-variant silicon
  (e.g. production + ES).

The full schema lives in
``chipscopy/examples/mesa/manifest_schema.json``. Both the JSON schema
and the Python-side :class:`ManifestValidator` set
``additionalProperties: false`` for nested ``debug_cores`` entries, so
typo'd keys (e.g. ``descripton``) are rejected at validation time
instead of silently behaving as no-ops at runtime.


Programming flows
-----------------

:meth:`ExampleDesign.program_device` and :meth:`Manifest.program_device`
both dispatch on the manifest's ``programming_flow`` field through an
internal flow table; adding a new flow is a one-line registration.

============== ============== ============ ===========================================
Flow           PDI files       Skip reset   Use case
============== ============== ============ ===========================================
``flat``       1 (monolithic) No           Simple designs, full configuration
``segmented``  2 (boot + PLD) Yes (PLD)    Partial reconfiguration, boot + dynamic
============== ============== ============ ===========================================

Segmented boot and PLD PDIs (and LTX paths during example resolution) use
the manifest's ``boot_pdi_pattern`` / ``pld_pdi_pattern`` with the same
matching rules whenever MESA resolves files or runs the segmented program
steps.


Management CLI (internal)
-------------------------

ChipScoPy maintainers use the private :mod:`chipscopy.examples.mesa._cli`
module to validate, lint, and scaffold MESA manifests and example notebooks.
End users do not need to call it; it is documented here as a reference for
maintainers contributing new MESA examples.

.. code-block:: bash

    # Validate every manifest under chipscopy/examples/designs.
    python -m chipscopy.examples.mesa._cli validate --all

    # Validate a specific manifest by path.
    python -m chipscopy.examples.mesa._cli validate --manifest path/to/manifest.json

    # Cross-check manifests vs. notebook filenames; flag dangling references
    # and per-manifest lint warnings.
    python -m chipscopy.examples.mesa._cli lint

    # Add an example ID to all compatible manifests (use --dry-run first).
    python -m chipscopy.examples.mesa._cli add-example \
        --example-id my_example --dry-run

    # Scaffold a new MESA-powered example notebook.
    python -m chipscopy.examples.mesa._cli new-example \
        --example-id my_example --template basic

    # Print a compatibility report (platforms, examples, categories).
    python -m chipscopy.examples.mesa._cli report


API reference
-------------

Notebook entry points
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: resolve_example_design

.. autofunction:: get_manifest

.. autofunction:: get_all_platforms

.. autofunction:: get_designs_directory

.. autofunction:: print_manifest_info

ExampleDesign
~~~~~~~~~~~~~

.. autoclass:: ExampleDesign
    :members:

Manifest
~~~~~~~~

.. autoclass:: Manifest
    :members:

.. autoclass:: DebugCore
    :members:

.. autoclass:: DesignInfo
    :members:

.. autoclass:: ManifestMetadata
    :members:

Registry and errors
~~~~~~~~~~~~~~~~~~~

.. autoclass:: ManifestRegistry
    :members:

.. autoexception:: ManifestError

Validation
~~~~~~~~~~

.. autofunction:: validate_manifest_file

.. autoclass:: ManifestValidationReporter
    :members:
