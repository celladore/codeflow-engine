"""Guards the Sluice request-metadata contract (ADR 10, raised to MUST by ADR 17).

These tests assert the *contract* — what the gateway requires — not what the code
currently happens to send. That distinction is the reason this file exists.

The same contract was silently violated for months in house-of-veritas: the call
sent `consumer`/`capability` instead of `app`/`agent`, and the repo's own test
asserted those wrong names, so it actively defended the bug. Nothing failed,
because there is no build error for sending the wrong key name and `(none)` in a
cost rollup only looks wrong to someone already suspicious.

So: every assertion below is written against
`phoenixvc/sluice` docs/architecture/17-mandatory-request-metadata.md. If an
assertion here ever disagrees with the implementation, the implementation is what
moves — unless the ADR itself changed, in which case update the citation too.

codeflow-engine's virtual key carries no `use:` in the gateway's keys.yaml, which
classifies it as a *service*: enforced, not exempt.
"""

from __future__ import annotations

import re
import sys
import types
from typing import Any

import pytest

from codeflow_engine.actions.llm.manager import ActionLLMProviderManager
from codeflow_engine.core.llm.openai_compatible import OpenAICompatibleProvider
from codeflow_engine.core.llm.sluice import (
    SLUICE_APP,
    SluiceAgent,
    SluiceConfig,
    SluiceMetadataError,
    SluiceNotConfiguredError,
    build_request_metadata,
)
from codeflow_engine.core.llm.sluice_provider import SluiceProvider

# ADR 10 naming rule, unchanged by ADR 17: `app` and `agent` become Prometheus label
# values, so they must be lowercase kebab-case — stable, one token per dimension.
KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SLUICE_BASE_URL = "https://litellm.sluice.example"

# Field names an earlier generation of this contract used. The gateway reads these
# as absent, so a caller sending them is untagged while looking tagged.
SUPERSEDED_FIELD_NAMES = ("consumer", "capability")


class _CompletionsRecorder:
    """Stands in for `client.chat.completions`, capturing outgoing call kwargs."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        message = types.SimpleNamespace(content="ok")
        choice = types.SimpleNamespace(message=message, finish_reason="stop")
        return types.SimpleNamespace(choices=[choice], usage=None, model="test-model")


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _CompletionsRecorder:
    """Install a fake `openai` module so tests assert on the request, not the network.

    Stubbing at the module boundary rather than patching the provider's `client`
    attribute keeps `_initialize_client` in the code path — that is where the
    base_url and api_key actually get bound.
    """
    completions = _CompletionsRecorder()

    class _FakeClient:
        def __init__(self, api_key: str | None = None, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url
            self.chat = types.SimpleNamespace(completions=completions)

    monkeypatch.setitem(
        sys.modules, "openai", types.SimpleNamespace(OpenAI=_FakeClient)
    )
    return completions


@pytest.fixture
def sluice_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLUICE_BASE_URL", SLUICE_BASE_URL)
    monkeypatch.setenv("SLUICE_API_KEY", "sk-test")
    monkeypatch.delenv("SLUICE_MODEL", raising=False)


def sent_metadata(recorder: _CompletionsRecorder) -> dict[str, Any]:
    """Pull the metadata block out of the body the SDK was handed."""
    assert len(recorder.calls) == 1, f"expected 1 call, got {len(recorder.calls)}"
    extra_body = recorder.calls[0].get("extra_body")
    assert extra_body is not None, "request carried no extra_body, so no metadata"
    return extra_body["metadata"]


def complete_once(provider: OpenAICompatibleProvider) -> Any:
    return provider.complete({"messages": [{"role": "user", "content": "hello"}]})


class TestRequiredFields:
    """ADR 17: `metadata.app` and `metadata.agent` are MUST."""

    def test_sends_both_required_fields(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        complete_once(SluiceProvider(SluiceAgent.LINTING_FIXER))

        metadata = sent_metadata(recorder)
        assert metadata["app"] == "codeflow-engine"
        assert metadata["agent"] == "linting-fixer"

    def test_app_matches_the_provisioned_key_alias(self) -> None:
        # The `app` value and the Sluice virtual key alias are the same string by
        # design; ADR 17's enforced-set table keys off `codeflow-engine`.
        assert SLUICE_APP == "codeflow-engine"

    def test_every_agent_sends_a_complete_metadata_block(self) -> None:
        # Guards the whole closed set, not just the one the happy path exercises.
        for agent in SluiceAgent:
            metadata = build_request_metadata(agent)
            assert set(metadata) == {"app", "agent"}
            for field, value in metadata.items():
                assert isinstance(value, str) and value.strip(), (
                    f"{agent.value}: {field} must be a non-empty string; ADR 17 treats "
                    "null, empty and whitespace-only as absent"
                )

    def test_does_not_send_superseded_field_names(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # The house-of-veritas bug: right shape, wrong keys, read as untagged.
        complete_once(SluiceProvider(SluiceAgent.QUALITY_ANALYZER))

        metadata = sent_metadata(recorder)
        for name in SUPERSEDED_FIELD_NAMES:
            assert name not in metadata


class TestNamingRules:
    """ADR 10 naming rules — violations are counted, not rejected, so nothing else catches them."""

    def test_prometheus_labelled_fields_are_kebab_case(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        complete_once(SluiceProvider(SluiceAgent.CODE_QUALITY_AGENT))

        metadata = sent_metadata(recorder)
        for field in ("app", "agent"):
            value = metadata.get(field)
            # Type before shape: str(None) is "none", which passes a regex-only
            # check, so a missing field would sail through the pattern assertion.
            assert isinstance(value, str), f"{field} must be present and a string"
            assert KEBAB_CASE.match(value), f"{field}={value!r} is not kebab-case"

    def test_closed_set_members_are_kebab_case(self) -> None:
        for agent in SluiceAgent:
            assert KEBAB_CASE.match(agent.value), f"{agent.name} is not kebab-case"

    def test_agent_values_are_unique(self) -> None:
        # Two members sharing a value would silently merge two features into one
        # time series, which reads as one feature costing twice as much.
        values = [agent.value for agent in SluiceAgent]
        assert len(values) == len(set(values))


class TestClosedLabelSet:
    """Each distinct `agent` is a Prometheus time series, so the set must stay closed."""

    @pytest.mark.parametrize(
        "value",
        [
            "user-supplied-agent",
            "LintingFixer",  # would be accepted by the gateway, splitting attribution
            "linting_fixer",
            "",
            "   ",
        ],
    )
    def test_rejects_agents_outside_the_closed_set(self, value: str) -> None:
        with pytest.raises(SluiceMetadataError):
            build_request_metadata(value)

    def test_rejects_non_string_agents(self) -> None:
        for value in (1, 3.5, ["linting-fixer"], {"agent": "linting-fixer"}):
            with pytest.raises((SluiceMetadataError, TypeError)):
                build_request_metadata(value)  # type: ignore[arg-type]

    def test_known_literal_strings_still_resolve(self) -> None:
        # Call sites reading a literal from their own config keep working; the
        # closed-set check is what makes that safe.
        assert build_request_metadata("linting-fixer")["agent"] == "linting-fixer"


class TestUntaggedTrafficIsRefused:
    """An untagged request is accepted by the gateway today — local failure is the only signal."""

    def test_sluice_route_without_an_agent_refuses_to_send(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # Bypasses SluiceProvider to model the realistic mistake: a plain
        # OpenAI-compatible provider pointed at the gateway by configuration.
        provider = OpenAICompatibleProvider(
            {"api_key": "sk-test", "base_url": SLUICE_BASE_URL}
        )
        response = complete_once(provider)

        assert response.error is not None
        assert recorder.calls == [], "an untagged request reached the gateway"

    def test_sluice_provider_cannot_be_built_without_an_agent(self) -> None:
        with pytest.raises(TypeError):
            SluiceProvider()  # type: ignore[call-arg]

    def test_caller_config_cannot_strip_the_tag(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        provider = SluiceProvider(
            SluiceAgent.ISSUE_CREATOR, config={"sluice_agent": None}
        )
        complete_once(provider)

        assert sent_metadata(recorder)["agent"] == "issue-creator"

    def test_caller_config_cannot_redirect_the_gateway_credential(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # Overriding base_url while this class supplies api_key would send the
        # Sluice credential to an arbitrary OpenAI-compatible endpoint.
        provider = SluiceProvider(
            SluiceAgent.ISSUE_CREATOR,
            config={"base_url": "https://attacker.example", "api_key": "sk-other"},
        )

        assert provider.base_url == SLUICE_BASE_URL
        assert provider.api_key == "sk-test"

    def test_guard_holds_when_only_the_gateway_url_is_configured(
        self, recorder: _CompletionsRecorder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A provider pointed at the gateway with its *own* vendor key is exactly
        # the case worth catching, so the guard must not key off SLUICE_API_KEY.
        monkeypatch.setenv("SLUICE_BASE_URL", SLUICE_BASE_URL)
        monkeypatch.delenv("SLUICE_API_KEY", raising=False)

        provider = OpenAICompatibleProvider(
            {"api_key": "sk-vendor", "base_url": SLUICE_BASE_URL}
        )
        response = complete_once(provider)

        assert response.error is not None
        assert recorder.calls == []

    @pytest.mark.parametrize(
        "equivalent",
        [
            f"{SLUICE_BASE_URL}:443",  # explicit default port
            f"{SLUICE_BASE_URL}/v1",  # path suffix
            f"{SLUICE_BASE_URL}/",  # trailing slash
            "https://LITELLM.SLUICE.EXAMPLE",  # host case
        ],
    )
    def test_cosmetic_url_differences_do_not_evade_the_guard(
        self, recorder: _CompletionsRecorder, sluice_env: None, equivalent: str
    ) -> None:
        provider = OpenAICompatibleProvider(
            {"api_key": "sk-test", "base_url": equivalent}
        )
        response = complete_once(provider)

        assert response.error is not None, f"{equivalent} slipped past the guard"
        assert recorder.calls == []


class TestUntaggedProviderStacksCannotReachSluice:
    """The `actions.llm` stack sends no metadata, so it must not be pointable at Sluice."""

    def test_action_provider_refuses_a_sluice_base_url(self, sluice_env: None) -> None:
        from codeflow_engine.actions.llm.providers import OpenAIProvider

        with pytest.raises(SluiceMetadataError):
            OpenAIProvider({"api_key": "sk-test", "base_url": SLUICE_BASE_URL})

    def test_action_provider_still_accepts_vendor_urls(self, sluice_env: None) -> None:
        from codeflow_engine.actions.llm.providers import OpenAIProvider

        provider = OpenAIProvider(
            {"api_key": "sk-test", "base_url": "https://api.openai.com/v1"}
        )
        assert provider.base_url == "https://api.openai.com/v1"

    def test_guard_ignores_path_and_trailing_slash_differences(
        self, sluice_env: None
    ) -> None:
        from codeflow_engine.actions.llm.providers import OpenAIProvider

        # Same host, cosmetically different URL — must not slip past the guard.
        with pytest.raises(SluiceMetadataError):
            OpenAIProvider(
                {"api_key": "sk-test", "base_url": f"{SLUICE_BASE_URL}/v1/"}
            )


class TestNonSluiceRoutesAreUnaffected:
    """The contract binds Sluice traffic; direct-to-vendor routes must not change."""

    def test_direct_provider_sends_no_metadata(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        provider = OpenAICompatibleProvider(
            {"api_key": "sk-test", "base_url": "https://api.openai.com/v1"}
        )
        complete_once(provider)

        assert len(recorder.calls) == 1
        assert "extra_body" not in recorder.calls[0]

    def test_provider_with_no_base_url_sends_no_metadata(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        provider = OpenAICompatibleProvider({"api_key": "sk-test"})
        complete_once(provider)

        assert "extra_body" not in recorder.calls[0]


class TestLintingFixerRoutesThroughSluice:
    """The first real caller. Without one, the alias emits no traffic to verify."""

    def test_manager_exposes_sluice_when_an_agent_is_named(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        manager = ActionLLMProviderManager(
            {"providers": {"sluice": {"agent": SluiceAgent.LINTING_FIXER}}}
        )
        assert "sluice" in manager.providers

    def test_manager_omits_sluice_without_an_agent(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # Opt-in per caller: a shared default would misattribute one feature's
        # spend to whichever agent happened to be configured.
        manager = ActionLLMProviderManager({"providers": {}})
        assert "sluice" not in manager.providers

    def test_malformed_sluice_config_leaves_vendor_fallbacks_intact(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # A sluice block with no `agent` must degrade to "no sluice provider",
        # not abort construction and take the vendor providers down with it.
        manager = ActionLLMProviderManager(
            {"providers": {"sluice": {"model": "cheap-fast"}}}
        )

        assert "sluice" not in manager.providers
        assert manager.providers, "vendor providers were lost"

    def test_completion_through_the_manager_is_tagged(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        manager = ActionLLMProviderManager(
            {
                "providers": {"sluice": {"agent": SluiceAgent.LINTING_FIXER}},
                "default_provider": "sluice",
            }
        )
        manager.complete({"messages": [{"role": "user", "content": "fix this"}]})

        metadata = sent_metadata(recorder)
        assert metadata == {"app": "codeflow-engine", "agent": "linting-fixer"}

    def test_linting_fixer_prefers_sluice_when_configured(
        self, monkeypatch: pytest.MonkeyPatch, sluice_env: None
    ) -> None:
        from codeflow_engine.actions.ai_linting_fixer.display import DisplayConfig
        from codeflow_engine.actions.ai_linting_fixer.workflow_orchestrator import (
            WorkflowOrchestrator,
        )

        # A vendor key is present too, so this asserts precedence rather than
        # merely that sluice is the only option available.
        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        captured: dict[str, Any] = {}

        def capture(config: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
            captured.update(config)
            return None

        monkeypatch.setattr(
            "codeflow_engine.actions.ai_linting_fixer.workflow_orchestrator"
            ".LLMProviderManager",
            capture,
        )
        WorkflowOrchestrator(DisplayConfig()).create_llm_manager(
            types.SimpleNamespace(provider=None)
        )

        assert captured["default_provider"] == "sluice"
        assert captured["providers"]["sluice"]["agent"] == SluiceAgent.LINTING_FIXER


class TestConfiguration:
    """Connection settings come from the environment, never from the repo."""

    def test_requires_both_base_url_and_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for present, missing in (
            ("SLUICE_BASE_URL", "SLUICE_API_KEY"),
            ("SLUICE_API_KEY", "SLUICE_BASE_URL"),
        ):
            monkeypatch.setenv(present, "value")
            monkeypatch.delenv(missing, raising=False)
            assert SluiceConfig.from_env() is None
            with pytest.raises(SluiceNotConfiguredError):
                SluiceConfig.require_from_env()

    def test_blank_values_do_not_count_as_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SLUICE_BASE_URL", "   ")
        monkeypatch.setenv("SLUICE_API_KEY", "sk-test")
        assert SluiceConfig.from_env() is None

    def test_no_gateway_url_is_hardcoded(self, sluice_env: None) -> None:
        config = SluiceConfig.require_from_env()
        assert config.base_url == SLUICE_BASE_URL

    def test_trailing_slash_is_normalised(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Otherwise the base_url comparison that catches untagged routes misses.
        monkeypatch.setenv("SLUICE_BASE_URL", f"{SLUICE_BASE_URL}/")
        monkeypatch.setenv("SLUICE_API_KEY", "sk-test")
        assert SluiceConfig.require_from_env().base_url == SLUICE_BASE_URL
