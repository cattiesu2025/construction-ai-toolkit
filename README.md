# Construction AI Toolkit

> **PulseBuild AI Platform** — Two-surface LLM agent system for construction project risk management.

Built to demonstrate production-grade Agent and MCP Server engineering:

| Project | What it proves | How to run |
|---------|---------------|------------|
| **A: Delay Detection Agent** | Proactive Agent, Tool Use, Eval, observability | `uv run run-delay-agent` |
| **B: Construction MCP Server** | Protocol-layer abstraction, Tool/Resource/Prompt primitives | `uv run construction-mcp` |

Both surfaces share a single `core-tools` business-logic package — written once, consumed twice.

---

## Architecture

```
construction-ai-toolkit/
├── packages/
│   ├── core-tools/          # Shared business logic (schedule, weather, history, compliance, defects)
│   ├── delay-agent/         # Project A — proactive daily scheduled agent
│   └── mcp-server/          # Project B — MCP server for Claude Desktop / Cursor
├── data/                    # Mock data: 10 projects, 55 tasks, 17 defects, 35 compliance records
├── evals/                   # 20-case eval suite with LLM-as-judge
└── tests/                   # 54 unit tests (100% pass)
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
        ↓ MCP Protocol (stdio)
  Construction MCP Server
  ├── Tools (5):     find_defects_by_type, check_compliance, lookup_regulation,
  │                  get_schedule_data, analyze_progress_gap
  ├── Resources (3): project://{id}, schedule://{id}, compliance://{id}
  └── Prompts (2):   daily_report_template, risk_assessment_template
        ↓
  core-tools package (shared with Project A)
```

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
# Edit .env — fill in ANTHROPIC_API_KEY and SLACK_WEBHOOK_URL
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

### Run Tests

```bash
uv run pytest tests/ -v
# 54 passed in ~3s
```

---

## Claude Desktop Integration

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
```
