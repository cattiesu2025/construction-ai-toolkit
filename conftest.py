"""Root conftest.py — ensures all workspace packages are importable in pytest."""
import sys
from pathlib import Path

root = Path(__file__).parent
for pkg in ["core-tools", "delay-agent", "mcp-server", "slack-bot"]:
    src = str(root / "packages" / pkg / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
