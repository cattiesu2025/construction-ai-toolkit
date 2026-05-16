from typing import Any
from core_tools import data_layer


def check_compliance(project_id: str) -> dict[str, Any]:
    """Check compliance status for a project against all registered regulations."""
    df = data_layer.compliance()
    project_compliance = df[df["project_id"] == project_id]

    if project_compliance.empty:
        return {"error": f"No compliance records for project {project_id}"}

    by_status: dict[str, list] = {"compliant": [], "non_compliant": [], "in_review": []}
    for _, row in project_compliance.iterrows():
        status = row["status"]
        entry = {
            "regulation_code": row["regulation_code"],
            "regulation_name": row["regulation_name"],
            "category": row["category"],
            "due_date": row["due_date"],
            "responsible_party": row["responsible_party"],
            "notes": row.get("notes", "") if str(row.get("notes", "")) != "nan" else "",
        }
        if status in by_status:
            by_status[status].append(entry)

    risk_level = "LOW"
    if by_status["non_compliant"]:
        risk_level = "HIGH"
    elif by_status["in_review"]:
        risk_level = "MEDIUM"

    return {
        "project_id": project_id,
        "total_requirements": len(project_compliance),
        "compliant": len(by_status["compliant"]),
        "non_compliant": len(by_status["non_compliant"]),
        "in_review": len(by_status["in_review"]),
        "compliance_risk": risk_level,
        "non_compliant_items": by_status["non_compliant"],
        "in_review_items": by_status["in_review"],
    }


def lookup_regulation(keyword: str) -> list[dict[str, Any]]:
    """Search compliance records for regulations matching a keyword."""
    df = data_layer.compliance()
    keyword_lower = keyword.lower()

    mask = (
        df["regulation_code"].str.lower().str.contains(keyword_lower, na=False)
        | df["regulation_name"].str.lower().str.contains(keyword_lower, na=False)
        | df["category"].str.lower().str.contains(keyword_lower, na=False)
    )
    matches = df[mask]

    results = []
    for _, row in matches.iterrows():
        results.append({
            "regulation_code": row["regulation_code"],
            "regulation_name": row["regulation_name"],
            "category": row["category"],
            "project_id": row["project_id"],
            "status": row["status"],
            "responsible_party": row["responsible_party"],
        })
    return results
