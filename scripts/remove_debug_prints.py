"""Remove DEBUG print statements from the NCS compiler classes file."""
import re

from pathlib import Path

file_path = Path("Libraries/PyKotor/src/pykotor/resource/formats/ncs/compiler/classes.py")
content = file_path.read_text(encoding="utf-8")

# Remove lines that are just debug print statements
pattern = r'^\s*print\(f"DEBUG.*?\)\n'
new_content = re.sub(pattern, '', content, flags=re.MULTILINE)

file_path.write_text(new_content, encoding="utf-8")
print("Done removing DEBUG print statements")

