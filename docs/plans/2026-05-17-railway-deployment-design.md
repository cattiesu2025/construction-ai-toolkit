# Railway Deployment Design

**Date:** 2026-05-17  
**Services:** slack-bot, mcp-server  
**Approach:** Dockerfile per package, one Railway project with two services

---

## Goals

Deploy the `slack-bot` and `mcp-server` packages to Railway so they run continuously in the cloud, with `slack-bot` connecting to Slack via Socket Mode and `mcp-server` exposing an HTTP endpoint for remote MCP clients.

---

## File Changes

### New files
- `packages/slack-bot/Dockerfile`
- `packages/mcp-server/Dockerfile`
- `.railwayignore`

### Modified files
- `packages/mcp-server/src/construction_mcp/server.py` — switch `main()` from stdio to `streamable-http` transport

---

## Architecture

### Slack Bot (Railway Worker)

- Runs as a long-lived worker process using Socket Mode (WebSocket outbound).
- No inbound HTTP port required — Railway Service type: **Worker**.
- Entry point: `uv run run-slack-bot`

### MCP Server (Railway Web Service)

- Exposes MCP tools over HTTP using FastMCP `streamable-http` transport.
- Railway injects `PORT`; server binds to `0.0.0.0:$PORT`.
- Entry point: `uv run construction-mcp`
- Remote MCP clients (Claude Desktop, Cursor) connect via the Railway-assigned URL.

---

## Dockerfiles

Both Dockerfiles copy the full workspace root (needed for `core-tools` local workspace dependency) and use `uv sync --package <name> --no-dev` to install only the relevant package and its deps.

```
FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/core-tools ./packages/core-tools
COPY packages/<service> ./packages/<service>
RUN uv sync --package <package-name> --no-dev
CMD ["uv", "run", "<entrypoint>"]
```

---

## server.py Change

```python
# Before
def main() -> None:
    mcp.run()

# After
def main() -> None:
    port = int(os.getenv("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
```

---

## Environment Variables

Set in Railway Dashboard Variables — never committed to the repo.

| Variable | slack-bot | mcp-server |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | ✅ |
| `SLACK_BOT_TOKEN` | ✅ | — |
| `SLACK_APP_TOKEN` | ✅ | — |
| `BOT_MODEL` | optional | — |

---

## Railway Setup (Manual)

1. New Project → Deploy from GitHub repo
2. Service 1: Root Dir `/`, Dockerfile Path `packages/slack-bot/Dockerfile`, type Worker
3. Service 2: Root Dir `/`, Dockerfile Path `packages/mcp-server/Dockerfile`, type Web Service
4. Set Variables for each service

---

## Constraints

- `.env` is excluded via `.railwayignore` — all secrets go through Railway Variables.
- `ROLES_FILE` path in `config.py` resolves via `Path.cwd()` = `/app` at runtime, pointing to `/app/packages/slack-bot/roles.json` which is copied in the Dockerfile. No code change needed.
- `_pathsetup.py` uses `Path(__file__).parents[4]` which resolves to `/app` in the container — correct as long as source layout is preserved (it is, since we copy packages directly rather than installing wheels).
