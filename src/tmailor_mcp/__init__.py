"""MCP server for the Tmailor Open API: receive-only temporary email addresses for AI agents."""

from ._version import __version__
from .server import build_server

__all__ = ["__version__", "build_server", "main"]


def main() -> None:
    from .__main__ import main as _main

    _main()
