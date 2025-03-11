#!/usr/bin/env python3
from __future__ import annotations

if __name__ == "__main__":
    try:
        from toolset.main_init import main_init
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).absolute().parent.parent))
        from toolset.main_init import main_init
    main_init()
    from toolset.main_app import main
    main()

