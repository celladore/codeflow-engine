"""
Simplified tests for Quality Engine core functionality.
"""

import pytest

from codeflow_engine.actions.quality_engine import engine as engine_module
from codeflow_engine.actions.quality_engine.__tests__.engine_fixtures import (
    STUB_TOOL_NAME,
    make_engine,
    make_stub_tool_class,
)
from codeflow_engine.actions.quality_engine.models import QualityOutputs
from codeflow_engine.actions.quality_engine.tool_runner import run_tool
from codeflow_engine.actions.quality_engine.tools.registry import ToolRegistry
from codeflow_engine.utils.volume_utils import QualityMode


class TestQualityEngineSimple:
    """Simplified test for Quality Engine core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_files = ["test1.py", "test2.py"]

    def test_quality_mode_enum(self):
        """Test Quality Mode enumeration."""
        assert QualityMode.FAST.value == "fast"
        assert QualityMode.COMPREHENSIVE.value == "comprehensive"
        assert QualityMode.AI_ENHANCED.value == "ai_enhanced"
        assert QualityMode.SMART.value == "smart"

    def test_quality_outputs_model(self):
        """Test QualityOutputs model creation."""
        result = QualityOutputs(
            success=True,
            total_issues_found=5,
            total_issues_fixed=2,
            files_modified=["test.py"],
            issues_by_tool={"ruff": [{"issue": "test"}]},
            files_by_tool={"ruff": ["test.py"]},
            tool_execution_times={"ruff": 1.5},
            summary="Test summary",
            ai_enhanced=False,
        )

        assert result.success is True
        assert result.total_issues_found == 5
        assert result.total_issues_fixed == 2
        assert "test.py" in result.files_modified
        assert "ruff" in result.issues_by_tool
        assert result.tool_execution_times == {"ruff": 1.5}
        assert result.ai_enhanced is False

        # Everything the engine only fills in sometimes stays optional.
        assert result.ai_summary is None
        assert result.auto_fix_applied is False
        assert result.fix_summary is None
        assert result.fix_errors is None

    def test_quality_inputs_model(self):
        """Test QualityInputs model creation."""
        from codeflow_engine.actions.quality_engine.models import QualityInputs

        inputs = QualityInputs(
            mode=QualityMode.FAST,
            files=self.test_files,
            max_fixes=10,
            enable_ai_agents=True,
            verbose=True,
        )

        assert inputs.mode == QualityMode.FAST
        assert inputs.files == self.test_files
        assert inputs.max_fixes == 10
        assert inputs.enable_ai_agents is True
        assert inputs.verbose is True

    @pytest.mark.asyncio
    async def test_engine_import(self):
        """Test that Quality Engine can be imported."""
        try:
            from codeflow_engine.actions.quality_engine.engine import QualityEngine

            engine = QualityEngine()
            assert engine is not None
        except ImportError as e:
            pytest.fail(f"Failed to import QualityEngine: {e}")

    @pytest.mark.asyncio
    async def test_tool_result_model(self):
        """Test ToolResult model creation."""
        from codeflow_engine.actions.quality_engine.models import ToolResult

        tool_result = ToolResult(
            issues=[{"issue": "test"}],
            files_with_issues=["test.py"],
            summary="Test summary",
            execution_time=1.5,
        )

        assert len(tool_result.issues) == 1
        assert "test.py" in tool_result.files_with_issues
        assert tool_result.summary == "Test summary"
        assert tool_result.execution_time == 1.5


class TestQualityEngineIntegration:
    """Integration tests for Quality Engine."""

    def test_engine_initialization(self):
        """Test Quality Engine initialization."""
        engine = make_engine(tool_names=(STUB_TOOL_NAME,))

        # Entry points callers actually use.
        assert callable(engine.execute)
        assert callable(engine.run)

        # Collaborators the constructor is responsible for wiring up.
        assert isinstance(engine.tool_registry, ToolRegistry)
        assert set(engine.tools) == {STUB_TOOL_NAME}
        assert engine.platform_detector is not None

        # Tools are run through the module-level run_tool, not an engine method,
        # which is the seam tests patch to keep real linters out of the run.
        assert engine_module.run_tool is run_tool

    @pytest.mark.asyncio
    async def test_platform_detector(self):
        """Test platform detector functionality."""
        try:
            from codeflow_engine.actions.quality_engine.platform_detector import PlatformDetector

            detector = PlatformDetector()

            # Test basic functionality
            assert hasattr(detector, "is_windows")
            assert hasattr(detector, "is_linux")
            assert hasattr(detector, "is_macos")

        except Exception as e:
            pytest.fail(f"Failed to test PlatformDetector: {e}")

    def test_tool_registry(self):
        """Test tool registry functionality."""
        registry = ToolRegistry()
        assert registry.get_all_tools() == []

        stub_class = make_stub_tool_class(STUB_TOOL_NAME)
        assert registry.register(stub_class) is stub_class

        # register() instantiates the class and keys it on the tool's own name.
        assert registry.get_available_tools() == [STUB_TOOL_NAME]
        assert [tool.name for tool in registry.get_all_tools()] == [STUB_TOOL_NAME]
        assert isinstance(registry.get_tool(STUB_TOOL_NAME), stub_class)
        assert registry.get_tool_class(STUB_TOOL_NAME) is stub_class

        with pytest.raises(KeyError):
            registry.get_tool("not-registered")


if __name__ == "__main__":
    pytest.main([__file__])
