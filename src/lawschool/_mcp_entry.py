"""
src/lawschool/_mcp_entry.py

Entry point for the `lawschool-mcp` console script.

This shim adds the mcp-server/ directory to sys.path and delegates to
server.main(), matching how the server behaves when run directly.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    # Add mcp-server/ to sys.path so its local modules are importable
    _mcp_server_dir = Path(__file__).parent.parent.parent / "mcp-server"
    if str(_mcp_server_dir) not in sys.path:
        sys.path.insert(0, str(_mcp_server_dir))

    # Import and run the server
    import server as _server  # noqa: PLC0415
    _server.main()
