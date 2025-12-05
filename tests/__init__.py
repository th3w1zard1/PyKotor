from __future__ import annotations

from pathlib import Path
import pkgutil

# Allow the top-level `tests` package to span workspace test roots so both
# the repository-level tests and the library tests (e.g. Libraries/PyKotor/tests)
# are importable regardless of where pytest is launched from.
__path__: list[str] = pkgutil.extend_path(__path__, __name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYKOTOR_TESTS = _REPO_ROOT / "Libraries" / "PyKotor" / "tests"
if _PYKOTOR_TESTS.is_dir():
    _pykotor_tests_str = str(_PYKOTOR_TESTS)
    if _pykotor_tests_str not in __path__:
        __path__.append(_pykotor_tests_str)
