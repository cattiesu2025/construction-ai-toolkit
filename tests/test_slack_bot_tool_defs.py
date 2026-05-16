def test_all_tools_have_required_keys():
    from slack_bot.tool_defs import ALL_TOOLS
    for tool in ALL_TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


def test_all_tools_count():
    from slack_bot.tool_defs import ALL_TOOLS
    assert len(ALL_TOOLS) == 6


def test_filter_tools_for_worker():
    from slack_bot.tool_defs import filter_tools
    tools = filter_tools(["get_schedule_data", "analyze_progress_gap"])
    assert len(tools) == 2
    names = [t["name"] for t in tools]
    assert "get_schedule_data" in names
    assert "check_compliance" not in names


def test_filter_tools_empty_returns_empty():
    from slack_bot.tool_defs import filter_tools
    assert filter_tools([]) == []


def test_filter_tools_all():
    from slack_bot.tool_defs import ALL_TOOLS, filter_tools
    all_names = [t["name"] for t in ALL_TOOLS]
    assert filter_tools(all_names) == ALL_TOOLS
