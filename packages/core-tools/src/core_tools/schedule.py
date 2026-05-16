from datetime import date
from typing import Any
import pandas as pd
from core_tools import data_layer


def get_schedule_data(project_id: str) -> dict[str, Any]:
    """Return planned vs actual schedule for all tasks in a project."""
    df = data_layer.tasks()
    project_tasks = df[df["project_id"] == project_id].copy()

    if project_tasks.empty:
        return {"error": f"No tasks found for project {project_id}"}

    today = date.today().isoformat()
    records = []
    for _, row in project_tasks.iterrows():
        planned_end = row.get("planned_end", "")
        progress = row.get("actual_progress_pct", 0)
        if pd.isna(progress):
            progress = 0

        overdue = False
        if planned_end and str(planned_end) < today and float(progress) < 100:
            overdue = True

        records.append({
            "task_id": row["task_id"],
            "task_name": row["task_name"],
            "task_type": row["task_type"],
            "planned_start": row["planned_start"],
            "planned_end": row["planned_end"],
            "actual_start": row.get("actual_start", None) if not pd.isna(row.get("actual_start", float("nan"))) else None,
            "actual_end": row.get("actual_end", None) if not pd.isna(row.get("actual_end", float("nan"))) else None,
            "progress_pct": float(progress),
            "is_critical_path": bool(row.get("is_critical_path", False)),
            "overdue": overdue,
            "crew": row.get("assigned_crew", ""),
        })

    critical_overdue = [r for r in records if r["overdue"] and r["is_critical_path"]]
    return {
        "project_id": project_id,
        "total_tasks": len(records),
        "overdue_tasks": len([r for r in records if r["overdue"]]),
        "critical_path_overdue": len(critical_overdue),
        "tasks": records,
        "as_of": today,
    }


def analyze_progress_gap(task_id: str) -> dict[str, Any]:
    """Analyse the deviation between planned and actual progress for a task."""
    df = data_layer.tasks()
    rows = df[df["task_id"] == task_id]

    if rows.empty:
        return {"error": f"Task {task_id} not found"}

    row = rows.iloc[0]
    today = date.today()

    planned_start = pd.to_datetime(row["planned_start"]).date()
    planned_end = pd.to_datetime(row["planned_end"]).date()
    planned_duration = (planned_end - planned_start).days

    actual_start_raw = row.get("actual_start")
    actual_start = pd.to_datetime(actual_start_raw).date() if not pd.isna(actual_start_raw) else None

    progress = float(row.get("actual_progress_pct", 0) or 0)

    # Expected progress based on elapsed time
    if actual_start:
        elapsed = (today - actual_start).days
        expected_pct = min(100.0, (elapsed / planned_duration) * 100) if planned_duration > 0 else 100.0
    else:
        elapsed = 0
        expected_pct = 0.0

    gap_pct = expected_pct - progress

    # Projected end date based on current velocity
    if progress > 0 and actual_start:
        days_per_pct = elapsed / progress
        remaining_pct = 100 - progress
        projected_end = today + pd.Timedelta(days=int(days_per_pct * remaining_pct))
        delay_days = max(0, (projected_end.date() if hasattr(projected_end, "date") else projected_end - planned_end).days)
    else:
        projected_end = None
        delay_days = 0

    downstream = _get_downstream_tasks(task_id, row["project_id"])

    return {
        "task_id": task_id,
        "task_name": row["task_name"],
        "task_type": row["task_type"],
        "is_critical_path": bool(row.get("is_critical_path", False)),
        "planned_duration_days": planned_duration,
        "elapsed_days": elapsed,
        "progress_pct": progress,
        "expected_progress_pct": round(expected_pct, 1),
        "gap_pct": round(gap_pct, 1),
        "projected_end": str(projected_end) if projected_end else None,
        "planned_end": str(planned_end),
        "delay_days_estimate": delay_days,
        "downstream_tasks_at_risk": downstream,
        "notes": row.get("notes", "") if not pd.isna(row.get("notes", float("nan"))) else "",
    }


def _get_downstream_tasks(task_id: str, project_id: str) -> list[str]:
    """Return names of tasks that haven't started yet in the same project (simplified dependency model)."""
    df = data_layer.tasks()
    project_tasks = df[df["project_id"] == project_id]
    not_started = project_tasks[
        project_tasks["actual_progress_pct"].isna() | (project_tasks["actual_progress_pct"] == 0)
    ]
    return list(not_started["task_name"].head(3))
