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

"""Notebook cell template engine for the MESA CLI (internal).

The ``new-example`` subcommand of :mod:`chipscopy.examples.mesa._cli`
scaffolds notebooks by stitching together three kinds of code cells:
``setup_cell``, ``program_cell``, and a per-template ``body_*`` cell.
Those cell sources used to live as hardcoded Python strings inside
``_cli.py``, which was prone to API drift and impossible to syntax-check
at build time.

This module loads them from ``chipscopy/examples/mesa/templates/*.tmpl``
files and renders them with :class:`string.Template`. ``string.Template``
is part of the Python standard library, so no new third-party dependency
is required for the maintainer-only CLI.
"""

import re
from importlib.resources import files
from string import Template
from typing import List

_VALID_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_BODY_PREFIX = "body_"
_TEMPLATE_SUFFIX = ".py.tmpl"


def _sanitize_identifier(value: str) -> str:
    """Return ``value`` if it is a valid Python identifier, else raise."""
    if not _VALID_IDENTIFIER.match(value):
        raise ValueError(
            f"Invalid example_id: {value!r}; must be a valid Python identifier"
        )
    return value


class NotebookTemplateEngine:
    """Render MESA notebook cells from ``.tmpl`` files via ``string.Template``.

    Templates live in ``chipscopy.examples.mesa/templates`` and are loaded
    through :mod:`importlib.resources`, so the engine works the same way
    when running from a source checkout, an editable install, or a wheel.
    """

    def __init__(self) -> None:
        self._templates_dir = files("chipscopy.examples.mesa").joinpath("templates")

    def _load(self, name: str) -> Template:
        resource = self._templates_dir.joinpath(name)
        if not resource.is_file():
            raise FileNotFoundError(f"MESA template not found: {name}")
        return Template(resource.read_text(encoding="utf-8"))

    def render_setup_cell(self, example_id: str) -> str:
        """Render the canonical MESA setup cell for ``example_id``."""
        return self._load("setup_cell.py.tmpl").substitute(
            EXAMPLE_ID=_sanitize_identifier(example_id)
        )

    def render_program_cell(self) -> str:
        """Render the canonical MESA program/discover cell."""
        return self._load("program_cell.py.tmpl").substitute()

    def render_body(self, template_name: str) -> str:
        """Render the body cell for the named scaffolding template."""
        available = self.available_body_templates()
        if template_name not in available:
            raise ValueError(
                f"Unknown body template: {template_name!r}; available: {available}"
            )
        return self._load(f"{_BODY_PREFIX}{template_name}{_TEMPLATE_SUFFIX}").substitute()

    def available_body_templates(self) -> List[str]:
        """Return the sorted list of available body-template names.

        Returns an empty list if the templates directory is not present
        (for example, in a partial install) so importing the MESA package
        and running unrelated CLI subcommands keeps working. Callers that
        need at least one template should check the result and surface
        their own error.
        """
        try:
            entries = list(self._templates_dir.iterdir())
        except (FileNotFoundError, NotADirectoryError):
            return []
        return sorted(
            entry.name[len(_BODY_PREFIX): -len(_TEMPLATE_SUFFIX)]
            for entry in entries
            if entry.name.startswith(_BODY_PREFIX) and entry.name.endswith(_TEMPLATE_SUFFIX)
        )
