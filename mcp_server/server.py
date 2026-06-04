"""
mcp_server/server.py — entry point for the Law School Ranking MCP server.

All tool logic lives in mcp_server/tools/.
All resource logic lives in mcp_server/resources.py.

This file only wires up the MCP framework and runs the server.
"""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from mcp_server import resources as _resources
from mcp_server.tools import admin as _admin
from mcp_server.tools import career as _career
from mcp_server.tools import compare as _compare
from mcp_server.tools import profile as _profile
from mcp_server.tools import search as _search

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

app = Server("lawschool-ranking-mcp")

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

# Simple modules with a single TOOL_DEFINITION and handle()
_SIMPLE_TOOL_MODULES = [_search, _profile, _compare, _career]

# Admin module has multiple tools; handled separately
_ADMIN_DISPATCH = {
    "explain_ranking": _admin.handle_explain,
    "flag_press_release_gaps": _admin.handle_flag,
    "get_research_queue_stats": _admin.handle_stats,
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    tools = [m.TOOL_DEFINITION for m in _SIMPLE_TOOL_MODULES]
    tools.extend(_admin.TOOL_DEFINITIONS)
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> list[TextContent]:
    args = arguments or {}

    # Simple tools
    for module in _SIMPLE_TOOL_MODULES:
        if module.TOOL_DEFINITION.name == name:
            return await module.handle(args)

    # Admin tools
    if name in _ADMIN_DISPATCH:
        return await _ADMIN_DISPATCH[name](args)

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Resource registry
# ---------------------------------------------------------------------------

@app.list_resources()
async def list_resources() -> list[Resource]:
    return _resources.RESOURCE_DEFINITIONS


@app.read_resource()
async def read_resource(uri) -> str:
    return await _resources.read_resource(str(uri))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
