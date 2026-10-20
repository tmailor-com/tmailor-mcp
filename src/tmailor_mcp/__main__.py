"""Entry point: ``tmailor-mcp`` (stdio transport). The API key comes from ``TMAILOR_API_KEY``."""

from __future__ import annotations

import argparse
import os
import sys

from ._version import __version__


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tmailor-mcp",
        description="MCP server (stdio) for the Tmailor Open API. Set TMAILOR_API_KEY before starting it.",
    )
    parser.add_argument("--version", action="version", version=f"tmailor-mcp {__version__}")
    parser.parse_args(argv)
    if not os.environ.get("TMAILOR_API_KEY", "").strip():
        # stdout belongs to the MCP protocol: warnings go to stderr. The server still starts so the client can list
        # the tools; every call then explains how to set the key.
        print("tmailor-mcp: TMAILOR_API_KEY is not set; tool calls will fail until it is.", file=sys.stderr)
    from .server import build_server

    build_server().run("stdio")


if __name__ == "__main__":
    main()
