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
