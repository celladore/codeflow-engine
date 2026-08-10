"""
Tests for individual quality tools.

Every tool implements ``run(files, config)`` by shelling out and parsing the
result, so these tests patch the subprocess spawn and assert on the parsing.
Pure parsing helpers are called directly where a tool exposes one.
"""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from codeflow_engine.actions.quality_engine.tools.bandit_tool import BanditTool
from codeflow_engine.actions.quality_engine.tools.dependency_scanner_tool import (
    DependencyScannerTool,
)
from codeflow_engine.actions.quality_engine.tools.eslint_tool import ESLintTool
from codeflow_engine.actions.quality_engine.tools.interrogate_tool import (
    InterrogateTool,
)
from codeflow_engine.actions.quality_engine.tools.mypy_tool import MyPyTool
from codeflow_engine.actions.quality_engine.tools.performance_analyzer_tool import (
    PerformanceAnalyzerTool,
)
from codeflow_engine.actions.quality_engine.tools.pytest_tool import PyTestTool
from codeflow_engine.actions.quality_engine.tools.radon_tool import RadonTool
from codeflow_engine.actions.quality_engine.tools.ruff_tool import RuffTool
from codeflow_engine.actions.quality_engine.tools.semgrep_tool import SemgrepTool


MYPY_MODULE = "codeflow_engine.actions.quality_engine.tools.mypy_tool"


class FakeProcess:
    """Stand-in for the process asyncio.create_subprocess_exec returns."""

    def __init__(self, returncode: int, stdout: bytes, stderr: bytes) -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


def patch_exec(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
    """Patch the subprocess spawn every tool funnels through.

    Tools call ``asyncio.create_subprocess_exec`` by attribute lookup, so
    patching it on the asyncio module covers all of them.
    """
    return patch(
        "asyncio.create_subprocess_exec",
        AsyncMock(return_value=FakeProcess(returncode, stdout, stderr)),
    )


def command_of(mock_exec: AsyncMock) -> list[str]:
    """The command tokens a tool passed to create_subprocess_exec."""
    return list(mock_exec.call_args.args)


class TestRuffTool:
    """Ruff runs `ruff check --output-format json` and returns the JSON as-is."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RuffTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio
    async def test_returns_parsed_json_issues(self):
        payload = json.dumps(
            [
                {"code": "E501", "filename": "test.py"},
                {"code": "F401", "filename": "test.py"},
            ]
        ).encode()

        with patch_exec(returncode=1, stdout=payload):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["E501", "F401"]

    @pytest.mark.asyncio
    async def test_returns_nothing_when_ruff_is_silent(self):
        with patch_exec(returncode=0, stdout=b""):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_wraps_a_bare_json_object_in_a_list(self):
        with patch_exec(returncode=1, stdout=b'{"code": "E501"}'):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"code": "E501"}]

    @pytest.mark.asyncio
    async def test_reports_unexpected_exit_code_as_an_error_issue(self):
        with patch_exec(returncode=2, stderr=b"ruff: unknown option"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Ruff execution failed: ruff: unknown option"}]

    @pytest.mark.asyncio
    async def test_reports_unparseable_output_as_an_error_issue(self):
        with patch_exec(returncode=1, stdout=b"not json"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Failed to parse ruff JSON output"}]

    @pytest.mark.asyncio
    async def test_appends_configured_extra_args(self):
        config = {"args": ["--select", "E501"]}

        with patch_exec(returncode=0, stdout=b"[]") as mock_exec:
            await self.tool.run(self.test_files, config)

        command = command_of(mock_exec)
        assert command[-2:] == ["--select", "E501"]
        assert "test.py" in command

    @pytest.mark.asyncio
    async def test_skips_the_subprocess_without_files(self):
        with patch_exec() as mock_exec:
            assert await self.tool.run([], {}) == []

        mock_exec.assert_not_called()


class TestMyPyTool:
    """MyPy has no stable JSON output, so the tool parses its text output."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = MyPyTool()
        self.test_files = ["test.py"]

    def test_parse_output_windows_paths(self):
        """Test MyPy output parsing with Windows drive-letter paths."""
        windows_output = (
            'C:\\path\\to\\file.py:12:3: error: Incompatible return value type '
            '(got "int", expected "str")  [return-value]\n'
        )

        issues = self.tool._parse_output(windows_output)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["filename"] == "C:\\path\\to\\file.py"
        assert issue["line_number"] == 12
        assert issue["column_number"] == 3
        assert issue["level"] == "error"
        assert (
            issue["message"]
            == 'Incompatible return value type (got "int", expected "str")'
        )
        assert issue["code"] == "return-value"

    def test_parse_output_unix_paths(self):
        """Test MyPy output parsing with Unix-style paths (regression test)."""
        unix_output = (
            "/home/user/project/file.py:5:12: error: Incompatible types  [assignment]\n"
        )

        issues = self.tool._parse_output(unix_output)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["filename"] == "/home/user/project/file.py"
        assert issue["line_number"] == 5
        assert issue["column_number"] == 12
        assert issue["level"] == "error"
        assert issue["message"] == "Incompatible types"
        assert issue["code"] == "assignment"

    def test_parse_output_relative_paths(self):
        """Test MyPy output parsing with relative paths."""
        relative_output = (
            "src/module.py:8:1: warning: Missing return type annotation  "
            "[no-untyped-def]\n"
        )

        issues = self.tool._parse_output(relative_output)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["filename"] == "src/module.py"
        assert issue["line_number"] == 8
        assert issue["column_number"] == 1
        assert issue["level"] == "warning"
        assert issue["message"] == "Missing return type annotation"
        assert issue["code"] == "no-untyped-def"

    def test_parse_output_ignores_unmatched_lines(self):
        output = "Found 1 error in 1 file (checked 3 source files)\n\n"

        assert self.tool._parse_output(output) == []

    def test_parse_output_names_the_tool_when_a_line_carries_no_code(self):
        """Notes carry no bracketed code, but LintIssue.code is a str."""
        issues = self.tool._parse_output('a.py:3:1: note: Revealed type is "int"\n')

        assert len(issues) == 1
        issue = issues[0]
        assert issue["level"] == "note"
        assert issue["code"] == "mypy"

    @pytest.mark.asyncio
    async def test_run_parses_output_on_windows(self):
        """Windows takes the subprocess.run branch to avoid asyncio subprocesses."""
        completed = SimpleNamespace(
            stdout="test.py:3:1: error: Missing return  [return]\n",
            stderr="",
            returncode=1,
        )

        with (
            patch("platform.system", return_value="Windows"),
            patch(f"{MYPY_MODULE}.subprocess.run", return_value=completed) as mock_run,
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["return"]
        assert "--show-column-numbers" in mock_run.call_args.args[0]

    @pytest.mark.asyncio
    async def test_run_parses_output_on_posix(self):
        stdout = b"test.py:3:1: error: Missing return  [return]\n"

        with (
            patch("platform.system", return_value="Linux"),
            patch_exec(returncode=1, stdout=stdout) as mock_exec,
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["return"]
        assert "test.py" in command_of(mock_exec)

    @pytest.mark.asyncio
    async def test_run_appends_configured_args(self):
        completed = SimpleNamespace(stdout="", stderr="", returncode=0)

        with (
            patch("platform.system", return_value="Windows"),
            patch(f"{MYPY_MODULE}.subprocess.run", return_value=completed) as mock_run,
        ):
            await self.tool.run(self.test_files, {"args": ["--strict"]})

        assert "--strict" in mock_run.call_args.args[0]

    @pytest.mark.asyncio
    async def test_run_reports_a_missing_executable(self):
        with (
            patch("platform.system", return_value="Windows"),
            patch(f"{MYPY_MODULE}.subprocess.run", side_effect=FileNotFoundError),
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["mypy-not-found"]

    @pytest.mark.asyncio
    async def test_run_reports_an_unexpected_exit_code(self):
        completed = SimpleNamespace(stdout="", stderr="boom", returncode=2)

        with (
            patch("platform.system", return_value="Windows"),
            patch(f"{MYPY_MODULE}.subprocess.run", return_value=completed),
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["mypy-error"]
        assert "boom" in issues[0]["message"]

    @pytest.mark.asyncio
    async def test_run_reports_unparseable_output_when_only_stderr_is_set(self):
        completed = SimpleNamespace(stdout="", stderr="mypy: bad config", returncode=1)

        with (
            patch("platform.system", return_value="Windows"),
            patch(f"{MYPY_MODULE}.subprocess.run", return_value=completed),
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["mypy-no-output"]

    @pytest.mark.asyncio
    async def test_run_skips_the_subprocess_without_files(self):
        with patch(f"{MYPY_MODULE}.subprocess.run") as mock_run:
            assert await self.tool.run([], {}) == []

        mock_run.assert_not_called()


class TestBanditTool:
    """Bandit reports findings under a `results` key in its JSON output."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = BanditTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio
    async def test_returns_the_results_array(self):
        payload = json.dumps(
            {
                "results": [
                    {"test_id": "B101", "issue_text": "Use of assert detected."}
                ],
                "metrics": {},
            }
        ).encode()

        with patch_exec(returncode=1, stdout=payload):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["test_id"] for issue in issues] == ["B101"]

    @pytest.mark.asyncio
    async def test_returns_nothing_when_no_issues_are_reported(self):
        with patch_exec(returncode=0, stdout=b'{"results": []}'):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_reports_unexpected_exit_code_as_an_error_issue(self):
        with patch_exec(returncode=2, stderr=b"bandit: bad target"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Bandit execution failed: bandit: bad target"}]

    @pytest.mark.asyncio
    async def test_reports_unparseable_output_as_an_error_issue(self):
        with patch_exec(returncode=1, stdout=b"<not json>"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Failed to parse bandit JSON output"}]

    @pytest.mark.asyncio
    async def test_requests_json_output_and_appends_extra_args(self):
        with patch_exec(returncode=0, stdout=b'{"results": []}') as mock_exec:
            await self.tool.run(self.test_files, {"args": ["-ll"]})

        command = command_of(mock_exec)
        assert command[:3] == ["bandit", "-f", "json"]
        assert command[-1] == "-ll"

    @pytest.mark.asyncio
    async def test_skips_the_subprocess_without_files(self):
        with patch_exec() as mock_exec:
            assert await self.tool.run([], {}) == []

        mock_exec.assert_not_called()


class TestSemgrepTool:
    """Semgrep is the security scanner; it also normalises its own findings."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SemgrepTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio
    async def test_returns_the_results_array(self):
        payload = json.dumps(
            {
                "results": [
                    {
                        "check_id": "python.lang.security.unsafe-deserialization",
                        "path": "test.py",
                    }
                ],
                "errors": [],
            }
        ).encode()

        with patch_exec(returncode=1, stdout=payload):
            issues = await self.tool.run(self.test_files, {})

        assert len(issues) == 1
        assert issues[0]["path"] == "test.py"

    @pytest.mark.asyncio
    async def test_returns_nothing_when_no_findings_are_reported(self):
        with patch_exec(returncode=0, stdout=b'{"results": []}'):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_reports_unexpected_exit_code_as_an_error_issue(self):
        with patch_exec(returncode=7, stderr=b"semgrep: invalid rule"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [
            {"error": "Semgrep execution failed: semgrep: invalid rule"}
        ]

    @pytest.mark.asyncio
    async def test_reports_unparseable_output_as_an_error_issue(self):
        with patch_exec(returncode=0, stdout=b"<not json>"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Failed to parse semgrep JSON output"}]

    @pytest.mark.asyncio
    async def test_passes_explicit_rules_as_a_config_flag(self):
        with patch_exec(returncode=0, stdout=b'{"results": []}') as mock_exec:
            await self.tool.run(self.test_files, {"rules": "p/security-audit"})

        command = command_of(mock_exec)
        assert command[:3] == ["semgrep", "--json", "--quiet"]
        assert command[-2:] == ["--config", "p/security-audit"]

    @pytest.mark.asyncio
    async def test_leaves_auto_rules_off_the_command_line(self):
        with patch_exec(returncode=0, stdout=b'{"results": []}') as mock_exec:
            await self.tool.run(self.test_files, {"rules": "auto"})

        assert "--config" not in command_of(mock_exec)

    @pytest.mark.asyncio
    async def test_caps_the_files_it_scans(self):
        files = [f"file{i}.py" for i in range(self.tool.max_files_per_run + 10)]

        with patch_exec(returncode=0, stdout=b'{"results": []}') as mock_exec:
            await self.tool.run(files, {})

        scanned = [arg for arg in command_of(mock_exec) if arg.endswith(".py")]
        assert len(scanned) == self.tool.max_files_per_run

    @pytest.mark.asyncio
    async def test_skips_the_subprocess_without_files(self):
        with patch_exec() as mock_exec:
            assert await self.tool.run([], {}) == []

        mock_exec.assert_not_called()

    def test_parse_semgrep_output_normalises_a_finding(self):
        raw = {
            "results": [
                {
                    "path": "app/views.py",
                    "start": {"line": 12, "col": 4},
                    "end": {"line": 14, "col": 9},
                    "check_id": "python.lang.security.audit.eval-detected",
                    "message": "Detected eval usage",
                    "extra": {
                        "severity": "ERROR",
                        "metadata": {"cwe": ["CWE-95"], "impact": "HIGH"},
                    },
                }
            ]
        }

        issues = self.tool._parse_semgrep_output(raw)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["filename"] == "app/views.py"
        assert issue["line_number"] == 12
        assert issue["end_line"] == 14
        assert issue["column_number"] == 4
        assert issue["end_column"] == 9
        assert issue["code"] == "python.lang.security.audit.eval-detected"
        assert issue["message"] == "Detected eval usage"
        assert issue["severity"] == "error"
        assert issue["details"]["category"] == "security"
        assert issue["details"]["cwe"] == ["CWE-95"]

    def test_parse_semgrep_output_handles_an_empty_report(self):
        assert self.tool._parse_semgrep_output({}) == []


class TestInterrogateTool:
    """Interrogate checks docstring coverage against a threshold."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = InterrogateTool()
        self.test_files = ["src/module.py"]

    @pytest.mark.asyncio
    async def test_runs_against_directories_with_the_configured_threshold(self):
        with patch_exec(returncode=0, stdout=b"") as mock_exec:
            await self.tool.run(self.test_files, {"fail_under": 95})

        command = command_of(mock_exec)
        assert command[0] == "interrogate"
        assert "src" in command
        assert command[-2:] == ["--fail-under", "95"]

    @pytest.mark.asyncio
    async def test_treats_exit_code_two_as_coverage_below_threshold(self):
        stdout = b"TOTAL       10      5      5     50.0%\n"

        with patch_exec(returncode=2, stdout=stdout):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["COVERAGE_BELOW_THRESHOLD"]

    @pytest.mark.asyncio
    async def test_reports_unexpected_exit_code_as_an_error_issue(self):
        with patch_exec(returncode=1, stderr=b"interrogate: bad path"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [
            {"error": "Interrogate execution failed: interrogate: bad path"}
        ]

    @pytest.mark.asyncio
    async def test_skips_the_subprocess_without_files(self):
        with patch_exec() as mock_exec:
            assert await self.tool.run([], {}) == []

        mock_exec.assert_not_called()

    def test_parse_output_flags_coverage_below_the_threshold(self):
        output = "TOTAL       10      5      5     50.0%\n"

        issues = self.tool._parse_output(output, ["src/module.py"], fail_under=80)

        assert len(issues) == 1
        assert issues[0]["filename"] == "overall"
        assert issues[0]["code"] == "COVERAGE_BELOW_THRESHOLD"
        assert issues[0]["details"] == {"coverage_percentage": 50.0, "threshold": 80}

    def test_parse_output_accepts_coverage_at_the_threshold(self):
        output = "TOTAL       10      2      8     80.0%\n"

        assert self.tool._parse_output(output, ["src/module.py"], fail_under=80) == []

    def test_parse_output_reports_failed_lines_for_requested_files(self):
        output = (
            "FAILED: src/module.py:14 - DOC101 - Missing docstring\n"
            "FAILED: other/ignored.py:3 - DOC101 - Missing docstring\n"
        )

        issues = self.tool._parse_output(output, ["src/module.py"], fail_under=80)

        assert len(issues) == 1
        assert issues[0]["filename"] == "src/module.py"
        assert issues[0]["line_number"] == 14
        assert issues[0]["code"] == "DOC101"
        assert issues[0]["message"] == "Missing docstring"


class TestRadonTool:
    """Radon reports cyclomatic complexity keyed by filename."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RadonTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio
    async def test_formats_complexity_results_into_issues(self):
        payload = json.dumps(
            {
                "test.py": [
                    {
                        "name": "process",
                        "lineno": 5,
                        "col_offset": 0,
                        "complexity": 15,
                    }
                ]
            }
        ).encode()

        with patch_exec(returncode=0, stdout=payload):
            issues = await self.tool.run(self.test_files, {})

        assert len(issues) == 1
        assert issues[0]["filename"] == "test.py"
        assert issues[0]["code"] == "RADON_COMPLEXITY"

    @pytest.mark.asyncio
    async def test_returns_nothing_when_nothing_exceeds_the_threshold(self):
        with patch_exec(returncode=0, stdout=b"{}"):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_passes_the_configured_max_complexity(self):
        with patch_exec(returncode=0, stdout=b"{}") as mock_exec:
            await self.tool.run(self.test_files, {"max_complexity": 5})

        command = command_of(mock_exec)
        assert command[:3] == ["radon", "cc", "--json"]
        assert command[-2:] == ["--max", "5"]

    @pytest.mark.asyncio
    async def test_reports_a_non_zero_exit_code_as_an_error_issue(self):
        with patch_exec(returncode=1, stderr=b"radon: bad path"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Radon execution failed: radon: bad path"}]

    @pytest.mark.asyncio
    async def test_reports_unparseable_output_as_an_error_issue(self):
        with patch_exec(returncode=0, stdout=b"<not json>"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "Failed to parse radon JSON output"}]

    @pytest.mark.asyncio
    async def test_skips_the_subprocess_without_files(self):
        with patch_exec() as mock_exec:
            assert await self.tool.run([], {}) == []

        mock_exec.assert_not_called()

    def test_format_output_describes_the_offending_function(self):
        output = {
            "test.py": [
                {"name": "process", "lineno": 5, "col_offset": 2, "complexity": 15}
            ]
        }

        issues = self.tool._format_output(output, threshold=10)

        assert len(issues) == 1
        issue = issues[0]
        assert issue["line_number"] == 5
        assert issue["column_number"] == 2
        assert "process" in issue["message"]
        assert "15" in issue["message"]
        assert "10" in issue["message"]


class TestPyTestTool:
    """PyTest is judged purely by its exit code."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PyTestTool()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio
    async def test_returns_nothing_when_tests_pass(self):
        with patch_exec(returncode=0, stdout=b"1 passed"):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_reports_test_failures(self):
        with patch_exec(returncode=1, stdout=b"1 failed"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "PyTest found test failures"}]

    @pytest.mark.asyncio
    async def test_treats_no_tests_collected_as_clean(self):
        with patch_exec(returncode=5, stdout=b"no tests ran"):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_reports_unexpected_exit_code_as_an_error_issue(self):
        with patch_exec(returncode=4, stderr=b"usage error"):
            issues = await self.tool.run(self.test_files, {})

        assert issues == [{"error": "PyTest execution failed: usage error"}]

    @pytest.mark.asyncio
    async def test_falls_back_to_the_current_directory_without_files(self):
        with patch_exec(returncode=0) as mock_exec:
            await self.tool.run([], {})

        command = command_of(mock_exec)
        assert command[:3] == ["pytest", "--tb=short", "--maxfail=5"]
        assert command[3] == "."


class TestESLintTool:
    """ESLint runs through npx and emits a JSON report per file."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ESLintTool()
        self.test_files = ["test.js"]

    @pytest.mark.asyncio
    async def test_returns_nothing_when_no_messages_are_reported(self):
        payload = json.dumps([{"filePath": "test.js", "messages": []}]).encode()

        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch_exec(returncode=0, stdout=payload),
        ):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_returns_parsed_lint_messages(self):
        payload = json.dumps(
            [
                {
                    "filePath": "test.js",
                    "messages": [
                        {
                            "line": 5,
                            "column": 10,
                            "message": "'x' is defined but never used",
                            "ruleId": "no-unused-vars",
                            "severity": 2,
                        }
                    ],
                }
            ]
        ).encode()

        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch_exec(returncode=1, stdout=payload),
        ):
            issues = await self.tool.run(self.test_files, {})

        assert len(issues) == 1
        issue = issues[0]
        assert issue["filename"] == "test.js"
        assert issue["line_number"] == 5
        assert issue["column_number"] == 10
        assert issue["code"] == "no-unused-vars"
        assert issue["level"] == "error"

    @pytest.mark.asyncio
    async def test_reports_a_missing_eslint_as_a_warning_issue(self):
        with patch.object(self.tool, "is_available", return_value=False):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["eslint-not-available"]
        assert issues[0]["level"] == "warning"

    @pytest.mark.asyncio
    async def test_reports_unexpected_exit_code_as_an_error_issue(self):
        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch_exec(returncode=2, stderr=b"eslint: no configuration found"),
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["eslint-error"]
        assert "no configuration found" in issues[0]["message"]

    @pytest.mark.asyncio
    async def test_reports_a_spawn_failure_as_an_error_issue(self):
        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch("asyncio.create_subprocess_exec", side_effect=OSError("boom")),
        ):
            issues = await self.tool.run(self.test_files, {})

        assert [issue["code"] for issue in issues] == ["eslint-error"]

    @pytest.mark.asyncio
    async def test_builds_the_command_from_config(self):
        config = {"config": ".eslintrc.json", "fix": True, "args": ["--quiet"]}

        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch_exec(returncode=0, stdout=b"[]") as mock_exec,
        ):
            await self.tool.run(self.test_files, config)

        command = command_of(mock_exec)
        assert command[:4] == ["npx", "eslint", "--format", "json"]
        assert "--config" in command
        assert ".eslintrc.json" in command
        assert "--fix" in command
        assert command[-2:] == ["--quiet", "test.js"]

    @pytest.mark.asyncio
    async def test_skips_the_subprocess_without_files(self):
        with patch_exec() as mock_exec:
            assert await self.tool.run([], {}) == []

        mock_exec.assert_not_called()

    def test_parse_eslint_output_marks_severity_one_as_a_warning(self):
        payload = json.dumps(
            [
                {
                    "filePath": "test.js",
                    "messages": [{"line": 1, "column": 1, "severity": 1}],
                }
            ]
        )

        issues = self.tool._parse_eslint_output(payload)

        assert issues[0]["level"] == "warning"
        assert issues[0]["message"] == "Unknown issue"
        assert issues[0]["code"] == "unknown"

    def test_parse_eslint_output_handles_empty_output(self):
        assert self.tool._parse_eslint_output("   ") == []

    def test_parse_eslint_output_reports_unparseable_json(self):
        issues = self.tool._parse_eslint_output("<not json>")

        assert [issue["code"] for issue in issues] == ["eslint-error"]


class TestDependencyScannerTool:
    """The dependency scanner shells out to `safety` per requirements file."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DependencyScannerTool()
        self.test_files = ["requirements.txt"]

    @pytest.mark.asyncio
    async def test_returns_a_vulnerability_per_safety_finding(self):
        payload = json.dumps(
            [["requests", "2.0.0", "<2.20.0", "Redirect leak", "12345"]]
        ).encode()

        with patch_exec(returncode=1, stdout=payload) as mock_exec:
            issues = await self.tool.run(self.test_files, {})

        assert len(issues) == 1
        issue = issues[0]
        assert issue["file"] == "requirements.txt"
        assert issue["package"] == "requests"
        assert issue["installed_version"] == "2.0.0"
        assert issue["vulnerable_below"] == "<2.20.0"
        assert issue["vulnerability_id"] == "12345"
        assert issue["severity"] == "high"
        assert "Redirect leak" in issue["message"]
        assert command_of(mock_exec) == [
            "safety",
            "check",
            "-r",
            "requirements.txt",
            "--json",
        ]

    @pytest.mark.asyncio
    async def test_returns_nothing_when_safety_finds_no_vulnerabilities(self):
        with patch_exec(returncode=0, stdout=b"[]"):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_returns_nothing_when_safety_is_not_installed(self):
        with patch_exec(returncode=127, stderr=b"safety: command not found"):
            assert await self.tool.run(self.test_files, {}) == []

    @pytest.mark.asyncio
    async def test_returns_nothing_when_no_requirements_files_are_found(self):
        """Without a requirements file in `files` it searches, then gives up."""
        with patch_exec(returncode=0, stdout=b"\n") as mock_exec:
            assert await self.tool.run(["main.py"], {}) == []

        assert mock_exec.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_nothing_when_safety_output_is_unparseable(self):
        with patch_exec(returncode=0, stdout=b"<not json>"):
            assert await self.tool.run(self.test_files, {}) == []


class TestPerformanceAnalyzerTool:
    """The performance analyzer profiles with scalene and pattern-matches source."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PerformanceAnalyzerTool()

    @pytest.mark.asyncio
    async def test_reports_static_patterns_when_scalene_is_unavailable(self, tmp_path):
        source = tmp_path / "slow.py"
        source.write_text(
            'def build():\n'
            '    out = []\n'
            '    for i in range(10):\n'
            '        out.append(i)\n'
            '    text = ""\n'
            '    for item in out:\n'
            '        text += "x"\n'
            '    return text\n'
        )

        # returncode 1 from `python -m scalene --help` means scalene is absent.
        with patch_exec(returncode=1):
            issues = await self.tool.run([str(source)], {})

        assert len(issues) == 2
        assert {issue["code"] for issue in issues} == {"performance_pattern"}
        assert all(issue["filename"] == str(source) for issue in issues)

    @pytest.mark.asyncio
    async def test_ignores_paths_that_are_not_files(self, tmp_path):
        with patch_exec(returncode=1):
            issues = await self.tool.run([str(tmp_path / "missing.py"), "."], {})

        assert issues == []

    def test_analyze_python_performance_flags_append_loops(self):
        content = "for i in range(3):\n    items.append(i)\n"

        issues = self.tool._analyze_python_performance("loop.py", content)

        assert len(issues) == 1
        assert "list comprehension" in issues[0]["message"]

    def test_analyze_python_performance_flags_string_concatenation(self):
        content = 'text += "chunk"\n'

        issues = self.tool._analyze_python_performance("concat.py", content)

        assert len(issues) == 1
        assert "String concatenation" in issues[0]["message"]

    def test_analyze_python_performance_accepts_clean_source(self):
        content = "def add(a, b):\n    return a + b\n"

        assert self.tool._analyze_python_performance("clean.py", content) == []

    def test_analyze_js_performance_flags_console_logging(self):
        issues = self.tool._analyze_js_performance("app.js", "console.log('hi')\n")

        assert len(issues) == 1
        assert issues[0]["filename"] == "app.js"
        assert issues[0]["code"] == "performance_pattern"

    def test_analyze_js_performance_accepts_clean_source(self):
        assert self.tool._analyze_js_performance("app.js", "export const x = 1;\n") == []


class TestToolBase:
    """Behaviour every tool inherits from Tool, exercised through RuffTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RuffTool()

    def test_tool_exposes_its_identity_and_limits(self):
        assert self.tool.name == "ruff"
        assert self.tool.description
        assert self.tool.category == "general"
        assert self.tool.timeout == 60.0
        assert self.tool.max_files == 100
        assert self.tool.get_display_name() == "Ruff"
        assert self.tool.get_required_command() == "ruff"

    def test_validate_config_returns_an_empty_list_for_a_valid_config(self):
        """validate_config returns errors, not a boolean."""
        assert self.tool.validate_config({"timeout": 30.0, "max_files": 10}) == []

    def test_validate_config_rejects_a_non_positive_timeout(self):
        errors = self.tool.validate_config({"timeout": -1})

        assert len(errors) == 1
        assert "positive number" in errors[0]

    def test_validate_config_rejects_a_non_positive_max_files(self):
        errors = self.tool.validate_config({"max_files": 0})

        assert len(errors) == 1
        assert "positive integer" in errors[0]

    def test_validate_config_rejects_a_non_mapping(self):
        assert self.tool.validate_config("not a dict") == [
            "Configuration must be a dictionary"
        ]

    def test_config_schema_advertises_the_tools_own_defaults(self):
        schema = self.tool.get_config_schema()

        assert schema["timeout"]["default"] == 60.0
        assert schema["max_files"]["default"] == 100
        assert schema["verbose"]["default"] is False

    @pytest.mark.asyncio
    async def test_run_with_timeout_wraps_a_successful_run(self):
        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch.object(
                self.tool, "run", AsyncMock(return_value=[{"code": "E501"}])
            ),
        ):
            result = await self.tool.run_with_timeout(["test.py"], {})

        assert result["success"] is True
        assert result["issues"] == [{"code": "E501"}]
        assert result["error_message"] is None
        assert result["warnings"] == []
        assert "1 issue found" in result["output_summary"]

    @pytest.mark.asyncio
    async def test_run_with_timeout_reports_a_timeout(self):
        self.tool.default_timeout = 0.05

        async def slow_run(files, config):
            await asyncio.sleep(5)
            return []

        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch.object(self.tool, "run", side_effect=slow_run),
        ):
            result = await self.tool.run_with_timeout(["test.py"], {})

        assert result["success"] is False
        assert "timed out" in result["error_message"].lower()

    @pytest.mark.asyncio
    async def test_run_with_timeout_reports_a_missing_tool(self):
        with patch.object(self.tool, "is_available", return_value=False):
            result = await self.tool.run_with_timeout(["test.py"], {})

        assert result["success"] is False
        assert "not found" in result["error_message"].lower()
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_run_with_timeout_reports_a_failing_run(self):
        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch.object(self.tool, "run", side_effect=RuntimeError("boom")),
        ):
            result = await self.tool.run_with_timeout(["test.py"], {})

        assert result["success"] is False
        assert "boom" in result["error_message"]
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_run_with_timeout_caps_the_file_list(self):
        self.tool.max_files_per_run = 2

        with (
            patch.object(self.tool, "is_available", return_value=True),
            patch.object(self.tool, "run", AsyncMock(return_value=[])) as mock_run,
        ):
            result = await self.tool.run_with_timeout(["a.py", "b.py", "c.py"], {})

        assert mock_run.await_args.args[0] == ["a.py", "b.py"]
        assert result["warnings"] == ["Limited to first 2 files (out of 3)"]


if __name__ == "__main__":
    pytest.main([__file__])
