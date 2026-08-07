"""
Sluice gateway provider implementation.

Sluice is the org's OpenAI-compatible AI gateway. Routing through it is what
makes CodeFlow's model spend attributable — direct-provider calls are billed to
shared accounts with no record of which service or action incurred them, so they
are invisible to org cost reporting.

Because the wire protocol is OpenAI-compatible, this provider is deliberately a
thin variant of :class:`OpenAIProvider`. The one substantive difference is the
``metadata`` block required by Sluice ADR 10 (Request Metadata Contract).
"""

import os
from typing import Any

from codeflow_engine.actions.llm.base import BaseLLMProvider
from codeflow_engine.actions.llm.types import LLMResponse


#: Emitted as ``metadata.app``. Identifies the calling application to the
#: gateway. Lowercase kebab-case and stable across deploys — each distinct label
#: value becomes its own Prometheus time series, so it must never carry a
#: version or free-form input.
SLUICE_APP = "codeflow-engine"

#: Fallback for ``metadata.agent`` when a request does not name one. A generic
#: value is still far better than omitting the field: untagged requests roll up
#: at the gateway under ``(none)`` and cannot be attributed back here at all.
DEFAULT_AGENT = "llm-action"


class SluiceProvider(BaseLLMProvider):
    """Routes completions through the Sluice gateway with cost attribution."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        # Deliberately NOT configurable. `app` identifies the calling
        # application to the gateway; letting config override it means a
        # misconfiguration silently misattributes this service's spend to
        # another, which is worse than not attributing it at all — wrong data
        # looks authoritative in a way missing data does not.
        self.app = SLUICE_APP
        self.default_agent = _normalize_tag(config.get("agent")) or DEFAULT_AGENT
        try:
            import openai

            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url or os.getenv("SLUICE_BASE_URL"),
            )
            self.available = True
        except ImportError:
            self.available = False

    def complete(self, request: dict[str, Any]) -> LLMResponse:
        model = request.get("model") or self.default_model or "default"
        try:
            filtered_messages = [
                msg for msg in request["messages"] if msg["content"].strip()
            ]

            # ADR 10 metadata travels via the OpenAI SDK's extra_body escape
            # hatch — the SDK has no first-class parameter for it, and the
            # gateway reads it from the request body.
            agent = _normalize_tag(request.get("agent")) or self.default_agent
            metadata: dict[str, str] = {"app": self.app, "agent": agent}
            for optional in ("workflow", "stage"):
                value = _normalize_tag(request.get(optional))
                if value:
                    metadata[optional] = value

            response = self.client.chat.completions.create(
                model=str(model),
                messages=filtered_messages,
                temperature=request.get("temperature", 0.7),
                max_tokens=request.get("max_tokens"),
                top_p=request.get("top_p", 1.0),
                frequency_penalty=request.get("frequency_penalty", 0.0),
                presence_penalty=request.get("presence_penalty", 0.0),
                stop=request.get("stop"),
                extra_body={"metadata": metadata},
            )

            if hasattr(response, "choices") and hasattr(response.choices[0], "message"):
                content = response.choices[0].message.content or ""
                finish_reason = (
                    getattr(response.choices[0], "finish_reason", "stop") or "stop"
                )
            else:
                content = ""
                finish_reason = "stop"

            resolved_model = getattr(response, "model", model)
            usage = (
                response.usage.dict()
                if hasattr(response, "usage") and response.usage is not None
                else None
            )

            return LLMResponse(
                content=str(content),
                model=str(resolved_model),
                finish_reason=str(finish_reason),
                usage=usage,
            )
        except Exception as e:
            return LLMResponse.from_error(str(e), str(model))

    def is_available(self) -> bool:
        base_url = self.base_url or os.getenv("SLUICE_BASE_URL")
        return self.available and bool(self.api_key) and bool(base_url)


def _normalize_tag(value: Any) -> str | None:
    """Coerce a metadata value to the lowercase kebab-case ADR 10 requires.

    Returns ``None`` when nothing usable remains, so the caller can fall back
    rather than emit an empty label — an empty value is indistinguishable at the
    gateway from the untagged state this contract exists to eliminate.
    """
    if not isinstance(value, str) or not value.strip():
        return None

    out: list[str] = []
    for ch in value:
        if ch.isalnum():
            out.append(ch.lower())
        elif out and out[-1] != "-":
            out.append("-")

    normalized = "".join(out).strip("-")
    return normalized or None
