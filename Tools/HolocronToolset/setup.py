"""Custom setup.py to handle wiki directory inclusion for PyPI distribution.

This file extends setuptools to copy the wiki directory from the repo root
into the package during the build process, ensuring it's included in PyPI distributions.

Note: When using setuptools.build_meta (pyproject.toml), this file is automatically
detected and used for custom build commands.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


class BuildPyWithWiki(build_py):
    """Custom build_py that copies wiki directory before building."""

    def run(self):
        """Copy wiki directory to package before building (idempotent)."""
        # Get paths
        setup_dir = Path(__file__).parent
        repo_root = setup_dir.parent.parent
        wiki_src = repo_root / "wiki"
        wiki_dest = setup_dir / "src" / "toolset" / "wiki"

        # Copy wiki if it exists (idempotent: removes existing first)
        if wiki_src.exists() and wiki_src.is_dir():
            if wiki_dest.exists():
                shutil.rmtree(wiki_dest)
            shutil.copytree(wiki_src, wiki_dest, dirs_exist_ok=True)
            print(f"Copied wiki directory from {wiki_src} to {wiki_dest}")

        # Run standard build
        super().run()


class SDistWithWiki(sdist):
    """Custom sdist that ensures wiki is included in source distribution."""

    def run(self):
        """Copy wiki directory before processing MANIFEST.in (which happens in super().run())."""
        # Get paths
        setup_dir = Path(__file__).parent
        repo_root = setup_dir.parent.parent
        wiki_src = repo_root / "wiki"
        wiki_dest = setup_dir / "src" / "toolset" / "wiki"

        # Copy wiki to src/toolset/wiki if it exists (idempotent: removes existing first)
        # This must happen BEFORE super().run() so MANIFEST.in can find the files
        if wiki_src.exists() and wiki_src.is_dir():
            if wiki_dest.exists():
                shutil.rmtree(wiki_dest)
            shutil.copytree(wiki_src, wiki_dest, dirs_exist_ok=True)
            print(f"Copied wiki directory from {wiki_src} to {wiki_dest} for sdist")

        # Run standard sdist (processes MANIFEST.in, which will now find src/toolset/wiki)
        super().run()

    def make_release_tree(self, base_dir: str, files: list[str]) -> None:
        """Ensure wiki is also copied to build directory for source distribution."""
        # Get paths
        setup_dir = Path(__file__).parent
        repo_root = setup_dir.parent.parent
        wiki_src = repo_root / "wiki"

        # Copy wiki to build directory if it exists (idempotent: removes existing first)
        if wiki_src.exists() and wiki_src.is_dir():
            build_wiki = Path(base_dir) / "wiki"
            if build_wiki.exists():
                shutil.rmtree(build_wiki)
            shutil.copytree(wiki_src, build_wiki, dirs_exist_ok=True)
            print(f"Copied wiki directory to source distribution: {build_wiki}")

        # Run standard sdist
        super().make_release_tree(base_dir, files)


# Setup configuration is read from pyproject.toml
# This file provides custom build commands
if __name__ == "__main__":
    setup(
        cmdclass={
            "build_py": BuildPyWithWiki,
            "sdist": SDistWithWiki,
        }
    )
