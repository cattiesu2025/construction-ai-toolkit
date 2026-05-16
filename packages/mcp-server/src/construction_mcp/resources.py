"""MCP resource handlers — read-only project context loaders."""
import construction_mcp._pathsetup  # noqa: F401
from core_tools import data_layer, compliance as compliance_tools, schedule as schedule_tools


def get_project_summary(project_id: str) -> str:
    projects = data_layer.projects()
    row = projects[projects["project_id"] == project_id]
    if row.empty:
        return f"Project {project_id} not found."

    p = row.iloc[0]
    schedule = schedule_tools.get_schedule_data(project_id)
    comp = compliance_tools.check_compliance(project_id)

    lines = [
        f"# Project: {p['project_name']} ({project_id})",
        f"**Client:** {p['client']}",
        f"**Location:** {p['city']} — {p['location']}",
        f"**Type:** {p['project_type']}",
        f"**Timeline:** {p['start_date']} → {p['planned_end_date']}",
        f"**Budget:** AUD ${p['budget_aud']:,.0f}",
        f"**Project Manager:** {p['project_manager']}",
        "",
        f"## Schedule Status",
        f"- Total tasks: {schedule['total_tasks']}",
        f"- Overdue tasks: {schedule['overdue_tasks']}",
        f"- Critical path overdue: {schedule['critical_path_overdue']}",
        "",
        f"## Compliance Status",
        f"- Risk level: **{comp['compliance_risk']}**",
        f"- Compliant: {comp['compliant']} | Non-compliant: {comp['non_compliant']} | In review: {comp['in_review']}",
    ]

    if comp["non_compliant_items"]:
        lines.append("")
        lines.append("### Non-Compliant Items")
        for item in comp["non_compliant_items"]:
            lines.append(f"- **{item['regulation_code']}**: {item['regulation_name']} ({item['responsible_party']})")

    return "\n".join(lines)


def get_schedule_markdown(project_id: str) -> str:
    data = schedule_tools.get_schedule_data(project_id)
    if "error" in data:
        return data["error"]

    lines = [
        f"# Schedule — {project_id}",
        f"*As of {data['as_of']} | {data['overdue_tasks']}/{data['total_tasks']} overdue*",
        "",
        "| Task | Type | Planned End | Progress | Critical | Overdue |",
        "|------|------|-------------|----------|----------|---------|",
    ]
    for t in data["tasks"]:
        overdue_flag = "⚠️" if t["overdue"] else ""
        critical_flag = "✓" if t["is_critical_path"] else ""
        lines.append(
            f"| {t['task_name']} | {t['task_type']} | {t['planned_end']} | {t['progress_pct']:.0f}% | {critical_flag} | {overdue_flag} |"
        )
    return "\n".join(lines)


def get_compliance_checklist(project_id: str) -> str:
    comp = compliance_tools.check_compliance(project_id)
    if "error" in comp:
        return comp["error"]

    status_icon = {"compliant": "✅", "non_compliant": "❌", "in_review": "🔄"}
    lines = [
        f"# Compliance Checklist — {project_id}",
        f"**Overall Risk: {comp['compliance_risk']}** | {comp['compliant']} compliant | {comp['non_compliant']} non-compliant | {comp['in_review']} in review",
        "",
    ]
    for item in comp.get("non_compliant_items", []):
        icon = status_icon["non_compliant"]
        lines.append(f"{icon} **{item['regulation_code']}** — {item['regulation_name']}")
        if item["notes"]:
            lines.append(f"  > {item['notes']}")
    for item in comp.get("in_review_items", []):
        icon = status_icon["in_review"]
        lines.append(f"{icon} **{item['regulation_code']}** — {item['regulation_name']}")
        if item["notes"]:
            lines.append(f"  > {item['notes']}")

    return "\n".join(lines)
