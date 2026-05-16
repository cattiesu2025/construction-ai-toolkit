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
