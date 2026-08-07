"""
LLM Providers package - Individual provider implementations.
"""

from typing import Any

# Import base class for inline implementations
from codeflow_engine.actions.llm.base import BaseLLMProvider
from codeflow_engine.actions.llm.providers.anthropic import AnthropicProvider
from codeflow_engine.actions.llm.providers.groq import GroqProvider
from codeflow_engine.actions.llm.types import LLMResponse


# Optional AI providers
try:
    from codeflow_engine.actions.llm.providers.mistral import MistralProvider

    MISTRAL_AVAILABLE = True
except ImportError:
    MistralProvider: Any = None
    MISTRAL_AVAILABLE = False
from codeflow_engine.actions.llm.providers.openai import OpenAIProvider
from codeflow_engine.actions.llm.providers.sluice import SluiceProvider


class PerplexityProvider(BaseLLMProvider):
    """Perplexity AI provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import openai

            self.client = openai.OpenAI(
                api_key=self.api_key, base_url="https://api.perplexity.ai"
            )
            self.available = True
        except ImportError:
            self.available = False

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        try:
            messages = request.get("messages", [])
            model = (
                request.get("model", self.default_model)
                or "llama-3.1-sonar-large-128k-online"
            )
            max_tokens = request.get("max_tokens", 1024)
            temperature = request.get("temperature", 0.7)

            # Filter out empty messages
            filtered_messages = [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in messages
                if m.get("content")
            ]

            # Call the API
            response = self.client.chat.completions.create(
                model=str(model),
                messages=filtered_messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Extract content and finish reason
            content = ""
            finish_reason = "stop"
            if (
                hasattr(response, "choices")
                and response.choices
                and len(response.choices) > 0
            ):
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                finish_reason = getattr(choice, "finish_reason", "stop") or "stop"

            # Extract usage information
            usage = None
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(
                        response.usage, "completion_tokens", 0
                    ),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }

            return LLMResponse(
                content=content,
                model=str(model),
                finish_reason=finish_reason,
                usage=usage,
            )

        except Exception as e:
            return LLMResponse.from_error(
                f"Error calling Perplexity API: {e!s}",
                str(request.get("model") or "llama-3.1-sonar-large-128k-online"),
            )

    def is_available(self) -> bool:
        return self.available and bool(self.api_key)


class TogetherAIProvider(BaseLLMProvider):
    """Together AI provider for open source models."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        try:
            import openai

            self.client = openai.OpenAI(
                api_key=self.api_key, base_url="https://api.together.xyz/v1"
            )
            self.available = True
        except ImportError:
            self.available = False

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        try:
            messages = request.get("messages", [])
            model = (
                request.get("model", self.default_model)
                or "meta-llama/Llama-2-70b-chat-hf"
            )
            max_tokens = request.get("max_tokens", 1024)
            temperature = request.get("temperature", 0.7)

            # Filter out empty messages
            filtered_messages = [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in messages
                if m.get("content")
            ]

            # Call the API
            response = self.client.chat.completions.create(
                model=str(model),
                messages=filtered_messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Extract content and finish reason
            content = ""
            finish_reason = "stop"
            if (
                hasattr(response, "choices")
                and response.choices
                and len(response.choices) > 0
            ):
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                finish_reason = getattr(choice, "finish_reason", "stop") or "stop"

            # Extract usage information
            usage = None
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(
                        response.usage, "completion_tokens", 0
                    ),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }

            return LLMResponse(
                content=content,
                model=str(model),
                finish_reason=finish_reason,
                usage=usage,
            )

        except Exception as e:
            return LLMResponse.from_error(
                f"Error calling Together AI API: {e!s}",
                str(request.get("model") or "meta-llama/Llama-2-70b-chat-hf"),
            )

    def is_available(self) -> bool:
        return self.available and bool(self.api_key)


# Export all providers
__all__ = [
    "AnthropicProvider",
    "GroqProvider",
    "OpenAIProvider",
    "PerplexityProvider",
    "SluiceProvider",
    "TogetherAIProvider",
]

# Add MistralProvider if available
if MISTRAL_AVAILABLE:
    __all__.append("MistralProvider")
