# Railway Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy slack-bot (Socket Mode worker) and mcp-server (HTTP web service) to Railway as two services in one project.

**Architecture:** Each service gets its own Dockerfile inside its package directory. Both Dockerfiles copy the full workspace root so the `core-tools` local workspace dependency resolves correctly. `server.py` is updated to use FastMCP's `streamable-http` transport so it binds to Railway's injected `PORT`.

**Tech Stack:** Python 3.11, uv workspace, Dockerfile, FastMCP `streamable-http`, Railway

---

### Task 1: Test server.py HTTP transport (TDD)

**Files:**
- Modify: `tests/test_mcp_server.py`

**Step 1: Add failing tests to `tests/test_mcp_server.py`**

Add this class at the bottom of the file:

```python
class TestMCPServerMain:
    def test_main_uses_streamable_http(self, monkeypatch):
        from unittest.mock import patch
        monkeypatch.setenv("PORT", "9001")
        with patch("construction_mcp.server.mcp.run") as mock_run:
            from construction_mcp.server import main
            main()
            mock_run.assert_called_once_with(
                transport="streamable-http",
                host="0.0.0.0",
                port=9001,
            )

    def test_main_defaults_to_port_8000(self, monkeypatch):
        from unittest.mock import patch
        monkeypatch.delenv("PORT", raising=False)
        with patch("construction_mcp.server.mcp.run") as mock_run:
            from construction_mcp.server import main
            main()
            mock_run.assert_called_once_with(
                transport="streamable-http",
                host="0.0.0.0",
                port=8000,
            )
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_mcp_server.py::TestMCPServerMain -v
```

Expected: FAIL — `mcp.run` called with no args, not `transport="streamable-http"`

---

### Task 2: Update server.py main()

**Files:**
- Modify: `packages/mcp-server/src/construction_mcp/server.py`

**Step 1: Add `os` import and update `main()`**

At the top of the file, add `import os` after the existing imports. Replace `main()`:

```python
import os

def main() -> None:
    port = int(os.getenv("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
```

**Step 2: Run tests to verify they pass**

```bash
uv run pytest tests/test_mcp_server.py -v
```

Expected: ALL PASS (including the new `TestMCPServerMain` tests)

**Step 3: Commit**

```bash
git add packages/mcp-server/src/construction_mcp/server.py tests/test_mcp_server.py
git commit -m "feat: switch mcp-server to streamable-http transport for Railway"
```

---

### Task 3: Create .railwayignore

**Files:**
- Create: `.railwayignore`

**Step 1: Create the file**

```
.env
.venv/
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/
dist/
.DS_Store
```

**Step 2: Commit**

```bash
git add .railwayignore
git commit -m "chore: add .railwayignore to exclude dev artifacts from Railway builds"
```

---

### Task 4: Create slack-bot Dockerfile

**Files:**
- Create: `packages/slack-bot/Dockerfile`

**Step 1: Create the file**

```dockerfile
FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/core-tools ./packages/core-tools
COPY packages/slack-bot ./packages/slack-bot
RUN uv sync --package slack-bot --no-dev --frozen
CMD ["uv", "run", "run-slack-bot"]
```

**Step 2: Verify build (requires Docker)**

Run from the repo root:

```bash
docker build -f packages/slack-bot/Dockerfile . -t slack-bot-test
```

Expected: Build completes, image tagged `slack-bot-test`

If Docker is not available locally, skip this step — Railway will validate the build on first deploy.

**Step 3: Commit**

```bash
git add packages/slack-bot/Dockerfile
git commit -m "feat: add Dockerfile for slack-bot Railway deployment"
```

---

### Task 5: Create mcp-server Dockerfile

**Files:**
- Create: `packages/mcp-server/Dockerfile`

**Step 1: Create the file**

```dockerfile
FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/core-tools ./packages/core-tools
COPY packages/mcp-server ./packages/mcp-server
RUN uv sync --package construction-mcp-server --no-dev --frozen
CMD ["uv", "run", "construction-mcp"]
```

Note: the uv package name is `construction-mcp-server` (from `packages/mcp-server/pyproject.toml`), not `mcp-server`.

**Step 2: Verify build (requires Docker)**

Run from the repo root:

```bash
docker build -f packages/mcp-server/Dockerfile . -t mcp-server-test
```

Expected: Build completes, image tagged `mcp-server-test`

**Step 3: Commit**

```bash
git add packages/mcp-server/Dockerfile
git commit -m "feat: add Dockerfile for mcp-server Railway deployment"
```

---

### Task 6: Railway Dashboard setup (manual steps)

No code to write — this is a checklist for Railway setup after the branch is merged.

**Step 1: Create Railway project**

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select the `construction-ai-toolkit` repo

**Step 2: Configure slack-bot service**

1. Railway auto-creates a service — rename it `slack-bot`
2. Settings → Build:
   - Root Directory: `/` (leave blank / default)
   - Dockerfile Path: `packages/slack-bot/Dockerfile`
3. Settings → Networking: **disable** public networking (worker, no HTTP)
4. Variables → add:
   - `ANTHROPIC_API_KEY`
   - `SLACK_BOT_TOKEN`
   - `SLACK_APP_TOKEN`
   - `BOT_MODEL` = `claude-sonnet-4-6` (optional)

**Step 3: Configure mcp-server service**

1. New Service → GitHub repo (same repo)
2. Rename to `mcp-server`
3. Settings → Build:
   - Root Directory: `/`
   - Dockerfile Path: `packages/mcp-server/Dockerfile`
4. Settings → Networking: **enable** public networking, note the generated URL
5. Variables → add:
   - `ANTHROPIC_API_KEY`

**Step 4: Deploy both services**

Trigger deploy (or push to branch). Verify:
- `slack-bot` logs show `⚡️ Bolt app is running!`
- `mcp-server` logs show FastMCP startup on the assigned PORT

**Step 5: Test MCP Server endpoint**

```bash
curl https://<your-mcp-server-url.railway.app>/mcp
```

Expected: MCP server responds (JSON or SSE headers)

---

### Task 7: Push branch and create PR

**Step 1: Push branch**

```bash
git push origin feat/slack-bot
```

**Step 2: Create PR**

```bash
gh pr create --title "feat: Railway deployment for slack-bot and mcp-server" \
  --body "Adds Dockerfiles and HTTP transport for Railway cloud deployment. See docs/plans/2026-05-17-railway-deployment-design.md for full design."
```
