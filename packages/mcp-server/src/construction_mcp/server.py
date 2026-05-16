import construction_mcp._pathsetup  # noqa: F401 — must be first import
from mcp.server.fastmcp import FastMCP
from construction_mcp import tools, resources, prompts

mcp = FastMCP("construction-tools")


# ============ TOOLS ============

@mcp.tool()
def find_defects_by_type(project_id: str, defect_type: str) -> list[dict]:
    """Find all defects of a specific type in a project.

    Args:
        project_id: The project identifier e.g. 'PRJ-001'
        defect_type: Type of defect — 'structural', 'electrical', 'plumbing', 'finish', 'civil'
    """
    return tools.find_defects_by_type(project_id, defect_type)


@mcp.tool()
def check_compliance(project_id: str) -> dict:
    """Check compliance status for an Australian construction project against NCC and state standards.

    Args:
        project_id: The project identifier e.g. 'PRJ-001'
    """
    return tools.check_compliance(project_id)


@mcp.tool()
def lookup_regulation(keyword: str) -> list[dict]:
    """Search for Australian National Construction Code (NCC) or state regulations by keyword.

    Args:
        keyword: Search keyword e.g. 'fire safety', 'structural', 'WHS', 'heritage'
    """
    return tools.lookup_regulation(keyword)


@mcp.tool()
def get_schedule_data(project_id: str) -> dict:
    """Get planned vs actual schedule for all tasks in a project.

    Args:
        project_id: The project identifier e.g. 'PRJ-001'
    """
    return tools.get_schedule_data(project_id)


@mcp.tool()
def analyze_progress_gap(task_id: str) -> dict:
    """Analyse the deviation between planned and actual progress for a specific task.

    Args:
        task_id: Task ID e.g. 'T003'
    """
    return tools.analyze_progress_gap(task_id)


# ============ RESOURCES ============

@mcp.resource("project://{project_id}")
def project_resource(project_id: str) -> str:
    """Full project context — load when discussing a specific project.

    Provides: project details, schedule summary, compliance overview.
    """
    return resources.get_project_summary(project_id)


@mcp.resource("schedule://{project_id}")
def schedule_resource(project_id: str) -> str:
    """Project schedule as a markdown table with overdue indicators."""
    return resources.get_schedule_markdown(project_id)


@mcp.resource("compliance://{project_id}")
def compliance_resource(project_id: str) -> str:
    """Project compliance checklist with pass/fail/review status for all regulations."""
    return resources.get_compliance_checklist(project_id)


# ============ PROMPTS ============

@mcp.prompt()
def daily_report_template(project_id: str) -> str:
    """Generate today's site daily report for a project."""
    return prompts.daily_report(project_id)


@mcp.prompt()
def risk_assessment_template(project_id: str) -> str:
    """Run a comprehensive risk assessment for a project."""
    return prompts.risk_assessment(project_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
