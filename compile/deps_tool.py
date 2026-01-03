#!/usr/bin/env python3
"""Generic dependency installer for tools.

Centralizes the per-tool dependency logic; callers provide configuration flags
for requirements, Qt/Tk system packages, and optional extras.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys

from pathlib import Path
from typing import Iterable


def detect_os() -> str:
    system = platform.system()
    if system == "Windows":
        return "Windows"
    if system == "Darwin":
        return "Mac"
    if system == "Linux":
        return "Linux"
    raise SystemExit(f"Unsupported OS: {system}")


def detect_linux_distro() -> str | None:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return None
    content = os_release.read_text(encoding="utf-8").splitlines()
    for line in content:
        if line.startswith("ID="):
            distro = line.split("=", 1)[1].strip('"').strip("'")
            return "oracle" if distro == "ol" else distro
    return None


def run(cmd: list[str], allow_fail: bool = False) -> None:
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if allow_fail:
            return
        raise


LINUX_PACKAGE_PROFILES: dict[str, dict[str, list[str]]] = {
    "tk": {
        "debian": ["tcl8.6", "tk8.6", "tcl8.6-dev", "tk8.6-dev", "python3-tk", "python3-pip"],
        "ubuntu": ["tcl8.6", "tk8.6", "tcl8.6-dev", "tk8.6-dev", "python3-tk", "python3-pip"],
        "fedora": ["tk-devel", "tcl-devel", "python3-tkinter"],
        "almalinux": ["tk-devel", "tcl-devel", "python3-tkinter"],
        "rocky": ["tk-devel", "tcl-devel", "python3-tkinter"],
        "alpine": ["tcl", "tk", "python3-tkinter", "ttf-dejavu", "fontconfig"],
        "arch": ["tk", "tcl", "mpdecimal"],
        "manjaro": ["tk", "tcl", "mpdecimal"],
        "opensuse": ["tk-devel", "tcl-devel", "python3-tk"],
    },
    "qt_gui": {
        "debian": [
            "libicu-dev",
            "libunwind-dev",
            "libwebp-dev",
            "liblzma-dev",
            "libjpeg-dev",
            "libtiff-dev",
            "libquadmath0",
            "libgfortran5",
            "libopenblas-dev",
            "libxau-dev",
            "libxcb1-dev",
            "python3-opengl",
            "python3-pyqt5",
            "libpulse-mainloop-glib0",
            "libgstreamer-plugins-base1.0-dev",
            "gstreamer1.0-plugins-base",
            "gstreamer1.0-plugins-good",
            "gstreamer1.0-plugins-bad",
            "gstreamer1.0-plugins-ugly",
            "libgstreamer1.0-dev",
            "mesa-utils",
            "libgl1-mesa-glx",
            "libgl1-mesa-dri",
            "qtbase5-dev",
            "qtchooser",
            "qt5-qmake",
            "qtbase5-dev-tools",
            "libglu1-mesa",
            "libglu1-mesa-dev",
            "libqt5gui5",
            "libqt5core5a",
            "libqt5dbus5",
            "libqt5widgets5",
        ],
        "ubuntu": [
            "libicu-dev",
            "libunwind-dev",
            "libwebp-dev",
            "liblzma-dev",
            "libjpeg-dev",
            "libtiff-dev",
            "libquadmath0",
            "libgfortran5",
            "libopenblas-dev",
            "libxau-dev",
            "libxcb1-dev",
            "python3-opengl",
            "python3-pyqt5",
            "libpulse-mainloop-glib0",
            "libgstreamer-plugins-base1.0-dev",
            "gstreamer1.0-plugins-base",
            "gstreamer1.0-plugins-good",
            "gstreamer1.0-plugins-bad",
            "gstreamer1.0-plugins-ugly",
            "libgstreamer1.0-dev",
            "mesa-utils",
            "libgl1-mesa-glx",
            "libgl1-mesa-dri",
            "qtbase5-dev",
            "qtchooser",
            "qt5-qmake",
            "qtbase5-dev-tools",
            "libglu1-mesa",
            "libglu1-mesa-dev",
            "libqt5gui5",
            "libqt5core5a",
            "libqt5dbus5",
            "libqt5widgets5",
        ],
        "fedora": [
            "binutils",
            "libnsl",
            "mesa-libGL-devel",
            "python3-pyopengl",
            "PyQt5",
            "pulseaudio-libs-glib2",
            "gstreamer1-plugins-base",
            "gstreamer1-plugins-good",
            "gstreamer1-plugins-bad-free",
            "gstreamer1-plugins-ugly-free",
            "gstreamer1-devel",
        ],
        "oracle": [
            "binutils",
            "PyQt5",
            "mesa-libGL-devel",
            "pulseaudio-libs-glib2",
            "gstreamer1-plugins-base",
            "gstreamer1-plugins-good",
            "gstreamer1-plugins-bad-free",
            "gstreamer1-plugins-ugly-free",
            "gstreamer1-devel",
        ],
        "almalinux": [
            "binutils",
            "libnsl",
            "libglvnd-opengl",
            "python3-qt5",
            "python3-pyqt5-sip",
            "pulseaudio-libs-glib2",
            "pulseaudio-libs-devel",
            "gstreamer1-plugins-base",
            "gstreamer1-plugins-good",
            "gstreamer1-plugins-bad-free",
            "mesa-libGLw",
            "libX11",
            "mesa-dri-drivers",
            "mesa-libGL",
            "mesa-libglapi",
        ],
        "alpine": [
            "binutils",
            "gstreamer",
            "gstreamer-dev",
            "gst-plugins-bad-dev",
            "gst-plugins-base-dev",
            "pulseaudio-qt",
            "pulseaudio",
            "pulseaudio-alsa",
            "py3-opengl",
            "qt5-qtbase-x11",
            "qt5-qtbase-dev",
            "mesa-gl",
            "mesa-glapi",
            "qt5-qtbase-x11",
            "libx11",
            "ttf-dejavu",
            "fontconfig",
        ],
        "arch": [
            "mesa",
            "libxcb",
            "qt5-base",
            "qt5-wayland",
            "xcb-util-wm",
            "xcb-util-keysyms",
            "xcb-util-image",
            "xcb-util-renderutil",
            "python-opengl",
            "libxcomposite",
            "gtk3",
            "atk",
            "mpdecimal",
            "python-pyqt5",
            "qt5-base",
            "qt5-multimedia",
            "qt5-svg",
            "pulseaudio",
            "pulseaudio-alsa",
            "gstreamer",
            "mesa",
            "libglvnd",
            "ttf-dejavu",
            "fontconfig",
            "gst-plugins-base",
            "gst-plugins-good",
            "gst-plugins-bad",
            "gst-plugins-ugly",
        ],
    },
}


def install_linux_profile(profile: str, distro: str) -> None:
    packages = LINUX_PACKAGE_PROFILES.get(profile, {}).get(distro)
    if not packages:
        print(f"Warning: No package profile '{profile}' for distro '{distro}'")
        return
    print(f"Installing Linux packages for profile '{profile}' on {distro}: {', '.join(packages)}")
    if distro in ("debian", "ubuntu"):
        run(["sudo", "apt-get", "update", "-y"], allow_fail=True)
        run(["sudo", "apt-get", "install", "-y", *packages])
    elif distro == "fedora":
        run(["sudo", "dnf", "install", "-y", *packages])
    elif distro in ("almalinux", "oracle", "rocky"):
        run(["sudo", "yum", "install", "-y", *packages])
    elif distro == "alpine":
        run(["sudo", "apk", "add", "--update", *packages])
    elif distro in ("arch", "manjaro"):
        run(["sudo", "pacman", "-Sy", "--needed", "--noconfirm", *packages])
    elif distro == "opensuse":
        run(["sudo", "zypper", "install", "-y", *packages])
    else:
        print(f"Warning: Distro '{distro}' not handled for profile '{profile}'")


def install_brew_packages(packages: Iterable[str]) -> None:
    for package in packages:
        run(["brew", "install", package], allow_fail=True)


def install_qt_binding(python_exe: str, qt_api: str | None) -> None:
    if not qt_api:
        return
    run([python_exe, "-m", "pip", "install", "-U", qt_api, "--prefer-binary", "--progress-bar", "on"])
    run([python_exe, "-m", "pip", "install", "-U", "qtpy", "--prefer-binary", "--progress-bar", "on"])


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Generic dependency installer for repository tools")
    parser.add_argument("--tool-path", required=True, help="Path to the tool directory (e.g., Tools/HoloPatcher)")
    parser.add_argument("--venv-name", default=".venv", help="Virtual environment name")
    parser.add_argument("--noprompt", action="store_true", help="Skip prompts in install_python_venv.ps1")
    parser.add_argument("--pip-upgrade", action="store_true", default=True, help="Upgrade pip before installs")
    parser.add_argument("--no-pip-upgrade", dest="pip_upgrade", action="store_false")
    parser.add_argument("--pip-install-pyinstaller", default="pyinstaller", help="Specifier for PyInstaller")
    parser.add_argument("--pypy-pyinstaller-spec", help="Override PyInstaller spec when running under PyPy")
    parser.add_argument("--cpython-pyinstaller-spec", help="Override PyInstaller spec when running under CPython")
    parser.add_argument("--pip-requirements", action="append", default=[], help="Requirements files to install")
    parser.add_argument("--pip-package", action="append", default=[], help="Extra pip packages to install")
    parser.add_argument("--windows-extra-pip", action="append", default=[], help="Windows-only pip packages")
    parser.add_argument("--windows-cpython-pip", action="append", default=[], help="Windows-only pip packages for CPython")
    parser.add_argument("--windows-pypy-pip", action="append", default=[], help="Windows-only pip packages for PyPy")
    parser.add_argument("--linux-package-profile", action="append", default=[], help="Linux package profile(s) to install")
    parser.add_argument("--brew-package", action="append", default=[], help="Homebrew packages to install on macOS")
    parser.add_argument("--qt-api", help="Qt binding to install (PyQt5/PyQt6/PySide2/PySide6)")
    parser.add_argument("--qt-install-using-brew", action="store_true", help="Install Qt via Homebrew when on macOS")
    parser.add_argument("--playwright-browser", action="append", default=[], help="Browsers to install via playwright")
    parser.add_argument("--python-exe", default=os.environ.get("pythonExePath", "python"), help="Python executable to use")
    parser.add_argument("--skip-venv", action="store_true", help="Skip running install_python_venv.ps1")
    args = parser.parse_args()

    tool_path = (repo_root / args.tool_path).resolve() if not Path(args.tool_path).is_absolute() else Path(args.tool_path)
    requirements = list(args.pip_requirements)
    default_requirements = tool_path / "requirements.txt"
    if default_requirements.exists():
        requirements.append(str(default_requirements))

    python_exe = args.python_exe
    python_impl = subprocess.check_output([python_exe, "-c", "import platform; print(platform.python_implementation())"], text=True).strip()
    os_name = detect_os()

    if not args.skip_venv:
        installer = repo_root / "install_python_venv.ps1"
        if not installer.exists():
            raise SystemExit(f"install_python_venv.ps1 not found at {installer}")
        install_cmd = ["pwsh", "-File", str(installer)]
        if args.noprompt:
            install_cmd.append("-noprompt")
        install_cmd.extend(["-venv_name", args.venv_name])
        run(install_cmd)

    if args.pip_upgrade:
        run([python_exe, "-m", "pip", "install", "--upgrade", "pip", "--prefer-binary", "--progress-bar", "on"])

    if args.pip_install_pyinstaller:
        spec = args.pip_install_pyinstaller
        if python_impl == "PyPy" and args.pypy_pyinstaller_spec:
            spec = args.pypy_pyinstaller_spec
        elif python_impl == "CPython" and args.cpython_pyinstaller_spec:
            spec = args.cpython_pyinstaller_spec
        run([python_exe, "-m", "pip", "install", spec, "--prefer-binary", "--progress-bar", "on"])

    for req in requirements:
        run([python_exe, "-m", "pip", "install", "-r", req, "--prefer-binary", "--compile", "--progress-bar", "on"])

    if args.pip_package:
        run([python_exe, "-m", "pip", "install", *args.pip_package, "--prefer-binary", "--progress-bar", "on"])

    if args.playwright_browser:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "0")
        for browser in args.playwright_browser:
            run([python_exe, "-m", "playwright", "install", browser])

    if os_name == "Mac":
        if args.qt_install_using_brew:
            install_brew_packages(["qt@5", "qt@6"])
        if args.brew_package:
            install_brew_packages(args.brew_package)
    elif os_name == "Linux":
        distro = detect_linux_distro()
        if distro:
            for profile in args.linux_package_profile:
                install_linux_profile(profile, distro)
    elif os_name == "Windows":
        if args.windows_extra_pip:
            run([python_exe, "-m", "pip", "install", *args.windows_extra_pip, "--prefer-binary", "--progress-bar", "on"])
        if python_impl == "CPython" and args.windows_cpython_pip:
            run([python_exe, "-m", "pip", "install", *args.windows_cpython_pip, "--prefer-binary", "--progress-bar", "on"])
        if python_impl == "PyPy" and args.windows_pypy_pip:
            run([python_exe, "-m", "pip", "install", *args.windows_pypy_pip, "--prefer-binary", "--progress-bar", "on"])

    install_qt_binding(python_exe, args.qt_api)


if __name__ == "__main__":
    main()
