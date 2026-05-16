import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure workspace packages are importable (needed when .pth file processing is unreliable)
_root = Path(__file__).parents[4]
for _pkg in ["core-tools", "delay-agent", "mcp-server"]:
    _src = str(_root / "packages" / _pkg / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)

load_dotenv(Path(__file__).parents[4] / ".env")

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
AGENT_MODEL: str = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")
AGENT_MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
SCHEDULE_CRON: str = os.getenv("SCHEDULE_CRON", "0 7 * * *")
ALERT_THRESHOLD: str = os.getenv("ALERT_THRESHOLD", "MEDIUM")
