"""
LLM Manager for Quality Engine

Manages LLM interactions for quality analysis.
"""

import logging
import os
from typing import Any

from codeflow_engine.actions.llm.manager import ActionLLMProviderManager
from codeflow_engine.core.llm.sluice import SluiceAgent, SluiceConfig

logger = logging.getLogger(__name__)


async def initialize_llm_manager() -> ActionLLMProviderManager | None:
    """
    Initialize the LLM provider manager for AI-enhanced quality analysis.

    Returns:
        ActionLLMProviderManager: Configured LLM manager or None if no provider is
        available.
    """
    try:
        # Ordered: the first entry becomes the manager's default provider, and the
        # rest stay as fallbacks.
        providers: dict[str, dict[str, Any]] = {}

        # Prefer the Sluice gateway when configured: it centralises spend tracking
        # and enforces per-key budgets. Added before the vendor providers because the
        # default is derived from insertion order; those stay as fallbacks for
        # deployments with no gateway. Tagged `quality-analyzer` per Sluice ADR 17.
        #
        # One tag covers the whole quality engine's AI analysis — ai_modes, the
        # AICodeAnalyzer and the security/architecture prompt variants are all the
        # same calling feature. Splitting them per prompt would multiply Prometheus
        # series to answer a question nobody asks; "what did quality analysis cost"
        # is the useful rollup.
        if SluiceConfig.from_env() is not None:
            providers["sluice"] = {"agent": SluiceAgent.QUALITY_ANALYZER}
            logger.info("Sluice gateway provider configured for quality analysis")

        providers["openai"] = {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "default_model": "gpt-4",
            "max_tokens": 4000,
            "temperature": 0.1,
        }
        providers["anthropic"] = {
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "default_model": "claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "temperature": 0.1,
        }

        config: dict[str, Any] = {
            "providers": providers,
            "fallback_order": [name for name in providers if name != "sluice"],
            "default_provider": next(iter(providers)),
        }

        llm_manager = ActionLLMProviderManager(config)

        # Availability is self-reported by each provider, so no probe request is
        # needed. A test completion per initialization would be billed spend tagged
        # `quality-analyzer` that analyses nothing.
        available = llm_manager.get_available_providers()
        if not available:
            logger.warning("No LLM providers available for AI-enhanced analysis")
            return None

        logger.info("LLM manager initialized with providers: %s", available)
        return llm_manager

    except Exception as e:
        logger.exception(f"Failed to initialize LLM manager: {e}")
        return None


def get_llm_config_for_quality_analysis() -> dict[str, Any]:
    """
    Get configuration for LLM-based quality analysis.

    Returns:
        dict: Configuration for quality analysis LLM usage
    """
    return {
        "max_tokens": 4000,
        "temperature": 0.1,
        "system_prompt": """You are CodeQualityGPT, an expert code review assistant specialized in identifying improvements,
optimizations, and potential issues in code. Your task is to analyze code snippets and provide detailed,
actionable feedback that goes beyond what static analysis tools can find.

Focus on the following aspects:
1. Architecture and design patterns
2. Performance optimization opportunities
3. Security vulnerabilities or risks
4. Maintainability and readability concerns
5. Edge case handling and robustness
6. Business logic flaws or inconsistencies
7. API design and usability

Provide your feedback in a structured JSON format with:
- Specific issues identified
- Why they matter
- How to fix them
- A confidence score (0-1) for each suggestion""",
        "preferred_providers": ["openai", "anthropic"],
        "fallback_providers": ["groq", "mistral"],
    }
