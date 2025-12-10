#!/usr/bin/env python3
"""Setup local GitHub Actions workflow support using act.

This script checks for and installs act (https://github.com/nektos/act) and verifies
Docker/Podman availability for running GitHub Actions workflows locally.

Examples:
    python scripts/setup_act_workflow.py
    python scripts/setup_act_workflow.py --check-only
    python scripts/setup_act_workflow.py --install-act --act-version 0.2.67
    python scripts/setup_act_workflow.py --prefer-podman
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Literal

# Act version to install if not specified
DEFAULT_ACT_VERSION = "0.2.67"


def get_platform_info() -> dict[str, str]:
    """Get platform-specific information."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map common machine architectures
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "armv7l": "armv7",
    }
    
    arch = arch_map.get(machine, machine)
    
    return {
        "system": system,
        "machine": machine,
        "arch": arch,
    }


def check_command(cmd: str | list[str], check_path: bool = True) -> tuple[bool, str | None]:
    """Check if a command is available.
    
    Args:
        cmd: Command name or list of command parts
        check_path: If True, also check if it's in PATH
        
    Returns:
        Tuple of (is_available, version_output_or_path)
    """
    if isinstance(cmd, str):
        cmd_list = [cmd, "--version"]
    else:
        cmd_list = cmd + ["--version"]
    
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Also check if it's in PATH
    if check_path:
        which_cmd = "where" if platform.system() == "Windows" else "which"
        try:
            result = subprocess.run(
                [which_cmd, cmd if isinstance(cmd, str) else cmd[0]],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                return True, path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return False, None


def check_docker() -> tuple[bool, str | None, str]:
    """Check for Docker availability (CLI or Desktop).
    
    Returns:
        Tuple of (is_available, version_or_path, runtime_type)
    """
    available, version = check_command("docker")
    if available:
        # Check if it's actually working (not just installed)
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, version, "docker"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return False, None, "none"


def check_podman() -> tuple[bool, str | None, str]:
    """Check for Podman availability (CLI or Desktop).
    
    Returns:
        Tuple of (is_available, version_or_path, runtime_type)
    """
    available, version = check_command("podman")
    if available:
        # Check if it's actually working (not just installed)
        try:
            result = subprocess.run(
                ["podman", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, version, "podman"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return False, None, "none"


def check_container_runtime(prefer_podman: bool = False) -> tuple[bool, str, str | None]:
    """Check for available container runtime (Docker or Podman).
    
    Args:
        prefer_podman: If True, check Podman first
        
    Returns:
        Tuple of (is_available, runtime_type, version_or_path)
    """
    if prefer_podman:
        podman_available, podman_version, _ = check_podman()
        if podman_available:
            return True, "podman", podman_version
        
        docker_available, docker_version, _ = check_docker()
        if docker_available:
            return True, "docker", docker_version
    else:
        docker_available, docker_version, _ = check_docker()
        if docker_available:
            return True, "docker", docker_version
        
        podman_available, podman_version, _ = check_podman()
        if podman_available:
            return True, "podman", podman_version
    
    return False, "none", None


def check_act() -> tuple[bool, str | None]:
    """Check if act is installed.
    
    Returns:
        Tuple of (is_installed, version_output)
    """
    return check_command("act")


def get_package_manager() -> str | None:
    """Detect available package manager on the system.
    
    Returns:
        Package manager name or None
    """
    managers = {
        "Windows": ["choco", "scoop", "winget"],
        "Linux": ["apt", "yum", "dnf", "pacman", "zypper"],
        "Darwin": ["brew"],
    }
    
    system = platform.system()
    for manager in managers.get(system, []):
        available, _ = check_command(manager, check_path=False)
        if available:
            return manager
    
    return None


def install_act_windows(version: str = DEFAULT_ACT_VERSION, install_dir: Path | None = None) -> bool:
    """Install act on Windows via direct download.
    
    Args:
        version: Act version to install
        install_dir: Directory to install act.exe to (defaults to ~/.local/bin)
        
    Returns:
        True if installation succeeded
    """
    if install_dir is None:
        install_dir = Path.home() / ".local" / "bin"
    
    install_dir.mkdir(parents=True, exist_ok=True)
    act_exe_path = install_dir / "act.exe"
    
    # Determine architecture
    platform_info = get_platform_info()
    arch = platform_info["arch"]
    
    # Act uses different naming for Windows
    if arch == "arm64":
        arch_name = "arm64"
    else:
        arch_name = "x86_64"
    
    url = f"https://github.com/nektos/act/releases/download/v{version}/act_Windows_{arch_name}.zip"
    
    print(f"Downloading act from: {url}")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "act.zip"
            
            # Download
            with urllib.request.urlopen(url, timeout=60) as response:
                with open(zip_path, "wb") as f:
                    shutil.copyfileobj(response, f)
            print(f"Downloaded to: {zip_path}")
            
            # Extract
            extract_dir = Path(tmpdir) / "act"
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find act.exe
            act_exe = next(extract_dir.rglob("act.exe"), None)
            if not act_exe:
                print("ERROR: act.exe not found in extracted archive")
                return False
            
            print(f"Found act.exe at: {act_exe}")
            
            # Copy to install directory
            shutil.copy2(act_exe, act_exe_path)
            print(f"Copied to: {act_exe_path}")
            
            # Verify installation
            try:
                result = subprocess.run(
                    [str(act_exe_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print(f"✓ act installed successfully!")
                    print(f"  Version: {result.stdout.strip()}")
                    print(f"  Location: {act_exe_path}")
                    print(f"\n  Note: Add {install_dir} to your PATH if not already present")
                    return True
            except Exception as e:
                print(f"WARNING: Installation may have succeeded but verification failed: {e}")
                return True  # Assume success if file was copied
            
    except Exception as e:
        print(f"ERROR: Failed to install act: {e}")
        return False
    
    return False


def install_act_linux(version: str = DEFAULT_ACT_VERSION, install_dir: Path | None = None) -> bool:
    """Install act on Linux via direct download.
    
    Args:
        version: Act version to install
        install_dir: Directory to install act to (defaults to ~/.local/bin)
        
    Returns:
        True if installation succeeded
    """
    if install_dir is None:
        install_dir = Path.home() / ".local" / "bin"
    
    install_dir.mkdir(parents=True, exist_ok=True)
    act_path = install_dir / "act"
    
    # Determine architecture
    platform_info = get_platform_info()
    arch = platform_info["arch"]
    
    # Map Linux architectures to act release names
    arch_map = {
        "x86_64": "x86_64",
        "arm64": "arm64",
        "armv7": "armv7",
    }
    arch_name = arch_map.get(arch, "x86_64")
    
    url = f"https://github.com/nektos/act/releases/download/v{version}/act_Linux_{arch_name}.tar.gz"
    
    print(f"Downloading act from: {url}")
    
    try:
        import tarfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = Path(tmpdir) / "act.tar.gz"
            
            # Download
            with urllib.request.urlopen(url, timeout=60) as response:
                with open(tar_path, "wb") as f:
                    shutil.copyfileobj(response, f)
            print(f"Downloaded to: {tar_path}")
            
            # Extract
            extract_dir = Path(tmpdir) / "act"
            extract_dir.mkdir()
            with tarfile.open(tar_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_dir)
            
            # Find act binary
            act_binary = next(extract_dir.rglob("act"), None)
            if not act_binary:
                print("ERROR: act binary not found in extracted archive")
                return False
            
            print(f"Found act at: {act_binary}")
            
            # Copy to install directory
            shutil.copy2(act_binary, act_path)
            
            # Make executable
            os.chmod(act_path, 0o755)
            print(f"Copied to: {act_path}")
            
            # Verify installation
            try:
                result = subprocess.run(
                    [str(act_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print(f"✓ act installed successfully!")
                    print(f"  Version: {result.stdout.strip()}")
                    print(f"  Location: {act_path}")
                    print(f"\n  Note: Add {install_dir} to your PATH if not already present")
                    return True
            except Exception as e:
                print(f"WARNING: Installation may have succeeded but verification failed: {e}")
                return True  # Assume success if file was copied
            
    except ImportError:
        print("ERROR: tarfile module not available (this shouldn't happen)")
        return False
    except Exception as e:
        print(f"ERROR: Failed to install act: {e}")
        return False
    
    return False


def install_act_macos(version: str = DEFAULT_ACT_VERSION, install_dir: Path | None = None) -> bool:
    """Install act on macOS via direct download.
    
    Args:
        version: Act version to install
        install_dir: Directory to install act to (defaults to ~/.local/bin)
        
    Returns:
        True if installation succeeded
    """
    if install_dir is None:
        install_dir = Path.home() / ".local" / "bin"
    
    install_dir.mkdir(parents=True, exist_ok=True)
    act_path = install_dir / "act"
    
    # Determine architecture
    platform_info = get_platform_info()
    arch = platform_info["arch"]
    
    # Map macOS architectures
    arch_map = {
        "x86_64": "x86_64",
        "arm64": "arm64",
    }
    arch_name = arch_map.get(arch, "x86_64")
    
    url = f"https://github.com/nektos/act/releases/download/v{version}/act_Darwin_{arch_name}.tar.gz"
    
    print(f"Downloading act from: {url}")
    
    try:
        import tarfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = Path(tmpdir) / "act.tar.gz"
            
            # Download
            with urllib.request.urlopen(url, timeout=60) as response:
                with open(tar_path, "wb") as f:
                    shutil.copyfileobj(response, f)
            print(f"Downloaded to: {tar_path}")
            
            # Extract
            extract_dir = Path(tmpdir) / "act"
            extract_dir.mkdir()
            with tarfile.open(tar_path, "r:gz") as tar_ref:
                tar_ref.extractall(extract_dir)
            
            # Find act binary
            act_binary = next(extract_dir.rglob("act"), None)
            if not act_binary:
                print("ERROR: act binary not found in extracted archive")
                return False
            
            print(f"Found act at: {act_binary}")
            
            # Copy to install directory
            shutil.copy2(act_binary, act_path)
            
            # Make executable
            os.chmod(act_path, 0o755)
            print(f"Copied to: {act_path}")
            
            # Verify installation
            try:
                result = subprocess.run(
                    [str(act_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print(f"✓ act installed successfully!")
                    print(f"  Version: {result.stdout.strip()}")
                    print(f"  Location: {act_path}")
                    print(f"\n  Note: Add {install_dir} to your PATH if not already present")
                    return True
            except Exception as e:
                print(f"WARNING: Installation may have succeeded but verification failed: {e}")
                return True  # Assume success if file was copied
            
    except ImportError:
        print("ERROR: tarfile module not available (this shouldn't happen)")
        return False
    except Exception as e:
        print(f"ERROR: Failed to install act: {e}")
        return False
    
    return False


def install_act(version: str = DEFAULT_ACT_VERSION, install_dir: Path | None = None) -> bool:
    """Install act on the current platform.
    
    Args:
        version: Act version to install
        install_dir: Directory to install act to
        
    Returns:
        True if installation succeeded
    """
    system = platform.system()
    
    if system == "Windows":
        return install_act_windows(version, install_dir)
    elif system == "Linux":
        return install_act_linux(version, install_dir)
    elif system == "Darwin":
        return install_act_macos(version, install_dir)
    else:
        print(f"ERROR: Unsupported platform: {system}")
        return False


def print_installation_instructions(platform_info: dict[str, str]) -> None:
    """Print platform-specific installation instructions for act."""
    system = platform_info["system"]
    package_manager = get_package_manager()
    
    print("\nInstallation options for act:")
    
    if system == "Windows":
        print("  On Windows, act can be installed via:")
        if package_manager == "choco":
            print("    - Chocolatey: choco install act-cli")
        elif package_manager == "scoop":
            print("    - Scoop: scoop install act")
        elif package_manager == "winget":
            print("    - Winget: winget install nektos.act-cli")
        else:
            print("    - Chocolatey: choco install act-cli")
            print("    - Scoop: scoop install act")
            print("    - Winget: winget install nektos.act-cli")
        print("    - Or download from: https://github.com/nektos/act/releases")
    elif system == "Linux":
        if package_manager:
            if package_manager == "apt":
                print(f"    - APT: sudo apt install act (if available in your repos)")
            elif package_manager == "yum" or package_manager == "dnf":
                print(f"    - {package_manager.upper()}: sudo {package_manager} install act (if available)")
            elif package_manager == "pacman":
                print("    - Pacman: sudo pacman -S act (if available in AUR)")
        print("    - Or download from: https://github.com/nektos/act/releases")
    elif system == "Darwin":
        if package_manager == "brew":
            print("    - Homebrew: brew install act")
        print("    - Or download from: https://github.com/nektos/act/releases")
    else:
        print("    - Download from: https://github.com/nektos/act/releases")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup local GitHub Actions workflow support using act",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
    Check for act and container runtime, print status

  %(prog)s --check-only
    Only check, don't attempt installation

  %(prog)s --install-act
    Check and install act if missing

  %(prog)s --install-act --act-version 0.2.67
    Install specific version of act

  %(prog)s --prefer-podman
    Prefer Podman over Docker for container runtime
        """,
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for act and container runtime, don't install",
    )
    parser.add_argument(
        "--install-act",
        action="store_true",
        help="Install act if not found",
    )
    parser.add_argument(
        "--act-version",
        default=DEFAULT_ACT_VERSION,
        help=f"Act version to install (default: {DEFAULT_ACT_VERSION})",
    )
    parser.add_argument(
        "--prefer-podman",
        action="store_true",
        help="Prefer Podman over Docker for container runtime",
    )
    parser.add_argument(
        "--install-dir",
        type=Path,
        help="Directory to install act to (default: ~/.local/bin)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    args = parser.parse_args()
    
    platform_info = get_platform_info()
    
    print("Checking for GitHub Actions local workflow support...")
    print(f"Platform: {platform_info['system']} ({platform_info['arch']})")
    print()
    
    # Check act
    act_available, act_version = check_act()
    if act_available:
        print(f"✓ act is installed")
        if act_version:
            print(f"  Version: {act_version}")
    else:
        print("✗ act is not installed")
        if not args.check_only:
            print_installation_instructions(platform_info)
            
            if args.install_act:
                print("\nAttempting to install act...")
                success = install_act(args.act_version, args.install_dir)
                if success:
                    act_available = True
                    # Re-check version
                    act_available, act_version = check_act()
                else:
                    print("\nPlease install act manually using one of the options above.")
                    return 1
            else:
                print("\nUse --install-act to automatically install act.")
    
    print()
    
    # Check container runtime
    runtime_available, runtime_type, runtime_version = check_container_runtime(args.prefer_podman)
    if runtime_available:
        print(f"✓ {runtime_type.capitalize()} is available")
        if runtime_version:
            print(f"  Version: {runtime_version}")
    else:
        print("✗ No container runtime found (Docker or Podman required)")
        print("\nact requires a container runtime to run workflows:")
        print("  - Docker Desktop: https://www.docker.com/products/docker-desktop")
        print("  - Docker Engine: https://docs.docker.com/engine/install/")
        print("  - Podman Desktop: https://podman-desktop.io/")
        print("  - Podman: https://podman.io/getting-started/installation")
        
        if not act_available:
            return 1
    
    print()
    
    # Summary
    if act_available and runtime_available:
        print("✓ Setup complete! You can now run GitHub Actions workflows locally with act.")
        print(f"\nExample usage:")
        print(f"  act -l                    # List workflows")
        print(f"  act push                  # Run workflow on push event")
        print(f"  act pull_request          # Run workflow on pull_request event")
        if runtime_type == "podman":
            print(f"\nNote: Using Podman. You may need to set ACT_EXPERIMENTAL=1")
        return 0
    else:
        print("✗ Setup incomplete. Please install missing components above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

