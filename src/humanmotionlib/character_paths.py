# SPDX-License-Identifier: Apache-2.0
"""Pure path checks shared by host tests and the Blender construction entry."""

from __future__ import annotations


def validate_managed_output_entries(output, allowed):
    """Require managed scratch roots to be directories contained by output."""
    output = output.resolve()
    for name in allowed - {"input.json", "character-render-request.json"}:
        managed = output / name
        if managed.exists() and (not managed.is_dir() or not managed.resolve().is_relative_to(output)):
            raise ValueError("backend process scratch escaped its owning run: " + str(managed))


__all__ = ["validate_managed_output_entries"]
