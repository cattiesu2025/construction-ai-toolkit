import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# When installed as a wheel, __file__ points to site-packages — use find_dotenv()
# to locate .env by searching up from cwd instead of relative to __file__.
_dotenv_path = find_dotenv(usecwd=True)
load_dotenv(_dotenv_path)

# For local dev (source layout), also resolve project root for ROLES_FILE path.
_root = Path(_dotenv_path).parent if _dotenv_path else Path.cwd()

for _pkg in ["core-tools", "slack-bot"]:
    _src = str(_root / "packages" / _pkg / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
SLACK_BOT_TOKEN: str | None = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN: str | None = os.getenv("SLACK_APP_TOKEN")
BOT_MODEL: str = os.getenv("BOT_MODEL", "claude-opus-4-7")

ROLES_FILE: Path = _root / "packages" / "slack-bot" / "roles.json"
