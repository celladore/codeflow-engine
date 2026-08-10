"""
Tests for AI enhancement layer functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codeflow_engine.actions.quality_engine.__tests__.engine_fixtures import (
    STUB_TOOL_NAME,
    make_engine,
)
from codeflow_engine.actions.quality_engine.ai.ai_analyzer import AIAnalyzer
from codeflow_engine.actions.quality_engine.ai.ai_handler import AIHandler
from codeflow_engine.actions.quality_engine.ai.ai_modes import AIMode


class TestAIAnalyzer:
    """Test AI Analyzer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = AIAnalyzer()
        self.test_files = ["test.py"]
        self.test_content = "def test_function():\n    pass\n"

    @pytest.mark.asyncio
    async def test_analyze_code_quality(self):
        """Test AI code quality analysis."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(
                return_value={
                    "suggestions": ["Consider adding type hints", "Add docstring"],
                    "score": 0.85,
                    "issues": ["Missing type hints", "No docstring"],
                }
            )
            mock_get_provider.return_value = mock_provider

            result = await self.analyzer.analyze_code_quality(self.test_files)

            assert result["suggestions"] == [
                "Consider adding type hints",
                "Add docstring",
            ]
            assert result["score"] == 0.85
            assert result["issues"] == ["Missing type hints", "No docstring"]
            mock_provider.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_security_issues(self):
        """Test AI security analysis."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(
                return_value={
                    "security_issues": [
                        "Potential SQL injection",
                        "Hardcoded credentials",
                    ],
                    "risk_level": "medium",
                    "recommendations": [
                        "Use parameterized queries",
                        "Use environment variables",
                    ],
                }
            )
            mock_get_provider.return_value = mock_provider

            result = await self.analyzer.analyze_security_issues(self.test_files)

            assert result["security_issues"] == [
                "Potential SQL injection",
                "Hardcoded credentials",
            ]
            assert result["risk_level"] == "medium"
            assert result["recommendations"] == [
                "Use parameterized queries",
                "Use environment variables",
            ]

    @pytest.mark.asyncio
    async def test_analyze_performance_issues(self):
        """Test AI performance analysis."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(
                return_value={
                    "performance_issues": ["Inefficient loop", "Memory leak"],
                    "optimization_suggestions": [
                        "Use list comprehension",
                        "Add garbage collection",
                    ],
                }
            )
            mock_get_provider.return_value = mock_provider

            result = await self.analyzer.analyze_performance_issues(self.test_files)

            assert result["performance_issues"] == ["Inefficient loop", "Memory leak"]
            assert result["optimization_suggestions"] == [
                "Use list comprehension",
                "Add garbage collection",
            ]

    @pytest.mark.asyncio
    async def test_analyze_best_practices(self):
        """Test AI best practices analysis."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(
                return_value={
                    "best_practices": ["Follow PEP 8", "Use meaningful variable names"],
                    "violations": ["Line too long", "Unused import"],
                }
            )
            mock_get_provider.return_value = mock_provider

            result = await self.analyzer.analyze_best_practices(self.test_files)

            assert result["best_practices"] == [
                "Follow PEP 8",
                "Use meaningful variable names",
            ]
            assert result["violations"] == ["Line too long", "Unused import"]

    @pytest.mark.asyncio
    async def test_analyze_with_different_modes(self):
        """Test AI analysis with different modes."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(return_value={"result": "test"})
            mock_get_provider.return_value = mock_provider

            # Test comprehensive mode
            result = await self.analyzer.analyze(self.test_files, AIMode.COMPREHENSIVE)
            assert result is not None

            # Test focused mode
            result = await self.analyzer.analyze(self.test_files, AIMode.FOCUSED)
            assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_with_context(self):
        """Test AI analysis with additional context."""
        context = {
            "project_type": "web_application",
            "framework": "django",
            "target_audience": "enterprise",
        }

        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(return_value={"result": "test"})
            mock_get_provider.return_value = mock_provider

            result = await self.analyzer.analyze_with_context(self.test_files, context)

            assert result is not None
            # Verify context was passed to provider
            call_args = mock_provider.analyze.call_args[1]
            assert "context" in call_args

    @pytest.mark.asyncio
    async def test_analyze_ai_provider_failure(self):
        """Test AI analysis when provider fails."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(
                side_effect=Exception("AI provider error")
            )
            mock_get_provider.return_value = mock_provider

            result = await self.analyzer.analyze_code_quality(self.test_files)

            assert result["error"] == "AI provider error"
            assert result["success"] is False

    def test_get_ai_provider(self):
        """Test AI provider selection."""
        # Test with OpenAI provider
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}):
            provider = self.analyzer._get_ai_provider("openai")
            assert provider is not None

        # Test with Anthropic provider
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            provider = self.analyzer._get_ai_provider("anthropic")
            assert provider is not None

        # Test with invalid provider
        provider = self.analyzer._get_ai_provider("invalid")
        assert provider is None


class TestAIMode:
    """Test AI mode functionality."""

    def test_ai_mode_enum(self):
        """Test AI mode enumeration."""
        assert AIMode.COMPREHENSIVE == "comprehensive"
        assert AIMode.FOCUSED == "focused"
        assert AIMode.SECURITY == "security"
        assert AIMode.PERFORMANCE == "performance"

    def test_ai_mode_validation(self):
        """Test AI mode validation."""
        assert AIMode.is_valid("comprehensive") is True
        assert AIMode.is_valid("focused") is True
        assert AIMode.is_valid("invalid") is False

    def test_ai_mode_get_tools(self):
        """Test getting tools for AI mode."""
        comprehensive_tools = AIMode.get_tools("comprehensive")
        assert "code_quality" in comprehensive_tools
        assert "security" in comprehensive_tools
        assert "performance" in comprehensive_tools

        focused_tools = AIMode.get_tools("focused")
        assert "code_quality" in focused_tools
        assert len(focused_tools) < len(comprehensive_tools)


class TestAIHandler:
    """Test AI Handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AIHandler()
        self.test_result = {
            "suggestions": ["Add type hints", "Add docstring"],
            "score": 0.85,
            "issues": ["Missing type hints"],
        }

    def test_process_ai_result(self):
        """Test processing AI analysis result."""
        processed = self.handler.process_result(self.test_result)

        assert processed["suggestions"] == ["Add type hints", "Add docstring"]
        assert processed["score"] == 0.85
        assert processed["issues"] == ["Missing type hints"]
        assert processed["processed"] is True

    def test_filter_suggestions(self):
        """Test filtering AI suggestions."""
        suggestions = [
            "Add type hints",
            "Add docstring",
            "Consider using a different algorithm",
            "This is a minor suggestion",
        ]

        filtered = self.handler.filter_suggestions(suggestions, min_priority="medium")

        assert "Add type hints" in filtered
        assert "Add docstring" in filtered
        assert "This is a minor suggestion" not in filtered

    def test_prioritize_suggestions(self):
        """Test prioritizing AI suggestions."""
        suggestions = [
            "Add type hints",
            "Add docstring",
            "Fix security vulnerability",
            "Improve performance",
        ]

        prioritized = self.handler.prioritize_suggestions(suggestions)

        # Security issues should be prioritized highest
        assert prioritized[0] == "Fix security vulnerability"
        assert "Add type hints" in prioritized
        assert "Add docstring" in prioritized

    def test_format_suggestions_for_output(self):
        """Test formatting suggestions for output."""
        suggestions = ["Add type hints", "Add docstring"]

        formatted = self.handler.format_for_output(suggestions)

        assert "AI Suggestions:" in formatted
        assert "Add type hints" in formatted
        assert "Add docstring" in formatted

    def test_merge_ai_results(self):
        """Test merging multiple AI analysis results."""
        result1 = {"suggestions": ["Add type hints"], "score": 0.8}
        result2 = {"suggestions": ["Add docstring"], "score": 0.9}

        merged = self.handler.merge_results([result1, result2])

        assert len(merged["suggestions"]) == 2
        assert "Add type hints" in merged["suggestions"]
        assert "Add docstring" in merged["suggestions"]
        # Average of 0.8 and 0.9 - float mean, so compare approximately
        assert merged["score"] == pytest.approx(0.85)

    def test_validate_ai_result(self):
        """Test validating AI analysis result."""
        valid_result = {"suggestions": ["Add type hints"], "score": 0.85}
        assert self.handler.validate_result(valid_result) is True

        invalid_result = {"suggestions": "not a list"}
        assert self.handler.validate_result(invalid_result) is False

    def test_extract_actionable_items(self):
        """Test extracting actionable items from AI result."""
        result = {
            "suggestions": ["Add type hints", "Add docstring"],
            "issues": ["Missing type hints", "No docstring"],
            "recommendations": ["Use parameterized queries"],
        }

        actionable = self.handler.extract_actionable_items(result)

        assert "Add type hints" in actionable
        assert "Add docstring" in actionable
        assert "Use parameterized queries" in actionable

    @pytest.mark.asyncio
    async def test_apply_suggestions(self):
        """Test applying AI suggestions to code."""
        suggestions = ["Add type hints", "Add docstring"]
        file_content = "def test_function():\n    pass\n"

        with patch.object(self.handler, "_apply_suggestion") as mock_apply:
            mock_apply.return_value = (
                'def test_function() -> None:\n    """Test function."""\n    pass\n'
            )

            result = await self.handler.apply_suggestions(file_content, suggestions)

            assert result["modified"] is True
            # applied_suggestions records the whole suggestion, lower-cased
            assert result["applied_suggestions"] == ["add type hints", "add docstring"]

    def test_generate_fix_patches(self):
        """Test generating fix patches from AI suggestions."""
        suggestions = ["Add type hints", "Add docstring"]
        file_path = "test.py"

        patches = self.handler.generate_patches(file_path, suggestions)

        assert len(patches) == 2
        assert patches[0]["file"] == file_path
        assert patches[0]["suggestion"] == "Add type hints"
        assert patches[1]["file"] == file_path
        assert patches[1]["suggestion"] == "Add docstring"


class TestAIEnhancementIntegration:
    """Integration tests for AI enhancement."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = AIAnalyzer()
        self.handler = AIHandler()
        self.test_files = ["test.py"]

    @pytest.mark.asyncio
    async def test_end_to_end_ai_analysis(self):
        """Test end-to-end AI analysis workflow."""
        with patch.object(self.analyzer, "_get_ai_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.analyze = AsyncMock(
                return_value={
                    "suggestions": ["Add type hints", "Add docstring"],
                    "score": 0.85,
                    "issues": ["Missing type hints", "No docstring"],
                }
            )
            mock_get_provider.return_value = mock_provider

            # Run AI analysis
            result = await self.analyzer.analyze_code_quality(self.test_files)

            # Process results
            processed = self.handler.process_result(result)

            # Validate results
            assert processed["success"] is True
            assert len(processed["suggestions"]) == 2
            assert processed["score"] == 0.85

    @pytest.mark.asyncio
    async def test_ai_enhanced_quality_engine_integration(self):
        """Test AI enhancement integration with Quality Engine.

        Patches the engine's real seams: run_tool (imported into engine) and the
        initialize_llm_manager / run_ai_analysis pair the engine imports from the
        quality_engine.ai package at call time.
        """
        from codeflow_engine.actions.quality_engine.models import (
            QualityInputs,
            ToolResult,
        )
        from codeflow_engine.utils.volume_utils import QualityMode

        engine = make_engine()

        tool_result = ToolResult(
            issues=[
                {"filename": "test.py", "message": "Missing type hints"},
                {"filename": "test.py", "message": "No docstring"},
            ],
            files_with_issues=["test.py"],
            summary="ruff: 2 issues",
            execution_time=0.1,
        )
        ai_result = {
            "issues": [],
            "files_with_issues": [],
            "summary": "AI review: add type hints",
        }

        with (
            patch(
                "codeflow_engine.actions.quality_engine.engine.run_tool",
                AsyncMock(return_value=tool_result),
            ) as mock_run_tool,
            patch(
                "codeflow_engine.actions.quality_engine.ai.initialize_llm_manager",
                AsyncMock(return_value=MagicMock()),
            ),
            patch(
                "codeflow_engine.actions.quality_engine.ai.run_ai_analysis",
                AsyncMock(return_value=ai_result),
            ) as mock_ai_analysis,
        ):
            inputs = QualityInputs(
                mode=QualityMode.AI_ENHANCED,
                files=self.test_files,
                enable_ai_agents=True,
            )
            result = await engine.execute(inputs, {})

        mock_run_tool.assert_called_once()
        mock_ai_analysis.assert_called_once()
        assert mock_ai_analysis.call_args.args[0] == self.test_files

        assert result.ai_enhanced is True
        assert result.ai_summary == "AI review: add type hints"
        assert result.total_issues_found == 2
        assert set(result.issues_by_tool) == {STUB_TOOL_NAME, "ai_analysis"}
        # QualityOutputs.success means "no issues found", not "the run worked"
        assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__])
