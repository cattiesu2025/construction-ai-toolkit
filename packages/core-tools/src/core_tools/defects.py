from typing import Any
from core_tools import data_layer


def find_by_type(project_id: str, defect_type: str) -> list[dict[str, Any]]:
    """Find all defects of a specific type in a project.

    Args:
        project_id: Project identifier e.g. 'PRJ-001'
        defect_type: One of 'structural', 'electrical', 'plumbing', 'finish', 'civil'
    """
    df = data_layer.defects()
    filtered = df[(df["project_id"] == project_id) & (df["defect_type"] == defect_type)]

    results = []
    for _, row in filtered.iterrows():
        results.append({
            "defect_id": row["defect_id"],
            "task_id": row["task_id"],
            "severity": row["severity"],
            "description": row["description"],
            "reported_date": row["reported_date"],
            "resolved_date": row.get("resolved_date", "") if str(row.get("resolved_date", "")) != "nan" else None,
            "status": row["status"],
            "cost_to_fix_aud": float(row.get("cost_to_fix_aud", 0) or 0),
        })
    return results


def get_all_for_project(project_id: str) -> dict[str, Any]:
    """Return summary of all defects for a project grouped by severity."""
    df = data_layer.defects()
    project_defects = df[df["project_id"] == project_id]

    if project_defects.empty:
        return {"project_id": project_id, "total": 0, "by_severity": {}}

    open_defects = project_defects[project_defects["status"] == "open"]
    total_cost = project_defects["cost_to_fix_aud"].sum()

    by_severity = {}
    for severity in ["critical", "high", "medium", "low"]:
        count = len(project_defects[project_defects["severity"] == severity])
        if count:
            by_severity[severity] = count

    return {
        "project_id": project_id,
        "total": len(project_defects),
        "open": len(open_defects),
        "by_severity": by_severity,
        "total_remediation_cost_aud": float(total_cost),
    }
