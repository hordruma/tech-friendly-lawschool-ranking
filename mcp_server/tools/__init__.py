"""
mcp_server/tools/__init__.py

Each tool module exposes:
    TOOL_DEFINITION   mcp.types.Tool   (the schema dict)
    handle(args)      async function   (the implementation)

admin.py is the exception: it exposes TOOL_DEFINITIONS (a list) and
per-tool handle_* functions, dispatched explicitly by server.py.
"""
