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

    #: Whether this provider sends the Sluice ADR 17 `metadata.app` /
    #: `metadata.agent` block on every request. Default false: most providers in
    #: this stack build their own request bodies with no metadata, so pointing one
    #: at the gateway via `base_url` is a silent route to untagged traffic.
    #:
    #: A class-level capability rather than a config key on purpose — a
    #: caller-supplied flag would let any misconfiguration assert compliance it
    #: does not have, which is the failure this guard exists to prevent.
    SUPPORTS_SLUICE_REQUEST_METADATA: bool = False

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.api_key = config.get("api_key") or os.getenv(config.get("api_key_env", ""))
        self.base_url = config.get("base_url")
        self.default_model = config.get("default_model")
        self.name = config.get("name", self.__class__.__name__.lower().replace("provider", ""))

        # Refuse a gateway route from a provider that cannot tag it, and name the
        # supported path instead. Providers that do tag opt in above.
        if is_sluice_base_url(self.base_url) and not self.SUPPORTS_SLUICE_REQUEST_METADATA:
            raise SluiceMetadataError(
                f"Provider {self.name!r} is configured with base_url pointing at the "
                "Sluice gateway, but does not send the metadata.app / metadata.agent "
                "fields that Sluice ADR 17 requires. Use the SluiceProvider in "
                "codeflow_engine.actions.llm.providers.sluice, or "
                "codeflow_engine.core.llm.SluiceProvider for a typed agent."
            )

    @abstractmethod
    def complete(self, request: dict[str, Any]) -> LLMResponse:
        """Complete a chat conversation."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
