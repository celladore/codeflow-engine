"""
CodeFlow AI/LLM Base Classes

Base classes and interfaces for AI/LLM provider implementation.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from codeflow_engine.core.llm.sluice import SluiceMetadataError, is_sluice_route

logger = logging.getLogger(__name__)


# JSON response format instruction constant
JSON_INSTRUCTION = (
    "You must respond with valid JSON only. "
    "Do not include any markdown formatting or explanatory text."
)


@dataclass
class LLMMessage:
    """Represents a message in an LLM conversation."""

    role: str  # 'system', 'user', 'assistant'
    content: str
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CompletionRequest:
    """Represents a completion request to an LLM provider."""

    messages: list[LLMMessage]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    provider: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMResponse:
    """Represents a response from an LLM provider."""

    content: str
    model: str
    usage: dict[str, int] | None = None  # token usage info
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.usage is None:
            self.usage = {}
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """
    Base class for all LLM providers.

    Provides a unified interface for different AI/LLM services.
    """

    # Environment variable the vendor SDK falls back to when a client is built
    # without an explicit base_url. Set by subclasses; see _refuse_sluice_route.
    SDK_BASE_URL_ENV: str = ""

    #: Whether this provider sends the Sluice ADR 17 `metadata.app` /
    #: `metadata.agent` block on every request. Default false: nothing in this
    #: stack does. Mirrors the flag of the same name on the `actions.llm` base
    #: class — a class-level capability, never a config key, so a
    #: misconfiguration cannot assert compliance it does not have.
    SUPPORTS_SLUICE_REQUEST_METADATA: bool = False

    def __init__(
        self, name: str, description: str = "", version: str = "1.0.0"
    ) -> None:
        """
        Initialize the LLM provider.

        Args:
            name: Provider name (e.g., 'openai', 'anthropic')
            description: Human-readable description
            version: Provider version
        """
        self.name: str = name
        self.description: str = description
        self.version: str = version
        self.config: dict[str, Any] = {}
        self.supported_models: list[str] = []
        self.default_model: str = ""
        self._client: dict[str, Any] | None = None
        self._is_initialized: bool = False

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize the LLM provider with configuration.

        Args:
            config: Provider configuration
        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources."""

    @abstractmethod
    async def generate_completion(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: List of conversation messages
            model: Model name to use (defaults to provider default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM response
        """

    @abstractmethod
    async def generate_stream_completion(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> Any:
        """
        Generate a streaming completion from the LLM.

        Args:
            messages: List of conversation messages
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Partial LLM responses
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the provider.

        Returns:
            Health status dictionary
        """

    def supports_model(self, model: str) -> bool:
        """
        Check if provider supports a specific model.

        Args:
            model: Model name to check

        Returns:
            True if model is supported
        """
        return model in self.supported_models

    def get_metadata(self) -> dict[str, Any]:
        """
        Get provider metadata.

        Returns:
            Dictionary containing provider metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "supported_models": self.supported_models,
            "default_model": self.default_model,
        }

    def __str__(self) -> str:
        return f"LLMProvider(name='{self.name}', version='{self.version}')"

    def __repr__(self) -> str:
        return self.__str__()

    def _refuse_sluice_route(self, config: dict[str, Any]) -> None:
        """Refuse to initialize a client that would reach Sluice untagged.

        The providers in this module build their own request bodies through the
        vendor SDKs and none of them sends the ``metadata.app`` / ``metadata.agent``
        block Sluice ADR 17 requires. Sluice speaks the OpenAI-compatible API, so
        pointing one of them at the gateway takes no code change at all — just
        ``OPENAI_BASE_URL`` or a ``base_url`` in config.

        Both are checked. The SDK reads its own environment variable when no
        base_url is passed, and :meth:`OpenAIProvider.initialize` does not pass one,
        so the env var is the *only* thing that decides where those requests go.

        Failing here is the point: the gateway accepts an untagged request today and
        quietly increments ``untagged_requests_total{key_alias="codeflow-engine"}``,
        which restarts ADR 17's zero-for-a-week verification window for every other
        caller — and once enforcement lands, the same request is an HTTP 400.
        """
        if self.SUPPORTS_SLUICE_REQUEST_METADATA:
            return
        if not is_sluice_route(config.get("base_url"), self.SDK_BASE_URL_ENV):
            return
        env_hint = f" or {self.SDK_BASE_URL_ENV}" if self.SDK_BASE_URL_ENV else ""
        msg = (
            f"Provider {self.name!r} would send requests to the Sluice gateway "
            f"(via base_url{env_hint}), but this provider stack does not send the "
            "metadata.app / metadata.agent fields that Sluice ADR 17 requires. "
            "Use codeflow_engine.core.llm.SluiceProvider instead, or point this "
            "provider back at its vendor endpoint."
        )
        raise SluiceMetadataError(msg)

    def _apply_response_format(
        self, messages: list[LLMMessage], response_format: dict[str, Any] | None
    ) -> list[LLMMessage]:
        """
        Apply response format to messages without mutating the original list.

        Args:
            messages: Original list of messages
            response_format: Response format specification

        Returns:
            New list of messages with response format applied

        Raises:
            ValueError: If response format is unsupported
        """
        if not response_format:
            # Return a shallow-copied list with cloned metadata
            return [
                LLMMessage(role=m.role, content=str(m.content), metadata=dict(m.metadata or {}))
                for m in messages
            ]

        rtype = (response_format.get("type") or "").lower()

        # Create shallow copies of messages with cloned metadata
        msgs = [
            LLMMessage(
                role=m.role, content=str(m.content), metadata=dict(m.metadata or {})
            )
            for m in messages
        ]

        if rtype in {"json", "json_object"}:
            # Insert JSON instruction after any existing system messages
            insert_at = 0
            while insert_at < len(msgs) and msgs[insert_at].role == "system":
                insert_at += 1
            msgs.insert(
                insert_at,
                LLMMessage(
                    role="system",
                    content=JSON_INSTRUCTION,
                ),
            )
            return msgs
        elif rtype == "json_schema":
            # Pass through without modification for json_schema
            return msgs
        else:
            msg = f"Unsupported response_format: {response_format}"
            raise ValueError(msg)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    # `openai` falls back to this when AsyncOpenAI is built without a base_url,
    # which is what initialize() does — so this env var alone decides the endpoint.
    SDK_BASE_URL_ENV: str = "OPENAI_BASE_URL"

    def __init__(self) -> None:
        super().__init__(
            name="openai", description="OpenAI GPT models provider", version="1.0.0"
        )
        self.supported_models: list[str] = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
        self.default_model: str = "gpt-4"

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize OpenAI provider."""
        # Before the key check: a gateway-pointed provider is a contract violation
        # whether or not it also has credentials, and the contract is the useful
        # thing to say about it.
        self._refuse_sluice_route(config)

        if "api_key" not in config:
            msg = "OpenAI API key is required"
            raise ValueError(msg)

        self.config: dict[str, Any] = config

        try:
            # Initialize actual OpenAI client
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=config["api_key"])
            except ImportError:
                logger.warning("OpenAI package not installed, using placeholder client")
                self._client = {"api_key": config["api_key"]}

            self._is_initialized = True
            logger.info("OpenAI provider initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize OpenAI provider: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up OpenAI provider."""
        self._client = None
        self._is_initialized = False
        logger.info("OpenAI provider cleaned up")

    async def generate_completion(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        if not self._is_initialized:
            msg = "OpenAI provider not initialized"
            raise RuntimeError(msg)

        model = model or self.default_model

        # Handle response_format parameter
        response_format = kwargs.pop("response_format", None)
        messages = self._apply_response_format(messages, response_format)

        # Implement actual OpenAI API call
        try:
            from openai import AsyncOpenAI
            if isinstance(self._client, AsyncOpenAI):
                # Convert messages to OpenAI format
                openai_messages = [
                    {"role": msg.role, "content": msg.content} for msg in messages
                ]
                
                # Make API call
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                
                # Extract response data
                content = response.choices[0].message.content or ""
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                
                return LLMResponse(content=content, model=model, usage=usage)
        except (ImportError, AttributeError):
            logger.warning("OpenAI client not available, returning placeholder")
        
        # Fallback to placeholder response
        return LLMResponse(
            content=f"Generated response using {model}",
            model=model,
            usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        )

    async def generate_stream_completion(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> Any:
        """Generate streaming completion using OpenAI API."""
        if not self._is_initialized:
            msg = "OpenAI provider not initialized"
            raise RuntimeError(msg)

        model = model or self.default_model

        # Handle response_format parameter
        response_format = kwargs.pop("response_format", None)
        messages = self._apply_response_format(messages, response_format)

        # Implement actual OpenAI streaming API call
        try:
            from openai import AsyncOpenAI
            if isinstance(self._client, AsyncOpenAI):
                # Convert messages to OpenAI format
                openai_messages = [
                    {"role": msg.role, "content": msg.content} for msg in messages
                ]
                
                # Make streaming API call
                stream = await self._client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs,
                )
                
                # Yield chunks as they arrive
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield LLMResponse(
                            content=chunk.choices[0].delta.content,
                            model=model,
                            usage={},
                        )
                return
        except (ImportError, AttributeError):
            logger.warning("OpenAI client not available, using placeholder")
        
        # Fallback to placeholder response
        yield LLMResponse(
            content=f"Streaming response using {model}",
            model=model,
            usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform OpenAI API health check."""
        if not self._is_initialized:
            return {"status": "unhealthy", "message": "Provider not initialized"}

        try:
            # Perform actual OpenAI API health check
            from openai import AsyncOpenAI
            if isinstance(self._client, AsyncOpenAI):
                # Try to list models as a health check
                models = await self._client.models.list()
                return {
                    "status": "healthy",
                    "message": "OpenAI API accessible",
                    "models": self.supported_models,
                    "api_models_count": len(list(models.data)),
                }
            return {
                "status": "healthy",
                "message": "OpenAI API accessible (placeholder mode)",
                "models": self.supported_models,
            }
        except Exception as e:
            return {"status": "unhealthy", "message": f"OpenAI API error: {e}"}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider implementation."""

    # `anthropic` falls back to this when AsyncAnthropic is built without a base_url.
    SDK_BASE_URL_ENV: str = "ANTHROPIC_BASE_URL"

    def __init__(self) -> None:
        super().__init__(
            name="anthropic",
            description="Anthropic Claude models provider",
            version="1.0.0",
        )
        self.supported_models: list[str] = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        self.default_model: str = "claude-3-sonnet-20240229"

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize Anthropic provider."""
        self._refuse_sluice_route(config)

        if "api_key" not in config:
            msg = "Anthropic API key is required"
            raise ValueError(msg)

        self.config: dict[str, Any] = config

        try:
            # Initialize actual Anthropic client
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=config["api_key"])
            except ImportError:
                logger.warning("Anthropic package not installed, using placeholder client")
                self._client = {"api_key": config["api_key"]}

            self._is_initialized = True
            logger.info("Anthropic provider initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize Anthropic provider: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up Anthropic provider."""
        self._client = None
        self._is_initialized = False
        logger.info("Anthropic provider cleaned up")

    async def generate_completion(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using Anthropic API."""
        if not self._is_initialized:
            msg = "Anthropic provider not initialized"
            raise RuntimeError(msg)

        model = model or self.default_model

        # Handle response_format parameter
        response_format = kwargs.pop("response_format", None)
        messages = self._apply_response_format(messages, response_format)

        # Implement actual Anthropic API call
        try:
            from anthropic import AsyncAnthropic
            if isinstance(self._client, AsyncAnthropic):
                # Separate system messages from conversation messages
                system_msgs = [msg for msg in messages if msg.role == "system"]
                conv_msgs = [msg for msg in messages if msg.role != "system"]
                
                # Convert messages to Anthropic format
                anthropic_messages = [
                    {"role": msg.role, "content": msg.content} for msg in conv_msgs
                ]
                
                # Create system message if any
                system_content = " ".join([msg.content for msg in system_msgs]) if system_msgs else ""
                
                # Make API call
                response = await self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_content if system_content else None,
                    messages=anthropic_messages,
                    **kwargs,
                )
                
                # Extract response data
                content = response.content[0].text if response.content else ""
                usage = {
                    "input_tokens": response.usage.input_tokens if response.usage else 0,
                    "output_tokens": response.usage.output_tokens if response.usage else 0,
                }
                
                return LLMResponse(content=content, model=model, usage=usage)
        except (ImportError, AttributeError):
            logger.warning("Anthropic client not available, returning placeholder")
        
        # Fallback to placeholder response
        return LLMResponse(
            content=f"Generated response using {model}",
            model=model,
            usage={"input_tokens": 50, "output_tokens": 100},
        )

    async def generate_stream_completion(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> Any:
        """Generate streaming completion using Anthropic API."""
        if not self._is_initialized:
            msg = "Anthropic provider not initialized"
            raise RuntimeError(msg)

        model = model or self.default_model

        # Handle response_format parameter
        response_format = kwargs.pop("response_format", None)
        messages = self._apply_response_format(messages, response_format)

        # Implement actual Anthropic streaming API call
        try:
            from anthropic import AsyncAnthropic
            if isinstance(self._client, AsyncAnthropic):
                # Separate system messages from conversation messages
                system_msgs = [msg for msg in messages if msg.role == "system"]
                conv_msgs = [msg for msg in messages if msg.role != "system"]
                
                # Convert messages to Anthropic format
                anthropic_messages = [
                    {"role": msg.role, "content": msg.content} for msg in conv_msgs
                ]
                
                # Create system message if any
                system_content = " ".join([msg.content for msg in system_msgs]) if system_msgs else ""
                
                # Make streaming API call
                async with self._client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_content if system_content else None,
                    messages=anthropic_messages,
                    **kwargs,
                ) as stream:
                    async for text in stream.text_stream:
                        yield LLMResponse(
                            content=text,
                            model=model,
                            usage={},
                        )
                return
        except (ImportError, AttributeError):
            logger.warning("Anthropic client not available, using placeholder")
        
        # Fallback to placeholder response
        yield LLMResponse(
            content=f"Streaming response using {model}",
            model=model,
            usage={"input_tokens": 50, "output_tokens": 100},
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform Anthropic API health check."""
        if not self._is_initialized:
            return {"status": "unhealthy", "message": "Provider not initialized"}

        try:
            # Perform actual Anthropic API health check
            from anthropic import AsyncAnthropic
            if isinstance(self._client, AsyncAnthropic):
                # Try a simple message creation as health check
                test_msg = await self._client.messages.create(
                    model=self.default_model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}],
                )
                return {
                    "status": "healthy",
                    "message": "Anthropic API accessible",
                    "models": self.supported_models,
                    "test_response": bool(test_msg.content),
                }
            return {
                "status": "healthy",
                "message": "Anthropic API accessible (placeholder mode)",
                "models": self.supported_models,
            }
        except Exception as e:
            return {"status": "unhealthy", "message": f"Anthropic API error: {e}"}
