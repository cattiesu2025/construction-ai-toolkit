FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/core-tools ./packages/core-tools
COPY packages/slack-bot ./packages/slack-bot
COPY data ./data
RUN uv sync --package slack-bot --no-dev --frozen
CMD ["uv", "run", "run-slack-bot"]
