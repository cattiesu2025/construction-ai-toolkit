FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/core-tools ./packages/core-tools
COPY packages/mcp-server ./packages/mcp-server
COPY data ./data
RUN uv sync --package construction-mcp-server --no-dev --frozen
CMD ["uv", "run", "construction-mcp"]
