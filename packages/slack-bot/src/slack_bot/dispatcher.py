import slack_bot.config  # noqa: F401
from core_tools import schedule as _schedule
from core_tools import defects as _defects
from core_tools import compliance as _compliance


def dispatch(tool_name: str, tool_input: dict, crew: str | None) -> object:
    """Execute a tool call and return the result.

    crew is only used to post-filter get_schedule_data results for workers.
    """
    handlers = {
        "get_schedule_data":    lambda: _schedule.get_schedule_data(**tool_input),
        "analyze_progress_gap": lambda: _schedule.analyze_progress_gap(**tool_input),
        "get_all_defects":      lambda: _defects.get_all_for_project(**tool_input),
        "find_defects_by_type": lambda: _defects.find_by_type(**tool_input),
        "check_compliance":     lambda: _compliance.check_compliance(**tool_input),
        "lookup_regulation":    lambda: _compliance.lookup_regulation(**tool_input),
    }

    result = handlers[tool_name]()

    if tool_name == "get_schedule_data" and crew and isinstance(result, dict):
        result = dict(result)
        result["tasks"] = [t for t in result.get("tasks", []) if t.get("crew") == crew]

    return result
