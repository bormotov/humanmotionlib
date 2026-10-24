"""HumanMotionLib installed runtime package.

Keep package import safe for Blender's embedded Python: no host-only
libraries or bpy are imported here.
"""

from ._version import __version__

__all__ = ["__version__"]
