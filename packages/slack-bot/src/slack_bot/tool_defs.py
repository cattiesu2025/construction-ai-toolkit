import slack_bot.config  # noqa: F401

ALL_TOOLS: list[dict] = [
    {
        "name": "get_schedule_data",
        "description": "Get planned vs actual progress for all tasks in a construction project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "analyze_progress_gap",
        "description": "Analyse deviation between planned and actual progress for a specific task, returning delay estimate and downstream impact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID e.g. T003"}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "get_all_defects",
        "description": "Return a summary of all defects for a project grouped by severity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "find_defects_by_type",
        "description": "Find all defects of a specific type in a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"},
                "defect_type": {
                    "type": "string",
                    "enum": ["structural", "electrical", "plumbing", "finish", "civil"],
                    "description": "Type of defect to filter by",
                },
            },
            "required": ["project_id", "defect_type"],
        },
    },
    {
        "name": "check_compliance",
        "description": "Check compliance status for a project against all registered regulations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "lookup_regulation",
        "description": "Search compliance records for regulations matching a keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Keyword to search e.g. 'asbestos', 'fire'"}
            },
            "required": ["keyword"],
        },
    },
]

_TOOL_INDEX: dict[str, dict] = {t["name"]: t for t in ALL_TOOLS}


def filter_tools(allowed_names: list[str]) -> list[dict]:
    return [_TOOL_INDEX[name] for name in allowed_names if name in _TOOL_INDEX]
