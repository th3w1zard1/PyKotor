#!/usr/bin/env python3
"""Generic PyInstaller build helper for any tool under the repository.

This script centralizes the compile logic used by the per-tool wrappers so the
wrappers only need to pass configuration (paths, entrypoints, excludes, etc.).
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def detect_os() -> str:
    system = platform.system()
    if system == "Windows":
        return "Windows"
    if system == "Darwin":
        return "Mac"
    if system == "Linux":
        return "Linux"
    raise SystemExit(f"Unsupported OS: {system}")


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=cwd, env=env)


def install_venv(repo_root: Path, venv_name: str, noprompt: bool) -> None:
    installer = repo_root / "install_python_venv.ps1"
    if not installer.exists():
        raise SystemExit(f"install_python_venv.ps1 not found at {installer}")

    args = ["pwsh", "-File", str(installer)]
    if noprompt:
        args.append("-noprompt")
    args.extend(["-venv_name", venv_name])
    run(args)


def path_separator_for_data(os_name: str) -> str:
    return ";" if os_name == "Windows" else ":"


def add_flag_values(flag: str, values: Iterable[str], buffer: list[str]) -> None:
    for value in values:
        buffer.append(f"--{flag}={value}")


def compute_final_executable(distpath: Path, name: str, os_name: str) -> Path:
    extension = "exe" if os_name == "Windows" else ("app" if os_name == "Mac" else "")
    if extension:
        return distpath / f"{name}.{extension}"
    return distpath / name


def normalize_add_data(entries: Iterable[str], sep: str) -> list[str]:
    normalized: list[str] = []
    for entry in entries:
        if ":" not in entry and sep == ":":
            raise SystemExit(f"--add-data entry '{entry}' missing destination (use src{sep}dest)")
        if ";" not in entry and sep == ";" and ":" not in entry:
            raise SystemExit(f"--add-data entry '{entry}' missing destination (use src{sep}dest)")
        normalized.append(entry)
    return normalized


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Generic PyInstaller compiler for repository tools")
    parser.add_argument("--tool-path", required=True, help="Path to the tool directory (e.g., Tools/HoloPatcher)")
    parser.add_argument("--src-dir", help="Override src directory (defaults to <tool-path>/src)")
    parser.add_argument("--entrypoint", help="Relative path from src to __main__ (defaults to <slug>/__main__.py)")
    parser.add_argument("--name", help="PyInstaller --name (defaults to tool directory name)")
    parser.add_argument("--distpath", help="Output directory (defaults to <repo>/dist)")
    parser.add_argument("--workpath", help="PyInstaller workpath (defaults to <src>/build)")
    parser.add_argument("--icon", help="Icon path passed to PyInstaller")
    parser.add_argument("--hidden-import", action="append", default=[], help="Repeatable hidden imports")
    parser.add_argument("--exclude-module", action="append", default=[], help="Repeatable exclusions")
    parser.add_argument("--upx-exclude", action="append", default=[], help="Repeatable UPX exclusions")
    parser.add_argument("--add-data", action="append", default=[], help="Repeatable --add-data entries (src{sep}dest)")
    parser.add_argument("--add-data-if-exists", action="append", default=[], help="Optional --add-data entries only if src exists")
    parser.add_argument("--extra-path", action="append", default=[], help="Additional --path entries for PyInstaller")
    parser.add_argument("--inherit-pythonpath", action="store_true", default=True, help="Include PYTHONPATH entries")
    parser.add_argument("--no-inherit-pythonpath", dest="inherit_pythonpath", action="store_false")
    parser.add_argument("--include-library-src", action="store_true", default=True, help="Include all Libraries/*/src paths when present")
    parser.add_argument("--no-include-library-src", dest="include_library_src", action="store_false")
    parser.add_argument("--include-wiki-if-present", action="store_true", help="Bundle wiki directory if it exists")
    parser.add_argument("--wiki-dest", default="wiki", help="Destination folder name for wiki add-data")
    parser.add_argument("--clean", action="store_true", default=True, help="Enable PyInstaller --clean and remove workpath")
    parser.add_argument("--no-clean", dest="clean", action="store_false")
    parser.add_argument("--onefile", action="store_true", default=True)
    parser.add_argument("--no-onefile", dest="onefile", action="store_false")
    parser.add_argument("--noconfirm", action="store_true", default=True)
    parser.add_argument("--no-noconfirm", dest="noconfirm", action="store_false")
    parser.add_argument("--windowed", action="store_true", help="Use windowed mode")
    parser.add_argument("--console", action="store_true", help="Force console mode")
    parser.add_argument("--debug", help="Debug setting for PyInstaller")
    parser.add_argument("--log-level", help="Log level for PyInstaller")
    parser.add_argument("--upx-dir", help="Path to UPX binary")
    parser.add_argument("--qt-api", help="Normalize QT_API environment variable and exclude other bindings")
    parser.add_argument("--exclude-other-qt", action="store_true", default=False, help="Exclude other Qt bindings when qt-api is set")
    parser.add_argument("--preinstall-playwright", action="store_true", help="Run 'playwright install' before building")
    parser.add_argument("--playwright-browser", action="append", default=["chromium"], help="Browsers to install with playwright")
    parser.add_argument("--pre-pip", action="append", default=[], help="Packages to pip install before running PyInstaller")
    parser.add_argument("--venv-name", default=".venv", help="Virtual environment name")
    parser.add_argument("--skip-venv", action="store_true", help="Skip install_python_venv.ps1 invocation")
    parser.add_argument("--noprompt", action="store_true", help="Skip prompts in install_python_venv.ps1")
    parser.add_argument("--python-exe", default=os.environ.get("pythonExePath", "python"), help="Python executable to use")
    parser.add_argument("--remove-previous", action="store_true", default=True, help="Remove prior dist artifacts for this tool")
    parser.add_argument("--no-remove-previous", dest="remove_previous", action="store_false")
    args = parser.parse_args()

    os_name = detect_os()
    tool_path = (repo_root / args.tool_path).resolve() if not Path(args.tool_path).is_absolute() else Path(args.tool_path)
    src_dir = Path(args.src_dir) if args.src_dir else tool_path / "src"
    if not src_dir.exists():
        raise SystemExit(f"src directory not found: {src_dir}")

    name = args.name or Path(tool_path).name
    distpath = Path(args.distpath) if args.distpath else repo_root / "dist"
    workpath = Path(args.workpath) if args.workpath else src_dir / "build"

    entrypoint = args.entrypoint
    if not entrypoint:
        slug = Path(tool_path).name.lower()
        entrypoint = f"{slug}/__main__.py"

    data_sep = path_separator_for_data(os_name)

    # Prepare environment
    env = os.environ.copy()
    if args.qt_api:
        env["QT_API"] = args.qt_api
    if args.exclude_other_qt and args.qt_api:
        normalized_api = args.qt_api
        all_bindings = {"PyQt5", "PyQt6", "PySide2", "PySide6"}
        other_bindings = sorted(api for api in all_bindings if api != normalized_api)
        args.exclude_module.extend(other_bindings)

    if not args.skip_venv:
        install_venv(repo_root, args.venv_name, args.noprompt)

    if args.pre_pip:
        run([args.python_exe, "-m", "pip", "install", *args.pre_pip, "--prefer-binary", "--progress-bar", "on"])

    if args.preinstall_playwright:
        env["PLAYWRIGHT_BROWSERS_PATH"] = env.get("PLAYWRIGHT_BROWSERS_PATH", "0")
        for browser in args.playwright_browser:
            run([args.python_exe, "-m", "playwright", "install", browser])

    # Collect PyInstaller args
    pyinstaller_args: list[str] = []
    if args.clean:
        pyinstaller_args.append("--clean")
    if args.onefile:
        pyinstaller_args.append("--onefile")
    if args.noconfirm:
        pyinstaller_args.append("--noconfirm")
    if args.windowed and not args.console:
        pyinstaller_args.append("--windowed")
    if args.console and not args.windowed:
        pyinstaller_args.append("--console")
    if args.debug:
        pyinstaller_args.append(f"--debug={args.debug}")
    if args.log_level:
        pyinstaller_args.append(f"--log-level={args.log_level}")
    if args.icon:
        pyinstaller_args.append(f"--icon={args.icon}")
    pyinstaller_args.append(f"--name={name}")
    pyinstaller_args.append(f"--distpath={distpath}")
    pyinstaller_args.append(f"--workpath={workpath}")
    if args.upx_dir:
        pyinstaller_args.append(f"--upx-dir={args.upx_dir}")

    add_flag_values("hidden-import", args.hidden_import, pyinstaller_args)
    add_flag_values("exclude-module", args.exclude_module, pyinstaller_args)
    add_flag_values("upx-exclude", args.upx_exclude, pyinstaller_args)

    add_data_entries: list[str] = list(args.add_data)
    for candidate in args.add_data_if_exists:
        src, _, dest = candidate.partition(data_sep)
        if not src:
            continue
        if Path(src).expanduser().exists():
            add_data_entries.append(candidate)

    if args.include_wiki_if_present:
        wiki_dir = repo_root / "wiki"
        if wiki_dir.exists():
            add_data_entries.append(f"{wiki_dir}{data_sep}{args.wiki_dest}")

    normalized_data = normalize_add_data(add_data_entries, data_sep)
    add_flag_values("add-data", normalized_data, pyinstaller_args)

    paths: List[str] = []
    if args.include_library_src:
        libraries_dir = repo_root / "Libraries"
        if libraries_dir.exists():
            for child in libraries_dir.iterdir():
                candidate = child / "src"
                if candidate.exists():
                    paths.append(str(candidate))
    paths.extend(args.extra_path)
    if args.inherit_pythonpath:
        paths.extend([p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p])

    add_flag_values("path", paths, pyinstaller_args)

    entry_arg = str(Path(entrypoint))
    pyinstaller_args.append(entry_arg)

    final_executable = compute_final_executable(distpath, name, os_name)
    if args.remove_previous:
        if final_executable.exists():
            if final_executable.is_dir():
                shutil.rmtree(final_executable)
            else:
                final_executable.unlink()
        alt_dir = distpath / name
        if alt_dir.exists():
            shutil.rmtree(alt_dir)

        if args.clean and workpath.exists():
            shutil.rmtree(workpath)

    cmd = [args.python_exe, "-m", "PyInstaller"] + pyinstaller_args
    print("Executing:", " ".join(cmd))
    run(cmd, cwd=src_dir, env=env)

    if not final_executable.exists():
        raise SystemExit(f"Build failed, expected output missing: {final_executable}")
    print(f"Built executable at: {final_executable}")


if __name__ == "__main__":
    main()

