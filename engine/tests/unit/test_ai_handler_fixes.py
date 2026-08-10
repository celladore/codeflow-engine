#!/usr/bin/env python3
"""
Test AI Handler Fixes

Guards the quality engine's AI handler against the two regressions it was
written for: calling a provider-manager API that no longer exists, and blowing
up (rather than degrading) when no API keys are configured.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from codeflow_engine.actions.quality_engine.ai.ai_handler import initialize_llm_manager
from codeflow_engine.ai.core.providers.manager import LLMProviderManager
from codeflow_engine.config import CodeFlowConfig


# Methods initialize_llm_manager() calls on the manager. If any of them is
# renamed or dropped, the handler breaks at runtime rather than at import time,
# so pin the contract here.
REQUIRED_MANAGER_METHODS = (
    "get_provider",
    "set_default_provider",
    "list_providers",
    "initialize",
)


@pytest.mark.parametrize("method_name", REQUIRED_MANAGER_METHODS)
def test_manager_exposes_api_used_by_handler(method_name):
    """LLMProviderManager must keep the surface the AI handler depends on."""
    assert callable(getattr(LLMProviderManager, method_name, None))


@pytest.mark.asyncio
async def test_initialize_llm_manager_returns_none_without_api_keys():
    """Missing credentials must degrade to None, not raise."""
    with patch.dict(
        os.environ, {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": ""}, clear=False
    ):
        assert await initialize_llm_manager() is None


@pytest.mark.asyncio
async def test_initialize_llm_manager_builds_core_provider_manager():
    """The handler must construct the core manager with a CodeFlowConfig.

    The legacy codeflow_engine.actions.llm.manager.LLMProviderManager takes a
    different constructor, so binding to the wrong one fails here.
    """
    with patch(
        "codeflow_engine.ai.core.providers.manager.LLMProviderManager"
    ) as mock_manager_cls:
        manager = mock_manager_cls.return_value
        manager.list_providers.return_value = ["openai"]
        manager.initialize = MagicMock()

        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": ""}, clear=False
        ):
            result = await initialize_llm_manager()

    mock_manager_cls.assert_called_once()
    (config_arg,) = mock_manager_cls.call_args.args
    assert isinstance(config_arg, CodeFlowConfig)
    assert result is manager
    manager.set_default_provider.assert_called_once_with("openai")
