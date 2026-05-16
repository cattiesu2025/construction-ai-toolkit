# Slack Bot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `slack-bot` package that lets users @mention a Slack bot in natural language, which calls Claude API with role-filtered tools and replies with live project data.

**Architecture:** New `packages/slack-bot` workspace package. Socket Mode (no public URL needed). Role-based access: `roles.json` maps Slack user IDs to roles; `tool_defs.py` filters the Anthropic tool list per role before each API call. Adapts the agentic loop pattern already in `packages/delay-agent/src/delay_agent/agent.py`.

**Tech Stack:** `slack-bolt` (Socket Mode), `anthropic` SDK, `python-dotenv`, existing `core-tools` workspace package.

---

## Reference Files

Before starting, read these for patterns to follow:
- `packages/delay-agent/src/delay_agent/config.py` — sys.path setup + dotenv pattern
- `packages/delay-agent/src/delay_agent/agent.py` — TOOLS list, _TOOL_HANDLERS dict, agentic loop
- `packages/delay-agent/pyproject.toml` — package config pattern

---

## Task 1: Package Scaffold

**Files:**
- Create: `packages/slack-bot/pyproject.toml`
- Create: `packages/slack-bot/src/slack_bot/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p packages/slack-bot/src/slack_bot
touch packages/slack-bot/src/slack_bot/__init__.py
```

**Step 2: Create `packages/slack-bot/pyproject.toml`**

```toml
[project]
name = "slack-bot"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40",
    "slack-bolt>=1.18",
    "python-dotenv>=1.0",
    "core-tools",
]

[tool.uv.sources]
core-tools = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/slack_bot"]

[project.scripts]
run-slack-bot = "slack_bot.bot:main"
```

**Step 3: Sync workspace to pick up new package**

```bash
uv sync
```

Expected: resolves without error, `slack-bot` appears in installed packages.

**Step 4: Commit**

```bash
git add packages/slack-bot/
git commit -m "feat: scaffold slack-bot package"
```

---

## Task 2: config.py + roles.json

**Files:**
- Create: `packages/slack-bot/src/slack_bot/config.py`
- Create: `packages/slack-bot/roles.json`

**Step 1: Create `packages/slack-bot/src/slack_bot/config.py`**

Follow the exact same pattern as `delay-agent/config.py` — inline sys.path setup so workspace packages are importable.

```python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).parents[4]
for _pkg in ["core-tools", "slack-bot"]:
    _src = str(_root / "packages" / _pkg / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)

load_dotenv(_root / ".env")

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
SLACK_BOT_TOKEN: str = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN: str = os.environ["SLACK_APP_TOKEN"]
BOT_MODEL: str = os.getenv("BOT_MODEL", "claude-opus-4-7")

ROLES_FILE: Path = _root / "packages" / "slack-bot" / "roles.json"
```

**Step 2: Create `packages/slack-bot/roles.json`**

```json
{
  "UADMIN001": { "role": "admin",  "name": "Admin User" },
  "UPM000001": { "role": "pm",     "name": "Alice PM" },
  "UWORKER01": { "role": "worker", "name": "Bob Worker", "crew": "Crew-A" }
}
```

Note: Replace these with real Slack user IDs before demoing. Find your user ID in Slack → Profile → ⋮ → Copy member ID.

**Step 3: Commit**

```bash
git add packages/slack-bot/src/slack_bot/config.py packages/slack-bot/roles.json
git commit -m "feat: slack-bot config and roles.json"
```

---

## Task 3: roles.py (TDD)

**Files:**
- Create: `tests/test_slack_bot_roles.py`
- Create: `packages/slack-bot/src/slack_bot/roles.py`

**Step 1: Write failing tests**

Create `tests/test_slack_bot_roles.py`:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

SAMPLE_ROLES = {
    "UADMIN001": {"role": "admin",  "name": "Admin"},
    "UPM000001": {"role": "pm",     "name": "Alice"},
    "UWORKER01": {"role": "worker", "name": "Bob", "crew": "Crew-A"},
}


@pytest.fixture(autouse=True)
def patch_roles_file(tmp_path):
    roles_path = tmp_path / "roles.json"
    roles_path.write_text(json.dumps(SAMPLE_ROLES))
    with patch("slack_bot.roles.ROLES_FILE", roles_path):
        yield


def test_get_role_pm():
    from slack_bot.roles import get_role
    assert get_role("UPM000001") == "pm"


def test_get_role_worker():
    from slack_bot.roles import get_role
    assert get_role("UWORKER01") == "worker"


def test_get_role_unknown_returns_none():
    from slack_bot.roles import get_role
    assert get_role("UNKNOWN") is None


def test_get_crew_for_worker():
    from slack_bot.roles import get_crew
    assert get_crew("UWORKER01") == "Crew-A"


def test_get_crew_for_pm_returns_none():
    from slack_bot.roles import get_crew
    assert get_crew("UPM000001") is None


def test_get_allowed_tool_names_admin():
    from slack_bot.roles import get_allowed_tool_names
    tools = get_allowed_tool_names("admin")
    assert "get_schedule_data" in tools
    assert "check_compliance" in tools
    assert "find_defects_by_type" in tools
    assert len(tools) == 6


def test_get_allowed_tool_names_pm():
    from slack_bot.roles import get_allowed_tool_names
    tools = get_allowed_tool_names("pm")
    assert "get_schedule_data" in tools
    assert "check_compliance" in tools
    assert len(tools) == 6


def test_get_allowed_tool_names_worker():
    from slack_bot.roles import get_allowed_tool_names
    tools = get_allowed_tool_names("worker")
    assert "get_schedule_data" in tools
    assert "analyze_progress_gap" in tools
    assert "check_compliance" not in tools
    assert "find_defects_by_type" not in tools
    assert len(tools) == 2


def test_get_allowed_tool_names_unknown_returns_empty():
    from slack_bot.roles import get_allowed_tool_names
    assert get_allowed_tool_names(None) == []
```

**Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_slack_bot_roles.py -v
```

Expected: `ImportError: No module named 'slack_bot.roles'`

**Step 3: Implement `packages/slack-bot/src/slack_bot/roles.py`**

```python
import json
import slack_bot.config  # noqa: F401 — triggers sys.path setup
from slack_bot.config import ROLES_FILE

_PM_TOOLS = [
    "get_schedule_data",
    "analyze_progress_gap",
    "get_all_defects",
    "find_defects_by_type",
    "check_compliance",
    "lookup_regulation",
]
_WORKER_TOOLS = ["get_schedule_data", "analyze_progress_gap"]
_ADMIN_TOOLS = _PM_TOOLS  # same set; extend here if needed

_ROLE_TOOLS: dict[str, list[str]] = {
    "admin":  _ADMIN_TOOLS,
    "pm":     _PM_TOOLS,
    "worker": _WORKER_TOOLS,
}


def _load() -> dict:
    return json.loads(ROLES_FILE.read_text())


def get_role(slack_user_id: str) -> str | None:
    return _load().get(slack_user_id, {}).get("role")


def get_crew(slack_user_id: str) -> str | None:
    return _load().get(slack_user_id, {}).get("crew")


def get_allowed_tool_names(role: str | None) -> list[str]:
    if role is None:
        return []
    return _ROLE_TOOLS.get(role, [])
```

**Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_slack_bot_roles.py -v
```

Expected: all 10 tests PASS.

**Step 5: Run full suite to check no regressions**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

**Step 6: Commit**

```bash
git add tests/test_slack_bot_roles.py packages/slack-bot/src/slack_bot/roles.py
git commit -m "feat: roles.py with role/crew resolution and tool allow-list"
```

---

## Task 4: tool_defs.py (TDD)

**Files:**
- Create: `tests/test_slack_bot_tool_defs.py`
- Create: `packages/slack-bot/src/slack_bot/tool_defs.py`

**Step 1: Write failing tests**

Create `tests/test_slack_bot_tool_defs.py`:

```python
def test_all_tools_have_required_keys():
    from slack_bot.tool_defs import ALL_TOOLS
    for tool in ALL_TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


def test_all_tools_count():
    from slack_bot.tool_defs import ALL_TOOLS
    assert len(ALL_TOOLS) == 6


def test_filter_tools_for_worker():
    from slack_bot.tool_defs import filter_tools
    tools = filter_tools(["get_schedule_data", "analyze_progress_gap"])
    assert len(tools) == 2
    names = [t["name"] for t in tools]
    assert "get_schedule_data" in names
    assert "check_compliance" not in names


def test_filter_tools_empty_returns_empty():
    from slack_bot.tool_defs import filter_tools
    assert filter_tools([]) == []


def test_filter_tools_all():
    from slack_bot.tool_defs import ALL_TOOLS, filter_tools
    all_names = [t["name"] for t in ALL_TOOLS]
    assert filter_tools(all_names) == ALL_TOOLS
```

**Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_slack_bot_tool_defs.py -v
```

Expected: `ImportError: No module named 'slack_bot.tool_defs'`

**Step 3: Implement `packages/slack-bot/src/slack_bot/tool_defs.py`**

```python
import slack_bot.config  # noqa: F401

ALL_TOOLS: list[dict] = [
    {
        "name": "get_schedule_data",
        "description": "Get planned vs actual progress for all tasks in a construction project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "analyze_progress_gap",
        "description": "Analyse deviation between planned and actual progress for a specific task, returning delay estimate and downstream impact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID e.g. T003"}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "get_all_defects",
        "description": "Return a summary of all defects for a project grouped by severity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "find_defects_by_type",
        "description": "Find all defects of a specific type in a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"},
                "defect_type": {
                    "type": "string",
                    "enum": ["structural", "electrical", "plumbing", "finish", "civil"],
                    "description": "Type of defect to filter by",
                },
            },
            "required": ["project_id", "defect_type"],
        },
    },
    {
        "name": "check_compliance",
        "description": "Check compliance status for a project against all registered regulations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "lookup_regulation",
        "description": "Search compliance records for regulations matching a keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Keyword to search e.g. 'asbestos', 'fire'"}
            },
            "required": ["keyword"],
        },
    },
]

_TOOL_INDEX: dict[str, dict] = {t["name"]: t for t in ALL_TOOLS}


def filter_tools(allowed_names: list[str]) -> list[dict]:
    return [_TOOL_INDEX[name] for name in allowed_names if name in _TOOL_INDEX]
```

**Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_slack_bot_tool_defs.py -v
```

Expected: all 5 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_slack_bot_tool_defs.py packages/slack-bot/src/slack_bot/tool_defs.py
git commit -m "feat: tool_defs.py with all 6 tool schemas and role-based filter"
```

---

## Task 5: dispatcher.py (TDD)

**Files:**
- Create: `tests/test_slack_bot_dispatcher.py`
- Create: `packages/slack-bot/src/slack_bot/dispatcher.py`

**Step 1: Write failing tests**

Create `tests/test_slack_bot_dispatcher.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def test_dispatch_get_schedule_data():
    from slack_bot.dispatcher import dispatch
    mock_result = {"project_id": "PRJ-001", "tasks": []}
    with patch("slack_bot.dispatcher._schedule.get_schedule_data", return_value=mock_result) as mock_fn:
        result = dispatch("get_schedule_data", {"project_id": "PRJ-001"}, crew=None)
    mock_fn.assert_called_once_with(project_id="PRJ-001")
    assert result == mock_result


def test_dispatch_get_schedule_data_filters_by_crew():
    from slack_bot.dispatcher import dispatch
    tasks = [
        {"task_id": "T001", "crew": "Crew-A"},
        {"task_id": "T002", "crew": "Crew-B"},
    ]
    mock_result = {"project_id": "PRJ-001", "tasks": tasks, "total_tasks": 2}
    with patch("slack_bot.dispatcher._schedule.get_schedule_data", return_value=mock_result):
        result = dispatch("get_schedule_data", {"project_id": "PRJ-001"}, crew="Crew-A")
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["task_id"] == "T001"


def test_dispatch_analyze_progress_gap():
    from slack_bot.dispatcher import dispatch
    mock_result = {"task_id": "T003", "gap_pct": 15.0}
    with patch("slack_bot.dispatcher._schedule.analyze_progress_gap", return_value=mock_result) as mock_fn:
        result = dispatch("analyze_progress_gap", {"task_id": "T003"}, crew=None)
    mock_fn.assert_called_once_with(task_id="T003")
    assert result == mock_result


def test_dispatch_check_compliance():
    from slack_bot.dispatcher import dispatch
    mock_result = {"compliance_risk": "MEDIUM"}
    with patch("slack_bot.dispatcher._compliance.check_compliance", return_value=mock_result) as mock_fn:
        result = dispatch("check_compliance", {"project_id": "PRJ-001"}, crew=None)
    mock_fn.assert_called_once_with(project_id="PRJ-001")
    assert result == mock_result


def test_dispatch_unknown_tool_raises():
    from slack_bot.dispatcher import dispatch
    with pytest.raises(KeyError):
        dispatch("nonexistent_tool", {}, crew=None)
```

**Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_slack_bot_dispatcher.py -v
```

Expected: `ImportError: No module named 'slack_bot.dispatcher'`

**Step 3: Implement `packages/slack-bot/src/slack_bot/dispatcher.py`**

```python
import slack_bot.config  # noqa: F401
from core_tools import schedule as _schedule
from core_tools import defects as _defects
from core_tools import compliance as _compliance


def dispatch(tool_name: str, tool_input: dict, crew: str | None) -> object:
    """Execute a tool call and return the result.

    crew is only used to post-filter get_schedule_data results for workers.
    """
    handlers = {
        "get_schedule_data":    lambda: _schedule.get_schedule_data(**tool_input),
        "analyze_progress_gap": lambda: _schedule.analyze_progress_gap(**tool_input),
        "get_all_defects":      lambda: _defects.get_all_for_project(**tool_input),
        "find_defects_by_type": lambda: _defects.find_by_type(**tool_input),
        "check_compliance":     lambda: _compliance.check_compliance(**tool_input),
        "lookup_regulation":    lambda: _compliance.lookup_regulation(**tool_input),
    }

    result = handlers[tool_name]()

    if tool_name == "get_schedule_data" and crew and isinstance(result, dict):
        result = dict(result)
        result["tasks"] = [t for t in result.get("tasks", []) if t.get("crew") == crew]

    return result
```

**Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_slack_bot_dispatcher.py -v
```

Expected: all 5 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_slack_bot_dispatcher.py packages/slack-bot/src/slack_bot/dispatcher.py
git commit -m "feat: dispatcher.py with crew-level filter for worker role"
```

---

## Task 6: handler.py (TDD)

**Files:**
- Create: `tests/test_slack_bot_handler.py`
- Create: `packages/slack-bot/src/slack_bot/handler.py`

**Step 1: Write failing tests**

Create `tests/test_slack_bot_handler.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def _make_end_turn_response(text="All good."):
    response = MagicMock()
    response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = text
    text_block.type = "text"
    response.content = [text_block]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    response.usage.cache_read_input_tokens = 0
    return response


def _make_tool_use_response(tool_name, tool_input, tool_id="tool_1"):
    response = MagicMock()
    response.stop_reason = "tool_use"
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = tool_id
    response.content = [block]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    response.usage.cache_read_input_tokens = 0
    return response


def test_handle_unknown_user_returns_access_denied():
    from slack_bot.handler import handle_mention
    with patch("slack_bot.handler.roles.get_role", return_value=None):
        result = handle_mention(user_id="UNKNOWN", text="PRJ-001 risks?")
    assert "access" in result.lower() or "denied" in result.lower() or "permission" in result.lower()


def test_handle_pm_calls_claude_with_filtered_tools():
    from slack_bot.handler import handle_mention
    with patch("slack_bot.handler.roles.get_role", return_value="pm"), \
         patch("slack_bot.handler.roles.get_crew", return_value=None), \
         patch("slack_bot.handler.roles.get_allowed_tool_names", return_value=["get_schedule_data"]), \
         patch("slack_bot.handler._client.messages.create", return_value=_make_end_turn_response("Summary here.")) as mock_create:
        result = handle_mention(user_id="UPM000001", text="PRJ-001 risks?")
    assert result == "Summary here."
    call_kwargs = mock_create.call_args.kwargs
    assert len(call_kwargs["tools"]) == 1
    assert call_kwargs["tools"][0]["name"] == "get_schedule_data"


def test_handle_executes_tool_call_and_returns_result():
    from slack_bot.handler import handle_mention
    tool_response = _make_tool_use_response("get_schedule_data", {"project_id": "PRJ-001"})
    end_response = _make_end_turn_response("No delays found.")

    with patch("slack_bot.handler.roles.get_role", return_value="pm"), \
         patch("slack_bot.handler.roles.get_crew", return_value=None), \
         patch("slack_bot.handler.roles.get_allowed_tool_names", return_value=["get_schedule_data"]), \
         patch("slack_bot.handler._client.messages.create", side_effect=[tool_response, end_response]), \
         patch("slack_bot.handler.dispatch", return_value={"tasks": []}) as mock_dispatch:
        result = handle_mention(user_id="UPM000001", text="PRJ-001 risks?")
    mock_dispatch.assert_called_once_with("get_schedule_data", {"project_id": "PRJ-001"}, crew=None)
    assert result == "No delays found."
```

**Step 2: Run tests — verify they fail**

```bash
uv run pytest tests/test_slack_bot_handler.py -v
```

Expected: `ImportError: No module named 'slack_bot.handler'`

**Step 3: Implement `packages/slack-bot/src/slack_bot/handler.py`**

Adapt the agentic loop from `delay-agent/agent.py`:

```python
import anthropic
import slack_bot.config as config  # must be first: triggers sys.path setup
from slack_bot import roles
from slack_bot.dispatcher import dispatch
from slack_bot.tool_defs import filter_tools

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_SYSTEM_BASE = (
    "You are a construction project assistant integrated into Slack. "
    "Answer questions about project schedule, defects, and compliance using the available tools. "
    "Be concise — Slack messages should be short. Use bullet points where helpful. "
    "If data shows no issues, say so clearly."
)


def handle_mention(user_id: str, text: str) -> str:
    """Process a Slack @mention and return the reply text."""
    role = roles.get_role(user_id)
    if role is None:
        return "You don't have access to this bot. Contact your admin."

    crew = roles.get_crew(user_id)
    allowed_names = roles.get_allowed_tool_names(role)
    tools = filter_tools(allowed_names)

    system_prompt = _SYSTEM_BASE
    if crew:
        system_prompt += f" This user belongs to {crew}. Only show data relevant to {crew}."

    messages: list[dict] = [{"role": "user", "content": text}]

    for _ in range(10):
        response = _client.messages.create(
            model=config.BOT_MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")),
                "Done — no summary produced.",
            )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    result = dispatch(block.name, block.input, crew=crew)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
                except Exception as exc:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {exc}",
                        "is_error": True,
                    })
            messages.append({"role": "user", "content": tool_results})

    return "Request timed out after too many tool calls. Please try a more specific question."
```

**Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_slack_bot_handler.py -v
```

Expected: all 3 tests PASS.

**Step 5: Run full suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

**Step 6: Commit**

```bash
git add tests/test_slack_bot_handler.py packages/slack-bot/src/slack_bot/handler.py
git commit -m "feat: handler.py with Claude API agentic loop and role-based tool filter"
```

---

## Task 7: bot.py (Slack Socket Mode Entry Point)

No unit tests for this file — it's the I/O boundary. Verified by smoke test in Task 8.

**Files:**
- Create: `packages/slack-bot/src/slack_bot/bot.py`

**Step 1: Create `packages/slack-bot/src/slack_bot/bot.py`**

```python
import logging
import slack_bot.config as config  # must be first
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bot.handler import handle_mention

logging.basicConfig(level=logging.INFO)

app = App(token=config.SLACK_BOT_TOKEN)


@app.event("app_mention")
def on_mention(event, say):
    user_id = event.get("user", "")
    text = event.get("text", "")
    reply = handle_mention(user_id=user_id, text=text)
    say(reply)


def main():
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add packages/slack-bot/src/slack_bot/bot.py
git commit -m "feat: bot.py Slack Socket Mode entry point"
```

---

## Task 8: Update .env.example and Smoke Test

**Files:**
- Modify: `.env.example`

**Step 1: Add new env vars to `.env.example`**

Open `.env.example` and add:

```
# Slack Bot (Socket Mode)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-level-token-here
# BOT_MODEL=claude-opus-4-7  # optional override
```

**Step 2: Add real tokens to `.env`** (not committed)

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

To get these tokens:
1. Go to api.slack.com/apps → Create New App → From scratch
2. Enable Socket Mode → generate App-Level Token (scope: `connections:write`) → this is `SLACK_APP_TOKEN`
3. OAuth & Permissions → add scopes: `app_mentions:read`, `chat:write` → Install to workspace → copy Bot Token → this is `SLACK_BOT_TOKEN`
4. Event Subscriptions → Enable → Subscribe to bot events: `app_mention`
5. Re-install app to workspace after adding scopes

**Step 3: Update roles.json with your real Slack user ID**

In Slack: click your name → Profile → ⋮ menu → Copy member ID. Replace `UADMIN001` with your real ID.

**Step 4: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass (currently 54 core + new slack-bot tests).

**Step 5: Smoke test — start the bot**

```bash
uv run run-slack-bot
```

Expected output:
```
INFO:slack_bolt.App:⚡️ Bolt app is running!
```

Then in Slack, @mention the bot:
```
@construction-bot PRJ-001 今天有什么风险?
```

Expected: bot replies within ~10s with a risk summary.

**Step 6: Final commit**

```bash
git add .env.example
git commit -m "feat: complete slack-bot with role-based Claude API integration"
```

---

## Summary

| Task | What it adds |
|------|-------------|
| 1 | Package scaffold + uv workspace |
| 2 | config.py + roles.json sample |
| 3 | roles.py — user ID → role/crew/tools |
| 4 | tool_defs.py — Anthropic schemas + filter |
| 5 | dispatcher.py — tool execution + crew filter |
| 6 | handler.py — Claude API agentic loop |
| 7 | bot.py — Slack Socket Mode listener |
| 8 | .env.example + smoke test |

New test count: 54 (existing) + ~18 (slack-bot) = **~72 tests total**.
