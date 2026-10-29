# Changelog

## 0.4.0 (2026-10-29)

- **Breaking:** `read_message` and `wait_for_message` no longer return `otp` and `codes`. The agent reads the code in the
  message text, as with any other email (the body and `links` are unchanged). The REST API and the SDKs still return
  `otp` and `codes`.
- Tool error messages no longer end with `(request_id …)`; the request id is written to the server log instead.
- `account_status` returns `ip_allowlist_enforced` and `client_ip` only while the IP allowlist applies (Free plan).
- `openWorldHint` is `true` only on the tools that return mail from outside senders (`wait_for_message`, `list_messages`,
  `read_message`); the tools that only touch the user's own account set it to `false`.
- The "quota used up", "IP not allowed" and "daily cap reached" errors link the page that explains quotas and plans
  (https://tmailor.com/temp-mail-api) instead of the purchase page or a "use a paid plan" hint.
- README: section on the hosted server (no install, OAuth sign-in; listed in Claude's Connectors Directory).
- The MCP Registry entry also lists the hosted server `https://mcp.tmailor.com/mcp` (Streamable HTTP, sign-in with
  OAuth), next to the PyPI package.

## 0.3.1 (2026-10-21)

- The stdio server adds `tmailor-mcp/<version> (stdio)` to the User-Agent of its API calls, so Tmailor can count
  local MCP use apart from direct SDK use (no change for you; no data about you or your mail is added).

## 0.3.0 (2026-10-21)

- `read_message` and `wait_for_message` take `body_format`: `text` (default, unchanged), `html` (the raw HTML as
  received, up to `max_html_chars`, default 100000, at most 500000) or `both`. Every message now has `has_html`.
  `html` on a message without an HTML part returns the text plus a `note`, so no body is lost.

## 0.2.0 (2026-10-21)

- The 8 tools moved to `tmailor_mcp.tools` and run on a per-call `Session` (shared by the stdio server and the hosted
  server mcp.tmailor.com). `wait_for_message` never hands the same message to two concurrent calls (per-message
  reservation). No change for stdio users.

## 0.1.1 (2026-10-20)

- Listed in the official MCP Registry as `io.github.tmailor-com/tmailor-mcp` (`server.json`, `mcp-name` marker in the README).

## 0.1.0 (2026-10-20)

- First version: stdio MCP server with the tools `create_mailbox`, `wait_for_message`, `list_messages`,
  `read_message`, `delete_mailbox`, `list_mailboxes`, `list_domains` and `account_status`, built on `tmailor-sdk`.
