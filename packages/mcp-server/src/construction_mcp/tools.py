"""MCP tool implementations — thin wrappers over core_tools."""
import construction_mcp._pathsetup  # noqa: F401
from core_tools import defects as defects_tools
from core_tools import compliance as compliance_tools
from core_tools import schedule as schedule_tools


def find_defects_by_type(project_id: str, defect_type: str) -> list[dict]:
    return defects_tools.find_by_type(project_id, defect_type)


def check_compliance(project_id: str) -> dict:
    return compliance_tools.check_compliance(project_id)


def lookup_regulation(keyword: str) -> list[dict]:
    return compliance_tools.lookup_regulation(keyword)


def get_schedule_data(project_id: str) -> dict:
    return schedule_tools.get_schedule_data(project_id)


def analyze_progress_gap(task_id: str) -> dict:
    return schedule_tools.analyze_progress_gap(task_id)
