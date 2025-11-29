"""PyKotor tools package.

This package contains utility functions for working with KotOR game resources,
including model manipulation, door handling, creature management, and kit generation.
"""

# Lazy import to avoid circular dependency
def __getattr__(name: str):
    if name == "extract_kit":
        from pykotor.tools.kit import extract_kit
        return extract_kit
    if name == "find_module_file":
        from pykotor.tools.kit import find_module_file
        return find_module_file
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "extract_kit",
    "find_module_file",
]

