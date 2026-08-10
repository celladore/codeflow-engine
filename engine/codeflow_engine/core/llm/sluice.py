"""Sluice gateway contract — request metadata required by Sluice ADR 17.

Sluice is phoenixvc's OpenAI-compatible LiteLLM gateway. Every first-party caller
must send ``metadata.app`` and ``metadata.agent`` in the request body so gateway
spend can be attributed back to the feature that drove it.

ADR 17 (`phoenixvc/sluice` docs/architecture/17-mandatory-request-metadata.md)
raised those two fields from SHOULD to MUST. The rollout is staged:

1. observe  — untagged requests succeed, gateway increments
   ``untagged_requests_total{key_alias="codeflow-engine"}``
2. verify   — that counter must not increase for a full week
3. enforce  — ``SLUICE_REQUIRE_REQUEST_METADATA=true``, untagged requests get HTTP 400

This module exists so codeflow-engine cannot land in state 1. The gateway
classifies our virtual key as a *service* (it carries no ``use:`` in the gateway's
``scripts/keys.yaml``), so we are in the enforced set, not exempt.

Two separate things both spell themselves "metadata": this module is about
*request*-level metadata sent per call. The ``metadata:`` block on a virtual key is
static provisioning data and does not satisfy this contract — one key serves many
agents, so key-level tags cannot answer "which agent drove this spend".
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final
from urllib.parse import urlsplit

# The `app` value is fixed for this repo and matches the Sluice virtual key alias.
# It is not configurable: a deployment that could rename itself would fragment its
# own attribution, which is the problem the contract exists to prevent.
SLUICE_APP: Final[str] = "codeflow-engine"

# `app` and `agent` become Prometheus label values, so ADR 10 (unchanged by ADR 17)
# requires lowercase kebab-case: stable, one token per dimension, no version numbers.
KEBAB_CASE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SluiceAgent(str, Enum):
    """Closed set of `agent` values codeflow-engine may send.

    Closed on purpose. Each distinct value becomes a Prometheus time series, so
    these must never be derived from user input, file contents, model names, issue
    titles or anything else attacker- or data-controlled — that would let a single
    run invent unbounded label values and blow the gateway's cardinality budget.

    Granularity is *calling feature*, not sub-agent. The linting fixer dispatches to
    seven internal specialists (line-length, imports, exceptions, ...); they all
    report as `linting-fixer`, because the useful rollup question is "what did the
    linting fixer cost", not "what did its exception specialist cost". Splitting
    further is a deliberate decision to spend cardinality, not a default.
    """

    LINTING_FIXER = "linting-fixer"
    QUALITY_ANALYZER = "quality-analyzer"
    CODE_QUALITY_AGENT = "code-quality-agent"
    PR_REVIEW_ANALYZER = "pr-review-analyzer"
    COMMENT_ANALYZER = "comment-analyzer"
    ISSUE_CREATOR = "issue-creator"

    # The config-driven `actions.llm` route, which serves the manager's default
    # `sluice` provider when no caller has named a feature. Deliberately coarse:
    # it answers "codeflow-engine's untyped LLM path" and nothing finer.
    #
    # It earns its slot because the alternative for that route is not a better
    # label — the manager's default_provider is `sluice`, so a route with no
    # sendable agent falls through to a direct vendor, which is untagged spend.
    # One coarse bucket beats that. Prefer a specific member; this is the floor,
    # not a default to reach for.
    LLM_ACTION = "llm-action"


# Fail at import rather than at request time if someone adds a non-conforming member.
# A malformed-but-present value is accepted by the gateway (it increments
# `malformed_metadata_total` instead of rejecting), so nothing downstream would
# surface the mistake — attribution would just quietly split across near-duplicates.
for _agent in SluiceAgent:
    if not KEBAB_CASE.match(_agent.value):
        raise ValueError(
            f"SluiceAgent.{_agent.name} = {_agent.value!r} is not lowercase kebab-case; "
            "see Sluice ADR 10 naming rules"
        )
del _agent


class SluiceNotConfiguredError(RuntimeError):
    """Raised when a Sluice route is used without base URL and API key."""


class SluiceMetadataError(ValueError):
    """Raised when request metadata would violate the ADR 17 contract.

    Raised locally, before the request leaves the process. During the observe and
    verify stages the gateway would *accept* an untagged request and silently
    increment `untagged_requests_total`, so local failure is the only thing that
    surfaces the bug while it is still cheap to fix.
    """


@dataclass(frozen=True)
class SluiceConfig:
    """Connection settings for the gateway, read from the environment.

    Deliberately not hardcoded — the gateway URL is deployment configuration, and
    the API key is a secret that must never reach the repo.
    """

    base_url: str
    api_key: str
    model: str = "auto"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "SluiceConfig | None":
        """Build config from ``SLUICE_BASE_URL`` / ``SLUICE_API_KEY``.

        Returns ``None`` when either is unset, so callers can treat Sluice as an
        optional route rather than crashing a process that never intended to use it.
        Use :meth:`require_from_env` where the route is mandatory.
        """
        source = os.environ if env is None else env
        base_url = (source.get("SLUICE_BASE_URL") or "").strip()
        api_key = (source.get("SLUICE_API_KEY") or "").strip()
        if not base_url or not api_key:
            return None
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            # `auto` is a Sluice-side alias that lets the gateway pick a model; the
            # key is provisioned for it. Override per deployment, not per request.
            model=(source.get("SLUICE_MODEL") or "auto").strip() or "auto",
        )

    @classmethod
    def require_from_env(cls, env: dict[str, str] | None = None) -> "SluiceConfig":
        config = cls.from_env(env)
        if config is None:
            raise SluiceNotConfiguredError(
                "Sluice is not configured: set SLUICE_BASE_URL and SLUICE_API_KEY"
            )
        return config


def _origin(url: str | None) -> tuple[str, int | None] | None:
    """Normalise a URL to (hostname, effective port), or None if unusable.

    Compared on origin rather than raw ``netloc`` so that cosmetic differences —
    a trailing slash, a path, a case difference, or an explicit ``:443`` on an
    https URL — cannot disguise the same endpoint.
    """
    if not url or not str(url).strip():
        return None
    raw = str(url).strip()
    parts = urlsplit(raw if "//" in raw else f"//{raw}")
    hostname = (parts.hostname or "").lower()
    if not hostname:
        return None
    try:
        explicit_port = parts.port
    except ValueError:  # malformed port; treat as not-the-gateway rather than crash
        return None
    default_ports = {"http": 80, "https": 443}
    port = explicit_port or default_ports.get((parts.scheme or "https").lower())
    return hostname, port


def is_sluice_base_url(base_url: str | None) -> bool:
    """Whether ``base_url`` addresses the configured Sluice gateway.

    Sluice speaks the OpenAI-compatible API, so any provider that accepts a
    ``base_url`` can be pointed at it by configuration alone — which is the easy,
    plausible way to start sending untagged traffic without touching this module.

    Reads ``SLUICE_BASE_URL`` directly rather than going through
    :class:`SluiceConfig`, which requires the API key too. A provider pointed at
    the gateway with its *own* vendor key is exactly the case worth catching, and
    keying this on the key's presence would switch the guard off for it.
    """
    target = _origin(base_url)
    if target is None:
        return False
    gateway = _origin(os.environ.get("SLUICE_BASE_URL"))
    return gateway is not None and target == gateway


def coerce_agent(agent: SluiceAgent | str) -> SluiceAgent:
    """Resolve ``agent`` to a member of the closed set, or raise.

    Accepting the raw string is a convenience for call sites that read a literal
    from their own config; it is *not* an escape hatch. An unknown value raises
    rather than being passed through, which is what keeps the label set closed.
    """
    if isinstance(agent, SluiceAgent):
        return agent
    try:
        return SluiceAgent(agent)
    except ValueError:
        allowed = ", ".join(sorted(member.value for member in SluiceAgent))
        raise SluiceMetadataError(
            f"{agent!r} is not a known Sluice agent. Each value is a Prometheus time "
            f"series, so it must come from the closed set: {allowed}. Add a new member "
            "to SluiceAgent if this is a genuinely new calling feature."
        ) from None


def build_request_metadata(agent: SluiceAgent | str) -> dict[str, str]:
    """Build the ADR 17 request metadata block.

    ``app`` and ``agent`` are the required fields. ``workflow``, ``stage``,
    ``request_id`` and ``session_id`` remain optional under ADR 17 and are not sent
    here — an optional field with nothing meaningful to say is noise in a rollup.
    """
    return {"app": SLUICE_APP, "agent": coerce_agent(agent).value}


def sluice_extra_body(agent: SluiceAgent | str) -> dict[str, Any]:
    """Metadata wrapped for the ``openai`` Python SDK.

    The SDK models `metadata` on chat completions as the OpenAI stored-completions
    field, so it is not reliably settable as a normal keyword argument. ``extra_body``
    merges verbatim into the JSON request body, which is where Sluice reads it from.
    This is the Python analogue of mystira-workspace's ``SluiceGatewayHandler``,
    which injects the same tags in a ``DelegatingHandler`` beneath the .NET SDK.
    """
    return {"metadata": build_request_metadata(agent)}
