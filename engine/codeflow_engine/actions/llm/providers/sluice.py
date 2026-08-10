"""
Sluice gateway provider implementation.

Sluice is the org's OpenAI-compatible AI gateway. Routing through it is what
makes CodeFlow's model spend attributable — direct-provider calls are billed to
shared accounts with no record of which service or action incurred them, so they
are invisible to org cost reporting.

Because the wire protocol is OpenAI-compatible, this provider is deliberately a
thin variant of :class:`OpenAIProvider`. The one substantive difference is the
``metadata`` block required by Sluice ADR 10 (Request Metadata Contract), raised
from SHOULD to MUST by ADR 17.

Only the two required fields are sent. ``workflow`` and ``stage`` are optional
under ADR 10 and are omitted here on purpose: both are Prometheus labels with a
≤100-distinct budget, and the only values available at this layer would be read
free-form off the caller's request dict — the same unbounded-cardinality path
that ``agent`` is guarded against below, with no closed set to check them
against. An optional label nothing populates is noise in a rollup anyway.
"""

import os
from typing import Any

from codeflow_engine.actions.llm.base import BaseLLMProvider
from codeflow_engine.actions.llm.types import LLMResponse
from codeflow_engine.core.llm.sluice import (
    SLUICE_APP,
    SluiceAgent,
    build_request_metadata,
    coerce_agent,
)


#: Fallback for ``metadata.agent`` when a request does not name one. A generic
#: value is still far better than omitting the field: untagged requests roll up
#: at the gateway under ``(none)`` and cannot be attributed back here at all.
#:
#: A member of the closed set rather than a bare string — the fallback ends up in
#: the same Prometheus label as every explicit value, so it has to be as bounded
#: as they are.
DEFAULT_AGENT: SluiceAgent = SluiceAgent.LLM_ACTION


class SluiceProvider(BaseLLMProvider):
    """Routes completions through the Sluice gateway with cost attribution."""

    # This provider does send the ADR 17 block (see `complete` below), so it is
    # exempt from the base class's refuse-untagged-gateway-route guard.
    SUPPORTS_SLUICE_REQUEST_METADATA = True

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        # Deliberately NOT configurable. `app` identifies the calling
        # application to the gateway; letting config override it means a
        # misconfiguration silently misattributes this service's spend to
        # another, which is worse than not attributing it at all — wrong data
        # looks authoritative in a way missing data does not.
        self.app = SLUICE_APP
        # Checked against the closed set here, so a bad `agent` in config fails
        # at construction — while it is still traceable to the config that set
        # it — rather than becoming a brand-new time series on first request.
        configured_agent = config.get("agent")
        self.default_agent: SluiceAgent = (
            coerce_agent(configured_agent) if configured_agent else DEFAULT_AGENT
        )
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

            # ADR 17 metadata travels via the OpenAI SDK's extra_body escape
            # hatch — the SDK has no first-class parameter for it, and the
            # gateway reads it from the request body.
            #
            # The per-request override runs through the same closed-set check as
            # the constructor. One provider instance is shared by several calling
            # features, so the override is useful — but `agent` is a Prometheus
            # label with a ≤200-distinct budget, and ADR 10's *Forbidden* list
            # names this case directly: "Free-form user input in any required
            # field. app/agent are caller identity, not request payload."
            # Kebab-casing an unknown value only makes it *look* conformant; the
            # closed set is what keeps it bounded.
            override = request.get("agent")
            agent = coerce_agent(override) if override else self.default_agent
            # Built by the core helper so both Sluice providers construct the
            # block through one code path — two spellings of `app` would split
            # this repo's spend across two series.
            metadata = build_request_metadata(agent)

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
