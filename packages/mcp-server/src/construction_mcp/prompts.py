"""MCP prompt templates — user-selectable workflow starters."""
import construction_mcp._pathsetup  # noqa: F401
from core_tools import data_layer


def daily_report(project_id: str) -> str:
    projects = data_layer.projects()
    row = projects[projects["project_id"] == project_id]
    name = row.iloc[0]["project_name"] if not row.empty else project_id

    return (
        f"Generate a professional construction site daily report for **{name}** ({project_id}).\n\n"
        f"Use the available tools to:\n"
        f"1. Load the full project context using the resource `project://{project_id}`\n"
        f"2. Call `get_schedule_data` to retrieve today's progress status\n"
        f"3. Check for any open defects by calling `find_defects_by_type` for structural and electrical\n"
        f"4. Review compliance status with `check_compliance`\n\n"
        f"Format the report with sections: Executive Summary, Schedule Status, "
        f"Defects & Quality, Compliance, Weather Considerations, Tomorrow's Priorities.\n"
        f"Tone: professional, factual, suitable for a client-facing report."
    )


def risk_assessment(project_id: str) -> str:
    projects = data_layer.projects()
    row = projects[projects["project_id"] == project_id]
    name = row.iloc[0]["project_name"] if not row.empty else project_id
    city = row.iloc[0]["city"] if not row.empty else "Sydney"

    return (
        f"Run a comprehensive risk assessment for **{name}** ({project_id}) in {city}.\n\n"
        f"Step-by-step analysis:\n"
        f"1. `get_schedule_data({project_id!r})` — identify all overdue and at-risk tasks\n"
        f"2. For each overdue critical-path task, call `analyze_progress_gap` for delay quantification\n"
        f"3. `check_compliance({project_id!r})` — flag any regulatory non-compliance\n"
        f"4. `find_defects_by_type` for structural, electrical, and plumbing defects\n"
        f"5. Check weather for the next 7 days in {city} using the weather tool if available\n\n"
        f"Output format:\n"
        f"- **Overall Risk Rating** (LOW / MEDIUM / HIGH / CRITICAL) with justification\n"
        f"- **Top 3 Risks** with root cause and quantified impact (days, AUD)\n"
        f"- **Recommended Actions** with responsible party and deadline\n"
        f"- **Risk Register Table** covering all identified issues"
    )
