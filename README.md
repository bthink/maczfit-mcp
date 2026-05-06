# maczfit-mcp

Local MCP server for managing Maczfit diet deliveries via natural language.

**Example:** "przenieś obie diety z poniedziałku na środę"

## Tools

| Tool | Description |
|---|---|
| `list_diets` | List active diet subscriptions |
| `get_schedule(transaction_id)` | Get delivery schedule for a diet |
| `move_day(transaction_id, package_id, new_date)` | Move a single package |
| `move_day_by_date(from_date, to_date)` | Move all diets from one date to another |
| `get_menu(transaction_id, date)` | Get meal plan with macros for a specific date |

## Setup

**1. Clone repo**

```bash
git clone https://github.com/YOUR_USERNAME/maczfit-mcp
```

**2. Configure credentials**

```bash
cp .env.example .env
# Fill in MACZFIT_EMAIL and MACZFIT_PASSWORD
chmod 600 .env
```

**3. Add to Claude Desktop or Claude Code**

Claude Desktop - `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "maczfit": {
      "command": "uvx",
      "args": ["--from", "/path/to/maczfit-mcp", "maczfit-mcp"],
      "env": {
        "MACZFIT_EMAIL": "your@email.com",
        "MACZFIT_PASSWORD": "yourpassword"
      }
    }
  }
}
```

Claude Code - run once in terminal:

```bash
claude mcp add maczfit uvx --from /path/to/maczfit-mcp maczfit-mcp
```

`uvx` installs dependencies automatically on first run - no manual venv needed.

Restart Claude after config changes.

## Notes

- Only `MACZFIT_EMAIL` and `MACZFIT_PASSWORD` are needed - client ID, transaction IDs,
  and the app token are all discovered automatically after login
- Session expires after ~2h - client re-authenticates automatically
- Changes must be made before 15:00 the day prior to delivery
- Unofficial usage of your own account via web scraping - no public API
