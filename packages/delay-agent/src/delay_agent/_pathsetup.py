"""Ensure workspace packages are importable regardless of .pth file processing."""
import sys
from pathlib import Path

_root = Path(__file__).parents[4]
for _pkg in ["core-tools", "delay-agent", "mcp-server"]:
    _src = str(_root / "packages" / _pkg / "src")
    if _src not in sys.path:
        sys.path.insert(0, _src)
