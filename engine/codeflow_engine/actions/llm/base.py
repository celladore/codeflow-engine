"""
Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
import os
from typing import Any

from codeflow_engine.actions.llm.types import LLMResponse
from codeflow_engine.core.llm.sluice import SluiceMetadataError, is_sluice_base_url


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.api_key = config.get("api_key") or os.getenv(config.get("api_key_env", ""))
        self.base_url = config.get("base_url")
        self.default_model = config.get("default_model")
        self.name = config.get("name", self.__class__.__name__.lower().replace("provider", ""))

        # These providers build their own request bodies and none of them sends
        # Sluice ADR 17 metadata, so pointing one at the gateway via `base_url` is a
        # silent route to untagged traffic — the cheapest wrong way to "onboard".
        # Refuse it at construction and name the supported path instead.
        if is_sluice_base_url(self.base_url):
            raise SluiceMetadataError(
                f"Provider {self.name!r} is configured with base_url pointing at the "
                "Sluice gateway, but this provider stack does not send the "
                "metadata.app / metadata.agent fields that Sluice ADR 17 requires. "
                "Use codeflow_engine.core.llm.SluiceProvider instead."
            )

    @abstractmethod
    def complete(self, request: dict[str, Any]) -> LLMResponse:
        """Complete a chat conversation."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
