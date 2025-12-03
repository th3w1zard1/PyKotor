#!/usr/bin/env python3
"""Install dependencies for BatchPatcher tool.

Python equivalent of deps_batchpatcher.ps1
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def get_os() -> str:
    """Get operating system name."""
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Darwin":
        return "Mac"
    elif system == "Linux":
        return "Linux"
    else:
        print(f"Error: Unknown operating system: {system}", file=sys.stderr)
        sys.exit(1)


def get_linux_distro() -> str | None:
    """Get Linux distribution name."""
    if not os.path.exists("/etc/os-release"):
        return None
    
    with open("/etc/os-release", encoding="utf-8") as f:
        content = f.read()
        for line in content.split("\n"):
            if line.startswith("ID="):
                distro = line.split("=", 1)[1].strip('"').strip("'")
                if distro == "ol":
                    return "oracle"
                return distro
    return None


def install_linux_packages(distro: str) -> None:
    """Install Linux packages based on distribution."""
    packages = {
        "debian": ["sudo", "apt-get", "update", "-y"],
        "ubuntu": ["sudo", "apt-get", "update", "-y"],
        "fedora": ["sudo", "dnf", "install", "-y"],
        "almalinux": ["sudo", "yum", "install", "-y"],
        "rocky": ["sudo", "yum", "install", "-y"],
        "alpine": ["sudo", "apk", "add", "--update"],
        "arch": ["sudo", "pacman", "-Sy", "--needed", "--noconfirm"],
        "manjaro": ["sudo", "pacman", "-Sy", "--needed", "--noconfirm"],
        "opensuse": ["sudo", "zypper", "install", "-y"],
    }
    
    pkg_map = {
        "debian": ["tcl8.6", "tk8.6", "tcl8.6-dev", "tk8.6-dev", "python3-tk", "python3-pip"],
        "ubuntu": ["tcl8.6", "tk8.6", "tcl8.6-dev", "tk8.6-dev", "python3-tk", "python3-pip"],
        "fedora": ["tk-devel", "tcl-devel", "python3-tkinter"],
        "almalinux": ["tk-devel", "tcl-devel", "python3-tkinter"],
        "rocky": ["tk-devel", "tcl-devel", "python3-tkinter"],
        "alpine": ["tcl", "tk", "python3-tkinter", "ttf-dejavu", "fontconfig"],
        "arch": ["tk", "tcl", "mpdecimal"],
        "manjaro": ["tk", "tcl", "mpdecimal"],
        "opensuse": ["tk-devel", "tcl-devel", "python3-tk"],
    }
    
    if distro not in packages:
        print(f"Warning: Distribution '{distro}' not recognized or not supported.")
        return
    
    cmd = packages[distro] + pkg_map.get(distro, [])
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Package installation failed: {e}", file=sys.stderr)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Install dependencies for BatchPatcher")
    parser.add_argument("--noprompt", action="store_true", help="Skip prompts")
    parser.add_argument("--venv-name", default=".venv", help="Virtual environment name")
    args = parser.parse_args()
    
    # Get script directory and root path
    script_path = Path(__file__).parent
    root_path = script_path.parent
    
    print(f"The path to the script directory is: {script_path}")
    print(f"The path to the root directory is: {root_path}")
    
    # Initialize Python virtual environment
    print("Initializing python virtual environment...")
    install_venv_script = root_path / "install_python_venv.ps1"
    if install_venv_script.exists():
        # Try to call the PowerShell script
        try:
            cmd = ["pwsh", "-File", str(install_venv_script)]
            if args.noprompt:
                cmd.append("-noprompt")
            cmd.extend(["-venv_name", args.venv_name])
            subprocess.run(cmd, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: Could not run install_python_venv.ps1. Make sure PowerShell is available.")
    else:
        print("Warning: install_python_venv.ps1 not found.")
    
    # Get Python executable path from environment or use python
    python_exe = os.environ.get("pythonExePath", "python")
    path_sep = os.pathsep
    
    os_name = get_os()
    if os_name == "Mac":
        # On Mac, tkinter should be handled by install_python_venv
        pass
    elif os_name == "Linux":
        distro = get_linux_distro()
        if distro:
            install_linux_packages(distro)
    
    print("Installing required packages to build the batchpatcher...")
    
    # Install packages
    pip_commands = [
        [python_exe, "-m", "pip", "install", "--upgrade", "pip", "--prefer-binary", "--progress-bar", "on"],
        [python_exe, "-m", "pip", "install", "pyinstaller", "--prefer-binary", "--progress-bar", "on"],
        [python_exe, "-m", "pip", "install", "-r", str(root_path / "Tools" / "BatchPatcher" / "requirements.txt"), "--prefer-binary", "--progress-bar", "on"],
        [python_exe, "-m", "pip", "install", "-r", str(root_path / "Libraries" / "PyKotor" / "requirements.txt"), "--prefer-binary", "--progress-bar", "on"],
        [python_exe, "-m", "pip", "install", "-r", str(root_path / "Libraries" / "PyKotor" / "recommended.txt"), "--prefer-binary", "--progress-bar", "on"],
        [python_exe, "-m", "pip", "install", "-r", str(root_path / "Libraries" / "PyKotorFont" / "requirements.txt"), "--prefer-binary", "--progress-bar", "on"],
    ]
    
    for cmd in pip_commands:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to run: {' '.join(cmd)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
