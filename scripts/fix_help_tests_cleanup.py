"""Script to clean up leftover code after help test functions."""
from __future__ import annotations

from pathlib import Path


def fix_file(test_file_path: Path):
    """Remove leftover code after help test functions."""
    content = test_file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Find help test function and remove everything after it until next def or end of file
    i = 0
    fixed = False
    while i < len(lines):
        # Look for help test function
        if "help_dialog" in lines[i] and "def test_" in lines[i]:
            # Find the end of this function (next def or end of file)
            j = i + 1
            indent_level = len(lines[i]) - len(lines[i].lstrip())

            # Find the function body end
            while j < len(lines):
                line_stripped = lines[j].strip()
                # Empty lines are OK
                if not line_stripped:
                    j += 1
                    continue

                # If we hit another def at same or less indent, we're done
                if line_stripped.startswith("def ") and len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                    break

                # If we hit a docstring or code that looks like it belongs to another function, check
                if line_stripped.startswith('"""') and j > i + 5:
                    # Check if this looks like start of new function
                    k = j + 1
                    while k < len(lines) and k < j + 3:
                        if "def test_" in lines[k]:
                            # This is a new function, stop here
                            break
                        k += 1
                    else:
                        # Not a new function, continue
                        j += 1
                        continue
                    break

                j += 1

            # Check if there's leftover code between end of help test and next function
            # Look for lines that reference test_files_dir or look like they belong to another test
            k = i + 1
            while k < j:
                if "test_files_dir" in lines[k] and "def test_" not in lines[k - 5 : k]:
                    # This is leftover code, remove from here to next def
                    # Find where the next proper function starts
                    next_def = j
                    for m in range(k, len(lines)):
                        if lines[m].strip().startswith("def test_"):
                            next_def = m
                            break
                    # Remove lines from k to next_def
                    del lines[k:next_def]
                    fixed = True
                    j = k  # Adjust j since we removed lines
                    break
                k += 1

            i = j
        else:
            i += 1

    if fixed:
        new_content = "\n".join(lines)
        test_file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    """Main function."""
    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / "tests" / "test_toolset" / "gui" / "editors"

    print("Cleaning up leftover code in help test files...")

    test_files = list(test_dir.glob("test_*_editor.py"))
    fixed_count = 0

    for test_file_path in test_files:
        content = test_file_path.read_text(encoding="utf-8")
        # Simple approach: find help test, then remove any lines with test_files_dir that aren't in a function signature
        lines = content.split("\n")
        new_lines = []
        i = 0
        in_help_test = False
        help_test_indent = 0

        while i < len(lines):
            line = lines[i]

            # Check if we're entering a help test function
            if "def test_" in line and "help_dialog" in line:
                in_help_test = True
                help_test_indent = len(line) - len(line.lstrip())
                new_lines.append(line)
                i += 1
                continue

            # If we're in a help test, check if we've left it
            if in_help_test:
                line_stripped = line.strip()
                # Check if this is the start of a new function
                if line_stripped.startswith("def test_") and len(line) - len(line.lstrip()) <= help_test_indent:
                    in_help_test = False
                    new_lines.append(line)
                    i += 1
                    continue

                # If we see test_files_dir usage that's not in the function signature, skip it and following lines until next def
                if "test_files_dir" in line and "def test_" not in line and ":" not in line.split("=")[0] if "=" in line else True:
                    # Skip this line and any following non-def lines
                    while i + 1 < len(lines):
                        i += 1
                        next_line = lines[i]
                        if next_line.strip().startswith("def test_"):
                            # Found next function, add it and break
                            new_lines.append(next_line)
                            in_help_test = False
                            i += 1
                            break
                        # Skip this line
                    continue

                new_lines.append(line)
            else:
                new_lines.append(line)

            i += 1

        new_content = "\n".join(new_lines)
        if new_content != content:
            test_file_path.write_text(new_content, encoding="utf-8")
            print(f"  Fixed {test_file_path.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
