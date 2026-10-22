# SPDX-License-Identifier: Apache-2.0
"""Dependency-free finite-data guard shared with the Blender backend."""

import math


class SourceValidationError(ValueError):
    pass


def require_finite(value, path="$", identifier="source", _active=None):
    if isinstance(value, float) and not math.isfinite(value):
        raise SourceValidationError(f"{identifier} {path}: non-finite number")
    if isinstance(value, (dict, list)):
        active = set() if _active is None else _active
        if id(value) in active:
            raise SourceValidationError(f"{identifier} {path}: recursive YAML container")
        active.add(id(value))
        try:
            entries = value.items() if isinstance(value, dict) else enumerate(value)
            for key, child in entries:
                require_finite(child, f"{path}.{key}", identifier, active)
        finally:
            active.remove(id(value))


