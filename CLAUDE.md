# maczfit-mcp - project context

## Status: DONE, fully working

All 4 MCP tools tested live against real Maczfit account.

## What this is

Local MCP server (FastMCP/Python) for managing Maczfit diet deliveries via natural language.
Scrapes the Maczfit web app - no public API exists.

## Files

| File | Purpose |
|---|---|
| `server.py` | FastMCP server, exposes 4 tools |
| `client.py` | HTTP client - auth, CSRF, all API calls |
| `html_parser.py` | Parses JS variables + HTML from order pages |
| `.env` | Credentials (gitignored) |
| `requirements.txt` | fastmcp, requests, python-dotenv |

## Credentials (.env)

```
MACZFIT_EMAIL=...
MACZFIT_PASSWORD=...
MACZFIT_CLIENT_ID=180527
MACZFIT_TRANSACTION_IDS=8173549,8173576
```

`CLIENT_ID` and `TRANSACTION_IDS` must be in .env - they were accidentally committed to
public GitHub in early history. History was rewritten (orphan branch) and repo made private.

## APP_TOKEN in client.py

Hardcoded JWT is Maczfit's own public frontend token (not user credentials). Safe to commit.

## CSRF flow (reverse-engineered)

Laravel app uses single-use meta CSRF tokens:
1. `GET /` → extract `<meta name="csrf-token">` from HTML
2. POST to `/login-endpoint` with token as `X-CSRF-TOKEN` header + `Authorization: Bearer APP_TOKEN`
3. After login: `GET /moje-konto` → get fresh meta token for write ops
4. Before every POST: `_refresh_csrf()` fetches new token (single-use - stale = 419)
5. On 419: full re-login + retry

## Claude Desktop config

`~/Library/Application Support/Claude/claude_desktop_config.json` - already configured.
Restart Claude Desktop after any changes.

## Claude Code / CC config

Run once in terminal:
```bash
claude mcp add maczfit /Users/bartoszfink/dzikieProjekty/maczfit-mcp/.venv/bin/python3 /Users/bartoszfink/dzikieProjekty/maczfit-mcp/server.py
```
Do NOT add mcpServers to `~/.claude/settings.json` - CC schema rejects it.

## Known gotchas

- `html_parser.py` uses `(?:var|let|const)` - Maczfit uses `let`, not `var`
- `parse_all_transactions` parses `allTransactions` JS var which contains ALL diets across
  all transactions - one request is enough for `list_diets()`
- Changes must be made before 15:00 the day before delivery
- Session expires ~2h - client re-authenticates automatically on 401/302/500
