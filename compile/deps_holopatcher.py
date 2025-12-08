#!/usr/bin/env python3
"""Compatibility wrapper that delegates to deps_tool.py with HoloPatcher config."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--noprompt", action="store_true")
    parser.add_argument("--venv-name", default=".venv")
    args = parser.parse_args()

    script_path = Path(__file__).parent
    root_path = script_path.parent
    tool_path = root_path / "Tools" / "HoloPatcher"
    deps_tool = script_path / "deps_tool.py"

    cmd = [
        os.environ.get("pythonExePath", sys.executable),
        str(deps_tool),
        "--tool-path",
        str(tool_path),
        "--venv-name",
        args.venv_name,
        "--linux-package-profile",
        "tk",
        "--pip-requirements",
        str(root_path / "Libraries" / "PyKotor" / "requirements.txt"),
    ]
    if args.noprompt:
        cmd.append("--noprompt")

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
