"""Tests for the Construction MCP Server — tools, resources, and prompts."""
import pytest


class TestMCPTools:
    def test_find_defects_structural(self):
        from construction_mcp.tools import find_defects_by_type
        results = find_defects_by_type("PRJ-001", "structural")
        assert isinstance(results, list)
        assert len(results) > 0
        assert all("defect_id" in r for r in results)

    def test_find_defects_empty_project(self):
        from construction_mcp.tools import find_defects_by_type
        results = find_defects_by_type("PRJ-999", "structural")
        assert results == []

    def test_check_compliance_returns_risk_level(self):
        from construction_mcp.tools import check_compliance
        result = check_compliance("PRJ-007")
        assert "compliance_risk" in result
        assert result["compliance_risk"] in ("LOW", "MEDIUM", "HIGH")

    def test_lookup_regulation_fire_safety(self):
        from construction_mcp.tools import lookup_regulation
        results = lookup_regulation("fire")
        assert len(results) > 0
        assert all("regulation_code" in r for r in results)

    def test_lookup_regulation_no_match(self):
        from construction_mcp.tools import lookup_regulation
        results = lookup_regulation("xyzzy_impossible")
        assert results == []

    def test_get_schedule_data_returns_tasks(self):
        from construction_mcp.tools import get_schedule_data
        result = get_schedule_data("PRJ-005")
        assert "tasks" in result
        assert result["total_tasks"] > 0

    def test_analyze_progress_gap_returns_estimate(self):
        from construction_mcp.tools import analyze_progress_gap
        result = analyze_progress_gap("T042")
        assert "gap_pct" in result
        assert "delay_days_estimate" in result


class TestMCPResources:
    def test_project_resource_contains_project_name(self):
        from construction_mcp.resources import get_project_summary
        summary = get_project_summary("PRJ-001")
        assert "Harbour View Apartments" in summary
        assert "Sydney" in summary

    def test_project_resource_unknown(self):
        from construction_mcp.resources import get_project_summary
        summary = get_project_summary("PRJ-999")
        assert "not found" in summary.lower()

    def test_schedule_resource_markdown_format(self):
        from construction_mcp.resources import get_schedule_markdown
        md = get_schedule_markdown("PRJ-002")
        assert "|" in md
        assert "Progress" in md

    def test_compliance_resource_shows_status(self):
        from construction_mcp.resources import get_compliance_checklist
        checklist = get_compliance_checklist("PRJ-002")
        assert "HIGH" in checklist or "MEDIUM" in checklist or "LOW" in checklist


class TestMCPPrompts:
    def test_daily_report_template_contains_project_id(self):
        from construction_mcp.prompts import daily_report
        prompt = daily_report("PRJ-001")
        assert "PRJ-001" in prompt
        assert "Harbour View Apartments" in prompt

    def test_risk_assessment_template_has_steps(self):
        from construction_mcp.prompts import risk_assessment
        prompt = risk_assessment("PRJ-003")
        assert "PRJ-003" in prompt
        assert "Melbourne" in prompt

    def test_prompts_are_non_empty(self):
        from construction_mcp.prompts import daily_report, risk_assessment
        for project_id in ["PRJ-001", "PRJ-005", "PRJ-010"]:
            assert len(daily_report(project_id)) > 100
            assert len(risk_assessment(project_id)) > 100


class TestMCPServerImport:
    def test_server_can_be_imported(self):
        from construction_mcp.server import mcp
        assert mcp.name == "construction-tools"

    def test_five_tools_registered(self):
        from construction_mcp import tools
        expected_tools = [
            "find_defects_by_type",
            "check_compliance",
            "lookup_regulation",
            "get_schedule_data",
            "analyze_progress_gap",
        ]
        for tool_name in expected_tools:
            assert hasattr(tools, tool_name), f"Missing tool: {tool_name}"

    def test_three_resources_registered(self):
        from construction_mcp import resources
        assert hasattr(resources, "get_project_summary")
        assert hasattr(resources, "get_schedule_markdown")
        assert hasattr(resources, "get_compliance_checklist")

    def test_two_prompts_registered(self):
        from construction_mcp import prompts
        assert hasattr(prompts, "daily_report")
        assert hasattr(prompts, "risk_assessment")


class TestMCPServerMain:
    def test_main_uses_streamable_http_when_port_set(self, monkeypatch):
        from unittest.mock import patch
        monkeypatch.setenv("PORT", "9001")
        with patch("construction_mcp.server.mcp.run") as mock_run:
            from construction_mcp.server import main, mcp
            main()
            mock_run.assert_called_once_with(transport="streamable-http")
            assert mcp.settings.port == 9001

    def test_main_uses_stdio_when_port_not_set(self, monkeypatch):
        from unittest.mock import patch
        monkeypatch.delenv("PORT", raising=False)
        with patch("construction_mcp.server.mcp.run") as mock_run:
            from construction_mcp.server import main
            main()
            mock_run.assert_called_once_with(transport="stdio")
