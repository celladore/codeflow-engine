"""LLM provider that routes through the Sluice gateway.

Sluice speaks the OpenAI-compatible API, so this is `OpenAICompatibleProvider`
pointed at the gateway with connection settings from the environment and an ADR 17
`agent` tag that is required rather than optional.

The tag is a constructor argument with no default on purpose: an untagged Sluice
call is not a degraded call, it is a contract violation that the gateway currently
*accepts* while incrementing `untagged_requests_total`. Making the agent
unforgettable at construction is cheaper than noticing later on a dashboard.
"""

from __future__ import annotations

import logging
from typing import Any

from codeflow_engine.core.llm.openai_compatible import OpenAICompatibleProvider
from codeflow_engine.core.llm.sluice import SluiceAgent, SluiceConfig, coerce_agent

logger = logging.getLogger(__name__)


class SluiceProvider(OpenAICompatibleProvider):
    """OpenAI-compatible provider bound to the Sluice gateway.

    Example::

        provider = SluiceProvider(SluiceAgent.LINTING_FIXER)
        response = provider.complete({"messages": [...]})
    """

    # `auto` lets the gateway route; the virtual key is provisioned for it alongside
    # the cheap-* / premium aliases. Overridable per deployment via SLUICE_MODEL.
    DEFAULT_MODEL: str = "auto"

    def __init__(
        self,
        agent: SluiceAgent | str,
        config: dict[str, Any] | None = None,
    ) -> None:
        # Validate the agent before touching the network config so a bad literal
        # fails with the closed-set message rather than a missing-credentials one.
        resolved_agent = coerce_agent(agent)
        sluice = SluiceConfig.require_from_env()
        merged: dict[str, Any] = {
            "name": "sluice",
            "default_model": sluice.model,
            # Caller config first, so it can set model, timeouts and the like...
            **(config or {}),
            # ...but never the connection or the tag. Letting a caller override
            # `base_url` while this class supplies `api_key` would send the Sluice
            # credential to an arbitrary OpenAI-compatible endpoint, and overriding
            # `sluice_agent` would quietly drop the ADR 17 tag.
            "base_url": sluice.base_url,
            "api_key": sluice.api_key,
            "sluice_agent": resolved_agent,
        }
        super().__init__(merged)
