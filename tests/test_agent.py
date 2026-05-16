"""Tests for delay-agent — uses mocks to avoid real API calls."""
import pytest
from unittest.mock import MagicMock, patch


class TestToolHandlers:
    """Test that tool handlers correctly bridge to core_tools."""

    def test_get_schedule_data_tool(self):
        from delay_agent.agent import _TOOL_HANDLERS
        result = _TOOL_HANDLERS["get_schedule_data"](project_id="PRJ-001")
        assert result["project_id"] == "PRJ-001"
        assert "tasks" in result

    def test_analyze_progress_gap_tool(self):
        from delay_agent.agent import _TOOL_HANDLERS
        result = _TOOL_HANDLERS["analyze_progress_gap"](task_id="T003")
        assert result["task_id"] == "T003"
        assert "gap_pct" in result

    def test_check_weather_tool(self):
        from delay_agent.agent import _TOOL_HANDLERS
        result = _TOOL_HANDLERS["check_weather_impact"](
            date_range="2024-11-01 to 2024-11-07", location="Sydney"
        )
        assert "overall_weather_risk" in result
        assert result["overall_weather_risk"] in ("LOW", "MEDIUM", "HIGH", "unknown")

    def test_get_history_delays_tool(self):
        from delay_agent.agent import _TOOL_HANDLERS
        result = _TOOL_HANDLERS["get_history_delays"](task_type="piling", city="Sydney")
        assert result["found"] is True

    def test_send_slack_alert_mock(self):
        from delay_agent.agent import _TOOL_HANDLERS
        result = _TOOL_HANDLERS["send_slack_alert"](
            message="Test alert", severity="HIGH"
        )
        assert "ok" in result


class TestAgentTools:
    """Verify the TOOLS list has correct schema structure."""

    def test_tools_count(self):
        from delay_agent.agent import TOOLS
        assert len(TOOLS) == 5

    def test_all_tools_have_required_fields(self):
        from delay_agent.agent import TOOLS
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "type" in tool["input_schema"]
            assert "required" in tool["input_schema"]

    def test_send_slack_severity_enum(self):
        from delay_agent.agent import TOOLS
        slack_tool = next(t for t in TOOLS if t["name"] == "send_slack_alert")
        severity_schema = slack_tool["input_schema"]["properties"]["severity"]
        assert "enum" in severity_schema
        assert "CRITICAL" in severity_schema["enum"]


class TestNotifier:
    def test_mock_slack_when_no_webhook(self, monkeypatch):
        import delay_agent.config as cfg
        monkeypatch.setattr(cfg, "SLACK_WEBHOOK_URL", "")
        from delay_agent.notifier import send_slack_alert
        result = send_slack_alert("test", "MEDIUM")
        assert result["ok"] is True
        assert result.get("mock") is True

    def test_slack_mock_placeholder_url(self, monkeypatch):
        import delay_agent.config as cfg
        monkeypatch.setattr(cfg, "SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/...")
        from delay_agent.notifier import send_slack_alert
        result = send_slack_alert("test message", "HIGH")
        assert result["ok"] is True


class TestAgentLoop:
    """Test the agent loop logic with a mocked Anthropic client."""

    def _make_tool_use_response(self, tool_name: str, tool_input: dict, tool_id: str = "tu_1"):
        block = MagicMock()
        block.type = "tool_use"
        block.name = tool_name
        block.input = tool_input
        block.id = tool_id
        response = MagicMock()
        response.stop_reason = "tool_use"
        response.content = [block]
        response.usage = MagicMock(input_tokens=100, output_tokens=50, cache_read_input_tokens=0)
        return response

    def _make_end_response(self, text: str = "Risk assessment complete. Severity: LOW."):
        block = MagicMock()
        block.type = "text"
        block.text = text
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [block]
        response.usage = MagicMock(input_tokens=200, output_tokens=100, cache_read_input_tokens=50)
        return response

    def test_agent_returns_on_end_turn(self):
        with patch("delay_agent.agent._client") as mock_client:
            mock_client.messages.create.return_value = self._make_end_response()
            from delay_agent.agent import run_delay_agent
            result = run_delay_agent("PRJ-001")
            assert "summary" in result
            assert result["iterations"] == 1
            assert "token_usage" in result

    def test_agent_handles_tool_call(self):
        tool_resp = self._make_tool_use_response(
            "get_schedule_data", {"project_id": "PRJ-001"}, "tu_1"
        )
        end_resp = self._make_end_response("LOW risk. No alert needed.")
        with patch("delay_agent.agent._client") as mock_client:
            mock_client.messages.create.side_effect = [tool_resp, end_resp]
            from delay_agent.agent import run_delay_agent
            result = run_delay_agent("PRJ-001")
            assert result["iterations"] == 2
            assert "summary" in result

    def test_agent_raises_on_max_iterations(self):
        tool_resp = self._make_tool_use_response(
            "get_schedule_data", {"project_id": "PRJ-001"}, "tu_1"
        )
        with patch("delay_agent.agent._client") as mock_client:
            mock_client.messages.create.return_value = tool_resp
            from delay_agent.agent import run_delay_agent
            with pytest.raises(RuntimeError, match="exceeded"):
                run_delay_agent("PRJ-001", max_iterations=3)

    def test_cost_estimation(self):
        from delay_agent.agent import _estimate_cost
        cost = _estimate_cost(10000, 1000, 5000)
        assert cost > 0
        assert cost < 1.0
