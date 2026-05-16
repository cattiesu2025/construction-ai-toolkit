import pytest
from unittest.mock import patch, MagicMock


def test_dispatch_get_schedule_data():
    from slack_bot.dispatcher import dispatch
    mock_result = {"project_id": "PRJ-001", "tasks": []}
    with patch("slack_bot.dispatcher._schedule.get_schedule_data", return_value=mock_result) as mock_fn:
        result = dispatch("get_schedule_data", {"project_id": "PRJ-001"}, crew=None)
    mock_fn.assert_called_once_with(project_id="PRJ-001")
    assert result == mock_result


def test_dispatch_get_schedule_data_filters_by_crew():
    from slack_bot.dispatcher import dispatch
    tasks = [
        {"task_id": "T001", "crew": "Crew-A"},
        {"task_id": "T002", "crew": "Crew-B"},
    ]
    mock_result = {"project_id": "PRJ-001", "tasks": tasks, "total_tasks": 2}
    with patch("slack_bot.dispatcher._schedule.get_schedule_data", return_value=mock_result):
        result = dispatch("get_schedule_data", {"project_id": "PRJ-001"}, crew="Crew-A")
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["task_id"] == "T001"


def test_dispatch_analyze_progress_gap():
    from slack_bot.dispatcher import dispatch
    mock_result = {"task_id": "T003", "gap_pct": 15.0}
    with patch("slack_bot.dispatcher._schedule.analyze_progress_gap", return_value=mock_result) as mock_fn:
        result = dispatch("analyze_progress_gap", {"task_id": "T003"}, crew=None)
    mock_fn.assert_called_once_with(task_id="T003")
    assert result == mock_result


def test_dispatch_check_compliance():
    from slack_bot.dispatcher import dispatch
    mock_result = {"compliance_risk": "MEDIUM"}
    with patch("slack_bot.dispatcher._compliance.check_compliance", return_value=mock_result) as mock_fn:
        result = dispatch("check_compliance", {"project_id": "PRJ-001"}, crew=None)
    mock_fn.assert_called_once_with(project_id="PRJ-001")
    assert result == mock_result


def test_dispatch_unknown_tool_raises():
    from slack_bot.dispatcher import dispatch
    with pytest.raises(KeyError):
        dispatch("nonexistent_tool", {}, crew=None)
