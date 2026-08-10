"""Tests for the Tool base class and the tools that lean hardest on it.

The base class owns availability checks, timeouts, file caps and summaries. Those
are exercised through a stub tool so the results do not depend on which linters
happen to be installed; the tool-specific classes cover their own metadata.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from codeflow_engine.actions.quality_engine.tools.semgrep_tool import SemgrepTool
from codeflow_engine.actions.quality_engine.tools.tool_base import Tool
from codeflow_engine.actions.quality_engine.tools.windows_security_tool import (
    WindowsSecurityTool,
)


class StubTool(Tool):
    """A tool with no external command, so it is always available."""

    @property
    def name(self) -> str:
        return "stub_tool_name"

    @property
    def description(self) -> str:
        return "Stub description"

    async def run(self, files: list[str], config: dict[str, Any]) -> list[Any]:
        return []


class TestToolDefaults:
    """Metadata and configuration the base class derives."""

    def test_base_defaults(self):
        tool = StubTool()

        assert tool.category == "general"
        assert tool.timeout == 60.0
        assert tool.max_files == 100
        assert tool.is_available() is True
        assert tool.get_required_command() is None

    def test_display_name_expands_underscores(self):
        assert StubTool().get_display_name() == "Stub Tool Name"
        assert SemgrepTool().get_display_name() == "Semgrep"

    def test_string_representation(self):
        tool = SemgrepTool()

        assert str(tool) == "Semgrep (security)"
        assert repr(tool) == "SemgrepTool(name='semgrep', category='security')"

    def test_config_schema_reports_the_tools_own_limits(self):
        tool = SemgrepTool()

        schema = tool.get_config_schema()

        assert set(schema) == {"timeout", "max_files", "verbose"}
        assert schema["timeout"]["default"] == tool.timeout
        assert schema["max_files"]["default"] == tool.max_files
        assert schema["verbose"]["default"] is False
        assert "Semgrep" in schema["timeout"]["description"]

    def test_performance_metrics_report_the_tools_own_limits(self):
        tool = SemgrepTool()

        metrics = tool.get_performance_metrics()

        assert metrics["recommended_timeout"] == tool.timeout
        assert metrics["recommended_max_files"] == tool.max_files
        assert metrics["category"] == "security"
        assert "static analysis" in metrics["description"]

    def test_config_validation_accepts_valid_config(self):
        tool = StubTool()

        assert tool.validate_config({}) == []
        assert tool.validate_config({"timeout": 5.0, "max_files": 10}) == []

    def test_config_validation_rejects_a_non_positive_timeout(self):
        errors = StubTool().validate_config({"timeout": -1})

        assert len(errors) == 1
        assert "positive number" in errors[0]

    def test_config_validation_rejects_a_non_positive_file_cap(self):
        errors = StubTool().validate_config({"max_files": 0})

        assert len(errors) == 1
        assert "positive integer" in errors[0]

    def test_config_validation_rejects_a_non_mapping(self):
        errors = StubTool().validate_config("not a dict")

        assert len(errors) == 1
        assert "dictionary" in errors[0]


class TestToolExecution:
    """run_with_timeout wraps run() with availability, timeout and error handling."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        tool = StubTool()

        with patch.object(tool, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [{"issue": "test"}]

            result = await tool.run_with_timeout(["test.py"], {})

        assert result["success"] is True
        assert result["issues"] == [{"issue": "test"}]
        assert result["execution_time"] > 0
        assert result["error_message"] is None
        assert result["warnings"] == []
        assert "1 issue found" in result["output_summary"]

    @pytest.mark.asyncio
    async def test_unavailable_tool_is_not_run(self):
        tool = StubTool()

        with (
            patch.object(tool, "is_available", return_value=False),
            patch.object(tool, "run", new_callable=AsyncMock) as mock_run,
        ):
            result = await tool.run_with_timeout(["test.py"], {})

        mock_run.assert_not_awaited()
        assert result["success"] is False
        assert "not available" in result["error_message"]

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        tool = StubTool()
        tool.default_timeout = 0.1  # Very short timeout for testing

        async def slow_run(files, config):
            await asyncio.sleep(1)  # Sleep longer than timeout
            return []

        with patch.object(tool, "run", side_effect=slow_run):
            result = await tool.run_with_timeout(["test.py"], {})

        assert result["success"] is False
        assert "timed out" in result["error_message"]
        assert result["execution_time"] >= 0.1

    @pytest.mark.asyncio
    async def test_error_handling(self):
        tool = StubTool()

        async def failing_run(files, config):
            msg = "Test error"
            raise Exception(msg)

        with patch.object(tool, "run", side_effect=failing_run):
            result = await tool.run_with_timeout(["test.py"], {})

        assert result["success"] is False
        assert "Test error" in result["error_message"]
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_file_limit_warning(self):
        tool = StubTool()
        tool.max_files_per_run = 5

        with patch.object(tool, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []

            result = await tool.run_with_timeout(
                ["1.py", "2.py", "3.py", "4.py", "5.py", "6.py"], {}
            )

        assert result["success"] is True
        assert mock_run.await_args.args[0] == ["1.py", "2.py", "3.py", "4.py", "5.py"]
        assert len(result["warnings"]) == 1
        assert "Limited to first 5 files" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_output_summary_generation(self):
        tool = StubTool()

        # Test no issues
        result = await tool.run_with_timeout([], {})
        assert "No issues found" in result["output_summary"]

        # Test with issues
        with patch.object(tool, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [{"issue": "1"}, {"issue": "2"}]
            result = await tool.run_with_timeout(["test.py"], {})
            assert "2 issues found" in result["output_summary"]

        # Test with error
        with patch.object(tool, "run", side_effect=Exception("Test error")):
            result = await tool.run_with_timeout(["test.py"], {})
            assert "Test error" in result["output_summary"]


class TestSemgrepTool:
    """Test Semgrep tool specifically."""

    def test_semgrep_tool_properties(self):
        tool = SemgrepTool()

        assert tool.name == "semgrep"
        assert tool.category == "security"
        assert tool.timeout == 10.0
        assert tool.max_files == 25
        assert (
            tool.description
            == "Cross-platform static analysis for security vulnerabilities and code quality issues"
        )

    def test_semgrep_default_config(self):
        config = SemgrepTool().get_default_config()

        assert config["rules"] == "auto"
        assert config["severity"] == "INFO,WARNING,ERROR"
        assert config["strict"] is False
        assert config["verbose"] is False
        assert "security" in config["categories"]

    def test_semgrep_supported_languages(self):
        languages = SemgrepTool().get_supported_languages()

        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "java" in languages
        assert "go" in languages

    def test_semgrep_rule_categories(self):
        categories = SemgrepTool().get_rule_categories()

        assert "security" in categories
        assert "performance" in categories
        assert "maintainability" in categories
        assert "bug" in categories

    def test_semgrep_output_parsing(self):
        """_parse_semgrep_output flattens a findings payload into issues."""
        payload = {
            "results": [
                {
                    "path": "app.py",
                    "check_id": "python.lang.security.audit.eval-detected",
                    "start": {"line": 3, "col": 1},
                    "end": {"line": 3, "col": 20},
                    "message": "Detected eval",
                    "extra": {"severity": "ERROR", "metadata": {"cwe": ["CWE-95"]}},
                }
            ]
        }

        issues = SemgrepTool()._parse_semgrep_output(payload)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["filename"] == "app.py"
        assert issue["line_number"] == 3
        assert issue["column_number"] == 1
        assert issue["severity"] == "error"
        assert issue["details"]["category"] == "security"
        assert issue["details"]["cwe"] == ["CWE-95"]

    def test_category_determination(self):
        tool = SemgrepTool()

        assert tool._determine_category("security.vulnerability.xss", {}) == "security"
        assert tool._determine_category("performance.memory.leak", {}) == "performance"
        assert (
            tool._determine_category("maintainability.style.convention", {})
            == "maintainability"
        )
        assert tool._determine_category("bug.null.pointer", {}) == "bug"
        assert tool._determine_category("unknown.rule", {}) == "general"


class TestWindowsSecurityTool:
    """Test Windows Security tool specifically."""

    def test_windows_security_tool_properties(self):
        tool = WindowsSecurityTool()

        assert tool.name == "windows_security"
        assert tool.category == "security"
        assert tool.timeout == 30.0
        assert tool.max_files == 20
        assert tool.get_required_command() == "bandit"

    @pytest.mark.asyncio
    async def test_windows_security_empty_files(self):
        assert await WindowsSecurityTool().run([], {}) == []

    @pytest.mark.asyncio
    async def test_windows_security_python_security_patterns(self, tmp_path):
        # Fixture text only: the scanner greps this file, nothing executes it.
        source = tmp_path / "insecure.py"
        source.write_text(
            'password = "secret123"\n'
            'eval("dangerous_code")\n'
            'subprocess.run("command", shell=True)\n'
        )

        issues = await WindowsSecurityTool()._check_python_security_patterns(
            str(source), {}
        )

        assert [issue["code"] for issue in issues] == [
            "HARDCODED_SECRET",
            "EVAL_USAGE",
            "SHELL_INJECTION",
        ]
        assert all(issue["filename"] == str(source) for issue in issues)

    @pytest.mark.asyncio
    async def test_windows_security_ignores_clean_files(self, tmp_path):
        source = tmp_path / "clean.py"
        source.write_text("def add(a, b):\n    return a + b\n")

        issues = await WindowsSecurityTool()._check_python_security_patterns(
            str(source), {}
        )

        assert issues == []

    @pytest.mark.asyncio
    async def test_windows_security_reports_unreadable_files(self, tmp_path):
        missing = tmp_path / "gone.py"

        issues = await WindowsSecurityTool()._check_python_security_patterns(
            str(missing), {}
        )

        assert len(issues) == 1
        assert "Error checking security patterns" in issues[0]["error"]


if __name__ == "__main__":
    pytest.main([__file__])
