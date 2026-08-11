"""
Quality Engine - Main engine for running quality analysis tools.
"""

import os
from typing import Any

import structlog

from codeflow_engine.actions.base.action import Action
from codeflow_engine.actions.quality_engine.config import load_config
from codeflow_engine.actions.quality_engine.handler_registry import HandlerRegistry
from codeflow_engine.actions.quality_engine.models import (
    QualityInputs,
    QualityMode,
    QualityOutputs,
)
from codeflow_engine.actions.quality_engine.platform_detector import PlatformDetector
from codeflow_engine.actions.quality_engine.tool_runner import run_tool
from codeflow_engine.actions.quality_engine.tools.registry import ToolRegistry
from codeflow_engine.utils.volume_utils import get_volume_level_name

logger = structlog.get_logger(__name__)


class QualityEngine(Action):
    """Engine for all code quality operations"""

    id = "quality_engine"

    def __init__(
        self,
        config_path: str = "pyproject.toml",
        tool_registry: ToolRegistry | None = None,
        handler_registry: HandlerRegistry | None = None,
        config: Any | None = None,
        skip_windows_check: bool = False,
    ):
        super().__init__(
            name="quality_engine",
            description="Engine for all code quality operations",
            version="1.0.0",
        )

        # Initialize tool registry
        if tool_registry is None:
            from codeflow_engine.actions.quality_engine.tools import discover_tools

            tools = discover_tools()
            self.tool_registry = ToolRegistry()
            for tool_class in tools:
                self.tool_registry.register(tool_class)
        else:
            self.tool_registry = tool_registry

        # Initialize platform detector
        self.platform_detector = PlatformDetector()
        self.skip_windows_check = skip_windows_check

        # Show Windows warning if needed (unless skipped)
        if (
            not self.skip_windows_check
            and self.platform_detector.should_show_windows_warning()
        ):
            self._show_windows_warning()

        # Get tools from registry and filter for platform compatibility
        tools_list = self.tool_registry.get_all_tools()
        self.tools = {tool.name: tool for tool in tools_list}
        self.tools = self._filter_tools_for_platform()

        # Apply tool substitutions for Windows
        self._apply_tool_substitutions()

        self.handler_registry = handler_registry
        self.config = config or load_config(config_path)
        self.llm_manager: Any = None

        logger.info(
            "Quality Engine initialized",
            default_mode="smart",
            discovered_tools=list(self.tools.keys()),
            platform=self.platform_detector.detect_platform(),
        )

    def _show_windows_warning(self):
        """Show Windows-specific warnings and recommendations."""
        platform_info = self.platform_detector.detect_platform()
        limitations = self.platform_detector.get_windows_limitations()
        recommendations = self.platform_detector.get_windows_recommendations()

        logger.warning(
            "Running on Windows - some tools may have limitations",
            platform_info=platform_info,
            limitations=limitations,
            recommendations=recommendations,
        )

        if limitations:
            for _limitation in limitations:
                pass
        if recommendations:
            for _rec in recommendations:
                pass

    def _filter_tools_for_platform(self) -> dict[str, Any]:
        """Filter tools based on platform compatibility."""
        all_tool_names = list(self.tools.keys())
        available_tools = self.platform_detector.get_available_tools(all_tool_names)

        filtered_tools = {}
        for tool_name in available_tools:
            if tool_name in self.tools:
                filtered_tools[tool_name] = self.tools[tool_name]

        return filtered_tools

    def _apply_tool_substitutions(self) -> None:
        """Apply platform-specific tool substitutions."""
        if self.platform_detector.is_windows:
            # Substitute CodeQL with Semgrep on Windows
            if "codeql" in self.tools and "semgrep" in self.tools:
                logger.info(
                    "Substituting CodeQL with Semgrep for Windows compatibility"
                )
                # Remove CodeQL and keep Semgrep
                self.tools.pop("codeql", None)

    def _get_tool_config(self, tool_name: str) -> dict[str, Any]:
        """Get configuration for a specific tool."""
        if not self.config:
            return {"enabled": True, "config": {}}

        # Handle Pydantic model
        if hasattr(self.config, "tools"):
            tools_config = getattr(self.config, "tools", {})
            if isinstance(tools_config, dict):
                return tools_config.get(tool_name, {"enabled": True, "config": {}})

        # Fallback to dictionary access
        try:
            if hasattr(self.config, "get") and callable(
                getattr(self.config, "get", None)
            ):
                return self.config.get("tools", {}).get(
                    tool_name, {"enabled": True, "config": {}}
                )
            else:
                return {"enabled": True, "config": {}}
        except (AttributeError, TypeError):
            return {"enabled": True, "config": {}}

    def _validate_volume(self, volume: int) -> int:
        """Validate and clamp volume to valid range."""
        if not isinstance(volume, int):
            msg = f"Volume must be an integer, got {type(volume).__name__}"
            raise ValueError(msg)
        return max(0, min(1000, volume))  # Clamp to 0-1000 range

    async def _run_auto_fix(
        self, inputs: QualityInputs, files_to_check: list[str]
    ) -> tuple[bool, int, list[str], str | None, list[str] | None]:
        """Run auto-fix process and return results."""
        try:
            logger.info(
                "Starting auto-fix process",
                fix_types=inputs.fix_types,
                max_fixes=inputs.max_fixes,
            )

            # Import AI Linting Fixer
            from codeflow_engine.actions.ai_linting_fixer.ai_linting_fixer import (
                AILintingFixer,
            )
            from codeflow_engine.actions.ai_linting_fixer.models import (
                AILintingFixerInputs,
            )

            # Prepare fixer inputs
            target_path = files_to_check[0] if files_to_check else "."
            if isinstance(target_path, str) and target_path == ".":
                target_path = "."

            fixer_inputs = AILintingFixerInputs(
                target_path=target_path,
                fix_types=inputs.fix_types
                or ["E501", "F401", "F841", "E722", "E302", "E305"],
                max_fixes_per_run=inputs.max_fixes,
                provider=inputs.ai_provider,
                model=inputs.ai_model,
                dry_run=inputs.dry_run,
                max_workers=2,  # Conservative for quality engine integration
                use_specialized_agents=True,
                create_backups=True,
            )

            # Run the AI Linting Fixer
            try:
                with AILintingFixer() as fixer:
                    if hasattr(fixer, "run") and callable(getattr(fixer, "run", None)):
                        fix_result = fixer.run(fixer_inputs)
                    else:
                        msg = "AILintingFixer does not have a callable 'run' method"
                        raise RuntimeError(msg)
            except Exception as fixer_error:
                logger.exception(
                    "Failed to initialize AILintingFixer", error=str(fixer_error)
                )
                return (
                    False,
                    0,
                    [],
                    None,
                    [f"Fixer initialization failed: {fixer_error}"],
                )

            # Update results with fix information
            total_issues_fixed = fix_result.issues_fixed
            files_modified = fix_result.files_modified
            fix_summary = f"Fixed {fix_result.issues_fixed} issues across {len(fix_result.files_modified)} files"

            logger.info(
                "Auto-fix completed successfully",
                issues_fixed=fix_result.issues_fixed,
                files_modified=len(fix_result.files_modified),
                success=fix_result.success,
            )

            return True, total_issues_fixed, files_modified, fix_summary, None

        except Exception as e:
            logger.exception("Auto-fix failed", error=str(e))
            fix_errors = [f"Auto-fix failed: {e!s}"]
            return False, 0, [], None, fix_errors

    def _determine_tools_for_mode(
        self, mode: QualityMode, files: list[str], volume: int = 500
    ) -> list[str]:
        """Determine which tools to run based on mode and context."""
        available_tools = self.tool_registry.get_available_tools()

        if mode == QualityMode.ULTRA_FAST:
            # Only the fastest, most essential tools
            return ["ruff"]
        elif mode == QualityMode.FAST:
            # Essential tools for quick feedback
            return ["ruff", "mypy"]
        elif mode == QualityMode.COMPREHENSIVE:
            # All available tools
            return available_tools
        elif mode == QualityMode.AI_ENHANCED:
            # Core tools plus AI analysis
            core_tools = ["ruff", "mypy", "bandit", "interrogate", "radon"]
            if "ai_feedback" in available_tools:
                core_tools.append("ai_feedback")
            return core_tools
        elif mode == QualityMode.SMART:
            # Context-aware tool selection
            return self._select_smart_tools(files, volume, available_tools)

        # Default to comprehensive if mode is not recognized
        return available_tools

    def _select_smart_tools(
        self, files: list[str], volume: int, available_tools: list[str]
    ) -> list[str]:
        """Select tools intelligently based on file context and volume."""
        selected_tools = []

        # Always include essential tools
        essential_tools = ["ruff"]
        for tool in essential_tools:
            if tool in available_tools:
                selected_tools.append(tool)

        # Analyze file characteristics
        file_extensions = set()
        total_lines = 0
        has_python_files = False
        has_js_files = False

        for file_path in files:
            if file_path.endswith(".py"):
                has_python_files = True
                file_extensions.add(".py")
            elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
                has_js_files = True
                file_extensions.add(".js")

            # Count lines (rough estimate)
            try:
                with open(file_path, encoding="utf-8") as f:
                    total_lines += len(f.readlines())
            except Exception:
                pass

        # Add type checking for Python files
        if has_python_files and "mypy" in available_tools:
            selected_tools.append("mypy")

        # Add ESLint for JavaScript files (only if ESLint is properly configured)
        if has_js_files and "eslint" in available_tools:
            # Check if ESLint is actually available before adding it
            try:
                from codeflow_engine.actions.quality_engine.tools.eslint_tool import (
                    ESLintTool,
                )

                eslint_tool = ESLintTool()
                if eslint_tool.is_available():
                    selected_tools.append("eslint")
                else:
                    logger.warning(
                        "ESLint is not available - skipping JavaScript/TypeScript linting"
                    )
            except Exception as e:
                logger.warning(
                    "Failed to check ESLint availability: %s - skipping JavaScript/TypeScript linting",
                    e,
                )

        # Add security scanning for higher volumes
        if volume > 300 and "bandit" in available_tools:
            selected_tools.append("bandit")

        # Add complexity analysis for larger codebases
        if total_lines > 1000 and "radon" in available_tools:
            selected_tools.append("radon")

        # Add documentation checking for higher volumes
        if volume > 400 and "interrogate" in available_tools:
            selected_tools.append("interrogate")

        # Add dependency scanning for higher volumes
        if volume > 500 and "dependency_scanner" in available_tools:
            selected_tools.append("dependency_scanner")

        # Add performance analysis for very high volumes
        if volume > 700 and "performance_analyzer" in available_tools:
            selected_tools.append("performance_analyzer")

        # Add AI feedback for high volumes
        if volume > 600 and "ai_feedback" in available_tools:
            selected_tools.append("ai_feedback")

        return selected_tools

    async def execute(
        self, inputs: QualityInputs, context: dict[str, Any], volume: int | None = None
    ) -> QualityOutputs:
        """Execute the quality engine with the given inputs and volume level.

        Args:
            inputs: Quality engine input parameters
            context: Context dictionary for the execution
            volume: Volume level from 0-1000 that influences quality strictness.
                   If None, uses inputs.volume if set, otherwise defaults to 500.

        Returns:
            QualityOutputs with the results of the quality checks

        Raises:
            ValueError: If volume is not an integer or is outside the 0-1000 range
        """
        # Determine the volume to use, with proper precedence
        if volume is None:
            volume = getattr(inputs, "volume", None)
            if volume is None:
                volume = 500  # Default to 500 if not specified

        # Validate volume is an integer and within range
        volume = self._validate_volume(volume)

        # Apply volume settings to inputs if volume was explicitly provided AND no explicit mode was set
        # This prevents volume settings from overriding CLI mode arguments
        if (
            hasattr(inputs, "apply_volume_settings")
            and inputs.mode == QualityMode.SMART
        ):
            # Only apply volume settings if we're in the default SMART mode
            # This means no explicit mode was provided via CLI
            inputs.apply_volume_settings(volume)

        # Get volume level name for logging
        volume_level = get_volume_level_name(
            volume
        )  # Directly use the imported function

        logger.info(
            "Executing Quality Engine",
            mode=inputs.mode,
            volume=volume,
            volume_level=volume_level,
        )

        # Determine files to check
        files_to_check = inputs.files or []

        # If no files are provided, return early with success
        if not files_to_check:
            logger.info("No files provided for analysis")
            return QualityOutputs(
                success=True,
                total_issues_found=0,
                total_issues_fixed=0,
                files_modified=[],
                issues_by_tool={},
                files_by_tool={},
                tool_execution_times={},
                summary="No files provided for analysis",
                ai_enhanced=False,
                ai_summary=None,
            )

        # Determine tools to run based on mode and volume
        tools_to_run = self._determine_tools_for_mode(
            inputs.mode, files_to_check, volume=volume
        )

        # Log tool selection
        logger.info(
            "Tool selection completed",
            mode=inputs.mode,
            tools_selected=tools_to_run,
            total_tools_available=len(self.tools),
        )

        if not tools_to_run:
            logger.warning("No tools available for the specified mode and files")
            return QualityOutputs(
                success=True,
                total_issues_found=0,
                total_issues_fixed=0,
                files_modified=[],
                issues_by_tool={},
                files_by_tool={},
                tool_execution_times={},
                summary="No tools available for analysis",
                ai_enhanced=False,
                ai_summary=None,
            )

        # Initialize results
        results = {}

        # Add detailed logging for comprehensive mode
        if inputs.mode == QualityMode.COMPREHENSIVE:
            logger.info(
                "Comprehensive mode activated",
                tools=tools_to_run,
                file_count=len(files_to_check),
                file_types=list(
                    {os.path.splitext(f)[1] for f in files_to_check if "." in f}
                ),
            )
        else:
            logger.info(
                f"{inputs.mode.value.title()} mode activated",
                tools=tools_to_run,
                file_count=len(files_to_check),
            )

        # Run tools in parallel for better performance
        tool_tasks = []
        for tool_name in tools_to_run:
            tool_instance = self.tools.get(tool_name)
            if not tool_instance:
                logger.warning("Tool not available", tool=tool_name)
                continue

            tool_config = self._get_tool_config(tool_name)

            # Handle both dict and Pydantic model
            enabled = True
            if isinstance(tool_config, dict):
                enabled = tool_config.get("enabled", True)
            elif hasattr(tool_config, "enabled"):
                enabled = tool_config.enabled

            if enabled:
                task = run_tool(
                    tool_name=tool_name,
                    tool_instance=tool_instance,
                    files=files_to_check,
                    tool_config=(
                        tool_config.get("config", {})
                        if isinstance(tool_config, dict)
                        else {}
                    ),
                    handler_registry=self.handler_registry,
                )
                tool_tasks.append((tool_name, task))

        # Execute tools and gather results
        for tool_name, task in tool_tasks:
            tool_result = await task
            if tool_result:
                results[tool_name] = tool_result

        # Handle AI-enhanced mode
        ai_result = None
        ai_summary = None

        if inputs.mode == QualityMode.AI_ENHANCED and inputs.enable_ai_agents:
            # Lazy load the LLM manager if needed
            if not self.llm_manager:
                from codeflow_engine.actions.quality_engine.ai import (
                    initialize_llm_manager,
                )

                self.llm_manager = await initialize_llm_manager()

            if self.llm_manager:
                from codeflow_engine.actions.quality_engine.ai import run_ai_analysis

                # Both are optional: unset defers to the manager's default provider
                # and that provider's default model. Hardcoding a vendor and
                # `gpt-4` here would route past the Sluice gateway even when it is
                # configured, and ask it for a model its key is not provisioned for.
                ai_result = await run_ai_analysis(
                    files_to_check,
                    self.llm_manager,
                    provider_name=inputs.ai_provider,
                    model=inputs.ai_model,
                )

                if ai_result:
                    from codeflow_engine.actions.quality_engine.ai import (
                        create_tool_result_from_ai_analysis,
                    )

                    results["ai_analysis"] = create_tool_result_from_ai_analysis(
                        ai_result
                    )
                    ai_summary = ai_result.get("summary")

        # Handle auto-fix if requested
        auto_fix_applied = False
        fix_summary = None
        fix_errors = None
        total_issues_fixed = 0
        files_modified: list[str] = []

        if inputs.auto_fix and inputs.enable_ai_agents:
            (
                auto_fix_applied,
                total_issues_fixed,
                files_modified,
                fix_summary,
                fix_errors,
            ) = await self._run_auto_fix(inputs, files_to_check)

        # Build the comprehensive summary
        from codeflow_engine.actions.quality_engine.summary import (
            build_comprehensive_summary,
        )

        summary = build_comprehensive_summary(results, ai_summary)

        # Collect issues and files by tool
        issues_by_tool = {
            tool_name: result.issues for tool_name, result in results.items()
        }
        files_by_tool = {
            tool_name: result.files_with_issues for tool_name, result in results.items()
        }

        # Get execution times by tool
        tool_execution_times = {
            tool_name: result.execution_time for tool_name, result in results.items()
        }

        # Calculate total issues
        total_issues_found = sum(len(result.issues) for result in results.values())

        # Get unique files with issues
        unique_files_with_issues = set()
        for result in results.values():
            unique_files_with_issues.update(result.files_with_issues)

        return QualityOutputs(
            success=total_issues_found == 0,
            total_issues_found=total_issues_found,
            total_issues_fixed=total_issues_fixed,
            files_modified=files_modified,
            issues_by_tool=issues_by_tool,
            files_by_tool=files_by_tool,
            tool_execution_times=tool_execution_times,
            summary=summary,
            ai_enhanced=inputs.mode == QualityMode.AI_ENHANCED
            and ai_result is not None,
            ai_summary=ai_summary,
            auto_fix_applied=auto_fix_applied,
            fix_summary=fix_summary,
            fix_errors=fix_errors,
        )

    async def run(self, inputs: QualityInputs) -> QualityOutputs:
        """Execute the quality engine with the given inputs"""
        # Create an empty context dictionary to satisfy the base class contract
        return await self.execute(inputs, {})


# Factory function to create a quality engine with dependencies
def create_engine(
    config_path: str = "pyproject.toml",
    tool_registry: ToolRegistry | None = None,
    handler_registry: HandlerRegistry | None = None,
    config: Any | None = None,
) -> QualityEngine:
    """Create a quality engine with the given dependencies."""
    return QualityEngine(
        config_path=config_path,
        tool_registry=tool_registry,
        handler_registry=handler_registry,
        config=config,
    )


def create_quality_engine(
    config_path: str = "pyproject.toml",
    tool_registry: ToolRegistry | None = None,
    handler_registry: HandlerRegistry | None = None,
    config: Any | None = None,
) -> QualityEngine:
    """Backward-compatible alias for creating a quality engine."""
    return create_engine(
        config_path=config_path,
        tool_registry=tool_registry,
        handler_registry=handler_registry,
        config=config,
    )
