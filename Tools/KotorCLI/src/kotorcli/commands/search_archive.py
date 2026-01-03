"""Search archive command implementation."""
from __future__ import annotations

import fnmatch
import pathlib
import re
from argparse import Namespace
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykotor.tools.archives import (
    extract_bif,
    extract_key_bif,
    list_bif,
    list_key,
    search_in_erf,
    search_in_rim,
)

if TYPE_CHECKING:
    from logging import Logger


@dataclass(frozen=True)
class _SearchContext:
    case_sensitive: bool
    search_content: bool
    use_fnmatch: bool
    pat: str
    regex: re.Pattern[str] | None


def _compile_search(pattern: str, *, case_sensitive: bool, search_content: bool) -> _SearchContext:
    pat = pattern if case_sensitive else pattern.lower()
    if "*" in pat or "?" in pat:
        return _SearchContext(
            case_sensitive=case_sensitive,
            search_content=search_content,
            use_fnmatch=True,
            pat=pat,
            regex=None,
        )
    return _SearchContext(
        case_sensitive=case_sensitive,
        search_content=search_content,
        use_fnmatch=False,
        pat=pat,
        regex=re.compile(pat, re.IGNORECASE if not case_sensitive else 0),
    )


def _name_matches(
    *,
    resref: str,
    ext: str,
    ctx: _SearchContext,
) -> bool:
    name = f"{resref}.{ext}" if "." in ctx.pat else resref
    name_to_search = name if ctx.case_sensitive else name.lower()
    if ctx.use_fnmatch:
        return fnmatch.fnmatch(name_to_search, ctx.pat)
    assert ctx.regex is not None
    return bool(ctx.regex.search(name_to_search))


def _content_matches(data: bytes, ctx: _SearchContext) -> bool:
    try:
        content = data.decode("utf-8", errors="ignore")
    except Exception:
        return False

    content_to_search = content if ctx.case_sensitive else content.lower()
    if ctx.use_fnmatch:
        return ctx.pat in content_to_search
    assert ctx.regex is not None
    return bool(ctx.regex.search(content_to_search))


def _search_key(archive_path: pathlib.Path, ctx: _SearchContext, logger: Logger) -> int:
    bif_files, resources = list_key(archive_path)

    matches = 0
    if not ctx.search_content:
        for resref, ext, bif_index, res_index in resources:
            if _name_matches(resref=resref, ext=ext, ctx=ctx):
                bif_name = bif_files[bif_index] if bif_index < len(bif_files) else "?"
                logger.info(f"{resref}.{ext} (BIF: {bif_name}, idx: {res_index})")  # noqa: G004
                matches += 1
        return matches

    dummy_out = pathlib.Path.cwd() / ".kotorcli_search_tmp"
    for resource, _output_file, bif_path in extract_key_bif(
        archive_path,
        dummy_out,
        bif_search_dir=archive_path.parent,
    ):
        resref = resource.resref.get() if resource.resref else "unknown"
        ext = resource.restype.extension if resource.restype else "bin"
        if _content_matches(resource.data, ctx):
            logger.info(f"{resref}.{ext} (BIF: {bif_path.name})")  # noqa: G004
            matches += 1
    return matches


def _search_bif(archive_path: pathlib.Path, key_path: pathlib.Path | None, ctx: _SearchContext, logger: Logger) -> int:
    matches = 0
    if not ctx.search_content:
        for resource in list_bif(archive_path, key_path=key_path):
            resref = resource.resref.get() if resource.resref else "unknown"
            ext = resource.restype.extension if resource.restype else "bin"
            if _name_matches(resref=resref, ext=ext, ctx=ctx):
                logger.info(f"{resref}.{ext}")  # noqa: G004
                matches += 1
        return matches

    dummy_out = pathlib.Path.cwd() / ".kotorcli_search_tmp"
    for resource, _output_file in extract_bif(
        archive_path,
        dummy_out,
        key_path=key_path if key_path and key_path.exists() else None,
    ):
        resref = resource.resref.get() if resource.resref else "unknown"
        ext = resource.restype.extension if resource.restype else "bin"
        if _content_matches(resource.data, ctx):
            logger.info(f"{resref}.{ext}")  # noqa: G004
            matches += 1
    return matches


def cmd_search_archive(args: Namespace, logger: Logger) -> int:
    """Handle search-archive command - search for resources in archives.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    archive_path = pathlib.Path(args.file)

    if not archive_path.exists():
        logger.error(f"Archive file not found: {archive_path}")  # noqa: G004
        return 1

    suffix = archive_path.suffix.lower()

    try:
        case_sensitive = args.case_sensitive if hasattr(args, "case_sensitive") else False
        search_content = args.search_content if hasattr(args, "search_content") else False
        ctx = _compile_search(args.pattern, case_sensitive=case_sensitive, search_content=search_content)

        matches = 0
        if suffix in (".erf", ".mod", ".sav", ".hak"):
            for resref, restype in search_in_erf(
                archive_path,
                args.pattern,
                case_sensitive=case_sensitive,
                search_content=search_content,
            ):
                logger.info(f"{resref}.{restype}")  # noqa: G004
                matches += 1
        elif suffix == ".rim":
            for resref, restype in search_in_rim(
                archive_path,
                args.pattern,
                case_sensitive=case_sensitive,
                search_content=search_content,
            ):
                logger.info(f"{resref}.{restype}")  # noqa: G004
                matches += 1
        elif suffix == ".key":
            matches = _search_key(archive_path, ctx, logger)
        elif suffix == ".bif":
            key_path = pathlib.Path(args.key_file) if hasattr(args, "key_file") and args.key_file else None
            matches = _search_bif(archive_path, key_path, ctx, logger)
        else:
            logger.error(f"Unsupported archive type: {suffix}")  # noqa: G004
            return 1

        if matches == 0:
            logger.info("No matches found")
        else:
            logger.info(f"Found {matches} matches")  # noqa: G004

    except Exception:
        logger.exception("Failed to search archive")
        return 1
    else:
        return 0

