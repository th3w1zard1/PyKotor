"""
Enhanced diffing algorithms for KOTOR file formats.

This module provides improved diffing capabilities for all KOTOR file formats,
converting them to text representations for standardized diffing.
"""

from __future__ import annotations

import difflib
import hashlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any


class FileChange:
    """Represents a change to a file or resource."""
    
    def __init__(
        self,
        path: str,
        change_type: str,  # 'added', 'removed', 'modified'
        resource_type: str | None = None,
        old_content: str | None = None,
        new_content: str | None = None,
        diff_lines: list[str] | None = None,
    ):
        self.path = path
        self.change_type = change_type
        self.resource_type = resource_type
        self.old_content = old_content
        self.new_content = new_content
        self.diff_lines = diff_lines or []


class DiffResult:
    """Container for diff results between two installations."""
    
    def __init__(self):
        self.changes: list[FileChange] = []
        self.errors: list[str] = []
    
    def add_change(self, change: FileChange):
        """Add a file change to the results."""
        self.changes.append(change)
    
    def add_error(self, error: str):
        """Add an error message to the results."""
        self.errors.append(error)
    
    def get_changes_by_type(self, change_type: str) -> list[FileChange]:
        """Get all changes of a specific type."""
        return [change for change in self.changes if change.change_type == change_type]
    
    def get_changes_by_resource_type(self, resource_type: str) -> list[FileChange]:
        """Get all changes for a specific resource type."""
        return [change for change in self.changes if change.resource_type == resource_type]


class KotorDiffer:
    """Enhanced differ for KOTOR installations."""
    
    def __init__(self):
        # Common KOTOR file extensions
        self.gff_types = {
            'utc', 'uti', 'dlg', 'are', 'git', 'ifo', 'jrl', 'gff',
            'utm', 'utp', 'uts', 'utt', 'utw', 'ptm', 'ptt'
        }
        self.known_types = {
            '2da': '2da',
            'tlk': 'tlk', 
            'ssf': 'ssf',
            'lip': 'lip',
            'ini': 'ini'
        }
    
    def diff_installations(self, path1: Path, path2: Path) -> DiffResult:
        """Compare two KOTOR installations and return comprehensive diff results.
        
        Args:
        ----
            path1: Path to the first installation
            path2: Path to the second installation
            
        Returns:
        -------
            DiffResult: Comprehensive diff results
        """
        result = DiffResult()
        
        # Check if paths are KOTOR installations
        if not self._is_kotor_install(path1):
            result.add_error(f"Path {path1} is not a valid KOTOR installation")
            return result
        if not self._is_kotor_install(path2):
            result.add_error(f"Path {path2} is not a valid KOTOR installation")
            return result
        
        # Compare key directories and files
        self._diff_directory(path1 / "Override", path2 / "Override", result)
        self._diff_directory(path1 / "Modules", path2 / "Modules", result)
        
        # Optional directories
        if (path1 / "rims").exists() or (path2 / "rims").exists():
            self._diff_directory(path1 / "rims", path2 / "rims", result)
        if (path1 / "Lips").exists() or (path2 / "Lips").exists():
            self._diff_directory(path1 / "Lips", path2 / "Lips", result)
        
        return result
    
    def diff_files(self, file1: Path, file2: Path) -> FileChange | None:
        """Compare two individual files and return change information.
        
        Args:
        ----
            file1: Path to the first file
            file2: Path to the second file
            
        Returns:
        -------
            FileChange | None: The change information, or None if no changes
        """
        if not file1.exists() or not file2.exists():
            return None
        
        return self._diff_files(file1, file2, file1.name)
    
    def _is_kotor_install(self, path: Path) -> bool:
        """Check if a path is a valid KOTOR installation."""
        return path.is_dir() and (path / "chitin.key").exists()
    
    def _diff_directory(self, dir1: Path, dir2: Path, result: DiffResult):
        """Compare two directories recursively."""
        if not dir1.exists() and not dir2.exists():
            return
        
        # Get all files from both directories
        files1 = set()
        files2 = set()
        
        if dir1.exists():
            files1 = {f.relative_to(dir1) for f in dir1.rglob("*") if f.is_file()}
        if dir2.exists():
            files2 = {f.relative_to(dir2) for f in dir2.rglob("*") if f.is_file()}
        
        # Find added, removed, and common files
        added_files = files2 - files1
        removed_files = files1 - files2
        common_files = files1 & files2
        
        # Process each type of change
        for file_path in added_files:
            full_path = str(dir2.name / file_path)
            result.add_change(FileChange(full_path, "added", self._get_resource_type(file_path)))
        
        for file_path in removed_files:
            full_path = str(dir1.name / file_path)
            result.add_change(FileChange(full_path, "removed", self._get_resource_type(file_path)))
        
        for file_path in common_files:
            file1 = dir1 / file_path
            file2 = dir2 / file_path
            change = self._diff_files(file1, file2, str(dir1.name / file_path))
            if change:
                result.add_change(change)
    
    def _diff_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare two individual files."""
        try:
            # For now, do simple text comparison
            return self._diff_text_files(file1, file2, relative_path)
        except Exception as e:
            # Return an error change
            return FileChange(
                relative_path,
                "error",
                self._get_resource_type(file1),
                None,
                None,
                [f"Error comparing files: {str(e)}"]
            )
    
    def _diff_text_files(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare files as text and generate unified diff."""
        try:
            text1 = file1.read_text(encoding='utf-8', errors='ignore')
            text2 = file2.read_text(encoding='utf-8', errors='ignore')
            
            if text1 != text2:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=f"original/{relative_path}",
                    tofile=f"modified/{relative_path}",
                    lineterm=""
                ))
                return FileChange(
                    relative_path, 
                    "modified", 
                    self._get_resource_type(file1), 
                    text1, 
                    text2, 
                    diff_lines
                )
            
            return None
        except Exception:
            return self._diff_by_hash(file1, file2, relative_path)
    
    def _diff_by_hash(self, file1: Path, file2: Path, relative_path: str) -> FileChange | None:
        """Compare files by hash if no specific handler exists."""
        try:
            hash1 = self._calculate_file_hash(file1)
            hash2 = self._calculate_file_hash(file2)
            
            if hash1 != hash2:
                return FileChange(relative_path, "modified", self._get_resource_type(file1))
            
            return None
        except Exception:
            return FileChange(relative_path, "error", self._get_resource_type(file1))
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hasher = hashlib.sha256()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_resource_type(self, file_path: Path | str) -> str:
        """Get the resource type from a file path."""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        ext = file_path.suffix.lower().lstrip('.')
        
        if ext in self.gff_types:
            return ext
        elif ext in self.known_types:
            return self.known_types[ext]
        else:
            return 'binary'