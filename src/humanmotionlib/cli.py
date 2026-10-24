# SPDX-License-Identifier: Apache-2.0
"""Installed command dispatcher for the supported HML operations."""

from __future__ import annotations

import argparse
import sys

from humanmotionlib import __version__


_COMMANDS = {
    "validate": ("humanmotionlib.validate", "Validate packaged diagnostic sources."),
    "prepare-skeleton": ("humanmotionlib.prepare_skeleton", "Prepare canonical skeleton diagnostics."),
    "run-blender": ("humanmotionlib.run_blender", "Run the pinned Blender backend."),
    "verify-skeleton": ("humanmotionlib.verify_skeleton", "Verify evaluated skeleton evidence."),
    "review-pack": ("humanmotionlib.review_pack", "Build or regenerate a review pack."),
    "check-environment": ("humanmotionlib.check_host", "Inspect the installed HML host environment."),
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--version", "-V"):
        print(f"humanmotionlib {__version__}")
        return 0
    workspace = None
    if args and args[0] == "--workspace":
        if len(args) < 3:
            raise SystemExit("hml --workspace requires PATH followed by a subcommand")
        workspace = args[1]
        args = args[2:]
    if not args or args[0] in ("-h", "--help"):
        parser = argparse.ArgumentParser(prog="hml", description=__doc__)
        parser.add_argument("--workspace", metavar="PATH", help="Absolute caller-owned workspace for filesystem-writing commands")
        parser.add_argument("--version", action="version", version=f"humanmotionlib {__version__}")
        parser.add_argument("command", choices=sorted(_COMMANDS))
        parser.print_help()
        return 0
    command = args.pop(0)
    if command not in _COMMANDS:
        raise SystemExit(f"unknown hml command {command!r}; choose from {', '.join(sorted(_COMMANDS))}")
    module_name, _ = _COMMANDS[command]
    module = __import__(module_name, fromlist=["main"])
    sys.argv = ["hml " + command, *args]
    if command == "check-environment":
        return module.main(["--check-environment", *args])
    if command in ("prepare-skeleton", "run-blender", "verify-skeleton", "review-pack"):
        return module.main(workspace=workspace)
    return module.main()
