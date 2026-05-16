import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

SAMPLE_ROLES = {
    "UADMIN001": {"role": "admin",  "name": "Admin"},
    "UPM000001": {"role": "pm",     "name": "Alice"},
    "UWORKER01": {"role": "worker", "name": "Bob", "crew": "Crew-A"},
}


@pytest.fixture(autouse=True)
def patch_roles_file(tmp_path):
    roles_path = tmp_path / "roles.json"
    roles_path.write_text(json.dumps(SAMPLE_ROLES))
    with patch("slack_bot.roles.ROLES_FILE", roles_path):
        yield


def test_get_role_pm():
    from slack_bot.roles import get_role
    assert get_role("UPM000001") == "pm"


def test_get_role_worker():
    from slack_bot.roles import get_role
    assert get_role("UWORKER01") == "worker"


def test_get_role_unknown_returns_none():
    from slack_bot.roles import get_role
    assert get_role("UNKNOWN") is None


def test_get_crew_for_worker():
    from slack_bot.roles import get_crew
    assert get_crew("UWORKER01") == "Crew-A"


def test_get_crew_for_pm_returns_none():
    from slack_bot.roles import get_crew
    assert get_crew("UPM000001") is None


def test_get_allowed_tool_names_admin():
    from slack_bot.roles import get_allowed_tool_names
    tools = get_allowed_tool_names("admin")
    assert "get_schedule_data" in tools
    assert "check_compliance" in tools
    assert "find_defects_by_type" in tools
    assert len(tools) == 6


def test_get_allowed_tool_names_pm():
    from slack_bot.roles import get_allowed_tool_names
    tools = get_allowed_tool_names("pm")
    assert "get_schedule_data" in tools
    assert "check_compliance" in tools
    assert len(tools) == 6


def test_get_allowed_tool_names_worker():
    from slack_bot.roles import get_allowed_tool_names
    tools = get_allowed_tool_names("worker")
    assert "get_schedule_data" in tools
    assert "analyze_progress_gap" in tools
    assert "check_compliance" not in tools
    assert "find_defects_by_type" not in tools
    assert len(tools) == 2


def test_get_allowed_tool_names_unknown_returns_empty():
    from slack_bot.roles import get_allowed_tool_names
    assert get_allowed_tool_names(None) == []
