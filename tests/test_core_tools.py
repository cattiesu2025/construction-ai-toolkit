"""Tests for core_tools business logic — no external API calls."""
import pytest
from core_tools import schedule, history, compliance, defects, data_layer


class TestDataLayer:
    def test_projects_loads(self):
        df = data_layer.projects()
        assert len(df) == 10
        assert "project_id" in df.columns

    def test_tasks_loads(self):
        df = data_layer.tasks()
        assert len(df) > 0
        assert "task_id" in df.columns

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            data_layer._load("nonexistent.csv")


class TestSchedule:
    def test_get_schedule_valid_project(self):
        result = schedule.get_schedule_data("PRJ-001")
        assert result["project_id"] == "PRJ-001"
        assert result["total_tasks"] == 8
        assert "tasks" in result
        assert result["overdue_tasks"] >= 0

    def test_get_schedule_unknown_project(self):
        result = schedule.get_schedule_data("PRJ-999")
        assert "error" in result

    def test_analyze_gap_valid_task(self):
        result = schedule.analyze_progress_gap("T003")
        assert result["task_id"] == "T003"
        assert "gap_pct" in result
        assert "delay_days_estimate" in result
        assert result["is_critical_path"] is True

    def test_analyze_gap_unknown_task(self):
        result = schedule.analyze_progress_gap("T999")
        assert "error" in result

    def test_overdue_detection(self):
        result = schedule.get_schedule_data("PRJ-001")
        overdue_tasks = [t for t in result["tasks"] if t["overdue"]]
        assert len(overdue_tasks) > 0

    def test_critical_path_flagged(self):
        result = schedule.get_schedule_data("PRJ-001")
        critical = [t for t in result["tasks"] if t["is_critical_path"]]
        assert len(critical) > 0


class TestHistory:
    def test_known_type_and_city(self):
        result = history.get_history_delays("piling", "Sydney")
        assert result["found"] is True
        assert result["avg_delay_days"] > 0
        assert result["delay_frequency_pct"] > 0
        assert len(result["common_causes"]) > 0

    def test_unknown_type(self):
        result = history.get_history_delays("unknown_task_type")
        assert result["found"] is False

    def test_city_fallback(self):
        result = history.get_history_delays("piling", "Darwin")
        assert result["found"] is True

    def test_different_cities_have_different_data(self):
        sydney = history.get_history_delays("concrete", "Sydney")
        melbourne = history.get_history_delays("concrete", "Melbourne")
        assert sydney["found"] and melbourne["found"]
        # Melbourne concrete has higher average delays (winter weather)
        assert melbourne["avg_delay_days"] >= sydney["avg_delay_days"]


class TestCompliance:
    def test_check_compliance_valid(self):
        result = compliance.check_compliance("PRJ-002")
        assert result["project_id"] == "PRJ-002"
        assert result["compliance_risk"] in ("LOW", "MEDIUM", "HIGH")
        assert result["non_compliant"] >= 1

    def test_non_compliant_project_is_high_risk(self):
        result = compliance.check_compliance("PRJ-002")
        assert result["compliance_risk"] == "HIGH"

    def test_unknown_project(self):
        result = compliance.check_compliance("PRJ-999")
        assert "error" in result

    def test_lookup_regulation_finds_results(self):
        results = compliance.lookup_regulation("fire")
        assert len(results) > 0
        for r in results:
            assert "regulation_code" in r

    def test_lookup_regulation_no_match(self):
        results = compliance.lookup_regulation("xyzzy_nonexistent")
        assert results == []


class TestDefects:
    def test_find_by_type_structural(self):
        results = defects.find_by_type("PRJ-001", "structural")
        assert len(results) > 0
        for d in results:
            assert d["defect_id"].startswith("D")
            assert "severity" in d

    def test_find_by_type_no_match(self):
        results = defects.find_by_type("PRJ-999", "structural")
        assert results == []

    def test_get_all_for_project(self):
        result = defects.get_all_for_project("PRJ-003")
        assert result["total"] > 0
        assert "by_severity" in result

    def test_critical_defects_exist(self):
        result = defects.get_all_for_project("PRJ-003")
        assert result["by_severity"].get("critical", 0) >= 1
