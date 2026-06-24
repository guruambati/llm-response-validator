"""
test_reporter.py
================
Tests for Reporter: JSON output structure and file saving.
"""

import json
from pathlib import Path
import pytest
from src.validator.core import LLMResponseValidator
from src.validator.reporter import Reporter
from tests.conftest import make_response


@pytest.fixture
def passing_results(simple_response):
    return LLMResponseValidator(simple_response).not_empty().no_pii().validate()


@pytest.fixture
def mixed_results():
    r = make_response("")
    return LLMResponseValidator(r).not_empty().no_pii().validate()


class TestReporterDict:

    def test_to_dict_has_required_keys(self, passing_results):
        report = Reporter(passing_results, model="gpt-4o").to_dict()
        assert "timestamp" in report
        assert "model" in report
        assert "summary" in report
        assert "results" in report

    def test_summary_counts_correct(self, passing_results):
        report = Reporter(passing_results).to_dict()
        assert report["summary"]["total"] == 2
        assert report["summary"]["passed"] == 2
        assert report["summary"]["failed"] == 0

    def test_pass_rate_is_one_when_all_pass(self, passing_results):
        report = Reporter(passing_results).to_dict()
        assert report["summary"]["pass_rate"] == 1.0

    def test_mixed_results_counted_correctly(self, mixed_results):
        report = Reporter(mixed_results).to_dict()
        assert report["summary"]["failed"] == 1
        assert report["summary"]["passed"] == 1

    def test_results_list_length_matches(self, passing_results):
        report = Reporter(passing_results).to_dict()
        assert len(report["results"]) == 2


class TestReporterSaveJson:

    def test_saves_json_file(self, passing_results, tmp_path):
        output_path = tmp_path / "report.json"
        reporter = Reporter(passing_results, model="test-model")
        saved = reporter.save_json(str(output_path))
        assert saved.exists()

    def test_saved_json_is_valid(self, passing_results, tmp_path):
        output_path = tmp_path / "report.json"
        Reporter(passing_results).save_json(str(output_path))
        loaded = json.loads(output_path.read_text())
        assert "summary" in loaded

    def test_creates_parent_directory(self, passing_results, tmp_path):
        output_path = tmp_path / "nested" / "dir" / "report.json"
        Reporter(passing_results).save_json(str(output_path))
        assert output_path.exists()

    def test_model_name_in_output(self, passing_results, tmp_path):
        output_path = tmp_path / "report.json"
        Reporter(passing_results, model="claude-3-5-sonnet").save_json(str(output_path))
        loaded = json.loads(output_path.read_text())
        assert loaded["model"] == "claude-3-5-sonnet"
