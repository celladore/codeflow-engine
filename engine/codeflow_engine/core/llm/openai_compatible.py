"""OpenAI-Compatible Provider Template."""

import logging
from typing import Any

from codeflow_engine.core.llm.base import BaseLLMProvider
from codeflow_engine.core.llm.response import LLMResponse, ResponseExtractor
from codeflow_engine.core.llm.sluice import (
    SluiceAgent,
    SluiceMetadataError,
    coerce_agent,
    is_sluice_base_url,
    sluice_extra_body,
)

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    DEFAULT_MODEL: str = "gpt-4"
    LIBRARY_NAME: str = "openai"
    CLIENT_CLASS_PATH: str = "openai.OpenAI"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        # Set when this provider routes through the Sluice gateway. Requests then
        # carry the ADR 17 `metadata.app` / `metadata.agent` block. Left unset for
        # direct-to-vendor routes, where a stray `metadata` field is at best ignored
        # and at worst rejected (OpenAI only accepts it on stored completions).
        raw_agent = config.get("sluice_agent")
        self.sluice_agent: SluiceAgent | None = (
            coerce_agent(raw_agent) if raw_agent else None
        )
        self.client: Any = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.available = True
        except ImportError:
            logger.debug(f"{self.LIBRARY_NAME} package not installed")
            self.available = False

    def _get_default_model(self) -> str:
        return self.default_model or self.DEFAULT_MODEL

    def _prepare_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, str]]:
        return ResponseExtractor.filter_messages(messages)

    def _points_at_sluice(self) -> bool:
        """Whether this provider's base URL is the configured Sluice gateway.

        Used only to catch a Sluice route that forgot to declare `sluice_agent`.
        Tagging itself keys off the explicit config, not off URL sniffing.
        """
        return is_sluice_base_url(self.base_url)

    def _resolve_sluice_agent(self, override: Any = None) -> SluiceAgent | None:
        """Pick the agent for this call, and refuse to send Sluice an untagged one.

        A per-request override exists because one provider instance can be shared by
        several calling features; the closed-set check still runs on it, so the
        override cannot widen the label space.
        """
        agent = coerce_agent(override) if override else self.sluice_agent
        if agent is None and self._points_at_sluice():
            # Failing here is the whole point. The gateway would accept this request
            # today and quietly increment untagged_requests_total{codeflow-engine},
            # which restarts ADR 17's zero-for-a-week window for every other caller
            # — and once enforcement is on, the same request is an HTTP 400.
            raise SluiceMetadataError(
                "Refusing to send an untagged request to the Sluice gateway: this "
                "provider has base_url pointing at Sluice but no `sluice_agent` set. "
                "Sluice ADR 17 requires metadata.app and metadata.agent on every "
                "first-party request."
            )
        return agent

    def _make_api_call(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int | None,
        **kwargs: Any,
    ) -> Any:
        call_params: dict[str, Any] = {
            "model": str(model),
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens
        for key in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
            if key in kwargs and kwargs[key] is not None:
                call_params[key] = kwargs[key]
        agent = self._resolve_sluice_agent(kwargs.get("sluice_agent"))
        if agent is not None:
            # The openai SDK has no first-class body-level `metadata` for this
            # contract, so it goes through extra_body, which merges into the JSON.
            call_params["extra_body"] = sluice_extra_body(agent)
        return self.client.chat.completions.create(**call_params)

    def _extract_response(self, response: Any, model: str) -> LLMResponse:
        content, finish_reason, usage = ResponseExtractor.extract_openai_response(
            response
        )
        return LLMResponse(
            content=str(content),
            model=str(getattr(response, "model", model)),
            finish_reason=str(finish_reason),
            usage=usage,
        )

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        if not self.client:
            return LLMResponse.from_error(
                f"{self.name} client not initialized",
                self.get_model(request, self._get_default_model()),
            )
        try:
            messages = request.get("messages", [])
            model = self.get_model(request, self._get_default_model())
            temperature = request.get("temperature", 0.7)
            max_tokens = request.get("max_tokens")
            prepared_messages = self._prepare_messages(messages)
            if not prepared_messages:
                return LLMResponse.from_error("No valid messages provided", model)
            response = self._make_api_call(
                messages=prepared_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=request.get("top_p"),
                frequency_penalty=request.get("frequency_penalty"),
                presence_penalty=request.get("presence_penalty"),
                stop=request.get("stop"),
                sluice_agent=request.get("sluice_agent"),
            )
            return self._extract_response(response, model)
        except Exception as e:
            return self._create_error_response(e, request, self._get_default_model())
