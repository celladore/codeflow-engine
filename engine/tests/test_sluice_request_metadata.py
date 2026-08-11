"""Guards the Sluice request-metadata contract (ADR 10, raised to MUST by ADR 17).

These tests assert the *contract* â€” what the gateway requires â€” not what the code
currently happens to send. That distinction is the reason this file exists.

The same contract was silently violated for months in house-of-veritas: the call
sent `consumer`/`capability` instead of `app`/`agent`, and the repo's own test
asserted those wrong names, so it actively defended the bug. Nothing failed,
because there is no build error for sending the wrong key name and `(none)` in a
cost rollup only looks wrong to someone already suspicious.

So: every assertion below is written against
`phoenixvc/sluice` docs/architecture/17-mandatory-request-metadata.md. If an
assertion here ever disagrees with the implementation, the implementation is what
moves â€” unless the ADR itself changed, in which case update the citation too.

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
# values, so they must be lowercase kebab-case â€” stable, one token per dimension.
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
    attribute keeps `_initialize_client` in the code path â€” that is where the
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
    """ADR 10 naming rules â€” violations are counted, not rejected, so nothing else catches them."""

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
    """An untagged request is accepted by the gateway today â€” local failure is the only signal."""

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

        # Same host, cosmetically different URL â€” must not slip past the guard.
        with pytest.raises(SluiceMetadataError):
            OpenAIProvider(
                {"api_key": "sk-test", "base_url": f"{SLUICE_BASE_URL}/v1/"}
            )


class TestBothSluiceProvidersCoexist:
    """Two Sluice providers exist after #44 and #45 landed; both must work.

    The merge of those two branches produced no textual conflict but a semantic
    one: `manager.py` imported both classes under the bare name `SluiceProvider`,
    and the base-class guard added by #45 refused to construct #44's provider at
    all. The default provider is `sluice`, so the visible effect was every request
    silently falling back to a direct vendor — untagged, unattributable spend,
    which is the exact outcome both branches existed to prevent.
    """

    def test_config_driven_provider_can_reach_the_gateway(
        self, sluice_env: None
    ) -> None:
        from codeflow_engine.actions.llm.providers.sluice import (
            SluiceProvider as ConfigSluiceProvider,
        )

        provider = ConfigSluiceProvider(
            {"api_key": "sk-test", "base_url": SLUICE_BASE_URL}
        )
        assert provider.SUPPORTS_SLUICE_REQUEST_METADATA is True

    def test_config_driven_provider_tags_its_requests(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        from codeflow_engine.actions.llm.providers.sluice import (
            SluiceProvider as ConfigSluiceProvider,
        )

        provider = ConfigSluiceProvider(
            {"api_key": "sk-test", "base_url": SLUICE_BASE_URL}
        )
        provider.complete({"messages": [{"role": "user", "content": "hi"}]})

        metadata = sent_metadata(recorder)
        assert metadata["app"] == "codeflow-engine"
        assert KEBAB_CASE.match(metadata["agent"])

    def test_both_providers_agree_on_app(self) -> None:
        # They previously defined SLUICE_APP independently, which is a drift risk:
        # two spellings of `app` would split this repo's spend across two series.
        from codeflow_engine.actions.llm.providers import sluice as config_provider

        assert config_provider.SLUICE_APP == SLUICE_APP

    def test_default_manager_registers_sluice(self, sluice_env: None) -> None:
        # The regression: default_provider is "sluice", so if it fails to register
        # the manager silently serves every request from a direct vendor.
        manager = ActionLLMProviderManager({})

        assert manager.default_provider == "sluice"
        assert "sluice" in manager.providers, (
            "default provider missing — traffic would fall back to an untagged vendor"
        )

    def test_typed_agent_takes_precedence_over_the_free_form_provider(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        manager = ActionLLMProviderManager(
            {"providers": {"sluice": {"agent": SluiceAgent.LINTING_FIXER}}}
        )
        manager.complete(
            {"provider": "sluice", "messages": [{"role": "user", "content": "x"}]}
        )

        assert sent_metadata(recorder)["agent"] == "linting-fixer"


class TestClosedLabelSetHoldsThroughBothProviders:
    """ADR 10 forbids free-form input in `agent` — on *both* Sluice routes.

    `agent` is a Prometheus label with a ≤200-distinct budget, and ADR 10's
    *Forbidden* list names this case outright: "Free-form user input in any
    required field. `app`/`agent` are caller identity, not request payload."

    The typed provider takes a `SluiceAgent`, so it could not violate this. The
    config-driven one took a free-form string off the caller's request dict,
    kebab-cased it and sent it — a normaliser standing where a closed-set check
    belongs. Normalising an unknown value makes it *look* conformant without
    making it bounded, and the gateway accepts whatever arrives (it counts
    malformed values rather than rejecting them), so nothing downstream would
    have surfaced it either.

    Asserted against both providers together because the failure this guards is
    divergence: one route enforcing the set and the other not is how the hole
    reopens.
    """

    #: Values that must never reach the gateway as a label. Includes the shapes a
    #: kebab-caser would happily "fix" into something plausible, and the ones that
    #: would be derived from request payload or a model name.
    OUT_OF_SET_AGENTS = [
        "user-supplied-agent",
        "LintingFixer",  # normalises to `lintingfixer`, which is not a member
        "linting_fixer",  # normalises *onto* a real member — silent misattribution
        "fix the file src/foo.py",  # request payload as a label
        "gpt-4",  # model name as a label
        "   ",  # ADR 17 treats whitespace-only as absent
    ]

    def config_provider(self, **overrides: Any) -> Any:
        from codeflow_engine.actions.llm.providers.sluice import (
            SluiceProvider as ConfigSluiceProvider,
        )

        return ConfigSluiceProvider(
            {"api_key": "sk-test", "base_url": SLUICE_BASE_URL, **overrides}
        )

    @pytest.mark.parametrize("value", OUT_OF_SET_AGENTS)
    def test_typed_provider_refuses_an_out_of_set_agent(self, value: str) -> None:
        with pytest.raises(SluiceMetadataError):
            SluiceProvider(value)

    @pytest.mark.parametrize("value", OUT_OF_SET_AGENTS)
    def test_config_driven_provider_refuses_an_out_of_set_request_agent(
        self, recorder: _CompletionsRecorder, sluice_env: None, value: str
    ) -> None:
        provider = self.config_provider()
        response = provider.complete(
            {"messages": [{"role": "user", "content": "hi"}], "agent": value}
        )

        assert response.error is not None
        assert recorder.calls == [], f"{value!r} reached the gateway as a label"

    @pytest.mark.parametrize("value", OUT_OF_SET_AGENTS)
    def test_config_driven_provider_refuses_an_out_of_set_config_agent(
        self, sluice_env: None, value: str
    ) -> None:
        # Config is the other way in. Failing at construction keeps the bad value
        # attached to the config that set it, instead of surfacing one request later.
        with pytest.raises(SluiceMetadataError):
            self.config_provider(agent=value)

    @pytest.mark.parametrize("value", OUT_OF_SET_AGENTS)
    def test_both_routes_share_one_closed_set_chokepoint(self, value: str) -> None:
        # Why the two tests above can stay in step: both routes now resolve the
        # agent through `coerce_agent`, so neither can drift more permissive than
        # the other. A second, parallel implementation is how the hole opened the
        # first time — the config-driven provider had its own normaliser.
        with pytest.raises(SluiceMetadataError):
            build_request_metadata(value)

    def test_known_agents_still_pass_through_the_config_driven_provider(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # Closing the set must not close the door: a per-request override naming a
        # real member is the mechanism that lets one shared instance serve several
        # calling features.
        provider = self.config_provider()
        provider.complete(
            {
                "messages": [{"role": "user", "content": "hi"}],
                "agent": SluiceAgent.ISSUE_CREATOR.value,
            }
        )

        assert sent_metadata(recorder)["agent"] == "issue-creator"

    @pytest.mark.parametrize(
        "request_extra",
        [
            pytest.param({}, id="key-omitted"),
            pytest.param({"agent": None}, id="null"),
            pytest.param({"agent": ""}, id="empty-string"),
        ],
    )
    def test_absent_request_agent_falls_back_to_a_closed_set_member(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        request_extra: dict[str, Any],
    ) -> None:
        # Absent is not the same as invalid. ADR 17 treats omitted/null/empty as
        # missing, and the treatment for missing is the default bucket — not an
        # empty label, and not a silent fall-through to an untagged vendor.
        self.config_provider().complete(
            {"messages": [{"role": "user", "content": "hi"}], **request_extra}
        )

        assert sent_metadata(recorder)["agent"] in {a.value for a in SluiceAgent}

    def test_the_default_agent_is_itself_a_closed_set_member(self) -> None:
        # The fallback lands in the same Prometheus label as every explicit value,
        # so a free string here would reopen the set from the other end.
        from codeflow_engine.actions.llm.providers.sluice import DEFAULT_AGENT

        assert isinstance(DEFAULT_AGENT, SluiceAgent)

    def test_manager_route_refuses_an_out_of_set_agent(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # End to end: the closed set has to survive the manager, which is the only
        # way most callers reach a provider at all.
        manager = ActionLLMProviderManager({})
        response = manager.complete(
            {
                "provider": "sluice",
                "messages": [{"role": "user", "content": "x"}],
                "agent": "arbitrary-caller-string",
            }
        )

        assert response.error is not None
        assert recorder.calls == []


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

    def test_untyped_sluice_route_still_tags(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # Without a typed agent the config-driven provider serves `sluice`. The
        # invariant that matters is not which class registers, but that whatever
        # does still sends the ADR 17 block — so no path reaches the gateway bare.
        manager = ActionLLMProviderManager({"providers": {}})
        assert "sluice" in manager.providers

        manager.complete(
            {"provider": "sluice", "messages": [{"role": "user", "content": "x"}]}
        )
        metadata = sent_metadata(recorder)
        assert metadata["app"] == "codeflow-engine"
        assert KEBAB_CASE.match(metadata["agent"])

    def test_malformed_typed_config_leaves_the_manager_usable(
        self, recorder: _CompletionsRecorder, sluice_env: None
    ) -> None:
        # A sluice block with no `agent` must not abort construction. It degrades
        # to the config-driven provider; the vendor fallbacks survive either way.
        manager = ActionLLMProviderManager(
            {"providers": {"sluice": {"model": "cheap-fast"}}}
        )

        assert manager.providers, "vendor providers were lost"
        assert not isinstance(manager.providers.get("sluice"), SluiceProvider), (
            "a typed provider registered despite an invalid agent"
        )

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


class TestAsyncProviderStackCannotReachSluice:
    """`ai.core` is a third provider stack, async, and sends no metadata at all.

    It is the easiest of the three to point at the gateway by accident, because it
    never passes `base_url` to the SDK: `AsyncOpenAI(api_key=...)` falls back to
    `OPENAI_BASE_URL`, and `AsyncAnthropic` to `ANTHROPIC_BASE_URL`. So one
    environment variable — no code change, no config, nothing in a diff to notice —
    reroutes every request in this stack to Sluice with no `metadata` block.

    A guard that only inspected config would pass most of these.
    """

    @pytest.mark.asyncio
    async def test_refuses_a_gateway_base_url_in_config(self, sluice_env: None) -> None:
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        with pytest.raises(SluiceMetadataError):
            await AsyncOpenAIProvider().initialize(
                {"api_key": "sk-vendor", "base_url": SLUICE_BASE_URL}
            )

    @pytest.mark.asyncio
    async def test_refuses_a_gateway_reached_only_through_the_sdk_env_var(
        self, sluice_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        # No base_url anywhere in config — the env var alone decides the endpoint.
        monkeypatch.setenv("OPENAI_BASE_URL", SLUICE_BASE_URL)

        with pytest.raises(SluiceMetadataError):
            await AsyncOpenAIProvider().initialize({"api_key": "sk-vendor"})

    @pytest.mark.asyncio
    async def test_refuses_an_anthropic_gateway_route(
        self, sluice_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from codeflow_engine.ai.core.base import (
            AnthropicProvider as AsyncAnthropicProvider,
        )

        monkeypatch.setenv("ANTHROPIC_BASE_URL", SLUICE_BASE_URL)

        with pytest.raises(SluiceMetadataError):
            await AsyncAnthropicProvider().initialize({"api_key": "sk-vendor"})

    @pytest.mark.asyncio
    async def test_refusal_precedes_the_credential_check(
        self, sluice_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A gateway-pointed provider violates the contract whether or not it also
        # has a key, and the contract is the useful thing to report about it.
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        monkeypatch.setenv("OPENAI_BASE_URL", SLUICE_BASE_URL)

        with pytest.raises(SluiceMetadataError):
            await AsyncOpenAIProvider().initialize({})

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "equivalent",
        [
            f"{SLUICE_BASE_URL}:443",
            f"{SLUICE_BASE_URL}/v1",
            f"{SLUICE_BASE_URL}/",
            "https://LITELLM.SLUICE.EXAMPLE",
        ],
    )
    async def test_cosmetic_url_differences_do_not_evade_the_guard(
        self, sluice_env: None, monkeypatch: pytest.MonkeyPatch, equivalent: str
    ) -> None:
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        monkeypatch.setenv("OPENAI_BASE_URL", equivalent)

        with pytest.raises(SluiceMetadataError):
            await AsyncOpenAIProvider().initialize({"api_key": "sk-vendor"})

    @pytest.mark.asyncio
    async def test_guard_holds_when_only_the_gateway_url_is_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A provider pointed at the gateway with its own vendor key is exactly the
        # case worth catching, so the guard must not key off SLUICE_API_KEY.
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        monkeypatch.setenv("SLUICE_BASE_URL", SLUICE_BASE_URL)
        monkeypatch.delenv("SLUICE_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_BASE_URL", SLUICE_BASE_URL)

        with pytest.raises(SluiceMetadataError):
            await AsyncOpenAIProvider().initialize({"api_key": "sk-vendor"})

    @pytest.mark.asyncio
    async def test_vendor_endpoints_are_unaffected(
        self, sluice_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The guard binds Sluice routes only; a normal vendor route must still work.
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        provider = AsyncOpenAIProvider()
        await provider.initialize({"api_key": "sk-vendor"})

        assert provider._is_initialized

    @pytest.mark.asyncio
    async def test_no_configured_gateway_means_no_refusal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The guard is gateway-relative, not a blanket ban on unusual base URLs:
        # with no SLUICE_BASE_URL there is no gateway to send untagged traffic to.
        from codeflow_engine.ai.core.base import OpenAIProvider as AsyncOpenAIProvider

        monkeypatch.delenv("SLUICE_BASE_URL", raising=False)
        monkeypatch.setenv("OPENAI_BASE_URL", SLUICE_BASE_URL)
        provider = AsyncOpenAIProvider()
        await provider.initialize({"api_key": "sk-vendor"})

        assert provider._is_initialized

    @pytest.mark.asyncio
    async def test_manager_surfaces_the_refusal_rather_than_dropping_the_provider(
        self, sluice_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Provider registration swallows exceptions and logs a warning, so a guard
        # firing there would silently remove the provider — the same invisible
        # failure the contract exists to prevent. It must fire on the path that
        # actually builds the client, where it propagates to the caller.
        from codeflow_engine.ai.core.providers.manager import LLMProviderManager
        from codeflow_engine.config import CodeFlowConfig

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_BASE_URL", SLUICE_BASE_URL)

        manager = LLMProviderManager(CodeFlowConfig())

        with pytest.raises(SluiceMetadataError):
            await manager.initialize()


class TestQualityEngineRoutesThroughSluice:
    """The quality engine's AI analysis, tagged `quality-analyzer`."""

    @pytest.mark.asyncio
    async def test_prefers_the_gateway_when_it_is_configured(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from codeflow_engine.actions.quality_engine.ai import initialize_llm_manager

        # A vendor key is present too, so this asserts precedence rather than
        # merely that sluice is the only option available.
        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        manager = await initialize_llm_manager()

        assert manager is not None
        assert manager.default_provider == "sluice"
        assert "openai" in manager.providers, "vendor fallbacks were lost"

    @pytest.mark.asyncio
    async def test_analysis_requests_are_tagged(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        from codeflow_engine.actions.quality_engine.ai import (
            initialize_llm_manager,
            run_ai_analysis,
        )

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        target = tmp_path / "sample.py"
        target.write_text("x = 1\n", encoding="utf-8")

        manager = await initialize_llm_manager()
        await run_ai_analysis([str(target)], manager)

        assert sent_metadata(recorder) == {
            "app": "codeflow-engine",
            "agent": "quality-analyzer",
        }

    @pytest.mark.asyncio
    async def test_does_not_ask_the_gateway_for_a_vendor_model(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        # The gateway key is provisioned for Sluice's own aliases, not vendor model
        # names, so the deployment-configured alias must win. A hardcoded `gpt-4`
        # would reach the gateway correctly tagged and still fail.
        from codeflow_engine.actions.quality_engine.ai import (
            initialize_llm_manager,
            run_ai_analysis,
        )

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        monkeypatch.setenv("SLUICE_MODEL", "cheap-fast")
        target = tmp_path / "sample.py"
        target.write_text("x = 1\n", encoding="utf-8")

        manager = await initialize_llm_manager()
        await run_ai_analysis([str(target)], manager)

        assert recorder.calls[0]["model"] == "cheap-fast"

    @pytest.mark.asyncio
    async def test_naming_a_vendor_provider_opts_out_of_the_gateway(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        # Explicit beats default. The opt-out must stay available, and must not
        # send the gateway's metadata block to a vendor that did not ask for it.
        from codeflow_engine.actions.quality_engine.ai import (
            initialize_llm_manager,
            run_ai_analysis,
        )

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        target = tmp_path / "sample.py"
        target.write_text("x = 1\n", encoding="utf-8")

        manager = await initialize_llm_manager()
        await run_ai_analysis([str(target)], manager, provider_name="openai")

        assert len(recorder.calls) == 1
        assert "extra_body" not in recorder.calls[0]

    @pytest.mark.asyncio
    async def test_no_gateway_configured_leaves_vendor_routing_intact(
        self, recorder: _CompletionsRecorder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from codeflow_engine.actions.quality_engine.ai import initialize_llm_manager

        monkeypatch.delenv("SLUICE_BASE_URL", raising=False)
        monkeypatch.delenv("SLUICE_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")

        manager = await initialize_llm_manager()

        assert manager is not None
        assert manager.default_provider == "openai"

    @pytest.mark.asyncio
    async def test_initialization_sends_no_probe_request(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # A test completion per initialization is billed spend tagged
        # `quality-analyzer` that analyses nothing.
        from codeflow_engine.actions.quality_engine.ai import initialize_llm_manager

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        await initialize_llm_manager()

        assert recorder.calls == []

    @pytest.mark.asyncio
    async def test_the_second_initializer_shares_the_same_tag(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # ai_handler had its own initializer building a separate provider stack.
        # Two initializers meant only one of them could be routed, leaving the
        # other a standing untagged path to an LLM for the same calling feature.
        from codeflow_engine.actions.quality_engine.ai.ai_handler import (
            initialize_llm_manager as handler_initialize,
        )

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        manager = await handler_initialize()

        assert manager is not None
        assert manager.providers["sluice"].sluice_agent is SluiceAgent.QUALITY_ANALYZER

    @pytest.mark.asyncio
    async def test_the_code_analyzer_shares_the_same_tag(
        self,
        recorder: _CompletionsRecorder,
        sluice_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # AICodeAnalyzer is a sub-component of the same calling feature, so it
        # reports as `quality-analyzer` rather than spending a new time series.
        from codeflow_engine.actions.quality_engine.ai import (
            AICodeAnalyzer,
            initialize_llm_manager,
        )

        monkeypatch.setenv("OPENAI_API_KEY", "sk-vendor")
        manager = await initialize_llm_manager()
        await AICodeAnalyzer(manager).analyze_code("sample.py", "x = 1\n")

        assert sent_metadata(recorder)["agent"] == "quality-analyzer"
