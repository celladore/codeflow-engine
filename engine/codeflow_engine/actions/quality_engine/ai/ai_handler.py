"""
AI Handler for Quality Engine

Handles AI interactions for quality analysis.
"""

import time
from typing import TYPE_CHECKING, Any

import structlog

from codeflow_engine.actions.quality_engine.models import ToolResult


if TYPE_CHECKING:
    from codeflow_engine.actions.llm.manager import ActionLLMProviderManager

logger = structlog.get_logger(__name__)


class AIHandler:
    """Backward-compatible helper for post-processing AI analysis results."""

    def process_result(self, result: dict[str, Any]) -> dict[str, Any]:
        processed = dict(result)
        processed.setdefault("suggestions", [])
        processed.setdefault("issues", [])
        processed.setdefault("score", 0.0)
        processed["processed"] = True
        processed.setdefault("success", True)
        return processed

    def filter_suggestions(
        self, suggestions: list[str], min_priority: str = "medium"
    ) -> list[str]:
        if min_priority == "medium":
            return [s for s in suggestions if "minor" not in s.lower()]
        return suggestions

    def prioritize_suggestions(self, suggestions: list[str]) -> list[str]:
        def rank(item: str) -> tuple[int, str]:
            lowered = item.lower()
            if "security" in lowered:
                return (0, item)
            if "performance" in lowered:
                return (1, item)
            if "type hints" in lowered:
                return (2, item)
            return (3, item)

        return sorted(suggestions, key=rank)

    def format_for_output(self, suggestions: list[str]) -> str:
        lines = ["AI Suggestions:"]
        lines.extend(f"- {suggestion}" for suggestion in suggestions)
        return "\n".join(lines)

    def merge_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        suggestions: list[str] = []
        scores: list[float] = []
        for result in results:
            suggestions.extend(result.get("suggestions", []))
            if isinstance(result.get("score"), (int, float)):
                scores.append(float(result["score"]))
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return {"suggestions": suggestions, "score": avg_score, "success": True}

    def validate_result(self, result: dict[str, Any]) -> bool:
        return isinstance(result.get("suggestions"), list)

    def extract_actionable_items(self, result: dict[str, Any]) -> list[str]:
        items: list[str] = []
        for key in ("suggestions", "issues", "recommendations"):
            value = result.get(key, [])
            if isinstance(value, list):
                items.extend(str(item) for item in value)
        return items

    async def apply_suggestions(
        self, file_content: str, suggestions: list[str]
    ) -> dict[str, Any]:
        updated_content = file_content
        applied: list[str] = []
        for suggestion in suggestions:
            updated_content = await self._apply_suggestion(updated_content, suggestion)
            applied.append(suggestion.lower())
        return {
            "modified": updated_content != file_content,
            "content": updated_content,
            "applied_suggestions": applied,
        }

    async def _apply_suggestion(self, file_content: str, _suggestion: str) -> str:
        return file_content

    def generate_patches(
        self, file_path: str, suggestions: list[str]
    ) -> list[dict[str, str]]:
        return [
            {"file": file_path, "suggestion": suggestion} for suggestion in suggestions
        ]


async def run_ai_analysis(
    files: list[str],
    llm_manager: Any,
    provider_name: str = "openai",
    model: str = "gpt-4",
) -> dict[str, Any] | None:
    """Run AI-enhanced code analysis.

    Args:
        files: List of files to analyze
        llm_manager: The LLM provider manager
        provider_name: Optional specific provider to use
        model: Optional specific model to use

    Returns:
        Dictionary with analysis results or None if analysis fails
    """
    try:
        # Lazy import to avoid circular dependencies
        from codeflow_engine.actions.quality_engine.ai.ai_modes import (
            run_ai_analysis as run_analysis,
        )

        # Get available providers from the manager
        available_providers = []
        if hasattr(llm_manager, "list_providers"):
            available_providers = llm_manager.list_providers()
        elif hasattr(llm_manager, "get_available_providers"):
            available_providers = llm_manager.get_available_providers()
        # Early return if no providers are available
        if not available_providers:
            logger.error("No LLM providers are available for AI analysis")
            return None

        # Determine the selected provider
        selected_provider = provider_name
        if provider_name not in available_providers:
            # Use manager default if specified provider is not available
            if hasattr(llm_manager, "get_default_provider"):
                default_provider = llm_manager.get_default_provider()
                if default_provider and default_provider in available_providers:
                    selected_provider = default_provider
                    logger.info(
                        "Provider '%s' not available, using default: %s",
                        provider_name,
                        selected_provider,
                    )
                else:
                    # Use first available provider as fallback
                    selected_provider = available_providers[0]
                    logger.info(
                        "Provider '%s' not available, using first available: %s",
                        provider_name,
                        selected_provider,
                    )
            else:
                # Use first available provider as fallback
                selected_provider = available_providers[0]
                logger.info(
                    "Provider '%s' not available, using first available: %s",
                    provider_name,
                    selected_provider,
                )

        # Get the provider object and align model with provider's default if available
        provider_obj = None
        if hasattr(llm_manager, "get_provider"):
            provider_obj = llm_manager.get_provider(selected_provider)
        if (
            provider_obj
            and hasattr(provider_obj, "default_model")
            and provider_obj.default_model
        ):
            model = provider_obj.default_model
            logger.info("Using provider default model: %s", model)
        # Update provider_name to the resolved selected_provider
        provider_name = selected_provider

        logger.info(
            "Starting AI-enhanced analysis",
            file_count=len(files),
            provider=provider_name,
            model=model,
        )
        start_time = time.time()

        # Run the AI analysis
        result = await run_analysis(files, llm_manager, provider_name, model)
        if result is None:
            logger.warning("AI analysis returned None result")
            return None
        else:
            execution_time = time.time() - start_time
            logger.info(
                "AI analysis completed",
                issues_found=len(result.get("issues", [])),
                execution_time=f"{execution_time:.2f}s",
            )

            # Add execution time to the result
            result["execution_time"] = execution_time

            return result

    except Exception as e:
        logger.exception("Error running AI analysis", error=str(e))
        return None


async def initialize_llm_manager() -> "ActionLLMProviderManager | None":
    """Initialize the LLM manager for AI analysis.

    Delegates to the quality engine's single initializer rather than building a
    second manager here. Two initializers meant two provider stacks and only one of
    them could be routed through Sluice — the other was a standing way for quality
    analysis to reach an LLM untagged. Its Sluice tag is `quality-analyzer`: same
    calling feature, so it shares the label rather than adding a series.

    Returns:
        Initialized LLM manager or None if initialization fails
    """
    from codeflow_engine.actions.quality_engine.ai.llm_manager import (
        initialize_llm_manager as _initialize_llm_manager,
    )

    return await _initialize_llm_manager()


def create_tool_result_from_ai_analysis(ai_result: dict[str, Any]) -> ToolResult:
    """Convert AI analysis results to a ToolResult.

    Args:
        ai_result: The raw AI analysis result

    Returns:
        A ToolResult instance containing the AI analysis results
    """
    return ToolResult(
        issues=ai_result.get("issues", []),
        files_with_issues=ai_result.get("files_with_issues", []),
        summary=ai_result.get("summary", "AI analysis completed"),
        execution_time=ai_result.get("execution_time", 0.0),
    )
