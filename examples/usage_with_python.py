"""Programmatic usage examples for the construction AI toolkit."""

# ============================================================
# Example 1: Run the delay detection agent for a single project
# ============================================================
from delay_agent.agent import run_delay_agent

result = run_delay_agent("PRJ-001")
print(f"Severity assessment complete in {result['iterations']} iterations")
print(f"Estimated cost: ${result['token_usage']['estimated_cost_usd']:.4f}")
print(result["summary"])


# ============================================================
# Example 2: Use core-tools directly (without the agent)
# ============================================================
from core_tools import schedule, compliance, defects

# Check project schedule
sched = schedule.get_schedule_data("PRJ-003")
print(f"\nPRJ-003: {sched['overdue_tasks']}/{sched['total_tasks']} tasks overdue")

# Analyse a specific task gap
gap = schedule.analyze_progress_gap("T015")
print(f"T015 is {gap['gap_pct']}% behind expected progress ({gap['delay_days_estimate']} day delay estimate)")

# Check compliance
comp = compliance.check_compliance("PRJ-002")
print(f"\nPRJ-002 compliance: {comp['compliance_risk']} risk, {comp['non_compliant']} non-compliant items")

# List open defects
structural_defects = defects.find_by_type("PRJ-003", "structural")
print(f"PRJ-003 structural defects: {len(structural_defects)} found")


# ============================================================
# Example 3: Access MCP resources directly (same data, resource format)
# ============================================================
from construction_mcp.resources import get_project_summary, get_schedule_markdown

print("\n--- Project Summary (MCP resource format) ---")
print(get_project_summary("PRJ-001"))

print("\n--- Schedule Markdown (MCP resource format) ---")
print(get_schedule_markdown("PRJ-005"))
