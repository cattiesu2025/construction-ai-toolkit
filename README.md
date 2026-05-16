# Construction AI Toolkit

> **PulseBuild AI Platform** — Three-surface LLM agent system for construction project risk management.

Built to demonstrate production-grade Agent, MCP Server, and Slack Bot engineering:

| Project | What it proves | Local | Cloud |
|---------|---------------|-------|-------|
| **A: Delay Detection Agent** | Proactive Agent, Tool Use, Eval, observability | `uv run run-delay-agent` | — |
| **B: Construction MCP Server** | Protocol-layer abstraction, Tool/Resource/Prompt primitives | `uv run construction-mcp` | Railway (HTTP) |
| **C: Slack Bot** | Interactive Claude API tool use, role-based access control | `uv run run-slack-bot` | Railway (Worker) |

All three surfaces share a single `core-tools` business-logic package — written once, consumed three times.

---

## Architecture

```
construction-ai-toolkit/
├── packages/
│   ├── core-tools/          # Shared business logic (schedule, weather, history, compliance, defects)
│   ├── delay-agent/         # Project A — proactive daily scheduled agent
│   ├── mcp-server/          # Project B — MCP server for Claude Desktop / Cursor
│   └── slack-bot/           # Project C — interactive Slack bot with role-based access
├── data/                    # Mock data: 10 projects, 55 tasks, 17 defects, 35 compliance records
├── evals/                   # 20-case eval suite with LLM-as-judge
└── tests/                   # 76 unit tests (100% pass)
```

### Project A — Delay Detection Agent

```
APScheduler (daily 7:00 AM)
        ↓
  Claude Agent (claude-sonnet-4-6)
        ↓ Tool Use loop (max 10 iterations)
  ┌─────────────────────────────────────┐
  │ get_schedule_data   → Pandas CSV    │
  │ analyze_progress_gap → statistics   │
  │ check_weather_impact → Open-Meteo   │
  │ get_history_delays  → mock DB       │
  │ send_slack_alert    → Slack webhook │
  └─────────────────────────────────────┘
```

### Project B — MCP Server

```
Claude Desktop / Cursor / Claude Code
        ↓ stdio (local)  OR  streamable-http (Railway)
  Construction MCP Server
  ├── Tools (5):     find_defects_by_type, check_compliance, lookup_regulation,
  │                  get_schedule_data, analyze_progress_gap
  ├── Resources (3): project://{id}, schedule://{id}, compliance://{id}
  └── Prompts (2):   daily_report_template, risk_assessment_template
        ↓
  core-tools package (shared with Projects A & C)
```

Transport is selected automatically: stdio when run locally, `streamable-http` when `PORT` env var is set (Railway injects this).

### Project C — Slack Bot

```
User @mentions bot in Slack
        ↓ Socket Mode (no public URL needed)
  slack-bolt App
        ↓
  Role check (roles.json: admin / pm / worker)
        ↓
  Claude API (claude-opus-4-7) + role-filtered tool definitions
        ↓ Tool Use loop
  ┌─────────────────────────────────────────────┐
  │ get_schedule_data    → schedule + crew filter│
  │ analyze_progress_gap → task deviation        │
  │ get_all_defects      → defect summary        │  ← pm / admin only
  │ find_defects_by_type → filtered defects      │  ← pm / admin only
  │ check_compliance     → compliance status     │  ← pm / admin only
  │ lookup_regulation    → regulation search     │  ← pm / admin only
  └─────────────────────────────────────────────┘
        ↓
  Natural language reply → Slack channel
```

**Role permissions:**

| Tool | admin | pm | worker |
|------|-------|----|--------|
| Schedule & progress | ✅ | ✅ | ✅ (own crew only) |
| Defects | ✅ | ✅ | — |
| Compliance | ✅ | ✅ | — |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Setup

```bash
git clone <repo-url> && cd construction-ai-toolkit
uv sync --all-packages
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL,
#             SLACK_BOT_TOKEN, SLACK_APP_TOKEN
```

### Run Project A — Delay Agent (one-shot)

```bash
uv run python -c "
from delay_agent.agent import run_delay_agent
result = run_delay_agent('PRJ-001')
print(result['summary'])
print(f'Cost: \${result[\"token_usage\"][\"estimated_cost_usd\"]:.4f}')
"
```

### Run Project A — Eval Suite

```bash
# Run all 20 eval cases (takes ~15 min, costs ~$1.50)
uv run run-eval

# Quick validation — first 3 cases only
uv run run-eval 3
```

### Run Project B — MCP Server

```bash
# Start MCP server (stdio mode — for Claude Desktop)
uv run construction-mcp

# Test with MCP Inspector (requires Node.js)
npx @modelcontextprotocol/inspector uv run construction-mcp
```

### Run Project C — Slack Bot

```bash
# Start bot (Socket Mode — no public URL needed)
uv run run-slack-bot

# In Slack, @mention the bot in any channel it's added to:
# @Construction Alert Bot PRJ-001 今天有什么风险?
# @Construction Alert Bot PRJ-003 check compliance status
```

**Setup:** Go to [api.slack.com/apps](https://api.slack.com/apps) → your app → add scopes `app_mentions:read` + `chat:write`, enable Socket Mode, subscribe to `app_mention` event. Add your Slack user ID to `packages/slack-bot/roles.json`.

### Run Tests

```bash
uv run pytest tests/ -v
# 76 passed in ~3s
```

---

## Deploy to Railway

Projects B and C run on Railway as two services in one project.

### Services

| Service | Type | Dockerfile |
|---------|------|-----------|
| `slack-bot` | Worker (no public port) | `packages/slack-bot/Dockerfile` |
| `mcp-server` | Web Service (HTTP) | `packages/mcp-server/Dockerfile` |

### Steps

1. **New Project** → Deploy from GitHub repo
2. **Service 1 — slack-bot**
   - Dockerfile Path: `packages/slack-bot/Dockerfile`
   - Variables: `ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`
   - Networking: disable public port (worker process)
3. **Service 2 — mcp-server**
   - Dockerfile Path: `packages/mcp-server/Dockerfile`
   - Variables: `ANTHROPIC_API_KEY`
   - Networking: enable public networking, note the generated URL
4. Both services share the same git repo root as build context — `core-tools` and `data/` are copied into each image.

### Connect Claude Desktop to Railway MCP Server

Once deployed, connect via the Railway URL instead of a local command:

```json
{
  "mcpServers": {
    "construction": {
      "url": "https://<your-mcp-server>.railway.app/mcp"
    }
  }
}
```

---

## Claude Desktop Integration (Local)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "construction": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/construction-ai-toolkit",
        "run", "--package", "construction-mcp-server", "construction-mcp"
      ]
    }
  }
}
```

Restart Claude Desktop → the construction tools appear in the tool menu.

**Example prompts after connecting:**

- `@project://PRJ-001 What are the biggest risks on this project today?`
- Select `/risk_assessment_template` → enter PRJ-003 → full risk report
- Select `/daily_report_template` → enter PRJ-005 → client-ready daily report

---

## Eval Results

20 test scenarios (10 should-alert, 10 should-not-alert) judged by LLM-as-judge across 3 dimensions:

| Metric | Score |
|--------|-------|
| Correctness (severity classification) | **100%** (3-case pilot) |
| Specificity (cites exact data) | **100%** |
| Actionability (concrete next steps) | **100%** |
| Avg iterations per project | 4.3 |
| Avg cost per project scan | $0.06 |

---

## Key Design Decisions

**Why 5 separate tools instead of 1?**
Single-responsibility + let the agent decide call order. A `do_everything()` tool is a script, not an agent.

**Why Open-Meteo instead of OpenWeather?**
Free with no API key required, sufficient accuracy for 7-day construction risk window.

**Why not LangChain?**
Direct Anthropic SDK gives full control over the tool loop, error handling, and token tracking. No hidden abstractions to debug in production.

**Why MCP Tools vs Resources vs Prompts?**
Tools = LLM-driven, stateful. Resources = user-referenced, read-only context. Prompts = user-selected workflow starters. Using all three shows understanding of the full protocol, not just tool wrapping.

**Prompt Caching**
System prompt marked `cache_control: ephemeral` — saves ~85% tokens on repeated runs to the same model instance.

---

## Cost Reference

| Operation | Model | Avg Cost |
|-----------|-------|----------|
| Single project scan | claude-sonnet-4-6 | $0.03–$0.07 |
| Full 10-project daily run | claude-sonnet-4-6 | ~$0.50 |
| Eval (20 cases × 2 calls) | claude-sonnet-4-6 | ~$1.50 |

---

## Project Structure

```
packages/core-tools/src/core_tools/
├── data_layer.py      # CSV loader
├── schedule.py        # get_schedule_data, analyze_progress_gap
├── weather.py         # check_weather_impact (Open-Meteo)
├── history.py         # get_history_delays
├── compliance.py      # check_compliance, lookup_regulation
└── defects.py         # find_by_type, get_all_for_project

packages/delay-agent/src/delay_agent/
├── agent.py           # Main tool-use loop with iteration safeguard
├── prompts.py         # System prompt
├── notifier.py        # Slack webhook sender
├── scheduler.py       # APScheduler daily runner
└── config.py          # .env loader

packages/mcp-server/src/construction_mcp/
├── server.py          # FastMCP app with all primitives registered
├── tools.py           # MCP tool wrappers
├── resources.py       # project://, schedule://, compliance:// handlers
└── prompts.py         # daily_report, risk_assessment templates

packages/slack-bot/src/slack_bot/
├── bot.py             # Slack App entry point (Socket Mode)
├── handler.py         # Claude API agentic loop
├── dispatcher.py      # Tool execution + crew-level filter
├── tool_defs.py       # Anthropic tool schemas + role filter
├── roles.py           # Slack user ID → role/crew/allowed tools
└── config.py          # .env loader
packages/slack-bot/
└── roles.json         # User ID → role mapping (edit before running)
```
