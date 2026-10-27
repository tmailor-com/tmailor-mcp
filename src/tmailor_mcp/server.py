"""Stdio MCP server for the Tmailor Open API (one local account per process).

The tools live in ``tools.py``; this module only provides ``LocalSession``: one API client (key from
``TMAILOR_API_KEY``), an in-memory email -> token cache and in-process locks. The hosted server (``mcp_remote``)
uses the same tools with a per-request, per-account session backed by Redis.
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional

import httpx
import tmailor
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from tmailor import AsyncClient, AsyncMailbox

from ._version import __version__
from .tools import INSTRUCTIONS, MAX_POLL, MAX_SCAN, PLATFORM_URL, _norm_email, register_tools


class LocalSession:
    """One API client per process + email -> token cache (tokens never leave this object)."""

    max_wait = 300.0  # one local user: long waits are fine
    RESERVE_TTL = 120.0

    def __init__(self, client_factory: Callable[[], AsyncClient]) -> None:
        self._factory = client_factory
        self._client: Optional[AsyncClient] = None
        self._tokens: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._claim: Dict[str, asyncio.Lock] = {}
        self._reserved: Dict[str, float] = {}

    @property
    def client(self) -> AsyncClient:
        if self._client is None:
            self._client = self._factory()
        return self._client

    def require(self, scope: str) -> None:
        """A local API key has every scope."""

    async def remember(self, mb: Any) -> None:
        if getattr(mb, "token", None) and getattr(mb, "email", None):
            self._tokens[mb.email.lower()] = mb.token

    async def forget(self, email: str) -> None:
        self._tokens.pop(email, None)

    def claim(self, email: str) -> Any:
        """Review 2026-10-20 CORE-02: serialises "find unread + read it" per address inside this process, so two
        concurrent waits never return the same message. (Two MCP processes on one account can still race.)"""
        return self._claim.setdefault(email, asyncio.Lock())

    @asynccontextmanager
    async def wait_slot(self) -> AsyncIterator[None]:
        yield  # one local user: no limit on concurrent waits

    async def poll_delay(self, delay: float) -> float:
        rl = self.client.last_rate_limit
        if rl is not None and rl.remaining is not None and rl.remaining < 5:
            return max(delay, 10.0)  # keep requests for the user's other calls this minute
        return min(delay, MAX_POLL)

    async def _scan(self, email: str) -> Optional[str]:
        async with self._lock:
            if email in self._tokens:
                return self._tokens[email]
            async for mb in self.client.mailboxes.list(limit=MAX_SCAN, page_size=100):
                await self.remember(mb)
                if mb.email.lower() == email:
                    return mb.token
        return None

    async def mailbox(self, email: str, *, refresh: bool = False) -> AsyncMailbox:
        e = _norm_email(email)
        if refresh:
            await self.forget(e)
        token = self._tokens.get(e) or await self._scan(e)
        if not token:
            raise ToolError(
                f"{email} is not an address of this Tmailor account (checked the {MAX_SCAN} newest). "
                "Use an address from create_mailbox or list_mailboxes."
            )
        return self.client.mailbox(token)

    async def run(self, email: str, fn: Callable[[AsyncMailbox], Awaitable[Any]]) -> Any:
        """Call ``fn(mailbox)``; on MailboxNotFound with a cached token, reload the token once (it may have been rotated)."""
        e = _norm_email(email)
        cached = e in self._tokens
        try:
            return await fn(await self.mailbox(e))
        except tmailor.MailboxNotFoundError:
            if not cached:
                raise
            return await fn(await self.mailbox(e, refresh=True))

    async def release(self) -> None:
        """The process-wide client stays open between tool calls."""

    async def reserve(self, email: str, message_id: str) -> bool:
        now = time.monotonic()
        self._reserved = {k: t for k, t in self._reserved.items() if t > now}
        key = f"{email}\0{message_id}"
        if key in self._reserved:
            return False
        self._reserved[key] = now + self.RESERVE_TTL
        return True

    async def preflight(self) -> None:
        """Nothing to check locally."""

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()


USER_AGENT_TAG = f"tmailor-mcp/{__version__} (stdio)"


async def _tag_user_agent(request: httpx.Request) -> None:
    """Append this server to the SDK's User-Agent, so the Open API can count local MCP use apart from plain SDK use."""
    ua = request.headers.get("User-Agent", "")
    if USER_AGENT_TAG not in ua:
        request.headers["User-Agent"] = f"{ua} {USER_AGENT_TAG}".strip()


def default_client() -> AsyncClient:
    """SDK client (key from ``TMAILOR_API_KEY``) whose User-Agent also names tmailor-mcp."""
    http = httpx.AsyncClient(follow_redirects=False, event_hooks={"request": [_tag_user_agent]})
    client = AsyncClient(http_client=http)
    orig = client.aclose

    async def aclose() -> None:  # the SDK does not close an http_client it was given
        await orig()
        await http.aclose()

    client.aclose = aclose  # type: ignore[method-assign]
    return client


def build_server(client_factory: Optional[Callable[[], AsyncClient]] = None) -> MCPServer:
    """Build the stdio MCP server. ``client_factory`` is for tests; by default the key comes from ``TMAILOR_API_KEY``."""
    session = LocalSession(client_factory or default_client)
    mcp = MCPServer(
        "tmailor",
        title="Tmailor temporary email",
        instructions=INSTRUCTIONS,
        website_url=PLATFORM_URL,
        version=__version__,
    )

    async def get_session() -> LocalSession:
        return session

    register_tools(mcp, get_session)
    return mcp


__all__ = ["LocalSession", "__version__", "build_server", "default_client"]
