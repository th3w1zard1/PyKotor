#!/usr/bin/env python3
"""Test script to verify the filename conflict resolution logic."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from pykotor.extract.file import ResourceIdentifier, ResourceType


class MockFileResource:
    def __init__(
        self,
        resname: str,
        restype: ResourceType,
    ):
        self._identifier = ResourceIdentifier(resname=resname, restype=restype)

    def identifier(self) -> ResourceIdentifier:
        return self._identifier

    def restype(self) -> ResourceType:
        return self._identifier.restype


class MockUI:
    def __init__(
        self,
        tpc_decompile: bool = False,
        tpc_txi: bool = False,
        mdl_decompile: bool = False,
        mdl_textures: bool = False,
    ):
        self.tpc_decompile_checkbox_checked: bool = tpc_decompile
        self.tpc_txi_checkbox_checked: bool = tpc_txi
        self.mdl_decompile_checkbox_checked: bool = mdl_decompile
        self.mdl_textures_checkbox_checked: bool = mdl_textures

    def tpcDecompileCheckbox(self):
        return self

    def isChecked(self):
        return self.tpc_decompile_checkbox_checked

    def tpcTxiCheckbox(self):
        return self

    def mdlDecompileCheckbox(self):
        return self

    def mdlTexturesCheckbox(self):
        return self


def build_extract_save_paths_test(
    resources: list[MockFileResource],
    ui: MockUI,
    folder_path: Path,
) -> tuple[Path, dict[MockFileResource, Path]]:
    """Test version of build_extract_save_paths logic."""
    paths_to_write: dict[MockFileResource, Path] = {}

    # Track all potential output filenames to detect conflicts
    used_filenames: set[str] = set()
    resource_conflict_counts: dict[str, int] = defaultdict(int)

    for resource in resources:
        identifier: ResourceIdentifier = resource.identifier()
        base_name: str = identifier.resname
        base_path: Path = folder_path / base_name

        # Determine the main file save path based on UI checks
        main_save_path: Path = base_path
        if resource.restype() is ResourceType.TPC and ui.tpcDecompileCheckbox().isChecked():
            main_save_path = main_save_path.with_suffix(".tga")
        elif resource.restype() is ResourceType.MDL and ui.mdlDecompileCheckbox().isChecked():
            main_save_path = main_save_path.with_suffix(".mdl.ascii")
        else:
            main_save_path = main_save_path.with_suffix(f".{identifier.restype.extension}")

        # Check for conflicts with the main file and adjust if necessary
        main_filename: str = main_save_path.name
        if main_filename in used_filenames:
            # Increment conflict count for this base name
            conflict_count: int = resource_conflict_counts[base_name] + 1
            resource_conflict_counts[base_name] = conflict_count

            # Create unique filename by appending suffix
            stem = main_save_path.stem
            suffix = main_save_path.suffix
            main_save_path = main_save_path.with_name(f"{stem}_{conflict_count}{suffix}")

        used_filenames.add(main_save_path.name)

        # For TPC resources, also check TXI file conflicts if that option is enabled
        if resource.restype() is ResourceType.TPC and ui.tpcTxiCheckbox().isChecked():
            txi_path: Path = main_save_path.with_suffix(".txi")
            txi_filename: str = txi_path.name
            if txi_filename in used_filenames:
                # Use the same conflict resolution as the main file
                conflict_count = resource_conflict_counts[base_name]
                if conflict_count > 0:
                    stem = txi_path.stem
                    txi_path = txi_path.with_name(f"{stem}_{conflict_count}.txi")

            used_filenames.add(txi_path.name)

        # For MDL resources, check potential texture subfolder conflicts if texture extraction is enabled
        if resource.restype() is ResourceType.MDL and ui.mdlTexturesCheckbox().isChecked():
            model_subfolder_name: str = f"model_{base_name}"
            if model_subfolder_name in used_filenames:
                conflict_count = resource_conflict_counts[base_name]
                if conflict_count > 0:
                    model_subfolder_name = f"model_{base_name}_{conflict_count}"

            used_filenames.add(model_subfolder_name)

        paths_to_write[resource] = main_save_path

    return folder_path, paths_to_write


def test_conflict_resolution():
    """Test various conflict scenarios."""
    print("Testing filename conflict resolution...")

    # Test case 1: Two TPC files with same name, TXI extraction enabled
    print("\n=== Test Case 1: TPC files with TXI extraction ===")
    resources = [
        MockFileResource("texture", ResourceType.TPC),
        MockFileResource("texture", ResourceType.TPC),
    ]
    ui = MockUI(tpc_decompile=True, tpc_txi=True)
    folder_path = Path("/test")

    _, paths = build_extract_save_paths_test(resources, ui, folder_path)
    print("Resources:")
    for i, (res, path) in enumerate(paths.items()):
        print(f"  {i + 1}. {res.identifier()} -> {path}")

    # Test case 2: Two MDL files with same name, texture extraction enabled
    print("\n=== Test Case 2: MDL files with texture extraction ===")
    resources = [
        MockFileResource("model", ResourceType.MDL),
        MockFileResource("model", ResourceType.MDL),
    ]
    ui = MockUI(mdl_decompile=True, mdl_textures=True)

    _, paths = build_extract_save_paths_test(resources, ui, folder_path)
    print("Resources:")
    for i, (res, path) in enumerate(paths.items()):
        print(f"  {i + 1}. {res.identifier()} -> {path}")

    # Test case 3: Mixed resources with same base names
    print("\n=== Test Case 3: Mixed resources with conflicts ===")
    resources = [
        MockFileResource("shared", ResourceType.TPC),
        MockFileResource("shared", ResourceType.MDL),
        MockFileResource("shared", ResourceType.TPC),
    ]
    ui = MockUI(tpc_decompile=True, tpc_txi=True, mdl_decompile=True, mdl_textures=True)

    _, paths = build_extract_save_paths_test(resources, ui, folder_path)
    print("Resources:")
    for i, (res, path) in enumerate(paths.items()):
        print(f"  {i + 1}. {res.identifier()} -> {path}")

    # Test case 4: No conflicts
    print("\n=== Test Case 4: No conflicts ===")
    resources = [
        MockFileResource("unique1", ResourceType.TPC),
        MockFileResource("unique2", ResourceType.MDL),
    ]
    ui = MockUI(tpc_decompile=True, tpc_txi=True, mdl_decompile=True, mdl_textures=True)

    _, paths = build_extract_save_paths_test(resources, ui, folder_path)
    print("Resources:")
    for i, (res, path) in enumerate(paths.items()):
        print(f"  {i + 1}. {res.identifier()} -> {path}")

    print("\nTest completed!")


if __name__ == "__main__":
    test_conflict_resolution()
