"""
mcp-server/tools/__init__.py

Registry of all MCP tool modules.

Each tool module exposes:
    TOOL_DEFINITION   mcp.types.Tool   (the schema dict)
    handle(args)      async function   (the implementation)

Note: this package is imported via sys.path (mcp-server/ on path), not as
mcp_server.tools, because the directory name contains a hyphen.
"""

