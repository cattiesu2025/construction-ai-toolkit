# Slack Bot — Design Document
_2026-05-16_

## Goal

Add interactive query capability to the existing Slack integration so users can @mention the bot in natural language and receive AI-generated answers drawn from live project data. Role-based access control limits which tools each user can invoke.

---

## Context

The project already has:
- **core-tools** package — 6 functions across schedule, defects, compliance modules
- **delay-agent** — proactive Slack push via webhook (one-way)
- **mcp-server** — thin wrappers over core-tools for Claude Desktop

This adds a new **slack-bot** package for two-way interaction inside Slack.

---

## Architecture

```
User @mentions bot in Slack
        ↓
  bot.py (Socket Mode listener)
        ↓
  handler.py
    1. Resolve Slack user_id → role + crew  (roles.py)
    2. Filter tool definitions by role       (tool_defs.py)
    3. Call Claude API with filtered tools   (Anthropic SDK)
    4. Execute tool_calls via dispatcher     (dispatcher.py)
    5. Return tool results → Claude
    6. Format final reply → Slack Block Kit
```

---

## Package Structure

```
packages/slack-bot/
├── src/slack_bot/
│   ├── config.py        # env vars loader
│   ├── roles.py         # load roles.json, resolve role + allowed tools
│   ├── tool_defs.py     # Anthropic tool schema for each core_tool function
│   ├── dispatcher.py    # execute tool_call → call core_tools function
│   ├── handler.py       # orchestrate Claude API agentic loop
│   └── bot.py           # Slack App entry point (Socket Mode)
├── roles.json           # Slack user_id → role mapping
└── pyproject.toml
```

---

## Role & Permission Model

### roles.json schema

```json
{
  "U123ABC": { "role": "pm",     "name": "Alice" },
  "U456DEF": { "role": "worker", "name": "Bob",   "crew": "Crew-A" },
  "U789GHI": { "role": "admin",  "name": "Charlie" }
}
```

Unknown user IDs default to no tools → bot replies with an "access denied" message.

### Tool access matrix

| Tool                  | admin | pm | worker        |
|-----------------------|-------|----|---------------|
| get_schedule_data     | ✅    | ✅ | ✅ (crew only) |
| analyze_progress_gap  | ✅    | ✅ | ✅            |
| get_all_defects       | ✅    | ✅ | ✗             |
| find_defects_by_type  | ✅    | ✅ | ✗             |
| check_compliance      | ✅    | ✅ | ✗             |
| lookup_regulation     | ✅    | ✅ | ✗             |

### Worker crew filtering

Worker's `crew` value from `roles.json` is:
1. Injected into the Claude system prompt: _"This user belongs to Crew-A. Only show tasks assigned to Crew-A."_
2. Applied as a post-filter in `dispatcher.py` on `get_schedule_data` results before returning to Claude.

---

## Claude API Integration

- Model: `claude-opus-4-7`
- Pattern: agentic tool-use loop (send message → handle tool_calls → send results → repeat until `end_turn`)
- Tool definitions: defined in `tool_defs.py` as Anthropic `ToolParam` dicts, filtered per role before each call
- Prompt caching: enabled on system prompt (static per role)

---

## Slack Setup

- **Socket Mode** — no public URL required, works on local machine
- Required tokens (added to `.env`):
  - `SLACK_BOT_TOKEN` — `xoxb-...` (bot OAuth token)
  - `SLACK_APP_TOKEN` — `xapp-...` (Socket Mode app-level token)
- Required scopes: `app_mentions:read`, `chat:write`, `channels:history`
- Event subscription: `app_mention`

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Unknown Slack user | Reply: "You don't have access. Contact your admin." |
| Claude API error | Reply: "Something went wrong. Try again." + log error |
| Tool returns `{"error": ...}` | Pass error string back to Claude, let Claude explain naturally |
| Slack send failure | Log, do not retry |

---

## Testing

- Unit tests for `roles.py` (role lookup, crew extraction, unknown user)
- Unit tests for `dispatcher.py` (correct function called, crew filter applied)
- Integration test: mock Slack event → assert Claude API called with correct tool subset
- Existing 54 core-tools tests remain unchanged

---

## What This Adds to the Portfolio Story

> "Built a full Slack AI integration: proactive delay alerts (webhook push) + interactive project queries (Slack Bot + Claude API + role-based tool access), both running locally with Socket Mode — mirroring the AI Alerts + access control requirements of the PulseBuild platform."
