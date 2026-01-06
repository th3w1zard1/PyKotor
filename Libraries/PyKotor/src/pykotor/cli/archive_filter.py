"""Archive filtering helpers for PyKotor CLI.

PyKotor CLI users commonly think in terms of filenames like ``p_cand.utc`` rather than
separate (resref, restype) fields. These helpers implement a small, consistent rule
set that works across KEY/BIF/RIM/ERF listings and extraction.
"""

from __future__ import annotations

import fnmatch


def _has_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in ("*", "?", "["))


def matches_resource_name(
    resref: str,
    ext: str,
    pattern: str,
) -> bool:
    """Return True if a resource matches the user-supplied filter.

    Rules:
    - If pattern contains glob chars (*, ?, [), use fnmatch (case-insensitive).
      - If pattern contains a dot, match against ``resref.ext``.
      - Otherwise, match against ``resref``.
    - If pattern contains a dot and no glob chars, treat it as an exact filename match
      against ``resref.ext`` (case-insensitive).
    - Otherwise (no dot, no glob chars), treat it as a prefix match on ``resref``
      (case-insensitive).
    """
    resref_l = resref.lower()
    ext_l = ext.lower()
    pat_l = pattern.lower()

    full_name = f"{resref_l}.{ext_l}"

    if _has_glob(pat_l):
        if "." in pat_l:
            return fnmatch.fnmatch(full_name, pat_l)
        return fnmatch.fnmatch(resref_l, pat_l)

    if "." in pat_l:
        return full_name == pat_l

    return resref_l.startswith(pat_l)
