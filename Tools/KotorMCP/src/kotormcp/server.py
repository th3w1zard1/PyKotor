"""KotorMCP - Model Context Protocol server for Knights of the Old Republic resources.

This server exposes context-rich tools tailored for AI agents. It focuses on installation
management, resource discovery, and journal/plot inspection workflows that mirror the
pipelines used in `Tools/KotorCLI` and helper scripts under `scripts/`.

Implementation notes:
    * Resource scanning logic mirrors `scripts/investigate_module_structure.py:35-120`.
    * Journal summarisation follows the same structure documented in
      `vendor/xoreos/src/engines/nwn2/journal.cpp:35-78`, ensuring parity with established
      engine reimplementations.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from collections.abc import Iterable, Iterator
from io import BytesIO
from pathlib import Path
from typing import Any

try:
    from uvicorn import Config, Server as UvicornServer
except ImportError:
    UvicornServer = None  # type: ignore[assignment, misc]
    Config = None  # type: ignore[assignment, misc]

import mcp.server.sse
import mcp.server.stdio
import mcp.server.streamable_http
from mcp import types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pykotor.common.misc import Game
from pykotor.extract.file import FileResource, ResourceResult
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default

SERVER = Server("KotorMCP")

INSTALLATIONS: dict[Game, Installation] = {}
DEFAULT_PATH_CACHE = find_kotor_paths_from_default()
GAME_ALIASES: dict[str, Game] = {
    "k1": Game.K1,
    "kotori": Game.K1,
    "swkotor": Game.K1,
    "k2": Game.K2,
    "tsl": Game.K2,
    "kotor2": Game.K2,
}
ENV_HINTS: dict[Game, tuple[str, ...]] = {
    Game.K1: ("K1_PATH", "KOTOR_PATH", "KOTOR1_PATH"),
    Game.K2: ("K2_PATH", "TSL_PATH", "KOTOR2_PATH", "K1_PATH"),
}

GFF_HEAVY_TYPES = {
    ResourceType.GFF,
    ResourceType.BIC,
    ResourceType.UTC,
    ResourceType.UTD,
    ResourceType.UTE,
    ResourceType.UTI,
    ResourceType.UTP,
    ResourceType.UTS,
    ResourceType.UTM,
    ResourceType.UTT,
    ResourceType.UTW,
    ResourceType.ARE,
    ResourceType.GIT,
    ResourceType.IFO,
    ResourceType.DLG,
    ResourceType.FAC,
    ResourceType.JRL,
}


def _resolve_game(label: str | None) -> Game | None:
    if label is None:
        return None
    normalized = label.strip().lower()
    return GAME_ALIASES.get(normalized)


def _iter_candidate_paths(game: Game, explicit: str | None) -> Iterator[CaseAwarePath]:
    seen: set[str] = set()
    if explicit:
        candidate = CaseAwarePath(explicit).expanduser().resolve()
        key = str(candidate).lower()
        if key not in seen:
            seen.add(key)
            yield candidate
    for env_name in ENV_HINTS.get(game, ()):
        env_value = os.environ.get(env_name)
        if env_value:
            candidate = CaseAwarePath(env_value).expanduser().resolve()
            key = str(candidate).lower()
            if key not in seen:
                seen.add(key)
                yield candidate
    for default_path in DEFAULT_PATH_CACHE.get(game, []):
        key = str(default_path).lower()
        if key not in seen:
            seen.add(key)
            yield default_path


def _load_installation(game: Game, explicit_path: str | None = None) -> Installation:
    cached = INSTALLATIONS.get(game)
    if cached:
        return cached

    for candidate in _iter_candidate_paths(game, explicit_path):
        if candidate.is_dir():
            INSTALLATIONS[game] = Installation(candidate)
            return INSTALLATIONS[game]

    raise ValueError(f"Unable to locate installation for {game.name}. Provide --path or set {ENV_HINTS[game][0]}.")


def _parse_resource_types(raw: Iterable[str] | None) -> set[ResourceType]:
    if not raw:
        return set()
    parsed: set[ResourceType] = set()
    for token in raw:
        value = token.strip().upper()
        if not value:
            continue
        if value in ResourceType.__members__:
            parsed.add(ResourceType[value])
            continue
        cleaned = value.lstrip(".").lower()
        try:
            parsed.add(ResourceType.from_extension(cleaned))
        except ValueError:
            raise ValueError(f"Unknown resource type '{token}'") from None
    return parsed


def _resource_snapshot(source: str, resource: FileResource) -> dict[str, Any]:
    identifier = resource.identifier()
    return {
        "resref": identifier.lower_resname,
        "type": resource.restype().name,
        "extension": resource.restype().extension,
        "size": resource.size(),
        "source": source,
        "filepath": str(resource.filepath()),
        "inside_capsule": resource.inside_capsule,
        "inside_bif": resource.inside_bif,
    }


def _resolve_module_name(installation: Installation, alias: str) -> str | None:
    alias_lower = alias.lower()
    modules = installation.modules_list()
    lookup = {name.lower(): name for name in modules}
    if alias_lower in lookup:
        return lookup[alias_lower]
    for candidate in modules:
        if alias_lower in candidate.lower():
            return candidate
    return None


def _iter_resources_for_location(
    installation: Installation,
    location: str,
    module_filter: str | None,
) -> Iterator[tuple[str, FileResource]]:
    lowered = location.lower()
    if lowered == "auto":
        lowered = "all"
    if lowered in {"override", "all"}:
        for resource in installation.override_resources():
            yield "override", resource
    if lowered in {"core", "all"}:
        for resource in installation.core_resources():
            yield "core", resource
    if lowered.startswith("module:"):
        _, module_alias = lowered.split(":", 1)
        resolved = _resolve_module_name(installation, module_alias)
        if not resolved:
            return
        for resource in installation.module_resources(resolved):
            yield f"module:{resolved}", resource
        return
    if lowered in {"modules", "all"}:
        for module_name in installation.modules_list():
            if module_filter and module_filter.lower() not in module_name.lower():
                continue
            for resource in installation.module_resources(module_name):
                yield f"module:{module_name}", resource
    if lowered in {"chitin", "bif", "all"}:
        for resource in installation.chitin_resources():
            yield "chitin", resource
    if lowered in {"lips", "all"}:
        for filename in installation.lips_list():
            for resource in installation.lip_resources(filename):
                yield f"lips:{filename}", resource
    if lowered in {"texturepacks", "textures", "all"}:
        for filename in installation.texturepacks_list():
            for resource in installation.texturepack_resources(filename):
                yield f"texturepack:{filename}", resource
    if lowered in {"streammusic", "all"}:
        installation.load_streammusic()
        for resource in installation._streammusic:
            yield "streammusic", resource
    if lowered in {"streamsounds", "all"}:
        installation.load_streamsounds()
        for resource in installation._streamsounds:
            yield "streamsounds", resource
    if lowered in {"streamwaves", "voice", "all"}:
        installation.load_streamwaves()
        for resource in installation._streamwaves:
            yield "streamwaves", resource


def _summarize_gff(data: bytes) -> dict[str, Any]:
    gff = read_gff(BytesIO(data))
    root = gff.root
    fields: list[dict[str, Any]] = []
    for label, field_type, value in root:
        preview: Any = value
        if isinstance(value, bytes):
            preview = f"<bytes:{len(value)}>"
        elif hasattr(value, "__len__") and len(str(value)) > 120:
            preview = f"{str(value)[:117]}..."
        fields.append(
            {
                "label": label,
                "type": field_type.name,
                "preview": preview,
            }
        )
    return {
        "struct_id": root.struct_id,
        "field_count": len(root),
        "fields": fields[:20],
    }


def _summarize_tlk(data: bytes) -> dict[str, Any]:
    tlk = read_tlk(BytesIO(data))
    entries = []
    for strref, entry in list(tlk.strings.items())[:20]:
        entries.append(
            {
                "strref": strref,
                "text": entry.text[:200],
                "sound": entry.sound,
            }
        )
    return {"language": tlk.language.name, "entry_count": len(tlk.strings), "sample": entries}


def _summarize_2da(data: bytes) -> dict[str, Any]:
    table = read_2da(BytesIO(data))
    rows = []
    for idx, row in enumerate(table.rows):
        rows.append({"row": idx, "values": row})
        if idx >= 15:
            break
    return {"columns": table.headers, "row_count": len(table.rows), "sample": rows}


def _summarize_binary(data: bytes) -> dict[str, Any]:
    digest = hashlib.sha1(data).hexdigest()
    return {
        "size": len(data),
        "sha1": digest,
        "head": data[:64].hex(),
    }


def _describe_resource(result: ResourceResult) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "resref": result.resname,
        "type": result.restype.name,
        "extension": result.restype.extension,
        "bytes": len(result.data),
        "source": str(result.filepath),
    }
    data = result.data
    if result.restype in GFF_HEAVY_TYPES:
        summary["analysis"] = _summarize_gff(data)
    elif result.restype is ResourceType.TLK:
        summary["analysis"] = _summarize_tlk(data)
    elif result.restype is ResourceType.TwoDA:
        summary["analysis"] = _summarize_2da(data)
    else:
        summary["analysis"] = {"size": len(data), "head": data[:64].hex()}
    return summary


def _journal_entries(installation: Installation) -> list[dict[str, Any]]:
    """Parse global.jrl and extract plot entries (structure documented in xoreos journal.cpp)."""
    resource = installation.resource("global", ResourceType.JRL)
    if resource is None:
        raise ValueError("Unable to locate global.jrl in the current installation.")
    gff = read_gff(BytesIO(resource.data))
    categories = []
    for entry in gff.root.get_list("Categories", default=[]):
        category = {
            "name": entry.get_string("Name", ""),
            "tag": entry.get_string("Tag", ""),
            "comment": entry.get_string("Comment", ""),
            "priority": entry.get_uint("Priority", 0),
            "xp": entry.get_uint("XP", 0),
            "entries": [],
        }
        for quest in entry.get_list("EntryList", default=[]):
            category["entries"].append(
                {
                    "id": quest.get_uint("ID", 0),
                    "text": quest.get_string("Text", "")[:400],
                    "comment": quest.get_string("Comment", ""),
                    "completes_plot": bool(quest.get_uint("End", 0)),
                }
            )
        categories.append(category)
    return categories


def _json_content(payload: Any) -> types.CallToolResult:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)])


@SERVER.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="detectInstallations",
            description="Enumerate candidate installation paths for K1/K2 by inspecting env vars and platform defaults.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="loadInstallation",
            description="Activate an installation in memory so subsequent tools can reuse cached data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "game": {"type": "string", "description": "k1, k2, or tsl"},
                    "path": {"type": "string", "description": "Optional absolute path override."},
                },
                "required": ["game"],
            },
        ),
        types.Tool(
            name="listResources",
            description="List resources from override/modules/chitin/etc with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "game": {"type": "string"},
                    "location": {
                        "type": "string",
                        "description": "override, modules, module:<name>, core, texturepacks, streammusic, etc.",
                    },
                    "moduleFilter": {"type": "string", "description": "Substring filter for module names."},
                    "resourceTypes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Resource types (NCS, DLG, JRL, .gff, etc.).",
                    },
                    "resrefQuery": {"type": "string", "description": "Case-insensitive substring filter for resrefs."},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
                },
            },
        ),
        types.Tool(
            name="describeResource",
            description="Fetch and summarize a specific resource (GFF, TLK, 2DA, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "game": {"type": "string"},
                    "resref": {"type": "string"},
                    "restype": {"type": "string"},
                    "order": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional SearchLocation names (override, modules, chitin, ...).",
                    },
                },
                "required": ["game", "resref", "restype"],
            },
        ),
        types.Tool(
            name="journalOverview",
            description="Summarise global.jrl plot categories and entries for the active installation.",
            inputSchema={
                "type": "object",
                "properties": {"game": {"type": "string"}},
                "required": ["game"],
            },
        ),
    ]


@SERVER.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
    if name == "detectInstallations":
        payload = {}
        for game in (Game.K1, Game.K2):
            default_keys = {str(path).lower() for path in DEFAULT_PATH_CACHE.get(game, [])}
            details = []
            for candidate in _iter_candidate_paths(game, None):
                key = str(candidate).lower()
                details.append(
                    {
                        "path": str(candidate),
                        "exists": candidate.is_dir(),
                        "label": "default" if key in default_keys else "env",
                    }
                )
            payload[game.name] = details
        return _json_content(payload)

    if name == "loadInstallation":
        game = _resolve_game(arguments.get("game"))
        if game is None:
            raise ValueError("Specify game as k1 or k2.")
        path = arguments.get("path")
        installation = _load_installation(game, path)
        return _json_content({"game": game.name, "path": str(installation.path())})

    if name == "listResources":
        game = _resolve_game(arguments.get("game"))
        if game is None:
            raise ValueError("Specify game parameter (k1/k2).")
        installation = _load_installation(game)
        location = arguments.get("location", "all")
        module_filter = arguments.get("moduleFilter")
        type_filters = _parse_resource_types(arguments.get("resourceTypes"))
        resref_query = (arguments.get("resrefQuery") or "").lower()
        limit = int(arguments.get("limit", 50))
        results = []
        for source, resource in _iter_resources_for_location(installation, location, module_filter):
            if resref_query and resref_query not in resource.resname().lower():
                continue
            if type_filters and resource.restype() not in type_filters:
                continue
            results.append(_resource_snapshot(source, resource))
            if len(results) >= limit:
                break
        return _json_content({"count": len(results), "items": results, "truncated": len(results) >= limit})

    if name == "describeResource":
        game = _resolve_game(arguments.get("game"))
        if game is None:
            raise ValueError("Specify game parameter (k1/k2).")
        installation = _load_installation(game)
        resref = arguments["resref"]
        restype = arguments["restype"]
        order_labels = arguments.get("order") or [
            SearchLocation.OVERRIDE.name,
            SearchLocation.CUSTOM_FOLDERS.name,
            SearchLocation.MODULES.name,
            SearchLocation.CHITIN.name,
        ]
        order: list[SearchLocation] = []
        for label in order_labels:
            upper = label.upper()
            if upper not in SearchLocation.__members__:
                raise ValueError(f"Unknown SearchLocation '{label}'")
            order.append(SearchLocation[upper])
        resource_type = _parse_resource_types([restype]).pop()
        result = installation.resource(resref, resource_type, order=order)
        if result is None:
            raise ValueError(f"{resref}.{resource_type.extension} not found.")
        summary = _describe_resource(result)
        return _json_content(summary)

    if name == "journalOverview":
        game = _resolve_game(arguments.get("game"))
        if game is None:
            raise ValueError("Specify game parameter (k1/k2).")
        installation = _load_installation(game)
        payload = _journal_entries(installation)
        return _json_content({"count": len(payload), "categories": payload})

    msg = f"Unknown tool '{name}'"
    raise ValueError(msg)


async def _run_stdio() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await SERVER.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="KotorMCP",
                server_version="0.1.0",
                capabilities=SERVER.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
                notification_options=NotificationOptions(),
            ),
        )


async def _run_sse(port: int = 8000, host: str = "localhost") -> None:
    """Run the server with SSE (Server-Sent Events) transport.

    The SSE transport uses Server-Sent Events for one-way streaming from server to client,
    and HTTP POST for client-to-server messages.
    """
    if UvicornServer is None or Config is None:
        msg = "uvicorn is required for SSE mode. Install with: pip install uvicorn[standard]"
        raise ImportError(msg)

    transport = mcp.server.sse.SseServerTransport(endpoint="/mcp")

    async def asgi_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "")
            
            if method == "GET" and path == "/mcp":
                # SSE connection - establishes Server-Sent Events stream
                await transport.connect_sse(scope, receive, send)
            elif method == "POST" and path == "/mcp":
                # POST message handling - processes MCP messages from client
                await transport.handle_post_message(scope, receive, send)
            else:
                # 404 for other paths
                await send({
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b"Not Found",
                })
        else:
            msg = f"Unsupported scope type: {scope['type']}"
            raise ValueError(msg)

    config = Config(
        app=asgi_app,
        host=host,
        port=port,
        log_level="info",
    )

    server = UvicornServer(config)
    await server.serve()


async def _run_http(port: int = 8000, host: str = "localhost") -> None:
    """Run the server with HTTP streaming transport.

    The HTTP streaming transport uses HTTP for bidirectional communication
    with streaming support for large messages.
    """
    if UvicornServer is None or Config is None:
        msg = "uvicorn is required for HTTP mode. Install with: pip install uvicorn[standard]"
        raise ImportError(msg)

    # HTTP transport requires mcp_session_id (can be None for new sessions)
    transport = mcp.server.streamable_http.StreamableHTTPServerTransport(mcp_session_id=None)

    async def asgi_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            method = scope.get("method", "")

            if method in ("GET", "POST"):
                # HTTP streaming transport handles all requests
                # The transport manages the connection and message flow
                await transport.handle_request(scope, receive, send)
            else:
                await send({
                    "type": "http.response.start",
                    "status": 405,
                    "headers": [[b"content-type", b"text/plain"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b"Method Not Allowed",
                })
        else:
            msg = f"Unsupported scope type: {scope['type']}"
            raise ValueError(msg)

    config = Config(
        app=asgi_app,
        host=host,
        port=port,
        log_level="info",
    )

    server = UvicornServer(config)
    await server.serve()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the KotorMCP server.")
    parser.add_argument(
        "--mode",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport to use (stdio for command-line, sse for Server-Sent Events, http for HTTP streaming)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to for HTTP/SSE modes (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for HTTP/SSE modes (default: 8000)"
    )
    args = parser.parse_args(argv)

    if args.mode == "stdio":
        asyncio.run(_run_stdio())
    elif args.mode == "sse":
        asyncio.run(_run_sse(port=args.port, host=args.host))
    elif args.mode == "http":
        asyncio.run(_run_http(port=args.port, host=args.host))
    else:
        msg = f"Unsupported mode: {args.mode}"
        raise SystemExit(msg)


if __name__ == "__main__":
    main()

