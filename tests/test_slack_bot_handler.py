import pytest
from unittest.mock import patch, MagicMock


def _make_end_turn_response(text="All good."):
    response = MagicMock()
    response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = text
    text_block.type = "text"
    response.content = [text_block]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    response.usage.cache_read_input_tokens = 0
    return response


def _make_tool_use_response(tool_name, tool_input, tool_id="tool_1"):
    response = MagicMock()
    response.stop_reason = "tool_use"
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = tool_id
    response.content = [block]
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    response.usage.cache_read_input_tokens = 0
    return response


def test_handle_unknown_user_returns_access_denied():
    from slack_bot.handler import handle_mention
    with patch("slack_bot.handler.roles.get_role", return_value=None):
        result = handle_mention(user_id="UNKNOWN", text="PRJ-001 risks?")
    assert "access" in result.lower() or "denied" in result.lower() or "permission" in result.lower()


def test_handle_pm_calls_claude_with_filtered_tools():
    from slack_bot.handler import handle_mention
    with patch("slack_bot.handler.roles.get_role", return_value="pm"), \
         patch("slack_bot.handler.roles.get_crew", return_value=None), \
         patch("slack_bot.handler.roles.get_allowed_tool_names", return_value=["get_schedule_data"]), \
         patch("slack_bot.handler._client.messages.create", return_value=_make_end_turn_response("Summary here.")) as mock_create:
        result = handle_mention(user_id="UPM000001", text="PRJ-001 risks?")
    assert result == "Summary here."
    call_kwargs = mock_create.call_args.kwargs
    assert len(call_kwargs["tools"]) == 1
    assert call_kwargs["tools"][0]["name"] == "get_schedule_data"


def test_handle_executes_tool_call_and_returns_result():
    from slack_bot.handler import handle_mention
    tool_response = _make_tool_use_response("get_schedule_data", {"project_id": "PRJ-001"})
    end_response = _make_end_turn_response("No delays found.")

    with patch("slack_bot.handler.roles.get_role", return_value="pm"), \
         patch("slack_bot.handler.roles.get_crew", return_value=None), \
         patch("slack_bot.handler.roles.get_allowed_tool_names", return_value=["get_schedule_data"]), \
         patch("slack_bot.handler._client.messages.create", side_effect=[tool_response, end_response]), \
         patch("slack_bot.handler.dispatch", return_value={"tasks": []}) as mock_dispatch:
        result = handle_mention(user_id="UPM000001", text="PRJ-001 risks?")
    mock_dispatch.assert_called_once_with("get_schedule_data", {"project_id": "PRJ-001"}, crew=None)
    assert result == "No delays found."
