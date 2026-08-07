"""Compatibility wrapper for grouped LLM provider imports."""

from codeflow_engine.actions._module_aliases import register_module_aliases
from codeflow_engine.actions.llm.providers import (
    AnthropicProvider,
    GroqProvider,
    MISTRAL_AVAILABLE,
    MistralProvider,
    OpenAIProvider,
    PerplexityProvider,
    SluiceProvider,
    TogetherAIProvider,
)
from codeflow_engine.actions.llm.providers.azure_openai import AzureOpenAIProvider

register_module_aliases(
    __name__,
    {
        "anthropic": "codeflow_engine.actions.llm.providers.anthropic",
        "azure_openai": "codeflow_engine.actions.llm.providers.azure_openai",
        "groq": "codeflow_engine.actions.llm.providers.groq",
        "mistral": "codeflow_engine.actions.llm.providers.mistral",
        "openai": "codeflow_engine.actions.llm.providers.openai",
        "sluice": "codeflow_engine.actions.llm.providers.sluice",
    },
)

__all__ = [
    "AnthropicProvider",
    "AzureOpenAIProvider",
    "GroqProvider",
    "MISTRAL_AVAILABLE",
    "MistralProvider",
    "OpenAIProvider",
    "PerplexityProvider",
    "SluiceProvider",
    "TogetherAIProvider",
]
