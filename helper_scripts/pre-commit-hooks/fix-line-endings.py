#!/usr/bin/env python3
"""Fix line endings and end-of-file for text files. Always returns 0."""

import sys

for f in sys.argv[1:]:
    try:
        with open(f, "rb") as file:
            content = file.read()
        # Fix line endings: CRLF -> LF, CR -> LF
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        # Fix end of file: ensure it ends with newline
        if not content.endswith(b"\n"):
            content += b"\n"
        with open(f, "wb") as file:
            file.write(content)
    except Exception:
        pass  # Ignore errors, just continue

sys.exit(0)  # Always succeed
