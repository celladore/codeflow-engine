"""
Tests for Quality Engine core functionality.
"""

from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from codeflow_engine.actions.quality_engine.__tests__.engine_fixtures import (
    STUB_TOOL_NAME,
    make_engine,
)
from codeflow_engine.actions.quality_engine.engine import (
    QualityEngine,
    create_engine,
    create_quality_engine,
)
from codeflow_engine.actions.quality_engine.models import (
    QualityInputs,
    QualityOutputs,
    ToolResult,
)
from codeflow_engine.utils.volume_utils import QualityMode


def make_tool_result(issue_count: int = 1, filename: str = "test1.py") -> ToolResult:
    """Build a ToolResult of the shape run_tool returns."""
    return ToolResult(
        issues=[{"filename": filename, "message": f"issue {i}"} for i in range(issue_count)],
        files_with_issues=[filename] if issue_count else [],
        summary=f"{issue_count} issues",
        execution_time=0.5,
    )


def patch_run_tool(**kwargs) -> AsyncMock:
    """Patch the run_tool the engine imported, so no real tool is executed."""
    return patch(
        "codeflow_engine.actions.quality_engine.engine.run_tool",
        AsyncMock(**kwargs),
    )


class TestToolSelection:
    """Mode and volume driven tool selection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = make_engine(tool_names=("ruff", "mypy", "bandit"))
        self.test_files = ["test1.py", "test2.py"]

    def test_ultra_fast_mode_selects_only_ruff(self):
        tools = self.engine._determine_tools_for_mode(
            QualityMode.ULTRA_FAST, self.test_files
        )
        assert tools == ["ruff"]

    def test_fast_mode_selects_ruff_and_mypy(self):
        tools = self.engine._determine_tools_for_mode(
            QualityMode.FAST, self.test_files
        )
        assert tools == ["ruff", "mypy"]

    def test_comprehensive_mode_selects_every_registered_tool(self):
        tools = self.engine._determine_tools_for_mode(
            QualityMode.COMPREHENSIVE, self.test_files
        )
        assert set(tools) == {"ruff", "mypy", "bandit"}

    def test_ai_enhanced_mode_selects_core_tools(self):
        tools = self.engine._determine_tools_for_mode(
            QualityMode.AI_ENHANCED, self.test_files
        )
        assert set(tools) == {"ruff", "mypy", "bandit", "interrogate", "radon"}

    def test_smart_mode_adds_type_checking_for_python_files(self):
        tools = self.engine._select_smart_tools(
            ["module.py"], volume=500, available_tools=["ruff", "mypy", "bandit"]
        )
        assert "ruff" in tools
        assert "mypy" in tools

    def test_smart_mode_skips_type_checking_without_python_files(self):
        tools = self.engine._select_smart_tools(
            ["styles.css"], volume=500, available_tools=["ruff", "mypy"]
        )
        assert tools == ["ruff"]

    def test_smart_mode_gates_security_scanning_on_volume(self):
        available = ["ruff", "bandit"]

        quiet = self.engine._select_smart_tools(
            ["module.py"], volume=200, available_tools=available
        )
        loud = self.engine._select_smart_tools(
            ["module.py"], volume=800, available_tools=available
        )

        assert "bandit" not in quiet
        assert "bandit" in loud

    def test_unknown_mode_falls_back_to_all_tools(self):
        tools = self.engine._determine_tools_for_mode("not-a-mode", self.test_files)
        assert set(tools) == {"ruff", "mypy", "bandit"}


class TestEngineConfiguration:
    """Volume validation, tool config lookup, and construction."""

    def test_validate_volume_clamps_to_range(self):
        engine = make_engine()

        assert engine._validate_volume(2000) == 1000
        assert engine._validate_volume(-5) == 0
        assert engine._validate_volume(500) == 500

    def test_validate_volume_rejects_non_integers(self):
        engine = make_engine()

        with pytest.raises(ValueError, match="Volume must be an integer"):
            engine._validate_volume("high")

    def test_get_tool_config_defaults_to_enabled(self):
        engine = make_engine()

        assert engine._get_tool_config("ruff") == {"enabled": True, "config": {}}

    def test_get_tool_config_reads_supplied_config(self):
        engine = make_engine(config={"tools": {"ruff": {"enabled": False}}})

        assert engine._get_tool_config("ruff") == {"enabled": False}

    def test_registry_tools_are_exposed_by_name(self):
        engine = make_engine(tool_names=("ruff", "mypy"))

        assert set(engine.tools) == {"ruff", "mypy"}

    def test_factories_build_an_engine(self):
        engine = create_engine(config={"tools": {}})
        alias_engine = create_quality_engine(config={"tools": {}})

        assert isinstance(engine, QualityEngine)
        assert isinstance(alias_engine, QualityEngine)


class TestQualityEngineExecute:
    """End-to-end execute() behaviour with run_tool stubbed out."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_files = ["test1.py", "test2.py"]

    def make_inputs(self, mode=QualityMode.FAST, **kwargs) -> QualityInputs:
        return QualityInputs(mode=mode, files=self.test_files, **kwargs)

    @pytest.mark.asyncio
    async def test_execute_runs_each_selected_tool(self):
        engine = make_engine(tool_names=("ruff", "mypy"))

        with patch_run_tool(return_value=make_tool_result(issue_count=1)) as mock_run:
            result = await engine.execute(self.make_inputs(), {})

        assert mock_run.await_count == 2
        assert {call.kwargs["tool_name"] for call in mock_run.await_args_list} == {
            "ruff",
            "mypy",
        }
        assert result.total_issues_found == 2
        assert set(result.issues_by_tool) == {"ruff", "mypy"}
        assert result.files_by_tool["ruff"] == ["test1.py"]
        assert result.tool_execution_times["ruff"] == 0.5
        assert result.ai_enhanced is False

    @pytest.mark.asyncio
    async def test_execute_reports_success_when_no_issues_found(self):
        engine = make_engine()

        with patch_run_tool(return_value=make_tool_result(issue_count=0)):
            result = await engine.execute(self.make_inputs(), {})

        assert result.success is True
        assert result.total_issues_found == 0

    @pytest.mark.asyncio
    async def test_execute_reports_failure_when_issues_found(self):
        engine = make_engine()

        with patch_run_tool(return_value=make_tool_result(issue_count=3)):
            result = await engine.execute(self.make_inputs(), {})

        # success on QualityOutputs means "clean", not "the run completed"
        assert result.success is False
        assert result.total_issues_found == 3

    @pytest.mark.asyncio
    async def test_execute_with_empty_file_list_short_circuits(self):
        engine = make_engine()

        with patch_run_tool(return_value=make_tool_result()) as mock_run:
            result = await engine.execute(
                QualityInputs(mode=QualityMode.FAST, files=[]), {}
            )

        mock_run.assert_not_awaited()
        assert isinstance(result, QualityOutputs)
        assert result.success is True
        assert result.total_issues_found == 0
        assert result.files_modified == []
        assert result.summary == "No files provided for analysis"

    @pytest.mark.asyncio
    async def test_execute_skips_disabled_tools(self):
        engine = make_engine(
            tool_names=("ruff", "mypy"),
            config={"tools": {"ruff": {"enabled": False}}},
        )

        with patch_run_tool(return_value=make_tool_result()) as mock_run:
            await engine.execute(self.make_inputs(), {})

        assert mock_run.await_count == 1
        assert mock_run.await_args.kwargs["tool_name"] == "mypy"

    @pytest.mark.asyncio
    async def test_execute_ignores_tools_that_failed_to_run(self):
        """run_tool returns None when a tool blows up; the run must survive it."""
        engine = make_engine(tool_names=("ruff", "mypy"))

        with patch_run_tool(side_effect=[None, make_tool_result(issue_count=2)]):
            result = await engine.execute(self.make_inputs(), {})

        assert set(result.issues_by_tool) == {"mypy"}
        assert result.total_issues_found == 2

    @pytest.mark.asyncio
    async def test_execute_rejects_invalid_volume(self):
        engine = make_engine()

        with pytest.raises(ValueError, match="Volume must be an integer"):
            await engine.execute(self.make_inputs(), {}, volume="loud")

    @pytest.mark.asyncio
    async def test_execute_without_ai_agents_skips_ai_analysis(self):
        engine = make_engine()

        with (
            patch_run_tool(return_value=make_tool_result()),
            patch(
                "codeflow_engine.actions.quality_engine.ai.initialize_llm_manager",
                AsyncMock(),
            ) as mock_init,
        ):
            result = await engine.execute(
                self.make_inputs(mode=QualityMode.AI_ENHANCED, enable_ai_agents=False),
                {},
            )

        mock_init.assert_not_awaited()
        assert result.ai_enhanced is False
        assert result.ai_summary is None

    @pytest.mark.asyncio
    async def test_run_delegates_to_execute(self):
        engine = make_engine()

        with patch_run_tool(return_value=make_tool_result(issue_count=1)):
            result = await engine.run(self.make_inputs())

        assert isinstance(result, QualityOutputs)
        assert result.total_issues_found == 1


class TestQualityEngineIntegration:
    """Integration tests for Quality Engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = make_engine(tool_names=(STUB_TOOL_NAME,))
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename, content):
        """Create a test file with given content."""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        return str(file_path)

    @pytest.mark.asyncio
    async def test_end_to_end_fast_mode(self):
        """Real files in, aggregated QualityOutputs out."""
        test_file1 = self.create_test_file(
            "test1.py", "def test_function():\n    pass\n"
        )
        test_file2 = self.create_test_file("test2.py", "import os\nprint('hello')\n")

        with patch_run_tool(
            return_value=make_tool_result(issue_count=1, filename=test_file1)
        ) as mock_run:
            result = await self.engine.execute(
                QualityInputs(
                    mode=QualityMode.FAST, files=[test_file1, test_file2]
                ),
                {},
            )

        assert mock_run.await_args.kwargs["files"] == [test_file1, test_file2]
        assert result.total_issues_found == 1
        assert result.files_by_tool[STUB_TOOL_NAME] == [test_file1]
        assert result.summary


if __name__ == "__main__":
    pytest.main([__file__])
