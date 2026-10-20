# Changelog

## 0.2.0 (2026-10-21)

- The 8 tools moved to `tmailor_mcp.tools` and run on a per-call `Session` (shared by the stdio server and the hosted
  server mcp.tmailor.com). `wait_for_message` never hands the same message to two concurrent calls (per-message
  reservation). No change for stdio users.

## 0.1.1 (2026-10-20)

- Listed in the official MCP Registry as `io.github.tmailor-com/tmailor-mcp` (`server.json`, `mcp-name` marker in the README).

## 0.1.0 (2026-10-20)

- First version: stdio MCP server with the tools `create_mailbox`, `wait_for_message`, `list_messages`,
  `read_message`, `delete_mailbox`, `list_mailboxes`, `list_domains` and `account_status`, built on `tmailor-sdk`.
